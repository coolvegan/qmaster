#!/usr/bin/env python3
"""Generate deterministic test signals for the measurement harness.

No numpy, no external assets: everything is synthesised with the standard
library. Files are 44.1 kHz, 16-bit, stereo unless noted.
"""

from __future__ import annotations

import argparse
import math
import os
import random
import struct
import wave


def write_wav(path: str, frames: list[tuple[float, float]], sr: int = 44100) -> None:
    with wave.open(path, "wb") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(sr)
        payload = bytearray()
        for left, right in frames:
            l = max(-32768, min(32767, int(round(left * 32767.0))))
            r = max(-32768, min(32767, int(round(right * 32767.0))))
            payload += struct.pack("<hh", l, r)
        wav.writeframes(bytes(payload))


def sine(path: str, freq: float, amp: float, seconds: float, sr: int = 44100) -> None:
    n = int(sr * seconds)
    frames = [(amp * math.sin(2 * math.pi * freq * i / sr),) * 2 for i in range(n)]
    write_wav(path, frames, sr)


def dirac(path: str, seconds: float = 1.0, amp: float = 0.9, sr: int = 44100) -> None:
    n = int(sr * seconds)
    frames = [(0.0, 0.0)] * n
    frames[n // 2] = (amp, amp)
    write_wav(path, frames, sr)


def antiphase(path: str, freq: float = 60.0, amp: float = 0.5, seconds: float = 5.0,
              sr: int = 44100) -> None:
    n = int(sr * seconds)
    frames = []
    for i in range(n):
        s = amp * math.sin(2 * math.pi * freq * i / sr)
        frames.append((s, -s))
    write_wav(path, frames, sr)


def pink_noise(path: str, seconds: float = 10.0, rms_db: float = -20.0,
               sr: int = 44100, seed: int = 7) -> None:
    """Voss-McCartney pink noise, scaled to a target RMS."""
    rng = random.Random(seed)
    rows = [0.0] * 16
    counters = [0] * 16
    n = int(sr * seconds)
    raw = []
    for _ in range(n):
        for i in range(16):
            counters[i] += 1
            if counters[i] & (1 << i):
                rows[i] = rng.uniform(-1.0, 1.0)
                break
        raw.append(sum(rows) / 16.0)
    rms = math.sqrt(sum(x * x for x in raw) / len(raw)) or 1.0
    gain = (10 ** (rms_db / 20.0)) / rms
    frames = [(x * gain, x * gain) for x in raw]
    write_wav(path, frames, sr)


def _env(t: float, decay: float) -> float:
    return math.exp(-t / decay)


def loud_loop(path: str, seconds: float = 20.0, sr: int = 44100) -> None:
    """A dense synthetic beat: kick, bass, snare, hats, soft-clipped."""
    n = int(sr * seconds)
    rng = random.Random(11)
    frames = []
    for i in range(n):
        t = i / sr
        beat = t % 0.5
        bar = t % 2.0

        kick = 0.0
        if beat < 0.28:
            kick = 0.95 * _env(beat, 0.09) * math.sin(2 * math.pi * (55 + 90 * _env(beat, 0.02)) * beat)

        bass = 0.28 * math.sin(2 * math.pi * 55.0 * t) * (0.6 + 0.4 * math.cos(2 * math.pi * 0.5 * t))

        snare = 0.0
        if 0.5 <= bar < 0.72:
            snare = 0.55 * _env(bar - 0.5, 0.06) * rng.uniform(-1.0, 1.0)

        hat = 0.0
        hat_pos = t % 0.25
        if hat_pos < 0.03:
            hat = 0.18 * _env(hat_pos, 0.008) * rng.uniform(-1.0, 1.0)

        x = kick + bass + snare + hat
        y = math.tanh(1.8 * x)
        frames.append((y, y * 0.98))

    peak = max(max(abs(l), abs(r)) for l, r in frames) or 1.0
    gain = 0.89 / peak  # -1 dBFS
    frames = [(l * gain, r * gain) for l, r in frames]
    write_wav(path, frames, sr)


def main() -> int:
    parser = argparse.ArgumentParser(description="Testsignale für den Mess-Harness erzeugen.")
    parser.add_argument("outdir")
    args = parser.parse_args()
    os.makedirs(args.outdir, exist_ok=True)
    jobs = {
        "sine_997_-6.wav": lambda p: sine(p, 997.0, 0.5, 5.0),
        "dirac.wav": lambda p: dirac(p),
        "antiphase_60.wav": lambda p: antiphase(p),
        "pink_-20.wav": lambda p: pink_noise(p),
        "loud_loop.wav": lambda p: loud_loop(p),
    }
    for name, job in jobs.items():
        path = os.path.join(args.outdir, name)
        job(path)
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
