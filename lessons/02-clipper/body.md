## Worum es geht

Ein Clipper ist ein Versprechen: mehr Lautheit bei gleichem Deckel. Die Rechnung
geht auf, weil er Spitzen kappt, ohne den Dauerpegel zu senken. Die Rechnung hat
einen Preis: Aus jeder gekappten Spitze werden Harmonische, und aus Harmonischen
oberhalb der Nyquist-Frequenz werden Aliase.

Diese Lektion folgt diesem Preis vom ersten Sample über das Knie bei 0,96 bis
zur FFT. Alle Zahlen stammen aus den Analysen A2–A7, A9 und A10, aus dem Code in
`src/QMasterMpc.cpp` und aus dem Test in `tests/alias-check.py`.

Sieben Kapitel, jedes in sechs Schritten:

1. **Die Frage** — das Problem, das wirklich anlag.
2. **Die Mathematik** — die Herleitung mit den Zahlen aus dem Projekt.
3. **Der Code** — die Stelle im Repo, die daraus wurde.
4. **Die Messung** — was der Test zeigt.
5. **Fehler & Test** — was schiefging und welcher Test es heute verhindert.
6. **Die Anwendung** — welches Programm, welcher Regler, welche Zahl.

## 1. Warum laut oft billig klingt

### Die Frage

Der Rohmix von „Under One Sun“ liegt bei **−18,3 LUFS** und einem **PLR von
17,7** (A5). Das Ziel ist **−8 ± 1 LUFS**, **True Peak ≤ −1,0 dBTP** und ein
**PLR von 6–8**. Dazwischen liegen rund **10 dB Spitzenkontrolle** (A6).

Diese 10 dB kann man auf zwei Arten holen: den Pegel anheben, bis die Spitzen
abgeschnitten werden, oder die Spitzen aktiv herunterregeln. Der Clipper macht
das erste. Er ist damit der ehrlichste Teil der Kette — und der, der am
schnellsten hörbar wird.

„Billig“ meint dabei nicht „laut“. Es meint die Signatur der Methode: flache
Dachlinien, ein dichter Kranz ungerader Harmonischer, gefaltete Anteile oberhalb
von 22 050 Hz und ein Mittelband, das relativ zum Sub 3–5,6 dB verliert.

Dass der Deckel nicht reicht, zeigt schon der Test-Loop aus A2: Er ist auf
**−1,01 dBFS Sample Peak** ausgesteuert und misst trotzdem **+0,90 dBTP**. Das
sind **1,91 dB** Überschreitung zwischen den Samples. Ein Clipper, der nur auf
Sample-Peak schaut, wäre an dieser Stelle blind.

### Die Mathematik

Der PLR ist die Differenz zwischen True Peak und integrierter Loudness:

```
PLR = TP − LUFS
```

Aus 17,7 sollen 6 bis 8 werden:

```
17,7 − 6  = 11,7 dB
17,7 − 8  =  9,7 dB
```

Die Dokumentation rundet das auf **rund 10 dB** (A6). Diese 10 dB müssen aus
Spitzenkontrolle kommen, nicht aus einem leiser gedrehten Master.

Der Clipper nimmt dafür Gain vor einer festen Decke. Der Gain ist nicht der
Prozentwert selbst, sondern eine dB-Zahl:

```
drive_dB = Clip[%] · 0,12
drive    = 10^(drive_dB / 20)
```

Bei **Clip 55 %** sind das **6,6 dB** und ein Faktor **2,14**. Bei **Clip 100 %**
sind es **12,0 dB** und **3,98**. Dieselbe Spitze, die vorher bei 0,5 lag, liegt
danach bei 1,07 und wird gekappt.

### Der Code

Die Umrechnung steht in `src/QMasterMpc.cpp`:

```cpp
static float clipToDb (float percent)
{
    return clamp (percent, 0.0f, 100.0f) * 0.12f;   // 0..12 dB drive
}
```

Die Decke, an der gekappt wird, ist keine 1,0, sondern **0,96**:

```cpp
constexpr float kClipKnee = 0.96f;       // -0.35 dBFS
```

Beide Modi — Master und Bus — durchlaufen dieselbe Funktion. Der Unterschied
liegt nur davor: Im Master folgen Trim, Hochpass, Tilt und Mono-Maker; im Bus
folgt der Transient-Shaper. Danach wird in beiden Fällen bei 2× geclippt.

### Die Messung

Der Loop und die Kette im Vergleich:

| Station | Integrated | True Peak | PLR |
|---|---|---|---|
| Loop (A2) | −11,0 LUFS | +0,90 dBTP | 11,9 |
| Loop durch „CD Loud“ (A4) | **−8,5 LUFS** | **−1,10 dBTP** | **7,4** |
| Rohmix (A5) | −18,3 LUFS | −0,6 dBTP | 17,7 |
| Rohmix, Trim +8 / Clip 55 (A6) | −8,1 LUFS | −1,40 dBTP | 6,70 |

