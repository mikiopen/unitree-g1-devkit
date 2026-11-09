import json
import socket
import threading
import unittest

from g1devkit.protocol import PROTOCOL
from g1devkit.runtime import Simulator, exchange, request


class ReplyTests(unittest.TestCase):
    def test_untrusted_malformed_stale_or_motion_replies_are_ignored(self):
        errors = []
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server:
            server.bind(('127.0.0.1', 0))
            server.settimeout(2)

            def send_replies():
                try:
                    raw, sender = server.recvfrom(65535)
                    sent = json.loads(raw)
                    valid = {'protocol': PROTOCOL, 'request_id': sent['request_id'], 'command': 'status',
                             'robot_id': 'g1-a', 'source': 'synthetic', 'motion_executed': False,
                             'battery_percent': 80, 'mode': 'mock'}
                    invalid = [b'[]', b'null', b'\xff', b'x' * 5000,
                               b'[' * 1500 + b']' * 1500,
                               json.dumps(dict(valid, extra=float('nan'))).encode(),
                               json.dumps(dict(valid, request_id='stale')).encode(),
                               json.dumps(dict(valid, protocol='other')).encode(),
                               json.dumps(dict(valid, robot_id=['bad'])).encode(),
                               json.dumps(dict(valid, command='echo')).encode(),
                               json.dumps(dict(valid, motion_executed=True)).encode(),
                               json.dumps(dict(valid, battery_percent=True)).encode()]
                    for data in invalid:
                        server.sendto(data, sender)
                    server.sendto(json.dumps(valid).encode(), sender)
                except Exception as error:
                    errors.append(error)

            thread = threading.Thread(target=send_replies)
            thread.start()
            try:
                result = exchange([server.getsockname()], 'all', 'status', timeout=1)
            finally:
                thread.join(timeout=3)
            self.assertFalse(thread.is_alive())
            self.assertEqual(errors, [])
            self.assertTrue(result['all_endpoints_replied'])
            self.assertGreaterEqual(result['ignored_datagrams'], 12)
            self.assertEqual(result['responses'][0]['robot_id'], 'g1-a')

    def test_stop_persists_and_silence_is_not_claimed_as_device_failure(self):
        with Simulator('g1-a') as simulator:
            request([simulator.endpoint], 'g1-a', 'stop_demo')
            self.assertEqual(request([simulator.endpoint], 'g1-a', 'status')[0]['mode'], 'idle')
            result = exchange([simulator.endpoint], 'g1-b', 'status', timeout=0.02)
            self.assertEqual(result['responses'], [])
            self.assertEqual(len(result['unmatched_endpoints']), 1)
            self.assertIn('target filtering', result['silence_note'])
            self.assertFalse(result['all_endpoints_replied'])

    def test_empty_duplicate_and_invalid_endpoints_or_timeouts(self):
        for endpoints in ([], [('127.0.0.1', 19000)] * 2, [('127.0.0.1', True)], ['invalid']):
            with self.subTest(endpoints=endpoints):
                with self.assertRaises(ValueError):
                    exchange(endpoints, 'all', 'status')
        for timeout in (float('nan'), float('inf'), True, 0, -1):
            with self.subTest(timeout=timeout):
                with self.assertRaises(ValueError):
                    exchange([('127.0.0.1', 19000)], 'all', 'status', timeout=timeout)


if __name__ == '__main__':
    unittest.main()
