## Worum es geht

Ein Bass, der im Studio satt klingt, kann auf einem Handy fast verschwinden. Das
ist kein Lautsprecherproblem, sondern eine Rechenaufgabe: Das Handy spielt mono,
und was nur im Seitenkanal liegt, fällt bei der Summenbildung weg.

Diese Lektion baut die Antwort in sechs Kapiteln auf. Jedes Kapitel folgt den
sechs Schritten: Frage, Mathematik, Code, Messung, Fehler & Test, Anwendung.
Die Zahlen kommen aus den Analysen und dem Harness im Repo. Wo eine Zahl
gerechnet statt gemessen ist, steht es dabei.

## 1. Der Bass, der auf dem Handy verschwindet

### Die Frage

Warum hört man auf dem Handy keinen Bass, obwohl die Stereo-Datei im Studio
tief und breit klingt? Der Verdacht liegt nahe, dass der kleine Lautsprecher
einfach keine tiefen Frequenzen kann. Das ist ein Teil der Wahrheit. Der andere
Teil ist die Monosumme: Ein Handy-Lautsprecher gibt im Wesentlichen einen Kanal
wieder. Was in den beiden Kanälen gegeneinander läuft, löscht sich dabei aus.

Der Testfall steht in A2: ein 60-Hz-Sinus, links und rechts exakt gegenphasig.
Die Datei ist voller Energie, aber die Korrelation ist **−1,000**, der Mid-Anteil
ist **null**, und die Loudness liegt bei **−9,6 LUFS** (RMS **−9,03 dBFS**). In
der Monosumme bleibt von diesem Bass nichts übrig.

### Die Mathematik

Mid und Side sind eine andere Koordinatenbasis für dasselbe Stereosignal:

```
M = ½ · (L + R)
S = ½ · (L − R)

L = M + S
R = M − S
```

Für den gegenphasigen Bass gilt `R = −L`. Dann ist

```
M = ½ · (L − L) = 0
S = ½ · (L + L) = L
```

Die gesamte Bassenergie steckt im Side-Kanal. Die Monosumme ist `L + R = 0`.
Die Korrelation macht das sichtbar:

```
ρ = Σ (L · R) / √(Σ L² · Σ R²)
```

Bei `R = −L` ist der Zähler negativ und der Nenner positiv: `ρ = −1`. Je näher
ρ an −1 liegt, desto stärker löscht sich der Bass in mono aus. Je näher ρ an +1
liegt, desto besser überlebt er die Monosumme.

### Der Code

Der Mono Maker sitzt in `src/QMasterMpc.cpp`, Klasse `MonoMaker` ab Zeile 319.
Er arbeitet genau in dieser Basis: Mid und Side bilden, nur Side hochpassfiltern,
dann zurückrechnen.

```cpp
const float mid  = 0.5f * (l + r);
float side       = 0.5f * (l - r);
side = hp2.process (hp1.process (side));
l = mid + side;
r = mid - side;
```

Im Master-Pfad läuft er nach dem festen 24-Hz-Hochpass und dem Tilt, vor dem
Clipper:

```
In → Trim → 24 Hz High-Pass → Tilt → Mono Maker → Clipper → Limiter → Out
```

Wichtig: Der Mono Maker repariert keinen gegenphasigen Bass. Er entfernt den
Side-Anteil unter der eingestellten Frequenz. Aus `M = 0` wird unterhalb der
Grenzfrequenz auch noch `S ≈ 0`, und der Bass ist dort ganz weg. Die Reparatur
gehört in den Mix, nicht auf den Master.

### Die Messung

`tools/measure.py` filtert für den Mono-Check beide Kanäle mit einem LR4 bei
120 Hz und berechnet daraus Mid, Side und Korrelation. Für die Anti-Phase-Datei
aus A2 liefert der Lauf:

| Größe | Wert |
|---|---|
| Korrelation | **−1,000** |
| Mid relativ zu den Kanälen | **null** |
| Side − Mid | nicht definiert, weil Mid null ist |
| Integrated Loudness | **−9,6 LUFS** |
| RMS | **−9,03 dBFS** |

