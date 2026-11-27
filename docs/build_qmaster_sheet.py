import json
import os
import subprocess
import sys

OUT_JSONL = "/tmp/opencode/qmaster-mathe.jsonl"
OUT_XLSX = "/home/marco/Dev/qmaster-mpc/docs/QMaster-Mathematik.xlsx"

lines = []


def cmd(command_id, **params):
    lines.append(json.dumps({"command": command_id, "params": params}, ensure_ascii=False))


def vals(rng, rows):
    cmd("range.setValues", range=rng, values=rows)


def merge(rng):
    cmd("home.mergeCenter", range=rng)


def bold(rng, on=True):
    cmd("home.bold", range=rng, on=on)


def italic(rng, on=True):
    cmd("home.italic", range=rng, on=on)


def font_size(rng, size):
    cmd("home.fontSize", range=rng, size=size)


def font_color(rng, color):
    cmd("home.fontColor", range=rng, color=color)


def fill(rng, color):
    cmd("home.fillColor", range=rng, color=color)


def align_left(rng):
    cmd("home.alignLeft", range=rng)


def align_center(rng):
    cmd("home.alignCenter", range=rng)


def align_right(rng):
    cmd("home.alignRight", range=rng)


def wrap(rng):
    cmd("home.wrapText", range=rng, on=True)


def numfmt(rng, code):
    cmd("home.numberFormat", range=rng, code=code)


def border(rng, preset="all", style="thin", color="#BFBFBF"):
    cmd("home.borders", range=rng, preset=preset, style=style, color=color)


def width(cols, chars):
    cmd("home.columnWidth", cols=cols, chars=chars)


def height(rows, points):
    cmd("home.rowHeight", rows=rows, points=points)


def freeze(cell):
    cmd("view.freezePanes", cell=cell)


def section(row, text, last="H"):
    rng = "A%d:%s%d" % (row, last, row)
    vals("A%d" % row, [[text]])
    merge(rng)
    fill(rng, "#D9E2F3")
    bold(rng)
    font_size(rng, 12)
    font_color(rng, "#1F3864")
    align_left(rng)
    height("%d:%d" % (row, row), 22)


def header(row, labels, last="D"):
    end = chr(ord("A") + len(labels) - 1)
    rng = "A%d:%s%d" % (row, end, row)
    vals("A%d" % row, [labels])
    bold(rng)
    fill(rng, "#F2F2F2")
    border(rng, "all", "thin", "#BFBFBF")
    height("%d:%d" % (row, row), 20)


def note(row, text, last="H"):
    rng = "A%d:%s%d" % (row, last, row)
    vals("A%d" % row, [[text]])
    merge(rng)
    italic(rng)
    font_color(rng, "#595959")
    align_left(rng)
    wrap(rng)
    height("%d:%d" % (row, row), 30)


def start_sheet(name, tab):
    if name == "Start":
        cmd("sheet.rename", sheet="Sheet1", name="Start")
    else:
        cmd("home.insertSheet", name=name)
    cmd("sheet.tabColor", color=tab)


def title(name, subtitle, cols=8):
    last = chr(ord("A") + cols - 1)
    vals("A1", [[name]])
    merge("A1:%s1" % last)
    fill("A1:%s1" % last, "#0D1216")
    bold("A1:%s1" % last)
    font_size("A1:%s1" % last, 18)
    font_color("A1:%s1" % last, "#FFFFFF")
    align_left("A1:%s1" % last)
    height("1:1", 34)

    vals("A2", [[subtitle]])
    merge("A2:%s2" % last)
    italic("A2:%s2" % last)
    font_color("A2:%s2" % last, "#595959")
    align_left("A2:%s2" % last)
    wrap("A2:%s2" % last)
    height("2:2", 26)


def inputs(rng):
    fill(rng, "#FFF2CC")
    border(rng, "all", "thin", "#D6B656")


def results(rng):
    fill(rng, "#E2EFDA")


