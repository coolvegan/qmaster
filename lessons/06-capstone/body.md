Ein Master ist erst fertig, wenn er gemessen ist. Diese Lektion führt die
Zahlen aus Lautheit, Clipper, Limiter und Filter zu einer Kette zusammen — und
prüft sie an einem echten Export. Die Frage ist nicht, ob das Plugin läuft,
sondern ob es auf Musik läuft.

## 1. Der Prüfstein: Musik statt Testsignal

### Die Frage

Die bisherigen Lektionen haben die Messkette an Signalen mit bekanntem Pegel
geprüft und die Kette an einem synthetischen Loop getestet. Der Loop ist kein
Song. Er hat keine Strophen, keine 808, keine Vocals und keinen Arrangement-
Unterschied zwischen Intro und Hook.

Die Frage lautet deshalb: Trägt die Kette auch auf einer echten Produktion —
und zwar so, dass man es nachrechnen kann? Ein Höreindruck reicht dafür nicht.
Es braucht vier Zahlen, die alle gleichzeitig stimmen.

### Die Mathematik

Der Zielkorridor ist eine Konjunktion, keine Auswahl:

| Größe | Ziel | Bedeutung |
|---|---|---|
| Integrated | −8 ± 1 LUFS, also −9 bis −7 | kompetitive CD-Lautheit |
| True Peak | ≤ −1,0 dBTP | Reserve für Codec und Wandler |
| PLR | 6 bis 8 dB | dicht, aber nicht tot |
| LRA | 4 bis 7 LU | der Track atmet noch |

Die LRA wird nur geprüft, wenn die Datei mindestens 20 s lang ist. Darunter ist
die Perzentil-Verteilung nicht sinnvoll; `scripts/release-check.sh` überspringt
sie dann ausdrücklich. Ein Master ist erst release-fähig, wenn Loudness, True
Peak und PLR passen — und die LRA, sofern sie messbar ist.

### Der Code

Die Prüfung ist ein Befehl, der einen Exit-Code zurückgibt:

```bash
python3 tools/measure.py master.wav
scripts/release-check.sh master.wav
```

`measure.py` liefert die Zahlen, `release-check.sh` vergleicht sie mit dem
Korridor. Ein Exit-Code von 1 ist kein Absturz, sondern das Ergebnis „nicht
release-fähig“.

### Die Messung

Der erste Beweis war der synthetische Loop aus A4, gerendert mit dem Programm
„CD Loud“:

| Größe | vorher | nachher |
|---|---|---|
| Integrated | −11,0 LUFS | **−8,5 LUFS** |
| True Peak | +0,90 dBTP | **−1,10 dBTP** |
| PLR | 11,9 | **7,4** |
| Clipping | 0 | 0 |

Der Loop trifft Loudness, True Peak und PLR. Das beweist, dass die Kette diese
drei Pegelziele erreichen kann. Es beweist nicht, dass sie es auf einem Song
tut.

Der erste echte Rohmix aus A5 zeigt den Unterschied: **−18,3 LUFS, −0,6 dBTP,
PLR 17,7**. Die alte Vierer-Kette lag bei **−8,0 LUFS, PLR 8,2**. Zwischen
Rohmix und dieser alten Kette liegen 10,3 dB Lautheit und 9,5 dB PLR. Der
QMaster-Zielpunkt in Kapitel 2 liegt bei −8,1 LUFS; dorthin sind es 10,2 dB.

### Fehler & Test

Der Fehler wäre, den Loop als Beweis zu nehmen. Er ist ein Testsignal mit
bekanntem Verhalten, kein Material mit Arrangement. A5 zeigt, wie weit ein
echter Rohmix entfernt liegt: 10,2 dB Lautheit und ein PLR von 17,7 statt 6 bis
8.

Der Test, der das heute verhindert: `release-check.sh` läuft auf dem **echten
Export**, nicht auf dem Loop. Und weil eine einzelne Zahl keine Ursache
beweist, wird der PLR immer mitgelesen. Ein Master, der nur laut ist, hat den
Test nicht bestanden.

### Anwendung

