"""Optional WAV -> local ASR -> exact allowlist -> loopback mock status."""
import json
import re
import subprocess
import sys
from .config import ROOT
from .runtime import Simulator, request


def normalize(text):
    # Vosk emits spaces between Chinese tokens. Do not fuzzy-match or merge commands.
    return re.sub(r'(?<=[\u3400-\u9fff])\s+(?=[\u3400-\u9fff])', '', text).strip()


def run(audio, model):
    result = subprocess.run([sys.executable, str(ROOT/'examples/09-asr-demo/transcribe_file.py'),
                             str(audio), '--model', str(model)],
                            cwd=ROOT, capture_output=True, text=True, encoding='utf-8', timeout=120)
    if result.returncode:
        raise ValueError('ASR failed; verify dependencies, WAV format and an extracted model in an ASCII path')
    texts = [json.loads(line).get('text','') for line in result.stdout.splitlines() if line.strip()]
    raw = ' '.join(texts).strip()
    normalized = normalize(raw)
    mapping = json.loads((ROOT/'configs/command-map.example.json').read_text(encoding='utf-8'))
    if not isinstance(mapping,dict) or any(not isinstance(k,str) or v not in ('status','stop_demo') for k,v in mapping.items()):
        raise ValueError('Invalid voice allowlist')
    command = mapping.get(normalized)
    report = {'raw_text': raw, 'normalized_text': normalized, 'accepted': command is not None,
              'command': command, 'motion_executed': False, 'responses': []}
    if command:
        with Simulator('voice-g1') as simulator:
            report['responses'] = request([simulator.endpoint], 'voice-g1', command)
        if not report['responses']:
            raise RuntimeError('No loopback mock response')
    return report
