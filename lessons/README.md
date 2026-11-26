# Lektionen — Arbeitsweise

Die Lektionen entstehen **während** der Entwicklung, werden aber **erst am Ende
als Ganzes** veröffentlicht. Bis dahin sind sie Drafts im Repo.

Quellen für Zahlen und Befehle:
[`docs/ANALYSEN.md`](../docs/ANALYSEN.md) und
[`docs/WERKZEUGE.md`](../docs/WERKZEUGE.md).

## Regel

1. Jede Phase schreibt ihre Lektion (Body, Szenen, Quiz) direkt in
   `lessons/<nummer>-<thema>/`.
2. `lesson.json` bleibt auf `"status": "draft"`, solange die Phase nicht
   abgeschlossen ist.
3. Veröffentlicht wird **einmal**, wenn alle Lektionen `"status": "final"`
   haben und der Release-Check grün ist.
4. `scripts/publish-lessons.sh` verweigert jede Veröffentlichung, solange ein
   Draft dabei ist oder `PUBLISH_CONFIRM=yes` fehlt.

## Aufbau einer Lektion

```
lessons/<name>/
├── lesson.json     Titel, Summary, Tags, Level, status
├── body.md         Markdown
├── scenes/*.json   deklarative Szenen (width, height, steps)
└── quiz.json       Array aus question/options/answer/explanation
```

Jedes Kapitel folgt sechs Schritten, nicht vier:

1. **Die Frage** — das Problem, das wirklich anlag.
2. **Die Mathematik** — Herleitung mit den Zahlen aus dem Projekt.
3. **Der Code** — die Stelle im Repo, die daraus wurde.
4. **Die Messung** — was der Test zeigt.
5. **Fehler & Test** — was schiefging, wie es gefunden wurde und welcher Test
   es heute verhindert.
6. **Anwendung** — welches Programm, welcher Regler, welche Zahl.

Kein Video. Jede Lektion endet mit 8–12 Quizfragen, mindestens zwei
Rechenaufgaben.

## Fehlerkatalog (muss in der Reihe vorkommen)

Jeder Fehler, der im Projekt wirklich passiert ist, wird erzählt — mit
Fundstelle, Ursache und dem Test, der ihn verhindert.

| Fehler | Lektion | Test, der ihn heute verhindert |
|---|---|---|
| Geteilter FFT-Puffer zwischen L/R (QDSSD) | 05 | Crosstalk L≠R < −100 dB |
| OLA-Ring-Offset (QDSSD) | 05 | Impuls an erwarteter Position |
| Absolute statt relative dB (QDSSD) | 05, 01 | Gain-Invarianz der Maske |
| Lazy Bus Open (QDSSD) | 05 | Empfänger vor Sender konstruieren |
| Fehlinterpretation: −0,09 dBFS als Normalisierung gedeutet (eigentlich Limiter der alten Vierer-Kette) | 01, 05 | PLR vergleichen, Samples an der Decke zählen |
| Mono-Downmix überschreitet 0 dBFS (ffmpeg) | 01 | Stereo-Peak, nie Downmix |
| Bandpass-Leckage als „Alias" gedeutet | 02 | FFT statt Bandpass |
| 24-Bit-WAV falsch geschrieben | 05 | Erwarteter Peak nach dem Render |
| Ceiling-Smoother startet ungeguardet | 03 | Peak-Zeitpunkt prüfen |
| „4×"-Detektor war nur 2× | 03 | TP gegen Sample-Peak prüfen |
| Moduswechsel ohne Reset | 03 | Latenz- und Klick-Test |

## Testmethoden-Katalog (jede Methode einmal erklären)

| Methode | Lektion | Was sie beweist |
|---|---|---|
| Signale mit bekanntem Pegel (Sinus, Dirac, Pink, Antiphase) | 01 | Die Messkette selbst stimmt |
| Selbsttest der Messkette | 01 | Zahlen sind nicht nur plausibel |
| LUFS/TP/PLR gegen Zielkorridor | 01, 06 | Release-Fähigkeit |
| FFT mit Hann-Fenster statt Bandpass | 02 | Aliasing ohne Leckage |
| Impuls-Test | 03 | Latenz, Group Delay, Alignment |
| TP vs. Sample-Peak | 01, 03 | Intersample-Spitzen |
| Null-/Unity-Test | 04 | Kein versteckter Gain |
| Crosstalk-Test | 05 | Kanäle teilen keinen Zustand |
| Gain-Invarianz | 05 | Relative statt absolute Pegel |
| Zwei unabhängige Metriken (PLR + Sample-Verteilung) | 01, 05 | Unterscheidet Limiter von Normalisierung |
| State-Roundtrip | 06 | Preset überlebt Neustart |
| 10-Minuten-Soak | 06 | Keine Xruns, kein Drift |