Vor dem Mastern werden drei Zahlen des Rohmix gemessen: Integrated, True Peak
und PLR. Die Differenz zwischen Roh-PLR und Ziel-PLR ist die Spitzenkontrolle,
die die Kette leisten muss. Ist sie groß, ist der Weg zu −8 weit — dann wird
zuerst der Mix dichter, nicht der Limiter härter.

## 2. Die Rechnung: Zielkorridor und Gain

### Die Frage

Wie wird aus einem Rohmix bei −18,3 LUFS ein Master bei −8,1 LUFS? Und warum
reicht es nicht, einfach lauter zu drehen?

### Die Mathematik

Der gemessene Rohmix hat **−18,3 LUFS**, **−0,6 dBTP** und **PLR 17,7**. Der
Zielpunkt der Empfehlung ist **−8,1 LUFS** bei **−1,40 dBTP** und **PLR 6,7**.

Die Lautheitsdifferenz ist:

```
−8,1 − (−18,3) = +10,2 dB
```

Eine reine Verstärkung um 10,2 dB würde auch den True Peak um 10,2 dB anheben:

```
−0,6 + 10,2 = +9,6 dBTP
```

Gemessen wurden aber **−1,40 dBTP**. Die Kette hat also nicht nur verstärkt,
sondern zusätzlich Spitzen entfernt:

```
9,6 − (−1,4) = 11,0 dB Spitzenkontrolle
PLR: 17,7 − 11,0 = 6,7 dB
```

Der PLR ist der **Crest des Masters**: der Abstand zwischen True Peak und
integrierter Lautheit. Er beschreibt die Spitzenreserve des fertigen Masters,
nicht die Lautheitsvarianz über die Zeit — dafür steht die LRA.

Damit ist der Unterschied zwischen Normalisierung und Limiting exakt:

| Operation | Integrated | True Peak | PLR |
|---|---|---|---|
| Normalisieren: `g · x` | +g | +g | **unverändert** |
| Limitieren: `g · x`, Spitzen gedeckelt | +g | gedeckelt | **fällt** |

Normalisierung verschiebt Loudness und Peak gemeinsam. Nur die Begrenzung der
Spitzen senkt den PLR. Deshalb ist der PLR der Beweis dafür, dass eine
Dynamikbearbeitung im Spiel war — und nicht nur ein Gain.

Die 11,0 dB sind die eigentliche Aussage: So viel Spitzenkontrolle verlangt
dieser Mix. Ein dichterer Mix verlangt weniger, und genau deshalb muss die
Lautheit aus dem Mix kommen. Der Limiter kann die Differenz schließen, aber
nicht ohne Eingriff in die Wellenform.

Die Trim-Zahl ist dabei nicht die Loudness-Differenz: **+8 dB Trim** ergaben
gemessen **+10,2 LU**. Der Clipper verändert die Wellenform, nicht nur den
Pegel.

### Der Code

`build/render` nimmt normalisierte Werte von 0 bis 1, nicht die Anzeigewerte.
Die Umrechnung steht in `docs/WERKZEUGE.md`:

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

Ein Aufruf für die Empfehlung sieht so aus:

```bash
build/render build/native/qmaster.so raw.wav master.wav \
  --set Mode=0 --set Trim=0.8333 --set Clip=0.55 \
  --set Ceiling=0.5 --set Release=0.45 --set Mono=0.6
```

### Die Messung

Der Sweep aus A6 bestätigt die Rechnung an genau diesen Punkten:

| Trim | Clip | Integrated | True Peak | PLR |
|---|---|---|---|---|
| **+8** | **55** | **−8,1 LUFS** | **−1,40 dBTP** | **6,7** |
| +10 | 55 | −6,9 LUFS | — | 5,5 |
| +12 | 45 | −6,5 LUFS | — | 5,2 |

Der Feinsweep trennt Lautheit und Dichte:

| Trim | Clip | Integrated | PLR |
|---|---|---|---|
| +8,0 | 56 | −8,1 LUFS | 6,7 |
| +7,5 | 56 | −8,4 LUFS | 7,0 |
| +8,0 | 52 | −8,4 LUFS | 7,0 |
| +7,0 | 56 | −8,7 LUFS | 7,3 |
| +6,5 | 56 | −9,0 LUFS | 7,6 |

