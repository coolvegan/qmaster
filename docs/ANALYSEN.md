# Analysen — Archiv

Alle Messungen, die in den Lektionen und im `REPORT.md` verwendet werden.
Jede Analyse nennt Quelle, Methode, Zahlen, Einordnung und die Lektion, in der
sie erzählt wird.

## Übersicht

| # | Analyse | Datum | Kernzahl | Lektion |
|---|---|---|---|---|
| A1 | Messkette gegen bekannte Pegel | 26.11.2026 | 13/13 Prüfungen | 01 |
| A2 | Synthetische Signale | 26.11.2026 | LUFS mono/stereo, TP +0,90 | 01 |
| A3 | Plugin nativ (Latenz, TP, Alias) | 26.11.2026 | 102 Samples, −105 dBc | 03 |
| A4 | End-to-End Loop | 26.11.2026 | −11,0 → −8,5 LUFS | 03, 06 |
| A5 | Erste echte Exporte (Under One Sun) | 26.11.2026 | Rohmix −18,3 LUFS | 01, 06 |
| A6 | Rohmix-Sweep (Trim × Clip) | 26.11.2026 | 8 Korridor-Treffer | 03, 06 |
| A7 | Bandpass-Leckage vs. FFT | 26.11.2026 | −25 dBFS war Leckage | 02 |
| A8 | Fehlinterpretation „Normalisierung“ | 26.11.2026 | PLR 7,7 ≠ 17,7 | 01, 05 |
| A9 | CD-Loud-Export, verteilte Kette | 26.11.2026 | −7,8 LUFS, PLR 6,5 | 03, 06 |
| A10 | „Seele“ alt vs. neu | 26.11.2026 | −12,5 → −10,9 LUFS, TP +1,4 → −0,4 | 03, 06 |

---

## A1 — Messkette gegen bekannte Pegel

**Quelle:** `tests/selftest.py`, Testsignale aus `tools/make-signals.py`.
**Methode:** Signale mit analytisch bekannten Werten, Vergleich mit Toleranz.
**Ergebnis:** 13/13.

| Prüfung | Soll | Ist |
|---|---|---|
| Sinus 997 Hz, A = 0,5, Peak | −6,02 dBFS | −6,02 |
| derselbe Sinus, RMS | −9,03 dBFS | −9,03 |
| derselbe Sinus, mono, LUFS | −9,0 | −9,00 |
| derselbe Sinus, stereo, LUFS | −6,0 | −6,00 |
| Dirac, Peak | −0,92 dBFS | −0,92 |
| Pink Noise, RMS | −20,0 dBFS | −20,00 |
| Anti-Phase 60 Hz, Korrelation | −1,0 | −1,000 |
| Anti-Phase, Mid | null | null |
| Release-Guard auf nicht releasefähigem Loop | FAIL | FAIL (erwartet) |

**Einordnung:** Ohne diesen Test sind alle anderen Zahlen wertlos. Der Test
prüft die Messkette, nicht das Plugin.
**Lektion:** 01, Abschnitt „Testmethoden".

---

## A2 — Synthetische Signale

**Quelle:** `tools/make-signals.py`, 44,1 kHz, 16 Bit, stereo.

| Signal | Dauer | Peak | RMS | LUFS | TP | PLR | LRA |
|---|---|---|---|---|---|---|---|
| Sinus 997, A = 0,5, mono | 5 s | −6,02 | −9,03 | −9,0 | −6,0 | 3,0 | 0,0 |
| Sinus 997, stereo identisch | 5 s | −6,02 | −9,03 | −6,0 | −6,0 | 0,0 | 0,0 |
| Sinus 997, nur links | 5 s | −6,02 | −12,04 | −9,0 | −6,0 | 3,0 | 0,0 |
| Dirac | 1 s | −0,92 | — | — | −0,90 | — | — |
| Pink Noise, RMS −20 | 10 s | −7,41 | −20,00 | −18,8 | −7,4 | 11,4 | 0,1 |
| Anti-Phase 60 Hz | 5 s | −6,02 | −9,03 | −9,6 | −6,0 | 3,6 | 0,0 |
| Loop (Kick/Bass/Snare/Hat) | 20 s | −1,01 | −10,25 | −11,0 | **+0,90** | 11,9 | 0,8 |

