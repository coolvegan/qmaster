## Worum es geht

Ein Limiter ist das letzte Versprechen der Kette: Keine Spitze verlässt das
Plug-in über der Decke — auch nicht die zwischen den Samples. Dieses Versprechen
lässt sich nicht mit einem Regler einlösen, der auf die Spitze reagiert. Wenn
die Spitze da ist, ist es zu spät.

Die Lösung ist eine Verschiebung: Das Audio wird um **88 Samples** verzögert,
der Gain nicht. Der Gain weiß dadurch, was in **2,0 ms** am Ausgang ankommt.
Bezahlt wird das mit **102 Samples** Latenz, die das Plug-in dem Host meldet.

Diese Lektion folgt dem Sechs-Schritt-Vertrag der Reihe. Alle Messzahlen stammen
aus den Analysen **A3, A4, A6, A9 und A10** in `docs/ANALYSEN.md`; alle
Konstanten und Formeln aus `src/QMasterMpc.cpp` in der Fassung, die den
Impuls-Test besteht.

Acht Kapitel, jedes in sechs Schritten:

1. **Die Frage** — das Problem, das wirklich anlag.
2. **Die Mathematik** — die Herleitung mit den Zahlen aus dem Projekt.
3. **Der Code** — die Stelle im Repo, die daraus wurde.
4. **Die Messung** — was der Test zeigt.
5. **Fehler & Test** — was schiefging und welcher Test es heute verhindert.
6. **Die Anwendung** — welches Programm, welcher Regler, welche Zahl.

## 1. Die Frage: Wie folgt ein Gain den Spitzen, ohne zu pumpen?

### Die Frage

Der Clipper hat die Spitzen schon gerundet. Was übrig bleibt, sind Spitzen, die
knapp über der Decke liegen, und Spitzen, die zwischen den Samples entstehen.
Der Limiter muss beides abfangen. Drei Forderungen stehen gleichzeitig im Raum:

1. **Die Decke hält.** Kein Sample und kein Zwischenwert über dem Ceiling.
2. **Der Gain moduliert nicht hörbar.** Sonst klingt das ganze Programm, als
   würde jemand am Fader ziehen.
3. **Der Eingriff dauert nur so lange wie die Spitze.** Sonst duckt der Limiter
   Takte lang den ganzen Mix — das ist Pumpen.

Punkt 1 und Punkt 2 widersprechen sich. Eine Verstärkung, die schnell genug
ist, um eine Spitze abzufangen, ist schnell genug, um eine Flanke zu verbiegen.
Eine Verstärkung, die langsam genug ist, um nicht zu verbiegen, ist zu spät.

Der naheliegende Ausweg — die Spitze einfach abschneiden — ist der Clipper, und
der hat seine eigenen Kosten (Lektion 02). Der Limiter soll stattdessen den
Pegel *vor* der Spitze senken, sodass die Spitze selbst unangetastet bleibt.

### Die Mathematik

Der Unterschied zwischen „reagieren" und „vorwegnehmen" ist eine
Verzögerung. Ohne Verzögerung gilt am Ausgang:

```
y[n] = x[n] · g[n]
```

Der Gain `g[n]` kann nur aus Werten gebildet werden, die bis `n` bekannt sind.
Eine Spitze bei `n` ist für `g[n]` eine Überraschung. Mit einer Verzögerung von
`D` Samples gilt stattdessen:

```
y[n] = x[n − D] · g[n]
```

Jetzt darf `g[n]` aus `x[n]` gebildet werden — und `x[n]` ist die Spitze, die
`D` Samples später am Ausgang erscheint. Aus „zu spät" wird „rechtzeitig".

Die zweite Zutat ist die Glättung. Ein Gain, der von 1,0 auf 0,25 springt, ist
eine Rechteck-Multiplikation: Das erzeugt Breitbandanteile, hörbar als Klick
oder als raues Korn. Der Gain muss also einer Hüllkurve folgen, nicht einem
Sprung.

### Der Code

Die beiden Zutaten stehen in zwei Konstanten:

```cpp
constexpr int kLookahead = 88;          // Samples bei 1x
constexpr int kLatency   = 102;         // gemessen mit dem Impuls-Test
```

`kLookahead` ist die Verzögerung des Audios, `kLatency` die Zahl, die der Host
zum Kompensieren bekommt. Sie steht auf 102; die Differenz zum Lookahead sind
14 Samples, im Code als `kUpDownLatency` geführt:

```
88 + 14 = 102 Samples
```

### Die Messung

Der Sprung von „vorher" zu „nachher" ist in A4 zu sehen. Derselbe Loop, einmal
roh und einmal durch das Programm „CD Loud":

| Größe | vorher | nachher |
|---|---|---|
| Integrated | −11,0 LUFS | **−8,5 LUFS** |
| True Peak | +0,90 dBTP | **−1,10 dBTP** |
| PLR | 11,9 | **7,4** |
| Clipping | 0 | 0 |

