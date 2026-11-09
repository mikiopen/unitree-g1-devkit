"""Keep explicit, exclusive JSON reports in the ignored local report directory."""
import json
from pathlib import Path
from .config import ROOT


def save_report(value, path):
    target = Path(path).resolve()
    folder = (ROOT / '.local/reports').resolve()
    if not folder.is_relative_to(ROOT) or not target.is_relative_to(folder) or target.suffix.lower() != '.json':
        raise ValueError('Reports must be JSON files inside .local/reports')
    payload = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n'
    target.parent.mkdir(parents=True, exist_ok=True)
    # Refuse overwrites, including existing symlinks; do not destroy earlier evidence.
    with target.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(payload)
    return target.relative_to(ROOT).as_posix()
