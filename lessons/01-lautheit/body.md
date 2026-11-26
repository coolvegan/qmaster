## Worum es geht

Lautheit ist die Zahl, an der QMaster gemessen wird. Wer sie nicht messen kann,
mastert nach Gefühl — und Gefühl hat keinen True-Peak-Meter.

Diese Lektion baut die Messkette von Grund auf: Peak, RMS, dB, Stereo-Summe,
K-Wichtung, LUFS, Gating, True Peak, PLR. Jede Zahl stammt aus einem Lauf des
Harness im Repo, nicht aus einem Lehrbuch.

> **Status: Draft.** Diese Lektion wird während der Entwicklung geschrieben und
> erst veröffentlicht, wenn alle Teile geprüft sind.

## 1. Peak ist nicht Lautheit

Ein Sinus mit Amplitude 0,5 hat einen Sample-Peak von

```
20 · log10(0,5) = −6,02 dBFS
```

Sein Effektivwert ist aber kleiner:

```
RMS = 0,5 / √2 = 0,3536
20 · log10(0,3536) = −9,03 dBFS
```

Und die Loudness? Misst man denselben Sinus mono bei 997 Hz, zeigt `ebur128`
**−9,0 LUFS**. Peak −6,02, RMS −9,03, Loudness −9,0: drei Zahlen, ein Signal.

Peak sagt, wie viel Headroom bleibt. RMS sagt, wie viel Energie drinsteckt.
Loudness sagt, wie laut es das Ohr empfindet. Keine davon ersetzt die anderen.

## 2. dB: zwei Formeln, ein Missverständnis

Es gibt zwei dB-Formeln, und die Verwechslung ist der häufigste Rechenfehler:

```
Amplitude:  20 · log10(A / A0)
Leistung:   10 · log10(P / P0)
```

Warum? Leistung ist proportional zum Quadrat der Amplitude. Ein Faktor 2 in der
Amplitude ist ein Faktor 4 in der Leistung:

```
20 · log10(2) = +6,02 dB
10 · log10(4) = +6,02 dB
```

Merksätze:

| Verhältnis | Amplitude | Leistung |
|---|---|---|
| halbe Amplitude | −6,02 dB | −6,02 dB |
| ein Viertel | −12,04 dB | −12,04 dB |
| doppelte Leistung | +3,01 dB | +3,01 dB |
| zehnfache Leistung | +10 dB | +10 dB |

Die dritte Zeile ist die wichtigste für Loudness: **doppelte Leistung sind
3,01 dB**, nicht 6.

## 3. RMS und Crest

RMS ist die Wurzel aus dem Mittel der Quadrate:

```
RMS = √( (1/N) · Σ x[n]² )
```

Für einen Sinus gilt exakt `RMS = A/√2`. Für Musik ist RMS eine
Energie-Kennzahl, keine Lautheit — aber eine nützliche.

Der Crest-Faktor ist der Abstand zwischen Peak und RMS:

```
Crest = Peak − RMS
```

Gemessen:

| Signal | Peak | RMS | Crest |
|---|---|---|---|
| Sinus | −6,02 | −9,03 | 3,01 dB |
| Loop (Kick/Bass/Snare/Hat) | −1,01 | −10,25 | 9,24 dB |
| Pink Noise | −7,41 | −20,00 | 12,59 dB |

Ein Sinus hat 3 dB Crest, weil er keine Transienten hat. Ein Beat hat 9 dB,
weil Kick und Snare Spitzen über der Dauerenergie erzeugen. Je mehr Crest,
desto mehr muss ein Limiter später abfangen.

## 4. Stereo summiert: +3,01 dB

Derselbe 997-Hz-Sinus, einmal mono und einmal identisch auf beiden Kanälen:

| Variante | RMS (alle Samples) | LUFS |
|---|---|---|
| mono | −9,03 | **−9,0** |
| stereo, L = R | −9,03 | **−6,0** |
| stereo, nur L | −12,04 | **−9,0** |

Der Grund steht in der Definition: Loudness summiert die **Leistungen der
Kanäle**, sie mittelt sie nicht. Zwei identische Kanäle verdoppeln die Leistung
→ +3,01 dB.

Der Links-only-Fall ist die Falle: Der RMS über alle Samples fällt auf −12,04
dBFS, weil die Hälfte der Samples null ist. Die Loudness bleibt bei −9,0 LUFS,
weil nur der aktive Kanal zählt. Wer RMS und LUFS gleichsetzt, liegt bei
einseitigen Signalen um 3 dB daneben.

Konsequenz: Ein Vollaussteuerungs-Sinus bei 1 kHz misst

- mono: **−3,0 LUFS**
- stereo identisch: **0,0 LUFS**

## 5. K-Wichtung: das Ohr ist kein Messgerät