Der Peak fällt um **2,0 dB**, die Loudness steigt um **2,5 dB**. Der Limiter hat
also nicht den ganzen Track leiser gemacht — sonst wären beide Werte gefallen.
Er hat nur dort eingegriffen, wo Spitzen waren. Genau das ist der Unterschied
zwischen Limiter und Kompressor.

### Fehler & Test

Ohne Verzögerung wäre der Test nicht zu bestehen: Der Gain wäre erst unten, als
der Peak schon vorbei war. Im Diagramm ist das ein Peak, der rechts neben der
Gain-Flanke steht.

Der Test, der das verhindert, ist der **Impuls-Test**: Ein Dirac bei Sample 0
muss bei Sample 102 erscheinen. Ohne Lookahead läge er bei Sample 0 — die
gemessene Latenz wäre 0 statt 102. `tests/plugin-check.py` prüft diese Position
in beiden Modi.

### Die Anwendung

Der Lookahead ist kein Regler. Er steht fest bei 88 Samples, weil er die
Latenz bestimmt und weil beide Modi dieselbe Latenz brauchen. Wer die Latenz
nicht kompensieren kann, darf den Limiter nicht auf die Summe setzen — auf der
MPC meldet das Plug-in 102 Samples, der Renderer zieht sie ab.

## 2. Die Hüllkurve: 0,3 ms Attack, 131 ms Release

### Die Frage

Wie schnell darf der Gain fallen, und wie langsam darf er zurück? Zu schnell
ist Verzerrung, zu langsam ist Pumpen. Dazwischen liegt ein Fenster, das von
zwei Zahlen begrenzt wird: der kürzesten Spitze, die noch sauber abgefangen
werden soll, und dem längsten Ducken, das noch nicht als Atmen hörbar ist.

### Die Mathematik

Der Baustein ist ein Ein-Pol-Tiefpass erster Ordnung, hier auf den Gain
angewandt:

```
g[n] = g[n−1] + α · (t[n] − g[n−1])
     = (1 − α) · g[n−1] + α · t[n]
```

`t[n]` ist der Ziel-Gain, `α` der Koeffizient. Nach `N` Samples ist ein
Sprung zur Hälfte, zu 63 %, zu 95 % verdaut:

```
1 − (1 − α)^N  ≈  1 − e^(−N / (τ · fs))
```

Der Koeffizient, der die Zeitkonstante `τ` trifft, ist deshalb:

```
α = 1 − exp( −1 / (τ · fs) )
```

Bei **44 100 Hz** und **0,3 ms**:

```
τ · fs = 0,0003 · 44100 = 13,23 Samples
α      = 1 − exp(−1 / 13,23) = 0,0728
```

Der Attack ist damit nach **13,23 Samples** zu 63 % erledigt. Nach den 88
Samples des Lookaheads sind es:

```
88 / 13,23 = 6,65 Zeitkonstanten
e^(−6,65)  = 0,0013  →  99,87 % des Wegs
```

Der Release kommt nicht aus einer festen Zeit, sondern aus einer Kennlinie.
Der Regler 0…100 % bildet logarithmisch auf **30 ms … 800 ms** ab:

```
τ_rel = 30 ms · (800 / 30)^(Release[%] / 100)
```

Bei **Release 45 %**:

```
τ_rel = 30 · 26,667^0,45 = 131,5 ms
```

Das sind **5797 Samples** und ein Koeffizient von **1,73 · 10⁻⁴** — rund 420-mal
kleiner als der Attack. Genau diese Asymmetrie macht den Limiter aus: schnell
unten, langsam zurück.

| Regler | τ | Samples bei 44,1 kHz | α |
|---|---|---|---|
| Attack (fest) | 0,3 ms | 13,23 | 0,0728 |
| Release 45 % | 131,5 ms | 5797 | 1,73 · 10⁻⁴ |
| Release 50 % | 154,9 ms | 6832 | 1,46 · 10⁻⁴ |
| Release 60 % | 215,2 ms | 9490 | 1,05 · 10⁻⁴ |

### Der Code

Der Attack steht fest, der Release wird pro Block aus dem Regler gesetzt:

```cpp
attack = onePoleCoeff (0.3f, sampleRate);
...
const float releaseMs = 30.0f * std::pow (800.0f / 30.0f,
                            clamp (get (pRelease) * 0.01f, 0.0f, 1.0f));
limiter.setRelease (releaseMs, (double) srate);
```

`onePoleCoeff` ist genau die Formel von oben:

```cpp
inline float onePoleCoeff (float ms, double sampleRate)
{
    if (ms <= 0.0f) return 1.0f;
    return 1.0f - std::exp (-1.0f / (ms * 0.001f * (float) sampleRate));
}
```

Wichtig: Die Klasse heißt `StereoLimiter`, folgt aber nicht der Hüllkurve des
Audiosignals, sondern glättet den **Ziel-Gain**. Die Rekursion ist dieselbe, der
Eingang ist ein anderer. Das ist der Grund, warum der Limiter kein
Envelope-Follower im klassischen Sinn ist — und warum er nicht nachhallt.

