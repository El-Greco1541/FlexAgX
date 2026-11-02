"""No fake fixture can cause an automatic GPU certification."""
import copy
import json
from pathlib import Path

import pytest
from PIL import Image
from native_acceptance import core


def bundle(tmp_path):
    p = tmp_path / "collection"
    core.prepare(p)
    return p


def synthetic_record(p, different_zero=False):
    record = json.loads((p / 'capture_record.template.json').read_text())
    record['native_execution_reported'] = True
    record['environment'] = {
        'platform': 'synthetic-test-platform', 'gpu': 'synthetic-test-gpu',
        'driver': 'synthetic-test-driver', 'reshade_version': 'synthetic-test-version',
        'backend': 'd3d11'
    }
    (p / 'logs').mkdir(exist_ok=True)
    log = p / 'logs' / 'ReShade.log'
    log.write_text('SYNTHETIC UNIT-TEST ONLY - NOT COMPILER EVIDENCE\n')
    record['compile'] = {'outcome': 'SUCCESS', 'log_path': 'logs/ReShade.log', 'log_sha256': core.sha256_file(log)}
    for name in core.CAPTURES:
        src = p / 'fixtures' / 'gray_ramp.png'
        dst = p / 'captures' / (name+'.png')
        dst.write_bytes(src.read_bytes())
        record['captures'][name]['sha256'] = core.sha256_file(dst)
    if different_zero:
        dst = p / 'captures' / 'zero_effect.png'
        Image.new('RGB', (96, 64), (0, 0, 0)).save(dst)
        record['captures']['zero_effect']['sha256'] = core.sha256_file(dst)
    (p / 'capture_record.json').write_text(json.dumps(record))
    return record


def update_record(p, rec):
    (p / 'capture_record.json').write_text(json.dumps(rec))


def test_reference_pin():
    pins = core.source_identity()
    assert pins['original_sha256'] == core.UPSTREAM_PIN
    assert pins['candidate_sha256'] == '2700deed3c2ff76b439e2efa70d2c41f7b94cccd5efb4123afbd3623127960ec'


def test_fixture_determinism(tmp_path):
    x, y = tmp_path / 'x', tmp_path / 'y'
    core.prepare(x)
    core.prepare(y)
    assert (x/'plan.json').read_bytes() == (y/'plan.json').read_bytes()
    for name in core.FIXTURES:
        assert (x/'fixtures'/f'{name}.png').read_bytes() == (y/'fixtures'/f'{name}.png').read_bytes()


def test_empty_record_not_native_pass(tmp_path):
    p = bundle(tmp_path)
    result = core.verify(p)
    assert result['status'] == 'BLOCKED_OR_INVALID'
    assert not result['native_certified']


def test_prepare_no_overwrite(tmp_path):
    p = bundle(tmp_path)
    with pytest.raises(ValueError, match='overwrite'):
        core.prepare(p)


def test_full_synthetic_test_record_only_evidence_review(tmp_path):
    p = bundle(tmp_path)
    synthetic_record(p)
    result = core.verify(p)
    assert result['status'] == 'EVIDENCE_READY_FOR_INDEPENDENT_REVIEW'
    assert result['evidence_complete']
    assert result['native_certified'] is False
    assert result['production_authorized'] is False


def test_synthetic_flag_rejected(tmp_path):
    p = bundle(tmp_path)
    rec = synthetic_record(p)
    rec['synthetic_or_mock'] = True
    update_record(p, rec)
    assert core.verify(p)['status'] == 'BLOCKED_OR_INVALID'


def test_native_report_absent_rejected(tmp_path):
    p = bundle(tmp_path)
    rec = synthetic_record(p)
    rec['native_execution_reported'] = False
    update_record(p, rec)
    assert core.verify(p)['status'] == 'BLOCKED_OR_INVALID'


def test_failed_compilation_rejected(tmp_path):
    p = bundle(tmp_path)
    rec = synthetic_record(p)
    rec['compile']['outcome'] = 'FAIL'
    update_record(p, rec)
    assert core.verify(p)['status'] == 'BLOCKED_OR_INVALID'


def test_compile_log_tampering_rejected(tmp_path):
    p = bundle(tmp_path)
    synthetic_record(p)
    (p/'logs'/'ReShade.log').write_text('tampered')
    assert core.verify(p)['status'] == 'BLOCKED_OR_INVALID'


