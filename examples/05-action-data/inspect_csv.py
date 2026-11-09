"""Validate an explicitly defined teaching CSV schema; never execute motion."""
import argparse
import csv
import json
import math
from pathlib import Path
import sys


def inspect(path, joints, max_abs):
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.reader(stream)
        expected = ["time_s"] + [f"q{i}_rad" for i in range(joints)]
        if next(reader, None) != expected:
            raise ValueError(f"Header must be {expected}; legacy CSV requires an explicit adapter")
        previous = -1.0
        first = None
        rows = 0
        for line, row in enumerate(reader, 2):
            if len(row) != joints + 1:
                raise ValueError(f"Line {line}: incorrect column count")
            values = [float(value) for value in row]
            if not all(math.isfinite(value) for value in values):
                raise ValueError(f"Line {line}: NaN/Infinity is invalid")
            if values[0] < 0 or values[0] <= previous:
                raise ValueError(f"Line {line}: timestamps must be non-negative and strictly increasing")
            if any(abs(value) > max_abs for value in values[1:]):
                raise ValueError(f"Line {line}: exceeds the supplied teaching bound")
            if first is None:
                first = values[0]
            previous = values[0]
            rows += 1
        if rows < 2:
            raise ValueError("At least two data rows are required")
        return {"rows": rows, "joints": joints, "duration_s": previous - first,
                "schema_valid": True, "motion_validated": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("--joints", type=int, required=True)
    parser.add_argument("--max-abs-rad", type=float, required=True,
                        help="Teaching bound; not a robot joint limit")
    args = parser.parse_args()
    if args.joints < 1 or not math.isfinite(args.max_abs_rad) or args.max_abs_rad <= 0:
        parser.error("joints and finite max-abs-rad must be positive")
    try:
        print(json.dumps(inspect(args.path, args.joints, args.max_abs_rad)))
    except (OSError, ValueError) as exc:
        print(f"CSV invalid: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
