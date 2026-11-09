import json
from pathlib import Path
import socket
import tempfile
import unittest
from g1devkit.config import ROOT, load
from g1devkit.protocol import decode, inspect_legacy, packet
from g1devkit.runtime import Simulator, demo, request
from g1devkit.voice import normalize


class DevkitTests(unittest.TestCase):
    def test_integrated_two_device_pipeline(self):
        result=demo()
        self.assertTrue(result['passed'])
        self.assertEqual(len(result['steps']['discover_status']), 2)
        self.assertEqual(result['steps']['target_echo'][0]['robot_id'], 'g1-b')
        self.assertTrue(all(not reply['motion_executed'] for batch in result['steps'].values() for reply in batch))

    def test_invalid_packets_do_not_kill_receiver(self):
        with Simulator('g1-a') as simulator:
            with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as client:
                for raw in [b'[]', b'\xff', b'x'*5000, b'[' * 1500 + b']' * 1500,
                            b'{"command":"status","command":"walk"}',
                            json.dumps(dict(packet('all','status'),request_id=42)).encode(),
                            json.dumps(dict(packet('all','status'),command='walk')).encode()]:
                    client.sendto(raw,simulator.endpoint)
            self.assertEqual(len(request([simulator.endpoint],'all','status')),1)

    def test_timeout_and_non_loopback(self):
        with Simulator('g1-a') as simulator:
            self.assertEqual(request([simulator.endpoint],'missing','status',timeout=0.02),[])
        with self.assertRaises(ValueError): request([('192.168.1.1',2006)],'all','status')

    def test_config_rejects_collision_and_path_escape(self):
        data=load()
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/'config.json'
            data['ports']['action']=data['ports']['command']
            path.write_text(json.dumps(data),encoding='utf-8')
            with self.assertRaises(ValueError): load(path)
            data=load(); data['services']['action']='../outside.py'
            path.write_text(json.dumps(data),encoding='utf-8')
            with self.assertRaises(ValueError): load(path)

    def test_legacy_packet_inspection_is_not_execution(self):
        status=inspect_legacy('TARGET:192.168.1.8:9999')
        self.assertFalse(status['motion_possible']); self.assertFalse(status['sent'])
        velocity=inspect_legacy('ALL:0,0.1,0')
        self.assertTrue(velocity['motion_possible']); self.assertFalse(velocity['sent'])
        with self.assertRaises(ValueError): inspect_legacy('0,nan,0')

    def test_asr_spacing_normalizes_chinese_only(self):
        self.assertEqual(normalize('查询 状态'), '查询状态')
        self.assertEqual(normalize('status stop'), 'status stop')
        self.assertNotEqual(normalize('查询状态 停止演示'), '查询状态')


if __name__=='__main__': unittest.main()