## Programm- und Werkzeugkatalog

| Programm | Werte | Gemessen |
|---|---|---|
| Init | Clip 0, Ceiling −1, Mono 120 | neutral |
| CD Loud | Trim +8, Clip 55, Ceiling −1, Release 45, Mono 120 | **−8,1 LUFS, −1,40 dBTP, PLR 6,7** |
| CD Dynamic | Trim +7,5, Clip 56, sonst wie CD Loud | **−8,4 LUFS, PLR 7,0** |
| Streaming Safe | Trim +5, Clip 45, Ceiling −1,5, Release 60 | noch nicht gemessen |
| Bus Drums | Mode Bus, Clip 45, Transient 45 | noch nicht gemessen |
| Bus 808 | Mode Bus, Clip 55, Transient 20 | noch nicht gemessen |

Ein Programmwechsel meldet dem Host alle Parameter (`audioMasterAutomate`) und
fordert ein Redraw an (`audioMasterUpdateDisplay`). Ohne diese Meldungen bleibt
die MPC-UI auf den alten Knopfpositionen stehen.

| Werkzeug | Aufgabe | Lektion |
|---|---|---|
| `tools/measure.py` | LUFS, TP, PLR, LRA, Bänder, Mono | 01 |
| `scripts/release-check.sh` | Zielkorridor als Pass/Fail | 01, 06 |
| `scripts/codec-check.sh` | Ogg-320-Durchlauf | 01 |
| `tools/render.cpp` | WAV offline durch das Plugin | 03 |
| `scripts/check.sh` | eine Wahrheit vor dem Commit | 05 |

## Vorgehen (Lektion 05)

Die Meta-Lektion erzählt den Arbeitsablauf, nicht nur den Code:

- Phase 0 vor DSP: erst messen, dann bauen.
- Spezifikation → Test → Code → Messung → Review.
- Ein Commit pro DSP-Stufe, damit `git bisect` funktioniert.
- `check.sh` als einzige Wahrheit.
- Red-Team-Agent, der nur Plan und Tests sieht.
- Entscheidungen in `DECISIONS.md`, Fehler in `KNOWN_ISSUES.md`.
- Veröffentlichung erst nach der Freeze-Checkliste.

## Zuordnung Phase → Lektion

| Lektion | Phase | Kern |
|---|---|---|
| 00 Lernpfad | — | Übersicht, Reihenfolge, Fehler- und Testversprechen |
| 01 Lautheit | 0 | dB, RMS, LUFS, True Peak, PLR, Messtraps |
| 02 Clipper | 1 | Transferfunktion, Harmonische, Aliasing, FFT-Test |
| 03 Limiter | 1 | Hüllkurve, Lookahead, 4×-Detektor, Latenz, Verteilung der Gain Reduction |
| 04 Filter und Mono | 2 | Biquad, Pole, Shelf, M/S, Unity-Test |
| 05 Code-Generierung | 2/3 | Vorgehen, Fehlerkatalog, Testvertrag, Review |
| 06 Capstone | 3 | Beat mastern, Programme messen, Release |

## Freeze-Checkliste (100 %)

- [ ] Alle `lesson.json` haben `"status": "final"`.
- [ ] Jede Zahl im Text stimmt mit dem letzten `REPORT.md` überein.
- [ ] Alle Quiz-Antworten nachgerechnet, nicht geschätzt.
- [ ] Alle Szenen rendern lokal fehlerfrei.
- [ ] Interne Links und Repo-Verweise existieren.
- [ ] **Jeder Eintrag im Fehlerkatalog kommt in seiner Lektion vor.**
- [ ] **Jede verwendete Testmethode ist mindestens einmal erklärt.**
- [ ] **Jedes Programm hat gemessene Zahlen oder ist als „nicht gemessen" markiert.**
- [ ] **Lektion 05 beschreibt das Vorgehen, nicht nur das Ergebnis.**
- [ ] Sprache gelesen: keine Platzhalter, kein „DRAFT", keine veralteten
      Behauptungen.
- [ ] `scripts/release-check.sh` grün.
- [ ] Erst dann: `PUBLISH_CONFIRM=yes ./scripts/publish-lessons.sh`.