Der Nullwert ist kein Ausreißer, sondern die korrekte Antwort: Bei exakter
Gegenphase gibt es keinen Mid-Anteil. Ein Messwerkzeug, das hier trotzdem einen
Mid-Pegel zeigt, misst den falschen Punkt.

### Fehler & Test

Der Test dazu steht in `tests/selftest.py` und prüft zwei Dinge:

1. Die Korrelation der Anti-Phase-Datei ist **≤ −0,99**.
2. `mid_vs_channels_db` ist **None**, also echte Auslöschung.

Das ist der Beweis, dass der Mono-Check funktioniert. Würde man den Antiphase-Test
mit einem kaputten Analysator messen, käme ein Mid-Pegel heraus, und der Fehler
würde als „Bass ist doch da“ durchgehen. Der Test prüft die Messkette, nicht das
Plugin.

Die zweite Falle ist die Erwartung an den Mono Maker. Wer einen gegenphasigen
Bass durch den Master schickt und hofft, das Plugin drehe die Phase zurück,
bekommt Stille unter 120 Hz. Der Mono Maker macht kompatibel, indem er den
Side-Bass opfert. Er kann ihn nicht wiederherstellen.

### Anwendung

- **Mono 110–120 Hz** ist der Normalfall für einen Rap-Master.
- Ein absichtlich breiter Bass braucht einen niedrigeren Mono-Wert, nicht einen
  höheren.
- Gegenphasigen Bass im Mix mono machen, bevor der Master ins Spiel kommt.
- Ein Handy-Test ist ein Monotest. Er ersetzt keine Messung, zeigt aber sofort,
  ob der Bass nur auf der Side-Seite existiert.

## 2. Der Biquad: Differenzengleichung und Übertragungsfunktion

### Die Frage

Ein Filter soll eine Flanke mit 12 oder 24 dB/Okt liefern, auf einem ARM-Prozessor
in Echtzeit laufen und bei Parameteränderungen nicht springen. Ein FIR-Filter
mit steiler Flanke bräuchte viele Taps; ein IIR-Filter zweiter Ordnung braucht
fünf Koeffizienten und zwei Zustände pro Kanal.

### Die Mathematik

Die Differenzengleichung eines Biquads lautet

```
y[n] = b0·x[n] + b1·x[n−1] + b2·x[n−2]
                 − a1·y[n−1] − a2·y[n−2]
```

Die Koeffizienten `a1`, `a2` stehen mit negativem Vorzeichen, weil sie aus dem
Nenner der Übertragungsfunktion kommen:

```
        b0 + b1·z⁻¹ + b2·z⁻²
H(z) = ─────────────────────
        1 + a1·z⁻¹ + a2·z⁻²
```

Im Code steht die transponierte Direktform II. Sie braucht nur zwei
Zustandsvariablen und fünf Multiplikationen pro Sample:

```cpp
const float y = b0*x + z1;
z1 = b1*x - a1*y + z2;
z2 = b2*x - a2*y;
```

Die Koeffizienten kommen aus dem RBJ Audio EQ Cookbook. Für einen Hochpass ist

```
w0    = 2π · f0 / fs
α     = sin(w0) / (2Q)

b0 = (1 + cos w0) / 2
b1 = −(1 + cos w0)
b2 = (1 + cos w0) / 2
a0 = 1 + α
a1 = −2 cos w0
a2 = 1 − α
```

Für `f0 = 24 Hz`, `fs = 44,1 kHz` und `Q = 0,7071` sind das:

```
w0 = 0,003419 rad/Sample
α  = 0,002418

b0 =  0,997585
b1 = −1,995170
b2 =  0,997585
a1 = −1,995164
a2 =  0,995176
```

Das sind gerechnete Werte, keine Messwerte. Sie stehen hier, damit der Code
nachprüfbar ist.

### Der Code

`framework/dsp/biquad.h` enthält sowohl die Koeffizienten als auch den
Sample-Prozessor. Der Hochpass ist eine statische Funktion:

```cpp
static BiquadCoeffs highpass (double sr, float hz, float q = 0.7071f)
{
    float w, c, s, alpha; common (sr, hz, q, w, c, s, alpha);
    return normalise ((1.0f + c) * 0.5f, -(1.0f + c), (1.0f + c) * 0.5f,
                      1.0f + alpha, -2.0f * c, 1.0f - alpha);
}
```

