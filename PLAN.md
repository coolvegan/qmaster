# QMaster — Plan (MVP → 1.0)

Stand: 2026-11-26
Produkt: **QMaster**
Repo/Ordner: **`qmaster-mpc`**
Vendor: **`r3d0xStyle`**
Plattform: **MPC only** — ARM64/ARM32-VST2, kein Desktop-/DAW-Build

Ziel: Ein MPC-Master/Bus-Plug-in, das einen dichten Rap-Mix auf kompetitive
CD-Lautheit bringt, ohne ihn zu zerstören. Messbar, nicht nach Gefühl.

## 1. Ziel und Nicht-Ziel

**Ziel**
- Master-Modus: Trim, Tilt, HPF, Mono-Maker, Clipper (2× OS), True-Peak-Limiter.
- Bus-Modus: Trim, Transient, Clipper (2× OS), keine Lookahead-Latenz.
- Konstante Latenz über alle Modi und Einstellungen.
- Reproduzierbare Ergebnisse: Presets, Offline-Release-Check, dokumentierte Zahlen.

**Nicht-Ziel (bewusst gestrichen)**
- Shared-Memory-Koordinator („QBus" als Multi-Bus-Routing). Kein messbarer
  Beitrag zur Spotify-/CD-Tauglichkeit, hohes Risiko.
- Live-Metering im Plugin. Die MPC-UI kann nur knob/fader/switch/slider/text/empty.
- Automatischer LUFS-Abgleich im Plugin. Ohne Meter wäre das Raten.
- Dither im Plugin. Wortlängenreduktion passiert beim Export, nicht im Plug-in.
- Desktop-/DAW-Build. Zielgerät ist ausschließlich die MPC; der native Build
  dient nur als Test-Harness.

## 2. Abnahmekriterien

| Kriterium | Ziel | Messung |
|---|---|---|
| Integrated Loudness | −8 ± 1 LUFS (CD-laut) | ffmpeg ebur128 |
| True Peak | ≤ −1,0 dBTP | ebur128 / 4×-OS-Meter |
| PLR (TP − LUFS) | 6–8 dB | berechnet |
| LRA | 4–7 LU | ebur128 |
| Alias bei Clipping | ≤ −60 dBFS | 997-Hz-Sine, Spektrum |
| Null-Test (Clip 0, Tilt 0) | bit-transparent | bitweiser Vergleich |
| Latenz | identisch in Master/Bus, alle Settings | Dirac |
| Mono < 120 Hz | keine Auslöschung | L/R-Summe |
| Ogg 320 kbps | keine Sibilanz/Hi-Hat-Smear | Hörtest + Spektrum |
| CPU | 1× Master + 5× Bus ohne Xruns (48 kHz) | Gerät, 10-min-Loop |
| Export | unnormalisiert | MPC-Exportdialog |

## 3. Architektur

### Parameter (8, eine UI-Seite, `visibleWhen` pro Modus)

| # | Name | Bereich | Modus | Bedeutung |
|---|---|---|---|---|
| 0 | Mode | Master / Bus | beide | choice, `automatable: false` |
| 1 | Trim | −12…+12 dB | beide | Eingangspegel |
| 2 | Tilt | −6…+6 dB | Master | dunkel ↔ hell (Shelf-Paar) |
| 3 | Clip | 0…100 % | beide | Clipper-Amount, 2× OS |
| 4 | Transient | 0…100 % | Bus | Punch/Attack-Betonung |
| 5 | Ceiling | −2…0 dBTP | Master | Limiter-Decke |
| 6 | Release | 0…100 % | Master | program-dependent Release |
| 7 | Mono | 0…200 Hz | Master | 0 = aus, Side-HPF |

`uid: qmst`, Vendor `r3d0xStyle`, Palette Anthrazit/Cyan wie QVerb.

### Signalwege

Master:
```
In → Trim → HPF 24 Hz (LR4) → Tilt → Mono-Maker → Clipper (2× OS)
   → TP-Limiter (Lookahead, 2× OS) → Out
```

Bus:
```
In → Trim → Transient → Clipper (2× OS) → Delay-Pad → Out
```

### Latenz
- Lookahead + OS-Gruppenlaufzeit ergeben eine feste Latenz L.
- Bus-Modus schiebt um L und nutzt die Verzögerung nicht.
- OS bleibt fest 2×. Ein 4×-Schalter würde L ändern und ist nicht MVP.
- `setLatency(L)` einmal in `prepare()`; kein Wechsel zur Laufzeit.

### Zustand / RT-Sicherheit
- `std::atomic<int> mode`; Config pro Block einmal auflösen, Branch außerhalb
  der Sample-Schleife.
- Keine Allokation, keine Locks im Audiopfad.
- Moduswechsel: 2 ms Fade + Detektor-Reset, damit kein Klick entsteht.

## 4. Phase 0 — Messen (kein Plugin)

Deliverables:
- `tools/measure.py`: WAV → JSON: LUFS-I, LRA, TP, PLR, 16-Band-Balance,
  Mono-Korrelation < 120 Hz, DC.
- `scripts/release-check.sh`: WAV → Report + Pass/Fail gegen die Tabelle oben.
- `scripts/codec-check.sh`: Ogg 320 erzeugen, zurückdekodieren, Spektrumdiff.
- `REPORT.md`: Baseline von 3 Beats (dry, mit QDSSD, mit QVerb).

Gate:
- MPC-Export **ohne** Normalisierung verifiziert (Peak ≠ −0,09 dBFS).
- Baseline-Zahlen liegen vor; ohne sie wird kein DSP gebaut.

Aufwand: ~1 Tag.

Status 2026-11-26: Harness gebaut (`tools/measure.py`, `tools/make-signals.py`,
`scripts/release-check.sh`, `scripts/codec-check.sh`, `tests/selftest.py`,
13/13 grün, `REPORT.md`). Offen: MPC-Export-Normalisierung, echte Beats.

## 5. Phase 1 — Skeleton + Master-Modus

Deliverables:
- Neues Repo (Framework + `gen_ui.py` + Build/Install aus `verb-mpc` übernommen).
- DSP: HPF, Tilt, Mono-Maker, Clipper (aus QVerb), TP-Limiter, feste Latenz.
- Native Harness: Null-Test, Latenz, Alias, TP.
- Erstes Preset „CD Loud".

Gate:
- Null-Test bit-transparent.
- TP ≤ −1,0 dBTP bei voller Aussteuerung.
- Alias ≤ −60 dBFS.
- Release-Check: 3 Beats erreichen −8 ± 1 LUFS, PLR ≥ 6.

Aufwand: ~4–5 Tage.

## 6. Phase 2 — Bus-Modus

Deliverables:
- Transient-Shaper + Clipper, Latenz-Pad auf L.
- Moduswechsel mit Fade, kein Klick.
- Presets „Bus Drums", „Bus 808".

Gate:
- Latenz identisch zu Master (Dirac).
- Null-Test im Bus-Modus bei Clip 0.
- 5 Instanzen + Master: keine Xruns im 10-min-Loop.

Aufwand: ~2–3 Tage.

## 7. Phase 3 — CD-Finish und Release

Deliverables:
- Presets: Init, CD Loud, Streaming Safe, Bus Drums, Bus 808.
- README (EN), HANDOVER (DE), Lizenz, Build/Install-Skripte.
- Release-ZIP, Tag `v1.0.0`.
- Export-Pipeline: 44,1 kHz, 16 Bit + TPDF-Dither im Skript (nicht im Plugin).

Gate:
- Release-Check auf allen 3 Beats grün.
- Codec-Check grün.
- Installation auf MPC verifiziert (SHA-256).

Aufwand: ~1–2 Tage.

## 8. Phase 4 — optional, nicht 1.0

- QMaster liest den Vocal-Bus (QDSSD-Protokoll) und senkt Kollisionsbänder.
- Nur wenn Phase 0/1 messbar zeigt, dass es nötig ist.

## 9. Tests

| Test | Signal | Kriterium |
|---|---|---|
| Latenz | Dirac | exakt L in beiden Modi |
| Null | Musik, Clip/Tilt 0 | bitidentisch |
| Alias | 997 Hz, −0,5 dBFS, Clip 100 % | ≤ −60 dBFS |
| Sweep | 20 Hz–20 kHz, −3 dBFS | keine Images > −60 dBFS |
| Unity | Pink Noise −20 dBFS | ±0,1 dB |
| Loudness | 3 Beats | −8 ± 1 LUFS, PLR 6–8 |
| Mono | Bass-Sine 60 Hz | keine Auslöschung |
| Schalten | 100× Mode | kein Klick > −60 dBFS |
| CPU | 1 + 5 Instanzen | keine Xruns, 48 kHz |

## 10. Risiken

| Risiko | Wirkung | Gegenmaßnahme |
|---|---|---|
| MPC-Export normalisiert | Mastering wirkungslos | Phase 0, Dialog prüfen |
| Lookahead-Latenz wird nicht kompensiert | Timing verschiebt | feste Latenz, Dirac-Test am Gerät |
| CPU bei 6 Instanzen | Dropouts | 2× OS fix, Profile messen |
| Clipper-Aliasing | harsche Höhen | 2× OS, Alias-Test als Gate |
| Kein Meter | blindes Mastering | Offline-Release-Check |
| Moduswechsel-Klick | Bühnenrisiko | 2 ms Fade, `automatable: false` |
| State in `.xpj` undurchsichtig | kein Offline-Edit | Presets + Dokumentation |

## 11. Misch-Voraussetzungen

- Mix bei −15…−18 LUFS, PLR 10–12.
- 808 mono, Kick/808 getrennt, Busse geclippt (QMaster Bus).
- Stimme vorne; Master fügt nur die letzten 3–5 dB hinzu.
- Referenz: 2–3 kommerzielle Tracks, loudness-gematcht hören.

## 12. Entscheidungen

1. **Vendor:** `r3d0xStyle` — konsistent mit QDSSD.
2. **Name:** `qmaster-mpc`, Ordner `~/Dev/qmaster-mpc`.
3. **Plattform:** MPC only. Kein Desktop-Build; native Kompilierung nur für
   Host-Simulator und Tests.
4. **Bus-Modus ohne Tilt.** Begründung: Tilt formt die Summe, bevor sie
   geclippt wird, und konkurriert mit dem Master-Tilt. EQ gehört pro Quelle.
   Der Bus bleibt auf seine Rolle beschränkt: Pegel, Punch, Dichte.
   Falls sich im Test zeigt, dass ein Bus-Tilt fehlt, ist er ein späteres
   Programm, kein neuer Parameter.

## 13. Qualitätssicherung — Fehlervermeidung

Prinzip: Fehler unmöglich machen, nicht nur finden. Vier Schichten, absteigend
nach Wirkung.

### 13.1 Typen und Invarianten

Die häufigsten DSP-Bugs sind Einheitenfehler (absolut vs. relativ, dB vs.
linear, Samples vs. Sekunden). Sie werden durch Typen verhindert, nicht durch
Tests.

```cpp
struct Db  { float v; };   // relativ zu 0 dBFS
struct Lin { float v; };   // linear
struct Hz  { float v; };
struct Sec { float v; };
```

Regeln:
- Keine nackten floats über Systemgrenzen (Parameter, Audio, Masken).
- Clamping an jeder Grenze: Parameter, Ceiling, Frequenzen, Eingang.
- Koeffizienten in `double` in `prepare()`, pro Sample `float`.
- Keine `pow`/`exp`/`log` im Audiopfad.
- Jeden Parameter glätten (Gain, Tilt, Ceiling) — sonst Zipper/Klicks.
- `static_assert` für Puffergrößen und spätere Shared-Memory-Layouts
  (Magic, Version, `sizeof == N`).
- Compiler: `-Wall -Wextra -Werror`. **Kein `-ffast-math`** — es zerstört
  NaN-Checks und Denormal-Handling.

### 13.2 Tests als Gates

| Test | Findet |
|---|---|
| Impuls | Latenz, OLA-Offset, Filtergruppe |
| Null (Bypass-Zustand) | „klingt anders, obwohl nichts an ist" |
| Crosstalk L≠R | geteilte Puffer zwischen Kanälen |
| Gain-Invarianz (Eingang ×0,5 → Maske gleich) | absolute statt relative Pegel |
| Reset-Determinismus | versteckter Zustand |
| Sweep 20 Hz–20 kHz | Aliasing, Instabilität |
| Denormal/Silence 60 s | CPU-Explosion im Tail |
| Fuzz (Zufallsparameter + Rauschen) | NaN, Inf, Absturz |
| Soak 10 min | Drift, Leck, Xruns |

Golden Files: kurze Impulsantworten und Referenzblöcke im Repo, Vergleich mit
Toleranz (z. B. −120 dBFS). Jede ungewollte DSP-Änderung fällt sofort auf.

Mutationstest light: einen Koeffizienten absichtlich um 1 % verändern — schlägt
kein Test an, ist der Test wertlos.

### 13.3 Prozess

- Test zuerst: für jede DSP-Stufe erst den roten Test.
- Ein Commit = eine Stufe (HPF, Tilt, Mono, Clipper, Limiter getrennt), damit
  `git bisect` funktioniert.
- `./scripts/check.sh` als einzige Wahrheit: nativer Build, alle Tests,
  `validate.py`, UI-Validierung.
- Sanitizer (ASan/UBSan) im nativen Testbuild.
- Allokations-Verbot prüfen: Hook, der im `process()` bei `new`/`malloc`/Lock
  abbricht.
- `DECISIONS.md` pflegen (warum 2× OS, warum feste Latenz, warum kein Bus-Tilt).
- Red-Team-Agent: bekommt nur Plan + Tests und sucht Lücken — nicht der Agent,
  der implementiert hat.

### 13.4 Gerät (MPC-spezifisch)

- Export-Normalisierung einmal verifizieren, in `REPORT.md` festhalten.
- Latenz per Dirac auf dem Gerät prüfen, nicht nur nativ.
- Beide ABIs bauen und installieren (ARM64 und ARM32).
- 1× Master + 5× Bus im 10-Minuten-Loop; Aufnahme auf Sprünge/Klicks prüfen.
- State-Roundtrip: Preset speichern, MPC neu starten, laden, Parameter
  vergleichen (die `.xpj` ist undurchsichtig).
- SHA-256 der installierten Dateien gegen den Build prüfen.

### 13.5 Eigene Bugs als Regressionstests

| Damals | Heute als Test |
|---|---|
| geteilter FFT-Puffer L/R | Crosstalk L≠R < −100 dB |
| OLA-Ring-Offset | Impuls an erwarteter Position, Rekonstruktion = 1 |
| absolute dB im Spektrum | Gain-Invarianz der Maske |
| Lazy-Bus-Open | Empfänger vor Sender konstruieren, Daten müssen fließen |
| pegelabhängiger Breitband-Floor | Pegel-Sweep, Duck-Kurve monoton und pegelunabhängig |

### 13.6 Definition of Done pro Phase

1. `check.sh` grün (nativ).
2. Messwerte in `REPORT.md` aktualisiert (LUFS, TP, PLR, Alias).
3. Gerätetest bestanden (Latenz, 6 Instanzen, State-Roundtrip).
4. `DECISIONS.md` und `KNOWN_ISSUES.md` aktuell.
5. Erst dann Commit/Tag.

Leitsatz: **Was nicht messbar ist, ist nicht gebaut.**