Ein 60-Hz-Ton und ein 3-kHz-Ton mit gleichem Pegel werden nicht gleich laut
empfunden. Deshalb bewertet Loudness das Signal vor der Messung mit einem
Filter, der die Empfindlichkeit des Ohrs nachbildet (**K-Wichtung**):

- ein Hochpass um **38 Hz** (sehr tiefe Frequenzen zählen kaum),
- ein Hoch-Shelf mit **+4 dB** oberhalb etwa **1,5 kHz** (Höhen zählen mehr).

Bei 997 Hz ist die Wichtung praktisch 0 dB: RMS −9,03 → LUFS −9,0. Bei 60 Hz
sieht man den Hochpass: Der Anti-Phase-Test bei 60 Hz hat RMS −9,03, aber
Loudness **−9,6 LUFS** — 0,6 dB leiser.

Pink Noise zeigt die andere Seite: RMS −20,0 dBFS, Loudness **−18,8 LUFS**.
Die Höhen, die im Pink-Spektrum stecken, werden um 1,2 dB angehoben.

## 6. LUFS und Gating

Die integrierte Loudness ist definiert als

```
L = −0,691 + 10 · log10( Σ_kanäle mean( (K · x)² ) )
```

Die −0,691 kalibrieren die Skala so, dass ein Referenzsignal bei 0 LUFS
ankommt. Gemessen wird in Blöcken:

| Größe | Fenster | Bedeutung |
|---|---|---|
| Momentary | 400 ms | „wie laut gerade" |
| Short-term | 3 s | „wie laut in dieser Passage" |
| Integrated | ganzer Track | die eine Zahl |

Vor dem Mitteln wird **gegatet**, sonst würde Stille den Wert nach unten
ziehen:

1. **Absolutes Gate:** Blöcke unter −70 LUFS fliegen raus.
2. **Relatives Gate:** Blöcke, die mehr als 10 LU unter dem Mittel der
   verbleibenden Blöcke liegen, fliegen raus.

Erst danach wird gemittelt. Deshalb ändert ein leiser Intro-Teil die
integrierte Loudness kaum — und deshalb kann man sie nicht aus dem Peak
ableiten.

Die **Loudness Range (LRA)** ist die Spanne zwischen dem 10. und 95. Perzentil
der Short-Term-Loudness. Sie sagt, wie sehr der Track atmet. Unter 20 s
Material ist sie nicht sinnvoll; der Release-Check überspringt sie dann.

## 7. True Peak: der Wert zwischen den Samples

Ein Sample-Peak-Meter sieht nur die Abtastpunkte. Das analoge Signal zwischen
ihnen kann höher liegen — besonders wenn viele Höhen und steile Flanken im
Spiel sind.

Der Loop im Report ist auf **−1,01 dBFS Sample Peak** normalisiert. `ebur128`
misst aber **+0,90 dBTP**. Das sind **1,91 dB Überschreitung** zwischen den
Samples.

Deshalb:

- **Sample Peak** ist eine Datei-Eigenschaft.
- **True Peak (dBTP)** ist eine Signal-Eigenschaft, geschätzt durch
  Oversampling (BS.1770 mindestens 4×).
- Ein Codec kann danach noch mehr Überschwingen erzeugen.

Der Deckel für QMaster ist **−1,0 dBTP**, nicht −1,0 dBFS. Wer Sample-Peak
misst und glaubt, er sei sicher, mastert 2 dB zu heiß.

## 8. PLR und der Zielkorridor

```
PLR = True Peak − Integrated Loudness
```

Der Loop: `0,90 − (−11,0) = 11,9 dB`. Ein Mastering auf −8 LUFS mit −1 dBTP
hätte `PLR = 7 dB`.

| Ziel | Wert | Bedeutung |
|---|---|---|
| Integrated | −8 ± 1 LUFS | kompetitive CD-Lautheit |
| True Peak | ≤ −1,0 dBTP | Codec-Reserve |
| PLR | 6–8 dB | dicht, aber nicht tot |
| LRA | 4–7 LU | der Track atmet noch |

Und die wichtigste Einordnung: **−14 LUFS ist keine Mastering-Vorgabe**, sondern
die Wiedergabe-Referenz von Spotify. Ein −8-LUFS-Master wird dort um etwa 6 dB
abgesenkt und klingt genauso laut wie ein −14-Master — nur dichter. Lautheit
auf Spotify ist kein Wettbewerb, den man gewinnen kann; Dynamik schon.

## 9. Selbst messen

```bash
python3 tools/measure.py master.wav
python3 tools/measure.py master.wav --json
scripts/release-check.sh master.wav
scripts/codec-check.sh master.wav
```

