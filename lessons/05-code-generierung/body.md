Diese Lektion ist die Meta-Lektion der Reihe. Sie erklärt nicht einen weiteren
DSP-Block, sondern den Vertrag, mit dem QMaster gebaut wurde: Spezifikation →
Test → Code → Messung → Review. Die Zahlen stammen aus `scripts/check.sh`,
`tests/selftest.py`, `tests/plugin-check.py`, `tests/alias-check.py`,
`tests/loudness-check.py`, `tools/validate.py` und den Messungen in
`REPORT.md`.

Wer einen Agenten Code schreiben lässt, hat zwei Möglichkeiten: jede Zeile
lesen und trotzdem hoffen, oder prüfen, was das Programm mit bekannten Signalen
macht. Diese Lektion beschreibt die zweite Möglichkeit.

## 1. Die Frage: Wie vertraut man Code, den man nicht Zeile für Zeile geschrieben hat?

Die ehrliche Antwort: gar nicht — jedenfalls nicht dem Code. Man vertraut dem
Verfahren, das ihn geprüft hat. Ein Agent kann eine Biquad-Kaskade schreiben.
Er kann aber nicht ohne Test beweisen, dass diese Kaskade bei 0 dB exakt
durchlässt, keine Allokation im Audiopfad macht und den Impuls an Sample 102
liefert.

Drei Sätze tragen die ganze Lektion:

1. **Ein Test, der nicht rot werden kann, ist kein Test.** Er ist Dekoration.
2. **Eine Zahl ohne Einheit und Bezug ist keine Messung.** `−0,09` ist kein
   Ergebnis; `−0,09 dBFS Sample-Peak` ist eines.
3. **Eine Änderung ohne Basislinie ist keine Änderung.** Ohne Vorher-Messung
   bleibt nur die Erinnerung an einen Klang.

QMaster hat für diese drei Sätze konkrete Gates: 13 Prüfungen der Messkette,
10 Plugin-Prüfungen, einen Alias-Check, 5 Loudness-Prüfungen, eine
JSON-/Lektionen-Prüfung und einen Publish-Guard. Der Host-Simulator meldet
20/20. Das ist keine Garantie für guten Klang, aber es ist eine belastbare
Aussage darüber, was der Code tut.

Die Gegenprobe kommt aus dem Vorgängerprojekt QDSSD. Dort meldet der
Host-Simulator 19/19 für den einen und 20/20 für den anderen Build. Zwei Zahlen
für zwei Plugins mit unterschiedlichen Zuständen und Programmen; entscheidend
ist, dass beide ohne Fehlschlag enden.

## 2. Die Mathematik: Toleranz, dBc, PLR, Sample-Zählung

### 2.1 Toleranz: jede Prüfung ist eine Entscheidung

Eine Messung ist nie ein Punkt, sondern ein Intervall:

```
x_soll − t  ≤  x_ist  ≤  x_soll + t
```

`t` ist die Toleranz. Sie muss größer sein als das Rauschen der Messkette und
kleiner als der kleinste Fehler, den man finden will. Im Repo stehen
verschiedene Toleranzen, weil verschiedene Dinge gemessen werden:

| Größe | Soll | Toleranz | Warum |
|---|---|---|---|
| Sinus-Peak, Sinus-RMS | −6,02 / −9,03 dBFS | ±0,05 dB | analytisch exakt, nur Rundung |
| Pink-Noise-RMS | −20,0 dBFS | ±0,3 dB | Rauschvarianz |
| Dirac-Peak | −0,92 dBFS | ±0,05 dB | deterministisch |
| Latenz | 102 Samples | ±1 Sample | Impulsindex, ein Sample Auflösung |
| Integrated Loudness | −8 LUFS | ±1 LU | Material und Gate |
| Alias | ≤ −60 dBc | einseitig | alles darüber gilt als Fehler |
| Golden File | Referenz | ≤ −120 dBFS Differenz | unter der 16-Bit-Grenze |

Die letzte Zeile ist die wichtigste: −120 dBFS liegt 24 dB unter dem
16-Bit-LSB von −96 dBFS. Ein Unterschied in dieser Größe ist im fertigen
16-Bit-Export nicht darstellbar. Die Toleranz ist also nicht „so ungefähr“,
sondern eine Aussage über die Auflösung, die man tatsächlich ausliefert.