# ===========================================================================
# Start
# ===========================================================================
start_sheet("Start", "#22E6FF")
width("A:A", 30)
width("B:B", 28)
width("C:C", 62)
width("D:D", 12)
title("QMaster — Mathematik zum Durchgehen",
      "Gelb = Eingabe, grün = Ergebnis. Ändere die gelben Zellen; alles andere rechnet. "
      "Die Zahlen stammen aus dem QMaster-Projekt (docs/ANALYSEN.md).")

section(4, "Die Blätter")
header(5, ["Blatt", "Was", "Schlüsselformel"])
rows = [
    ("Lautheit", "Peak, RMS, LUFS, True Peak, PLR", "RMS = A/√2 · PLR = TP − LUFS"),
    ("Clipper", "Knie, Transferfunktion, Aliasing", "y = knee + (1−knee)·tanh(…)"),
    ("Limiter", "Attack, Release, Lookahead, Decke", "α = 1 − e^(−1/(t·fs))"),
    ("Filter", "Biquad, LR4, Tilt, Mono Maker", "H(z) = (b0+b1z⁻¹+b2z⁻²)/(1+a1z⁻¹+a2z⁻²)"),
    ("Zielkorridor", "Loudness, TP, PLR, Sweep", "PLR = TP − LUFS"),
    ("Messungen", "A2, A3, A10 als Rohdaten", "PLR und Crest als Formeln"),
]
vals("A6", [[r[0], r[1], r[2]] for r in rows])
bold("A6:C11")
border("A6:C11")
wrap("C6:C11")

section(13, "Zielkorridor")
header(14, ["Größe", "Ziel", "Toleranz"])
vals("A15", [["Integrated", "−8 LUFS", "±1"],
             ["True Peak", "−1,0 dBTP", "≤"],
             ["PLR", "6…8 dB", ""],
             ["LRA", "4…7 LU", ""],
             ["Mono <120 Hz", "keine Auslöschung", ""]])
border("A15:C19")

section(21, "Legende")
vals("A22", [["Eingabe", 0.5, "gelb"],
             ["Ergebnis", "=B22*2", "grün"],
             ["Hinweis", "Text", "grau"]])
inputs("B22")
results("B23")
italic("A24:C24")
font_color("A24:C24", "#595959")
numfmt("B22:B23", "0.00")
border("A22:C24")

note(26, "Alle Messwerte: docs/ANALYSEN.md, Stand 26.11.2026. "
         "Die sieben Lektionen: marcokittel.de/lesson/4ca48031-1624-4d83-9042-40fb6b3d3542")
freeze("A4")

# ===========================================================================
# Lautheit
# ===========================================================================
start_sheet("Lautheit", "#2E75B6")
width("A:A", 34)
width("B:B", 16)
width("C:C", 12)
width("D:D", 58)
title("Lautheit: Peak, RMS, LUFS und True Peak",
      "Drei Zahlen, ein Signal. Gelbe Zellen ändern, grüne Werte beobachten.")

section(4, "1. dB")
header(5, ["Größe", "Wert", "Einheit", "Formel"])
vals("A6", [["Amplitude A", 0.5, "–", "Eingabe"],
            ["Referenz A0", 1.0, "–", "Eingabe"],
            ["Pegel", "=20*LOG10(B6/B7)", "dB", "20·log10(A/A0)"],
            ["zurück", "=10^(B8/20)", "linear", "10^(dB/20)"],
            ["Leistungsverhältnis", 2, "–", "Eingabe"],
            ["Leistung in dB", "=10*LOG10(B10)", "dB", "10·log10(P/P0)"]])
inputs("B6:B7")
inputs("B10")
results("B8:B9")
results("B11")
numfmt("B8", "0.00")
numfmt("B9", "0.0000")
numfmt("B11", "0.00")
border("A6:D11")

