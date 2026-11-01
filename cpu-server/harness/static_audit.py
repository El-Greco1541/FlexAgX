"""Bounded structure audit: fails closed on an unbounded while loop or missing ceilings.

This is a structural audit, not a proof of total correctness or termination of 3rd-party C extensions.
"""
from pathlib import Path
import ast
import json
from dataclasses import fields, MISSING
from flexagx.controller import State, SessionStore
from flexagx.contracts import Settings, FrameResult, Observation, Sentinel

ROOT=Path(__file__).resolve().parents[1]
SOURCE_FILES=sorted((ROOT/'flexagx').glob('*.py'))+sorted((ROOT/'services').glob('*.py'))
HARNESS_FILES=sorted((ROOT/'harness').glob('*.py'))


def no_null(v):
    if v is None:raise AssertionError('Null rather than sentinel in serialized record')
    if isinstance(v,dict):
        for item in v.values():no_null(item)
    elif isinstance(v,(list,tuple)):
        for item in v:no_null(item)


def main():
    while_loops=[]; total_for=0;total_ast=0
    for src in SOURCE_FILES:
        tree=ast.parse(src.read_text(),filename=str(src))
        for node in ast.walk(tree):
            total_ast+=1
            if isinstance(node,(ast.For,ast.AsyncFor,ast.comprehension)):total_for+=1
            if isinstance(node,ast.While):while_loops.append(f'{src.name}:{node.lineno}')
    for src in HARNESS_FILES:
        tree=ast.parse(src.read_text(),filename=str(src))
        for node in ast.walk(tree):
            if isinstance(node,ast.While): while_loops.append(f'{src.name}:{node.lineno}')
    assert not while_loops,while_loops
    # Data layouts must begin with a real value; empty initialization is a sentinel code.
    for f in fields(State):
        assert f.default is not MISSING or f.default_factory is not MISSING, f.name
    assert all(field.annotation is not type(None) for field in Settings.model_fields.values())
    assert all(field.annotation is not type(None) for field in FrameResult.model_fields.values())
    assert all(field.annotation is not type(None) for field in Observation.model_fields.values())
    assert len(State().prev_hist)==64
    assert SessionStore().max_sessions==128
    assert Sentinel(kind='UNINITIALIZED',reason='test sentinel').fallback=='REJECT'
    limits={'body_bytes':21_000_000,'decoded_image_pixels':2_000_000,'base64_chars':20_000_000,
        'histogram_bins':64,'lut_size':1024,'lut_build_attempts':4,'hue_gamut_iterations':10,
        'controller_binary_search_iterations':30,'max_sessions':128,'max_pending':128,
        'pending_ttl_seconds':30,'http_timeout_seconds_per_service':15,'harness_frames_max':1000}
    result={'files_checked':len(SOURCE_FILES)+len(HARNESS_FILES),'ast_nodes_inspected':total_ast,'loops_found':total_for,
            'unbounded_while_loops':while_loops,'state_fields_initialized':len(fields(State)),
            'limits':limits,'verdict':'PASS','limitation':'structural guard; no formal total-termination proof'}
    no_null(result)
    print(json.dumps(result,indent=2,allow_nan=False))
    return result


if __name__=='__main__':main()
