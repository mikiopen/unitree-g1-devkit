"""Portable checks for public teaching docs and scripts; no device or external network."""
import ast
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]


def main():
    errors = []
    docs = [ROOT / "README.md", ROOT / "CONTRIBUTING.md", ROOT / "examples/README.md",
            ROOT / "adapters/reference/README.md", ROOT / "third-party-notices/README.md",
            *sorted((ROOT / "docs").rglob("*.md"))]
    for doc in docs:
        if not doc.exists():
            errors.append(f"Missing guide: {doc.relative_to(ROOT)}")
            continue
        content = re.sub(r"```.*?```", "", doc.read_text(encoding="utf-8"), flags=re.S)
        # Support ordinary relative links that contain one parenthesized segment.
        pattern = r"\]\((<[^>]+>|[^()\n]+(?:\([^()\n]*\)[^()\n]*)*)\)"
        for target in re.findall(pattern, content):
            target = target.strip("<>")
            if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target) or target.startswith("#"):
                continue
            path = doc.parent / unquote(target.split("#")[0])
            if not path.exists():
                errors.append(f"Missing link: {doc.relative_to(ROOT)} -> {target}")
    scripts = [*sorted((ROOT / "examples").rglob("*.py")),
               *sorted((ROOT / "adapters").rglob("*.py")),
               ROOT / "g1.py", *sorted((ROOT / "g1devkit").glob("*.py")),
               *sorted((ROOT / "tools").glob("*.py")), *sorted((ROOT / "tests").glob("*.py"))]
    for script in scripts:
        try:
            ast.parse(script.read_text(encoding="utf-8"), filename=str(script))
        except SyntaxError as exc:
            errors.append(str(exc))
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1")

    def run(arguments, expected=0):
        result = subprocess.run([sys.executable, *map(str, arguments)], cwd=ROOT, env=env,
                                capture_output=True, text=True, encoding="utf-8", timeout=30)
        if result.returncode != expected:
            errors.append(f"Command {arguments}: exit {result.returncode}\n{result.stderr}")
        return result

    run(["tools/check_course.py"])
    run(["tools/check_environment.py", "--profile", "pc"])
    run(["g1.py", "doctor"])
    run(["g1.py", "demo"])
    run(["g1.py", "plan"])
    run(["g1.py", "preflight"], expected=1)
    run(["g1.py", "inspect-action", "adapters/reference/actions/init.json", "--dof", "29"])
    run(["g1.py", "state", "--duration", "nan"], expected=2)
    run(["g1.py", "state", "--dds"], expected=2)
    synthetic = run(["examples/03-state-reader/read_state.py", "--duration", "0.05"])
    if synthetic.returncode == 0:
        if json.loads(synthetic.stdout.splitlines()[0]).get("source") != "synthetic":
            errors.append("Default state reader was not synthetic")
    run(["examples/05-action-data/inspect_csv.py", "examples/05-action-data/toy.csv",
         "--joints", "2", "--max-abs-rad", "1"])
    run(["examples/10-command-router/route_text.py", "查询状态"])
    run(["examples/10-command-router/route_text.py", "向前走"], expected=1)
    run(["examples/09-asr-demo/transcribe_file.py", "missing.wav", "--model", "missing-model"], expected=2)
    with tempfile.TemporaryDirectory() as temporary:
        audio = Path(temporary) / "tone.wav"
        run(["examples/08-audio-demo/audio_file.py", "create", "--output", audio])
        result = run(["examples/08-audio-demo/audio_file.py", "inspect", audio])
        if result.returncode == 0:
            properties = json.loads(result.stdout)
            if (properties["channels"], properties["sample_rate_hz"], properties["duration_s"]) != (1, 16000, 1):
                errors.append("Generated audio has unexpected properties")
    tests = run(["-m", "unittest", "discover", "-s", "tests", "-v"])
    print(tests.stderr.strip())
    print(json.dumps({"guides_checked": len(docs), "scripts_parsed": len(scripts),
                      "errors": errors}, ensure_ascii=False, indent=2))
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