section(13, "2. Sinus und Crest")
header(14, ["Größe", "Wert", "Einheit", "Formel"])
vals("A15", [["Spitzenamplitude", 0.5, "–", "Eingabe"],
             ["Peak", "=20*LOG10(B15)", "dBFS", "20·log10(A)"],
             ["RMS", "=B15/SQRT(2)", "linear", "A/√2"],
             ["RMS", "=20*LOG10(B17)", "dBFS", ""],
             ["Crest", "=B16-B18", "dB", "Peak − RMS"]])
inputs("B15")
results("B16:B19")
numfmt("B16", "0.00")
numfmt("B17", "0.0000")
numfmt("B18:B19", "0.00")
border("A15:D19")

section(21, "3. Stereo summiert")
header(22, ["Größe", "Wert", "Einheit", "Formel"])
vals("A23", [["Mono", -9.0, "LUFS", "Eingabe (A2)"],
             ["Stereo L = R", "=B23+10*LOG10(2)", "LUFS", "+3,01 dB"],
             ["Differenz", "=B24-B23", "dB", ""]])
inputs("B23")
results("B24:B25")
numfmt("B23:B24", "0.0")
numfmt("B25", "0.00")
border("A23:D25")

section(27, "4. Gating")
header(28, ["Block", "Loudness", "über absolut", "über relativ"])
vals("A29", [["Block 1", -12, "", ""],
             ["Block 2", -11, "", ""],
             ["Block 3", -13, "", ""],
             ["Block 4", -75, "", ""]])
vals("C29", [[f'=IF(B{r}>=$B$33,B{r},"")'] for r in range(29, 33)])
vals("D29", [[f'=IF(AND(B{r}>=$B$33,B{r}>=$B$35),B{r},"")'] for r in range(29, 33)])
vals("A33", [["Absolutes Gate", -70, "LUFS", "Eingabe"],
             ["Mittel über absolut", "=AVERAGE(C29:C32)", "LUFS", "nur Blöcke über −70"],
             ["Relatives Gate", "=B34-10", "LUFS", "10 LU unter dem Mittel"],
             ["Integriert", "=AVERAGE(D29:D32)", "LUFS", "nur Blöcke über beiden Gates"]])
inputs("B29:B32")
inputs("B33")
results("B34:B36")
numfmt("B29:B36", "0.0")
border("A28:D36")

section(38, "5. True Peak und PLR")
header(39, ["Größe", "Wert", "Einheit", "Formel"])
vals("A40", [["Sample Peak", -1.01, "dBFS", "Loop A2"],
             ["True Peak", 0.90, "dBTP", "Eingabe"],
             ["Überschreitung", "=B41-B40", "dB", "TP − Peak"],
             ["Integrated", -8.0, "LUFS", "Eingabe"],
             ["PLR", "=B41-B43", "dB", "TP − LUFS"],
             ["TP bei +6 dB", "=B41+6", "dBTP", ""],
             ["LUFS bei +6 dB", "=B43+6", "LUFS", ""],
             ["PLR danach", "=B45-B46", "dB", "unverändert"]])
inputs("B40:B41")
inputs("B43")
results("B42")
results("B44:B48")
numfmt("B40:B41", "0.00")
numfmt("B42", "0.00")
numfmt("B43:B44", "0.0")
numfmt("B45:B46", "0.00")
numfmt("B47:B48", "0.0")
border("A39:D48")

note(50, "Der PLR ist gegenüber reiner Verstärkung invariant: TP und LUFS steigen gemeinsam. "
         "Nur Dynamikbearbeitung ändert ihn.")
freeze("A4")

# ===========================================================================
# Clipper
# ===========================================================================
start_sheet("Clipper", "#C55A11")
width("A:A", 14)
width("B:B", 18)
width("C:C", 20)
width("D:D", 20)
title("Clipper: Knie, Transferfunktion und Aliasing",
      "Der Clipper arbeitet bei 2×; das Knie ist 2 dB breit und endet am Ceiling (0,851 bei −1 dBTP).")

