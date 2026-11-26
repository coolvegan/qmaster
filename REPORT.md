# Mess-Report — Phase 0

Stand: 2026-11-26
Zweck: Bevor DSP gebaut wird, muss die Messkette selbst stimmen. Dieser Report
hält fest, was der Harness an Signalen mit bekanntem Pegel liefert — und was
noch fehlt.

## Harness

| Werkzeug | Aufgabe |
|---|---|
| `tools/measure.py` | LUFS, LRA, True Peak, PLR, Crest, DC, Clipping, 16-Band-Balance, Mono < 120 Hz |
| `tools/make-signals.py` | deterministische Testsignale ohne externe Assets |
| `scripts/release-check.sh` | Pass/Fail gegen die Abnahmekriterien |
| `scripts/codec-check.sh` | Ogg-Vorbis-q9-Durchlauf und Rückvergleich |
| `tests/selftest.py` | prüft die Messkette gegen bekannte Pegel |

Der Selbsttest läuft mit **13 Prüfungen**, alle grün. Wenn er rot ist, sind alle
Zahlen in diesem Report wertlos.

## Baseline (synthetische Signale)

Alle Dateien 44,1 kHz, 16 Bit, stereo (außer wo angegeben).

| Signal | Dauer | Peak | RMS | LUFS | True Peak | PLR | LRA |
|---|---|---|---|---|---|---|---|
| Sinus 997 Hz, mono, A = 0,5 | 5 s | −6,02 | −9,03 | **−9,0** | −6,0 | 3,0 | 0,0 |
| Sinus 997 Hz, stereo identisch | 5 s | −6,02 | −9,03 | **−6,0** | −6,0 | 0,0 | 0,0 |
| Sinus 997 Hz, nur links | 5 s | −6,02 | −12,04 | **−9,0** | −6,0 | 3,0 | 0,0 |
| Dirac | 1 s | −0,92 | — | — | −0,90 | — | — |
| Pink Noise, RMS −20 dBFS | 10 s | −7,41 | −20,00 | −18,8 | −7,4 | 11,4 | 0,1 |
| Anti-Phase 60 Hz (L = −R) | 5 s | −6,02 | −9,03 | −9,6 | −6,0 | 3,6 | 0,0 |
| Loop (Kick/Bass/Snare/Hat, tanh) | 20 s | −1,01 | −10,25 | −11,0 | **+0,90** | 11,9 | 0,8 |

## Befunde

### 1. Stereo summiert +3,01 dB

Derselbe Sinus misst mono **−9,0 LUFS**, stereo identisch **−6,0 LUFS**. Der
Grund ist die Definition: Loudness summiert die **Kanalleistungen**, nicht den
Mittelwert. Zwei identische Kanäle verdoppeln die Leistung → +3,01 dB.

Der Links-only-Fall zeigt die Falle: Der RMS über alle Samples fällt auf
−12,04 dBFS (die Hälfte der Samples ist null), die Loudness bleibt aber −9,0
LUFS, weil nur der aktive Kanal zählt. Wer RMS und LUFS gleichsetzt, liegt bei
einseitigen Signalen um 3 dB daneben.

### 2. True Peak ist nicht Sample Peak

Der Loop ist auf **−1,01 dBFS Sample Peak** normalisiert — und misst trotzdem
**+0,90 dBTP**. Das sind **1,91 dB Überschreitung** zwischen den Samples. Genau
deshalb ist der Deckel −1,0 dBTP und nicht −1,0 dBFS. Ein reiner Sample-Peak-
Meter hätte das Signal für sicher erklärt.

### 3. Auslöschung wird erkannt

Anti-Phase 60 Hz: Korrelation **−1,000**, `mid_vs_channels` = `null`. Der
Release-Check wertet das als Fehler. Für den Mono-Check unter 120 Hz ist das
die richtige Härte: Bass, der auf dem Handy verschwindet, ist ein Fehler, kein
Geschmack.

### 4. Bandanalyse

16 geometrische Bänder von 60 Hz bis 16 kHz, getrennt mit 24 dB/Okt-Filtern
(Highpass/Lowpass 4. Ordnung je Flanke). Ein 997-Hz-Sinus landet im Band
**980–1390 Hz** (Mitte 1167 Hz), die Nachbarbänder liegen ≥ 6,4 dB darunter,
alle fernen Bänder ≤ −17,8 dB.

### 5. Der Release-Guard greift

Der Loop wird vom `release-check.sh` abgelehnt: −11,0 LUFS statt −8 ± 1,
PLR 11,9 statt 6–8, LRA 0,8 statt 4–7. Der Guard prüft also nicht nur, ob das
Skript läuft, sondern ob es Nein sagen kann.

### 6. Codec-Check

Ogg Vorbis q9 auf dem Loop: Δ Loudness **+0,10 LU**, Δ True Peak **+0,10 dB**,
größte Bandabweichung **0,11 dB**. Der Check ist empfindlich genug, um
Ausreißer zu zeigen, ohne bei sauberem Material grundlos rot zu werden.

## Offen (blockiert)

| Punkt | Warum blockiert | Nächster Schritt |
|---|---|---|
| MPC-Export normalisiert? | braucht das Gerät | eine bekannte Datei exportieren, Peak messen; erwartet −0,09 dBFS, wenn normalisiert |
| Echte Beats | liegen nicht im Repo | 3 Beats dry/FX exportieren, unnormalisiert |
| LRA | braucht ≥ 20 s Material | mit den echten Beats erledigen |

## Reproduktion

