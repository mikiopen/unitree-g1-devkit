"""Device-adapter contracts plus a non-motion in-memory reference implementation."""
from dataclasses import dataclass, field
from enum import Enum
import json
import time
from types import MappingProxyType
from typing import Any, Mapping, Protocol, runtime_checkable
import uuid


MAX_ID_LENGTH = 128
MAX_OPERATION_LENGTH = 64
MAX_TIMEOUT_MS = 60_000
MAX_COMPLETED_REQUESTS = 1024


def _identifier(value, field_name, maximum=MAX_ID_LENGTH):
    if not isinstance(value, str) or not value or len(value) > maximum:
        raise ValueError(f"{field_name} must be a non-empty string up to {maximum} characters")
    if value != value.strip() or any(ord(character) < 32 for character in value):
        raise ValueError(f"{field_name} contains whitespace padding or control characters")
    return value


def _timestamp(value, field_name):
    if type(value) is not int or value < 0:
        raise ValueError(f"{field_name} must be a non-negative integer timestamp in milliseconds")
    return value


def _freeze_json(value):
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze_json(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze_json(item) for item in value)
    return value


def _thaw_json(value):
    if isinstance(value, Mapping):
        return {key: _thaw_json(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json(item) for item in value]
    return value


def _json_object(value, field_name):
    if not isinstance(value, Mapping):
        raise ValueError(f"{field_name} must be a JSON object")
    copied = _thaw_json(value)
    try:
        encoded = json.dumps(copied, ensure_ascii=False, allow_nan=False, sort_keys=True,
                             separators=(",", ":"))
    except (TypeError, ValueError, OverflowError, RecursionError) as error:
        raise ValueError(f"{field_name} must contain finite JSON-compatible values") from error
    if len(encoded.encode("utf-8")) > 4096:
        raise ValueError(f"{field_name} exceeds 4096 encoded bytes")
    return _freeze_json(json.loads(encoded))


class TaskState(str, Enum):
    """States exposed across the application/adapter boundary."""

    ACCEPTED = "accepted"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    FAILED = "failed"


@dataclass(frozen=True)
class Capability:
    device_id: str
    adapter: str
    operations: tuple[str, ...]
    simulation: bool
    motion_capable: bool

    def __post_init__(self):
        _identifier(self.device_id, "device_id")
        _identifier(self.adapter, "adapter")
        if type(self.simulation) is not bool or type(self.motion_capable) is not bool:
            raise ValueError("simulation and motion_capable must be booleans")
        if not self.operations or len(set(self.operations)) != len(self.operations):
            raise ValueError("operations must be a non-empty tuple without duplicates")
        for operation in self.operations:
            _identifier(operation, "operation", MAX_OPERATION_LENGTH)

    def to_dict(self):
        return {"device_id": self.device_id, "adapter": self.adapter,
                "operations": list(self.operations), "simulation": self.simulation,
                "motion_capable": self.motion_capable}


@dataclass(frozen=True)
class Observation:
    device_id: str
    name: str
    value: Mapping[str, Any]
    captured_at_ms: int
    received_at_ms: int
    source: str
    simulation: bool

    def __post_init__(self):
        _identifier(self.device_id, "device_id")
        _identifier(self.name, "observation name", MAX_OPERATION_LENGTH)
        _identifier(self.source, "source")
        object.__setattr__(self, "value", _json_object(self.value, "observation value"))
        _timestamp(self.captured_at_ms, "captured_at_ms")
        _timestamp(self.received_at_ms, "received_at_ms")
        if self.received_at_ms < self.captured_at_ms:
            raise ValueError("received_at_ms cannot precede captured_at_ms")
        if type(self.simulation) is not bool:
            raise ValueError("simulation must be a boolean")

    def to_dict(self):
        return {"device_id": self.device_id, "name": self.name, "value": _thaw_json(self.value),
                "captured_at_ms": self.captured_at_ms, "received_at_ms": self.received_at_ms,
                "source": self.source, "simulation": self.simulation}


@dataclass(frozen=True)
class TaskRequest:
    request_id: str
    device_id: str
    operation: str
    parameters: Mapping[str, Any]
    created_at_ms: int
    deadline_at_ms: int

    def __post_init__(self):
        try:
            uuid.UUID(self.request_id)
        except (ValueError, AttributeError, TypeError) as error:
            raise ValueError("request_id must be a UUID string") from error
        _identifier(self.device_id, "device_id")
        _identifier(self.operation, "operation", MAX_OPERATION_LENGTH)
        object.__setattr__(self, "parameters", _json_object(self.parameters, "parameters"))
        _timestamp(self.created_at_ms, "created_at_ms")
        _timestamp(self.deadline_at_ms, "deadline_at_ms")
        if self.deadline_at_ms <= self.created_at_ms:
            raise ValueError("deadline_at_ms must be later than created_at_ms")
        if self.deadline_at_ms - self.created_at_ms > MAX_TIMEOUT_MS:
            raise ValueError(f"task timeout cannot exceed {MAX_TIMEOUT_MS} milliseconds")

    @classmethod
    def create(cls, device_id, operation, parameters=None, timeout_ms=1000,
               request_id=None, now_ms=None):
        if type(timeout_ms) is not int or not 1 <= timeout_ms <= MAX_TIMEOUT_MS:
            raise ValueError(f"timeout_ms must be an integer in [1, {MAX_TIMEOUT_MS}]")
        created = int(time.time() * 1000) if now_ms is None else now_ms
        return cls(request_id or str(uuid.uuid4()), device_id, operation, parameters or {},
                   created, created + timeout_ms)

    def to_dict(self):
        return {"request_id": self.request_id, "device_id": self.device_id,
                "operation": self.operation, "parameters": _thaw_json(self.parameters),
                "created_at_ms": self.created_at_ms, "deadline_at_ms": self.deadline_at_ms}


@dataclass(frozen=True)
class TaskEvent:
    request_id: str
    device_id: str
    operation: str
    state: TaskState
    occurred_at_ms: int
    result: Mapping[str, Any] = field(default_factory=dict)
    error: str | None = None
    simulation: bool = True
    motion_executed: bool = False

    def __post_init__(self):
        try:
            uuid.UUID(self.request_id)
        except (ValueError, AttributeError, TypeError) as error:
            raise ValueError("request_id must be a UUID string") from error
        _identifier(self.device_id, "device_id")
        _identifier(self.operation, "operation", MAX_OPERATION_LENGTH)
        if not isinstance(self.state, TaskState):
            raise ValueError("state must be a TaskState")
        _timestamp(self.occurred_at_ms, "occurred_at_ms")
        object.__setattr__(self, "result", _json_object(self.result, "result"))
        if self.error is not None and (not isinstance(self.error, str) or not self.error.strip()):
            raise ValueError("error must be a non-empty string or null")
        if self.state in (TaskState.REJECTED, TaskState.FAILED) and self.error is None:
            raise ValueError("rejected and failed events require an error")
        if self.state == TaskState.SUCCEEDED and self.error is not None:
            raise ValueError("succeeded events cannot contain an error")
        if type(self.simulation) is not bool or type(self.motion_executed) is not bool:
            raise ValueError("simulation and motion_executed must be booleans")
        if self.motion_executed and self.simulation:
            raise ValueError("a simulated event cannot claim physical motion")

    def to_dict(self):
        return {"request_id": self.request_id, "device_id": self.device_id,
                "operation": self.operation, "state": self.state.value,
                "occurred_at_ms": self.occurred_at_ms, "result": _thaw_json(self.result),
                "error": self.error, "simulation": self.simulation,
                "motion_executed": self.motion_executed}


@runtime_checkable
class DeviceAdapter(Protocol):
    """Minimum application-facing shape; transport and lifecycle remain implementation-specific."""

    def capabilities(self) -> Capability: ...

    def observe(self, name: str = "status", now_ms: int | None = None) -> Observation: ...

    def submit(self, request: TaskRequest, now_ms: int | None = None) -> TaskEvent: ...


class ReferenceAdapter:
    """Deterministic adapter for contract tests; it has no network or motion path."""

    OPERATIONS = ("status", "echo")

    def __init__(self, device_id="reference-g1"):
        self.device_id = _identifier(device_id, "device_id")
        if self.device_id == "all":
            raise ValueError("all is a selector, not a device_id")
        self._completed = {}

    def capabilities(self):
        return Capability(self.device_id, "reference-memory", self.OPERATIONS,
                          simulation=True, motion_capable=False)

    def observe(self, name="status", now_ms=None):
        if name != "status":
            raise ValueError("reference adapter only exposes the status observation")
        now = int(time.time() * 1000) if now_ms is None else now_ms
        return Observation(self.device_id, "status", {"mode": "mock", "battery_percent": 80},
                           now, now, "reference-memory", simulation=True)

    def submit(self, request, now_ms=None):
        if not isinstance(request, TaskRequest):
            raise TypeError("request must be a TaskRequest")
        now = int(time.time() * 1000) if now_ms is None else now_ms
        _timestamp(now, "now_ms")
        previous = self._completed.get(request.request_id)
        if previous is not None:
            previous_request, previous_event = previous
            if previous_request != request:
                raise ValueError("request_id was reused with different content")
            return previous_event
        if request.device_id != self.device_id:
            event = self._event(request, TaskState.REJECTED, now, error="unknown device")
        elif now < request.created_at_ms:
            event = self._event(request, TaskState.REJECTED, now, error="request creation time is in the future")
        elif now > request.deadline_at_ms:
            event = self._event(request, TaskState.REJECTED, now, error="request deadline expired")
        elif request.operation not in self.OPERATIONS:
            event = self._event(request, TaskState.REJECTED, now, error="unsupported operation")
        elif request.operation == "status":
            event = self._event(request, TaskState.SUCCEEDED, now,
                                result=self.observe(now_ms=now).value)
        else:
            text = request.parameters.get("text")
            if not isinstance(text, str) or len(text) > 256:
                event = self._event(request, TaskState.REJECTED, now,
                                    error="echo.text must be a string up to 256 characters")
            else:
                event = self._event(request, TaskState.SUCCEEDED, now, result={"text": text})
        self._completed[request.request_id] = (request, event)
        if len(self._completed) > MAX_COMPLETED_REQUESTS:
            self._completed.pop(next(iter(self._completed)))
        return event

    @staticmethod
    def _event(request, state, now, result=None, error=None):
        return TaskEvent(request.request_id, request.device_id, request.operation, state, now,
                         result or {}, error, simulation=True, motion_executed=False)


def contract_demo(now_ms=None):
    """Exercise success, idempotent replay and explicit rejection without I/O."""
    now = int(time.time() * 1000) if now_ms is None else now_ms
    adapter = ReferenceAdapter()
    status = TaskRequest.create(adapter.device_id, "status", now_ms=now)
    first = adapter.submit(status, now_ms=now)
    replay = adapter.submit(status, now_ms=now + 1)
    unsupported = TaskRequest.create(adapter.device_id, "walk", now_ms=now)
    rejected = adapter.submit(unsupported, now_ms=now)
    return {"capability": adapter.capabilities().to_dict(),
            "observation": adapter.observe(now_ms=now).to_dict(),
            "status_event": first.to_dict(), "idempotent_replay": replay == first,
            "unsupported_event": rejected.to_dict(), "network_accessed": False,
            "motion_executed": False}