section(4, "1. Drive")
header(5, ["Clip %", "dB", "linear", ""])
vals("A6", [[0, "=A6*0.12", "=10^(B6/20)", ""],
            [30, "=A7*0.12", "=10^(B7/20)", ""],
            [45, "=A8*0.12", "=10^(B8/20)", ""],
            [55, "=A9*0.12", "=10^(B9/20)", ""],
            [56, "=A10*0.12", "=10^(B10/20)", ""],
            [100, "=A11*0.12", "=10^(B11/20)", ""]])
inputs("A6:A11")
results("B6:C11")
numfmt("A6:A11", "0")
numfmt("B6:B11", "0.00")
numfmt("C6:C11", "0.0000")
border("A5:D11")

section(13, "2. Transferfunktion")
header(14, ["x", "linear", "y (clipped)", "Gain y/x"])
xs = [round(-1.2 + 0.1 * i, 1) for i in range(25)]
vals("A15", [[x, f"=A{r}", None, None] for x, r in zip(xs, range(15, 40))])
for r in range(15, 40):
    vals(f"C{r}", [[f"=IF(ABS(A{r})<=0.6757,A{r},SIGN(A{r})*(0.6757+0.1753*TANH((ABS(A{r})-0.6757)/0.1753)))"]])
    vals(f"D{r}", [[f'=IF(A{r}=0,"",C{r}/A{r})']])
inputs("A15:A39")
results("C15:D39")
numfmt("A15:A39", "0.0")
numfmt("C15:C39", "0.0000")
numfmt("D15:D39", "0.000")
border("A14:D39")
cmd("insert.chart", range="A14:C39", type="line", subtype="markers",
    title="Transferfunktion: linear vs. clipped", at="F14", width=560, height=320)

section(41, "3. Gemessen")
header(42, ["Fall", "Wert", "Einheit", "Quelle"])
vals("A43", [["Alias Clip 0", -120.0, "dBc", "A3"],
             ["Alias Clip 100", -95.8, "dBc", "A3"],
             ["Loop Sample Peak", -1.01, "dBFS", "A2"],
             ["Loop True Peak", 0.90, "dBTP", "A2"],
             ["Überschreitung", "=B46-B45", "dB", "TP − Peak"],
             ["Bandpass-Fake", -25.3, "dBFS", "A7"],
             ["FFT-Wahrheit", -95.8, "dBc", "A7"]])
results("B47")
numfmt("B43:B44", "0.00")
numfmt("B45:B48", "0.00")
border("A42:D49")

section(51, "4. Anwendung")
header(52, ["Programm", "Clip %", "Drive dB", ""])
vals("A53", [["CD Loud", 40, "=B53*0.12", ""],
             ["CD Dynamic", 30, "=B54*0.12", ""],
             ["Bus Drums", 30, "=B55*0.12", ""],
             ["Bus 808", 35, "=B56*0.12", ""]])
inputs("B53:B55")
results("C53:C55")
numfmt("B53:B56", "0")
numfmt("C53:C56", "0.00")
border("A52:D55")

note(57, "Ein Ergebnis, das sich nicht ändert, wenn man das System ändert, ist verdächtig. "
         "Der Bandpass zeigte −25,3 dBFS bei 1229 Hz; die FFT zeigte −95,8 dBc. "
         "1.0.3: Knie von 0,35 auf 2 dB verbreitert, Schwelle ans Ceiling gekoppelt; "
         "Presets von Trim +8/Clip 55 auf Trim 0/Clip 40. Kick-Klirr fiel um 57–68 dB.")
freeze("A4")

# ===========================================================================
# Limiter
# ===========================================================================
start_sheet("Limiter", "#7030A0")
width("A:A", 34)
width("B:B", 16)
width("C:C", 12)
width("D:D", 52)
title("Limiter: Hüllkurve, Lookahead und Decke",
      "Der Gain muss die Spitze erreichen, bevor sie am Ausgang ankommt.")