**Befunde:**
- Stereo summiert +3,01 dB (Leistungssumme der Kanäle).
- Links-only: RMS über alle Samples −12,04, Loudness −9,0 — RMS und LUFS sind
  nicht dasselbe.
- Der Loop hat bei −1,01 dBFS Sample-Peak **+0,90 dBTP**: 1,91 dB
  Intersample-Überschreitung.
**Lektion:** 01.

---

## A3 — Plugin nativ

**Quelle:** `host_sim`, `tests/plugin-check.py`, `tests/alias-check.py`.
**Build:** ARM64/ARM32, `validate.py` 0 Fehler / 0 Warnungen.

| Prüfung | Ergebnis |
|---|---|
| Latenz Master | 102 Samples gemessen, 102 gemeldet |
| Latenz Bus | 102 Samples, identisch |
| TP default (Clip 30) | −1,40 dBTP |
| TP Clip 100 | −1,20 dBTP |
| TP Ceiling −2 | −2,40 dBTP |
| Alias Clip 0 | −120,0 dBc |
| Alias Clip 100 | −105,4 dBc bei 19175 Hz |
| Programme | Init, CD Loud, Streaming Safe, Bus Drums, Bus 808 |
| Mode automatisierbar | nein |

**Aufbau:** Clipper bei 2× (31-Tap-Halfband), Limiter bei 1× mit
4×-Detektor (zwei Halfband-Stufen) und 0,40 dB Guard.
**Lektion:** 03; die Alias-Methode in 02.

---

## A4 — End-to-End Loop

**Quelle:** `tools/render.cpp`, Programm „CD Loud" (Index 1).
**Eingang:** `loud_loop.wav` (A2).

| Größe | vorher | nachher |
|---|---|---|
| Integrated | −11,0 LUFS | **−8,5 LUFS** |
| True Peak | +0,90 dBTP | **−1,10 dBTP** |
| PLR | 11,9 | **7,4** |
| Clipping | 0 | 0 |

**Lektion:** 03, 06.

---

## A5 — Erste echte Exporte: „90 Under One Sun"

**Quelle:** SSD, 44,1 kHz, 24 Bit, 19,46 s.
**Dateien:**
- `90-Under-One-Sun-NoFx.wav` (alt, alte Master-Kette)
- `90-Under-One-Sun-Fx.wav` (alt, alte Master-Kette)
- `90-Under-One-Sun-FX-master.wav` (Bus-Modus)
- `90-Under-One-Sun-FX-master-2.wav` (Master-Modus)
- `90-Under-One-Sun-FX-157.wav` (**Rohmix, ohne Master-Effekt**)

| Datei | Modus | LUFS | TP | PLR | LRA | Side−Mid |
|---|---|---|---|---|---|---|
| NoFx (alt) | ohne FX | −7,6 | +0,1 | 7,7 | 1,2 | −29,0 |
| Fx (alt) | mit FX | −8,0 | +0,2 | 8,2 | 1,4 | −30,4 |
| FX-master | Bus | −18,3 | −0,6 | 17,7 | 3,1 | −23,9 |
| FX-master-2 | Master | −14,0 | −0,5 | 13,5 | 2,4 | −41,0 |
| **FX-157** | **roh** | **−18,3** | **−0,6** | **17,7** | 3,1 | −23,9 |

**Befunde:**
1. **Die MPC normalisiert nicht** (vom Nutzer bestätigt). Die alten Referenzen
   peakten zwar exakt bei −0,09 dBFS, aber das war der **Limiter der alten
   Master-Kette**: 309 bzw. 261 Samples liegen auf 0,99, und der PLR ist 7,7
   statt 17,7. Eine reine Pegelanhebung kann den PLR nicht ändern. Der Rohmix
   liegt bei **−18,3 LUFS**. Die alte Kette bestand aus vier Plugins —
   Kompressor, Clipper, Maximizer und ein weiteres (Nutzerangabe); der
   Maximizer bildete die Decke bei −0,09 dBFS.