`common()` begrenzt die Frequenz auf `1 … 0,49·fs` und Q auf mindestens 0,025.
Damit können keine ungültigen Koeffizienten entstehen. `normalise()` teilt durch
`a0`, sodass im Prozessor `a0 = 1` gilt.

Der Kommentar im Header ist Teil des Vertrags: Koeffizienten werden pro Block
berechnet, nicht pro Sample. `sin`, `cos` und `pow` sind zu teuer für den
Sample-Takt.

### Die Messung

Die Bandanalyse in `tools/measure.py` nutzt 16 geometrische Bänder von 60 Hz bis
16 kHz, getrennt mit 24 dB/Okt-Filtern. Ein 997-Hz-Sinus landet im Band
**980–1390 Hz**; die Nachbarbänder liegen mindestens **6,4 dB** darunter, alle
fernen Bänder bei **≤ −17,8 dB**.

Das ist eine Messung der Analysemethode, nicht des Plugins. Sie zeigt aber, dass
eine Filterflanke dieser Steilheit ausreicht, um Bänder sauber zu trennen. Ohne
diese Prüfung wäre jede Bandaussage über einen Mix nur eine Behauptung.

### Fehler & Test

Der klassische Fehler ist, die Koeffizienten im Sample-Takt neu zu rechnen. Das
Ergebnis klingt zunächst richtig, kostet aber ein Vielfaches an CPU und macht
die Parameteränderung nicht glatter, sondern nur teurer. Der Code zieht die
Grenze richtig: `tilt.set()` und `mono.setFrequency()` laufen einmal pro Block,
`Biquad::process()` einmal pro Sample.

Der zugehörige Test ist der **Null-/Unity-Test** für die beiden Abschnitte: Tilt
0 dB und Mono 0 Hz müssen als Abschnitt die Identität bilden; die Differenz vor
und nach dem Abschnitt ist exakt 0. Im Gesamtplugin bleibt davor der feste
24-Hz-Hochpass aktiv, deshalb ist das kein Bypass-Test des ganzen Plugins.
Rechnerisch ist die Identität kein Zufall: Für `gain = 0` wird `A = 1`, und bei
beiden Shelves sind Zähler und Nenner identisch (`b0 = a0`, `b1 = a1`,
`b2 = a2`). Nach der Normalisierung ist `b0 = 1` und `b1 = a1`, `b2 = a2`; die
Übertragungsfunktion ist damit H(z) = 1. Jede Abweichung davon ist ein
versteckter Gain oder ein Vorzeichenfehler.

### Anwendung

- Biquads für statische oder blockweise geänderte Filter.
- Für audio-rate-modulierte Cutoffs stattdessen den SVF aus
  `framework/dsp/svf.h` nehmen; der Biquad ist dafür nicht gebaut.
- Koeffizienten immer normalisieren (`a0 = 1`), sonst hängt der Gain von der
  Frequenz ab.
- Bei sehr tiefen Frequenzen die Pole im Blick behalten; dazu Kapitel 3.

## 3. Pole, Nullstellen und die feste 24-Hz-Flanke

### Die Frage

Warum sitzt der Hochpass fest bei 24 Hz, und warum sind es zwei Biquads? Und
warum ist ein Filter, dessen Pol fast auf dem Einheitskreis liegt, trotzdem
stabil?

### Die Mathematik

Die Pole sind die Nullstellen des Nenners:

```
z² + a1·z + a2 = 0
```

Für das 24-Hz-Biquad liegen sie bei (gerechnet):

```
p = 0,997582 ± j·0,002412
|p| = 0,997585
Winkel = ±0,002418 rad
```

Der Betrag ist kleiner als 1, also ist der Filter stabil. Der Abstand zum
Einheitskreis ist

```
1 − |p| = 0,002415
```

Bei 44,1 kHz entspricht das einer Zeitkonstante von etwa

```
1 / (1 − |p|) ≈ 414 Samples ≈ 9,4 ms
```