section(4, "1. Koeffizienten")
header(5, ["Größe", "Wert", "Einheit", "Formel"])
vals("A6", [["fs", 44100, "Hz", "Eingabe"],
            ["Attack", 0.3, "ms", "Eingabe"],
            ["Release", 45, "%", "Eingabe"],
            ["Release", "=30*(800/30)^(B8/100)", "ms", "30…800 ms"],
            ["alpha Attack", "=1-EXP(-1/(B7/1000*B6))", "–", "1 − e^(−1/(t·fs))"],
            ["alpha Release", "=1-EXP(-1/(B9/1000*B6))", "–", ""],
            ["Attack", "=B7/1000*B6", "Samples", "t·fs"],
            ["Release", "=B9/1000*B6", "Samples", ""]])
inputs("B6:B8")
results("B9:B13")
numfmt("B9", "0.0")
numfmt("B10:B11", "0.00000")
numfmt("B12:B13", "0")
border("A5:D13")

section(15, "2. Gain Computer")
header(16, ["Größe", "Wert", "Einheit", "Formel"])
vals("A17", [["Ceiling", -1.0, "dBTP", "Eingabe"],
             ["Guard", 0.4, "dB", "Konstante"],
             ["intern", "=B17-B18", "dBTP", ""],
             ["linear", "=10^(B19/20)", "–", ""],
             ["Peak", 0.93, "linear", "Eingabe"],
             ["target", "=MIN(1,B20/B21)", "–", "Decke / Peak"],
             ["GR", "=20*LOG10(B22)", "dB", ""]])
inputs("B17")
inputs("B21")
results("B19:B23")
numfmt("B18:B19", "0.00")
numfmt("B20", "0.0000")
numfmt("B21", "0.0000")
numfmt("B22", "0.0000")
numfmt("B23", "0.00")
border("A16:D23")

section(25, "3. Latenz")
header(26, ["Größe", "Wert", "Einheit", "Formel"])
vals("A27", [["Lookahead", 88, "Samples", ""],
             ["Up/Down", 14, "Samples", ""],
             ["gesamt", "=B27+B28", "Samples", ""],
             ["ms @ 44,1", "=B29/44100*1000", "ms", ""],
             ["ms @ 48", "=B29/48000*1000", "ms", ""]])
results("B29:B31")
numfmt("B29", "0")
numfmt("B30:B31", "0.00")
border("A26:D31")

section(33, "4. Gemessen")
header(34, ["Fall", "LUFS", "TP", "PLR"])
vals("A35", [["Loop A4", -8.5, -1.1, "=C35-B35"],
             ["A9 verteilt", -7.8, -1.3, "=C36-B36"],
             ["A10 alt", -12.5, 1.4, "=C37-B37"],
             ["A10 neu", -10.9, -0.4, "=C38-B38"],
             ["Sweep +8/55", -8.1, -1.4, "=C39-B39"]])
results("D35:D39")
numfmt("B35:B39", "0.0")
numfmt("C35:C39", "0.00")
numfmt("D35:D39", "0.00")
border("A34:D39")

section(41, "5. Sweep A6")
header(42, ["Trim", "Clip", "LUFS", "TP", "PLR", "ΔLUFS"])
sweep = [
    (8, 55, -8.1, -1.4), (6, 65, -8.6, -1.4), (10, 30, -8.8, -1.4),
    (8, 45, -8.9, -1.4), (10, 45, -7.6, -1.4), (12, 30, -7.5, -1.4),
    (6, 75, -7.9, -1.4), (8, 65, -7.4, -1.4),
]
vals("A43", [[t, c, l, tp, f"=D{r}-C{r}", f"=C{r}+8"] for r, (t, c, l, tp) in zip(range(43, 51), sweep)])
results("E43:F50")
numfmt("A43:A50", "0")
numfmt("B43:B50", "0")
numfmt("C43:C50", "0.0")
numfmt("D43:D50", "0.00")
numfmt("E43:E50", "0.00")
numfmt("F43:F50", "0.00")
border("A42:F50")

note(52, "Zu heiß: Trim +10 / Clip 55 → −6,9 LUFS bei PLR 5,5. "
         "Der Korridor ist −8 ±1, TP ≤ −1, PLR 6…8.")
freeze("A4")

