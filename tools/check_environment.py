"""Report learning dependencies without starting any robot service."""
import argparse
import importlib.util
import json
import platform
import shutil
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=("pc", "robot", "voice", "app"), default="pc")
    args = parser.parse_args()
    checks = {"python_3_10_plus": sys.version_info >= (3, 10)}
    if args.profile == "robot":
        checks.update(linux=platform.system() == "Linux",
                      unitree_sdk2py=importlib.util.find_spec("unitree_sdk2py") is not None)
    elif args.profile == "voice":
        checks["vosk"] = importlib.util.find_spec("vosk") is not None
    elif args.profile == "app":
        checks["flutter_on_path"] = shutil.which("flutter") is not None
    print(json.dumps({"profile": args.profile, "system": platform.system(),
                      "python": platform.python_version(), "executable": sys.executable,
                      "checks": checks, "note": "Dependency presence does not verify hardware compatibility."},
                     ensure_ascii=False, indent=2))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