So lange klingt der Filter nach einem Impuls nach. Die Marge ist klein, aber
ausreichend.

Die Stabilitätsbedingung für einen Biquad lässt sich auch ohne komplexe Rechnung
prüfen:

```
1 + a1 + a2 > 0
1 − a1 + a2 > 0
1 − a2 > 0
```

Bei 24 Hz ist `1 + a1 + a2` nur **1,2·10⁻⁵** von null entfernt. Der Filter liegt
also nah an der Grenze, aber auf der richtigen Seite. Genau deshalb ist die
fest eingestellte Frequenz sicherer als ein frei drehbarer Regler bis 0 Hz.

Die Nullstellen des Hochpasses liegen bei `z = 1` (doppelt). Ein Hochpass lässt
DC nicht durch; das Nullstellenpaar drückt die tiefen Frequenzen nach unten.

Zwei identische Biquads mit `Q = 0,7071` ergeben einen Linkwitz-Riley-Filter
4. Ordnung (LR4):

```
|H_LR4(f)| = |H_HP(f)|²
```

Die Dämpfungen des LR4 sind gerechnet: Bei 24 Hz dämpft ein Biquad
**−3,01 dB**, die Kaskade **−6,02 dB**. Die Flanke beträgt 24 dB/Okt. Bei 60 Hz
ist die Dämpfung des LR4 nur **−0,22 dB**, bei 20 Hz **−9,75 dB**. Der Bass bei
60 Hz bleibt also praktisch unangetastet, während der Subsonic-Bereich abfällt.

### Der Code

Der Hochpass wird in `prepare()` einmal gebaut und ist kein Parameter:

```cpp
const auto hp = BiquadCoeffs::highpass (sampleRate, 24.0f, 0.7071f);
hp1L.setCoeffs (hp); hp1R.setCoeffs (hp);
hp2L.setCoeffs (hp); hp2R.setCoeffs (hp);
```

Im Sample-Loop wird kaskadiert:

```cpp
l = hp2L.process (hp1L.process (l));
r = hp2R.process (hp1R.process (r));
```

Es gibt keinen Regler für diese Frequenz. Der einzige Regler im Master-Modus,
der gezielt unter einer Grenzfrequenz eingreift, ist `Mono`; er sitzt hinter dem
Hochpass und arbeitet auf der Side-Seite.

### Die Messung

In A9 und A10 läuft dieser Hochpass in jedem Master-Render mit. Die Exporte
zeigen die Kette als Ganzes:

| Analyse | Integrated | True Peak | PLR | Side − Mid |
|---|---|---|---|---|
| A9, CD Loud verteilt | **−7,8 LUFS** | **−1,30 dBTP** | **6,5** | **−32,0 dB** |
| A10, neue Kette | **−10,9 LUFS** | **−0,40 dBTP** | **10,5** | **−37,4 dB** |

Aus diesen Zahlen lässt sich der 24-Hz-Punkt nicht isolieren. Sie belegen, dass
die Kette mit dem festen Hochpass läuft, nicht die Flanke des Hochpasses allein.
Wer die Flanke messen will, braucht einen Sweep durch das Plugin und einen
Vergleich mit der gerechneten Antwort.

### Fehler & Test

Der Fehler, der hier lauert, ist ein Vorzeichenfehler in `a1` oder ein falsches
Q. Dann wandert der Pol aus dem Einheitskreis, und der Filter schwingt oder
läuft weg. Der Test ist eine Rechnung, keine Hörprobe:

1. Pole aus `a1`, `a2` berechnen.
2. `|p| < 1` für alle Pole verlangen.
3. Die Randbedingungen `1 ± a1 + a2 > 0` und `1 − a2 > 0` prüfen.

Bei 24 Hz ist die Marge klein genug, dass dieser Test nicht optional ist.
Zusätzlich verhindert `common()` mit der Q-Untergrenze 0,025 und der
Frequenzgrenze 0,49·fs, dass ungültige Eingaben überhaupt bis zum Koeffizienten
kommen.

### Anwendung

- Der 24-Hz-Hochpass bleibt fest. Er schützt den Clipper vor Subsonic-Energie
  und lässt 60 Hz praktisch unberührt.
