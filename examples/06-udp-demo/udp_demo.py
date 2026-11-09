"""Loopback-only teaching protocol, independent of the legacy App/robot protocol."""
import argparse
import ipaddress
import json
import math
import socket
import sys
import time
import uuid

COMMANDS = ("status", "echo", "stop_demo")
MAX_BYTES = 4096


def encode(message):
    raw = json.dumps(message, ensure_ascii=False, allow_nan=False).encode("utf-8")
    if len(raw) > MAX_BYTES:
        raise ValueError("message exceeds 4096 bytes")
    return raw


def decode(raw):
    if len(raw) > MAX_BYTES:
        raise ValueError("oversized datagram")
    value = json.loads(raw.decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError("message must be a JSON object")
    return value


def endpoint(value):
    host, port = value.rsplit(":", 1)
    if not ipaddress.ip_address(host).is_loopback or ":" in host:
        raise ValueError("this IPv4 teaching program only accepts loopback endpoints")
    number = int(port)
    if not 1 <= number <= 65535:
        raise ValueError("invalid UDP port")
    return host, number


def handle(message, robot_id):
    if message.get("schema") != "g1-learning/v1" or message.get("kind") != "request":
        raise ValueError("unknown schema or kind")
    if not isinstance(message.get("request_id"), str) or not message["request_id"]:
        raise ValueError("request_id must be a nonempty string")
    if message.get("target") not in (robot_id, "all"):
        return None
    command = message.get("command")
    if command not in COMMANDS:
        raise ValueError("unsupported command")
    text = message.get("text", "")
    if not isinstance(text, str):
        raise ValueError("text must be a string")
    return {"schema": "g1-learning/v1", "kind": "reply", "request_id": message["request_id"],
            "robot_id": robot_id, "command": command, "result": "simulated",
            "text": text if command == "echo" else "", "motion_executed": False}


def serve(robot_id, port):
    if robot_id == "all" or not robot_id.strip():
        raise ValueError("robot-id must be nonempty and cannot be 'all'")
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind(("127.0.0.1", port))
        print(json.dumps({"event": "ready", "robot_id": robot_id, "port": sock.getsockname()[1]}), flush=True)
        while True:
            raw, peer = sock.recvfrom(MAX_BYTES + 1)
            try:
                reply = handle(decode(raw), robot_id)
                if reply is not None:
                    sock.sendto(encode(reply), peer)
                    print(json.dumps(reply, ensure_ascii=False), flush=True)
            except (ValueError, UnicodeError) as exc:
                print(json.dumps({"event": "rejected", "reason": str(exc)}), flush=True)


def send(destinations, target, command, text, timeout):
    request = {"schema": "g1-learning/v1", "kind": "request", "request_id": str(uuid.uuid4()),
               "target": target, "command": command, "text": text}
    payload = encode(request)
    destinations = set(destinations)
    results = {}
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind(("127.0.0.1", 0))
        for address in destinations:
            sock.sendto(payload, address)
        deadline = time.monotonic() + timeout
        while len(results) < len(destinations) and time.monotonic() < deadline:
            sock.settimeout(max(0.001, deadline - time.monotonic()))
            try:
                raw, peer = sock.recvfrom(MAX_BYTES + 1)
            except socket.timeout:
                break
            except ConnectionResetError:
                # Windows may surface ICMP port-unreachable as a UDP reset.
                # Keep collecting other endpoints until the normal deadline.
                continue
            try:
                reply = decode(raw)
            except (ValueError, UnicodeError):
                continue
            if (peer in destinations and reply.get("schema") == "g1-learning/v1"
                    and reply.get("kind") == "reply" and reply.get("request_id") == request["request_id"]
                    and reply.get("command") == command and isinstance(reply.get("robot_id"), str)
                    and (target == "all" or reply["robot_id"] == target)
                    and reply.get("result") == "simulated" and reply.get("motion_executed") is False):
                results[peer] = reply
    return {"request_id": request["request_id"], "replies": list(results.values()),
            "missing_endpoints": [f"{host}:{port}" for host, port in sorted(destinations - results.keys())]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    server = sub.add_parser("serve")
    server.add_argument("--robot-id", required=True)
    server.add_argument("--port", type=int, default=19006)
    client = sub.add_parser("send")
    client.add_argument("--endpoint", action="append", type=endpoint, required=True)
    client.add_argument("--target", default="all")
    client.add_argument("--command", choices=COMMANDS, default="status")
    client.add_argument("--text", default="")
    client.add_argument("--timeout", type=float, default=1)
    args = parser.parse_args()
    if args.mode == "serve":
        if not 0 <= args.port <= 65535:
            parser.error("port must be within 0..65535")
        serve(args.robot_id, args.port)
    else:
        if not math.isfinite(args.timeout) or not 0 < args.timeout <= 60:
            parser.error("timeout must be finite and within (0, 60]")
        report = send(args.endpoint, args.target, args.command, args.text, args.timeout)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return int(bool(report["missing_endpoints"]))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        pass
    except (OSError, ValueError) as exc:
        print(f"UDP demo failed: {exc}", file=sys.stderr)
        raise SystemExit(2)