# ===========================================================================
# Filter
# ===========================================================================
start_sheet("Filter", "#548235")
width("A:A", 14)
width("B:B", 14)
width("C:C", 14)
width("D:D", 14)
width("E:E", 14)
width("F:F", 14)
width("G:G", 12)
width("H:H", 12)
width("I:I", 12)
title("Filter und Mono: Biquad, LR4, Tilt und Mid/Side",
      "Ein Biquad ist eine Differenzengleichung; zwei kaskadierte ergeben LR4.")

section(4, "1. Biquad HPF 24 Hz", "D")
header(5, ["Größe", "Wert", "Einheit", "Formel"])
vals("A6", [["fs", 44100, "Hz", "Eingabe"],
            ["f0", 24, "Hz", "Eingabe"],
            ["Q", 0.7071, "–", "Eingabe"],
            ["w0", "=2*PI()*B7/B6", "rad", "2πf/fs"],
            ["cos w0", "=COS(B9)", "–", ""],
            ["sin w0", "=SIN(B9)", "–", ""],
            ["alpha", "=B11/(2*B8)", "–", "sin/(2Q)"],
            ["b0", "=(1+B10)/2", "–", ""],
            ["b1", "=-(1+B10)", "–", ""],
            ["b2", "=(1+B10)/2", "–", ""],
            ["a0", "=1+B12", "–", ""],
            ["a1", "=-2*B10", "–", ""],
            ["a2", "=1-B12", "–", ""],
            ["b0 norm", "=B13/B16", "–", "b0/a0"],
            ["b1 norm", "=B14/B16", "–", ""],
            ["b2 norm", "=B15/B16", "–", ""],
            ["a1 norm", "=B17/B16", "–", ""],
            ["a2 norm", "=B18/B16", "–", ""],
            ["Polradius", "=SQRT(ABS(B23))", "–", "√a2"]])
inputs("B6:B8")
results("B9:B24")
numfmt("B9", "0.00000")
numfmt("B10:B12", "0.00000")
numfmt("B13:B24", "0.000000")
border("A5:D24")

section(26, "2. Magnitude Response", "I")
header(27, ["f Hz", "w", "Re N", "Im N", "Re D", "Im D", "|H|", "dB", "LR4 dB"])
freqs = [10, 20, 24, 30, 40, 60, 100, 200]
for idx, f in enumerate(freqs):
    r = 28 + idx
    vals(f"A{r}", [[f, f"=2*PI()*A{r}/$B$6",
                    f"=$B$19+$B$20*COS(B{r})+$B$21*COS(2*B{r})",
                    f"=-($B$20*SIN(B{r})+$B$21*SIN(2*B{r}))",
                    f"=1+$B$22*COS(B{r})+$B$23*COS(2*B{r})",
                    f"=-($B$22*SIN(B{r})+$B$23*SIN(2*B{r}))",
                    f"=SQRT((C{r}^2+D{r}^2)/(E{r}^2+F{r}^2))",
                    f"=20*LOG10(G{r})",
                    f"=2*H{r}"]])
inputs("A28:A35")
results("B28:I35")
numfmt("A28:A35", "0")
numfmt("B28:B35", "0.0000")
numfmt("C28:F35", "0.0000")
numfmt("G28:G35", "0.0000")
numfmt("H28:I35", "0.00")
border("A27:I35")

section(37, "3. Tilt", "D")
header(38, ["Größe", "Wert", "Einheit", "Formel"])
vals("A39", [["Tilt", 0, "dB", "Eingabe"],
             ["Low Shelf", "=-B39/2", "dB @200", "halbe Spreizung"],
             ["High Shelf", "=B39/2", "dB @3k", ""]])
inputs("B39")
results("B40:B41")
numfmt("B39:B41", "0.0")
border("A38:D41")

