#!/usr/bin/env bash
# Veröffentlicht die QMaster-Lektionen als Ganzes — aber nur, wenn alle
# Lektionen final sind und die Freigabe ausdrücklich erteilt wurde.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIARY_REPO="${DIARY_REPO:-$HOME/Dev/rust-diary}"
PUBLISHER="$DIARY_REPO/scripts/publish-lesson.sh"

if [ ! -x "$PUBLISHER" ]; then
    echo "Publisher nicht gefunden: $PUBLISHER" >&2
    echo "Setze DIARY_REPO auf das rust-diary-Repo." >&2
    exit 1
fi

if [ "$#" -gt 0 ]; then
    DIRS=("$@")
else
    mapfile -t DIRS < <(find "$ROOT/lessons" -mindepth 2 -maxdepth 2 \
        -name lesson.json -printf '%h\n' | sort)
fi

if [ "${#DIRS[@]}" -eq 0 ]; then
    echo "Keine Lektionen gefunden." >&2
    exit 1
fi

echo "Prüfe ${#DIRS[@]} Lektion(en) ..."
failed=0
for dir in "${DIRS[@]}"; do
    status=$(jq -r '.status // "draft"' "$dir/lesson.json")
    if [ "$status" != "final" ]; then
        echo "  DRAFT   $dir (status=$status)"
        failed=1
    fi
    if [ -f "$dir/body.md" ] && grep -qiE 'DRAFT|TODO' "$dir/body.md"; then
        echo "  MARKER  $dir/body.md enthält noch DRAFT/TODO"
        failed=1
    fi
    if [ -d "$dir/scenes" ] && [ -z "$(find "$dir/scenes" -name '*.json' -print -quit)" ]; then
        echo "  SZENE   $dir/scenes enthält keine Szene"
        failed=1
    fi
done

if [ "$failed" -ne 0 ]; then
    echo
    echo "Nicht veröffentlicht. Erst die Freeze-Checkliste in lessons/README.md erfüllen." >&2
    exit 1
fi

if [ "${PUBLISH_CONFIRM:-}" != "yes" ]; then
    cat >&2 <<'EOF'

Freeze-Checkliste (lessons/README.md):
  [ ] Zahlen stimmen mit REPORT.md
  [ ] Quiz-Antworten nachgerechnet
  [ ] Szenen rendern lokal
  [ ] Links und Repo-Verweise existieren
  [ ] Kein Platzhalter, kein veralteter Stand
  [ ] scripts/release-check.sh grün

Freigabe: PUBLISH_CONFIRM=yes ./scripts/publish-lessons.sh
EOF
    exit 1
fi

for dir in "${DIRS[@]}"; do
    echo
    echo "== $dir"
    "$PUBLISHER" "$dir"
done

echo
echo "Alle Lektionen veröffentlicht."
