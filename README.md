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
./scripts/check.sh              # measurement chain + plugin + alias checks

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
tools/               measure.py, make-signals.py
scripts/             release-check.sh, codec-check.sh, publish-lessons.sh
tests/               selftest.py (tests the measurement chain)
lessons/             draft lessons, published only at the end
```

## Documentation

- [PLAN.md](PLAN.md) — what is built, in which order, and when it counts as done.
- [REPORT.md](REPORT.md) — what the harness measures, including its limits.
- [lessons/README.md](lessons/README.md) — lesson workflow and freeze checklist.

## License

GPL-3.0-or-later.
