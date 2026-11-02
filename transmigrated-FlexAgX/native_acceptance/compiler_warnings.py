"""Privacy-safe ReShade log warning summarizer. Does not claim GPU acceptance."""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re

_WARNING = re.compile(r'warning\s+(X\d{4}):\s*([^\r\n]*)', re.I)
_SYMBOL = re.compile(r'\((F__[A-Za-z][A-Za-z0-9_]*)\)')
_LOCATION = re.compile(r'Shader@0x[0-9a-f]+\((\d+),\s*(\d+)(?:-\d+)?\):', re.I)


def summarize(raw: str) -> dict:
    """Parse diagnostics; discard addresses, executable paths, and full log lines."""
    if not isinstance(raw, str):
        raise TypeError('log must be decoded text')
    if len(raw) > 4_000_000:
        raise ValueError('log exceeds permitted 4 MB input')
    counts: Counter[str] = Counter()
    helpers: Counter[str] = Counter()
    locations: list[dict] = []
    for line in raw.splitlines():
        match = _WARNING.search(line)
        if not match:
            continue
        code = match.group(1).upper()
        counts[code] += 1
        if code == 'X4000':
            sym = _SYMBOL.search(match.group(2))
            helpers[sym.group(1) if sym else 'UNRESOLVED'] += 1
        loc = _LOCATION.search(line[:match.start()])
        if loc and len(locations) < 100:
            locations.append({'code': code, 'generated_line': int(loc.group(1)), 'generated_column': int(loc.group(2))})
    # 'with warnings' in a compile log is an indication, not proof of which version was compiled.
    reported_compilation = bool(re.search(r'\bwith warnings\s*:', raw, re.I))
    return {
        'status': 'WARNINGS_REPORTED' if counts else 'NO_WARNINGS_IN_EXCERPT',
        'reported_compile_with_warnings': reported_compilation,
        'warning_count': sum(counts.values()),
        'codes': dict(sorted(counts.items())),
        'x4000_helpers': dict(sorted(helpers.items())),
        'generated_positions': locations,
        'provenance': 'UNVERIFIED_UNLESS_SHADER_HASH_AND_BACKEND_ARE_RECORDED',
        'native_warning_free': False,
        'gpu_certified': False,
        'production_approved': False,
    }


def main(argv=None) -> int:
    parser=argparse.ArgumentParser(description='Redact ReShade compiler warning logs for issue triage')
    parser.add_argument('--input',required=True,type=Path)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args(argv)
    result=summarize(args.input.read_text(encoding='utf-8',errors='replace'))
    formatted=json.dumps(result,sort_keys=True,indent=2)+'\n'
    if args.output:
        # This write contains no original file paths, addresses, or shader bytes.
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(formatted,encoding='utf-8')
    else:
        print(formatted,end='')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