2. `FX-master` (Bus) ist praktisch identisch mit dem Rohmix: Clip 41 hat bei
   diesem niedrigen Eingangspegel fast nichts getan; ohne Limiter bleibt
   PLR 17,7.
3. `FX-master-2` (Master) arbeitet, ist aber mit Trim +3,8 / Clip 18 nur
   −14,0 LUFS. Für −8 fehlen rund 6 dB.
4. Mono 200 Hz ist zu aggressiv: Side−Mid −41 dB; 110–120 Hz reichen.

**Lektion:** 01 (Normalisierung), 03 (Limiter/Mono), 06 (Programmwahl).

---

## A6 — Rohmix-Sweep (Trim × Clip)

**Quelle:** `raw-157` durch `build/render`, Master-Modus, Ceiling −1,
Release 45, Mono 120, Tilt 0.
**Raster:** Trim +4…+12 × Clip 30…75 = 25 Läufe.
**Korridor:** −9…−7 LUFS, TP ≤ −1,0, PLR 6–8 → **8 Treffer**.

| Trim | Clip | LUFS | TP | PLR |
|---|---|---|---|---|
| **+8** | **55** | **−8,1** | **−1,40** | **6,70** |
| +6 | 65 | −8,6 | −1,40 | 7,20 |
| +10 | 30 | −8,8 | −1,40 | 7,40 |
| +8 | 45 | −8,9 | −1,40 | 7,50 |
| +10 | 45 | −7,6 | −1,40 | 6,20 |
| +12 | 30 | −7,5 | −1,40 | 6,10 |
| +6 | 75 | −7,9 | −1,40 | 6,50 |
| +8 | 65 | −7,4 | −1,40 | 6,00 |

Zu heiß: Trim +10/Clip 55 → −6,9 LUFS, PLR 5,5; Trim +12/Clip 45 → −6,5, PLR 5,2.

**Feinsweep** (Trim +6,5…+8 × Clip 48…56):

| Trim | Clip | LUFS | PLR |
|---|---|---|---|
| +8,0 | 56 | −8,1 | 6,7 |
| +7,5 | 56 | −8,4 | 7,0 |
| +8,0 | 52 | −8,4 | 7,0 |
| +7,0 | 56 | −8,7 | 7,3 |
| +6,5 | 56 | −9,0 | 7,6 |

Die alte Vierer-Kette erreichte −8,0 bei PLR 7,7–8,2. QMaster allein ist bei
gleicher Lautheit rund 1 dB dichter: Der Kompressor der alten Kette hat die
Gain Reduction gleichmäßiger verteilt als Clipper plus Limiter.

**Empfehlung:** Trim +8, Clip 55, Ceiling −1,0, Release 45, Mono 120.
**Caveat:** Der Rohmix hat PLR 17,7; für −8 müssen ~10 dB Spitzenkontrolle
geleistet werden. Das ist die Obergrenze des Materials — bei einem dichteren
Mix klingt derselbe Korridor besser.
**Lektion:** 03 (Ballistik), 06 (Capstone).

---

## A9 — CD-Loud-Export mit verteilter Kette

**Quelle:** `90-Under-One-Sun-FX-Cd-loud-preset.wav`, 44,1 kHz, 24 Bit,
19,46 s.
**Aufbau:** QMaster **Bus Drums** auf dem Drum-Bus, QMaster **CD Loud** auf dem
Master. Rohmix davor −18,3 LUFS (A5).

| Größe | Ergebnis |
|---|---|
| Integrated | **−7,8 LUFS** |
| True Peak | **−1,30 dBTP** |
| PLR | **6,5** |
| LRA | 1,3 LU |
| Mono Side−Mid | −32,0 dB |
| Clipping | 0 |

**Einordnung:** Der Korridor ist getroffen (−8 ±1, TP ≤ −1, PLR 6–8).
Gegenüber dem einzelnen CD-Loud-Master (−8,1 / 6,7) ist das nur 0,3 dB lauter
und 0,2 dB dichter: Der Bus-Clip verschiebt die Lautheit kaum, der Master
macht die Hauptarbeit.