Der Loop wird **2,5 dB lauter**, der True Peak fällt um **2,0 dB**, der PLR
sinkt um **4,5 dB**. Genau das ist die gekaufte Verdichtung: Der Dauerpegel
steigt, die Spitze fällt, die Differenz dazwischen verschwindet.

### Fehler & Test

Die erste große Fehldeutung des Projekts passt genau hierher: Alle alten
Exporte peakten exakt bei **−0,09 dBFS**. Daraus wurde geschlossen, die MPC
normalisiere. Sie normalisiert aber nicht — der Limiter der alten Vierer-Kette
saß bei dieser Decke.

Der Gegenbeweis war nicht der Peak, sondern der PLR: **7,7 bzw. 8,2** bei den
Exporten gegen **17,7** beim Rohmix. Eine reine Pegelanhebung verschiebt True Peak
und Loudness gemeinsam und lässt den PLR unverändert. Zusätzlich lagen **309 bzw.
261 Samples** auf 0,99 — eine Limiter-Decke, kein einzelner normalisierter
Spitzenwert.

Die Regel daraus: **Eine Zahl ist kein Ursachenbeweis.** Beim Clipper heißt das:
Der Pegel allein sagt nichts über die Klangänderung. Es braucht mindestens eine
zweite, unabhängige Metrik — hier PLR, Sample-Verteilung und später das
Spektrum.

### Die Anwendung

Der Clip-Regler ist kein Lautstärkeregler. Er entscheidet, wie viel Spitze in
Dichte umgewandelt wird:

- **CD Loud: Clip 55** — 6,6 dB Treiber, der gemessene Kompromiss bei
  −8,1 LUFS und PLR 6,70.
- **Bus Drums: Clip 45** — 5,4 dB Treiber, verteilte Reduction auf dem Drum-Bus.
- **Clip 0** — kein Treiber, aber die Kette ist deshalb nicht automatisch
  sauber; der Limiter arbeitet weiter.

Wenn der PLR unter 6 fällt, war es zu viel. Wenn er über 8 bleibt, war es zu
wenig oder der Eingang war zu leise.

## 2. Das Knie bei 0,96

### Die Frage

Warum clippt QMaster bei 0,96 und nicht bei 1,0? Und warum ist die Kennlinie
kein hartes `min(x, 1)`, sondern ein `tanh`?

Die Antwort ist zweiteilig: 0,96 lässt **0,35 dB** Reserve bis zur vollen
Aussteuerung, und der weiche Übergang verhindert eine Ecke, die als Klick und
als breites Harmonischen-Spektrum messbar wäre.

### Die Mathematik

Die Transferfunktion ist stückweise definiert. Mit `k = 0,96` gilt:

```
f(x) = x                                              für |x| ≤ k
f(x) = sign(x) · ( k + (1−k) · tanh( (|x|−k)/(1−k) ) ) für |x| > k
```

Drei Eigenschaften folgen direkt daraus:

1. **Stetigkeit bei x = k.** Beide Zweige liefern `k`.
2. **Stetige Ableitung.** Links ist die Ableitung 1. Rechts ist sie
   `(1−k) · (1/(1−k)) · sech²(0) = 1`. Es gibt also keinen Knick erster
   Ordnung, sondern einen weichen Übergang.
3. **Feste Decke.** Für `x → ∞` geht `tanh` gegen 1, der Ausgang gegen
   `k + (1−k) = 1,0`. Kein Sample kann über 0 dBFS hinaus.

Das Knie liegt bei

```
20 · log10(0,96) = −0,35 dBFS
```

also **0,35 dB unter Vollaussteuerung**. Ein Signal, das leiser ist, wird
linear durchgelassen. Erst darüber beginnt die Sättigung.

Der Treiber davor ist der eigentliche Regler:

| Clip | Treiber | Gain |
|---|---|---|
| 0 % | 0,0 dB | 1,00 |
| 30 % | 3,6 dB | 1,51 |
| 45 % | 5,4 dB | 1,86 |
| 55 % | 6,6 dB | 2,14 |
| 100 % | 12,0 dB | 3,98 |

Der `tanh` wird nicht als Bibliotheksfunktion pro Sample aufgerufen. Der Code
nutzt eine Padé-Approximation:

```
fastTanh(x) = x · (135135 + 17325x² + 378x⁴ + x⁶)
            / (135135 + 62370x² + 3150x⁴ + 28x⁶)
```

Sie ist ungerade, hat im Bereich **−3 … 3** einen Fehler von etwa **1 · 10⁻³**
und klemmt außerhalb von **±4,97** auf **±1**. Auf einem ARM-Prozessor ist das
deutlich billiger als `std::tanh`, und für ein Audiosignal reicht die Genauigkeit.

Weil die Funktion ungerade ist, erzeugt sie bei einem Sinus **nur ungerade
Harmonische**. Ein symmetrischer Clipper macht keine geraden Vielfachen; die
kommen erst durch Asymmetrie im Material oder durch eine gleichgerichtete Stufe
dazu.

