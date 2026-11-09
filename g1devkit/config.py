"""One validated configuration shared by the CLI and installation plan."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path=None):
    path = Path(path) if path else ROOT / 'configs/devkit.example.json'
    data = json.loads(path.read_text(encoding='utf-8-sig'))
    if not isinstance(data, dict):
        raise ValueError('Configuration must be a JSON object')
    if data.get('schema_version') != 1 or data.get('profile') != 'reference':
        raise ValueError('Only schema 1 / reference is supported by the maintained entry point')
    robot = data.get('robot', {})
    if not isinstance(robot, dict):
        raise ValueError('robot must be an object')
    if robot.get('dof') is not None and (type(robot['dof']) is not int or robot['dof'] not in (23, 29)):
        raise ValueError('robot.dof must be 23, 29 or null')
    for key in ('model', 'firmware', 'interface', 'sdk_commit'):
        if robot.get(key) is not None and (not isinstance(robot[key], str) or not robot[key].strip()):
            raise ValueError('robot.' + key + ' must be a non-empty string or null')
    if robot.get('sdk_commit') is not None and not re.fullmatch(r'[0-9a-fA-F]{40}', robot['sdk_commit']):
        raise ValueError('robot.sdk_commit must be a full 40-character Git commit')
    if robot.get('state_topic') not in ('rt/lowstate', 'rt/lf/lowstate'):
        raise ValueError('robot.state_topic must be rt/lowstate or rt/lf/lowstate')
    ports = data.get('ports', {})
    if not isinstance(ports, dict) or set(ports) != {'command', 'status', 'action'}:
        raise ValueError('Define command, status and action ports')
    if any(type(p) is not int or not 1024 <= p <= 65535 for p in ports.values()):
        raise ValueError('Ports must be integers in [1024, 65535]')
    if len(set(ports.values())) != 3:
        raise ValueError('Service ports must be distinct')
    services = data.get('services')
    if not isinstance(services, dict) or set(services) != {'controller', 'subscriber', 'action'}:
        raise ValueError('Define the three baseline services')
    for name, relative in services.items():
        if not isinstance(relative, str) or not relative.strip():
            raise ValueError('Service paths must be non-empty strings: ' + name)
        target = (ROOT / relative).resolve()
        if not target.is_relative_to(ROOT) or not target.exists():
            raise ValueError('Service path must exist inside the repository: ' + name)
        if (name == 'controller' and not target.is_dir()) or (name != 'controller' and not target.is_file()):
            raise ValueError('controller must be a directory and subscriber/action must be files')
    resources = data.get('resources')
    if not isinstance(resources, dict) or set(resources) != {'vosk_model', 'actions', 'logs'}:
        raise ValueError('Define vosk_model, actions and logs resource paths')
    for relative in resources.values():
        if not isinstance(relative, str) or not relative.strip() or not (ROOT / relative).resolve().is_relative_to(ROOT):
            raise ValueError('Resource paths must stay inside the repository')
    return data


def hardware_missing(data):
    robot = data['robot']
    return [key for key in ('model', 'dof', 'firmware', 'interface', 'sdk_commit') if not robot.get(key)]
