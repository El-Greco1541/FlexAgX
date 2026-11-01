"""Fail-closed staged harness runner (v0.4): bounded output, fresh evidence, strict reconciliation.

No background operation. No production deployment. Applies watchdogs to each child and
process group. JSON evidence uses sentinels, never null or nonfinite scalars.
"""
from __future__ import annotations
import argparse
from collections import deque
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import signal
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / 'results_v04'
PINNED_SHADER_SHA256 = 'e744bdb7c410039f6835485c023f242ea399de14b09b3fd13657c02166d06e4d'
MAX_OUTPUT_BYTES = 1_048_576
TAIL_BYTES = 12_288
MAX_EVIDENCE_BYTES = 8_000_000
MAX_CASES = 4_096
MAX_WAIT_SECONDS = 180
MAX_READS = MAX_OUTPUT_BYTES // 4096 + 2
BASELINE_FILE = ROOT / 'reference/APP_BASELINE_HASHES.json'
SENTINEL = {'kind': 'NOT_APPLICABLE', 'reason': 'this suite does not produce phase cases', 'fallback': 'SKIP'}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def valid_json(value, path='$', depth=0):
    if depth > 32: raise AssertionError(f'nesting limit exceeded at {path}')
    if value is None: raise AssertionError(f'JSON null prohibited at {path}')
    if isinstance(value, float):
        import math
        if not math.isfinite(value): raise AssertionError(f'nonfinite JSON value at {path}')
    elif isinstance(value, dict):
        if len(value) > 6_000: raise AssertionError(f'mapping bound exceeded at {path}')
        for k, v in value.items():
            if not isinstance(k, str): raise AssertionError(f'non-string key at {path}')
            valid_json(v, f'{path}.{k[:60]}', depth+1)
    elif isinstance(value, list):
        if len(value) > MAX_CASES + 16: raise AssertionError(f'array bound exceeded at {path}')
        for i, v in enumerate(value): valid_json(v, f'{path}[{i}]', depth+1)
    elif not isinstance(value, (str, int, bool)):
        raise AssertionError(f'non-JSON type at {path}: {type(value).__name__}')


def read_evidence(path: Path, phase: str, seed: int):
    if not path.is_file(): raise AssertionError(f'missing fresh evidence for {phase}')
    if path.stat().st_size > MAX_EVIDENCE_BYTES: raise AssertionError('evidence size exceeded')
    def reject_constant(token): raise ValueError(f'nonfinite JSON token {token}')
    data = json.loads(path.read_text(encoding='utf8'), parse_constant=reject_constant)
    valid_json(data)
    if not isinstance(data, dict) or data.get('phase') != phase or data.get('seed') != seed:
        raise AssertionError('phase or seed mismatch in evidence')
    cases = data.get('cases'); checks = data.get('checks'); passed = data.get('passed'); failed = data.get('failed')
    if type(checks) is not int or type(passed) is not int or type(failed) is not int:
        raise AssertionError('invalid count types')
    if not isinstance(cases, list) or not (1 <= checks <= MAX_CASES):
        raise AssertionError('missing or oversized case collection')
    if not (checks == passed+failed == len(cases)):
        raise AssertionError('phase result count mismatch')
    statuses = [case.get('status') for case in cases if isinstance(case, dict)]
    if len(statuses) != checks or any(s not in ('pass', 'fail') for s in statuses):
        raise AssertionError('invalid case status')
    if statuses.count('pass') != passed or statuses.count('fail') != failed:
        raise AssertionError('declared counts disagree with actual cases')
    if len({case.get('name') for case in cases}) != checks:
        raise AssertionError('case names not unique')
    return {'checks':checks, 'passed':passed, 'failed':failed, 'evidence_sha256':sha(path), 'evidence_bytes':path.stat().st_size}