- Wer mehr Tiefbass abschneiden will, nimmt dafür nicht den Hochpass, sondern
  den Mono-Regler oder den Mix.
- Wer den Hochpass tiefer legen will, muss die Polmarge neu rechnen; bei 10 Hz
  wird sie noch kleiner.

## 4. Tilt: zwei Shelves, halbe Spreizung

### Die Frage

Ein Regler soll den Mix dunkler oder heller machen, ohne nur eine schmale Kerbe
zu treffen. Ein einzelner Peak-Filter würde nur ein Band verbiegen. Gesucht ist
eine breite, monotone Neigung über den ganzen Hörbereich.

### Die Mathematik

Tilt besteht aus zwei Shelves:

- Low Shelf bei **200 Hz** mit **−g**,
- High Shelf bei **3 kHz** mit **+g**,
- mit `g = Tilt / 2`.

Die halbe Spreizung ist der entscheidende Punkt. Bei `Tilt = +6 dB` ist
`g = 3 dB`. Der Low Shelf senkt um 3 dB, der High Shelf hebt um 3 dB. Zwischen
den beiden Shelves liegt der Übergang; die Gesamtspreizung von 20 Hz bis 20 kHz
beträgt

```
(+g) − (−g) = 2g = Tilt
```

Also 6 dB, nicht 12 dB. Gerechnet für `Tilt = +6 dB`:

| Frequenz | Low Shelf | High Shelf | Summe |
|---|---|---|---|
| 20 Hz | −3,0 dB | 0,0 dB | **−3,0 dB** |
| 200 Hz | −1,5 dB | 0,0 dB | **−1,5 dB** |
| 3 kHz | 0,0 dB | +1,5 dB | **+1,5 dB** |
| 20 kHz | 0,0 dB | +3,0 dB | **+3,0 dB** |

Die 0-dB-Linie wird bei etwa 1 kHz gekreuzt (gerechnet: +0,03 dB). Beide Shelves
sind Minimum-Phase-Filter; sie erzeugen keine Pre-Ringing-Artefakte wie ein
linearphasiger FIR-Eingriff.

### Der Code

Die Klasse `Tilt` steht in `src/QMasterMpc.cpp` ab Zeile 365:

```cpp
void set (float db)
{
    const float g = db * 0.5f;
    const auto low  = BiquadCoeffs::lowShelf  (sr, 200.0f,  0.7071f, -g);
    const auto high = BiquadCoeffs::highShelf (sr, 3000.0f, 0.7071f,  g);
    loL.setCoeffs (low);  loR.setCoeffs (low);
    hiL.setCoeffs (high); hiR.setCoeffs (high);
}
```

Pro Kanal läuft erst der Low Shelf, dann der High Shelf:

```cpp
l = hiL.process (loL.process (l));
r = hiR.process (loR.process (r));
```

Beide Kanäle bekommen dieselben Koeffizienten. Der Tilt ist also ein
Stereo-Eingriff, kein M/S-Eingriff.

### Die Messung

A10 vergleicht die alte Vierer-Kette mit der neuen Kette. Die neue Kette ist
zwar lauter und dichter, aber die Mitten liegen relativ zum Sub **3–5,6 dB**
leiser (204 Hz bis 13 kHz). Bei „Under One Sun“ war die neue Kette noch **1–3 dB**
heller; die Wirkung ist materialabhängig.

Daraus folgt die Empfehlung für „Seele“: **Tilt +1,0 … +1,5 dB**, um die Mitten
zurückzuholen. Die Bandbalance ist gemessen; der Tilt-Wert ist eine Empfehlung
daraus. Der Tilt ersetzt allerdings keinen EQ im Mix; er verschiebt die gesamte
Neigung.

### Fehler & Test

Der häufigste Fehler ist, die volle Spreizung pro Shelf anzuwenden. Dann ist die
Neigung doppelt so stark wie angezeigt: Aus `Tilt +6 dB` werden Low Shelf −6 dB
und High Shelf +6 dB, also 12 dB Spreizung. Der Regler lügt um Faktor 2.

