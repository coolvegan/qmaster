#!/usr/bin/env bash
# Install/update QMaster on a connected Akai MPC drive.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$ROOT/dist/mpc/r3d0xStyle - VST - QMaster"
[ -d "$SRC" ] || { echo "missing $SRC - run ./scripts/build-mpc.sh first" >&2; exit 1; }

DEV="$(blkid -L 'MPC User' 2>/dev/null || true)"
[ -n "$DEV" ] || DEV="$(blkid -L 'MPC Content' 2>/dev/null || true)"
[ -n "$DEV" ] || { echo "MPC drive not found (labels: MPC User / MPC Content)" >&2; exit 1; }

MNT="$(findmnt -n -o TARGET "$DEV" 2>/dev/null || true)"
MOUNTED_BY_US=0
if [ -z "$MNT" ]; then
    udisksctl mount -b "$DEV" >/dev/null
    MNT="$(findmnt -n -o TARGET "$DEV")"
    MOUNTED_BY_US=1
fi

DEST="$MNT/VST2 Plugins"
mkdir -p "$DEST"
rm -rf "$DEST/r3d0xStyle - VST - QMaster"
cp -a "$SRC" "$DEST/"
sync

echo "installed: $DEST/r3d0xStyle - VST - QMaster"
find "$DEST/r3d0xStyle - VST - QMaster" -maxdepth 2 -type f -printf '  %P\n' | sort

if [ "$MOUNTED_BY_US" = "1" ]; then
    udisksctl unmount -b "$DEV" >/dev/null
    echo "unmounted $DEV (safe to disconnect)"
fi
