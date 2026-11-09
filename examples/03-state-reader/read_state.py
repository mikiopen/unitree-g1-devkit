"""Synthetic state by default; explicit --mode dds subscribes without motion commands."""
import argparse
import json
import math
import queue
import sys
import time


def emit(state):
    print(json.dumps(state, ensure_ascii=False), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("mock", "dds"), default="mock")
    parser.add_argument("--interface", help="Linux interface name, required for DDS")
    parser.add_argument("--topic", choices=("rt/lowstate", "rt/lf/lowstate"), default="rt/lowstate")
    parser.add_argument("--duration", type=float, default=3)
    args = parser.parse_args()
    if not math.isfinite(args.duration) or not 0 < args.duration <= 300:
        parser.error("duration must be finite and within (0, 300] seconds")
    if args.mode == "mock":
        deadline = time.monotonic() + args.duration
        while time.monotonic() < deadline:
            emit({"source": "synthetic", "received_at": time.time(), "joint_index": 0,
                  "q_rad": 0.0, "dq_rad_s": 0.0})
            time.sleep(min(0.5, args.duration))
        return 0
    if not args.interface:
        parser.error("--interface is required for DDS; record model, firmware and SDK first")
    try:
        from unitree_sdk2py.core.channel import ChannelFactoryInitialize, ChannelSubscriber
        from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowState_
    except ImportError as exc:
        print(f"SDK unavailable: {exc}. See docs/tutorials/03-state.md", file=sys.stderr)
        return 2
    messages = queue.Queue(maxsize=1)

    def on_state(msg):
        try:
            joint = msg.motor_state[0]
            state = {"source": "dds", "received_at": time.time(), "joint_index": 0,
                     "q_rad": float(joint.q), "dq_rad_s": float(joint.dq)}
            messages.put_nowait(state)
        except queue.Full:
            pass

    subscriber = None
    received = 0
    try:
        ChannelFactoryInitialize(0, args.interface)
        subscriber = ChannelSubscriber(args.topic, LowState_)
        subscriber.Init(on_state, 10)
        deadline = time.monotonic() + args.duration
        while time.monotonic() < deadline:
            try:
                state = messages.get(timeout=min(0.5, max(0.001, deadline - time.monotonic())))
            except queue.Empty:
                continue
            received += 1
            emit(state)
    finally:
        if subscriber is not None:
            subscriber.Close()
    if not received:
        print("No DDS state received; check interface, topic, domain, firewall and firmware.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        pass