### 2.2 dBFS, dBTP, dBc: der Bezug entscheidet

Drei Pegel, drei Bezugspunkte:

```
dBFS  = 20·log10(A / 1,0)        bezogen auf Vollaussteuerung
dBTP  = 20·log10(A_tp / 1,0)     True Peak, zwischen den Samples geschätzt
dBc   = 20·log10(A_stör / A_grundton)   bezogen auf den Grundton
```

Der Alias-Check liefert beide Zahlen. Der Grundton liegt bei **−1,2 dBFS**, der
stärkste Nicht-Harmonische bei **−106,6 dBFS** und **19175 Hz**. Daraus folgt:

```
−106,6 − (−1,2) = −105,4 dBc
```

Der Frequenzwert ist kein Zufall: Die 25. Harmonische von 997 Hz liegt bei
`25 · 997 = 24925 Hz`, oberhalb von Nyquist (22050 Hz). Sie faltet sich auf
`44100 − 24925 = 19175 Hz` zurück. Genau dort misst die FFT den stärksten
Alias.

Der Unterschied zwischen dBFS und dBc ist der Unterschied zwischen „wie laut
ist der Störer absolut“ und „wie weit liegt er unter dem Nutzsignal“. Eine
reine Pegeländerung verschiebt beide Werte um denselben Betrag. Deshalb ist
dBc die richtige Einheit für einen Alias-Test und dBTP die richtige für einen
Ceiling-Test.

### 2.3 Warum PLR unter reiner Verstärkung invariant ist

Der Peak-to-Loudness-Ratio ist definiert als

```
PLR = True Peak − Integrated Loudness
```

Verstärkt man das Signal um den Faktor `g`, dann gilt für beide Größen
derselbe Faktor:

```
TP(g·x)  = TP(x)  + 20·log10(g)
L(g·x)   = L(x)   + 20·log10(g)
PLR(g·x) = TP(g·x) − L(g·x) = PLR(x)
```

Der PLR kann sich unter einer reinen Pegelanhebung **nicht** ändern. Genau
damit lässt sich der berühmte −0,09-dBFS-Fall entscheiden. Der Rohmix misst
**−0,6 dBTP** und **−18,3 LUFS**, also

```
PLR_roh = −0,6 − (−18,3) = 17,7 dB
```

Die alte Referenz `NoFx` misst **+0,1 dBTP** und **−7,6 LUFS**, also

```
PLR_alt = +0,1 − (−7,6) = 7,7 dB
```

Der Peak-Unterschied erklärt nur `0,1 − (−0,6) = 0,7 dB` der Lautheitsdifferenz
von `−7,6 − (−18,3) = 10,7 dB`. Die restlichen **10,0 dB** können keine
Verstärkung sein. Und genau 10,0 dB ist auch der Abfall des PLR:
`17,7 − 7,7 = 10,0 dB`. Das ist Dynamikbearbeitung, kein Export-Normalisieren.

### 2.4 Die Decke zählen: Limiter oder Normalisierung?

Eine Normalisierung skaliert alle Samples mit einem Faktor, bis der **eine**
höchste Sample bei Vollaussteuerung liegt. Danach liegt genau ein Sample bei
0,99; alle anderen liegen darunter. Ein Limiter dagegen hält viele Samples an
der Decke. In den alten Exporten liegen **309** (NoFx) und **261** (Fx) Samples
bei 0,99.

Bei 44,1 kHz sind das

```
309 / 44100 = 7,0 ms
261 / 44100 = 5,9 ms
```

Ein einzelner normalisierter Spitzenwert kann keine 5–7 ms lange Decke
erzeugen. Die zweite, unabhängige Metrik widerlegt die Normalisierungs-These,
ohne dass man den Export-Dialog kennen muss.

### 2.5 Impuls, Latenz und Group Delay

Die Latenz wird mit einem Dirac gemessen, der bei 0,05 s im Eingang liegt. Der
Peak im Ausgang muss bei

