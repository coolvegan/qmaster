#!/usr/bin/env bash
# Release-Check: prüft eine fertige WAV gegen die QMaster-Abnahmekriterien.
#
#   scripts/release-check.sh master.wav
#   TARGET_LUFS=-9 CEILING_DBTP=-1.0 scripts/release-check.sh master.wav
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WAV="${1:-}"
TARGET="${TARGET_LUFS:--8}"
CEIL="${CEILING_DBTP:--1.0}"

if [ -z "$WAV" ] || [ ! -f "$WAV" ]; then
    echo "Usage: $0 <master.wav>" >&2
    exit 2
fi

JSON="$(mktemp)"
trap 'rm -f "$JSON"' EXIT

python3 "$ROOT/tools/measure.py" --json "$WAV" > "$JSON"

python3 - "$JSON" "$TARGET" "$CEIL" <<'PY'
import json
import sys

data = json.load(open(sys.argv[1]))
target = float(sys.argv[2])
ceiling = float(sys.argv[3])

checks = []


def add(name, ok, text):
    checks.append((name, ok, text))


def db(value):
    return "—" if value is None else "%.2f" % value


lufs = data.get("lufs_i")
tp = data.get("true_peak_dbtp")
plr = data.get("plr_db")
lra = data.get("lra_lu")
mono = data.get("mono", {})
duration = data.get("duration_s", 0)

add("Loudness", lufs is not None and abs(lufs - target) <= 1.0,
    "I %s LUFS (Ziel %+.1f ±1.0)" % (db(lufs), target))
add("True Peak", tp is not None and tp <= ceiling,
    "TP %s dBTP (Deckel %+.1f)" % (db(tp), ceiling))
add("PLR", plr is not None and 6.0 <= plr <= 8.0,
    "PLR %s dB (6–8)" % db(plr))
if duration >= 20.0:
    add("LRA", lra is not None and 4.0 <= lra <= 7.0,
        "LRA %s LU (4–7)" % db(lra))
else:
    add("LRA", True, "übersprungen (Datei < 20 s)")
add("DC", abs(data.get("dc") or 0.0) < 0.001,
    "DC %.5f" % (data.get("dc") or 0.0))
add("Clipping", (data.get("clipped_samples") or 0) == 0,
    "%d Samples ≥ 0.999" % (data.get("clipped_samples") or 0))

mid = mono.get("mid_vs_channels_db")
add("Mono-Phasen", mid is not None and mid >= -3.0,
    "Mid/Channels %s dB (≥ −3)" % db(mid))

side = mono.get("side_minus_mid_db")
add("Mono-Bass", side is not None and side <= -3.0,
    "Side−Mid <120 Hz %s dB (≤ −3)" % db(side))

print("Release-Check: %s" % data["file"])
print("  Format: %d Hz, %d ch, %.1f s" %
      (data["sample_rate"], data["channels"], duration))
failed = 0
for name, ok, text in checks:
    print("  [%s] %-12s %s" % ("PASS" if ok else "FAIL", name, text))
    failed += 0 if ok else 1
print()
if failed:
    print("NICHT RELEASE-FÄHIG — %d Kriterium/Kriterien verfehlt." % failed)
    raise SystemExit(1)
print("RELEASE-FÄHIG — alle Kriterien erfüllt.")
PY
