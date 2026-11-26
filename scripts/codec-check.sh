#!/usr/bin/env bash
# Codec-Check: prüft, ob ein Master den 320-kbps-Ogg-Durchlauf übersteht.
#
#   scripts/codec-check.sh master.wav
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WAV="${1:-}"

if [ -z "$WAV" ] || [ ! -f "$WAV" ]; then
    echo "Usage: $0 <master.wav>" >&2
    exit 2
fi

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

OGG="$TMP/codec.ogg"
BACK="$TMP/codec.wav"
A="$TMP/a.json"
B="$TMP/b.json"

ffmpeg -v error -y -i "$WAV" -c:a libvorbis -q:a 9 "$OGG"
ffmpeg -v error -y -i "$OGG" -c:a pcm_s24le "$BACK"

python3 "$ROOT/tools/measure.py" --json "$WAV" > "$A"
python3 "$ROOT/tools/measure.py" --json "$BACK" > "$B"

python3 - "$A" "$B" <<'PY'
import json
import sys

a = json.load(open(sys.argv[1]))
b = json.load(open(sys.argv[2]))

checks = []


def add(name, ok, text):
    checks.append((name, ok, text))


def delta(x, y):
    if x is None or y is None:
        return None
    return y - x


dl = delta(a["lufs_i"], b["lufs_i"])
add("Loudness", dl is not None and abs(dl) <= 0.3,
    "Δ %s LU (≤ 0.3)" % ("—" if dl is None else "%+.2f" % dl))

dtp = delta(a["true_peak_dbtp"], b["true_peak_dbtp"])
add("True Peak", dtp is not None and abs(dtp) <= 0.5,
    "Δ %s dB (≤ 0.5)" % ("—" if dtp is None else "%+.2f" % dtp))

worst = ("—", 0.0)
for band_a, band_b in zip(a.get("bands", []), b.get("bands", [])):
    if band_a["rel_db"] is None or band_b["rel_db"] is None:
        continue
    if band_a["rel_db"] < -30.0:
        continue
    d = abs(band_b["rel_db"] - band_a["rel_db"])
    if d > worst[1]:
        worst = ("%d Hz" % band_a["center_hz"], d)
add("Bandbalance", worst[1] <= 2.0,
    "größte Abweichung %s bei %s (≤ 2.0 dB)" % ("%.2f dB" % worst[1], worst[0]))

print("Codec-Check (Ogg Vorbis q9): %s" % a["file"])
failed = 0
for name, ok, text in checks:
    print("  [%s] %-12s %s" % ("PASS" if ok else "FAIL", name, text))
    failed += 0 if ok else 1
print()
if failed:
    print("CODEC-CHECK VERFEHLT — %d Kriterium/Kriterien." % failed)
    raise SystemExit(1)
print("CODEC-CHECK BESTANDEN.")
PY