```
0,05 · 44100 + 102 = 2205 + 102 = 2307
```

liegen. Der Test rechnet `peak_index − 2205` und erwartet **102 Samples**.
Das sind

```
102 / 44100 = 2,313 ms
```

Gemeldet und gemessen werden beide 102 — im Master- und im Bus-Modus. Der
Renderer kompensiert dieselben 102 Samples, sonst wäre jede End-to-End-Messung
um 2,3 ms verschoben.

Group Delay ist die Verzögerung, die eine Frequenz durch das System erfährt.
Bei einer festen, linearen Kette ist sie konstant; ein Impuls bleibt ein
Impuls. Ändert ein Filter die Group Delay, wandert der Impuls, und der Test
wird rot. Deshalb ist der Impuls-Test kein Latenz-Test allein, sondern ein
Test auf **Zeitkohärenz** der ganzen Kette.

### 2.6 Golden Files: die Nulllinie aus der Vergangenheit

Ein Golden File ist eine kurze, gespeicherte Impulsantwort oder ein
Referenzblock. Jede neue Version muss ihn innerhalb von **−120 dBFS**
reproduzieren. Das fängt Änderungen, die kein Zielkriterium verletzen: ein
verschobener OLA-Ring, ein anderer Filterkoeffizient, ein zusätzlicher
Gain-Schritt. Ohne Golden File merkt man solche Änderungen erst, wenn ein
Export „irgendwie anders“ klingt.

## 3. Der Code: params.json → gen_ui.py → TUI/ABI

Die MPC-UI wird nicht von Hand gepflegt. Sie wird aus dem Plugin generiert.
Die Kette ist:

```
Plugin  →  host_sim dump  →  params.json
params.json + ui.json  →  gen_ui.py  →  TUI.json + Q-Links.json + PNG-Kit
```

`params.json` beschreibt **8 Parameter** in dieser Reihenfolge: `Mode`, `Trim`,
`Tilt`, `Clip`, `Transient`, `Ceiling`, `Release`, `Mono`. Jeder Eintrag hat
einen `kind` (`choice`, `float`, `int`), einen Default und — bei `choice` —
eine Liste von Labels. `Mode` ist `["Master", "Bus"]` und ausdrücklich **nicht
automatisierbar**; die Moduswahl ist eine Strukturentscheidung, kein Regler,
den ein Host pro Block schickt.

`gen_ui.py` macht aus dem Dump eine 4×4-Matrix mit 16 Reglern pro Seite. Ein
`choice`-Parameter wird als `switch` mit 2 bis 4 Segmenttasten gerendert
(`MAX_SWITCH_CHOICES = 4`). `ui.json` legt fest, was sichtbar ist:

```json
{ "param": "Transient", "widget": "knob",
  "visibleWhen": { "param": "Mode", "choice": "Bus" } }
{ "param": "Ceiling", "widget": "knob",
  "visibleWhen": { "param": "Mode", "choice": "Master" } }
```

`visibleWhen` wird beim Generieren gegen `params.json` validiert: Der
Referenzparameter muss `choice` oder `bool` sein, und `choice`/`index` müssen
existieren. Ein Tippfehler im Label bricht den Build, nicht erst die MPC.
Im Master-Modus sind damit 7 Regler sichtbar, im Bus-Modus 5 — die jeweils
anderen werden ausgeblendet, nicht deaktiviert. `validate.py` prüft danach die
erzeugte `TUI.json`: Q-Link-Rechtecke, Parameter-Handles 0…7, vorhandene
Bilder. Ergebnis: **0 Fehler, 0 Warnungen**.

Die zweite Hälfte der Kette ist das ABI. `framework/mpc_plugin.h` implementiert
die VST2-AEffect-Schnittstelle. Zwei Stellen sind für die UI entscheidend:

- `setProgram(i)` setzt alle Parameter und meldet **jeden** Parameter mit
  `audioMasterAutomate` an den Host; danach fordert es mit
  `audioMasterUpdateDisplay` ein Redraw an.
- `internalLoadState()` (also `effSetChunk`, ein Projekt- oder Preset-Load)
  macht dasselbe: erst alle Werte, dann alle Automate-Aufrufe, dann
  UpdateDisplay.