### Der Code

`src/QMasterMpc.cpp`, Zeilen 122–129:

```cpp
inline float softClipKnee (float x, float knee)
{
    const float a = std::fabs (x);
    if (a <= knee)
        return x;
    const float y = knee + (1.0f - knee) * fastTanh ((a - knee) / (1.0f - knee));
    return x < 0.0f ? -y : y;
}
```

Die Vorzeichenbehandlung ist der Grund für die ungeraden Harmonischen: Für
`−x` kommt exakt `−f(x)` heraus. Es gibt keinen Offset, keine Diode, keine
Gleichrichtung.

### Die Messung

Bei **Clip 100 %** — also 12 dB Treiber — misst der Alias-Test einen Grundton
von **−3,2 dBFS** (A7). Die Spitze ist längst an der Decke; der Grundton bleibt
endlich, weil die Sättigung ihn ebenfalls zusammendrückt.

Der Unterschied zwischen „kein Treiber“ und „voller Treiber“ ist im Spektrum
messbar:

| Einstellung | stärkster Nicht-Harmonischer |
|---|---|
| Clip 0 % | **−120,0 dBc** |
| Clip 100 % | **−105,4 dBc** bei 19 175 Hz |

Bei Clip 0 bleibt das Testsignal unter dem Knie; die FFT sieht praktisch nichts.
Bei Clip 100 arbeitet die Funktion oberhalb des Knies, und der stärkste
gefaltete Anteil steigt um **14,6 dB**.

Die Transferfunktion begrenzt das Sample auf 1,0. Sie begrenzt nicht den
Verlauf **zwischen** den Samples. Deshalb bleibt der True Peak eine Aufgabe des
Limiters — und deshalb steht in A2 der Loop bei −1,01 dBFS Sample Peak und
+0,90 dBTP.

### Fehler & Test

Ein einzelner Testpunkt beweist keine Kennlinie. Wer nur `x = 1,0` einsetzt,
sieht `1,0` herauskommen und hält die Funktion für einen harten Clip. Das Knie
bei 0,96 ist dann unsichtbar.

Der Fehler, den der Test verhindert, ist ein **Sprung bei 0,96**: Er würde bei
jedem Signal oberhalb des Knies eine breite Harmonischen-Wolke erzeugen und bei
Modulation als Klicken hörbar. Die stetige Form ist die eine Hälfte des Tests;
die andere ist die FFT. Bei Clip 0 muss sie **−120,0 dBc** zeigen. Zeigt sie
mehr, ist das Knie falsch oder die Messung.

### Die Anwendung

Der Regler beginnt dort zu arbeiten, wo das Signal 0,96 erreicht. Ein Bus, der
nur bis −10 dBFS ausgesteuert ist, wird von Clip 55 kaum berührt. Genau das ist
in A5 passiert: **Clip 41** im Bus-Modus hat auf dem leise ankommenden Master
„fast nichts“ getan, der PLR blieb bei 17,7.

Die Praxisregel: erst Trim, dann Clip. Trim bringt das Material an das Knie
heran; Clip entscheidet, wie viel darüber hinausgeht. Clip 100 % mit 12 dB ist
kein Reparaturwerkzeug für einen zu leisen Mix, sondern eine massive
Übersteuerung.

## 3. Warum Clipping nach Höhen klingt

### Die Frage

Ein Clipper verändert nicht nur die Hüllkurve, sondern das Spektrum. Warum
klingt ein stark geclippter 997-Hz-Ton nach Höhen, obwohl die Grundfrequenz
dieselbe bleibt? Und warum ist ausgerechnet die 25. Harmonische gefährlich?

### Die Mathematik

Ein periodisches Signal lässt sich als Summe seiner Harmonischen schreiben:

```
x(t) = Σ A_k · sin(2π · k · f0 · t + φ_k)
```

Für einen symmetrisch geclippten Sinus sind nur **ungerade** Vielfache `k = 1,
3, 5, …` besetzt. Ihre Amplituden fallen bei einem harten Rechteck mit **1/k**;
ein weicher Clip rundet die Ecken und lässt die hohen Ordnungen schneller
abfallen.

Bei **997 Hz** liegen die ersten ungeraden Harmonischen bei:

| k | Frequenz |
|---|---|
| 1 | 997 Hz |
| 3 | 2 991 Hz |
| 5 | 4 985 Hz |
| 7 | 6 979 Hz |
| 25 | **24 925 Hz** |

Die 25. ist ungerade und damit im erzeugten Spektrum. Sie liegt aber über der
Nyquist-Frequenz von **22 050 Hz**. Was oberhalb liegt, verschwindet nicht; es
faltet sich zurück:

```
44 100 − 24 925 = 19 175 Hz
```