Der Test ist einfach und gehört in jede Tilt-Änderung: die Bandbalance bei
20 Hz und 20 kHz messen. Die Differenz muss dem Tilt-Wert entsprechen, nicht dem
Doppelten. Zusätzlich gilt der Null-/Unity-Test für die Tilt-Kaskade: Bei
`Tilt = 0` sind beide Shelves identisch, die Kaskade muss also bitgleich
durchlaufen.

### Anwendung

- **Tilt 0 dB** ist der neutrale Startpunkt; die Init- und CD-Programme stehen
  dort.
- Für einen mittigen, basslastigen Mix **Tilt +1,0 … +1,5 dB**.
- Tilt ist kein Mono-Ersatz. Ein Bass, der nur im Side-Kanal liegt, wird durch
  eine Neigung nicht mono-kompatibel.
- Nach jeder Tilt-Änderung die Bandbalance neu messen; das Ohr gewöhnt sich in
  wenigen Sekunden an die neue Neigung.

## 5. Der Mono Maker: Mid/Side, Phasenauslöschung und Korrelation

### Die Frage

Wie wird der Bass mono, ohne dass der gesamte Mix in die Mitte kollabiert? Ein
einfacher Mono-Schalter würde auch Höhen und Stimme monofizieren. Gesucht ist
ein Eingriff, der nur den tiefen Side-Anteil entfernt.

### Die Mathematik

Der Mono Maker arbeitet in der M/S-Basis aus Kapitel 1:

```
M = ½ · (L + R)
S = ½ · (L − R)
```

Nur `S` wird mit einem LR4-Hochpass bei der eingestellten Frequenz gefiltert.
Danach wird zurückgerechnet:

```
L = M + S_HP
R = M − S_HP
```

Für `S_HP ≈ 0` unterhalb der Grenzfrequenz ist dort `L = R = M`: Der Bass ist
mono, der Mid-Anteil unverändert. Der Hochpass auf Side hat bei 120 Hz folgende
Werte (gerechnet):

| Frequenz | Side-Dämpfung |
|---|---|
| 20 Hz | −62,3 dB |
| 40 Hz | −38,3 dB |
| 60 Hz | −24,6 dB |
| 120 Hz | **−6,02 dB** |
| 200 Hz | −1,06 dB |

Unter 120 Hz wird Side also stark bedämpft, oberhalb von 200 Hz praktisch nicht
mehr. Der Bass verliert seine Breite, die Höhen und die Stimme bleiben stereo.

Die Messgröße dafür ist **Side − Mid** in dB, gemessen unter 120 Hz:

```
Side−Mid = 10 · log10( E_Side / E_Mid )
```

Ein sehr negativer Wert heißt: Fast die ganze Tiefbassenergie liegt im
Mid-Kanal, der Bass ist mono. Ein Wert nahe 0 heißt: Der Bass ist breit und
mono-empfindlich.

### Der Code

`MonoMaker` steht in `src/QMasterMpc.cpp` ab Zeile 319. Der Kern ist kurz:

```cpp
void setFrequency (float hz)
{
    freq = std::max (0.0f, hz);
    if (freq <= 0.0f)
        return;
    const auto c = BiquadCoeffs::highpass (sr, freq, 0.7071f);
    hp1.setCoeffs (c);
    hp2.setCoeffs (c);
}

void process (float& l, float& r)
{
    if (freq <= 0.0f)
        return;
    const float mid  = 0.5f * (l + r);
    float side       = 0.5f * (l - r);
    side = hp2.process (hp1.process (side));
    l = mid + side;
    r = mid - side;
}
```

`Mono 0 Hz` ist ein echter Bypass: `process()` kehrt sofort zurück. Das ist für
den Null-/Unity-Test wichtig. Die beiden Biquads sind identisch; zusammen sind
sie ein LR4 mit 24 dB/Okt.

### Die Messung

Die Exporte zeigen, wie stark der Regler wirkt:

| Analyse | Einstellung | Side − Mid |
|---|---|---|
| A5, Rohmix | ohne Master | **−23,9 dB** |
| A5, Master | Mono 200 Hz | **−41,0 dB** |
| A9, CD Loud verteilt | Mono 120 Hz | **−32,0 dB** |
| A10, neue Kette | Mono 120 Hz | **−37,4 dB** |
| A10, alte Kette | ohne QMaster | **−29,8 dB** |