Der Grund ist die MPC-Firmware: Ein Programmwechsel kommt vom Host, nicht vom
Drehregler. Ohne die Meldungen bleibt die Oberfläche auf den alten
Knopfpositionen stehen, obwohl der Klang schon der neue ist. Der Testlauf mit
Programmwechsel zählt **48 Automate** und **6 UpdateDisplay**. Das sind sechs
Ladevorgänge mit je acht Parametern — Initialisierung, State-Runden und der
explizite Programmwechsel:

```
6 Ladevorgänge × 8 Parameter = 48 Automate
6 Ladevorgänge × 1 Redraw    =  6 UpdateDisplay
```

Ein einzelner Programmwechsel liefert 8 und 1. `tests/plugin-check.py` verlangt
deshalb mindestens 8 Automate und mindestens 1 UpdateDisplay: Die untere
Grenze prüft den Mechanismus, nicht die zufällige Zahl der Ladevorgänge.

## 4. Der Testvertrag: check.sh als einzige Wahrheit

Die Reihenfolge ist Teil des Vertrags: **erst der rote Test, dann der Code.**
Ein Test, der nach dem Code entsteht, beschreibt nur, was der Code zufällig
tut. Ein Test, der vorher rot war, beschreibt, was der Code tun soll.

`scripts/check.sh` ist die eine Wahrheit vor dem Commit. Es läuft:

| Stufe | Was | Ergebnis |
|---|---|---|
| Messkette | `tests/selftest.py` | 13/13 |
| Lektionen | `tests/lesson-check.py` (Status, Quiz, Szenen, Geometrie) | bestanden |
| Plugin | `tests/plugin-check.py` | 10/10 |
| Alias | `tests/alias-check.py 997 --clip 1.0` | −105,4 dBc |
| Loudness | `tests/loudness-check.py` | 5/5 |
| Skripte | `bash -n` über `scripts/*.sh` | ok |
| Publish-Guard | `publish-lessons.sh` muss unfertige Lektionen verweigern | verweigert (erwartet) |

Der Guard ist Teil des Checks: Ein Guard, der nie Nein sagt, ist kein Guard.
`check.sh` ruft `publish-lessons.sh` ohne `PUBLISH_CONFIRM` auf und **erwartet**
einen Fehlschlag. Käme ein Erfolg, wäre der Check rot.

Zwei Dinge sind bewusst **nicht** in `check.sh`, weil sie eigene Läufe
brauchen:

**Sanitizer.** Der native Testbuild kann zusätzlich mit
`-fsanitize=address,undefined` gebaut werden. ASan findet Pufferüberläufe und
Use-after-free, UBSan findet vorzeichenbehaftete Überläufe, ungültige Shifts
und fehlerhafte Konvertierungen. Genau diese Klassen stecken in
Ringpuffer-Indizes und Sample-Konvertierung.

**Allokations-Verbot.** Ein Hook um `operator new`/`malloc` zählt Allokationen
und bricht ab, wenn im `process()` eine stattfindet. Der Audiopfad darf nicht
allokieren, nicht locken, nicht loggen. Das ist keine Stilfrage: Eine
Allokation kann den Speicher defragmentieren und einen Block zu spät
zurückgeben — auf der MPC ist das ein Xrun, kein Schönheitsfehler.

Dazu kommt der **Red-Team-Agent**. Er bekommt nur den Plan und die Tests,
nicht die Implementierung. Seine Aufgabe ist, Lücken zu finden: Welche
Invariante prüft kein Test? Welcher Parameter wird geclampt, aber nicht
geglättet? Welcher Fehler würde alle Tests grün lassen? Der Agent, der den
Code geschrieben hat, ist für diese Frage befangen.

Ein Agentenauftrag ist erst vollständig, wenn er den roten Test nennt, den
Diff klein hält, `check.sh` unverändert lässt und die Messwerte vorlegt. Wer
einem Agenten erlaubt, Tests zu ändern, hat keinen Test mehr — er hat dann nur
noch eine Beschreibung des Ist-Zustands.