### Fehler & Test

Der klassische Fehlschluss: „Der Export peakte bei −0,09 dBFS, also hat die MPC
normalisiert.“ Das ist falsch. Eine Normalisierung würde den PLR nicht
verändern. Die alten Exporte hatten aber **PLR 7,7** gegen **17,7** beim
Rohmix, und in der Analyse lagen **309 bzw. 261 Samples** bei 0,99. Das ist eine
Limiter-Decke, kein einzelner normalisierter Spitzenwert. Der Peak kam vom
Maximizer der alten Vierer-Kette.

Der Test dagegen ist eine zweite, unabhängige Metrik: PLR plus
Sample-Verteilung. Eine einzelne Peak-Zahl beweist keine Ursache.

Der zweite Fehler betrifft den Deckel. Der Guard von QMaster ist **0,40 dB**
groß. Auf „Under One Sun“ reichte er für **−1,40 dBTP**; auf „Seele“ lag der
neue Master bei **−0,40 dBTP** — **0,6 dB über** dem Ziel −1,0. Der Guard ist
also nicht materialunabhängig. Deshalb wird der True Peak nach jedem Song
gemessen, nicht nur einmal am Plugin.

### Anwendung

Der Trim wird aus der gemessenen Loudness gesetzt, nicht nach Gefühl. Wer bei
−8,1 LUFS noch mehr Loudness will, landet bei −6,9 LUFS und PLR 5,5 — außerhalb
des Korridors. Wer mehr Dynamik will, geht auf **Trim +7,5, Clip 56** und
misst **−8,4 LUFS bei PLR 7,0**. Die Zahl am Regler ist eine Stellschraube, das
Ergebnis steht im Report.

## 3. Der Werkzeugkasten: rendern, messen, prüfen

### Die Frage

Wie wird ein Master reproduzierbar gerendert, gemessen und gegen den Korridor
geprüft — ohne MPC-UI und ohne Gehör?

### Die Mathematik

Der Renderer kompensiert die gemeldete Latenz von **102 Samples**. Bei 44,1 kHz
sind das

```
102 / 44100 · 1000 = 2,31 ms
```

Die Ausgabe ist ein 24-Bit-WAV, stereo. Mono-Dateien werden abgelehnt, weil der
Stereo-Pfad gemessen werden soll. `measure.py` liefert Integrated, True Peak,
PLR, LRA, DC, Clipping, 16 Bänder und den Mono-Check unter 120 Hz. Die LRA wird
bei Dateien unter 20 s übersprungen.

### Der Code

```bash
./scripts/build-mpc.sh

build/render build/native/qmaster.so in.wav out.wav --program 1

python3 tools/measure.py out.wav
python3 tools/measure.py out.wav --json
python3 tools/measure.py out.wav --bands 8

scripts/release-check.sh out.wav
TARGET_LUFS=-9 CEILING_DBTP=-1.0 scripts/release-check.sh out.wav
scripts/codec-check.sh out.wav

./scripts/check.sh
```

Die Programm-Indizes sind: 0 Init, 1 CD Loud, 2 Streaming Safe, 3 Bus Drums,
4 Bus 808. `release-check.sh` prüft Loudness (±1 LU), True Peak (≤ Deckel), PLR
(6–8), LRA (4–7, nur ab 20 s), DC (< 0,001), Clipping (0 Samples ≥ 0,999) und
den Mono-Check. `codec-check.sh` schickt die Datei durch Ogg Vorbis q9 und
vergleicht Loudness, True Peak und Bandbalance.

### Die Messung

Der End-to-End-Lauf aus A4 rendert den Loop durch Programm 1 und misst danach
**−8,5 LUFS, −1,10 dBTP, PLR 7,4**. Der Codec-Check auf demselben Loop zeigt,
wie empfindlich der Durchlauf ist:

| Größe | Abweichung nach Ogg q9 |
|---|---|
| Loudness | +0,10 LU |
| True Peak | +0,10 dB |
| größte Bandabweichung | 0,11 dB |

Das sind keine Mastering-Zahlen, sondern die Empfindlichkeit des Prüfwerkzeugs.
Für den echten Export A9 steht das Ergebnis weiter unten: Codec-Check
bestanden.