section(43, "4. Mono Maker", "D")
header(44, ["Größe", "Wert", "Einheit", "Formel"])
vals("A45", [["L", 0.8, "–", "Eingabe"],
             ["R", 0.2, "–", "Eingabe"],
             ["Mid", "=(B45+B46)/2", "–", "(L+R)/2"],
             ["Side", "=(B45-B46)/2", "–", "(L−R)/2"],
             ["L rekonstruiert", "=B47+B48", "–", "Mid+Side"],
             ["R rekonstruiert", "=B47-B48", "–", "Mid−Side"]])
inputs("B45:B46")
results("B47:B50")
numfmt("B45:B50", "0.000")
border("A44:D50")

section(52, "5. Gemessen", "D")
header(53, ["Fall", "Side−Mid", "Einheit", "Quelle"])
vals("A54", [["A9, Mono 120", -32.0, "dB", "A9"],
             ["A10, Mono 120", -37.4, "dB", "A10"],
             ["A5, Mono 200", -41.0, "dB", "A5"]])
numfmt("B54:B56", "0.0")
border("A53:D56")

note(58, "Side wird unter 120 Hz hochpassgefiltert: L = Mid + Side, R = Mid − Side. "
         "Mono 200 Hz war zu aggressiv (−41 dB).")
freeze("A4")

# ===========================================================================
# Zielkorridor
# ===========================================================================
start_sheet("Zielkorridor", "#BF8F00")
width("A:A", 26)
width("B:B", 12)
width("C:C", 12)
width("D:D", 12)
width("E:E", 12)
width("F:F", 10)
width("G:G", 10)
width("H:H", 12)
title("Zielkorridor: Loudness, True Peak, PLR",
      "Der Master ist erst fertig, wenn alle vier Kriterien gleichzeitig passen.")

section(4, "1. Ziel")
header(5, ["Größe", "Ziel", "Toleranz"])
vals("A6", [["Integrated", -8.0, "±1"],
            ["True Peak", -1.0, "≤"],
            ["PLR", 7.0, "6…8"],
            ["LRA", 5.5, "4…7"]])
numfmt("B6:B9", "0.0")
border("A5:C9")

section(11, "2. Messungen")
header(12, ["Fall", "LUFS", "TP", "PLR", "ΔLUFS", "TP ok", "PLR ok", "Gesamt"])
meas = [("Loop A4", -8.5, -1.1), ("A9 verteilt", -7.8, -1.3),
        ("A10 alt", -12.5, 1.4), ("A10 neu", -10.9, -0.4)]
for idx, (name, lufs, tp) in enumerate(meas):
    r = 13 + idx
    vals(f"A{r}", [[name, lufs, tp, f"=C{r}-B{r}", f"=B{r}-$B$6",
                    f'=IF(C{r}<=$B$7,"ok","fail")',
                    f'=IF(AND(D{r}>=6,D{r}<=8),"ok","fail")',
                    f'=IF(AND(ABS(E{r})<=1,F{r}="ok",G{r}="ok"),"PASS","FAIL")']])
results("D13:H16")
numfmt("B13:C16", "0.00")
numfmt("D13:D16", "0.00")
numfmt("E13:E16", "0.0")
border("A12:H16")

section(18, "3. Gain-Rechnung")
header(19, ["Größe", "Wert", "Einheit"])
vals("A20", [["Rohmix", -18.3, "LUFS"],
             ["Ziel", -8.0, "LUFS"],
             ["nötiger Gain", "=B21-B20", "dB"],
             ["TP Rohmix", -0.6, "dBTP"],
             ["TP bei reiner Verstärkung", "=B23+B22", "dBTP"],
             ["gemessen nach Kette", -1.4, "dBTP"],
             ["Differenz", "=B25-B24", "dB"]])
inputs("B20:B21")
inputs("B23")
inputs("B25")
results("B22:B24")
results("B26")
numfmt("B20:B21", "0.0")
numfmt("B22", "0.0")
numfmt("B23:B26", "0.00")
border("A19:C26")

section(28, "4. Sweep A6")
header(29, ["Trim", "Clip", "LUFS", "TP", "PLR", "ΔLUFS"])
for idx, (t, c, l, tp) in enumerate(sweep):
    r = 30 + idx
    vals(f"A{r}", [[t, c, l, tp, f"=D{r}-C{r}", f"=C{r}+8"]])