**Ein Commit pro DSP-Stufe** ist die Regel, die aus dem Projekt kommt. HPF,
Tilt, Mono, Clipper und Limiter getrennt committen, damit `git bisect` eine
Regression auf eine Stufe eingrenzen kann. Im QMaster-Verlauf liegt die
DSP-Kette dagegen in einem einzigen Commit (`03c9e66`). Genau deshalb steht die
Regel jetzt im Plan: Nachtäglich ist sie nicht mehr herstellbar.

## 5. Die Messung: was der Harness tatsächlich zeigt

Die Messkette wird zuerst gegen bekannte Signale geprüft. `selftest.py` macht
13 Prüfungen; ein Auszug:

| Prüfung | Soll | Ist |
|---|---|---|
| Sinus 997 Hz, Peak | −6,02 dBFS | −6,02 |
| Sinus 997 Hz, RMS | −9,03 dBFS | −9,03 |
| Sinus stereo, LUFS | −6,0 | −6,00 |
| Dirac, Peak | −0,92 dBFS | −0,92 |
| Anti-Phase 60 Hz, Korrelation | −1,0 | −1,000 |
| Anti-Phase, Mid | null | null (Auslöschung erkannt) |
| Pink Noise, RMS | −20,0 dBFS | −20,00 |
| Loop, Dauer | 20,0 s | 20,00 |
| Loop, Intersample | TP > Peak | +0,90 > −1,01 |
| Release-Guard | nicht releasefähig | wird abgelehnt |

Der letzte Punkt ist der wichtigste: Der Guard muss **Nein** sagen können. Ein
Release-Check, der einen Loop mit −11,0 LUFS, PLR 11,9 und LRA 0,8 durchlässt,
misst nicht die Zielwerte, sondern nur sich selbst.

Danach das Plugin, 10/10:

| Prüfung | Ergebnis |
|---|---|
| Parameter | Mode, Trim, Tilt, Clip, Transient, Ceiling, Release, Mono |
| Mode automatisierbar | nein |
| Programme | Init, CD Loud, CD Dynamic, Streaming Safe, Bus Drums, Bus 808 |
| Latenz Master | 102 gemessen, 102 gemeldet |
| Latenz Bus | 102, identisch zum Master |
| UI-Update bei Programmwechsel | 48 Automate, 6 UpdateDisplay |
| True Peak default | −1,00 dBTP |
| Sample-Peak default | −1,40 dBFS |
| True Peak, Clip 100 % | −1,00 dBTP |
| Ceiling −2 dBTP | −2,00 dBTP |

Die beiden Peaks sind kein Widerspruch, sondern der Guard:
`−1,00 − (−1,40) = 0,40 dB`. Der 4×-Detektor begrenzt den True Peak auf
−1,00 dBTP; in diesem Lauf bleiben die Samples 0,40 dB darunter. Genau dieser
Abstand ist der Puffer, den der Guard abdeckt.

Der Alias-Check bestätigt die Rechnung aus Abschnitt 2.2: Grundton −1,2 dBFS,
stärkster Alias −106,6 dBFS bei 19175 Hz, relativ **−105,4 dBc**. Die
Schwelle liegt bei −60 dBc; die Reserve beträgt `105,4 − 60 = 45,4 dB`.

Der Loudness-Check fährt den synthetischen Loop durch den Master:

| Größe | vorher | nachher |
|---|---|---|
| Integrated | −11,0 LUFS | −8,5 LUFS |
| True Peak | +0,90 dBTP | −1,10 dBTP |
| PLR | 11,90 | 7,40 |
| Clipping | 0 | 0 |

Fünf Prüfungen, alle grün: lauter, im Zielkorridor, TP ≤ −1,0, PLR 6–8, kein
Clipping. Der Host-Simulator meldet für QMaster **20/20**, `validate.py`
**0/0** (0 Fehler, 0 Warnungen).

Eine Zahl fehlt bewusst: Wie gut das Plugin auf echter Musik klingt. Das
entscheidet kein Test, sondern der Export und das Ohr. Die Tests entscheiden
nur, ob die Maschine das tut, was spezifiziert wurde.

## 6. Fehler & Test: der Katalog