### Fehler & Test

Der Renderer hatte einen 24-Bit-Fehler: Das erste Byte wurde mit `s >> 8` statt
mit `s & 0xff` geschrieben. Das Ergebnis war **48 dB zu leise** und sah wie
Stille aus. Gefunden wurde es durch den Vergleich mit dem erwarteten Peak, nicht
durch Hören.

Der Test heute: Nach jedem Render wird der erwartete Peak geprüft, bevor
irgendeine Loudness-Zahl interpretiert wird. Ein 24-Bit-Wort hat drei Bytes; ein
verschobenes Byte kostet 8 Bit, also 48 dB.

### Anwendung

Die Reihenfolge ist fix: bauen, rendern, messen, `release-check`, `codec-check`.
Im Report wird zuerst Integrated gegen −8 ± 1 LUFS gelesen, dann True Peak gegen
−1,0 dBTP, dann PLR gegen 6–8. Die LRA folgt nur ab 20 s; Clipping 0 und der
Mono-Check sind Gates, keine Klangurteile. Erst wenn diese Zahlen stehen, wird
über Klang gesprochen. Ein Exit-Code 1 aus `release-check.sh` wird gelesen,
nicht ignoriert.

## 4. Der Sweep: 25 Läufe, 8 Treffer

### Die Frage

Wo genau liegt auf diesem Rohmix die Einstellung, die den Korridor trifft — und
welche Kompromisse stehen daneben?

### Die Mathematik

A6 fährt 25 Kombinationen: Trim +4 bis +12 gegen Clip 30 bis 75, bei Ceiling
−1, Release 45, Mono 120. **8 der 25 Läufe** liegen im Korridor, also **32 %**.
Der Korridor ist nur 2 LU breit und 2 dB PLR hoch; daneben fällt ein Lauf
schnell heraus.

Der Sweep zeigt den Trade-off:

- **+8 / 55:** −8,1 LUFS, PLR 6,7 — die Empfehlung.
- **+7,5 / 56:** −8,4 LUFS, PLR 7,0 — 0,3 dB leiser, 0,3 dB mehr PLR.
- **+10 / 55:** −6,9 LUFS, PLR 5,5 — 1,2 dB lauter, 1,2 dB dichter, außerhalb.
- **+12 / 45:** −6,5 LUFS, PLR 5,2 — noch heißer.

Mehr Clip bedeutet nicht automatisch mehr Loudness im Korridor. Ab einem Punkt
steigt die Loudness, aber der PLR fällt unter 6. Dann ist der Master laut, aber
außerhalb des Korridors.

### Der Code

Der Sweep ist eine Schleife um denselben Renderer-Aufruf. Ein Punkt daraus:

```bash
build/render build/native/qmaster.so raw.wav out.wav \
  --set Mode=0 --set Trim=0.8333 --set Clip=0.55 \
  --set Ceiling=0.5 --set Release=0.45 --set Mono=0.6

python3 tools/measure.py out.wav --json
```

`--json` liefert die Werte maschinenlesbar; `release-check.sh` macht daraus
Pass/Fail. Der Sweep selbst ist im Repo nicht als eigenes Skript abgelegt — die
Wahrheit ist die Tabelle in `docs/ANALYSEN.md`, nicht ein neues Tool.

### Die Messung

Die acht Treffer aus A6:

| Trim | Clip | Integrated | True Peak | PLR |
|---|---|---|---|---|
| **+8** | **55** | **−8,1 LUFS** | **−1,40 dBTP** | **6,70** |
| +6 | 65 | −8,6 LUFS | −1,40 dBTP | 7,20 |
| +10 | 30 | −8,8 LUFS | −1,40 dBTP | 7,40 |
| +8 | 45 | −8,9 LUFS | −1,40 dBTP | 7,50 |
| +10 | 45 | −7,6 LUFS | −1,40 dBTP | 6,20 |
| +12 | 30 | −7,5 LUFS | −1,40 dBTP | 6,10 |
| +6 | 75 | −7,9 LUFS | −1,40 dBTP | 6,50 |
| +8 | 65 | −7,4 LUFS | −1,40 dBTP | 6,00 |

