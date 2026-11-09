"""Negative-path checks plus real loopback multi-device integration."""
import importlib.util
import json
import os
from pathlib import Path
import queue
import socket
import subprocess
import sys
import tempfile
import threading
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


udp = load("learning_udp", "examples/06-udp-demo/udp_demo.py")
csv_tool = load("learning_csv", "examples/05-action-data/inspect_csv.py")
router = load("learning_router", "examples/10-command-router/route_text.py")


class DataTests(unittest.TestCase):
    def test_csv_invalid_time_nan_columns_and_bounds(self):
        invalid_rows = ["0,0,0\n0,0,0\n", "0,0,0\n1,nan,0\n",
                        "0,0,0\n1,0\n", "0,0,0\n1,3,0\n"]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.csv"
            for rows in invalid_rows:
                with self.subTest(rows=rows):
                    path.write_text("time_s,q0_rad,q1_rad\n" + rows, encoding="utf-8")
                    with self.assertRaises(ValueError):
                        csv_tool.inspect(path, 2, 1)
            path.write_text("0,0,0\n1,0,0\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                csv_tool.inspect(path, 2, 1)

    def test_toy_is_schema_only(self):
        result = csv_tool.inspect(ROOT / "examples/05-action-data/toy.csv", 2, 1)
        self.assertEqual(result["rows"], 3)
        self.assertFalse(result["motion_validated"])

    def test_router_rejects_unknown_and_unsafe_mapping(self):
        mapping = {"查询状态": "status"}
        self.assertTrue(router.route("查询状态", mapping)["accepted"])
        self.assertFalse(router.route("查询状态并向前走", mapping)["accepted"])
        with self.assertRaises(ValueError):
            router.route("走", {"走": "move"})


class UDPTests(unittest.TestCase):
    def setUp(self):
        self.processes = []
        self.endpoints = []
        self.env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1")

    def tearDown(self):
        for process in self.processes:
            if process.poll() is None:
                process.terminate()
            try:
                process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate()

    def start_receiver(self, robot_id):
        process = subprocess.Popen([sys.executable, str(ROOT / "examples/06-udp-demo/udp_demo.py"),
                                    "serve", "--robot-id", robot_id, "--port", "0"],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                   encoding="utf-8", env=self.env)
        self.processes.append(process)
        ready = queue.Queue()
        threading.Thread(target=lambda: ready.put(process.stdout.readline()), daemon=True).start()
        try:
            line = ready.get(timeout=8)
        except queue.Empty:
            self.fail("receiver failed to become ready within 8 seconds")
        data = json.loads(line)
        self.assertEqual(data["event"], "ready")
        address = ("127.0.0.1", data["port"])
        self.endpoints.append(address)
        return address

    def test_two_receivers_all_and_single_target(self):
        first = self.start_receiver("g1-a")
        self.start_receiver("g1-b")
        result = udp.send(self.endpoints, "all", "status", "", 2)
        self.assertFalse(result["missing_endpoints"])
        self.assertEqual({r["robot_id"] for r in result["replies"]}, {"g1-a", "g1-b"})
        targeted = udp.send(self.endpoints, "g1-a", "echo", "你好", 0.3)
        self.assertEqual([r["robot_id"] for r in targeted["replies"]], ["g1-a"])
        self.assertEqual(targeted["replies"][0]["text"], "你好")
        self.assertEqual(len(targeted["missing_endpoints"]), 1)
        stop = udp.send([first], "g1-a", "stop_demo", "", 1)
        self.assertFalse(stop["replies"][0]["motion_executed"])
        self.assertIsNone(self.processes[0].poll())

    def test_malformed_datagrams_do_not_kill_receiver(self):
        address = self.start_receiver("g1-a")
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            for raw in (b"{", b"[]", b"\xff", b"x" * 4097):
                sock.sendto(raw, address)
        result = udp.send([address], "g1-a", "status", "", 1)
        self.assertEqual(len(result["replies"]), 1)

    def test_terminated_receiver_is_reported_missing(self):
        address = self.start_receiver("g1-a")
        self.processes[0].terminate()
        self.processes[0].wait(timeout=5)
        result = udp.send([address], "all", "status", "", 0.1)
        self.assertEqual(result["replies"], [])
        self.assertEqual(len(result["missing_endpoints"]), 1)

    def test_non_loopback_and_invalid_protocol_rejected(self):
        with self.assertRaises(ValueError):
            udp.endpoint("192.0.2.1:2006")
        with self.assertRaises(ValueError):
            udp.handle({"schema": "legacy"}, "g1-a")
        with self.assertRaises(ValueError):
            udp.encode({"text": "x" * 5000})


if __name__ == "__main__":
    unittest.main()
