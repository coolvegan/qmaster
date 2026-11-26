# Lektionen — Arbeitsweise

Die Lektionen entstehen **während** der Entwicklung, werden aber **erst am Ende
als Ganzes** veröffentlicht. Bis dahin sind sie Drafts im Repo.

## Regel

1. Jede Phase schreibt ihre Lektion (Body, Szenen, Quiz) direkt in
   `lessons/<nummer>-<thema>/`.
2. `lesson.json` bleibt auf `"status": "draft"`, solange die Phase nicht
   abgeschlossen ist.
3. Veröffentlicht wird **einmal**, wenn alle Lektionen `"status": "final"`
   haben und der Release-Check grün ist.
4. `scripts/publish-lessons.sh` verweigert jede Veröffentlichung, solange ein
   Draft dabei ist oder `PUBLISH_CONFIRM=yes` fehlt.

## Zuordnung Phase → Lektion

| Lektion | Phase | Kern |
|---|---|---|
| 00 Lernpfad | — | Übersicht und Reihenfolge |
| 01 Lautheit | 0 | dB, RMS, LUFS, True Peak, PLR |
| 02 Clipper | 1 | Transferfunktion, Harmonische, Aliasing, Oversampling |
| 03 Limiter | 1 | Hüllkurve, Attack/Release, Lookahead |
| 04 Filter und Mono | 2 | Biquad, Pole, Shelf, M/S |
| 05 Code-Generierung | 2/3 | Spezifikation → Test → Code → Review |
| 06 Capstone | 3 | Beat mastern, messen, iterieren |

## Aufbau einer Lektion

```
lessons/<name>/
├── lesson.json     Titel, Summary, Tags, Level, status
├── body.md         Markdown; pro Kapitel: Frage → Mathe → Code → Messung
├── scenes/*.json   deklarative Szenen (width, height, steps)
└── quiz.json       Array aus question/options/answer/explanation
```

Jedes Kapitel endet mit 6–8 Quizfragen, mindestens zwei davon Rechenaufgaben.
Kein Video.

## Freeze-Checkliste (100 %)

- [ ] Alle `lesson.json` haben `"status": "final"`.
- [ ] Jede Zahl im Text stimmt mit dem letzten `REPORT.md` überein.
- [ ] Alle Quiz-Antworten nachgerechnet, nicht geschätzt.
- [ ] Alle Szenen rendern lokal fehlerfrei (keine fehlenden Typen, keine
      Koordinaten außerhalb des Canvas).
- [ ] Interne Links und Repo-Verweise existieren.
- [ ] Sprache gelesen: keine Platzhalter, kein „DRAFT", keine veralteten
      Behauptungen aus früheren Phasen.
- [ ] `scripts/release-check.sh` grün.
- [ ] Erst dann: `PUBLISH_CONFIRM=yes ./scripts/publish-lessons.sh`.

Der letzte Punkt ist absichtlich manuell. 100 % ist eine Checkliste, kein
Gefühl.