### Die Messung

Die Wirkung zeigt sich in der Verteilung, nicht am einzelnen Sample. In A4
fällt der PLR von **11,9 auf 7,4**. Ein Release von 131 ms bedeutet: Nach einer
Spitze ist der Gain nach 131 ms zu 63 % zurück, nach 394 ms (3 τ) zu 95 % und
nach ~650 ms (5 τ) praktisch ganz. Die 95 % passen in einen Schlag bei 120 BPM
(500 ms): Der Limiter atmet innerhalb eines Schlags, nicht über einen Takt.

### Fehler & Test

Ein zu schneller Release folgt der Wellenform. Bei 30 ms ändert sich der Gain
innerhalb einer Bassperiode: Aus dem Sinus wird ein Kamm, aus dem Bass ein raues
Rechteck. Das ist kein Messfehler, sondern die Definition von Verzerrung — der
Gain ist dann Teil des Signals, nicht mehr nur sein Pegel.

Der **Sweep** (20 Hz bis 20 kHz) deckt das auf: Ein sauberer Limiter lässt den
Grundton stehen und erzeugt keine neuen Linien. Ein zu schneller Release
erzeugt Seitenbänder um den Grundton, sichtbar als breiter Fuß im Spektrum.

### Die Anwendung

**Release 45 %** ist der Wert für dichten Rap: 131 ms sind kurz genug, dass
aufeinanderfolgende Kicks nicht als ein einziger Ducken-Block wirken, und lang
genug, dass der Gain nicht der Basswelle folgt. Für dynamische Songs geht der
Regler auf 55–60 %, für kurze Staccato-Spitzen eher auf 35 %.

## 3. Der Lookahead: 88 Samples, 89 Werte im Fenster

### Die Frage

Eine Verzögerung allein reicht nicht. Der Gain muss auch **unten bleiben**,
solange die Spitze noch in der Verzögerung steckt. Sonst passiert Folgendes:
Der Gain erholt sich, sobald die Spitze den Eingang verlassen hat — und genau
dann kommt sie am Ausgang an. Der Limiter würde die Spitze verfehlen, die er
gerade abfangen wollte.

### Die Mathematik

Der Code hält ein Fenster mit den letzten Peaks. Bei jedem Sample:

```
p[n]  = max( |L[n]|, |R[n]|, detektor[n] )
mx[n] = max( p[n−88] … p[n] )
t[n]  = min( 1, c / mx[n] )
```

`c` ist die Decke als linearer Faktor. Der Ziel-Gain ist nie größer als 1: Der
Limiter verstärkt nicht, er senkt nur.

Der Beweis, dass keine Spitze durchkommt, ist zwei Zeilen lang. Am Ausgang
steht bei `n` das Sample `x[n−88]`, und dessen Peak `p[n−88]` liegt im Fenster:

```
mx[n] ≥ p[n−88]
t[n]  = c / mx[n] ≤ c / p[n−88]
y[n]  = x[n−88] · g[n] ≤ x[n−88] · c / p[n−88] ≤ c
```

Die letzte Ungleichung gilt, weil `p[n−88] ≥ |x[n−88]|`. Der Gain darf dabei
höchstens zu klein sein — nie zu groß. Ein zu kleiner Gain kostet Lautheit,
ein zu großer kostet die Decke.

Das Fenster ist **88 Samples** breit; im Code werden **89 Werte** gelesen
(`k = 0 … 88`), weil der aktuelle Peak mitgezählt wird. Der Abstand zwischen
erstem und letztem Wert ist genau der Lookahead.

### Der Code

```cpp
window[(size_t) wpos] = peak;
wpos = (wpos + 1) & (WindowSize - 1);

float mx = 0.0f;
for (int k = 0; k <= kLookahead; ++k)
{
    const float v = window[(size_t) ((wpos - 1 - k) & (WindowSize - 1))];
    if (v > mx) mx = v;
}

float target = 1.0f;
if (mx > ceiling && mx > 1.0e-9f)
    target = ceiling / mx;

const float coeff = target < gain ? attack : release;
gain += coeff * (target - gain);

delayL.write (l);
delayR.write (r);
l = delayL.readInt (kLookahead) * gain;
r = delayR.readInt (kLookahead) * gain;
```

`WindowSize` ist 128, also eine Zweierpotenz: Der Ring läuft über eine Maske
statt über einen Vergleich. Das Fenster ist stereo gekoppelt — `peak` ist das
Maximum beider Kanäle, beide bekommen denselben Gain. Sonst würde sich das
Stereobild mit dem Gain verschieben.

### Die Messung

Der Lookahead ist die Ursache der Latenz, und die Latenz ist messbar. A3:

| Prüfung | Ergebnis |
|---|---|
| Latenz Master | **102 Samples gemessen, 102 gemeldet** |
| Latenz Bus | **102 Samples, identisch** |