`measure.py` liefert Peak, RMS, Crest, LUFS, True Peak, PLR, LRA, DC, Clipping,
16 Bänder und den Mono-Check unter 120 Hz. `release-check.sh` prüft dieselben
Zahlen gegen die Tabelle oben und sagt Nein, wenn eines verfehlt wird.

Der Selbsttest der Messkette:

```bash
python3 tests/selftest.py
```

Er prüft bekannte Pegel (Sinus, Dirac, Anti-Phase, Pink Noise) und ob der
Release-Guard einen nicht release-fähigen Loop ablehnt.

## 10. Testmethoden, die diese Zahlen tragen

Eine Zahl ist nur so gut wie das Signal, an dem sie gemessen wurde. Deshalb
gibt es Signale mit bekanntem Pegel:

| Signal | Erwartung | Gemessen |
|---|---|---|
| Sinus 997 Hz, A = 0,5, mono | Peak −6,02, RMS −9,03, LUFS −9,0 | exakt |
| Derselbe Sinus stereo | LUFS −6,0 | exakt |
| Dirac | Peak −0,92 dBFS | −0,92 |
| Pink Noise, RMS −20 dBFS | RMS −20,0 | −20,00 |
| Anti-Phase 60 Hz | Korrelation −1,0, Mid = null | exakt |

`tests/selftest.py` prüft 13 dieser Erwartungen. Der Test testet die
**Messkette**, nicht das Plugin. Wenn er rot ist, sind alle Zahlen wertlos —
auch die schönen.

Drei Regeln, die daraus folgen:

1. **Nicht „plausibel" prüfen, sondern „erwartet".** −9,0 LUFS ist ein
   Prüfwert, weil A/√2 und die K-Wichtung bei 997 Hz bekannt sind.
2. **Das Messwerkzeug mitprüfen.** Ein Bandpass mit Q = 30 dämpft einen 232 Hz
   entfernten Ton nur um etwa 22 dB. Wer damit „Aliase" misst, misst die
   Leckage des eigenen Filters (Lektion 02 zeigt die FFT-Lösung).
3. **LRA erst ab 20 s.** Darunter ist die Perzentil-Verteilung nicht sinnvoll;
   der Release-Check überspringt sie dann bewusst.

## 11. Fehler, die zu diesen Zahlen geführt haben

Diese Lektion ist nicht vom Himmel gefallen. Drei Messfehler waren nötig:

**Der erste Testsinus war 21 dB zu leise.** `ffmpeg -f lavfi -i sine` liefert
nicht die Amplitude, die man erwartet: Der „−6-dB-Sinus" maß −27,1 dBFS. Statt
die Ursache zu suchen, generieren wir die Testsignale jetzt selbst — mit
bekannter Amplitude, in Python, ohne versteckte Skalierung.

**Der MPC-Export normalisiert.** Alle Testexporte peakten bei −0,09 dBFS. Ein
Delta-Signal, das eigentlich leiser sein muss, lag plötzlich genauso hoch.
Erst nach dem Abschalten der Normalisierung sind absolute Pegel vergleichbar.
Die Regel: **erst den Exportpfad messen, dann das DSP.**

**Der Mono-Downmix log.** `ffmpeg -ac 1` summiert die Kanäle; ein Stereo-Peak
von −1,03 dBFS erschien als +1,25 im Downmix. Das ist keine Clipping-Stelle im
Signal, sondern die Summe zweier Kanäle. Gemessen wird deshalb der
**Stereo-Peak**, nie ein Downmix.

Dazu kommt der beruhigende Fall: Ein Ergebnis, das sich **nicht ändert**, wenn
man das System ändert, ist verdächtig. Die „Aliase" bei −25 dBFS blieben
identisch, egal ob 15 oder 31 Filter-Taps — weil sie gar keine Aliase waren.
Diese Geschichte steht in Lektion 02, wo die FFT sie auflöst.

Die Programme (`CD Loud`, `Bus Drums`, …) bekommen ihre Zahlen in Lektion 03
und im Capstone; hier stehen nur die Messprinzipien.

## 12. Was das für QMaster heißt

1. Der Limiter arbeitet auf **True Peak**, nicht auf Sample Peak.
2. Das Oversampling ist kein Luxus: Es verhindert, dass der Clipper neue
   Spitzen zwischen den Samples erzeugt.
3. Ohne Offline-Messung ist kein Ziel erreichbar. Die MPC-UI hat keinen
   LUFS-Meter; also wird nach dem Export gemessen.
4. Ein Mix, der bei −11 LUFS schon 11,9 dB PLR hat, wird bei −8 LUFS entweder
   geclippt oder gebremst. Die Lautheit muss aus dem Mix kommen, nicht aus dem
   Limiter.

Die Rechenaufgaben dazu stehen im Selbsttest am Ende der Lektion.