results("E30:F37")
numfmt("A30:B37", "0")
numfmt("C30:C37", "0.0")
numfmt("D30:D37", "0.00")
numfmt("E30:F37", "0.00")
border("A29:F37")

note(39, "Korridor: −9…−7 LUFS, TP ≤ −1, PLR 6…8. "
         "Die alte Vierer-Kette lag bei −8,0 / PLR 8,2; QMaster ist bei gleicher Lautheit dichter.")
freeze("A4")

# ===========================================================================
# Messungen
# ===========================================================================
start_sheet("Messungen", "#7F7F7F")
width("A:A", 26)
width("B:B", 12)
width("C:C", 12)
width("D:D", 12)
width("E:E", 12)
width("F:F", 10)
width("G:G", 10)
title("Messungen: Rohdaten aus dem Projekt",
      "Diese Blätter sind die Quelle für die Formeln. PLR und Crest sind berechnet.")

section(4, "A2 — Synthetische Signale")
header(5, ["Signal", "Peak", "RMS", "LUFS", "TP", "PLR", "Crest"])
signals = [
    ("Sinus mono", -6.02, -9.03, -9.0, -6.0),
    ("Sinus stereo", -6.02, -9.03, -6.0, -6.0),
    ("Links only", -6.02, -12.04, -9.0, -6.0),
    ("Pink Noise", -7.41, -20.00, -18.8, -7.4),
    ("Anti-Phase", -6.02, -9.03, -9.6, -6.0),
    ("Loop", -1.01, -10.25, -11.0, 0.90),
]
for idx, (name, peak, rms, lufs, tp) in enumerate(signals):
    r = 6 + idx
    vals(f"A{r}", [[name, peak, rms, lufs, tp, f"=E{r}-D{r}", f"=B{r}-C{r}"]])
results("F6:G11")
numfmt("B6:E11", "0.00")
numfmt("F6:G11", "0.00")
border("A5:G11")

section(13, "A3 — Plugin nativ")
header(14, ["Prüfung", "Wert", "Einheit"])
vals("A15", [["Latenz Master", 102, "Samples"],
             ["Latenz Bus", 102, "Samples"],
             ["TP default", -1.40, "dBTP"],
             ["TP Clip 100", -1.10, "dBTP"],
             ["Alias Clip 100", -95.8, "dBc"]])
numfmt("B15:B16", "0")
numfmt("B17:B19", "0.00")
border("A14:C19")

section(21, "A10 — Seele, Bandbalance")
header(22, ["Hz", "alt", "neu", "Differenz"])
bands = [(204, -0.73, -4.17), (289, 0.00, -5.35), (580, -1.57, -6.19),
         (1167, -4.96, -8.38), (3325, -6.98, -10.11), (13437, -9.86, -13.21)]
for idx, (hz, old, new) in enumerate(bands):
    r = 23 + idx
    vals(f"A{r}", [[hz, old, new, f"=C{r}-B{r}"]])
results("D23:D28")
numfmt("A23:A28", "0")
numfmt("B23:D28", "0.00")
border("A22:D28")

note(30, "Differenz negativ: Die neue Kette ist dort relativ zum Sub leiser. "
         "Bei Under One Sun war sie 1–3 dB heller; die Wirkung ist materialabhängig.")
freeze("A4")

# activate Start
cmd("sheet.activate", sheet="Start")

os.makedirs(os.path.dirname(OUT_XLSX), exist_ok=True)
with open(OUT_JSONL, "w", encoding="utf-8") as fh:
    fh.write("\n".join(lines) + "\n")

print("commands:", len(lines))
proc = subprocess.run(["gridcraft-cli", "run", "--script", OUT_JSONL, "--out", OUT_XLSX],
                      stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
print(proc.stdout[-1500:])
print(proc.stderr[-3000:], file=sys.stderr)
sys.exit(proc.returncode)