Die alte Vierer-Kette lag bei −8,0 / PLR 8,2. Für mehr Dynamik müsste der
Master-Clip auf ~48 und Trim auf +7 (A6: −8,7 / 7,3), der Bus dafür heißer.

LRA 1,3 ist kein Fehler: Der Ausschnitt ist 19,5 s und repetitiv; die alten
Referenzen lagen ebenfalls bei 1,2–1,4.

**Lektion:** 06 (Capstone), 03 (Gain-Reduction-Verteilung).

---

## A10 — „Seele“: alte Vierer-Kette vs. QMaster

**Quellen:** `0089-Seele-Check-alte kette.wav` und
`0089-Seele-Check-Neue-kette.wav`, 44,1 kHz, 24 Bit, 106,67 s.
Die alte Kette ist dieselbe Vierer-Kette (Kompressor, Clipper, Maximizer);
die neue ist QMaster **Bus Drums** auf dem Drum-Bus plus **CD Loud** auf dem
Master.

| Größe | alte Kette | neue Kette |
|---|---|---|
| Integrated | −12,5 LUFS | **−10,9 LUFS** |
| True Peak | **+1,40 dBTP** | −0,40 dBTP |
| PLR | 13,9 | 10,5 |
| LRA | 6,1 LU | 7,6 LU |
| Mono Side−Mid | −29,8 dB | −37,4 dB |

### Befunde

1. **Die neue Kette ist 1,6 dB lauter und 3,4 dB dichter.** Der Korridor
   (−8 ±1, PLR 6–8) wird auf diesem Song nicht erreicht: Er ist dynamischer
   als „Under One Sun“, und die Presets wurden dort eingemessen.
2. **True Peak: +1,4 dBTP alt, −0,4 dBTP neu.** Die neue Kette ist deutlich
   sicherer, liegt aber noch 0,6 dB über dem Ziel −1,0. Der 0,40-dB-Guard
   reicht für dieses Material nicht.
3. **Die Mitten sind relativ zum Sub 3–5,6 dB leiser** (204 Hz bis 13 kHz).
   Die neue Kette ist basslastiger und mittiger leer. Bei „Under One Sun“ war
   sie noch 1–3 dB heller — die Wirkung ist materialabhängig.
4. Der Unterschied entsteht vermutlich durch das starke Master-Clipping:
   Sub-Sinuswellen passieren, Mittenspitzen werden abgeschnitten.

### Empfehlung

- **Ceiling auf −1,6 dBTP** für diesen Song, dann liegt der TP bei ≈ −1,0;
  kostet 0,6 dB Lautheit.
- **Clip auf 45, Trim auf +6, Tilt +1,0 … +1,5**, um die Mitten
  zurückzuholen; die Lautheit kommt dann aus dem Bus, nicht aus dem Master.
- Für eine exakte Einmessung fehlt ein **Roh-Export von „Seele“ ohne
  Master-Kette**.

### Produktfolgen

- Der TP-Guard von 0,40 dB ist nicht materialunabhängig. Nächster Schritt:
  Guard auf 0,8–1,0 dB erhöhen oder den 4×-Detektor auf 8× erweitern.
- Presets sind Startpunkte, keine Garantie. Ein Preset pro Songtyp wäre
  sinnvoller als ein „CD Loud“ für alles.

**Lektion:** 03 (Limiter, Guard), 06 (Capstone, materialabhängige Ziele).

---

## A7 — Bandpass-Leckage vs. FFT

**Quelle:** 997-Hz-Ton, Clip 100, Ausgang des Plugins.
**Methode 1:** `bandpass=f=…:width_type=q:w=30` + `astats`.
**Ergebnis 1:** „Alias" bei 1229 Hz mit −25,3 dBFS — **unverändert**, egal ob
15 oder 31 Filter-Taps. Verdacht: Messfehler.
**Methode 2:** FFT, 65536 Punkte, Hann-Fenster, Bin 0,67 Hz.
**Ergebnis 2:** stärkster echter Alias **−105,4 dBc** bei 19175 Hz.

