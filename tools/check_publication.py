"""Check that the current tree stays inside the public learning-framework boundary."""
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_ROOTS = ("apps/", "modules/")
FORBIDDEN_NAMES = {
    "private-sync.md", "source-manifest.json", "extension-manifest.json",
    "credential-migration.json", "version-history.md", "validation-record.json",
}
TEXT_SUFFIXES = {".md", ".py", ".json", ".yaml", ".yml", ".toml", ".txt", ".ini", ".conf"}
PERSONAL_PATH = re.compile(r"(?i)(?:[A-Z]:\\Users\\[^\\\s]+|/home/[^/\s]+|/Users/[^/\s]+)")
EMAIL = re.compile(r"(?<![\w.+-])[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}(?![\w.-])", re.I)


def publication_candidates():
    result = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
                            cwd=ROOT, capture_output=True, check=True)
    return sorted(name.decode("utf-8") for name in result.stdout.split(b"\0") if name)


def main():
    findings = []
    names = publication_candidates()
    for name in names:
        normalized = name.replace("\\", "/")
        if normalized.startswith(FORBIDDEN_ROOTS):
            findings.append({"file": name, "category": "forbidden_root"})
        if Path(normalized).name in FORBIDDEN_NAMES:
            findings.append({"file": name, "category": "private_or_history_artifact"})
        path = ROOT / name
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if not normalized.startswith("tools/check_") and PERSONAL_PATH.search(line):
                findings.append({"file": name, "line": number, "category": "personal_directory"})
            if not normalized.startswith("tools/check_") and EMAIL.search(line):
                findings.append({"file": name, "line": number, "category": "email_address"})
    report = {"tracked_files": len(names), "findings": findings,
              "history_checked": False,
              "note": "A clean tree does not sanitize earlier Git commits."}
    destination = ROOT / ".local/publication-review.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"tracked_files": len(names), "findings": len(findings),
                      "report": str(destination.relative_to(ROOT)),
                      "history_checked": False}, ensure_ascii=False, indent=2))
    return int(bool(findings))


if __name__ == "__main__":
    raise SystemExit(main())
