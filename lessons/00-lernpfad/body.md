## Worum es geht

QMaster ist ein Master- und Bus-Plug-in für die Akai MPC. Es soll einen dichten
Rap-Mix auf kompetitive CD-Lautheit bringen, ohne ihn zu zerstören — und dabei
auf einem Gerät laufen, das weder Meter noch Sidechain-Bus kennt.

Diese Lektionen sind kein Marketing. Sie sind der Versuch, die Mathematik und
den Code hinter dem Plugin so zu erklären, dass man beides selbst prüfen kann.
Jede Zahl stammt aus einem Messlauf, jede Behauptung hat einen Test.

## Wie du liest

Jedes Kapitel hat sechs Schritte:

1. **Die Frage** — das Problem, das wirklich anlag.
2. **Die Mathematik** — eine Herleitung, mit den Zahlen aus dem Projekt.
3. **Der Code** — die Stelle im Repo, die daraus wurde.
4. **Die Messung** — was der Test zeigt.
5. **Fehler & Test** — was schiefging, wie es gefunden wurde und welcher Test
   es heute verhindert.
6. **Anwendung** — welches Programm, welcher Regler, welche Zahl.

Am Ende jeder Lektion stehen Rechenaufgaben. Wer nur lesen will, kann sie
überspringen; wer rechnen kann, versteht den Code danach anders.

## Fehler gehören dazu

Diese Reihe zeigt nicht nur, wie es am Ende aussieht. Sie zeigt die Irrwege:
einen geteilten Puffer zwischen zwei Kanälen, einen falsch geschriebenen
24-Bit-WAV, einen Ceiling-Glätter, der 20 ms lang ungeguardet war, und einen
„4×"-Detektor, der nur 2× war. Jeder dieser Fehler steht in der Lektion, in der
er passiert ist — mit dem Test, der ihn heute verhindert.

Das ist kein Selbstzweck. Wer nur Rezepte liest, erkennt den Fehler nicht, wenn
er das nächste Mal anders aussieht.

## Die sechs Lektionen

| # | Lektion | Frage | Was du danach kannst |
|---|---|---|---|
| 01 | [**Lautheit**](https://marcokittel.de/lesson/19c51f56-cdc1-4610-b883-b1ea29cc4540) | Warum ist −14 LUFS kein Mastering-Ziel? | LUFS, True Peak und PLR messen und einordnen |
| 02 | [**Clipper**](https://marcokittel.de/lesson/482db70e-d09d-4d6f-b54c-183b64972491) | Warum klingt laut oft billig? | Harmonische und Aliasing vorhersagen, Oversampling begründen |
| 03 | [**Limiter**](https://marcokittel.de/lesson/f8d09145-6f1e-4b59-98a0-3ddff283ca3a) | Wie folgt ein Gain ohne zu pumpen? | Attack, Release und Lookahead dimensionieren |
| 04 | [**Filter und Mono**](https://marcokittel.de/lesson/eda3d6ed-27cd-4a80-b946-5c09808f854a) | Warum verschwindet der Bass auf dem Handy? | Biquads, Pole und M/S verstehen |
| 05 | [**Code-Generierung**](https://marcokittel.de/lesson/ddfe2add-5451-4b3d-a48c-866c2b6215f3) | Wie kontrolliert man einen Agenten? | Spezifikation, Testvertrag und Review beherrschen |
| 06 | [**Capstone**](https://marcokittel.de/lesson/94f4b4a8-23ad-4751-8778-59e8fc2c8f8f) | Klingt es wirklich? | Einen Beat mastern und die Ziele nachweisen |

## Die zwei Spuren

**Verstehen** führt über die Mathematik. **Bauen** führt über den Code. Beide
treffen sich in der Messung. Wer nur eine Spur geht, bekommt entweder Theorie
ohne Gefühl oder Code ohne Begründung.

## Was am Ende steht

Kein „so klingt highend", sondern eine überprüfbare Kette:

- integrierte Lautheit im Zielkorridor,
- True Peak unter dem Deckel,
- keine Aliasing-Artefakte,
- Mono-Kompatibilität unter 120 Hz,
- und ein Mix, der auch leise noch funktioniert.

Der Rest ist Musik.

Alle Teile sind veröffentlicht: die Links stehen in der Tabelle oben.