102 Samples bei 44,1 kHz sind **2,31 ms**. Der Bus-Modus hat keinen Limiter,
aber dieselbe Verzögerung (`StereoPad`, ebenfalls 88 Samples). Ein Moduswechsel
verschiebt die Zeit also nicht — das ist der Grund, warum der Bus-Pad überhaupt
existiert.

### Fehler & Test

Der Test ist der **Impuls an erwarteter Position**: Ein Dirac muss exakt bei
Sample 102 erscheinen. Zusätzlich prüft `tests/plugin-check.py` den True Peak
bei voller Aussteuerung — ein zu kurzes Fenster zeigt sich dort als
Überschreitung, nicht als Latenzfehler.

Zur Größenordnung: Ein Fenster von 44 Samples wäre zu kurz. Dann blieben
`44 / 13,23 = 3,3` Zeitkonstanten, also **3,6 %** des Wegs. Bei einer Spitze,
die 6 dB über der Decke liegt, sind das noch **0,2 dB** zu heiß. 88 Samples
sind rund **2,0 ms** — lang genug für 6,65 Zeitkonstanten und kurz genug für
eine Latenz von 2,31 ms.

### Die Anwendung

88 Samples sind ein Kompromiss aus drei Randbedingungen: 6,65
Attack-Zeitkonstanten (damit der Gain wirklich unten ist), 2,0 ms Latenz (damit
das Plug-in auf der MPC noch spielbar ist) und 89 Vergleiche pro Sample, die
ohne Allokation im Audiopfad auskommen. Wer den Lookahead erhöht, gewinnt
Sicherheit und verliert Latenz — beides gleichzeitig geht nicht.

## 4. Decke, 4×-Detektor, Guard: 0,40 dB und 102 Samples

### Die Frage

Eine Decke in dBTP ist eine Aussage über ein Signal, das es als Sample noch
nicht gibt. Das Sample-Peak-Meter sieht nur die Abtastpunkte; der True Peak
liegt dazwischen. Wie prüft man also eine Decke, die man nicht direkt messen
kann — und wie viel Reserve braucht die Schätzung?

### Die Mathematik

Die Decke ist ein Pegel in dBTP. Verglichen wird aber in linearer Skala, weil
der Gain ein Faktor ist:

```
c = 10^( (Ceiling − Guard) / 20 )
```

Bei **Ceiling −1,0 dBTP** und **Guard 0,40 dB**:

```
c = 10^(−1,40 / 20) = 0,8511
```

Der Guard ist keine Kosmetik: Er verschiebt die interne Decke um 0,40 dB nach
unten. Bei Ceiling −2,0 dBTP wird daraus **−2,40 dBTP** und **0,7586**.

Der Detektor rechnet **4×**. Zwei Halfband-Stufen mit je **31 Taps**:

```
1× → 2× → 4×
```

Pro 1×-Sample entstehen vier interpolierte Werte. Der Peak ist das Maximum
ihrer Beträge. Der Limiter läuft dabei weiter bei 1×; nur der Detektor sieht
die Zwischenwerte.

Warum 4× und nicht 2×? Bei 2× liegt zwischen zwei Samples nur ein
Interpolationspunkt. Eine Spitze, die schmaler ist als ein halbes Sample,
fällt zwischen die Punkte. Der gemessene Fall: Sample-Peak **−1,25 dBFS**,
gemessener TP **−0,10 dBTP** — **1,15 dB** lagen zwischen den Samples. Ein
2×-Detektor sah sie nicht.

Die Latenz setzt sich aus zwei Teilen zusammen:

```
kLatency = kLookahead + kUpDownLatency
102      = 88          + 14
```

### Der Code

```cpp
class TruePeak4x
{
public:
    float peak (float x)
    {
        float a0, a1;
        first.process (x, a0, a1);       // 1x → 2x

        float b0, b1, c0, c1;
        second.process (a0, b0, b1);     // 2x → 4x
        second.process (a1, c0, c1);

        return std::max (std::max (std::fabs (b0), std::fabs (b1)),
                         std::max (std::fabs (c0), std::fabs (c1)));
    }
};
```

Im `process()` der Plugin-Klasse wird der Detektor mit dem Sample-Peak
verodert:

```cpp
const float peak = std::max (std::max (std::fabs (yl), std::fabs (yr)),
                             std::max (detL.peak (yl), detR.peak (yr)));
limiter.process (yl, yr, ceiling, peak);
```

`yl` und `yr` sind hier bereits auf 1× heruntergetaktet. Die Maximum-Bildung
ist eine Versicherung: Der Detektor darf nie **kleiner** lesen als der
Sample-Peak. Nach dem Limiter folgt noch ein Sicherheits-Clipper bei 0,995
(**−0,04 dB**), der nur bei Ausreißern greift.

### Die Messung

A3 misst die Decke an drei Punkten:

