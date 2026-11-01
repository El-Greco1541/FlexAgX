"""CT-006/F39 containment and CT-007/F40 contract characterization; CPU not FX execution."""
from pathlib import Path
import math,random
import pytest
from harness.color_oracle import constrain_composite, from_lab,to_lab,ingamut,mixed,encode,decode,bypass_or_encode
from harness.source_audit import check_corrections
ROOT=Path(__file__).resolve().parents[1]
SRC=(ROOT/'shader/FlexAgX_transmigrated.fx').read_text()
REF=(ROOT/'reference/FlexAgX_1.2.fx').read_text()

def test_structural_gamut_guard_and_zero_bypass():
    assert check_corrections(SRC,REF)==[]

def test_mutate_guard_away_is_detected():
    changed=SRC.replace('finalLinear = FA_ConstrainGamutAfterMix(finalLinear);','finalLinear = finalLinear;',1)
    assert 'COMPOSITE_GAMUT_SECTION_MISSING' in check_corrections(changed,REF)

def test_mutate_guard_before_blend_is_detected():
    changed=SRC.replace('finalLinear = FA_ConstrainGamutAfterMix(finalLinear);','float3 noop = FA_ConstrainGamutAfterMix(finalLinear);',1)
    assert 'COMPOSITE_GAMUT_SECTION_MISSING' in check_corrections(changed,REF)

def test_mutate_guard_loop_is_detected():
    changed=SRC.replace('for (int i = 0; i < 12; ++i)','for (int i = 0; i < 1; ++i)',1)
    assert 'COMPOSITE_GAMUT_GUARD_INVALID' in check_corrections(changed,REF)

def test_exact_in_gamut_identity():
    rng=random.Random(3901)
    for i in range(4000):
        c=tuple(rng.random() for _ in range(3))
        assert constrain_composite(c)==c

def test_post_blend_rescues_out_of_gamut_original():
    orig=(1.8,.5,-.08);processed=(.2,.3,.4)
    for strength in (0.001,1,2,5,10,20,40):
        unguarded=mixed(orig,processed,strength)
        assert not ingamut(unguarded)
        corrected=constrain_composite(unguarded)
        assert ingamut(corrected)
        assert corrected!=unguarded

def test_hue_direction_preserved_when_lightness_is_valid():
    rng=random.Random(3902)
    measured=0
    for i in range(1500):
        c=(rng.uniform(-.15,1.75),rng.uniform(-.15,1.75),rng.uniform(-.15,1.75))
        if ingamut(c):continue
        L,a,b=to_lab(c)
        corrected=constrain_composite(c)
        assert ingamut(corrected)
        if 0.03<L<0.97 and a*a+b*b>1e-7:
            _,aa,bb=to_lab(corrected)
            norm=math.hypot(a,b)*math.hypot(aa,bb)
            if norm>1e-8:
                cosine=(a*aa+b*bb)/norm
                assert cosine>0.999, (c,corrected,cosine)
                measured+=1
    assert measured>100

def test_neutral_out_of_gamut_approaches_neutral():
    for c in ((2.,2.,2.),(-.1,-.1,-.1),(1.5,1.5,1.5)):
        out=constrain_composite(c)
        assert ingamut(out)
        assert max(out)-min(out)<1e-4

def test_float_domains_reject_invalids():
    for x in (float('nan'),float('inf'),float('-inf'),9.):
        with pytest.raises(ValueError):constrain_composite((x,0,0))

def test_f40_exact_zero_bypass_and_cross_encoding_jump():
    for encoded in (.05,.18,.4,.8):
        lin=decode(encoded,'srgb')
        zero=bypass_or_encode(encoded,lin,0,'gamma22')
        pos=bypass_or_encode(encoded,lin,.00001,'gamma22')
        assert zero==encoded
        assert abs(pos-zero)>1e-5

def test_f40_same_encoding_near_zero_continuity_without_dither():
    for enc in ('srgb','gamma22'):
        for value in (0.,.05,.2,.7,1.):
            decoded=decode(value,enc)
            if value in (0.,1.):continue
            assert abs(bypass_or_encode(value,decoded,1e-8,enc)-value)<1e-6

def test_f40_zero_bypass_preserves_out_of_domain_bits_via_identity():
    assert bypass_or_encode(1.15,.5,0,'gamma22')==1.15

def test_encoding_source_is_not_implicitly_changed():
    out=SRC[SRC.index('float4 FlexAgX_OutputPS'):SRC.index('technique FlexAgX')]
    assert 'return originalEncoded;' in out
    assert 'float3 encoded = FA_Encode(clamp(finalLinear, 0.0, 1.0));' in out