Genau diese Frequenz meldet der Alias-Test als stärksten Nicht-Harmonischen
(A3, A7). Das ist kein Zufall und kein Rauschen, sondern die gefaltete 25.
Harmonische.

### Der Code

Die Symmetrie steckt in einer Zeile:

```cpp
return x < 0.0f ? -y : y;
```

Für positive und negative Eingänge wird derselbe Betrag verarbeitet. Damit ist
`f(−x) = −f(x)`, und die Fourier-Reihe enthält nur ungerade Terme. Der
`fastTanh` ist ebenfalls ungerade; auch er bringt keine geraden Vielfachen ins
Signal.

Der Test weiß das und schließt erwartete Harmonische aus. In
`tests/alias-check.py` werden Frequenzen innerhalb von **15 Hz** um ein
Vielfaches von 997 Hz, das unter Nyquist liegt, nicht als Alias gezählt. Gesucht
wird nur, was **nicht** dorthin gehört.

### Die Messung

A7 zeigt beide Seiten desselben Signals:

- Der Grundton liegt bei **−3,2 dBFS**.
- Der stärkste echte Alias liegt bei **−105,4 dBc** und **19 175 Hz**.

A3 bestätigt den Zusammenhang mit dem Treiber:

| Clip | Alias |
|---|---|
| 0 % | −120,0 dBc |
| 100 % | −105,4 dBc bei 19 175 Hz |

**14,6 dB** mehr Alias, wenn der Treiber von 0 auf 12 dB geht. Die Harmonischen
wachsen also mit dem Drive — aber nicht linear, weil die Kennlinie mit
zunehmender Übersteuerung immer flacher wird.

### Fehler & Test

Die erste „Alias“-Messung sah bei **1229 Hz** einen Pegel von **−25,3 dBFS**
(A7). Das war kein Alias. 1229 Hz ist **997 + 232 Hz**, also kein Vielfaches des
Grundtons. Ein Bandpass zweiter Ordnung mit Q = 30 dämpft einen 232 Hz
entfernten Ton nur um etwa **22 dB**. Aus dem Grundton bei −3,2 dBFS wurde so
eine scheinbare Energie bei −25,3 dBFS.

Der Test, der das heute verhindert, ist die FFT mit Harmonischen-Ausschluss. Ein
echter Alias muss **nicht-harmonisch** sein und mit dem Drive wachsen. Die
ausführliche Geschichte steht in Kapitel 5.

### Die Anwendung

Wenn Becken oder Stimmen mit steigendem Clip hart werden, ist das kein Fall für
mehr Tilt. Der Tilt hebt die Höhen an, aber er entfernt die Harmonischen nicht.
Die Beobachtung aus A10 passt dazu: Beim starken Master-Clipping lagen die
Mitten relativ zum Sub **3–5,6 dB** tiefer (204 Hz bis 13 kHz). Der Sub passiert,
die Mittenspitzen werden gekappt.

Praxis: **Clip 55** ist der Startsound für dichtes Material. Bei hellem oder
bereits komprimiertem Material lieber **Clip 45** und den Pegel über den Bus
holen, statt die Höhen mit dem Clipper zu verbrennen.

## 4. Nyquist, 2× und der 31-Tap-Halfband

### Die Frage

Warum clippt QMaster nicht einfach bei 44,1 kHz? Was passiert mit den
Harmonischen oberhalb von 22 050 Hz, und warum reicht ein 31-Tap-Filter?

### Die Mathematik

Bei **44 100 Hz** Abtastrate liegt die Nyquist-Frequenz bei **22 050 Hz**. Ein
Signalanteil oberhalb davon kann nicht gespeichert werden. Er erscheint
stattdessen als gefaltete Frequenz:

```
f_alias = |44 100 − f|     für 22 050 < f < 44 100
```

Für die 25. Harmonische bei **24 925 Hz**:

```
44 100 − 24 925 = 19 175 Hz
```

Bei **2× Oversampling** läuft der Clipper bei **88 200 Hz**. Die Nyquist-Frequenz
liegt dort bei **44 100 Hz**, die 25. Harmonische passt also in den Bereich. Nach
dem Clipping muss sie entfernt werden, **bevor** wieder auf 44,1 kHz dezimiert
wird. Genau das macht der Halfband-Filter.

Ein Halfband-Filter hat seine Grenzfrequenz bei einem Viertel der aktuellen
Abtastrate — bei 88,2 kHz also bei **22 050 Hz**. Die 31 Taps bestimmen, wie
steil der Übergang ist und wie weit das Stopband dämpft. Der Code baut die
Koeffizienten als gefensterte Sinc-Funktion:

```cpp
const double sinc = std::fabs (x) < 1.0e-9 ? 1.0
                 : std::sin (kPi * 0.5 * x) / (kPi * 0.5 * x);
const double w = 0.42
               - 0.5 * std::cos (2.0 * kPi * n / (N - 1))
               + 0.08 * std::cos (4.0 * kPi * n / (N - 1));
h[n] = 0.5 * sinc * w;
```

