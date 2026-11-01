"""Source-anchored assertions; static validation is not GPU compiler verification."""
import hashlib, re
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]
ORIGINAL=(BASE/'reference/FlexAgX_1.2.fx').read_bytes()
FX=(BASE/'shader/FlexAgX_transmigrated.fx').read_text()

def test_upstream_source_immutable():
    assert hashlib.sha256(ORIGINAL).hexdigest() == 'e744bdb7c410039f6835485c023f242ea399de14b09b3fd13657c02166d06e4d'

def test_clear_before_histogram():
    assert FX.index('pass FlexAgX_ClearHistogramPass') < FX.index('pass FlexAgX_HistogramPass')
    assert 'ComputeShader = FlexAgX_ClearHistogram;' in FX
    assert 'if (id.x < 67u)' in FX
    assert 'tex2Dstore(FA_HistStorage, int2((int)id.x, 0), 0u)' in FX
    assert FX.index('void FlexAgX_ClearHistogram') < FX.index('void FlexAgX_Histogram')

def test_original_eight_passes_retained():
    source=ORIGINAL.decode()
    old=re.findall(r'pass (FlexAgX_\w+)',source)
    new=re.findall(r'pass (FlexAgX_\w+)',FX)
    assert len(old)==8 and len(new)==9
    assert old==[s for s in new if s != 'FlexAgX_ClearHistogramPass']

def test_no_unguarded_achromatic_hue():
    src=FX[FX.index('float4 FlexAgX_HuePS'):FX.index('// P5:')]
    out=FX[FX.index('float4 FlexAgX_OutputPS'):FX.index('technique FlexAgX')]
    assert 'if (inputChroma >= 1.0e-4)' in src
    assert 'if (curvedChroma > 1.0e-6)' in src
    assert 'if (C > 1.0e-6)' in out
    assert src.index('if (curvedChroma > 1.0e-6)') < src.index('h = atan2(lab.z, lab.y)')
    assert out.index('if (C > 1.0e-6)') < out.index('h = atan2(b, a)')

def test_no_unbounded_while_constructs():
    assert not re.search(r'\bwhile\s*\(',FX)
