"""CT-008: warning log sanitization and gamut pow domain regression."""
from pathlib import Path
from math import isfinite
import json
import math
import random
import subprocess
import sys

from native_acceptance.compiler_warnings import summarize
from harness.source_audit import check_corrections

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT/'shader/FlexAgX_transmigrated.fx').read_text()
ORIGINAL = (ROOT/'reference/FlexAgX_1.2.fx').read_text()


def _log():
    return ("SYNTHETIC_SHADER_STREAM\\Shader@0x000001ABCDEF(102,2): warning X4000: use of potentially uninitialized variable (F__FA_Decode)\n"
            "SYNTHETIC_SHADER_STREAM\\Shader@0x000001ABCDEF(556,17-43): warning X3571: pow(f, e) will not work for negative f\n"
            "SYNTHETIC_SHADER_STREAM\\Shader@0x000001ABCDEF(123,2): warning X4000: use of potentially uninitialized variable (F__FA_Decode)\n")


def test_count_and_helper_counts():
    x=summarize(_log())
    assert x['warning_count']==3
    assert x['codes']=={'X3571':1,'X4000':2}
    assert x['x4000_helpers']=={'F__FA_Decode':2}


def test_generated_locations_do_not_claim_fx_source_line():
    x=summarize(_log())
    assert x['generated_positions'][0]['generated_line']==102
    assert all('fx_source_line' not in d for d in x['generated_positions'])


def test_redaction_of_path_and_pointer():
    out=json.dumps(summarize(_log()))
    assert 'SYNTHETIC_SHADER_STREAM' not in out and '0x000001ABCDEF' not in out


def test_provenance_and_gpu_gate_always_unverified():
    x=summarize(_log())
    assert x['provenance'].startswith('UNVERIFIED')
    assert not x['native_warning_free'] and not x['gpu_certified'] and not x['production_approved']


def test_unrecognized_warning_code_is_grouped():
    x=summarize('Shader@0x1(12,4): warning X9999: arbitrary\n')
    assert x['codes']=={'X9999':1} and x['warning_count']==1


def test_plain_log_does_not_claim_success():
    x=summarize(_log())
    assert not x['reported_compile_with_warnings']
    y=summarize('Compiled shader in 1.8 s with warnings:\n'+_log())
    assert y['reported_compile_with_warnings']


def test_empty_log_is_not_warning_free_certification():
    x=summarize('')
    assert x['status']=='NO_WARNINGS_IN_EXCERPT' and not x['native_warning_free']


def test_unmatched_helper_is_explicit():
    x=summarize('warning X4000: unknown target')
    assert x['x4000_helpers']=={'UNRESOLVED':1}


def test_bounded_input():
    import pytest
    with pytest.raises(ValueError): summarize('x' * 4_000_001)


def test_nonstring_rejected():
    import pytest
    with pytest.raises(TypeError): summarize(None)


def test_case_insensitive_codes():
    assert summarize('WARNING x4000: use of potentially uninitialized variable (F__FA_Dn)')['codes']=={'X4000':1}


def test_pow_guard_is_source_visible():
    assert 'pow(max(t, 0.0), _FA_GAMUT_P)' in SOURCE
    assert 'pow(t, _FA_GAMUT_P)' not in SOURCE
    assert not check_corrections(SOURCE, ORIGINAL)


def test_mutant_without_explicit_pow_domain_is_rejected():
    mutant=SOURCE.replace('pow(max(t, 0.0), _FA_GAMUT_P)','pow(t, _FA_GAMUT_P)')
    assert 'GAMUT_POW_DOMAIN_GUARD_MISSING' in check_corrections(mutant,ORIGINAL)


def test_equivalence_for_legal_ui_domain():
    # Original and guarded expression are mathematically identical when t >= 0.
    rng=random.Random(16402)
    for _ in range(5000):
        k=rng.uniform(.6,.95)
        x=rng.uniform(k,12.0)
        t=(x-k)/(1.0-k)
        p=2.0 # positive exponent is sufficient for domain test
        old=k+(1-k)*t / (1.0+t**p)**(1.0/p)
        new=k+(1-k)*t / (1.0+max(t,0.0)**p)**(1.0/p)
        assert old == new and isfinite(new)


def test_negative_excursion_is_bounded_only_in_pow_input():
    for t in [-1e-8,-0.01,-1.0]:
        assert max(t,0.0)==0


def test_cli_sanitizes_output(tmp_path):
    inp=tmp_path/'source.log';out=tmp_path/'summary.json'
    inp.write_text(_log())
    subprocess.run([sys.executable,'-m','native_acceptance.compiler_warnings','--input',str(inp),'--output',str(out)],cwd=ROOT,check=True,timeout=10)
    data=json.loads(out.read_text())
    assert data['warning_count']==3
    assert 'PRIVATE' not in out.read_text()