Der Sprung auf −41,0 dB bei Mono 200 ist kein zusätzlicher Gewinn, sondern zu
viel des Guten. Die Werte stammen allerdings aus verschiedenen Exporten mit
unterschiedlichen Ketten; sie zeigen die Größenordnung, nicht einen isolierten
Reglervergleich. Für einen echten A/B-Test müsste dasselbe Material zweimal
durch das Plugin, nur mit anderem Mono-Wert.

### Fehler & Test

**Mono 200 Hz war zu aggressiv.** In A5 fiel Side − Mid auf −41,0 dB; der Bereich
unter 200 Hz war mono. Das ist mehr, als die Monokompatibilität verlangt, und
kostet die Breite im tiefen Bass. 110–120 Hz reichen.

Der Test dafür ist zweistufig:

1. `scripts/release-check.sh` verlangt `Mid/Channels ≥ −3 dB` und
   `Side − Mid ≤ −3 dB`. Beide Werte sind bewusst locker; sie prüfen
   Kompatibilität, nicht Geschmack.
2. Der Vergleich zweier Mono-Einstellungen zeigt, ob der Regler über das Ziel
   hinausschießt. A5 (200 Hz: −41,0 dB) und A9 (120 Hz: −32,0 dB) liefern die
   Größenordnung; für einen kontrollierten A/B-Test müsste dasselbe Material
   zweimal gerendert werden, nur mit anderem Mono-Wert.

Der Antiphase-Test aus Kapitel 1 bleibt der Grundtest: Er zeigt, ob der
Analysator Auslöschung überhaupt erkennt. Der Release-Check kann nur so gut sein
wie diese Messung.

### Anwendung

- **Mono 110–120 Hz** ist der Standard; die Programme `Init`, `CD Loud` und
  `CD Dynamic` stehen auf 120 Hz.
- Ein absichtlich breiter Bass: Mono tiefer stellen, aber dann auf einem echten
  Monosystem gegenhören.
- `Mono 0` ist Bypass. Ohne Mono-Check ist der Bass nicht garantiert
  mono-kompatibel.
- Nach dem Setzen von Mono immer Side − Mid messen; der Regler ist keine
  Geschmacksinstanz, sondern eine Kompatibilitätsversicherung.

## 6. Fehler, Tests und die Anwendung

### Die Frage

Welche Fehler sind in diesem Bereich wirklich passiert, wodurch wurden sie
gefunden, und welcher Test verhindert sie heute? Drei Fehler aus diesem Bereich
stehen im Projekt: der zu aggressive Mono-Wert, der Downmix als Pegelmesser und
die Verwechslung von RMS und LUFS.

### Die Mathematik

**Downmix.** `ffmpeg -ac 1` addiert die Kanäle. Aus einem Stereo-Peak von
**−1,03 dBFS** wurde im Downmix **+1,25 dBFS**. Das ist keine Clipping-Stelle im
Signal, sondern die Summe zweier Kanäle. Wer den Downmix als Datei-Peak liest,
misst die Addition, nicht die Aufnahme.

**RMS gegen LUFS.** Ein Stereo-Signal, das nur links anliegt, hat über alle
Samples einen RMS von **−12,04 dBFS**, aber eine Loudness von **−9,0 LUFS**. Die
mittlere Leistung halbiert sich, weil die Hälfte der Samples null ist; der RMS
fällt dadurch um 3,01 dB. Die Loudness summiert die Kanalleistungen; der stille
Kanal trägt nichts bei. Zwei Metriken, zwei verschiedene Fragen.

**Mono 200 Hz.** Side − Mid fällt auf **−41,0 dB**. Der Bereich unter 200 Hz wird
mono. Das ist mathematisch korrekt und klanglich zu viel.

### Der Code

Die Messung sitzt in `tools/measure.py`:

- `mono_stats()` filtert mit `lowpass=f=120:poles=2,lowpass=f=120:poles=2`, also
  einem LR4 bei 120 Hz.