| Einstellung | gemessener TP | interner Deckel | Rest des Guards |
|---|---|---|---|
| Default, Clip 30 | **−1,40 dBTP** | −1,40 | 0,00 dB |
| Clip 100 | **−1,20 dBTP** | −1,40 | 0,20 dB |
| Ceiling −2 | **−2,40 dBTP** | −2,40 | 0,00 dB |

Bei Clipping bis 100 % bleiben von den 0,40 dB Guard noch **0,20 dB** übrig.
Der Detektor unterschätzt die schärferen Zwischenwerte also um 0,20 dB. Bei
Ceiling −2 und bei Clip 30 liegt er exakt.

### Fehler & Test

Der „4×"-Detektor war eine Zeit lang nur **2×**. Nachdem der Limiter von 2× auf
1× gezogen wurde, wurde der Detektor nicht mitgezogen: Er interpolierte nur
einen Zwischenwert pro Sample. Der TP blieb bei **−0,10 dBTP**, obwohl der
Sample-Peak bei **−1,25** lag — das Messgerät zeigte eine Überschreitung, das
Plug-in sah sie nicht.

Der Test ist **TP gegen Sample-Peak**: Auf geclipptem Material muss der TP
über dem Sample-Peak liegen. Liegt er darunter oder gleichauf, ist der Detektor
zu flach. `tests/plugin-check.py` prüft zusätzlich, dass der TP bei voller
Aussteuerung unter −1,0 dBTP bleibt.

### Die Anwendung

Der Guard ist die Reserve, die man nicht hört, sondern misst. 0,40 dB reichen
für Clipping bis 100 % (A3), aber nicht für jedes Material: Bei „Seele“ lag der
TP der neuen Kette trotz Guard bei **−0,40 dBTP** statt −1,40 (A10). Für solche
Songs wird die Decke um 0,6 dB tiefer gesetzt, nicht der Guard im Code
verändert — der Guard ist eine Konstante, die Decke ein Regler.

## 5. Der Code: StereoLimiter, TruePeak4x und die Konstanten

### Die Frage

Wie sieht die Stelle im Repo aus, an der aus den Formeln ein Sample wird? Und
welche Reihenfolge haben die Stufen — vor oder nach dem Oversampling?

### Die Mathematik

Die Reihenfolge ist keine Geschmacksfrage. Der Clipper arbeitet bei 2×, weil
seine Harmonischen oberhalb der Basis-Nyquist entstehen und vor dem
Heruntertakten gefiltert werden müssen. Der Limiter arbeitet bei 1×, weil er
die Spitzen des **fertigen** Signals kontrollieren muss, nicht die eines
Zwischensignals.

```
In → Trim → HPF → Tilt → Mono → Clipper (2×)
   → Heruntertakten → Limiter (1×, Detektor 4×) → Out
```

Würde der Limiter bei 2× sitzen, würde er Spitzen begrenzen, die nach dem
Heruntertakten gar nicht mehr existieren — und die Spitzen, die beim
Heruntertakten entstehen, nicht sehen.

### Der Code

Die fünf Konstanten, die das Verhalten festlegen:

```cpp
constexpr int   kUpDownLatency  = 14;
constexpr int   kLookahead      = 88;
constexpr int   kLatency        = 102;
constexpr float kCeilingGuardDb = 0.40f;
constexpr float kOutputGuard    = 0.995f;
```

Der Limiter selbst ist ein Fenster, ein Ziel und ein Ein-Pol-Glied:

```cpp
float target = 1.0f;
if (mx > ceiling && mx > 1.0e-9f)
    target = ceiling / mx;

const float coeff = target < gain ? attack : release;
gain += coeff * (target - gain);
```

Der Reset setzt den Gain auf 1,0 und leert Fenster und Verzögerung:

```cpp
void reset()
{
    delayL.reset();
    delayR.reset();
    window.fill (0.0f);
    wpos = 0;
    gain = 1.0f;
}
```

Der Deckel wird **geguardet** gesetzt — das ist die Korrektur aus Kapitel 7:

```cpp
ceilingSmooth.snap (dbToGain (get (pCeiling) - kCeilingGuardDb));
```

### Die Messung

Der Code ist nur so gut wie der Test, der ihn trägt. `tests/plugin-check.py`
prüft neun Dinge, darunter Latenz in beiden Modi, TP bei Default und bei
Clip 100 sowie den Ceiling-Fall. `build/host_sim` prüft die Ladesequenz und den
Parameter-Dump. `tools/render.cpp` schickt eine WAV durch das Plugin und
kompensiert dabei die gemeldeten 102 Samples.

### Fehler & Test

Der Kommentar über `StereoLimiter` sagt noch „operating at 2x". Das ist ein
Fossil aus der Zeit vor dem Umzug auf 1×. Der Kommentar wurde nicht mitgezogen,
die Klasse schon. Die Verschiebung auf 1× war die Ursache des 2×-Fehlers in
Kapitel 4. Lehre: Ein Kommentar ist kein Test. Wer die Rate ändert, muss den
Kommentar und den Detektor gleichzeitig ändern.