**Erklärung:** Ein Bandpass 2. Ordnung mit Q = 30 dämpft einen 232 Hz
entfernten Ton nur um ~22 dB. Aus −3,2 dBFS Grundton wird −25,3 dBFS
„Alias" — reine Leckage.

**Regel:** Ändert sich ein Ergebnis nicht, wenn man das System ändert, ist die
Messung verdächtig.
**Lektion:** 02.

---

## A8 — Fehlinterpretation: scheinbare Normalisierung

**Quelle:** alte MPC-Exporte (`NoFx`, `Fx`), 44,1 kHz, 24 Bit.
**Beobachtung:** Beide peakten exakt bei −0,09 dBFS. Daraus wurde geschlossen:
„der MPC-Export normalisiert“.
**Korrektur (Nutzer, 26.11.2026):** Die MPC nimmt **keine** Normalisierung vor.
**Gegenbeweis:**

- PLR 7,7 bzw. 8,2 gegen 17,7 beim Rohmix. Eine Pegelanhebung verschiebt TP und
  LUFS gemeinsam und lässt den PLR unverändert. Der Unterschied ist also
  Dynamikbearbeitung, keine Verstärkung.
- 309 bzw. 261 Samples liegen bei 0,99 — eine Limiter-Decke, nicht ein
  einzelner normalisierter Spitzenwert.

**Ursache:** Der Limiter der alten Master-Kette saß bei −0,09 dBFS.
**Lehre:** Eine einzelne Zahl ist kein Ursachenbeweis. Zweite, unabhängige
Metrik prüfen (PLR, Sample-Verteilung), sonst wird aus einem Limiter eine
Normalisierung.
**Lektion:** 01 (Fehler), 05 (Fehlerkatalog, Vorgehen).

---

## Reproduktion

```bash
python3 tools/make-signals.py /tmp/qm-signals
python3 tests/selftest.py
python3 tests/plugin-check.py
python3 tests/alias-check.py 997 --clip 1.0
python3 tests/loudness-check.py
python3 tools/measure.py /tmp/opencode/exports/raw-157.wav
build/render build/native/qmaster.so in.wav out.wav --program 1
```

Die Rohdaten der Exporte liegen nicht im Repo (Musik, Größe). Die Tabellen
enthalten alle Werte, die für die Lektionen gebraucht werden.

## A7 — Clipper-Knie und Preset-Drive (27.11.2026)

**Frage:** Warum kratzt die Kick im Bass, obwohl der Limiter sauber arbeitet?

**Messung:** Synthetischer Kick (−1 dBFS, 45–120 Hz Sweep) und 55-Hz-Sinus
durch den nativen Build, Programm „CD Loud“ (alt: Trim +8, Clip 55; neu:
Trim 0, Clip 40). Analyse per FFT (8192 Punkte, Hann) relativ zum Grundton.

| Größe | alt | neu |
|---|---|---|
| Kick 120–500 Hz | −17,7 dB | −75,4 dB |
| Kick 0,5–2 kHz | −41,0 dB | −106,7 dB |
| Kick 2–8 kHz | −63,9 dB | −131,8 dB |
| 55 Hz THD | −10,7 dB | −35,5 dB |
| Loop-Lautheit | −8,5 LUFS | −8,4 LUFS |
| Loop-PLR | 7,4 dB | 7,3 dB |

**Ursache:** Knie 0,35 dB = Hard-Clip; Preset-Drive +14,6 dB. Der Clipper
begrenzt bei 0,96, unabhängig vom eingestellten Ceiling (−1 bis −2 dBTP).

**Korrektur:** Knie 2 dB, Schwelle = Ceiling; Presets auf Trim 0 und Clip
20–40 neu eingemessen. Bus-Modus: eigenes Ceiling −1,0 dBFS.

**Offen:** Ein Preset bleibt pegelabhängig. Ein Auto-Trim (langsamer
Peak-Detektor vor dem Clipper) wäre die nächste Stufe, ist aber noch nicht
implementiert.

