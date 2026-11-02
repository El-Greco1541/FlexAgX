"""CT-009 source-isolation tests: no ReShade FX compiler is invoked."""
from pathlib import Path
import re
import pytest

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "shader" / "FlexAgX_transmigrated.fx"
TRIAL = ROOT / "shader" / "FlexAgX_transmigrated_CT009_X4000_candidate.fx"
NAMES = ("FA_Decode", "FA_Encode", "FA_Dn", "FA_Native",
         "FA_ComposedCurve", "FA_WhiteBalance", "FA_ConstrainGamutAfterMix")
RESULTS = ("decoded", "encoded", "result", "result",
           "result", "balanced", "constrained")

def find_span(s, name):
    m = re.search(r"\\bfloat(?:3)?\\s+" + name + r"\\s*\\([^;{}]*\\)\\s*\\{", s)
    assert m, name
    depth = 0
    for i in range(s.index("{", m.start()), len(s)):
        depth += (s[i] == "{") - (s[i] == "}")
        if depth == 0:
            return m.start(), i + 1
    raise AssertionError("unbalanced " + name)

def mask(s):
    for name in NAMES:
        a, b = find_span(s, name)
        s = s[:a] + "/*CT009_REPLACEMENT*/" + s[b:]
    return s

def test_no_other_shader_code_changed():
    assert mask(BASE.read_text(encoding="utf8")) == mask(TRIAL.read_text(encoding="utf8"))

@pytest.mark.parametrize("name,out", zip(NAMES, RESULTS))
def test_initialized_single_exit(name, out):
    s = TRIAL.read_text(encoding="utf8")
    a, b = find_span(s, name)
    body = s[a:b]
    assert len(re.findall(r"\\breturn\\s+\\w+\\s*;", body)) == 1
    assert re.search(r"\\b" + out + r"\\s*=\\s*", body)
    assert re.search(r"\\breturn\\s+" + out + r"\\s*;", body)

def test_ct008_and_pass_chain():
    a = BASE.read_text(encoding="utf8")
    b = TRIAL.read_text(encoding="utf8")
    assert "pow(max(t, 0.0), _FA_GAMUT_P)" in b
    assert b.count("pass FlexAgX_") == a.count("pass FlexAgX_")
    assert b.count("technique FlexAgX") == 1
