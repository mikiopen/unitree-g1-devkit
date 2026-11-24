"""Run a short sequence against the in-memory teaching adapter."""
import json
from pathlib import Path

from .adapter import ReferenceAdapter, TaskRequest, TaskState


PLAN_SCHEMA = "g1devkit/task-plan/v1"
REPORT_SCHEMA = "g1devkit/task-report/v1"
MAX_PLAN_BYTES = 64 * 1024
MAX_STEPS = 16


def _unique_fields(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate plan field: {key}")
        result[key] = value
    return result


def _load_requests(path, device_id):
    with Path(path).open("rb") as stream:
        raw = stream.read(MAX_PLAN_BYTES + 1)
    if len(raw) > MAX_PLAN_BYTES:
        raise ValueError("Task plan exceeds 64 KiB")
    try:
        plan = json.loads(raw.decode("utf-8-sig"), object_pairs_hook=_unique_fields)
    except (ValueError, RecursionError) as error:
        raise ValueError(f"Invalid task plan JSON: {error}") from error
    if not isinstance(plan, dict) or set(plan) != {"schema", "steps"}:
        raise ValueError("Task plan must contain exactly schema and steps")
    if plan["schema"] != PLAN_SCHEMA:
        raise ValueError(f"Task plan schema must be {PLAN_SCHEMA}")
    if not isinstance(plan["steps"], list) or not 1 <= len(plan["steps"]) <= MAX_STEPS:
        raise ValueError(f"Task plan must contain 1 to {MAX_STEPS} steps")

    requests = []
    for number, step in enumerate(plan["steps"], 1):
        if (not isinstance(step, dict) or "operation" not in step
                or step.keys() - {"operation", "parameters"}):
            raise ValueError(f"Step {number}: expected operation and optional parameters")
        parameters = step.get("parameters", {})
        if not isinstance(parameters, dict):
            raise ValueError(f"Step {number}: parameters must be an object")
        try:
            request = TaskRequest.create(device_id, step["operation"], parameters)
        except (ValueError, RecursionError) as error:
            raise ValueError(f"Step {number}: {error}") from error
        requests.append(request)
    return requests


def run_task(path):
    """Validate a whole plan, then submit steps until the first non-success."""
    adapter = ReferenceAdapter()
    requests = _load_requests(path, adapter.device_id)
    steps = []
    stopped_at = None
    for number, request in enumerate(requests, 1):
        entry = {"step": number, "operation": request.operation}
        if stopped_at is None:
            event = adapter.submit(request)
            entry.update(state=event.state.value, event=event.to_dict())
            if event.state != TaskState.SUCCEEDED:
                stopped_at = number
        else:
            entry.update(state="skipped", blocked_by_step=stopped_at)
        steps.append(entry)

    return {
        "schema": REPORT_SCHEMA,
        "capability": adapter.capabilities().to_dict(),
        "steps": steps,
        "passed": stopped_at is None,
        "network_accessed": False,
        "motion_executed": False,
    }
