"""Reproducible fixture and strict evidence-review protocol for ReShade/GPU acceptance.

This validates provenance and observed capture evidence only. It CANNOT certify that a
log or image came from a real GPU. External operator review is mandatory.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
from pathlib import Path

from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "shader" / "FlexAgX_transmigrated.fx"
UPSTREAM = ROOT / "reference" / "FlexAgX_1.2.fx"
UPSTREAM_PIN = "e744bdb7c410039f6835485c023f242ea399de14b09b3fd13657c02166d06e4d"
CANDIDATE_PIN = "6603e5ecb42458ce55845021d56c653ed01806ecaead3a5be21c69b6152808ca"
MAX_JSON = 256 * 1024
MAX_IMAGE = 30 * 1024 * 1024
MAX_LOG = 4 * 1024 * 1024
BACKENDS = {"d3d11", "d3d12", "opengl43", "vulkan"}
CAPTURES = (
    "zero_baseline", "zero_effect", "neutral_gray", "saturated_color",
    "first_frame", "reload_frame", "cut_first", "cut_second",
)
FIXTURES = ("gray_ramp", "saturated_grid", "highlight_step", "scene_dark", "scene_bright")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    with path.open("rb") as f:
        digest = hashlib.sha256()
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def valid_sha(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def source_identity() -> dict:
    manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
    original_hash = sha256_file(UPSTREAM)
    candidate_hash = sha256_file(SOURCE)
    if original_hash != UPSTREAM_PIN or original_hash != manifest["original_sha256"]:
        raise ValueError("Original shader reference identity mismatch")
    if candidate_hash != CANDIDATE_PIN or candidate_hash != manifest["corrected_sha256"]:
        raise ValueError("Candidate shader does not match the pinned v0.6 source")
    return {"original_sha256": original_hash, "candidate_sha256": candidate_hash}


def probe() -> dict:
    # A generic HLSL/GLSL compiler is NOT a ReShade FX compiler.
    names = ("reshadefx", "ReShade", "vulkaninfo", "nvidia-smi", "dxc", "glslangValidator")
    found = {n: bool(shutil.which(n)) for n in names}
    return {
        "status": "NATIVE_VALIDATION_NOT_EXECUTED",
        "platform": platform.system(),
        "compilers": {"reshade_fx_tool_discovered": found["reshadefx"] or found["ReShade"],
                      "generic_compilers_not_sufficient": True},
        "runtime_indicators": {"vulkaninfo": found["vulkaninfo"], "nvidia_smi": found["nvidia-smi"]},
        "executables_detected": found,
        "gpu_device": "UNVERIFIED",
        "fx_compilation": "NOT_EXECUTED",
        "gpu_render": "NOT_EXECUTED",
        "operator_review": "REQUIRED",
    }


def image_pixels(kind: str, size=(96, 64)) -> Image.Image:
    w, h = size
    image = Image.new("RGB", size)
    pixels = []
    palette = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0),
               (0, 255, 255), (255, 0, 255), (255, 255, 255), (0, 0, 0)]
    for y in range(h):
        for x in range(w):
            if kind == "gray_ramp":
                v = (x * 255) // (w - 1)
                rgb = (v, v, v)
            elif kind == "saturated_grid":
                rgb = palette[((x // 12) + (y // 16)) % len(palette)]
            elif kind == "highlight_step":
                rgb = ((8, 8, 8), (64, 64, 64), (190, 190, 190), (250, 250, 250), (255, 255, 255))[(x * 5) // w]
            elif kind == "scene_dark":
                rgb = (12 + x * 9 // w, 13 + y * 8 // h, 15)
            elif kind == "scene_bright":
                rgb = (231 + x * 12 // w, 232 + y * 11 // h, 233)
            else:
                raise ValueError("Unknown fixture")
            pixels.append(rgb)
    image.putdata(pixels)
    return image


def prepare(destination: Path) -> dict:
    source = source_identity()
    destination = destination.expanduser().resolve()
    if destination.exists() and any(destination.iterdir()):
        raise ValueError("Refuse to overwrite a nonempty evidence directory")
    if ROOT.resolve() == destination or ROOT.resolve() in destination.parents:
        raise ValueError("Native evidence must be outside the tracked project tree")
    (destination / "fixtures").mkdir(parents=True, exist_ok=True)
    (destination / "captures").mkdir(exist_ok=True)
    fixtures = {}
    for name in FIXTURES:
        path = destination / "fixtures" / (name + ".png")
        image_pixels(name).save(path, format="PNG", optimize=False)
        fixtures[name] = {"path": "fixtures/" + name + ".png", "sha256": sha256_file(path), "width": 96, "height": 64}
    plan = {
        "schema": "FlexAgX-native-acceptance-v1", "status": "PREPARATION_ONLY",
        **source, "fixtures": fixtures, "required_captures": list(CAPTURES),
        "instructions": "Follow docs/NATIVE_ACCEPTANCE.md. Manually collect real ReShade log and captures; no simulated capture is acceptable.",
        "required_decisions": ["F18/F32 cold/reload", "F23/F24 deadband", "F29 scene cut", "F39 gamut", "F40 encoding hold"],
    }
    (destination / "plan.json").write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    template = {
        "schema": plan["schema"], "candidate_sha256": source["candidate_sha256"],
        "original_sha256": source["original_sha256"],
        "synthetic_or_mock": False, "native_execution_reported": False,
        "environment": {"platform": "", "gpu": "", "driver": "", "reshade_version": "", "backend": ""},
        "compile": {"outcome": "NOT_RUN", "log_path": "", "log_sha256": ""},
        "captures": {k: {"path": "captures/" + k + ".png", "sha256": ""} for k in CAPTURES},
        "notes": "Complete only from a real offline GPU execution. This record is untrusted until independently reviewed.",
    }
    (destination / "capture_record.template.json").write_text(json.dumps(template, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"status": "PREPARED_NOT_EXECUTED", "path": str(destination), "fixture_count": len(fixtures), "capture_slots": len(CAPTURES), **source}


def _path_within(bundle: Path, rel: str) -> Path:
    if not isinstance(rel, str) or not rel or rel.startswith(("/", "\\")) or "\\" in rel:
        raise ValueError("Unsafe evidence path")
    parts = Path(rel).parts
    if ".." in parts or "." in parts or ":" in rel or any(not p for p in parts):
        raise ValueError("Unsafe evidence path")
    p = bundle / rel
    if p.is_symlink() or not p.resolve().is_relative_to(bundle.resolve()):
        raise ValueError("Evidence path escapes bundle")
    return p


def _read_json(path: Path) -> dict:
    if not path.is_file() or path.stat().st_size > MAX_JSON or path.is_symlink():
        raise ValueError("JSON evidence missing, oversized or linked")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Expected JSON object")
    return data


def _check_pinned_file(bundle: Path, rel: str, digest: object, size_limit: int):
    if not valid_sha(digest):
        raise ValueError("Missing or malformed sha256")
    p = _path_within(bundle, rel)
    if not p.is_file() or p.stat().st_size > size_limit or p.stat().st_size == 0:
        raise ValueError("Evidence artifact missing or oversized")
    if sha256_file(p) != digest:
        raise ValueError("Evidence artifact SHA-256 mismatch")
    return p


def verify(bundle: Path) -> dict:
    bundle = bundle.expanduser().resolve()
    issues = []
    metrics = {}
    try:
        source = source_identity()
        plan = _read_json(bundle / "plan.json")
        record = _read_json(bundle / "capture_record.json")
        if plan.get("schema") != "FlexAgX-native-acceptance-v1" or record.get("schema") != plan.get("schema"):
            raise ValueError("Wrong acceptance evidence schema")
        for field in ("candidate_sha256", "original_sha256"):
            if plan.get(field) != source[field] or record.get(field) != source[field]:
                raise ValueError("Source reference changed")
        for name in FIXTURES:
            item = plan.get("fixtures", {}).get(name)
            if not isinstance(item, dict) or item.get("path") != "fixtures/" + name + ".png":
                raise ValueError("Fixture manifest incomplete")
            _check_pinned_file(bundle, item["path"], item.get("sha256"), MAX_IMAGE)
        if record.get("synthetic_or_mock") is not False or record.get("native_execution_reported") is not True:
            raise ValueError("Real native execution must be recorded; synthetic runs cannot satisfy acceptance")
        env = record.get("environment")
        if not isinstance(env, dict) or env.get("backend") not in BACKENDS:
            raise ValueError("Missing or unsupported backend")
        if any(not isinstance(env.get(field), str) or not 1 <= len(env[field]) <= 160 for field in ("platform", "gpu", "driver", "reshade_version")):
            raise ValueError("Incomplete native environment identity")
        compile_e = record.get("compile")
        if not isinstance(compile_e, dict) or compile_e.get("outcome") != "SUCCESS":
            raise ValueError("Native compilation not reported successful")
        log_rel = compile_e.get("log_path")
        if not isinstance(log_rel, str) or not log_rel.startswith("logs/") or not log_rel.endswith(".log"):
            raise ValueError("Native compile log must be under logs/*.log")
        _check_pinned_file(bundle, log_rel, compile_e.get("log_sha256"), MAX_LOG)
        captures = record.get("captures")
        if not isinstance(captures, dict) or set(captures) != set(CAPTURES) or plan.get("required_captures") != list(CAPTURES):
            raise ValueError("Capture series incomplete")
        images = {}
        size = None
        for key in CAPTURES:
            row = captures[key]
            if not isinstance(row, dict) or row.get("path") != "captures/" + key + ".png":
                raise ValueError("Missing named capture")
            path = _check_pinned_file(bundle, row["path"], row.get("sha256"), MAX_IMAGE)
            with Image.open(path) as im:
                if im.format != "PNG" or im.width < 16 or im.height < 16 or im.width > 4096 or im.height > 2160:
                    raise ValueError("Invalid capture PNG size/format")
                im.verify()
            with Image.open(path) as im:
                rgb = im.convert("RGB")
                if size is None: size = rgb.size
                elif rgb.size != size: raise ValueError("Captures must share identical uncropped dimensions")
                images[key] = rgb
        difference = ImageChops.difference(images["zero_baseline"], images["zero_effect"])
        metrics["zero_strength_max_channel_delta"] = max(difference.getextrema()[i][1] for i in range(3))
        metrics["capture_dimensions"] = list(size)
        if metrics["zero_strength_max_channel_delta"] != 0:
            issues.append("Exact zero-strength bypass failed equality check; verify frame alignment and host determinism")
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError, Image.UnidentifiedImageError) as exc:
        issues.append(str(exc)[:400])
    status = "EVIDENCE_READY_FOR_INDEPENDENT_REVIEW" if not issues else "BLOCKED_OR_INVALID"
    return {
        "schema": "FlexAgX-native-acceptance-verdict-v1", "status": status,
        "native_certified": False, "production_authorized": False,
        "evidence_complete": not issues,
        "metrics": metrics, "issues": issues,
        "notes": "Hash/integrity and PNG comparisons cannot prove the capture was performed on a real GPU; separate operator/peer attestation is mandatory.",
    }
