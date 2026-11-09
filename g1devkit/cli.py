"""Unified entry: catalog, doctor, configuration plan, demo and read-only state."""
import argparse
import importlib.util
import json
import math
import platform
import subprocess
import sys
from .config import ROOT, hardware_missing, load
from .protocol import inspect_legacy
from .runtime import demo
from .reports import save_report


def emit(value):
    print(json.dumps(value, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', help='Local JSON configuration (copy example into .local)')
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('catalog')
    commands.add_parser('doctor')
    commands.add_parser('plan')
    demo_parser = commands.add_parser('demo')
    demo_parser.add_argument('--report', help='New JSON file inside .local/reports')
    preflight_parser = commands.add_parser('preflight', help='Offline source, port, interface and action review')
    preflight_parser.add_argument('--actions-dir', help='Local stage JSON directory; no deployment or motion')
    preflight_parser.add_argument('--report', help='New JSON file inside .local/reports')
    action_parser = commands.add_parser('inspect-action', help='Read-only stage JSON checker')
    action_parser.add_argument('path')
    action_parser.add_argument('--dof', type=int, choices=(23, 29), required=True)
    action_parser.add_argument('--max-abs-rad', type=float, help='Optional caller review bound, not hardware limits')
    wire = commands.add_parser('inspect-packet'); wire.add_argument('payload')
    state = commands.add_parser('state')
    state.add_argument('--dds', action='store_true')
    state.add_argument('--duration', type=float, default=1)
    commands.add_parser('gui')
    voice = commands.add_parser('voice')
    voice.add_argument('--audio', required=True)
    voice.add_argument('--model', required=True)
    args = parser.parse_args()
    try:
        config = load(args.config)
        if args.command == 'catalog':
            emit(json.loads((ROOT/'configs/modules.json').read_text(encoding='utf-8')))
        elif args.command == 'doctor':
            emit({'python': platform.python_version(), 'platform': platform.system(),
                  'config_valid': True, 'hardware_missing': hardware_missing(config),
                  'resources': {key: (ROOT/path).exists() for key, path in config['resources'].items()},
                  'optional_imports': {name: importlib.util.find_spec(name) is not None
                                      for name in ('unitree_sdk2py', 'vosk', 'redis', 'numpy', 'cv2')},
                  'adapter_programs_executed': False})
        elif args.command == 'plan':
            emit({'profile': config['profile'], 'ports': config['ports'], 'services': config['services'],
                  'startup_order': ['verify SDK and device baseline', 'read-only device state',
                                    'inspect action data and stop procedure', 'device adapter',
                                    'application interface'],
                  'hardware_missing': hardware_missing(config), 'executed': False,
                  'guide': 'docs/install.md', 'adapter_port_config': 'Source constants; match before deployment'})
        elif args.command == 'demo':
            result = demo()
            if args.report:
                result['saved_report'] = save_report(result, args.report)
            emit(result)
        elif args.command == 'preflight':
            from .preflight import preflight
            result = preflight(config, args.actions_dir)
            if args.report:
                result['saved_report'] = save_report(result, args.report)
            emit(result)
            return 0 if result['offline_checks_passed'] else 1
        elif args.command == 'inspect-action':
            from .actions import inspect_action
            emit(inspect_action(args.path, args.dof, args.max_abs_rad))
        elif args.command == 'inspect-packet':
            emit(inspect_legacy(args.payload))
        elif args.command == 'state':
            if not math.isfinite(args.duration) or not 0 < args.duration <= 300:
                raise ValueError('duration must be finite and within (0, 300] seconds')
            command = [sys.executable, str(ROOT/'examples/03-state-reader/read_state.py'), '--duration', str(args.duration)]
            if args.dds:
                missing = hardware_missing(config)
                if missing or platform.system() != 'Linux':
                    raise ValueError('DDS requires Linux and a filled device baseline: '+','.join(missing))
                command += ['--mode', 'dds', '--interface', config['robot']['interface'],
                            '--topic', config['robot']['state_topic']]
            return subprocess.run(command, cwd=ROOT, check=False).returncode
        elif args.command == 'gui':
            from .gui import start
            start()
        elif args.command == 'voice':
            from .voice import run
            result = run(args.audio, args.model)
            emit(result)
            return 0 if result['accepted'] else 1
        return 0
    except (ValueError, OSError, KeyError, TypeError, RuntimeError, subprocess.TimeoutExpired) as error:
        print(str(error), file=sys.stderr)
        return 2
