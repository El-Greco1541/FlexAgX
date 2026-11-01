"""Explicit read-only dependency on sibling CPU rendition v0.5.0.

The original v0.5.0 code is reused instead of making another independent
approximate numerical port. Failure to resolve the sibling is fail-closed.
"""
from __future__ import annotations
import hashlib
import sys
from pathlib import Path

FX_SHA256 = 'e744bdb7c410039f6835485c023f242ea399de14b09b3fd13657c02166d06e4d'
CPU_ROOT = Path(__file__).resolve().parents[2] / 'cpu-server'
FX_REFERENCE = Path(__file__).resolve().parents[1] / 'reference' / 'FlexAgX_1.2.fx'


def source_hash()->str:
    return hashlib.sha256(FX_REFERENCE.read_bytes()).hexdigest()


def check_reference()->bool:
    if source_hash() != FX_SHA256:
        raise RuntimeError('Source integrity failure: original shader hash mismatch')
    return True


def import_cpu_core():
    if not (CPU_ROOT/'flexagx'/'compute.py').is_file() or not (CPU_ROOT/'flexagx'/'journal.py').is_file():
        raise RuntimeError('Required sibling cpu-server/ v0.5.0 unavailable')
    if str(CPU_ROOT) not in sys.path:
        sys.path.insert(0,str(CPU_ROOT))
    from flexagx import compute, contracts, controller
    return compute, contracts, controller
