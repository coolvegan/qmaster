#!/usr/bin/env python3
"""Alias check for the QMaster clipper.

Renders a pure tone through the native plugin, then measures the spectrum with
a pure-Python FFT. Reports the strongest non-harmonic component relative to the
fundamental (dBc).

Usage: tests/alias-check.py [tone-hz] [--clip 0..1]
"""

from __future__ import annotations

import argparse
import cmath
import math
import os
import subprocess
import sys
import tempfile
import wave
from array import array

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOST = os.path.join(ROOT, "build", "host_sim")
LIB = os.path.join(ROOT, "build", "native", "qmaster.so")

N = 1 << 16


def fft(a: list[complex]) -> None:
    n = len(a)
    j = 0
    for i in range(1, n):
        bit = n >> 1
        while j & bit:
            j ^= bit
            bit >>= 1
        j ^= bit
        if i < j:
            a[i], a[j] = a[j], a[i]

    length = 2
    while length <= n:
        ang = -2.0 * math.pi / length
        wlen = complex(math.cos(ang), math.sin(ang))
        half = length // 2
        for start in range(0, n, length):
            w = 1.0 + 0.0j
            for k in range(start, start + half):
                u = a[k]
                v = a[k + half] * w
                a[k] = u + v
                a[k + half] = u - v
                w *= wlen
        length <<= 1


def peak_db(mag: list[float], sr: int, freq: float, span: int = 2) -> float:
    center = int(round(freq * N / sr))
    lo = max(0, center - span)
    hi = min(len(mag) - 1, center + span)
    best = max(mag[lo:hi + 1])
    if best <= 0:
        return -200.0
    return 20.0 * math.log10(4.0 * best / N)


def render(tone: float, clip: float, tmp: str) -> str:
    wav = os.path.join(tmp, "tone.wav")
    out = subprocess.run(
        [HOST, LIB, "test", "--signal", "tone", "--freq", str(tone),
         "--seconds", "2", "--set", "Clip=%.3f" % clip,
         "--set", "Ceiling=1", "--wav", wav],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if "Result: PASS" not in out.stdout:
        raise RuntimeError(out.stdout[-2000:])
    return wav


def load_mono(path: str) -> tuple[list[float], int]:
    with wave.open(path, "rb") as f:
        sr = f.getframerate()
        ch = f.getnchannels()
        frames = f.readframes(f.getnframes())
    samples = array("h")
    samples.frombytes(frames)
    if sys.byteorder != "little":
        samples.byteswap()
    mono = [samples[i] / 32768.0 for i in range(0, len(samples), ch)]
    return mono, sr


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("tone", nargs="?", type=float, default=997.0)
    ap.add_argument("--clip", type=float, default=1.0)
    args = ap.parse_args()

    if not os.path.exists(HOST) or not os.path.exists(LIB):
        print("build/host_sim or build/native/qmaster.so is missing", file=sys.stderr)
        return 2

    with tempfile.TemporaryDirectory(prefix="qmaster-alias-") as tmp:
        wav = render(args.tone, args.clip, tmp)
        mono, sr = load_mono(wav)

    start = int(0.2 * sr)
    block = mono[start:start + N]
    if len(block) < N:
        print("not enough samples", file=sys.stderr)
        return 2
    for i in range(N):
        block[i] *= 0.5 - 0.5 * math.cos(2.0 * math.pi * i / (N - 1))

    spec = [complex(v, 0.0) for v in block]
    del block
    fft(spec)
    half = N // 2
    mag = [abs(spec[i]) for i in range(half)]

    fundamental = peak_db(mag, sr, args.tone)
    print("Tone %.0f Hz, Clip %.0f%%" % (args.tone, args.clip * 100))
    print("  Fundamental: %.1f dBFS" % fundamental)

    harmonics = {round(args.tone * k, 1) for k in range(1, int(sr / 2 / args.tone) + 3)}
    aliases: dict[int, list[int]] = {}
    for k in range(2, 121):
        f = (args.tone * k) % sr
        if f > sr / 2:
            f = sr - f
        if f < 100 or f > sr / 2 - 100:
            continue
        if min(abs(f - h) for h in harmonics) < 15.0:
            continue
        aliases.setdefault(round(f), []).append(k)

    results = []
    for f in aliases:
        results.append((peak_db(mag, sr, f), f, aliases[f]))
    results.sort(reverse=True)
    worst = results[0] if results else (-200.0, 0, [])
    print("  Strongest alias: %.1f dBFS at %d Hz (harmonics %s)" %
          (worst[0], worst[1], ",".join(str(k) for k in worst[2][:4])))
    rel = worst[0] - fundamental
    print("  Relative: %.1f dBc" % rel)

    ok = rel <= -60.0
    print()
    print("ALIAS-CHECK %s" % ("BESTANDEN" if ok else "FEHLGESCHLAGEN"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