### Die Anwendung

Wer im Code etwas an der Limiter-Strecke ändert, prüft in dieser Reihenfolge:

1. `tests/plugin-check.py` — Latenz, TP, Ceiling.
2. `tests/loudness-check.py` — End-to-End gegen den Korridor.
3. `build/render` mit dem Test-Loop — PLR und Sample-Verteilung.
4. Erst dann ein echter Export.

## 6. Die Messung: Latenz, Decke und fünf Analysen

### Die Frage

Welche Zahlen belegen, dass der Limiter tut, was er soll? Und welche Zahlen
belegen, dass er es **nicht** tut? Beides gehört in dieselbe Tabelle, sonst
wird aus einem Test ein Werbeprospekt.

### Die Mathematik

Die eine Zahl, die alles zusammenfasst, ist der PLR:

```
PLR = TP − LUFS
```

Ein Limiter senkt den TP und lässt die LUFS stehen (oder hebt sie, wenn davor
mehr Gain kommt). Der PLR fällt. Ein Kompressor verteilt die Gain Reduction
gleichmäßiger und lässt bei gleicher Lautheit mehr PLR übrig — genau das war
der Unterschied zwischen der alten Vierer-Kette und QMaster in A6. Deshalb ist
der PLR die erste Zahl, die man nach einem Limiter prüft — und die zweite ist
die Verteilung der Samples an der Decke.

Bei A4:

```
ΔTP  = −1,10 − 0,90   = −2,0 dB
ΔLUFS = −8,5 − (−11,0) = +2,5 dB
ΔPLR = 7,4 − 11,9     = −4,5 dB
```

Die Probe stimmt: `−2,0 − 2,5 = −4,5`.

### Der Code

Die Programme, die diese Zahlen erzeugen, stehen als Tabelle im Code:

```cpp
program ("CD Loud", {
    { pTrim, 8.0f }, { pClip, 55.0f }, { pCeiling, -1.0f },
    { pRelease, 45.0f }, { pMono, 120.0f },
});
program ("CD Dynamic", {
    { pTrim, 7.5f }, { pClip, 56.0f }, { pCeiling, -1.0f },
    { pRelease, 45.0f }, { pMono, 120.0f },
});
```

Gemessen werden sie nicht im Plugin, sondern offline: `build/render` schreibt
eine WAV, `tools/measure.py` liest sie aus.

### Die Messung

**A3 — Plugin nativ.** Latenz 102 in beiden Modi, TP −1,40 bei Default,
−1,20 bei Clip 100, −2,40 bei Ceiling −2. Die Tabelle steht in Kapitel 4.

**A4 — End-to-End.** Der Loop aus A2, vorher −11,0 LUFS / +0,90 dBTP / PLR 11,9,
nachher −8,5 LUFS / −1,10 dBTP / PLR 7,4.

**A6 — Rohmix-Sweep.** 25 Kombinationen aus Trim und Clip, Korridor −9…−7 LUFS,
TP ≤ −1,0, PLR 6–8. Acht Treffer. Die drei wichtigsten:

| Trim | Clip | LUFS | TP | PLR |
|---|---|---|---|---|
| **+8** | **55** | **−8,1** | **−1,40** | **6,7** |
| +7,5 | 56 | −8,4 | −1,40 | 7,0 |
| +10 | 55 | −6,9 | −1,40 | 5,5 |

**A9 — verteilte Kette.** Bus Drums auf dem Drum-Bus, CD Loud auf dem Master:
**−7,8 LUFS, −1,30 dBTP, PLR 6,5**. Gegenüber dem einzelnen CD-Loud-Master
(−8,1 / 6,7) nur 0,3 dB lauter und 0,2 dB dichter.

**A10 — „Seele“.** Alte Vierer-Kette gegen QMaster:

| Größe | alt | neu |
|---|---|---|
| Integrated | −12,5 LUFS | **−10,9 LUFS** |
| True Peak | +1,40 dBTP | **−0,40 dBTP** |
| PLR | 13,9 | 10,5 |
| LRA | 6,1 LU | 7,6 LU |

### Fehler & Test

A6 zeigt die Grenze. Bei **Trim +10 / Clip 55** steht der Limiter bei
**−6,9 LUFS und PLR 5,5**. Der TP ist mit −1,40 immer noch sicher, aber der
Mix ist tot: 5,5 dB Abstand zwischen Spitze und Dauerpegel sind weniger als die
6 dB, die der Korridor verlangt.

Der Test, der das meldet, ist `scripts/release-check.sh`. Er prüft nicht, ob
das Plugin läuft, sondern ob das Ergebnis im Korridor liegt — und sagt Nein,
wenn der PLR unter 6 fällt.

### Die Anwendung

Die fünf Analysen decken drei verschiedene Dinge ab: das Plugin allein (A3),
die Kette auf synthetischem Material (A4, A6) und die Kette auf echter Musik
(A9, A10). Wer nur eine davon liest, überschätzt entweder das Plugin oder das
Material. Erst die drei zusammen sagen, ob der Limiter trägt.

