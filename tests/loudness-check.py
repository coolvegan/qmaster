#!/usr/bin/env python3
"""End-to-end loudness check: render a beat through QMaster and verify the
release targets on the result.

Requires build/render and build/native/qmaster.so.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RENDER = os.path.join(ROOT, "build", "render")
LIB = os.path.join(ROOT, "build", "native", "qmaster.so")
SIGNALS = os.path.join(ROOT, "tools", "make-signals.py")
MEASURE = os.path.join(ROOT, "tools", "measure.py")


def measure(path: str) -> dict:
    out = subprocess.run([sys.executable, MEASURE, "--json", path],
                         stdout=subprocess.PIPE, check=True)
    return json.loads(out.stdout)


def main() -> int:
    if not os.path.exists(RENDER) or not os.path.exists(LIB):
        print("build/render or build/native/qmaster.so is missing", file=sys.stderr)
        return 2

    with tempfile.TemporaryDirectory(prefix="qmaster-loudness-") as tmp:
        subprocess.run([sys.executable, SIGNALS, tmp], check=True,
                       stdout=subprocess.DEVNULL)
        source = os.path.join(tmp, "loud_loop.wav")
        mastered = os.path.join(tmp, "mastered.wav")
        subprocess.run([RENDER, LIB, source, mastered, "--program", "1"],
                       check=True, stdout=subprocess.DEVNULL)

        before = measure(source)
        after = measure(mastered)

    checks = []

    def check(name: str, ok: bool, detail: str) -> None:
        checks.append((name, ok, detail))

    check("Lauter", after["lufs_i"] > before["lufs_i"] + 1.0,
          "%.1f → %.1f LUFS" % (before["lufs_i"], after["lufs_i"]))
    check("Loudness-Ziel", abs(after["lufs_i"] + 8.0) <= 1.0,
          "%.1f LUFS (Ziel −8 ±1)" % after["lufs_i"])
    check("True Peak", after["true_peak_dbtp"] <= -1.0,
          "%.2f dBTP" % after["true_peak_dbtp"])
    check("PLR", 6.0 <= after["plr_db"] <= 8.0,
          "%.2f dB (6–8)" % after["plr_db"])
    check("Clipping", after["clipped_samples"] == 0,
          "%d Samples ≥ 0.999" % after["clipped_samples"])

    print("End-to-End: synthetischer Loop durch QMaster (Programm „CD Loud“)")
    print("  vorher:  %6.1f LUFS  %6.2f dBTP  PLR %5.2f" %
          (before["lufs_i"], before["true_peak_dbtp"], before["plr_db"]))
    print("  nachher: %6.1f LUFS  %6.2f dBTP  PLR %5.2f" %
          (after["lufs_i"], after["true_peak_dbtp"], after["plr_db"]))
    print()
    failed = 0
    for name, ok, detail in checks:
        print("  [%s] %-14s %s" % ("PASS" if ok else "FAIL", name, detail))
        failed += 0 if ok else 1
    print()
    if failed:
        print("LOUDNESS-CHECK FEHLGESCHLAGEN — %d Prüfung(en)." % failed)
        return 1
    print("LOUDNESS-CHECK BESTANDEN — %d Prüfungen." % len(checks))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
