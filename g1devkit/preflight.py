"""Offline configuration/resource review via AST; never import adapter programs."""
import ast
from collections import Counter
from pathlib import Path, PurePosixPath
from .actions import inspect_action
from .config import ROOT, hardware_missing


def read_source(path):
    tree = ast.parse(Path(path).read_text(encoding='utf-8-sig'), filename=str(path))
    constants = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    try:
                        constants[target.id] = ast.literal_eval(node.value)
                    except (ValueError, TypeError):
                        pass
    interfaces = []
    action_maps = []
    forward_endpoints = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == 'forward_to_action_service':
            for call in ast.walk(node):
                if isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute) and call.func.attr == 'sendto' and len(call.args) >= 2:
                    try:
                        forward_endpoints.append(ast.literal_eval(call.args[1]))
                    except (ValueError, TypeError):
                        pass
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'ChannelFactoryInitialize':
            if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
                interfaces.append(node.args[1].value)
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Attribute) and t.attr == 'action_map'
                                              and isinstance(t.value, ast.Name) and t.value.id == 'self'
                                              for t in node.targets):
            try:
                action_maps.append(ast.literal_eval(node.value))
            except (ValueError, TypeError):
                raise ValueError('action_map is not a static literal; review the selected source')
    if len(action_maps) > 1:
        raise ValueError('Multiple action_map definitions; select a single service version')
    return {'constants': constants, 'dds_interfaces': sorted(set(interfaces)), 'forward_endpoints': forward_endpoints,
            'action_map': action_maps[0] if action_maps else None}


def preflight(config, actions_dir=None):
    checks = []

    def add(name, status, detail):
        checks.append({'check': name, 'status': status, 'detail': detail})

    missing = hardware_missing(config)
    add('device_baseline', 'blocked' if missing else 'pass', {'missing': missing})
    sources = {}
    for name in ('subscriber', 'action'):
        try:
            sources[name] = read_source(ROOT / config['services'][name])
            add(name + '_source', 'pass', 'AST parsed without importing or executing the program')
        except (OSError, UnicodeError, SyntaxError, ValueError) as error:
            add(name + '_source', 'blocked', str(error))
    for name, source in sources.items():
        for constant, field in ({'UDP_RECV_PORT': 'command', 'UDP_SEND_PORT': 'status'}
                                if name == 'subscriber' else {'UDP_PORT': 'action'}).items():
            actual = source['constants'].get(constant)
            expected = config['ports'][field]
            add(name + '_' + field + '_port', 'pass' if type(actual) is int and actual == expected else 'blocked',
                {'configured': expected, 'source_literal': actual})
        actual = source['dds_interfaces']
        interface = config['robot'].get('interface')
        add(name + '_dds_interface', 'pass' if interface and actual == [interface] else 'blocked',
            {'configured': interface, 'source_literals': actual})
    action = sources.get('action')
    subscriber = sources.get('subscriber')
    if subscriber:
        expected = ('127.0.0.1', config['ports']['action'])
        add('subscriber_action_forward', 'pass' if subscriber['forward_endpoints'] == [expected] else 'blocked',
            {'configured': list(expected), 'source_literals': subscriber['forward_endpoints']})
    if action:
        add('action_listener', 'warning' if action['constants'].get('UDP_IP') != '127.0.0.1' else 'pass',
            {'source_literal': action['constants'].get('UDP_IP'),
             'note': 'Legacy action listener is separate from the loopback-only teaching runtime; restrict access on the target device'})
    action_map = action['action_map'] if action else None
    reviewed = []
    candidates = []
    directory = Path(actions_dir) if actions_dir is not None else ROOT / config['resources']['actions']
    if not isinstance(action_map, dict) or not action_map:
        add('action_map', 'blocked', 'No unambiguous literal action_map found')
    elif not directory.is_dir():
        add('action_directory', 'blocked', 'Selected action resource directory does not exist')
    else:
        names = {p.name for p in directory.iterdir() if p.is_file()}
        dof = config['robot'].get('dof')
        if dof is None:
            add('action_dof', 'blocked', 'Record 23/29 DOF before checking action target layout; file availability is still reviewed')
        for command, entry in sorted(action_map.items()):
            if isinstance(entry, dict) and entry.get('type') == 'emergency_stop' and 'path' not in entry:
                add('control_' + str(command), 'pass', 'Literal control entry; no action file needed. Stop behavior remains unverified')
                continue
            if not isinstance(entry, dict) or not isinstance(entry.get('path'), str):
                add('action_' + str(command), 'blocked', 'action_map entry has no literal path')
                continue
            filename = PurePosixPath(entry['path']).name + '.json'
            # Exact case matters on the target Linux machine, even if reviewed on Windows.
            if filename not in names:
                add('action_' + str(command), 'blocked', {'file': filename, 'reason': 'missing or different filename case'})
                continue
            candidates.append({'command': command, 'file': filename})
            if dof is None:
                continue
            try:
                report = inspect_action(directory / filename, dof)
                reviewed.append({'command': command, **report})
                add('action_' + str(command), 'pass', {'file': filename, 'stages': report['stages']})
            except (OSError, ValueError, OverflowError) as error:
                add('action_' + str(command), 'blocked', {'file': filename, 'reason': str(error)})
        add('action_resource_mapping', 'warning',
            'Inspected local filenames by basename; real device paths must be mapped by the deployment adapter')
    counts = dict(Counter(check['status'] for check in checks))
    return {'profile': config['profile'], 'kind': 'offline-preflight', 'checks': checks,
            'summary': counts, 'offline_checks_passed': not counts.get('blocked'),
            'action_files': reviewed, 'available_action_files': candidates,
            'adapter_programs_executed': False, 'network_accessed': False,
            'motion_validated': False,
            'limits': 'No network, firmware, physical device, collision, external credentials or stop behavior verification'}