## 7. Die drei Fehler: Ceiling, 2×, Moduswechsel

### Die Frage

Warum reicht ein Test, der sagt „klingt gut", nicht? Weil alle drei Fehler
dieses Kapitels im Hörtest als „irgendwie leise" oder „irgendwie falsch"
erscheinen — und keiner davon als das, was er war: ein Guard, der zu spät
greift, ein Detektor, der zu flach sieht, und ein Zustand, der den Modus
überlebt.

### Die Mathematik

Der erste Fehler ist reine Arithmetik. Der Ceiling-Glätter hat eine
Zeitkonstante von **20 ms**:

```
α = 1 − exp(−1 / (0,020 · 44100)) = 1 − exp(−1/882) = 1,13 · 10⁻³
```

Beim Start steht der Glätter auf dem **rohen** Ceiling, also 0 dB unter der
Decke statt 0,40 dB darunter. Bis er eingeschwungen ist, ist die Decke um bis
zu **0,40 dB** zu hoch. Gemessen wurden **0,25 dB** in den ersten 20 ms.

Der zweite Fehler ist eine Rate: 2× statt 4×. Der Detektor sieht pro Sample
einen statt drei Zwischenwerte. Die fehlende Spitze war **1,15 dB** hoch.

Der dritte Fehler ist ein Zustand: `gain` und die Verzögerungsleitungen
überleben den Moduswechsel. Ein Bus-Sample, das mit dem alten Master-Gain
multipliziert wird, ist ein Klick.

### Der Code

Alle drei Fixes stehen an einer Stelle:

```cpp
// 1. Guard schon beim Start
ceilingSmooth.snap (dbToGain (get (pCeiling) - kCeilingGuardDb));

// 2. Zwei Halfband-Stufen statt einer
first.process (x, a0, a1);
second.process (a0, b0, b1);
second.process (a1, c0, c1);

// 3. Reset bei Moduswechsel
if (index == pMode)
{
    ...
    limiter.reset();
    pad.reset();
    detL.reset();
    detR.reset();
    lastMode = getInt (pMode);
}
```

Der dritte Fix greift doppelt: `parameterChanged()` reagiert auf den
Host-Aufruf, und `process()` prüft zusätzlich `mode != lastMode`. Ein Modus, der
über einen Pfad hereinkommt, den die UI nicht kennt, wird trotzdem zurückgesetzt.

### Die Messung

Gefunden wurden alle drei durch dieselbe Methode: eine Zahl, die nicht zur
Erwartung passte.

- **Ceiling:** Der globale Peak lag bei **5 ms** — mitten in der Einschwingzeit
  des Glätters. Ein Peak am Anfang ist verdächtig, weil dort der Reset wirkt.
- **2×:** TP **−0,10 dBTP** gegen Sample-Peak **−1,25 dBFS**. Der TP darf nicht
  unter dem Sample-Peak liegen; wenn doch, ist der Detektor das Problem.
- **Modus:** Ein Wechsel Master → Bus mitten im Signal erzeugte einen Sprung,
  der vor dem Wechsel nicht da war.

### Fehler & Test

**(1) Ceiling-Smoother startet ungeguarded.** `reset()` setzte den Glätter auf
`dbToGain(get(pCeiling))` statt auf `dbToGain(get(pCeiling) − kCeilingGuardDb)`.
Die ersten 20 ms waren **0,25 dB** zu heiß. Gefunden, weil der globale Peak bei
**5 ms** lag. Test heute: `plugin-check.py` misst den TP und seine Position;
ein Peak in den ersten 20 ms ist ein Reset-Verdacht.

**(2) Der „4×"-Detektor war nur 2×.** Nach dem Umzug des Limiters auf 1× wurde
der Detektor nicht verdoppelt. Der TP blieb bei **−0,10 dBTP**, obwohl der
Sample-Peak bei **−1,25** lag. Behoben mit zwei Halfband-Stufen (1×→2×→4×) und
**0,40 dB** Guard. Test heute: TP gegen Sample-Peak auf geclipptem Material.

**(3) Moduswechsel ohne Reset.** Der alte Gain und die alten Filterzustände
überlebten den Wechsel. Test heute: Impuls-Latenz in beiden Modi (102/102),
Klick-Test über 100 Wechsel (Kriterium ≤ −60 dBFS) und ein Programmwechsel,
der den Modus kippt (CD Loud → Bus Drums): Beide Programme müssen ihre acht
Parameter melden, die UI muss neu zeichnen, und der Limiter muss bei 1,0
starten.

### Die Anwendung

Die Regel aus den drei Fehlern: **Jede Zustandsvariable braucht einen Reset,
jede Rate einen Test, jeder Guard eine Messung an der Stelle, an der er wirkt.**
Ein Guard, der nur im eingeschwungenen Zustand gilt, ist kein Guard. Ein
Detektor, der nur eine Rate kennt, ist ein Sample-Peak-Meter mit Extraschritt.