```bash
python3 tools/make-signals.py /tmp/qm-signals
python3 tests/selftest.py
python3 tools/measure.py /tmp/qm-signals/loud_loop.wav
scripts/release-check.sh /tmp/qm-signals/loud_loop.wav   # erwartet: FAIL
scripts/codec-check.sh  /tmp/qm-signals/loud_loop.wav   # erwartet: PASS
```

## Grenzen

- Alle Werte sind **synthetisch**. Sie validieren die Messkette, nicht die Musik.
- `ebur128` liefert LRA erst ab ausreichender Dauer sinnvoll; unter 20 s wird
  das Kriterium übersprungen.
- Die Bandfilter sind 4. Ordnung, keine Brickwall. Benachbarte Bänder
  überlappen an den Kanten; für Balance-Vergleiche reicht das, für exakte
  Bandpegel nicht.
- Der Mono-Check filtert mit LR4 bei 120 Hz. Andere Grenzfrequenzen ändern das
  Ergebnis; die Grenze ist eine Konvention, keine Wahrheit.

## Phase 1 — QMaster nativ (2026-11-26)

Der native Build läuft durch: `host_sim` 20/20, `validate.py` 0 Fehler /
0 Warnungen, `plugin-check.py` 9/9, `alias-check.py` bestanden.

| Prüfung | Ergebnis |
|---|---|
| Latenz Master | 102 Samples gemessen, 102 gemeldet |
| Latenz Bus | 102 Samples, identisch zu Master |
| True Peak, Default (Clip 30 %) | −1,20 dBTP |
| True Peak, Clip 100 % | −1,00 dBTP |
| Ceiling −2 dBTP | −2,20 dBTP |
| Alias, Clip 0 % | −120,0 dBc |
| Alias, Clip 100 % | −105,3 dBc bei 19175 Hz |

### Was der Alias-Test gelehrt hat

Die erste Messung mit `bandpass` + `astats` zeigte „Aliase" bei −25 dBFS — und
zwar unverändert, egal ob 15 oder 31 Taps im Oversampler. Das war kein DSP-
Fehler, sondern **Leckage des Messfilters**: Ein Bandpass mit Q = 30 dämpft
einen 232 Hz entfernten 997-Hz-Ton nur um etwa 22 dB. Genau dieser Wert erschien
als „Alias".

Die Wahrheit liefert eine FFT: 65536 Punkte, Hann-Fenster, Bins von 0,67 Hz.
Damit liegt der stärkste echte Alias bei **−105 dBc**. Der Test misst jetzt die
Messkette mit, nicht nur das Plugin.

### Warum die Kette so aufgebaut ist

- **Clipper bei 2×** — die Harmonischen entstehen oberhalb der Basis-Nyquist,
  der 31-Tap-Halbband filtert sie vor der Dezimierung weg.
- **Limiter bei 1×** — er muss die Spitzen des *fertigen* Signals kontrollieren,
  nicht die eines Zwischensignals.
- **4×-Detektor** — interpoliert zwischen den 1×-Samples und sieht damit die
  Spitzen, die ein Sample-Peak-Meter verpasst.
- **0,40 dB Guard** — deckt den Restfehler des Detektors bei starker
  Übersteuerung ab.

## Phase 1 — End-to-End (synthetischer Loop, 2026-11-26)

`tools/render.cpp` schickt eine WAV-Datei durch den nativen Build und
kompensiert die gemeldete Latenz. Damit lässt sich die Kette ohne MPC prüfen.

Loop durch das Programm „CD Loud“:

| Größe | vorher | nachher |
|---|---|---|
| Integrated | −11,0 LUFS | **−8,5 LUFS** |
| True Peak | +0,90 dBTP | **−1,10 dBTP** |
| PLR | 11,9 dB | **7,4 dB** |
| Clipping | 0 | 0 |

Das ist kein Beweis für echte Musik, aber der Beweis, dass die Kette die
Zielwerte erreicht: −8 ±1 LUFS, TP ≤ −1,0, PLR 6–8.

### Drei Fehler, die der End-to-End-Test gefunden hat

1. **24-Bit-WAV falsch geschrieben.** Der Renderer schrieb `s >> 8` statt
   `s & 0xff` als erstes Byte — das Ergebnis war 48 dB zu leise und sah wie
   Stille aus. Gefunden durch Vergleich mit dem erwarteten Peak.
2. **Ceiling-Smoother startete ungeguardet.** `reset()` setzte den Glätter auf
   den rohen Ceiling-Wert; die ersten 20 ms waren dadurch 0,25 dB zu heiß.
   Gefunden, weil der globale Peak bei 5 ms lag.
3. **Der „4×“-Detektor war nur 2×.** Nach dem Umzug des Limiters auf 1× wurde
   der Detektor nicht mitgezogen: TP blieb bei −0,1 dBTP, obwohl der
   Sample-Peak bei −1,25 lag. Behoben mit zwei Halfband-Stufen (1×→2×→4×) und
   0,40 dB Guard.

Alle drei wären auf der MPC als „klingt irgendwie leise/falsch“ aufgefallen —
ohne die Offline-Messung hätte die Ursache Tage gekostet.

## Offen (Phase 1)

| Punkt | Warum blockiert | Nächster Schritt |
|---|---|---|
| Installation auf der MPC | Gerät nicht angeschlossen | `scripts/install-mpc.sh` bei verbundenem Laufwerk |
| CPU mit 1× Master + 5× Bus | nur Desktop-Messung (0,32 %) | 10-Minuten-Loop auf dem Gerät |
| State-Roundtrip auf dem Gerät | `.xpj` undurchsichtig | Preset speichern, MPC neu starten, laden |
| Echte Beats durch QMaster | kein WAV-Renderer im Harness | Renderer-Tool oder MPC-Export |
| −8 LUFS aus einem echten Mix | braucht die Beats | Release-Check auf dem Export |