- Danach berechnet es `e_mid`, `e_side`, `e_l`, `e_r` und `cross`.
- `side_minus_mid_db` ist `10·log10(e_side / e_mid)`.
- `correlation` ist `cross / √(e_l · e_r)`.

Die Abnahme sitzt in `scripts/release-check.sh`:

```python
add("Mono-Phasen", mid is not None and mid >= -3.0, ...)
add("Mono-Bass",   side is not None and side <= -3.0, ...)
```

Der Check misst den Stereo-Peak, nie einen Downmix. Das ist keine Konvention,
sondern die Lehre aus dem Fehler.

### Die Messung

| Prüfung | Wert | Einordnung |
|---|---|---|
| A2, Anti-Phase 60 Hz | Korrelation **−1,000**, Mid **null** | Auslöschung erkannt |
| A2, nur links | RMS **−12,04 dBFS**, LUFS **−9,0** | RMS ≠ Loudness |
| A5, Mono 200 Hz | Side − Mid **−41,0 dB** | zu aggressiv |
| A9, Mono 120 Hz | Side − Mid **−32,0 dB** | im Ziel |
| A10, Mono 120 Hz | Side − Mid **−37,4 dB** | im Ziel |
| Downmix | **−1,03 dBFS** stereo → **+1,25 dBFS** mono | Summe, kein Signal-Peak |

Die Werte stammen aus A2, A5, A9 und A10; der Downmix aus dem Report. Sie sind
nicht nachträglich gerundet; die Tabellen nennen dieselben Zahlen.

### Fehler & Test

**Fehler 1: Mono 200 Hz.** Gefunden in A5, als Side − Mid auf −41,0 dB fiel.
Ursache: Der Regler wurde als „mehr ist besser“ verstanden. Test: Der Vergleich
mit 120 Hz (A9: −32,0 dB; A10: −37,4 dB) und der Release-Check, der nur
Kompatibilität verlangt. Die Lehre: Ein numerisch bestandener Check kann
klanglich zu weit gehen.

**Fehler 2: Der Downmix als Pegelmesser.** Ein Stereo-Peak von −1,03 dBFS
erschien mit `ffmpeg -ac 1` als +1,25 dBFS. Ursache: Der Downmix addiert die
Kanäle. Test: Es wird immer der Stereo-Peak gemessen; der Downmix ist nur eine
Wiedergabe-Simulation, kein Datei-Messwert. Die Lehre: Eine Zahl ohne ihre
Bezugsgröße ist keine Messung.

**Fehler 3: RMS mit LUFS verwechseln.** Der Links-only-Fall zeigt RMS −12,04
und LUFS −9,0. Ursache: RMS mittelt über alle Samples, Loudness über die
Kanalleistungen. Test: Beide Werte getrennt ausgeben und bei einseitigen
Signalen die Differenz erklären. Die Lehre: Zwei Metriken, die fast gleich
heißen, beantworten nicht dieselbe Frage.

Dazu kommt der **Antiphase-Test** als Wächter: Korrelation −1,000 und Mid null.
Er beweist, dass der Mono-Check Auslöschung sieht. Ohne ihn wäre der
Release-Check ein Blindflug.

### Anwendung

Für einen Rap-Master mit diesem Material:

| Regler | Wert | Begründung |
|---|---|---|
| 24-Hz-Hochpass | **fest** | kein Parameter, schützt vor Subsonic |
| Tilt | **0 dB** (Start) | neutral; +1,0 … +1,5 dB nur bei Mitten-Defizit |
| Mono | **110–120 Hz** | A9/A10: −32,0 / −37,4 dB, im Ziel |
| Mono bei breitem Bass | **tiefer** | Breite ist eine Entscheidung, kein Messfehler |
| Peak-Messung | **stereo** | nie `ffmpeg -ac 1` als Datei-Peak |

Die eigentliche Lehre: Der Bass verschwindet auf dem Handy nicht, weil das Handy
zu klein ist, sondern weil er im Side-Kanal lag. Der Mono Maker macht ihn
mono-kompatibel, indem er den Side-Bass unter 120 Hz entfernt. Wer diesen
Eingriff versteht, stellt ihn einmal richtig ein und misst danach — statt ihn
nach Gehör immer weiter aufzudrehen.