Anschließend wird die Summe der Koeffizienten auf 1 normiert. Der Faktor 0,5
im Sinc-Argument setzt die Grenze auf die halbe 2×-Bandbreite; das Fenster
(Blackman-ähnlich) senkt die Nebenkeulen.

Die Latenz der ganzen Kette ist **102 Samples**, gemessen und gemeldet (A3).
Davon stammen **88 Samples** aus dem Lookahead des Limiters; der Rest ist das
Up-/Down-Paar. Im Bus-Modus wird dieselbe Latenz als Delay-Pad ausgeglichen.

### Der Code

`src/QMasterMpc.cpp`, Zeilen 47–117, in Auszügen:

```cpp
class Oversampler2x
{
public:
    static constexpr int N = 31;
    static constexpr int Ring = 64;

    void processUp (float x, float& u0, float& u1)
    {
        up[write] = x;
        up[(write + 1) & (Ring - 1)] = 0.0f;
        // 31-Tap-Faltung, danach * 2 für den Null-Einschub
    }

    float processDown (float v0, float v1)
    {
        // 31-Tap-Faltung, danach write += 2 (Dezimierung)
    }
};
```

Der Null-Einschub zwischen zwei Eingangssamples und der Faktor 2 sind der
eigentliche Upsampler. `processDown` faltet über die beiden 2×-Samples und
behält nur jedes zweite Ergebnis — die Dezimierung.

### Die Messung

A3 misst die Latenz in beiden Modi mit **102 Samples**; gemeldet werden ebenfalls
102. Der Alias-Test misst:

| Prüfung | Ergebnis |
|---|---|
| Latenz Master | 102 Samples gemessen, 102 gemeldet |
| Latenz Bus | 102 Samples, identisch |
| Alias Clip 0 % | −120,0 dBc |
| Alias Clip 100 % | −105,4 dBc bei 19 175 Hz |

Die FFT in A7 arbeitet mit **65 536 Punkten**, einem **Hann-Fenster** und einer
Bin-Breite von **0,67 Hz**. Damit liegt der stärkste echte Alias bei
**−105,4 dBc** — deutlich unter dem Testgate von **−60 dBc**.

### Fehler & Test

Der Fehler saß nicht im Oversampler, sondern in der Messung davor. Die erste
Alias-Prüfung nutzte einen Bandpass mit Q = 30 und `astats`. Sie zeigte bei
**1229 Hz** einen „Alias“ von **−25,3 dBFS** — und dieser Wert blieb gleich,
egal ob **15 oder 31 Taps** im Oversampler steckten.

Ein Ergebnis, das sich nicht ändert, wenn man das System ändert, ist
verdächtig. Die FFT zeigte später: Der echte Alias liegt bei **−105,4 dBc**, und
die −25,3 dBFS waren die Leckage des Messfilters. Der Test, der das heute
verhindert, ist `tests/alias-check.py` mit FFT und Harmonischen-Ausschluss.

### Die Anwendung

Das 2×-Oversampling ist fest verdrahtet. Ein 4×-Schalter würde die Latenz
ändern und den festen Latenzvertrag brechen; deshalb gibt es ihn nicht. Der
Preis ist CPU: Auf dem Desktop läuft **1× Master + 5× Bus** bei **0,32 %**
(REPORT). Die Gerätemessung über 10 Minuten steht noch aus.

Für die Praxis heißt das: Aliasing ist keine Geschmacksfrage und kein
„analoges Mojo“. Es ist eine messbare Faltung. Wer sie beurteilen will, rendert
und rechnet eine FFT — nicht ein Bandpass-Skript.

## 5. Der FFT-Test

### Die Frage

Wie beweist man, dass ein Peak im Spektrum ein Alias ist und nicht der eigene
Messfilter? Die naheliegende Antwort — ein Bandpass auf die verdächtige
Frequenz — ist genau die falsche.

### Die Mathematik

Die diskrete Fourier-Transformation zerlegt **N** Samples in **N** Bins:

```
X[k] = Σ x[n] · e^(−i·2π·k·n/N)
```

Die Bin-Breite ist `fs / N`. Bei **44 100 Hz** und **65 536 Punkten**:

```
44 100 / 65 536 = 0,6729 Hz ≈ 0,67 Hz
```

Vor der FFT wird ein **Hann-Fenster** angelegt:

```
w[n] = 0,5 − 0,5 · cos(2π·n/(N−1))
```

Das Fenster senkt die Leckage eines starken Tons in die Nachbarbins. Ohne Fenster
würde der 997-Hz-Grundton den ganzen Bereich um sich herum anheben, und ein
kleiner Alias wäre nicht mehr von seinen Nebenkeulen zu unterscheiden.

Ein Bandpass zweiter Ordnung mit **Q = 30** hat dagegen eine breite Flanke. Bei
**232 Hz** Abstand dämpft er nur um etwa **22 dB**. Aus dem Grundton bei
**−3,2 dBFS** wird damit:

```
−3,2 dBFS − 22 dB = −25,2 dBFS
```

Gemessen wurden **−25,3 dBFS**. Die Differenz ist Rundung, nicht DSP.

### Der Code

`tests/alias-check.py` macht vier Dinge:

```python
N = 1 << 16                       # 65 536 Punkte
block[i] *= 0.5 - 0.5 * math.cos(2.0 * math.pi * i / (N - 1))   # Hann
harmonics = {round(tone * k, 1) for k in range(1, int(sr / 2 / tone) + 3)}
# Alias-Suche: k = 2..120, falten, Harmonische im 15-Hz-Abstand überspringen
ok = rel <= -60.0                # Gate: −60 dBc
```

Der Test rendert einen **997-Hz-Ton** durch das Plugin, schneidet ab 0,2 s ein
Fenster von 65 536 Samples heraus, fenstert und sucht den stärksten
nicht-harmonischen Anteil. Das Ergebnis wird relativ zum Grundton in **dBc**
ausgegeben.

### Die Messung

A7 ist der vollständige Vergleich:

| Methode | Ergebnis |
|---|---|
| Bandpass Q = 30, `astats` | −25,3 dBFS bei 1229 Hz |
| FFT, 65 536 Punkte, Hann | **−105,4 dBc bei 19 175 Hz** |

Die Bandpass-Messung änderte sich nicht, als der Oversampler von **15 auf 31
Taps** geändert wurde. Die FFT zeigte von Anfang an einen Wert, der um ein
Vielfaches unter dem angeblichen Alias lag. Der Unterschied zwischen beiden
Messungen ist die Messmethode, nicht das Signal.

### Fehler & Test

Der Ablauf war:

1. Bandpass auf 1229 Hz, Pegel **−25,3 dBFS**. Das sah nach einem ernsten
   Alias aus.
2. Der Wert blieb bei **15 und 31 Taps** identisch. Das System änderte sich, das
   Ergebnis nicht.
3. Verdacht: Messfehler. Die FFT zeigte **−105,4 dBc** bei 19 175 Hz.
4. Erklärung: 1229 Hz ist **997 + 232 Hz**; der Bandpass dämpft den 232 Hz
   entfernten Grundton nur um **22 dB**.

Die Regel steht seitdem im Fehlerkatalog: **Ändert sich ein Ergebnis nicht,
wenn man das System ändert, ist die Messung verdächtig.** Der Test, der es
heute verhindert, ist die FFT mit **65 536 Punkten**, **Hann-Fenster**,
**Harmonischen-Ausschluss** und dem Gate **−60 dBc**.

### Die Anwendung

Der Test läuft mit einem Befehl:

```bash
python3 tests/alias-check.py 997 --clip 1.0
```

Die Zeile „Relative“ muss **≤ −60,0 dBc** sein. Wer stattdessen einen Bandpass
benutzt, muss mindestens die Q-Änderung prüfen: Ändert sich der „Alias“ mit Q
oder mit der Filterlänge, war es Leckage. Für Musik nimmt man dieselbe FFT auf
dem Export; gesucht wird, was nicht harmonisch zum Material gehört.

## 6. Loop und echte Exporte

### Die Frage

Funktioniert die Rechnung auf dem Loop und auf echten Exporten — und was kostet
sie dort? Ein Clipper, der im Synthetik-Test sauber ist, kann auf einem Mix
immer noch die Mitten fressen.

### Die Mathematik

Die Differenzen lassen sich direkt aus den Tabellen rechnen.

Loop durch „CD Loud“ (A4):

```
Loudness:  −8,5 − (−11,0) = +2,5 dB
True Peak: −1,10 − 0,90   = −2,0 dB
PLR:        7,4 − 11,9    = −4,5 dB
```

Verteilte Kette (A9) gegen den einzelnen CD-Loud-Master (A6):

```
Loudness:  −7,8 − (−8,1) = +0,3 dB
PLR:        6,5 − 6,7    = −0,2 dB
```

„Seele“ (A10), neue gegen alte Kette:

```
Loudness:  −10,9 − (−12,5) = +1,6 dB
PLR:        10,5 − 13,9    = −3,4 dB
True Peak:  −0,40 − 1,40   = −1,8 dB
```

Der Zielkorridor ist **−8 ± 1 LUFS**, **TP ≤ −1,0 dBTP**, **PLR 6–8**. A9
trifft ihn, A10 nicht: −10,9 LUFS, 10,5 PLR und −0,4 dBTP liegen außerhalb.

### Der Code

Die Programme stehen in `src/QMasterMpc.cpp`:

```cpp
program ("CD Loud", {
    { pTrim, 8.0f }, { pClip, 55.0f }, { pCeiling, -1.0f },
    { pRelease, 45.0f }, { pMono, 120.0f },
});
program ("Bus Drums", {
    { pMode, 1.0f }, { pClip, 45.0f }, { pTransient, 45.0f }, { pMono, 0.0f },
});
```