### Fehler & Test

Acht Treffer sind nicht acht gleich gute Master. **+8 / 65** liegt mit
**−7,4 LUFS** und **PLR 6,00** im Korridor, aber genau an der unteren Kante.
Wer nur die Loudness liest, nimmt den lauteren Lauf; wer den PLR liest, sieht,
dass er der dichteste ist.

Der Test: Ein Lauf wird erst ausgewählt, wenn Integrated **und** PLR passen.
Danach folgt ein A/B bei gleicher Loudness. Ohne Pegelangleich gewinnt immer
der lautere Master, unabhängig von der Dynamik.

### Anwendung

Der Startpunkt auf diesem Rohmix ist **Trim +8, Clip 55, Ceiling −1, Release
45, Mono 120**. Für mehr Dynamik: **Trim +7,5, Clip 56**. Beide Werte sind
gemessen. Bei einem anderen Mix wird neu gesweept; die Zahlen sind Startpunkte,
keine Garantie.

## 5. Der echte Export: A9 und Seele

### Die Frage

Hält der Korridor auf einer echten Produktion — und was passiert auf einem
zweiten Song, der dynamischer ist?

### Die Mathematik

A9 verteilt die Arbeit auf zwei Instanzen: **Bus Drums** auf dem Drum-Bus und
**CD Loud** auf dem Master. Gegenüber dem einzelnen CD-Loud-Master ist das
Ergebnis

- **0,3 dB lauter**: −7,8 gegen −8,1 LUFS,
- **0,2 dB dichter**: PLR 6,5 gegen 6,7.

Der Bus-Clip verschiebt die Lautheit also kaum; der Master macht die
Hauptarbeit.

A10 vergleicht dieselbe neue Kette mit der alten Vierer-Kette auf „Seele“:

- **1,6 dB lauter**: −10,9 gegen −12,5 LUFS,
- **3,4 dB dichter**: PLR 10,5 gegen 13,9,
- **1,8 dB weniger True Peak**: −0,4 gegen +1,4 dBTP,
- **1,5 LU mehr LRA**: 7,6 gegen 6,1.

Der Korridor wird trotzdem verfehlt: Die Loudness liegt **1,9 dB unter** der
unteren Grenze −9, der True Peak **0,6 dB über** −1,0, der PLR **2,5 dB über**
8. Die Mitten liegen relativ zum Sub **3 bis 5,6 dB tiefer** (204 Hz bis
13 kHz).

### Der Code

Auf dem Gerät sind zwei Instanzen im Spiel:

- Programm 3, **Bus Drums**, auf dem Drum-Bus,
- Programm 1, **CD Loud**, auf dem Master.

Der Offline-Renderer verarbeitet eine Instanz pro Lauf. Die verteilte Kette aus
A9 ist deshalb ein Geräte-Export; die Sweeps aus A6 sind Einzelinstanzen auf dem
Master. Gemessen wird in beiden Fällen mit demselben Werkzeug:

```bash
python3 tools/measure.py export.wav
scripts/release-check.sh export.wav
scripts/codec-check.sh export.wav
```

### Die Messung

A9, „Under One Sun“ mit Bus Drums plus CD Loud:

| Größe | Ergebnis |
|---|---|
| Integrated | **−7,8 LUFS** |
| True Peak | **−1,30 dBTP** |
| PLR | **6,5** |
| LRA | **1,3 LU** |
| Mono Side−Mid | **−32,0 dB** |
| Clipping | **0** |
| Codec-Check | **bestanden** |

Die LRA von 1,3 liegt unter dem Ziel 4–7, wird aber wegen der Länge von 19,46 s
übersprungen. Der Ausschnitt ist repetitiv; die alten Referenzen lagen
ebenfalls bei 1,2 bis 1,4.

A10, „Seele“ (106,67 s), alte Kette gegen neue Kette:

| Größe | alte Kette | neue Kette |
|---|---|---|
| Integrated | −12,5 LUFS | **−10,9 LUFS** |
| True Peak | **+1,40 dBTP** | −0,40 dBTP |
| PLR | 13,9 | 10,5 |
| LRA | 6,1 LU | 7,6 LU |
| Mono Side−Mid | −29,8 dB | −37,4 dB |

