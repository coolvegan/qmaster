#!/usr/bin/env python3
"""Native Phase-1 checks for QMaster: parameters, latency, true peak.

Requires build/host_sim and build/native/qmaster.so (run scripts/build-mpc.sh
or the two compile commands from it first).
"""

from __future__ import annotations

import json
import os
import re
import struct
import subprocess
import sys
import tempfile
import wave

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOST = os.path.join(ROOT, "build", "host_sim")
LIB = os.path.join(ROOT, "build", "native", "qmaster.so")
MEASURE = os.path.join(ROOT, "tools", "measure.py")


def run(args: list[str]) -> str:
    return subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          text=True, check=False).stdout


def render(tmp: str, name: str, extra: list[str]) -> str:
    wav = os.path.join(tmp, name + ".wav")
    out = run([HOST, LIB, "test", "--seconds", "3", "--wav", wav] + extra)
    if "Result: PASS" not in out:
        raise RuntimeError("host_sim failed for %s:\n%s" % (name, out[-2000:]))
    return wav


def measure(path: str) -> dict:
    out = subprocess.run([sys.executable, MEASURE, "--json", path],
                         stdout=subprocess.PIPE, check=True)
    return json.loads(out.stdout)


def impulse_delay(tmp: str, name: str, extra: list[str]) -> int:
    wav = os.path.join(tmp, name + ".wav")
    out = run([HOST, LIB, "test", "--seconds", "1", "--signal", "impulse",
               "--wav", wav] + extra)
    if "Result: PASS" not in out:
        raise RuntimeError("impulse render failed:\n" + out[-2000:])
    with wave.open(wav, "rb") as f:
        sr = f.getframerate()
        ch = f.getnchannels()
        frames = f.readframes(f.getnframes())
    samples = struct.unpack("<%dh" % (len(frames) // 2), frames)
    left = samples[0::ch]
    peak = max(range(len(left)), key=lambda i: abs(left[i]))
    return peak - int(round(0.05 * sr))


def main() -> int:
    if not os.path.exists(HOST) or not os.path.exists(LIB):
        print("build/host_sim or build/native/qmaster.so is missing", file=sys.stderr)
        return 2

    results = []

    def check(name: str, ok: bool, detail: str) -> None:
        results.append((name, ok, detail))

    dump = json.loads(run([HOST, LIB, "dump"]))
    names = [p["name"] for p in dump["params"]]
    check("Parameter", names == ["Mode", "Trim", "Tilt", "Clip", "Transient",
                                 "Ceiling", "Release", "Mono"],
          ", ".join(names))
    check("Mode nicht automatisierbar", dump["params"][0]["automatable"] is False,
          "automatable=%s" % dump["params"][0]["automatable"])
    check("Programme", dump["numPrograms"] == 6,
          ", ".join(dump["programs"]))

    with tempfile.TemporaryDirectory(prefix="qmaster-check-") as tmp:
        info = run([HOST, LIB, "test", "--seconds", "1"])
        m = re.search(r"latency: (\d+) samples", info)
        reported = int(m.group(1)) if m else -1

        master_delay = impulse_delay(tmp, "imp-master", [])
        bus_delay = impulse_delay(tmp, "imp-bus", ["--set", "Mode=1", "--set", "Clip=0"])
        check("Latenz Master", abs(master_delay - reported) <= 1,
              "gemessen %d, gemeldet %d" % (master_delay, reported))
        check("Latenz Bus", bus_delay == master_delay,
              "Bus %d, Master %d" % (bus_delay, master_delay))

        info = run([HOST, LIB, "test", "--seconds", "1", "--program", "1"])
        m = re.search(r"Automate (\d+), UpdateDisplay (\d+)", info)
        automate = int(m.group(1)) if m else 0
        display = int(m.group(2)) if m else 0
        check("UI-Update bei Programmwechsel", automate >= 8 and display >= 1,
              "%d Automate, %d UpdateDisplay" % (automate, display))

        default = measure(render(tmp, "default", ["--program", "1"]))
        check("True Peak default", default["true_peak_dbtp"] <= -1.0,
              "%.2f dBTP" % default["true_peak_dbtp"])
        check("Peak default", default["peak_dbfs"] <= -1.0,
              "%.2f dBFS" % default["peak_dbfs"])

        hot = measure(render(tmp, "clip100", ["--program", "1", "--set", "Clip=1"]))
        check("True Peak Clip 100", hot["true_peak_dbtp"] <= -1.0,
              "%.2f dBTP" % hot["true_peak_dbtp"])

        low = measure(render(tmp, "ceil-2", ["--program", "1", "--set", "Ceiling=0"]))
        check("Ceiling -2", -2.4 <= low["true_peak_dbtp"] <= -1.9,
              "%.2f dBTP" % low["true_peak_dbtp"])

    failed = 0
    for name, ok, detail in results:
        print("  [%s] %-24s %s" % ("PASS" if ok else "FAIL", name, detail))
        failed += 0 if ok else 1
    print()
    if failed:
        print("PLUGIN-CHECK FEHLGESCHLAGEN — %d Prüfung(en)." % failed)
        return 1
    print("PLUGIN-CHECK BESTANDEN — %d Prüfungen." % len(results))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
