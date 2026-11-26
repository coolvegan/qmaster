# QMaster

Master and bus processor for the Akai MPC. MPC-only: ARM64/ARM32 VST2, no
desktop build.

QMaster exists to make a dense rap mix reach competitive CD loudness without
destroying it — and to do it on a device that has no loudness meter and no
sidechain bus. Everything is measured offline; nothing is guessed.

**Status: Phase 1** — Master and Bus modes are built and natively verified.
Device verification (install, CPU, state round-trip) is still open.

## Targets

| Metric | Target |
|---|---|
| Integrated loudness | −8 ± 1 LUFS |
| True peak | ≤ −1.0 dBTP |
| PLR | 6–8 dB |
| LRA | 4–7 LU |
| Alias at full clip | ≤ −60 dBFS |
| Mono below 120 Hz | no cancellation |

## Modes (planned)

- **Master** — trim, tilt, 24 Hz HPF, mono maker, 2× oversampled clipper,
  true-peak limiter.
- **Bus** — trim, transient, 2× oversampled clipper. Identical latency to
  Master; no limiter.

## Quick start

```bash
./scripts/build-mpc.sh          # native test, UI, cross-compile, validate, zip
./scripts/check.sh              # measurement chain + plugin + alias + loudness

# a file through the native plugin (normalised --set values, 0..1)
build/render build/native/qmaster.so in.wav out.wav --program 1

python3 tools/make-signals.py /tmp/qm-signals
python3 tools/measure.py /tmp/qm-signals/loud_loop.wav
```

Requirements: `docker`, `ffmpeg`, `ffprobe`, `python3` (standard library only),
`g++`.

The build writes `dist/mpc/r3d0xStyle - VST - QMaster/` and a release ZIP next
to it. `scripts/install-mpc.sh` copies the folder to a connected MPC drive.

## Layout

```
PLAN.md              scope, phases, acceptance criteria, QA
REPORT.md            measured baseline and open items
docs/ANALYSEN.md     every measurement, with lesson mapping
docs/WERKZEUGE.md    tools, shell recipes, conventions
docs/QMaster-Mathematik.xlsx   live-formula workbook for the lessons
docs/build_qmaster_sheet.py    regenerates the workbook
docs/MPC-SDK-2026-11.md        analysis of the official inMusic SDK
tools/               measure.py, make-signals.py
scripts/             release-check.sh, codec-check.sh, publish-lessons.sh
tests/               selftest.py (tests the measurement chain)
lessons/             the seven-part German series (published)
```

## Lessons

A seven-part German series with the full maths, the code, the measurements and
the mistakes: [Lernpfad](https://marcokittel.de/lesson/4ca48031-1624-4d83-9042-40fb6b3d3542),
[Lautheit](https://marcokittel.de/lesson/19c51f56-cdc1-4610-b883-b1ea29cc4540),
[Clipper](https://marcokittel.de/lesson/482db70e-d09d-4d6f-b54c-183b64972491),
[Limiter](https://marcokittel.de/lesson/f8d09145-6f1e-4b59-98a0-3ddff283ca3a),
[Filter und Mono](https://marcokittel.de/lesson/eda3d6ed-27cd-4a80-b946-5c09808f854a),
[Code-Generierung](https://marcokittel.de/lesson/ddfe2add-5451-4b3d-a48c-866c2b6215f3),
[Capstone](https://marcokittel.de/lesson/94f4b4a8-23ad-4751-8778-59e8fc2c8f8f).

## Workbook

[docs/QMaster-Mathematik.xlsx](docs/QMaster-Mathematik.xlsx) is a Gridcraft/Excel
workbook with the maths of the series as live formulas: dB, RMS, LUFS gating,
true peak, clipper transfer, limiter coefficients, biquad magnitude, mono maker,
the target corridor and the measured data. Yellow cells are inputs.

## Documentation

- [PLAN.md](PLAN.md) — what is built, in which order, and when it counts as done.
- [REPORT.md](REPORT.md) — what the harness measures, including its limits.
- [lessons/README.md](lessons/README.md) — lesson workflow and freeze checklist.

## License

GPL-3.0-or-later.
