#!/usr/bin/env bash
# Build QMaster for Akai MPC: native host test, ARM64 + ARM32 cross-compile,
# MPC touch UI, validation and a ready-to-copy plugin folder.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

BUILD="$ROOT/build"
PKG="$ROOT/dist/mpc/r3d0xStyle - VST - QMaster"
IMAGE="qmaster-mpc-cross"
CXX="${CXX:-g++}"
PY="${PYTHON:-python3}"

command -v docker >/dev/null || { echo "docker is required" >&2; exit 1; }
command -v "$PY" >/dev/null || { echo "python3 is required" >&2; exit 1; }

echo "== 1/6  native build + MPC host simulator test"
mkdir -p "$BUILD/native"
"$CXX" -std=c++17 -O2 -fPIC -shared -fvisibility=hidden -fvisibility-inlines-hidden \
    -I "$ROOT/framework" -I "$ROOT/src" \
    -Wl,--version-script="$ROOT/tools/exports.map" \
    -o "$BUILD/native/qmaster.so" "$ROOT/src/QMasterMpc.cpp"

"$CXX" -std=c++17 -O2 -o "$BUILD/host_sim" "$ROOT/tools/host-sim/host_sim.cpp"
"$CXX" -std=c++17 -O2 -I "$ROOT/framework" -o "$BUILD/render" "$ROOT/tools/render.cpp"
"$BUILD/host_sim" "$BUILD/native/qmaster.so" test --seconds 3 --wav "$BUILD/qmaster-test.wav"
"$BUILD/host_sim" "$BUILD/native/qmaster.so" dump > "$ROOT/params.json"

echo "== 2/6  generate the MPC touch UI"
"$PY" "$ROOT/tools/gen_ui.py" \
    --params "$ROOT/params.json" \
    --ui "$ROOT/ui.json" \
    --out "$BUILD/Plugin Skins" \
    --kit-cache "$BUILD"

echo "== 3/6  build the cross-compiler image"
docker build -q -t "$IMAGE" -f "$ROOT/docker/Dockerfile.mpc-cross" "$ROOT"

echo "== 4/6  cross-compile ARM64 and ARM32"
mkdir -p "$BUILD/cross/arm64" "$BUILD/cross/arm32"
docker run --rm -u "$(id -u):$(id -g)" -e HOME=/tmp \
    -v "$ROOT":/work/src -w /work/src "$IMAGE" bash -lc '
set -euo pipefail
CFLAGS="-std=c++17 -O2 -fPIC -shared -fvisibility=hidden -fvisibility-inlines-hidden \
 -ffunction-sections -fdata-sections -I framework -I src"
LDFLAGS="-Wl,--gc-sections -Wl,-s -Wl,--version-script=tools/exports.map \
 -static-libstdc++ -static-libgcc -Wl,--as-needed"

aarch64-linux-gnu-g++ $CFLAGS -march=armv8-a $LDFLAGS \
  -o build/cross/arm64/qmaster-arm64.so src/QMasterMpc.cpp

arm-linux-gnueabihf-g++ $CFLAGS -mcpu=cortex-a17 -mfpu=neon-vfpv4 -mfloat-abi=hard $LDFLAGS \
  -o build/cross/arm32/qmaster-arm32.so src/QMasterMpc.cpp
'

echo "== 5/6  package"
rm -rf "$PKG"
mkdir -p "$PKG/VST" "$PKG/Plugin Skins"
cp "$ROOT/plugin.json" "$ROOT/version.xml" "$PKG/"
cp "$ROOT/LICENSE" "$PKG/LICENSE.txt"
cp "$BUILD/cross/arm64/qmaster-arm64.so" "$PKG/VST/"
cp "$BUILD/cross/arm32/qmaster-arm32.so" "$PKG/VST/"
cp "$BUILD/Plugin Skins/"* "$PKG/Plugin Skins/"

cat > "$PKG/INSTALL.txt" <<'EOF'
QMaster for Akai MPC - installation
===================================

1. Copy the whole folder

       r3d0xStyle - VST - QMaster

   into a folder named exactly

       VST2 Plugins

   at the root of a USB drive, SD card or the MPC's internal drive.

2. On the MPC enable:
       Preferences -> Enhancements (Beta) -> Enable Enhancements
       Preferences -> Enhancements (Beta) -> External Plugin Support

3. Restart or rescan. QMaster appears under External Plugins.

The arm64 build is for 64-bit MPC OS devices (MPC Live III / XL and later).
The arm32 build is for Gen1 devices (Live / Live II / One / One+ / X / Key /
Force) running MPC OS 3.10.1 or later.

The UI is one page and changes with the Mode switch:
  Master: Trim, Tilt, Clip, Ceiling, Release, Mono
  Bus:    Trim, Clip, Transient
Both modes report the same latency (102 samples), so switching Mode never
shifts the timing.
EOF

cat > "$PKG/README.txt" <<'EOF'
QMaster 1.0.0 - master and bus processor for Akai MPC
=====================================================

QMaster is the finish stage for a dense rap mix: a 2x oversampled clipper and
a true-peak limiter in Master mode, a transient/clipper in Bus mode.

Controls
--------
Mode       Master / Bus
Trim       input level, -12 .. +12 dB
Tilt       dark / bright, -6 .. +6 dB
Clip       clipper drive, 0 .. 100 % (0 .. 12 dB)
Transient  bus punch, 0 .. 100 % (Bus only)
Ceiling    true-peak ceiling, -2 .. 0 dBTP (Master only)
Release    limiter release, 30 .. 800 ms (Master only)
Mono       mono below 0 .. 200 Hz, 0 = off (Master only)

Master signal path
------------------
In -> Trim -> 24 Hz high-pass -> Tilt -> Mono maker
   -> 2x oversampled clipper -> true-peak limiter -> Out

Bus signal path
---------------
In -> Trim -> Transient -> 2x oversampled clipper -> latency pad -> Out

Latency
-------
Both modes: 102 samples (about 2.1 ms at 44.1 kHz), reported to the host.

Programs
--------
Init, CD Loud, CD Dynamic, Streaming Safe, Bus Drums, Bus 808.

CD Loud     Trim +8.0, Clip 55, Ceiling -1.0, Release 45, Mono 120
CD Dynamic  Trim +7.5, Clip 56, Ceiling -1.0, Release 45, Mono 120

A program change reports every parameter to the host (audioMasterAutomate)
and requests a redraw (audioMasterUpdateDisplay), so the MPC knobs follow.

Measurement
-----------
The ceiling is a target, not a guess. The limiter detects peaks with a 4x
interpolator and keeps a 0.40 dB guard for heavy clipping. Verify the result
offline with tools/measure.py.
EOF

echo "== 6/6  validate and zip"
"$PY" "$ROOT/tools/validate.py" "$PKG" --params "$ROOT/params.json"

"$PY" - "$PKG" <<'PY'
import os, shutil, sys
pkg = sys.argv[1]
root = os.path.dirname(os.path.dirname(pkg))
archive = os.path.join(root, "r3d0xStyle - VST - QMaster-1.0.0")
shutil.make_archive(archive, "zip", os.path.dirname(pkg), os.path.basename(pkg))
print("wrote " + archive + ".zip")
PY

echo
echo "MPC plugin folder: $PKG"
file "$PKG/VST/qmaster-arm64.so" "$PKG/VST/qmaster-arm32.so"
