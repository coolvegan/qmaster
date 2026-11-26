#!/usr/bin/env bash
# Ein Kommando, eine Wahrheit: alles, was vor einem Commit grün sein muss.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "== Messkette"
python3 tests/selftest.py

echo
echo "== Lektionen (JSON)"
python3 - <<'PY'
import glob
import json

files = sorted(glob.glob("lessons/*/lesson.json") +
               glob.glob("lessons/*/quiz.json") +
               glob.glob("lessons/*/scenes/*.json"))
for path in files:
    json.load(open(path))
print("  %d Dateien gültig" % len(files))
PY

echo
echo "== Plugin (nativ)"
if [ -x build/host_sim ] && [ -f build/native/qmaster.so ]; then
    python3 tests/plugin-check.py
    python3 tests/alias-check.py 997 --clip 1.0
    python3 tests/loudness-check.py
else
    echo "  übersprungen (kein Build; erst ./scripts/build-mpc.sh)"
fi

echo
echo "== Skripte (Syntax)"
for script in scripts/*.sh; do
    bash -n "$script"
done
echo "  ok"

echo
echo "== Publish-Guard"
if ./scripts/publish-lessons.sh >/dev/null 2>&1; then
    echo "  FEHLER: Guard hat Drafts durchgelassen" >&2
    exit 1
fi
echo "  verweigert Drafts (erwartet)"

echo
echo "CHECK OK"