def test_screenshot_tampering_rejected(tmp_path):
    p = bundle(tmp_path)
    synthetic_record(p)
    with (p/'captures'/'neutral_gray.png').open('ab') as f:
        f.write(b'changed')
    assert core.verify(p)['status'] == 'BLOCKED_OR_INVALID'


def test_malformed_png_rejected_with_valid_digest(tmp_path):
    p = bundle(tmp_path)
    rec = synthetic_record(p)
    dst = p/'captures'/'neutral_gray.png'
    dst.write_bytes(b'NOT A PNG')
    rec['captures']['neutral_gray']['sha256'] = core.sha256_file(dst)
    update_record(p, rec)
    assert core.verify(p)['status'] == 'BLOCKED_OR_INVALID'


def test_frame_dimensions_mismatch(tmp_path):
    p = bundle(tmp_path)
    rec = synthetic_record(p)
    dst = p/'captures'/'cut_second.png'
    Image.new('RGB', (97, 64)).save(dst)
    rec['captures']['cut_second']['sha256'] = core.sha256_file(dst)
    update_record(p, rec)
    assert core.verify(p)['status'] == 'BLOCKED_OR_INVALID'


def test_exact_bypass_mismatch(tmp_path):
    p = bundle(tmp_path)
    synthetic_record(p, different_zero=True)
    result = core.verify(p)
    assert result['status'] == 'BLOCKED_OR_INVALID'
    assert result['metrics']['zero_strength_max_channel_delta'] > 0


def test_missing_capture_rejected(tmp_path):
    p = bundle(tmp_path)
    synthetic_record(p)
    (p/'captures'/'cut_first.png').unlink()
    assert core.verify(p)['status'] == 'BLOCKED_OR_INVALID'


def test_missing_case_name_rejected(tmp_path):
    p = bundle(tmp_path)
    rec=synthetic_record(p)
    del rec['captures']['cut_first']
    update_record(p, rec)
    assert core.verify(p)['status'] == 'BLOCKED_OR_INVALID'


def test_traversal_log_rejected(tmp_path):
    p=bundle(tmp_path)
    rec=synthetic_record(p)
    rec['compile']['log_path']='logs/../../secret.log'
    update_record(p,rec)
    assert core.verify(p)['status']=='BLOCKED_OR_INVALID'


def test_absolute_capture_path_rejected(tmp_path):
    p=bundle(tmp_path)
    rec=synthetic_record(p)
    rec['captures']['neutral_gray']['path']='/etc/passwd'
    update_record(p,rec)
    assert core.verify(p)['status']=='BLOCKED_OR_INVALID'


def test_symlink_capture_rejected(tmp_path):
    p=bundle(tmp_path)
    rec=synthetic_record(p)
    src=p/'captures'/'neutral_gray.png'
    src.unlink()
    src.symlink_to(p/'fixtures'/'gray_ramp.png')
    update_record(p,rec)
    assert core.verify(p)['status']=='BLOCKED_OR_INVALID'


def test_backend_spoof_rejected(tmp_path):
    p=bundle(tmp_path)
    rec=synthetic_record(p)
    rec['environment']['backend']='test-mock'
    update_record(p,rec)
    assert core.verify(p)['status']=='BLOCKED_OR_INVALID'


def test_source_hash_spoof_rejected(tmp_path):
    p=bundle(tmp_path)
    rec=synthetic_record(p)
    rec['candidate_sha256']='0'*64
    update_record(p,rec)
    assert core.verify(p)['status']=='BLOCKED_OR_INVALID'


def test_fixture_tampering_rejected(tmp_path):
    p=bundle(tmp_path)
    synthetic_record(p)
    (p/'fixtures'/'gray_ramp.png').write_bytes(b'junk')
    assert core.verify(p)['status']=='BLOCKED_OR_INVALID'


def test_toolchain_probe_never_claims_compile_or_gpu():
    r=core.probe()
    assert r['fx_compilation']=='NOT_EXECUTED'
    assert r['gpu_render']=='NOT_EXECUTED'
    assert r['gpu_device']=='UNVERIFIED'
    assert r['status']=='NATIVE_VALIDATION_NOT_EXECUTED'