### Fehler & Test

Die Geschichte von „Seele“ ist die wichtigste des Capstones: **Ein Master kann
nicht mischen.** Der Versuch, auf einem nicht arrangierten Track −8 LUFS zu
erzwingen, endet bei −10,9 LUFS und PLR 10,5 — und die Mitten liegen 3 bis
5,6 dB tiefer als der Sub. Die Analyse vermutet das starke Master-Clipping als
Ursache: Sub-Sinuswellen passieren, Mittenspitzen werden abgeschnitten.

Weil kein Roh-Export von „Seele“ ohne Master-Kette vorliegt, ist die Ursache
nicht bis auf ein einzelnes Plugin isoliert. Die Messung zeigt aber die
Richtung: mehr Bass relativ zu den Mitten, Korridor verfehlt. Der Test, der das
heute verhindert, ist ein **Roh-Export vor dem Master**, eine Bandmessung mit
`measure.py --bands 8` und ein A/B bei gleicher Loudness.

### Anwendung

Erst der Bus, dann der Master. Wenn ein Song nach der Bus-Stufe noch weit vom
Korridor entfernt ist, wird nicht der Master weiter aufgedreht, sondern der Mix
geändert. Für „Seele“ ist als nächster Schritt ein Roh-Export ohne Master-Kette
dokumentiert; die Empfehlung lautet Ceiling −1,6 dBTP, Clip 45, Trim +6 und
Tilt +1,0 bis +1,5. Diese Einstellung ist noch nicht als Messung bestätigt.

## 6. Die Fehlschlüsse: vier Plugins, Guard, Mitten

### Die Frage

Welche vier Fehler haben das erste „es funktioniert“ falsch gemacht — und
welcher Test verhindert sie heute?

### Die Mathematik

**Fehler 1: Plugin-Zahl als Qualität.** Die alte Kette bestand aus vier
Plugins — Kompressor, Clipper, Maximizer und einem weiteren (Nutzerangabe) — und
erreichte **−8,0 LUFS bei PLR 8,2**. QMaster erreicht **−8,1 LUFS bei PLR 6,7**. Bei
fast gleicher Loudness ist QMaster damit **1,5 dB dichter**. Gegen den alten
NoFx-Export mit PLR 7,7 sind es **1,0 dB**. Der Report fasst das als „rund 1 dB
dichter“ zusammen. Der Kompressor der alten Kette hatte die Gain Reduction
gleichmäßiger verteilt als Clipper plus Limiter.

**Fehler 2: −0,09 dBFS als Normalisierung.** Eine Normierung lässt den PLR
unverändert. Die alten Exporte hatten **PLR 7,7** gegen **17,7** beim Rohmix,
und **309 bzw. 261 Samples** lagen bei 0,99. Das ist der Maximizer, nicht der
Export.

**Fehler 3: Guard als materialunabhängig.** Der Guard ist **0,40 dB**. Auf
„Under One Sun“ lag der True Peak bei **−1,40 dBTP**, auf „Seele“ bei
**−0,40 dBTP**. Ziel ist −1,0; das sind **0,6 dB zu viel**. Die alte Kette lag
sogar bei **+1,40 dBTP**. Derselbe Korridor, anderes Material, anderer Abstand.

**Fehler 4: Master statt Mix.** „Seele“ ist 1,6 dB lauter und 3,4 dB dichter
geworden, verfehlt aber alle drei Hauptkriterien. Die Mitten sind 3 bis 5,6 dB
leiser. Ein Master kann Pegel und Spitzen kontrollieren, aber keine
Arrangement-Entscheidung nachholen.

### Der Code

Die Tests, die zu diesen Fehlern gehören:

```bash
python3 tests/plugin-check.py          # Latenz, True Peak, Ceiling
python3 tools/measure.py master.wav --bands 8
scripts/release-check.sh master.wav    # pro Song, nicht pro Plugin
```

`plugin-check.py` prüft das Plugin an Testsignalen. `release-check.sh` prüft den
Song. Das eine ersetzt das andere nicht.