Im Master läuft der Clipper vor dem True-Peak-Limiter. Im Bus läuft er vor dem
Delay-Pad; es gibt keinen Limiter. Deshalb ist der Bus-Clip die Stelle, an der
sich Gain Reduction verteilen lässt, bevor der Master die Spitzenkontrolle
übernimmt.

### Die Messung

Der Loop (A4):

| Größe | vorher | nachher |
|---|---|---|
| Integrated | −11,0 LUFS | **−8,5 LUFS** |
| True Peak | +0,90 dBTP | **−1,10 dBTP** |
| PLR | 11,9 | **7,4** |
| Clipping | 0 | 0 |

Die verteilte Kette (A9), Bus Drums auf dem Drum-Bus und CD Loud auf dem Master:

| Größe | Ergebnis |
|---|---|
| Integrated | **−7,8 LUFS** |
| True Peak | **−1,30 dBTP** |
| PLR | **6,5** |
| LRA | 1,3 LU |
| Mono Side−Mid | −32,0 dB |
| Clipping | 0 |

„Seele“ (A10):

| Größe | alte Kette | neue Kette |
|---|---|---|
| Integrated | −12,5 LUFS | **−10,9 LUFS** |
| True Peak | **+1,40 dBTP** | −0,40 dBTP |
| PLR | 13,9 | 10,5 |
| LRA | 6,1 LU | 7,6 LU |
| Mono Side−Mid | −29,8 dB | −37,4 dB |

### Fehler & Test

A10 zeigt den Fehler, den ein Preset produziert, wenn man es für eine andere
Produktion hält. „CD Loud“ wurde auf „Under One Sun“ eingemessen. „Seele“ ist
dynamischer; dieselbe Kette wird **1,6 dB lauter**, aber **3,4 dB dichter**, und
der Korridor wird verfehlt.

Zwei Dinge sind daran lehrreich:

1. **Der True Peak bleibt 0,6 dB über dem Ziel.** Der Guard von **0,40 dB** ist
   nicht materialunabhängig. Für „Seele“ wird eine Decke von **−1,6 dBTP**
   empfohlen; das kostet **0,6 dB** Lautheit.
2. **Die Mitten verlieren relativ zum Sub 3–5,6 dB** (204 Hz bis 13 kHz). Das
   starke Master-Clipping lässt den Sub passieren und kappt die Mittenspitzen.

Der Test dagegen ist nicht das Preset, sondern `scripts/release-check.sh` auf
jedem Song. Ein Preset ist ein Startpunkt, keine Garantie.

Dazu kommt der stille Fall aus A5: **Clip 41** im Bus-Modus auf dem Master hat
bei dem niedrigen Eingangspegel „fast nichts“ getan; der PLR blieb bei 17,7. Wenn
sich zwischen Clip 41 und Clip 55 nichts ändert, ist nicht der Clipper kaputt,
sondern das Signal erreicht das Knie nicht.

### Die Anwendung

Für „Under One Sun“ bleibt der gemessene Punkt **Trim +8, Clip 55**: −8,1 LUFS,
−1,40 dBTP, PLR 6,70. Für „Seele“ gilt die materialabhängige Empfehlung:

- **Ceiling −1,6 dBTP**, damit der True Peak bei etwa −1,0 landet.
- **Clip 45, Trim +6, Tilt +1,0 … +1,5**, um die Mitten zurückzuholen.
- Die Lautheit kommt aus dem Bus, nicht aus dem Master.

Die verteilte Kette (A9) ist der Beweis, dass der Bus-Clip die Hauptarbeit nicht
übernehmen kann: Gegenüber dem einzelnen Master ist sie nur **0,3 dB lauter**
und **0,2 dB dichter**.

## 7. Der Clip-Regler in der Praxis

### Die Frage

Welche Zahl stellt man ein, wann senkt man sie, und wann hebt man sie? Die
Antwort ist keine Geschmacksfrage, sondern eine Tabelle mit drei Grenzen:
Loudness, True Peak und PLR.

### Die Mathematik

Der Treiber in dB ist linear zum Prozentwert:

| Clip | Treiber | Gain | Bedeutung |
|---|---|---|---|
| 0 % | 0,0 dB | 1,00 | kein Treiber, Knie bleibt aktiv |
| 30 % | 3,6 dB | 1,51 | sanfte Spitzenkontrolle |
| 45 % | 5,4 dB | 1,86 | Bus Drums |
| 48 % | 5,76 dB | 1,94 | in A9 für mehr Dynamik empfohlen |
| 55 % | 6,6 dB | 2,14 | CD Loud |
| 56 % | 6,72 dB | 2,17 | CD Dynamic |
| 100 % | 12,0 dB | 3,98 | massiv, nur für leises Material |

Die Zielbedingung bleibt:

```
−8 ± 1 LUFS   ·   TP ≤ −1,0 dBTP   ·   PLR 6–8
```

Der PLR ist die Bremse. Unter 6 ist es zu dicht; über 8 ist es zu dynamisch für
den Korridor. Die Loudness allein sagt nicht, ob der Clip-Regler zu weit ging.

### Der Code

Der Regler ist auf **0 … 100 %** begrenzt, die Umrechnung auf **0 … 12 dB**:

```cpp
return clamp (percent, 0.0f, 100.0f) * 0.12f;
```

Am Ende der Kette steht ein zweiter Clip bei **0,995**:

```cpp
constexpr float kOutputGuard = 0.995f;   // decimation safety
```

Er fängt Dezimierungs-Überschwinger ab, bevor sie die Datei erreichen. Er ist
kein Ersatz für den Limiter und keine zweite Klangstufe.

### Die Messung

Der Sweep aus A6 zeigt, wo der Korridor liegt:

| Trim | Clip | Integrated | PLR |
|---|---|---|---|
| **+8** | **55** | **−8,1 LUFS** | **6,70** |
| +8 | 45 | −8,9 LUFS | 7,50 |
| +7,5 | 56 | −8,4 LUFS | 7,0 |
| +8 | 52 | −8,4 LUFS | 7,0 |
| +7 | 56 | −8,7 LUFS | 7,3 |
| +6,5 | 56 | −9,0 LUFS | 7,6 |
| +10 | 55 | −6,9 LUFS | 5,5 |
| +12 | 45 | −6,5 LUFS | 5,2 |

Die letzten beiden Zeilen sind der Fehler: mehr Loudness, aber PLR unter 6. Das
ist die Grenze, an der „laut“ in „billig“ umschlägt.

Die verteilte Kette (A9) bestätigt die Rollenverteilung: **Bus Drums mit Clip
45** und **CD Loud mit Clip 55** ergeben −7,8 LUFS, −1,30 dBTP und PLR 6,5.
Gegenüber dem einzelnen CD-Loud-Master sind das nur **0,3 dB** mehr Loudness.

### Fehler & Test

Der häufigste Anwendungsfehler ist, den Clip-Regler nach Gehör auf Loudness zu
drehen. Drei Gegenproben fehlen dann:

1. **PLR und True Peak.** Ein zu heißer Master zeigt sich nicht am Clip-Prozent,
   sondern an PLR < 6 und TP über dem Deckel. A6: +10/55 ergibt −6,9 LUFS bei
   PLR 5,5; +12/45 ergibt −6,5 bei 5,2.
2. **Mitten und Spektrum.** A10 zeigt 3–5,6 dB Mittenverlust relativ zum Sub.
   Das ist kein Loudness-Gewinn, sondern eine Klangverschiebung.
3. **Die Messung selbst.** Wenn Clip 45 und Clip 55 dasselbe Ergebnis liefern,
   ist entweder der Eingang zu leise (A5, Clip 41) oder die Messung falsch (A7,
   Bandpass). In beiden Fällen hilft kein weiteres Drehen am Regler.

### Die Anwendung

Die Startpunkte aus den Programmen:

| Programm | Modus | Clip | Weitere Werte |
|---|---|---|---|
| Init | Master | 0 % | Ceiling −1, Release 50, Mono 120 |
| CD Loud | Master | 55 % | Trim +8, Ceiling −1, Release 45 |
| CD Dynamic | Master | 56 % | Trim +7,5, Ceiling −1 |
| Streaming Safe | Master | 45 % | Trim +5, Ceiling −1,5, Release 60 |
| Bus Drums | Bus | 45 % | Transient 45, Mono 0 |
| Bus 808 | Bus | 55 % | Transient 20, Mono 0 |

Wann senken:

- **PLR unter 6** — zu dicht, besonders bei +10/55 oder +12/45.
- **True Peak über dem Deckel** — bei „Seele“ bleibt er mit 0,40 dB Guard bei
  −0,4 dBTP; Ceiling auf −1,6 und Clip auf 45.
- **Mitten 3–5,6 dB unter dem Sub** — der Clipper kappt die Mittenspitzen.
- **Harte Becken oder Stimmen** — die ungeraden Harmonischen sitzen oben.

Wann heben:

- **Leises Material**, das das Knie nicht erreicht (A5, Clip 41).
- **Mehr Dichte bei gleichem True Peak**, solange der PLR über 6 bleibt.
- **Bus statt Master**, wenn die Reduction verteilt werden soll (A9).

Der Schlusssatz ist derselbe wie am Anfang: Der Clip-Regler kauft Lautheit mit
Spitzenkontrolle. Wer den Preis nicht messen kann, hört ihn erst, wenn der Mix
schon exportiert ist. Deshalb gilt für jede Einstellung: rendern, `measure.py`,
`release-check.sh` und bei Verdacht auf Aliasing `tests/alias-check.py` mit
FFT — nicht mit dem Bandpass.
