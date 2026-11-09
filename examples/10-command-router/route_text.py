"""Exact text allowlist returning a dry-run plan; no socket or SDK calls."""
import argparse
import json
from pathlib import Path
import sys


def route(text, mapping):
    if not isinstance(mapping, dict) or any(
        not isinstance(key, str) or not isinstance(value, str) or value not in ("status", "stop_demo")
        for key, value in mapping.items()
    ):
        raise ValueError("mapping must contain only status/stop_demo string values")
    command = mapping.get(text.strip())
    return {"input": text, "accepted": command is not None, "command": command,
            "mode": "dry-run", "motion_executed": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("text")
    parser.add_argument("--mapping", type=Path,
                        default=Path(__file__).resolve().parents[2] / "configs/command-map.example.json")
    args = parser.parse_args()
    try:
        result = route(args.text, json.loads(args.mapping.read_text(encoding="utf-8")))
    except (OSError, ValueError) as exc:
        print(f"Mapping invalid: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