### Die Messung

Die Zahlen, die die vier Fehlschlüsse belegen:

| Fall | Integrated | True Peak | PLR |
|---|---|---|---|
| alter NoFx-Export | −7,6 LUFS | +0,1 dBTP | 7,7 |
| alter Fx-Export (Vierer-Kette) | −8,0 LUFS | +0,2 dBTP | 8,2 |
| QMaster CD Loud (+8/55) | −8,1 LUFS | −1,40 dBTP | 6,7 |
| QMaster auf „Seele“ | −10,9 LUFS | −0,4 dBTP | 10,5 |

Dazu die Sample-Verteilung der alten Exporte: 309 bzw. 261 Samples bei 0,99.
Das ist keine einzelne Spitze, sondern eine Decke.

### Fehler & Test

1. **Vier Plugins, weniger Dynamik.** Die alte Kette war bei −8,0 LUFS mit PLR
   8,2. QMaster ist bei −8,1 LUFS mit PLR 6,7 rund 1 bis 1,5 dB dichter. Test:
   PLR bei gleicher Loudness vergleichen, nicht die Plugin-Liste.
2. **−0,09 dBFS war der Maximizer.** Test: PLR plus Sample-Verteilung; eine
   einzelne Peak-Zahl reicht nicht.
3. **Der Guard ist nicht materialunabhängig.** Alt +1,4, neu −0,4, Ziel −1,0.
   Test: True Peak nach jedem Song; der 0,40-dB-Guard ist kein Freibrief.
4. **Der Master kann nicht mischen.** „Seele“ verfehlt den Korridor trotz
   besserem True Peak; die Mitten sind 3 bis 5,6 dB leiser. Test: Roh-Export,
   Bandmessung, A/B bei gleicher Loudness.

### Anwendung

Keine dieser Zahlen erlaubt „set and forget“. Der Testvertrag vor einer
Veröffentlichung ist: Rohmix messen, Bus und Master getrennt prüfen, den Export
mit `release-check.sh` abnehmen, den Codec prüfen und erst dann hören. Ein
Preset ist ein Startpunkt, keine Garantie.

## 7. Die Übergabe: Checkliste und Programme

### Die Frage

Welche Schritte führt man in welcher Reihenfolge aus — und welches Programm
wählt man wann?

### Die Mathematik

Die Programme mit ihren gemessenen Werten:

| Programm | Werte | Gemessen |
|---|---|---|
| Init | Clip 0, Ceiling −1, Mono 120 | neutral |
| CD Loud | Trim +8, Clip 55, Ceiling −1, Release 45, Mono 120 | **−8,1 LUFS, −1,40 dBTP, PLR 6,7** |
| CD Dynamic | Trim +7,5, Clip 56, sonst wie CD Loud | **−8,4 LUFS, PLR 7,0** |
| Streaming Safe | Trim +5, Clip 45, Ceiling −1,5, Release 60 | nicht gemessen |
| Bus Drums | Mode Bus, Clip 45, Transient 45 | in A9 als Bus-Stufe: Gesamt **−7,8 LUFS, PLR 6,5**; solo nicht gemessen |
| Bus 808 | Mode Bus, Clip 55, Transient 20 | nicht gemessen |

Wann welches Programm:

- **CD Loud** ist der Standard für einen Mix, der bereits dicht ist und den
  Korridor bei −8,1 LUFS / PLR 6,7 trifft.
- **CD Dynamic** nimmt 0,3 dB Loudness zurück und gibt 0,3 dB PLR: −8,4 LUFS
  bei PLR 7,0. Sinnvoll, wenn der Master atmen soll, aber im Korridor bleiben
  muss.
- **Streaming Safe** hat mit −1,5 dBTP und Release 60 mehr Reserve, ist aber
  nicht gemessen. Die Zahlen müssen am eigenen Song entstehen.
- **Bus Drums** gehört auf den Drum-Bus, wenn Transienten vor dem Master
  kontrolliert werden sollen. A9 misst die Kombination mit CD Loud; solo ist
  das Programm nicht vermessen.
- **Bus 808** ist für sustainierte 808 gedacht (Clip 55, Transient 20), aber
  nicht gemessen. Ohne Messung ist es eine Hypothese, kein Preset.
