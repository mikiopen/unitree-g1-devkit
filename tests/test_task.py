import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from g1devkit.adapter import ReferenceAdapter
from g1devkit.task import PLAN_SCHEMA, run_task


class TaskTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.plan = Path(folder.name) / "plan.json"

    def write_plan(self, steps):
        self.plan.write_text(
            json.dumps({"schema": PLAN_SCHEMA, "steps": steps}),
            encoding="utf-8",
        )

    def test_rejection_skips_remaining_steps_without_submitting_them(self):
        self.write_plan([
            {"operation": "status"},
            {"operation": "echo", "parameters": {}},
            {"operation": "status"},
        ])
        adapter = ReferenceAdapter()
        with patch("g1devkit.task.ReferenceAdapter", return_value=adapter), \
                patch.object(adapter, "submit", wraps=adapter.submit) as submit:
            report = run_task(self.plan)
        self.assertEqual(submit.call_count, 2)
        self.assertEqual([step["state"] for step in report["steps"]],
                         ["succeeded", "rejected", "skipped"])
        self.assertIn("echo.text", report["steps"][1]["event"]["error"])
        self.assertEqual(report["steps"][2]["blocked_by_step"], 2)
        self.assertNotIn("event", report["steps"][2])
        self.assertFalse(report["passed"])

    def test_invalid_later_step_prevents_any_submission(self):
        self.write_plan([{"operation": "status"}, {"operation": "echo", "parameters": []}])
        with patch("g1devkit.task.ReferenceAdapter.submit") as submit:
            with self.assertRaisesRegex(ValueError, "Step 2: parameters"):
                run_task(self.plan)
        submit.assert_not_called()

    def test_duplicate_keys_and_oversized_plan_are_rejected(self):
        self.plan.write_text(
            '{"schema":"g1devkit/task-plan/v1","steps":[{"operation":"status","operation":"echo"}]}',
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "Duplicate plan field"):
            run_task(self.plan)
        self.plan.write_bytes(b" " * (64 * 1024 + 1))
        with self.assertRaisesRegex(ValueError, "exceeds 64 KiB"):
            run_task(self.plan)
