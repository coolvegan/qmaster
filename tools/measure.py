#!/usr/bin/env python3
"""Measure an audio file: loudness, true peak, dynamics, band balance, mono bass.

Uses only ffmpeg/ffprobe and the Python standard library. No numpy.

Examples:
    tools/measure.py take.wav
    tools/measure.py take.wav --json
    tools/measure.py take.wav --bands 16
"""

from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import sys
from array import array

BAND_EDGES = [60, 85, 121, 171, 243, 344, 488, 691, 980,
              1390, 1971, 2794, 3962, 5618, 7966, 11295, 16000]


def _run(cmd: list[str]) -> str:
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        raise RuntimeError("command failed: %s\n%s" % (" ".join(cmd), proc.stderr.decode(errors="replace")))
    return proc.stderr.decode(errors="replace")


def probe(path: str) -> dict:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a:0",
         "-show_entries", "stream=sample_rate,channels:format=duration",
         "-of", "json", path],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    ).stdout
    data = json.loads(out)
    stream = data["streams"][0]
    duration = float(data.get("format", {}).get("duration") or 0.0)
    return {
        "sample_rate": int(stream["sample_rate"]),
        "channels": int(stream["channels"]),
        "duration_s": duration,
    }


def _num(text: str):
    text = text.strip()
    if text in ("-inf", "inf", "nan", "-nan"):
        return None
    try:
        return float(text)
    except ValueError:
        return None


def loudness(path: str) -> dict:
    log = _run(["ffmpeg", "-hide_banner", "-nostats", "-i", path,
                "-af", "ebur128=peak=true", "-f", "null", "-"])
    summary = log.split("Summary:", 1)[-1]
    lufs = lra = tp = None
    m = re.search(r"\bI:\s+(-?[\d.]+|-inf)\s+LUFS", summary)
    if m:
        lufs = _num(m.group(1))
    m = re.search(r"\bLRA:\s+(-?[\d.]+)\s+LU", summary)
    if m:
        lra = _num(m.group(1))
    m = re.search(r"True peak:.*?\bPeak:\s+(-?[\d.]+|-inf)\s+dBFS", summary, re.S)
    if m:
        tp = _num(m.group(1))
    return {"lufs_i": lufs, "lra_lu": lra, "true_peak_dbtp": tp}