Jeder dieser Fehler ist im Projekt wirklich passiert. Die Reihenfolge ist die
Reihenfolge, in der sie gefunden wurden.

**Geteilter FFT-Puffer zwischen links und rechts (QDSSD).** Analyse und
Synthese benutzten denselben Spektrum-Puffer für beide Kanäle. Der rechte Kanal
überschrieb das Spektrum des linken, bevor er es zurücktransformierte; das
Ergebnis war Übersprechen, kein Stereobild. Der Test, der ihn heute verhindert:
ein Signal, das nur links Energie hat, und **Crosstalk L≠R < −100 dB**. Alles
darüber wäre ein Zustand, den ein Kanal vom anderen erbt.

**OLA-Ring-Offset (QDSSD).** Die Overlap-Add-Schleife schrieb den Block um
einen Ringplatz versetzt zurück. Die Hann-Fenster benachbarter Frames lagen
nicht mehr aufeinander; an der Naht blieb ein Pegelverlust. Der Test: **Impuls
an der erwarteten Position, Rekonstruktion = 1**. Bei 75 % Overlap (1024
Punkte, Hop 256) ist die COLA-Summe des Hann-Fensters 2, die OLA-Normierung also
0,5. Weicht der Offset um einen Ringplatz ab, ist die Summe an der Naht nicht
mehr 2, sondern kleiner — der Test misst die Abweichung als Pegelverlust.

**Absolute dB im Spektrum (QDSSD).** Die Maske verglich absolute dBFS-Werte
miteinander. Ein leiser Frame hatte dadurch andere Gewichte als ein lauter
Frame mit identischem Spektrum; jede Fenster-Nebenkeule sah wie Signal aus.
Die Lösung: Das Spektrum wird **relativ zum lautesten Band** in dB gespeichert.
Der Test: **Gain-Invarianz der Maske** — Eingang ×0,5, Maske unverändert. Ein
absoluter Pegel würde die Maske mitverschieben und den Test rot machen.

**Lazy Bus Open (QDSSD).** Der Shared-Memory-Pool wurde im Konstruktor
geöffnet. Baute der Host den Empfänger vor dem Sender, existierte der Pool noch
nicht, und der Empfänger blieb für immer taub. Die Lösung: Der Pool wird
**lazy in `process()`** geöffnet, damit die Ladereihenfolge keine Rolle spielt.
Der Test: **Empfänger vor Sender konstruieren, Daten müssen fließen** — plus
`bus-test` mit 8 Bussen, Unabhängigkeit der Busse und 1000 Frames
Round-Trip.

**24-Bit-WAV falsch geschrieben (QMaster).** Der Renderer schrieb als erstes
Byte `s >> 8` statt `s & 0xff`. Das Signal wurde dadurch effektiv um den Faktor
256 zu klein geschrieben. Das sind

```
20·log10(256) = 48,2 dB
```

zu leise — es sah aus wie Stille. Gefunden durch den Vergleich mit dem
**erwarteten Peak** der Testsignale, nicht durch Hören. Der Test: Peak nach dem
Render gegen den bekannten Eingangspegel prüfen; die 24-Bit-Bytes sind
little-endian `s & 0xff`, `(s >> 8) & 0xff`, `(s >> 16) & 0xff`.

**Ceiling-Smoother startet ungeguardet (QMaster).** `reset()` setzte den
Glätter auf den rohen Ceiling-Wert statt auf den geglätteten Startwert. Die
ersten **20 ms** waren dadurch **0,25 dB** zu heiß. Gefunden wurde es, weil der
globale Peak bei **5 ms** lag — ein Mastering-Limiter, der mitten im Track
seine höchste Spitze hat, ist verdächtig. Der Test: **Peak-Zeitpunkt prüfen**;
der globale Peak darf nicht in der Einschwingphase des Glätters liegen.

**Der „4×“-Detektor war nur 2× (QMaster).** Nach dem Umzug des Limiters auf
1× wurde der Detektor nicht mitgezogen: Eine Halfband-Stufe fehlte. Der
gemeldete True Peak blieb bei **−0,1 dBTP**, obwohl der Sample-Peak bei
**−1,25 dBFS** lag — eine Lücke von 1,15 dB, größer als der 0,40-dB-Guard.
Behoben mit zwei Halfband-Stufen (1×→2×→4×) und 0,40 dB Guard. Der Test:
**TP gegen Sample-Peak prüfen**; die Differenz muss innerhalb des Guards
bleiben (`−1,00` gegen `−1,40`).

