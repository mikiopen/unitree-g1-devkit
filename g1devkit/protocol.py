"""Validate teaching packets and inspect the selected legacy App wire format."""
import ipaddress
import json
import math
import uuid

MAX_PACKET = 4096
COMMANDS = {'status', 'echo', 'stop_demo'}
PROTOCOL = 'g1devkit/mock/v1'


def _json_packet(raw):
    def nonfinite(value):
        raise ValueError('Nonfinite JSON number: ' + value)

    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate JSON field: ' + key)
            result[key] = value
        return result

    try:
        return json.loads(raw.decode('utf-8'), parse_constant=nonfinite, object_pairs_hook=unique)
    except RecursionError as error:
        raise ValueError('JSON nesting exceeds the parser limit') from error


def packet(target, command, text=''):
    data = {'protocol': PROTOCOL, 'request_id': str(uuid.uuid4()),
            'target': target, 'command': command, 'text': text}
    decode(json.dumps(data).encode())
    return data


def decode(raw):
    if len(raw) > MAX_PACKET:
        raise ValueError('Packet exceeds 4096 bytes')
    data = _json_packet(raw)
    if not isinstance(data, dict) or data.get('protocol') != PROTOCOL:
        raise ValueError('Unknown teaching protocol')
    if not isinstance(data.get('command'), str) or data['command'] not in COMMANDS:
        raise ValueError('Command outside teaching allowlist')
    if not isinstance(data.get('target'), str) or not data['target']:
        raise ValueError('Missing target')
    if not isinstance(data.get('request_id'), str):
        raise ValueError('request_id must be a UUID string')
    uuid.UUID(data['request_id'])
    if not isinstance(data.get('text', ''), str) or len(data.get('text', '')) > 256:
        raise ValueError('Text must contain at most 256 characters')
    return data


def decode_reply(raw, sent):
    """Accept only a correlated synthetic response; never label arbitrary JSON as success."""
    if len(raw) > MAX_PACKET:
        raise ValueError('Reply exceeds 4096 bytes')
    reply = _json_packet(raw)
    if not isinstance(reply, dict) or reply.get('protocol') != PROTOCOL:
        raise ValueError('Unknown reply protocol')
    if reply.get('request_id') != sent['request_id'] or reply.get('command') != sent['command']:
        raise ValueError('Reply does not match request')
    robot_id = reply.get('robot_id')
    if not isinstance(robot_id, str) or not robot_id or len(robot_id) > 128:
        raise ValueError('Invalid robot_id')
    if sent['target'] not in ('all', robot_id):
        raise ValueError('Reply from an unrequested robot')
    if reply.get('source') != 'synthetic' or reply.get('motion_executed') is not False:
        raise ValueError('Reply must explicitly identify itself as a non-motion mock')
    if reply.get('mode') not in ('mock', 'idle'):
        raise ValueError('Invalid mock mode')
    battery = reply.get('battery_percent')
    if type(battery) is not int or not 0 <= battery <= 100:
        raise ValueError('Invalid synthetic battery percentage')
    if sent['command'] == 'echo' and reply.get('text') != sent.get('text', ''):
        raise ValueError('Echo payload mismatch')
    if sent['command'] == 'stop_demo' and reply['mode'] != 'idle':
        raise ValueError('Mock stop must report idle')
    return reply


def inspect_legacy(text):
    """Parse without sending: numbers and velocity triples can move a real G1."""
    if len(text.encode('utf-8')) > MAX_PACKET:
        raise ValueError('Packet too large')
    target = 'all'
    if text.startswith('TARGET:'):
        _, target, text = text.split(':', 2)
        ipaddress.IPv4Address(target)
    elif text.startswith('ALL:'):
        text = text[4:]
    if ',' in text:
        values = [float(value) for value in text.split(',')]
        if len(values) != 3 or not all(math.isfinite(value) for value in values):
            raise ValueError('Expected three finite velocities')
        return {'target': target, 'kind': 'velocity', 'order': ['vy', 'vx', 'yaw'], 'values': values,
                'motion_possible': True, 'sent': False}
    command = int(text)
    return {'target': target, 'kind': 'integer', 'command': command,
            'motion_possible': command != 9999, 'sent': False}