- **Init** ist der neutrale Referenzpunkt: Clip 0, Ceiling −1, Mono 120.

### Der Code

Die vollständige Kette als Befehlsfolge:

```bash
./scripts/build-mpc.sh

# 1. Rohmix exportieren, unnormalisiert
# 2. Rohmix messen
python3 tools/measure.py raw.wav

# 3. Bus und Master rendern
build/render build/native/qmaster.so raw.wav master.wav --program 1

# 4. Abnehmen
scripts/release-check.sh master.wav
scripts/codec-check.sh master.wav

# 5. Alles zusammen
./scripts/check.sh
```

Für ein A/B bei gleicher Loudness werden beide Dateien mit `measure.py`
gemessen und auf denselben Integrated-Wert gebracht, bevor gehört wird. Ohne
Pegelangleich gewinnt der lautere Master.

### Die Messung

Die gemessenen Fälle im Überblick:

| Fall | Integrated | True Peak | PLR |
|---|---|---|---|
| Loop A4 | −8,5 LUFS | −1,10 dBTP | 7,4 |
| A6 +8/55 | −8,1 LUFS | −1,40 dBTP | 6,7 |
| A6 +7,5/56 | −8,4 LUFS | — | 7,0 |
| A9 Bus + CD Loud | −7,8 LUFS | −1,30 dBTP | 6,5 |
| „Seele“ neu | −10,9 LUFS | −0,4 dBTP | 10,5 |
| „Seele“ alt | −12,5 LUFS | +1,4 dBTP | 13,9 |

A9 besteht den Codec-Check. Die LRA von A9 ist 1,3 LU, wird aber wegen 19,46 s
übersprungen. Bei „Seele“ sind es 7,6 LU gegen 6,1 LU alt; 7,6 liegt über dem
Ziel 4–7.

### Fehler & Test

Zwei Gerätetests sind noch offen, und sie stehen ausdrücklich im Report:

- **CPU auf dem Gerät:** Auf dem Desktop wurden **0,32 %** für 1× Master und
  5× Bus gemessen. Ein 10-Minuten-Loop auf der MPC fehlt. Der Test sucht Xruns
  und Drift, nicht nur einen kurzen Peak.
- **State-Roundtrip:** Preset speichern, MPC neu starten, laden und Parameter
  sowie Audio vergleichen. Der Test beweist, dass das Preset den Neustart
  überlebt.

Dazu kommt die Hörmethode: **A/B bei gleicher Loudness.** Beide Master werden
auf denselben Integrated-Wert gebracht, dann wird gehört. Ohne Pegelangleich
gewinnt der lautere Master.

Solange die zwei Gerätetests offen sind, ist ein Export wie A9 nach Korridor
release-fähig; das Plugin auf dem Gerät ist es noch nicht.

### Anwendung

Die Checkliste für einen Track:

1. **Mix zuerst.** Arrangement, Buspegel und Balance, dann ein Roh-Export ohne
   Master-Kette.
2. **Rohmix messen.** Integrated, True Peak und PLR notieren. Der PLR sagt, wie
   viel Spitzenkontrolle nötig ist.
3. **Bus clip.** Bus Drums auf den Drum-Bus, wenn Transienten kontrolliert
   werden sollen.
4. **Master CD Loud.** Trim +8, Clip 55, Ceiling −1, Release 45, Mono 120.
5. **Unnormalisiert exportieren.** Die MPC normalisiert nicht; der Export bleibt
   der Pegel, den die Kette eingestellt hat.
6. **`release-check.sh`.** Loudness, True Peak, PLR und — ab 20 s — LRA prüfen.
7. **`codec-check.sh`.** Ogg-Vorbis-q9-Durchlauf; A9 besteht ihn.
8. **A/B bei gleicher Loudness.** Erst pegeln, dann hören.
9. **Gerätetests.** CPU, 10-Minuten-Soak und State-Roundtrip nachholen.

Wer diese neun Schritte geht, hat keinen „so klingt highend“-Satz, sondern
einen Report mit Zahlen. Das ist der Unterschied zwischen einem Master und
einem lauten Export.