**Bandpass-Leckage als „Alias“ gedeutet (QMaster).** Die erste Alias-Messung
nutzte `bandpass` mit Q = 30 und `astats` und zeigte Energie bei **1229 Hz**
mit **−25,3 dBFS** — unverändert, egal ob 15 oder 31 Filter-Taps. Ein
Bandpass 2. Ordnung mit Q = 30 dämpft einen 232 Hz entfernten 997-Hz-Ton nur um
etwa **22 dB**; aus −3,2 dBFS Grundton wird so −25,3 dBFS „Alias“. Die FFT mit
65536 Punkten, Hann-Fenster und 0,67-Hz-Bins zeigte den stärksten echten Alias
bei **−105,4 dBc**. Der Test: **FFT statt Bandpass**, und die Regel: Ändert
sich ein Ergebnis nicht, wenn man das Messsystem ändert, ist die Messung
verdächtig.

**Die Fehlinterpretation „−0,09 dBFS = MPC-Normalisierung“ (QMaster).** Beide
alten Exporte peakten exakt bei −0,09 dBFS, und daraus wurde geschlossen, der
MPC-Export normalisiere. Der Nutzer bestätigte das Gegenteil. Der Gegenbeweis
steht in Abschnitt 2.3 und 2.4: PLR **7,7 statt 17,7**, und **309 bzw. 261
Samples** auf 0,99. Eine reine Pegelanhebung kann den PLR nicht ändern; eine
Decke aus hunderten Samples ist ein Limiter, kein Normalisierer. Die Ursache
war der Maximizer der alten Vierer-Kette (Kompressor, Clipper, Maximizer und
ein weiteres Plugin), der bei −0,09 dBFS begrenzte. Der Test: **PLR vergleichen
und Samples an der Decke zählen** — zwei unabhängige Metriken, nicht eine.

| Fehler | Gefunden durch | Test heute |
|---|---|---|
| geteilter FFT-Puffer | Links-only-Signal | Crosstalk < −100 dB |
| OLA-Ring-Offset | Impuls an falscher Position | Impuls + Rekonstruktion = 1 |
| absolute dB im Spektrum | leiser Frame, andere Maske | Gain-Invarianz |
| Lazy Bus Open | Empfänger vor Sender | Bus-Roundtrip, 1000 Frames |
| 24-Bit-Writer | 48 dB zu leise | erwarteter Peak |
| Ceiling-Smoother | Peak bei 5 ms | Peak-Zeitpunkt |
| „4×“ war 2× | TP −0,1 vs. Sample −1,25 | TP gegen Sample-Peak |
| Bandpass-Leckage | −25,3 dBFS bei 1229 Hz | FFT, dBc |
| −0,09 dBFS fehlgedeutet | PLR 7,7 vs. 17,7 | PLR + Sample-Zählung |

## 7. Anwendung: ein generierter DSP-Change im Review

Ein Agent schlägt eine Änderung vor, zum Beispiel einen anderen Tilt-Filter.
Die Review-Reihenfolge ist immer dieselbe:

**1. Einheiten.** Steht im Code `Db`, `Lin`, `Hz`, `Sec` — oder ein nackter
`float`? Der Renderer nimmt normalisierte Werte: `Trim = (dB + 12) / 24`,
`Ceiling = (dBTP + 2) / 2`, `Mono = Hz / 200`. Ein Fehler von 1 % im
normalisierten Trim sind `0,24 dB`; eine Verdopplung des normalisierten
Ceiling-Werts sind 1 dB. Wer die Einheit nicht nennen kann, hat die Änderung
nicht verstanden.

**2. Stabilität.** Liegen die Pole innerhalb des Einheitskreises? Werden die
Koeffizienten in `double` in `prepare()` gerechnet und pro Sample als `float`
verwendet? Steht `pow`/`exp`/`log` im Audiopfad? Letzteres ist verboten, nicht
aus Geschwindigkeitsgründen, sondern weil es bei jedem Sample teuer und
schwer zu testen ist. Ein Stabilitätstest ist der Sweep 20 Hz–20 kHz plus
60 s Stille gegen Denormals.

