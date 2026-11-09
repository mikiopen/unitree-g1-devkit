"""A complete, bounded, two-device UDP mock; all sockets stay on loopback."""
import json
import math
import socket
import threading
import time
from .protocol import PROTOCOL, decode, decode_reply, packet


class Simulator:
    def __init__(self, robot_id):
        if not isinstance(robot_id, str) or not robot_id or len(robot_id) > 128 or robot_id == 'all':
            raise ValueError('robot_id must be a non-empty ID up to 128 characters, other than all')
        self.robot_id = robot_id
        self.mode = 'mock'
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('127.0.0.1', 0))
        self.endpoint = self.socket.getsockname()
        self.socket.settimeout(0.05)
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self.serve, daemon=True)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *_):
        self.stop.set()
        self.thread.join(timeout=1)
        self.socket.close()

    def serve(self):
        while not self.stop.is_set():
            try:
                # Windows raises WSAEMSGSIZE rather than returning a truncated datagram.
                raw, sender = self.socket.recvfrom(65535)
            except (socket.timeout, ConnectionResetError):
                continue
            try:
                data = decode(raw)
                if data['target'] not in ('all', self.robot_id):
                    continue
                if data['command'] == 'stop_demo':
                    self.mode = 'idle'
                response = {'protocol': PROTOCOL, 'request_id': data['request_id'], 'robot_id': self.robot_id,
                            'command': data['command'], 'source': 'synthetic', 'motion_executed': False,
                            'battery_percent': 80, 'mode': self.mode}
                if data['command'] == 'echo':
                    response['text'] = data.get('text', '')
                self.socket.sendto(json.dumps(response).encode(), sender)
            except (ValueError, KeyError, TypeError, UnicodeError):
                continue


def exchange(endpoints, target, command, text='', timeout=0.4):
    """Return matched replies and unmatched endpoints, without guessing why a peer was silent."""
    if type(timeout) not in (int, float) or not math.isfinite(timeout) or not 0 < timeout <= 5:
        raise ValueError('timeout must be within (0, 5] seconds')
    endpoints = list(endpoints)
    if not endpoints:
        raise ValueError('At least one mock endpoint is required')
    normalized = []
    for endpoint in endpoints:
        if not isinstance(endpoint, (tuple, list)) or len(endpoint) != 2:
            raise ValueError('Endpoints must be host/port pairs')
        host, port = endpoint
        if host != '127.0.0.1' or type(port) is not int or not 1 <= port <= 65535:
            raise ValueError('Mock client accepts only IPv4 loopback endpoints')
        normalized.append((host, port))
    if len(set(normalized)) != len(normalized):
        raise ValueError('Duplicate mock endpoint')
    endpoints = normalized
    data = packet(target, command, text)
    replies = {}
    ignored = 0
    started = time.monotonic()
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client:
        client.bind(('127.0.0.1', 0))
        for endpoint in endpoints:
            client.sendto(json.dumps(data).encode(), endpoint)
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            client.settimeout(max(0.001, deadline - time.monotonic()))
            try:
                raw, sender = client.recvfrom(65535)
                if sender not in endpoints:
                    ignored += 1
                    continue
                reply = decode_reply(raw, data)
                if sender not in replies and any(r['robot_id'] == reply['robot_id'] for r in replies.values()):
                    ignored += 1
                    continue
                replies[sender] = reply
                if len(replies) == len(endpoints):
                    break
            except (socket.timeout, ConnectionResetError):
                continue
            except (ValueError, KeyError, TypeError, UnicodeError):
                ignored += 1
    return {'request_id': data['request_id'], 'command': command, 'target': target,
            'responses': sorted(replies.values(), key=lambda reply: reply['robot_id']),
            'unmatched_endpoints': [f'{host}:{port}' for host, port in endpoints if (host, port) not in replies],
            'ignored_datagrams': ignored, 'elapsed_ms': round((time.monotonic() - started) * 1000, 3),
            'all_endpoints_replied': len(replies) == len(endpoints), 'motion_executed': False,
            'silence_note': 'No matching reply may mean target filtering, packet loss, timeout or an unavailable peer'}


def request(endpoints, target, command, text='', timeout=0.4):
    return exchange(endpoints, target, command, text, timeout)['responses']


def demo():
    with Simulator('g1-a') as a, Simulator('g1-b') as b:
        endpoints = [a.endpoint, b.endpoint]
        exchanges = [exchange(endpoints, 'all', 'status'),
                     exchange(endpoints, 'g1-b', 'echo', '你好，G1'),
                     exchange(endpoints, 'all', 'stop_demo'),
                     exchange(endpoints, 'all', 'status')]
        results = [item['responses'] for item in exchanges]
        expected = [['g1-a', 'g1-b'], ['g1-b'], ['g1-a', 'g1-b']]
        if [[r['robot_id'] for r in batch] for batch in results[:3]] != expected:
            raise RuntimeError('Mock round-trip or target filtering failed')
        if len(results[3]) != 2 or any(reply['mode'] != 'idle' for reply in results[3]):
            raise RuntimeError('Mock stop state did not persist')
        return {'profile': 'mock', 'passed': True, 'motion_executed': False,
                'steps': dict(zip(('discover_status', 'target_echo', 'stop_demo', 'status_after_stop'), results)),
                'exchanges': exchanges}