def _f32_chunks(path: str, af: str | None = None):
    cmd = ["ffmpeg", "-v", "error", "-i", path]
    if af:
        cmd += ["-af", af]
    cmd += ["-f", "f32le", "-acodec", "pcm_f32le", "-"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert proc.stdout is not None
    remainder = b""
    while True:
        chunk = proc.stdout.read(1 << 20)
        if not chunk:
            break
        chunk = remainder + chunk
        usable = len(chunk) - (len(chunk) % 4)
        remainder = chunk[usable:]
        yield array("f", chunk[:usable])
    if remainder:
        yield array("f", remainder)
    err = proc.stderr.read() if proc.stderr else b""
    if proc.wait() != 0:
        raise RuntimeError("ffmpeg decode failed: %s" % err.decode(errors="replace"))


def sample_stats(path: str, channels: int) -> dict:
    frames = 0
    peak = 0.0
    sumsq = 0.0
    dc_sum = 0.0
    clipped = 0
    for block in _f32_chunks(path):
        n = len(block)
        if not n:
            continue
        frames += n // channels
        for value in block:
            a = abs(value)
            if a > peak:
                peak = a
            sumsq += value * value
            dc_sum += value
            if a >= 0.999:
                clipped += 1
    if not frames:
        raise RuntimeError("no audio frames decoded")
    total = frames * channels
    rms = math.sqrt(sumsq / total) if total else 0.0
    return {
        "frames": frames,
        "peak_dbfs": 20 * math.log10(peak) if peak > 0 else None,
        "rms_dbfs": 20 * math.log10(rms) if rms > 0 else None,
        "dc": dc_sum / total if total else 0.0,
        "clipped_samples": clipped,
    }


def _band_edges(count: int) -> list[float]:
    count = max(1, min(count, 32))
    low, high = BAND_EDGES[0], BAND_EDGES[-1]
    return [low * (high / low) ** (i / count) for i in range(count + 1)]


def _band_centers(count: int) -> list[float]:
    edges = _band_edges(count)
    return [math.sqrt(edges[i] * edges[i + 1]) for i in range(len(edges) - 1)]


def band_levels(path: str, count: int) -> list[dict]:
    edges = _band_edges(count)
    levels = []
    for i in range(len(edges) - 1):
        low, high = edges[i], edges[i + 1]
        af = (
            "highpass=f=%.1f:poles=2,highpass=f=%.1f:poles=2,"
            "lowpass=f=%.1f:poles=2,lowpass=f=%.1f:poles=2,"
            "astats=metadata=1:reset=0"
        ) % (low, low, high, high)
        log = _run(["ffmpeg", "-hide_banner", "-nostats", "-i", path,
                    "-af", af, "-f", "null", "-"])
        values = re.findall(r"RMS level dB:\s*(-?[\d.]+)", log)
        rms = float(values[-1]) if values else None
        levels.append({"center_hz": round(math.sqrt(low * high)), "rms_dbfs": rms})
    finite = [b["rms_dbfs"] for b in levels if b["rms_dbfs"] is not None]
    top = max(finite) if finite else None
    for band in levels:
        band["rel_db"] = round(band["rms_dbfs"] - top, 2) if (band["rms_dbfs"] is not None and top is not None) else None
    return levels


def mono_stats(path: str) -> dict:
    channels = 2
    e_l = e_r = e_mid = e_side = cross = 0.0
    frames = 0
    for block in _f32_chunks(path, "lowpass=f=120:poles=2,lowpass=f=120:poles=2"):
        usable = len(block) - (len(block) % channels)
        if usable <= 0:
            continue
        frames += usable // channels
        left = block[0:usable:2]
        right = block[1:usable:2]
        for l, r in zip(left, right):
            e_l += l * l
            e_r += r * r
            mid = 0.5 * (l + r)
            side = 0.5 * (l - r)
            e_mid += mid * mid
            e_side += side * side
            cross += l * r
    if not frames:
        return {"mid_vs_channels_db": None, "side_minus_mid_db": None, "correlation": None}
    e_avg = 0.5 * (e_l + e_r)
    mid_db = 10 * math.log10(e_mid / e_avg) if e_mid > 0 and e_avg > 0 else None
    if e_mid > 0 and e_side > 0:
        side_db = 10 * math.log10(e_side / e_mid)
    else:
        side_db = None
    denom = math.sqrt(e_l * e_r)
    corr = cross / denom if denom > 0 else 0.0
    return {
        "mid_vs_channels_db": round(mid_db, 2) if mid_db is not None else None,
        "side_minus_mid_db": round(side_db, 2) if side_db is not None else None,
        "correlation": round(corr, 3),
    }


def measure(path: str, bands: int = 16) -> dict:
    info = probe(path)
    result = {"file": path, **info}
    result.update(sample_stats(path, info["channels"]))
    result.update(loudness(path))
    if result.get("true_peak_dbtp") is not None and result.get("lufs_i") is not None:
        result["plr_db"] = round(result["true_peak_dbtp"] - result["lufs_i"], 2)
    else:
        result["plr_db"] = None
    if result.get("peak_dbfs") is not None and result.get("rms_dbfs") is not None:
        result["crest_db"] = round(result["peak_dbfs"] - result["rms_dbfs"], 2)
    else:
        result["crest_db"] = None
    if bands > 0:
        result["bands"] = band_levels(path, bands)
    result["mono"] = mono_stats(path)
    return result


def _fmt(value, suffix=""):
    if value is None:
        return "—"
    if isinstance(value, float):
        return ("%.2f%s" % (value, suffix))
    return "%s%s" % (value, suffix)


def print_report(data: dict) -> None:
    print("Datei:        %s" % data["file"])
    print("Format:       %d Hz, %d Kanal/Kanäle, %.2f s" %
          (data["sample_rate"], data["channels"], data["duration_s"]))
    print("Peak:         %s dBFS" % _fmt(data["peak_dbfs"]))
    print("RMS:          %s dBFS" % _fmt(data["rms_dbfs"]))
    print("Crest:        %s dB" % _fmt(data["crest_db"]))
    print("Integrated:   %s LUFS" % _fmt(data["lufs_i"]))
    print("True Peak:    %s dBTP" % _fmt(data["true_peak_dbtp"]))
    print("PLR:          %s dB" % _fmt(data["plr_db"]))
    print("LRA:          %s LU" % _fmt(data["lra_lu"]))
    print("DC:           %s" % _fmt(data["dc"]))
    print("Clipped:      %d Samples" % data["clipped_samples"])
    mono = data["mono"]
    print("Mono <120 Hz: mid/channels %s dB, side−mid %s dB, corr %s" %
          (_fmt(mono["mid_vs_channels_db"]), _fmt(mono["side_minus_mid_db"]),
           _fmt(mono["correlation"])))
    if data.get("bands"):
        print("Bänder (relativ zum lautesten):")
        line = []
        for band in data["bands"]:
            line.append("%d Hz %s" % (band["center_hz"], _fmt(band["rel_db"])))
        print("  " + " · ".join(line))


def main() -> int:
    parser = argparse.ArgumentParser(description="Audio-Messung: LUFS, True Peak, PLR, LRA, Bänder, Mono.")
    parser.add_argument("file")
    parser.add_argument("--json", action="store_true", help="JSON statt Tabelle")
    parser.add_argument("--bands", type=int, default=16, help="Anzahl Bänder (0 = aus)")
    args = parser.parse_args()
    try:
        data = measure(args.file, args.bands)
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        print("Fehler: %s" % exc, file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print_report(data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
