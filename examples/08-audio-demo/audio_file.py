"""Create an original test tone or inspect WAV properties; no TTS or automatic playback."""
import argparse
import json
import math
from pathlib import Path
import struct
import wave


def describe(path):
    with wave.open(str(path), "rb") as audio:
        return {"channels": audio.getnchannels(), "sample_width_bytes": audio.getsampwidth(),
                "sample_rate_hz": audio.getframerate(), "frames": audio.getnframes(),
                "duration_s": audio.getnframes() / audio.getframerate(),
                "compression": audio.getcomptype()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    create = sub.add_parser("create")
    create.add_argument("--output", type=Path, default=Path(".local/test-tone.wav"))
    inspect = sub.add_parser("inspect")
    inspect.add_argument("path", type=Path)
    args = parser.parse_args()
    if args.mode == "create":
        args.output.parent.mkdir(parents=True, exist_ok=True)
        # Exclusive creation protects a user's existing recording from replacement.
        with args.output.open("xb") as stream, wave.open(stream, "wb") as audio:
            audio.setnchannels(1)
            audio.setsampwidth(2)
            audio.setframerate(16000)
            samples = (int(2000 * math.sin(2 * math.pi * 440 * i / 16000)) for i in range(16000))
            audio.writeframes(b"".join(struct.pack("<h", sample) for sample in samples))
        path = args.output
    else:
        path = args.path
    print(json.dumps(describe(path), indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, wave.Error) as exc:
        raise SystemExit(f"Audio file failed: {exc}")
