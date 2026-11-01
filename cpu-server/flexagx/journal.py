"""Bounded SQLite transaction journal; no null or nonfinite wire values.
Single writer/controller-process only; use external coordination before multi-replica.
"""
from __future__ import annotations
import sqlite3, json, math

MAX_RECEIPTS=512
MAX_TOTAL_RECEIPT_BYTES=128*1024*1024
MAX_SINGLE_RECEIPT_BYTES=20*1024*1024

def _json(obj):
    return json.dumps(obj,sort_keys=True,separators=(',',':'),allow_nan=False)

class Journal:
    def __init__(self,path=':memory:'):
        self.conn=sqlite3.connect(path,check_same_thread=False,timeout=5,isolation_level=None)
        if path!=':memory:':
            self.conn.execute('PRAGMA journal_mode=WAL')
            self.conn.execute('PRAGMA synchronous=FULL')
        self.conn.execute('CREATE TABLE IF NOT EXISTS sessions (session_id TEXT PRIMARY KEY NOT NULL, state_json TEXT NOT NULL, last_frame INTEGER NOT NULL)')
        self.conn.execute('CREATE TABLE IF NOT EXISTS receipts (session_id TEXT NOT NULL, frame_index INTEGER NOT NULL, digest TEXT NOT NULL, response_json TEXT NOT NULL, token TEXT NOT NULL UNIQUE, PRIMARY KEY(session_id,frame_index))')
    def load(self):
        states={}
        for sid,s,idx in self.conn.execute('SELECT session_id,state_json,last_frame FROM sessions'):
            o=json.loads(s)
            if (not isinstance(o,dict) or len(o.get('prev_hist',[]))!=64 or any(not isinstance(v,(int,float)) or not math.isfinite(v) for v in o['prev_hist']) or any(not isinstance(o.get(k),(int,float)) or not math.isfinite(o[k]) for k in ('x','v','knee','cut_count','stored_lambda','applied_auto_ev','warmup')) or type(o.get('frames')) is not int or not 0<=o['frames']<2**63 or type(idx) is not int or not -1<=idx<2**63):
                raise ValueError('invalid persisted controller state; fail closed')
            states[sid]=(o,idx)
        return states
    def find(self,sid,frame):
        return self.conn.execute('SELECT digest,response_json,token FROM receipts WHERE session_id=? AND frame_index=?',(sid,frame)).fetchone()
    def last(self,sid):
        row=self.conn.execute('SELECT last_frame FROM sessions WHERE session_id=?',(sid,)).fetchone()
        return row[0] if row else -1
    def write(self,sid,frame,digest,response,token,state):
        serial=_json(response)
        if len(serial.encode('utf-8'))>MAX_SINGLE_RECEIPT_BYTES: raise ValueError('receipt exceeds bounded size')
        state_text=_json(state)
        db=self.conn
        db.execute('BEGIN IMMEDIATE')
        try:
            existing=self.find(sid,frame)
            if existing or frame<=self.last(sid): raise ValueError('frame replay/conflict detected before commit')
            db.execute('INSERT INTO receipts(session_id,frame_index,digest,response_json,token) VALUES(?,?,?,?,?)',(sid,frame,digest,serial,token))
            db.execute('INSERT INTO sessions(session_id,state_json,last_frame) VALUES(?,?,?) ON CONFLICT(session_id) DO UPDATE SET state_json=excluded.state_json,last_frame=excluded.last_frame',(sid,state_text,frame))
            # Bounded eviction; watermarks survive eviction so stale requests cannot reexecute.
            db.execute('DELETE FROM receipts WHERE rowid IN (SELECT rowid FROM receipts ORDER BY rowid DESC LIMIT -1 OFFSET ?)',(MAX_RECEIPTS,))
            for _ in range(MAX_RECEIPTS):
                n=db.execute('SELECT COALESCE(SUM(LENGTH(response_json)),0) FROM receipts').fetchone()[0]
                if n<=MAX_TOTAL_RECEIPT_BYTES: break
                db.execute('DELETE FROM receipts WHERE rowid=(SELECT MIN(rowid) FROM receipts)')
            else: raise ValueError('receipt budget exhausted')
            db.execute('COMMIT')
        except BaseException:
            db.execute('ROLLBACK')
            raise
    def reset(self,sid):
        db=self.conn;db.execute('BEGIN IMMEDIATE')
        try:
            db.execute('DELETE FROM sessions WHERE session_id=?',(sid,))
            db.execute('DELETE FROM receipts WHERE session_id=?',(sid,))
            db.execute('COMMIT')
        except BaseException:
            db.execute('ROLLBACK');raise