def _stop(proc):
    # Kill the whole POSIX process group even if its leader exited, so surviving
    # descendants cannot keep stdout pipes open after a timed-out phase.
    if os.name == 'posix':
        try: os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError: pass
    else:
        # Windows fallback: terminate the full process tree when taskkill is present.
        try: subprocess.run(['taskkill', '/T', '/F', '/PID', str(proc.pid)], timeout=3,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        except (FileNotFoundError, subprocess.TimeoutExpired): proc.kill()


def bounded(cmd: list[str], seconds: int, env: dict[str,str]):
    if not (1 <= seconds <= MAX_WAIT_SECONDS): raise ValueError('invalid per-phase time budget')
    start = time.monotonic(); output_size = 0; chunks = deque(); stored = 0
    exceeded = threading.Event(); reader_done = threading.Event()
    popen_args = {'cwd':ROOT, 'env':env, 'stdin':subprocess.DEVNULL, 'stdout':subprocess.PIPE,
                  'stderr':subprocess.STDOUT}
    if os.name == 'posix': popen_args['start_new_session'] = True
    proc = subprocess.Popen(cmd, **popen_args)

    def drain():
        nonlocal output_size, stored
        try:
            for _ in range(MAX_READS):
                b = proc.stdout.read(4096)
                if not b: break
                output_size += len(b)
                if output_size > MAX_OUTPUT_BYTES: exceeded.set(); _stop(proc); break
                chunks.append(b); stored += len(b)
                # Drain a fixed number of chunks: the accumulated tail is capped.
                if stored > TAIL_BYTES:
                    excess=stored-TAIL_BYTES
                    for _ in range(MAX_READS):
                        if excess <= 0 or not chunks: break
                        head=chunks.popleft()
                        if len(head)>excess:
                            chunks.appendleft(head[excess:]);stored-=excess;excess=0
                        else:
                            stored-=len(head);excess-=len(head)
            else:
                exceeded.set(); _stop(proc)
        finally: reader_done.set()
    thread = threading.Thread(target=drain, name='bounded-output-reader', daemon=True)
    thread.start(); timed_out = False
    try:
        proc.wait(timeout=seconds)
    except subprocess.TimeoutExpired:
        timed_out = True; _stop(proc)
    finally:
        try: proc.wait(timeout=5)
        except subprocess.TimeoutExpired: _stop(proc)
        if proc.stdout: proc.stdout.close()
        thread.join(timeout=2)
        if not reader_done.is_set(): _stop(proc)
    return {'exit_code':int(proc.returncode) if proc.returncode is not None else -999,
            'timed_out':bool(timed_out), 'output_limit_exceeded':exceeded.is_set(),
            'reader_closed':reader_done.is_set(), 'seconds':round(time.monotonic()-start,3),
            'output_tail':b''.join(chunks).decode('utf8','replace'),
            'output_bytes':output_size, 'output_limit_bytes':MAX_OUTPUT_BYTES}


def suite_catalog(seed: int, frames: int, run_dir: Path):
    phases=[]
    phases.append(('static_audit', [sys.executable,'-m','harness.static_audit'], 20, 'static'))
    phases.append(('harness_selftest', [sys.executable,'-m','harness.selftest'], 20, 'selftest'))
    phases.append(('regression_and_assurance', [sys.executable,'-m','pytest','-q','tests'], 75, 'pytest'))
    for phase,limit in [('validation',90),('metamorphic',90),('adversarial',100),('torture',160)]:
        cmd=[sys.executable,'-m',('harness.adversarial' if phase=='adversarial' else 'harness.phase'),
             *([] if phase=='adversarial' else [phase]),
             '--seed',str(seed),'--output',str(run_dir/f'{phase}.json')]
        if phase=='torture': cmd += ['--frames',str(frames)]
        phases.append((phase,cmd,limit,'phase'))
    phases.append(('distributed_guarded',[sys.executable,'tests/distributed_guarded.py',
        '--seed',str(seed),'--output',str(run_dir/'distributed_guarded.json')],80,'phase'))
    return phases


def baseline_hashes():
    baseline=json.loads(BASELINE_FILE.read_text(encoding='utf8'))
    if not isinstance(baseline,dict) or len(baseline)<10:
        raise AssertionError('baseline artifact missing or malformed')
    for rel, expected in baseline.items():
        if not isinstance(rel,str) or not isinstance(expected,str) or not (ROOT/rel).is_file():
            raise AssertionError('source baseline entry invalid')
        if sha(ROOT/rel)!=expected: raise AssertionError(f'baseline hash mismatch: {rel}')
    return len(baseline)

def main():
    parser=argparse.ArgumentParser(description='Staged, bounded, fail-closed FlexAgX v0.4 harness')
    parser.add_argument('--frames',type=int,default=900)
    parser.add_argument('--seed',type=int,default=20261101)
    opts=parser.parse_args()
    if not (1 <= opts.frames <= 1000): parser.error('frames must be 1..1000')
    if not (0 <= opts.seed <= 2**63-1): parser.error('seed must be 0..2^63-1')
    shader=ROOT/'reference/FlexAgX_original.fx'
    initial=sha(shader)
    if initial != PINNED_SHADER_SHA256:
        print('FAIL-CLOSED: reference shader hash differs from pinned v0.3.0 value',file=sys.stderr)
        return 2
    try: baseline_count=baseline_hashes()
    except (ValueError,OSError,AssertionError) as exc:
        print('FAIL-CLOSED: '+str(exc),file=sys.stderr)
        return 2
    RESULTS.mkdir(parents=True,exist_ok=True)
    run_id='run-'+secrets.token_hex(8)
    run_dir=RESULTS/'runs'/run_id
    run_dir.mkdir(parents=True,exist_ok=False)
    env={**os.environ,'PYTHONPATH':str(ROOT),'PYTHONHASHSEED':'0',
         'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1',
         'OMP_THREAD_LIMIT':'1','PYTHONDONTWRITEBYTECODE':'1'}
    out={'version':'0.4.0','seed':opts.seed,'frame_count':opts.frames,
         'run_id':run_id,'reference_shader_sha256':initial,
         'application_baseline_sha256':sha(BASELINE_FILE),'application_files_pinned':baseline_count,
         'production_gate':'LOCKED',
         'scope':'staged local verification','suites':{},'evidence_policy':'fresh-only; no JSON nulls; fail closed'}
    for name,command,limit,kind in suite_catalog(opts.seed,opts.frames,run_dir):
        detail={}
        try:
            detail=bounded(command,limit,env)
            if kind=='phase':
                detail.update(read_evidence(run_dir/f'{name}.json',name,opts.seed))
                if detail['failed']: raise AssertionError('phase recorded failed cases')
            elif kind=='pytest':
                m=re.search(r'(\d+) passed',detail['output_tail'])
                if not m: raise AssertionError('pytest pass count unavailable')
                detail['checks']=int(m.group(1));detail['passed']=detail['checks'];detail['failed']=0
            else:
                detail['checks']=1;detail['passed']=1 if detail['exit_code']==0 else 0
                detail['failed']=0 if detail['exit_code']==0 else 1
            if detail['exit_code']!=0 or detail['timed_out'] or detail['output_limit_exceeded'] or not detail['reader_closed']:
                raise AssertionError('subprocess did not complete within execution envelope')
            detail['status']='PASS'
        except Exception as exc:
            # The evidence for this suite must not reuse details from another suite.
            detail['status']='FAIL'
            detail['failure_reason']=str(exc)[:200]
        out['suites'][name]=detail
        print(f'{name}: {detail["status"]}'+(f' ({detail["failure_reason"]})' if detail['status']=='FAIL' else ''),flush=True)
        # Fail-closed: never let one failed phase prevent evidence/report creation.
    out['reference_shader_unchanged']=sha(shader)==initial
    try: out['application_baseline_unchanged']=baseline_hashes()==baseline_count
    except (AssertionError,ValueError,OSError): out['application_baseline_unchanged']=False
    out['passed']=out['reference_shader_unchanged'] and out['application_baseline_unchanged'] and all(x.get('status')=='PASS' for x in out['suites'].values())
    out['total_checks']=sum(x.get('checks',0) for x in out['suites'].values())
    out['total_failed']=sum(x.get('failed',0) for x in out['suites'].values())
    valid_json(out)
    report_path=RESULTS/'RUN_REPORT.json'
    report_path.write_text(json.dumps(out,indent=2,allow_nan=False)+'\n',encoding='utf8')
    print('OVERALL', 'PASS' if out['passed'] else 'FAIL', 'checks=',out['total_checks'])
    return 0 if out['passed'] else 1

if __name__=='__main__': sys.exit(main())
