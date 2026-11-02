"""CLI for native FX evidence collection and strict verification."""
import argparse
import json
from pathlib import Path
from .core import prepare, probe, verify


def main():
    parser = argparse.ArgumentParser(description="Native ReShade FX acceptance kit (never self-certifies GPU parity)")
    p = parser.add_subparsers(dest="command", required=True)
    p.add_parser("probe")
    p.add_parser("prepare").add_argument("--output", required=True, type=Path)
    p.add_parser("verify").add_argument("--bundle", required=True, type=Path)
    args = parser.parse_args()
    try:
        if args.command == "probe": result = probe()
        elif args.command == "prepare": result = prepare(args.output)
        else: result = verify(args.bundle)
    except (OSError, ValueError, KeyError) as exc:
        result = {"status": "BLOCKED_OR_INVALID", "errors": [str(exc)[:400]], "native_certified": False}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if result["status"] == "BLOCKED_OR_INVALID" else 0

if __name__ == "__main__":
    raise SystemExit(main())