## 8. Die Anwendung: Release 45, Ceiling −1,0

### Die Frage

Welche Einstellung für welchen Song? Und was tut man, wenn der TP trotz
Limiter über dem Ziel liegt — Decke tiefer oder Trim tiefer?

### Die Mathematik

Die Decke ist ein Regler, der Trim ein Regler, der Limiter dazwischen. Wer den
TP senken will, hat zwei Möglichkeiten — solange der Limiter an der Decke
arbeitet:

```
Trim −0,6 dB  →  LUFS −0,6, TP gleich (der Limiter hält ihn)
Ceiling −0,6  →  LUFS −0,6, TP −0,6
```

In der Praxis kosten beide rund **0,6 dB Lautheit** (A10). Der Unterschied ist,
was mit dem PLR passiert: Trim senken erhöht ihn (weniger Dichte), Ceiling
senken lässt ihn stehen. Für einen Song, der zu dicht ist, ist Trim die
richtige Schraube; für einen, der zu heiß ist, das Ceiling.

Bei „Seele“ lag der TP bei **−0,40 dBTP** und das Ziel bei −1,0. Die Differenz
ist **0,60 dB**:

```
−1,0 − 0,6 = −1,6 dBTP
```

Deshalb die Empfehlung **Ceiling −1,6 dBTP** für diesen Song.

### Der Code

Die Programme sind Startpunkte, keine Garantie:

| Programm | Trim | Clip | Ceiling | Release | gemessen |
|---|---|---|---|---|---|
| Init | 0 | 0 | −1,0 | 50 | neutral |
| CD Loud | +8,0 | 55 | −1,0 | 45 | **−8,1 / −1,40 / 6,7** |
| CD Dynamic | +7,5 | 56 | −1,0 | 45 | **−8,4 / −1,40 / 7,0** |
| Streaming Safe | +5,0 | 45 | −1,5 | 60 | nicht gemessen |

„CD Loud“ und „CD Dynamic“ unterscheiden sich nur in 0,5 dB Trim und einem
Prozent Clip — und in **0,3 dB Lautheit** und **0,3 dB PLR**. Das ist der
Spielraum, den der Limiter am Ende noch lässt.

### Die Messung

A6 zeigt, wo die Grenze liegt:

| Trim | Clip | LUFS | PLR | Urteil |
|---|---|---|---|---|
| +8,0 | 55 | −8,1 | 6,7 | Korridor |
| +7,5 | 56 | −8,4 | 7,0 | Korridor, mehr Dynamik |
| +10 | 55 | −6,9 | 5,5 | zu dicht |

A9 bestätigt das auf der verteilten Kette: **−7,8 LUFS, PLR 6,5**. A10 zeigt
den materialabhängigen Teil: Der Guard von 0,40 dB reicht für „Under One Sun“,
nicht für „Seele“.

### Fehler & Test

Der häufigste Anwendungsfehler ist, Loudness mit Trim zu erzwingen. Bei
**+10 / 55** sind es **−6,9 LUFS** — 1,2 dB lauter als CD Loud, aber der PLR
fällt von 6,7 auf **5,5**. Der Limiter arbeitet dann nicht mehr als
Spitzenkontrolle, sondern als Dauerbremse.

Der Test ist `scripts/release-check.sh` mit dem Zielkorridor. Er prüft LUFS,
TP und PLR gemeinsam; ein einzelner guter Wert rettet die anderen nicht.

### Die Anwendung

| Fall | Trim | Clip | Ceiling | Release |
|---|---|---|---|---|
| Dichter Rap, CD-Lautheit | +8,0 | 55 | −1,0 | 45 |
| Etwas mehr Dynamik | +7,5 | 56 | −1,0 | 45 |
| Lossy/Streaming, Reserve | +5,0 | 45 | −1,5 | 60 |
| Dynamischer Song („Seele“) | +6,0 | 45 | −1,6 | 45 |

Drei Regeln dazu:

1. **PLR unter 6 heißt: zu viel.** Dann Trim runter, nicht Ceiling.
2. **TP über dem Ziel heißt: Ceiling runter.** 0,1 dB TP kosten 0,1 dB
   Lautheit, nicht mehr.
3. **Der Limiter macht die letzten 3–5 dB.** Was davor fehlt, holt er nicht
   sauber zurück. Ein Mix bei −18 LUFS und PLR 17,7 braucht die Busse, nicht
   den Master.

Für „Seele“ bleiben damit **0,6 dB** auf der Strecke — der Preis dafür, dass
der TP von **−0,40** auf etwa **−1,0 dBTP** kommt.

Für dynamische Songs liegt das Ceiling bei **−1,5 bis −1,6 dBTP**: 0,5 bis
0,6 dB mehr Headroom sind billiger als ein zerstörter Transient. Der Limiter
bekommt dann weniger zu tun — bei „Seele“ liegt der PLR mit 10,5 ohnehin über
dem Korridor.
