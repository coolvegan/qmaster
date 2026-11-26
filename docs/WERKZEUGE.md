# Werkzeuge und Befehle

Alles, was zum Messen, Bauen, Prüfen und Installieren gebraucht wird — mit
konkreten Shell-Befehlen. Alle Pfade relativ zum Repo, wenn nicht anders
angegeben.

## Werkzeuge

| Werkzeug | Pfad | Aufgabe |
|---|---|---|
| Messung | `tools/measure.py` | LUFS, LRA, True Peak, PLR, Crest, DC, Clipping, 16 Bänder, Mono < 120 Hz |
| Testsignale | `tools/make-signals.py` | deterministische WAVs mit bekanntem Pegel |
| Renderer | `tools/render.cpp` → `build/render` | WAV offline durch das native Plugin, Latenz kompensiert |
| Host-Simulator | `tools/host-sim/host_sim.cpp` → `build/host_sim` | MPC-Ladesequenz, Parameter-Dump, Render-Test |
| Release-Check | `scripts/release-check.sh` | Pass/Fail gegen die Abnahmekriterien |
| Codec-Check | `scripts/codec-check.sh` | Ogg-Vorbis-q9-Durchlauf und Rückvergleich |
| Gesamt-Check | `scripts/check.sh` | Messkette, Plugin, Alias, Loudness, JSON, Guard |
| Selbsttest | `tests/selftest.py` | 13 Prüfungen der Messkette |
| Plugin-Check | `tests/plugin-check.py` | Parameter, Latenz, True Peak, Ceiling |
| Alias-Check | `tests/alias-check.py` | FFT-Spektrum, stärkster Nicht-Harmonischer |
| Loudness-Check | `tests/loudness-check.py` | End-to-End: Loop → Master → Zielkorridor |
| Build | `scripts/build-mpc.sh` | nativ, UI, ARM64/ARM32, Paket, ZIP |
| Installation | `scripts/install-mpc.sh` | kopiert das Paket auf ein MPC-Laufwerk |
| Lektionen | `scripts/publish-lessons.sh` | veröffentlicht alle Lektionen, nur wenn final |

## Konventionen

**`--set` im Renderer nimmt normalisierte Werte (0…1)**, nicht die Anzeigewerte:

| Parameter | Umrechnung | Beispiel |
|---|---|---|
| Mode | 0 = Master, 1 = Bus | `--set Mode=0` |
| Trim | `(dB + 12) / 24` | +8 dB → 0.8333 |
| Tilt | `(dB + 6) / 12` | 0 dB → 0.5 |
| Clip | `% / 100` | 55 % → 0.55 |
| Transient | `% / 100` | 60 % → 0.6 |
| Ceiling | `(dBTP + 2) / 2` | −1 dBTP → 0.5 |
| Release | `% / 100` | 45 % → 0.45 |
| Mono | `Hz / 200` | 120 Hz → 0.6 |

**Renderer:** schreibt 24-Bit-WAV, stereo, kompensiert `initialDelay`
(102 Samples). Mono-Dateien werden abgelehnt.

**Messung:** Bänder sind 16 geometrische Bänder von 60 Hz bis 16 kHz, getrennt
mit 24 dB/Okt-Filtern. Der Mono-Check nutzt einen LR4 bei 120 Hz.

## Messen

```bash
python3 tools/measure.py master.wav
python3 tools/measure.py master.wav --json
python3 tools/measure.py master.wav --bands 8
```

## Release prüfen

```bash
scripts/release-check.sh master.wav
TARGET_LUFS=-9 CEILING_DBTP=-1.0 scripts/release-check.sh master.wav
scripts/codec-check.sh master.wav
```

## Durch das Plugin rendern

```bash
# Programm (0 Init, 1 CD Loud, 2 Streaming Safe, 3 Bus Drums, 4 Bus 808)
build/render build/native/qmaster.so in.wav out.wav --program 1

# Einzelne Parameter überschreiben (normalisiert)
build/render build/native/qmaster.so in.wav out.wav \
  --set Mode=0 --set Trim=0.8333 --set Clip=0.55 \
  --set Ceiling=0.5 --set Release=0.45 --set Mono=0.6
```

## Alles prüfen

```bash
./scripts/check.sh
```

Läuft: Selbsttest (13), Lektionen-JSON, Plugin-Check (9), Alias-Check,
Loudness-Check, Shell-Syntax, Publish-Guard.

## Bauen

```bash
./scripts/build-mpc.sh
```

Ergebnis:

```
dist/mpc/r3d0xStyle - VST - QMaster/
dist/r3d0xStyle - VST - QMaster-1.0.0.zip
```

## Installieren

```bash
./scripts/install-mpc.sh          # sucht Laufwerk "MPC User" / "MPC Content"
```

Manuell:

```bash
udisksctl mount -b /dev/sda2
# VST2 Plugins liegt auf "MPC User"
cp -a "dist/mpc/r3d0xStyle - VST - QMaster" \
      "/run/media/$USER/MPC User/VST2 Plugins/"
sync
udisksctl unmount -b /dev/sda2
```

## Exporte finden

```bash
udisksctl mount -b /dev/sdb1
find /run/media/$USER -iname '*.wav' -newermt '2026-11-26 00:00' \
     -printf '%TY-%Tm-%Td %TH:%TM  %s  %p\n' | sort -r | head
```

## Host-Simulator

```bash
build/host_sim build/native/qmaster.so test --seconds 3 --wav out.wav
build/host_sim build/native/qmaster.so test --signal impulse --seconds 1 --wav imp.wav
build/host_sim build/native/qmaster.so test --signal tone --freq 997 --set Clip=1
build/host_sim build/native/qmaster.so dump > params.json
```

## Lektionen

```bash
python3 tools/gen_ui.py --params params.json --ui ui.json \
        --out "build/Plugin Skins" --kit-cache build
python3 tools/validate.py "dist/mpc/r3d0xStyle - VST - QMaster" --params params.json

# Veröffentlichen: nur wenn alle status=final und PUBLISH_CONFIRM gesetzt ist
PUBLISH_CONFIRM=yes ./scripts/publish-lessons.sh
```

## Typische Fehlerquellen

| Symptom | Ursache | Prüfung |
|---|---|---|
| Ausgabe 48 dB zu leise | 24-Bit-WAV falsches Byte zuerst | erwarteten Peak vergleichen |
| TP über dem Deckel | Detektor zu flach / Guard zu klein | `tests/plugin-check.py` |
| „Alias" ändert sich nicht mit der Filterlänge | Bandpass-Leckage | `tests/alias-check.py` (FFT) |
| Export plötzlich laut | andere Master-Kette oder anderer Projektstand | PLR und Sample-Verteilung prüfen; die MPC normalisiert nicht |
| Mono-Pegel über 0 dBFS | Downmix summiert Kanäle | Stereo-Peak messen |
| Bass verschwindet auf dem Handy | Side-Anteil unter 120 Hz | `measure.py`, Mono-Zeile |
| Preset ändert die UI nicht | Programmwechsel meldet keine Automate-/UpdateDisplay-Aufrufe | `host_sim`-Zeile „Automate / UpdateDisplay“ prüfen |
