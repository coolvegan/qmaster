#!/usr/bin/env python3
"""Selbsttest des Mess-Harness.

Prüft die Messkette gegen Signale mit bekanntem Pegel. Wenn dieser Test rot
ist, sind alle Zahlen im Report wertlos.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEASURE = os.path.join(ROOT, "tools", "measure.py")
SIGNALS = os.path.join(ROOT, "tools", "make-signals.py")
RELEASE = os.path.join(ROOT, "scripts", "release-check.sh")


def run_measure(path: str) -> dict:
    out = subprocess.run([sys.executable, MEASURE, "--json", path],
                         stdout=subprocess.PIPE, check=True)
    return json.loads(out.stdout)


def check(results: list, name: str, ok: bool, detail: str) -> None:
    results.append((name, ok, detail))


def near(value, target: float, tol: float) -> bool:
    return value is not None and abs(value - target) <= tol


def main() -> int:
    results: list[tuple[str, bool, str]] = []
    with tempfile.TemporaryDirectory(prefix="qmaster-signals-") as tmp:
        subprocess.run([sys.executable, SIGNALS, tmp], check=True,
                       stdout=subprocess.DEVNULL)

        sine = run_measure(os.path.join(tmp, "sine_997_-6.wav"))
        check(results, "Sinus Peak", near(sine["peak_dbfs"], -6.02, 0.05),
              "%.2f dBFS (Soll −6.02)" % sine["peak_dbfs"])
        check(results, "Sinus RMS", near(sine["rms_dbfs"], -9.03, 0.05),
              "%.2f dBFS (Soll −9.03)" % sine["rms_dbfs"])
        check(results, "Sinus LUFS", near(sine["lufs_i"], -6.0, 0.3),
              "%.2f LUFS (Soll −6.0)" % sine["lufs_i"])
        check(results, "Sinus True Peak", near(sine["true_peak_dbtp"], -6.0, 0.3),
              "%.2f dBTP" % sine["true_peak_dbtp"])
        check(results, "Sinus DC", abs(sine["dc"]) < 1e-4,
              "%.6f" % sine["dc"])
        bands = sine["bands"]
        peak_idx = max(range(len(bands)), key=lambda i: bands[i]["rel_db"])
        far = max(b["rel_db"] for b in bands
                  if b["center_hz"] < 580 or b["center_hz"] > 2345)
        check(results, "Sinus Bandlage",
              bands[peak_idx]["center_hz"] in (823, 1167) and far <= -10.0,
              "Maximum bei %d Hz, fernab %.2f dB" %
              (bands[peak_idx]["center_hz"], far))

        dirac = run_measure(os.path.join(tmp, "dirac.wav"))
        check(results, "Dirac Peak", near(dirac["peak_dbfs"], -0.92, 0.05),
              "%.2f dBFS (Soll −0.92)" % dirac["peak_dbfs"])

        anti = run_measure(os.path.join(tmp, "antiphase_60.wav"))
        check(results, "Antiphase Korrelation", anti["mono"]["correlation"] <= -0.99,
              "%.3f (Soll −1.0)" % anti["mono"]["correlation"])
        check(results, "Antiphase Mono", anti["mono"]["mid_vs_channels_db"] is None,
              "Mid/Channels = None (Auslöschung erkannt)")

        pink = run_measure(os.path.join(tmp, "pink_-20.wav"))
        check(results, "Pink RMS", near(pink["rms_dbfs"], -20.0, 0.3),
              "%.2f dBFS (Soll −20.0)" % pink["rms_dbfs"])

        loud = run_measure(os.path.join(tmp, "loud_loop.wav"))
        check(results, "Loop Dauer", near(loud["duration_s"], 20.0, 0.1),
              "%.2f s" % loud["duration_s"])
        check(results, "Intersample erkannt",
              loud["true_peak_dbtp"] > loud["peak_dbfs"] + 1.0,
              "TP %.2f > Peak %.2f" % (loud["true_peak_dbtp"], loud["peak_dbfs"]))

        proc = subprocess.run([RELEASE, os.path.join(tmp, "loud_loop.wav")],
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        check(results, "Release-Guard", proc.returncode != 0,
              "nicht release-fähiger Loop wird abgelehnt")

    failed = 0
    for name, ok, detail in results:
        print("  [%s] %-22s %s" % ("PASS" if ok else "FAIL", name, detail))
        failed += 0 if ok else 1
    print()
    if failed:
        print("SELBSTTEST FEHLGESCHLAGEN — %d Prüfung(en)." % failed)
        return 1
    print("SELBSTTEST BESTANDEN — %d Prüfungen." % len(results))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
