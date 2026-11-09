"""Optional Vosk file transcription only; no microphone or robot control."""
import argparse
import json
from pathlib import Path
import sys
import wave


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audio", type=Path)
    parser.add_argument("--model", type=Path, required=True)
    args = parser.parse_args()
    if not args.model.is_dir():
        parser.error("model directory is missing; see docs/tutorials/09-asr.md")
    try:
        from vosk import Model, KaldiRecognizer
    except ImportError:
        print("Missing vosk; install the optional requirements, then provide your model.", file=sys.stderr)
        return 2
    with wave.open(str(args.audio), "rb") as audio:
        if audio.getnchannels() != 1 or audio.getsampwidth() != 2 or audio.getcomptype() != "NONE":
            parser.error("audio must be mono, signed 16-bit uncompressed PCM WAV")
        try:
            model = Model(str(args.model.resolve()))
        except Exception as exc:
            # Vosk raises a plain Exception for invalid/model-path loader failures.
            raise RuntimeError('Model load failed; check extracted files and use an ASCII path on Windows') from exc
        recognizer = KaldiRecognizer(model, audio.getframerate())
        while chunk := audio.readframes(4000):
            if recognizer.AcceptWaveform(chunk):
                print(json.dumps(json.loads(recognizer.Result()), ensure_ascii=False))
        print(json.dumps(json.loads(recognizer.FinalResult()), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, wave.Error, RuntimeError) as exc:
        raise SystemExit(f"ASR failed: {exc}")
