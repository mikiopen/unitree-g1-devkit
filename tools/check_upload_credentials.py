"""Heuristic credential scan of Git candidates; reports locations, never values."""
import argparse
import ipaddress
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
TEXT = {".py", ".cpp", ".c", ".h", ".hpp", ".dart", ".sh", ".ps1", ".md", ".txt",
        ".yaml", ".yml", ".json", ".toml", ".ini", ".conf", ".service", ".env", ".xml", ".html"}
PATTERNS = {
    "credential_literal": re.compile(
        r'''(?i)\b(?:[a-z0-9]*_)?(?:api[_-]?key|api[_-]?secret|app[_-]?secret|app[_-]?id|password|passwd|secret[_-]?key|access[_-]?token|auth[_-]?token|private[_-]?key)\b[\s'"\]]*[:=]\s*['"]([^'"\r\n]+)['"]'''),
    "service_token": re.compile(r"\b(?:sk-[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[A-Z0-9]{16})\b"),
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "url_credentials": re.compile(r"(?:https?|redis|postgres(?:ql)?|mysql)://[^\s/:]+:[^\s/@]+@"),
    "email_address": re.compile(r"(?<![\w.+-])[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}(?![\w.-])", re.I),
    "personal_directory": re.compile(r"(?i)(?:[A-Z]:\\Users\\[^\\\s]+|/home/[^/\s]+|/Users/[^/\s]+)"),
}

IPV4 = re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])")


def placeholder(value):
    lower = value.strip().lower()
    return (not lower or lower.startswith(("<", "${", "your_", "请输入", "请填写", "请替换"))
            or lower in {"xxx", "xxxx", "xxxxx", "password", "secret", "example", "changeme",
                         "change_me", "replace_me", "redacted", "string"}
            or set(lower) <= {"*"} or set(lower) <= {"x"})


def scan():
    result = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
                            cwd=ROOT, capture_output=True, check=True)
    names = sorted(set(name.decode("utf-8") for name in result.stdout.split(b"\0") if name))
    findings = []
    checked = 0
    for name in names:
        path = ROOT / name
        if not path.is_file() or path.suffix.lower() not in TEXT:
            continue
        checked += 1
        text = path.read_text(encoding="utf-8", errors="replace")
        for line, content in enumerate(text.splitlines(), 1):
            for category, pattern in PATTERNS.items():
                if category in {"email_address", "personal_directory"} and name.startswith("tools/check_"):
                    continue
                for match in pattern.finditer(content):
                    if (category == "credential_literal"
                            and re.fullmatch(r"\{[^{}\r\n]+\}", match.group(1))):
                        continue
                    if category != "credential_literal" or not placeholder(match.group(1)):
                        findings.append({"file": name, "line": line, "category": category})
            for match in IPV4.finditer(content):
                try:
                    address = ipaddress.ip_address(match.group(0))
                except ValueError:
                    continue
                if address.is_global:
                    findings.append({"file": name, "line": line, "category": "public_ipv4"})
    return {"files_checked": checked, "findings": findings,
            "note": "Heuristic findings require review; no credential values are stored. Private visibility does not replace review."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=ROOT / ".local/upload-review.json")
    args = parser.parse_args()
    report_path = args.report.resolve()
    if not report_path.is_relative_to((ROOT / ".local").resolve()):
        parser.error("reports must stay in the ignored .local directory")
    report = scan()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    counts = {}
    for finding in report["findings"]:
        counts[finding["category"]] = counts.get(finding["category"], 0) + 1
    print(json.dumps({"files_checked": report["files_checked"], "finding_counts": counts,
                      "report": str(report_path.relative_to(ROOT)), "values_printed": False},
                     ensure_ascii=False, indent=2))
    return int(bool(report["findings"]))


if __name__ == "__main__":
    raise SystemExit(main())
