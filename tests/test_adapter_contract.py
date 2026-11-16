import unittest
import uuid

from g1devkit.adapter import (Capability, DeviceAdapter, Observation, ReferenceAdapter,
                              TaskEvent, TaskRequest, TaskState, contract_demo)


class AdapterContractTests(unittest.TestCase):
    def test_contract_demo_is_non_motion_and_covers_replay_and_rejection(self):
        report = contract_demo(now_ms=1000)
        self.assertFalse(report["network_accessed"])
        self.assertFalse(report["motion_executed"])
        self.assertTrue(report["idempotent_replay"])
        self.assertEqual(report["status_event"]["state"], "succeeded")
        self.assertEqual(report["unsupported_event"]["state"], "rejected")

    def test_status_echo_and_capabilities(self):
        adapter = ReferenceAdapter("g1-test")
        self.assertIsInstance(adapter, DeviceAdapter)
        capability = adapter.capabilities()
        self.assertEqual(capability.operations, ("status", "echo"))
        self.assertFalse(capability.motion_capable)
        status = TaskRequest.create("g1-test", "status", now_ms=100)
        event = adapter.submit(status, now_ms=101)
        self.assertEqual(event.state, TaskState.SUCCEEDED)
        self.assertEqual(event.result["mode"], "mock")
        echo = TaskRequest.create("g1-test", "echo", {"text": "hello"}, now_ms=100)
        self.assertEqual(adapter.submit(echo, now_ms=101).result["text"], "hello")

    def test_expired_unknown_and_invalid_echo_are_explicit_rejections(self):
        adapter = ReferenceAdapter()
        expired = TaskRequest.create(adapter.device_id, "status", timeout_ms=1, now_ms=100)
        wrong = TaskRequest.create("other", "status", now_ms=100)
        invalid = TaskRequest.create(adapter.device_id, "echo", {}, now_ms=100)
        future = TaskRequest.create(adapter.device_id, "status", now_ms=200)
        for request, error in ((expired, "deadline"), (wrong, "unknown device"),
                               (invalid, "echo.text"), (future, "future")):
            with self.subTest(error=error):
                event = adapter.submit(request, now_ms=102)
                self.assertEqual(event.state, TaskState.REJECTED)
                self.assertIn(error, event.error)

    def test_same_request_is_idempotent_but_uuid_reuse_with_new_content_is_rejected(self):
        adapter = ReferenceAdapter()
        ident = str(uuid.uuid4())
        first = TaskRequest.create(adapter.device_id, "status", request_id=ident, now_ms=100)
        first_event = adapter.submit(first, now_ms=101)
        self.assertIs(adapter.submit(first, now_ms=102), first_event)
        changed = TaskRequest.create(adapter.device_id, "echo", {"text": "x"},
                                     request_id=ident, now_ms=100)
        with self.assertRaisesRegex(ValueError, "reused"):
            adapter.submit(changed, now_ms=102)

    def test_models_reject_invalid_time_json_and_identity(self):
        with self.assertRaises(ValueError):
            TaskRequest.create("g1", "status", timeout_ms=True)
        with self.assertRaises(ValueError):
            TaskRequest.create("g1", "status", {"bad": float("nan")})
        with self.assertRaises(ValueError):
            ReferenceAdapter(" all ")
        with self.assertRaises(ValueError):
            Observation("g1", "status", {}, 2, 1, "test", True)
        with self.assertRaises(ValueError):
            Capability("g1", "test", ("status", "status"), True, False)
        with self.assertRaises(ValueError):
            TaskEvent(str(uuid.uuid4()), "g1", "status", TaskState.SUCCEEDED, 1,
                      simulation=True, motion_executed=True)
        with self.assertRaises(ValueError):
            TaskEvent(str(uuid.uuid4()), "g1", "status", TaskState.REJECTED, 1)

    def test_payloads_are_copied_and_read_only(self):
        parameters = {"text": "safe", "nested": {"items": [1, 2]}}
        request = TaskRequest.create("g1", "echo", parameters, now_ms=1)
        parameters["text"] = "changed"
        parameters["nested"]["items"].append(3)
        self.assertEqual(request.parameters["text"], "safe")
        self.assertEqual(request.to_dict()["parameters"]["nested"]["items"], [1, 2])
        with self.assertRaises(TypeError):
            request.parameters["text"] = "mutated"
        with self.assertRaises(AttributeError):
            request.parameters["nested"]["items"].append(3)


if __name__ == "__main__":
    unittest.main()