**3. Allokation.** Kein `new`, kein `malloc`, kein Lock, kein Log im
`process()`. Der Hook zählt; steht der Zähler nach einem Block nicht auf null,
ist die Änderung nicht commit-fähig.

**4. Latenz.** Der Impuls muss bei 102 Samples bleiben. Ändert die Änderung die
Latenz, muss sie gemeldet und im Renderer kompensiert werden — sonst ist jede
folgende Messung um 2,3 ms verschoben und der Vergleich mit dem Golden File
falsch.

**5. Null, Impuls, Alias.** Drei Signale, drei Fragen: Kommt bei 0 dB exakt
dasselbe heraus (Null-Test)? Steht der Impuls an der erwarteten Stelle, und
ist die Rekonstruktion 1? Liegt der stärkste Nicht-Harmonische unter −60 dBc
(FFT, nicht Bandpass)? Diese drei Tests decken die häufigsten DSP-Fehler ab:
versteckter Gain, Zeitversatz, nichtlineare Verzerrung.

**6. Messen.** Erst danach der End-to-End-Lauf: Loop durch das Plugin, LUFS,
TP, PLR, Clipping. Der PLR wird gegen den Rohmix verglichen, nicht gegen die
Erinnerung. Im Beispiel ändert sich der PLR um 10 dB — das war
Dynamikbearbeitung; um 0,7 dB — das war Gain.

**7. Commit.** `check.sh` grün, Messwerte in `REPORT.md`, Entscheidung in
`DECISIONS.md`, offener Punkt in `KNOWN_ISSUES.md`. Ein Commit pro Stufe.

**8. Review durch den Red-Team-Agenten.** Er sieht Plan und Tests, nicht den
Diff. Antwortet er mit „welcher Test verhindert eigentlich, dass der
Ceiling-Smoother beim Reset zu heiß startet?“, ist die Lücke gefunden, bevor
sie auf der MPC knallt.

Ein Change wird abgelehnt, wenn eine der Zahlen aus 1–6 fehlt. Nicht weil der
Code hässlich wäre, sondern weil man sonst nicht weiß, was man da eigentlich
abnimmt.

## 8. Anwendung: die Veröffentlichungspforte

Die Lektionen werden während der Entwicklung geschrieben, aber **einmal als
Ganzes** veröffentlicht. Die Pforte besteht aus vier Bedingungen:

1. Alle `lesson.json` stehen auf `"status": "final"`.
2. `check.sh` ist grün — inklusive Publish-Guard, der unfertige Lektionen
   verweigern muss.
3. Jede Zahl im Text stimmt mit dem letzten `REPORT.md` überein, jede
   Quiz-Antwort ist nachgerechnet, jede Szene rendert.
4. `PUBLISH_CONFIRM=yes` ist gesetzt.

`scripts/publish-lessons.sh` prüft die Status und verweigert die
Veröffentlichung, solange eine Lektion nicht final ist. Der Aufruf ohne
Bestätigung schlägt fehl — und genau dieser Fehlschlag ist Teil von `check.sh`.
Ein Publish-Skript, das ohne Bestätigung durchläuft, wäre die gefährlichste
Zeile im Repo.

Für QMaster heißt das konkret: 13 Messketten-Prüfungen, 10 Plugin-Prüfungen,
Alias bei −105,4 dBc, 5 Loudness-Prüfungen, 0 Fehler / 0 Warnungen in
`validate.py`, 20/20 im Host-Simulator. Erst wenn diese Zahlen zusammenpassen,
darf aus einem generierten DSP-Change ein Commit werden. Aus einem Commit wird
noch keine Veröffentlichung; die Pforte bleibt zu, bis auch die Sprache, die
Links und die Fehlerkatalog-Vollständigkeit geprüft sind.

Der Leitsatz steht im Plan und ist die Kurzfassung dieser Lektion:

> **Was nicht messbar ist, ist nicht gebaut.**
