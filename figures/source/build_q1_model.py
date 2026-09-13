"""Build matching editable Draw.io and vector TikZ sources for the Q1 figure."""

from pathlib import Path
import re
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[2]
FIG = ROOT / "figures"
WIDTH, HEIGHT = 1180, 580
UNIT_PT = 0.44
BLUE = "#5470DB"
ORANGE = "#E6886D"
INK = "#333333"
GRAY = "#B8B8B8"
LIGHT = "#E5E5E5"
OUTLINE = BLUE
LIGHT_BLUE = "#96B7FC"

mxfile = ET.Element("mxfile", host="app.diagrams.net", agent="Codex", version="24.7.17")
diagram = ET.SubElement(mxfile, "diagram", id="q1-physical-model", name="问题一物理模型")
model = ET.SubElement(
    diagram, "mxGraphModel", dx=str(WIDTH), dy=str(HEIGHT), grid="1",
    gridSize="10", guides="1", tooltips="1", connect="1", arrows="1",
    fold="1", page="1", pageScale="1", pageWidth=str(WIDTH),
    pageHeight=str(HEIGHT), math="1", shadow="0", background="#FFFFFF",
)
root = ET.SubElement(model, "root")
ET.SubElement(root, "mxCell", id="0")
ET.SubElement(root, "mxCell", id="1", parent="0")
tikz = []
counter = 0


def color(hex_color):
    return "{rgb,255:red,%d;green,%d;blue,%d}" % tuple(
        int(hex_color[i:i + 2], 16) for i in (1, 3, 5)
    )


def cell(name, style, value="", edge=False):
    global counter
    counter += 1
    return ET.SubElement(root, "mxCell", id=f"{counter:03d}-{name}", value=value,
                         style=style, parent="1", **{"edge" if edge else "vertex": "1"})


def shape(name, kind, x, y, w, h, fill=None, stroke=OUTLINE, lw=1.5, dashed=False,
          opacity=100):
    style = (f"shape={kind};html=1;whiteSpace=wrap;fillColor={fill or 'none'};"
             f"strokeColor={stroke or 'none'};strokeWidth={lw};"
             f"fillOpacity={opacity};dashed={int(dashed)};dashPattern=6 5;")
    c = cell(name, style)
    ET.SubElement(c, "mxGeometry", x=str(x), y=str(y), width=str(w), height=str(h),
                  **{"as": "geometry"})
    opts = [f"line width={lw * UNIT_PT:.3f}pt"]
    opts.append("draw=" + (color(stroke) if stroke else "none"))
    opts.append("fill=" + (color(fill) if fill else "none"))
    if opacity != 100:
        opts.append(f"fill opacity={opacity / 100}")
    if dashed:
        opts.append("dash pattern=on 2.64pt off 2.2pt")
    if kind == "ellipse":
        path = f"({x + w / 2},{y + h / 2}) ellipse [x radius={w / 2}, y radius={h / 2}]"
    else:
        path = f"({x},{y}) rectangle ({x + w},{y + h})"
    tikz.append(r"\path[" + ",".join(opts) + "] " + path + ";")


def line(name, points, stroke=INK, lw=1.5, dashed=False, arrow=False, both=False,
         dashdot=False):
    start_arrow = "classic" if both else "none"
    end_arrow = "classic" if arrow or both else "none"
    style = ("edgeStyle=none;rounded=0;html=1;"
             f"strokeColor={stroke};strokeWidth={lw};dashed={int(dashed or dashdot)};"
             f"dashPattern={'12 4 2 4' if dashdot else '6 5'};"
             f"startArrow={start_arrow};endArrow={end_arrow};"
             "startFill=1;endFill=1;endSize=8;startSize=8;")
    c = cell(name, style, edge=True)
    g = ET.SubElement(c, "mxGeometry", relative="1", **{"as": "geometry"})
    ET.SubElement(g, "mxPoint", x=str(points[0][0]), y=str(points[0][1]),
                  **{"as": "sourcePoint"})
    ET.SubElement(g, "mxPoint", x=str(points[-1][0]), y=str(points[-1][1]),
                  **{"as": "targetPoint"})
    if len(points) > 2:
        array = ET.SubElement(g, "Array", **{"as": "points"})
        for x, y in points[1:-1]:
            ET.SubElement(array, "mxPoint", x=str(x), y=str(y))
    opts = ["draw=" + color(stroke), f"line width={lw * UNIT_PT:.3f}pt"]
    if dashdot:
        opts.append("dash pattern=on 5.28pt off 1.76pt on 0.88pt off 1.76pt")
    elif dashed:
        opts.append("dash pattern=on 2.64pt off 2.2pt")
    tip = "{Latex[length=3.5pt,width=2.8pt]}"
    if both:
        opts.append(tip + "-" + tip)
    elif arrow:
        opts.append("-" + tip)
    tikz.append(r"\draw[" + ",".join(opts) + "] " +
                " -- ".join(f"({x},{y})" for x, y in points) + ";")


def text(name, x, y, w, h, value, size=22, ink=INK, align="center", bold=False):
    # The same math strings go to MathJax in Draw.io and to XeLaTeX in the PDF.
    mx_value = re.sub(r"\$([^$]+)\$", lambda m: r"\(" + m.group(1) + r"\)", value)
    mx_value = mx_value.replace(r"\\", "<br>")
    style = ("text;html=1;strokeColor=none;fillColor=none;whiteSpace=wrap;"
             "overflow=visible;verticalAlign=middle;spacing=0;"
             f"align={align};fontFamily=SimSun;fontSize={size};fontColor={ink};"
             f"fontStyle={int(bold)};")
    c = cell(name, style, mx_value)
    ET.SubElement(c, "mxGeometry", x=str(x - w / 2), y=str(y - h / 2),
                  width=str(w), height=str(h), **{"as": "geometry"})
    font_pt = size * UNIT_PT
    font = rf"\fontsize{{{font_pt:.2f}}}{{{font_pt * 1.28:.2f}}}\selectfont"
    if bold:
        font += r"\bfseries"
    opts = [f"align={align}", "inner sep=0pt", "outer sep=0pt",
            "text=" + color(ink), "font={" + font + "}"]
    if align == "left":
        opts += ["anchor=west", f"text width={w * UNIT_PT:.2f}pt"]
        x -= w / 2
    tikz.append(r"\node[" + ",".join(opts) + f"] at ({x},{y}) " + "{" + value + "};")


# Draw both end ellipses after the interior so neither outline is occluded.
# A transparent schematic shows the internal axial plane within a full cylinder.
shape("longitudinal-section", "rectangle", 112, 204, 480, 204,
      fill=LIGHT_BLUE, stroke=None, opacity=22)
shape("left-end", "ellipse", 60, 204, 104, 204,
      fill=LIGHT_BLUE, stroke=OUTLINE, lw=1.8, opacity=16)
shape("right-end", "ellipse", 540, 204, 104, 204,
      fill=LIGHT_BLUE, stroke=OUTLINE, lw=1.8, opacity=20)
line("top-surface", [(112, 204), (592, 204)], lw=2.2, stroke=OUTLINE)
line("bottom-surface", [(112, 408), (592, 408)], lw=2.2, stroke=OUTLINE)
line("center-axis", [(42, 306), (660, 306)], stroke="#8E8E8E", dashdot=True)

text("oven-environment", 352, 30, 530, 28,
     r"烘房环境：$T_a(t),\ C_a(t)$", size=23)
text("heat-direction", 274, 94, 180, 30, "热量传入", ink=ORANGE, size=22)
text("water-direction", 458, 94, 180, 30, "水分迁出", ink=BLUE, size=22)
text("heat-sign", 274, 125, 120, 25, r"$q_s<0$", ink=ORANGE, size=21)
text("water-sign", 458, 125, 120, 25, r"$j_s>0$", ink=BLUE, size=21)
for offset in (-25, 25):
    line("heat-in", [(274 + offset, 153), (274 + offset, 229)],
         stroke=ORANGE, lw=3.2, arrow=True)
    line("water-out", [(458 + offset, 222), (458 + offset, 146)],
         stroke=BLUE, lw=3.2, arrow=True)

line("radius", [(200, 306), (200, 205)], lw=1.9, arrow=True)
shape("center-point", "ellipse", 196.8, 302.8, 6.4, 6.4, fill=INK, stroke=None)
shape("surface-point", "ellipse", 196.8, 200.8, 6.4, 6.4, fill=INK, stroke=None)
text("radius-symbol", 219, 254, 28, 30, r"$r$", size=25)
text("center-label", 245, 338, 140, 30, r"中心 $r=0$", size=22)
text("surface-label", 184, 174, 165, 30, r"表面 $r=R$", size=22)
text("temperature-field", 382, 264, 275, 38, r"温度场 $T(r,t)$", ink=ORANGE, size=26)
text("moisture-field", 399, 368, 300, 38, r"含水率场 $C(r,t)$", ink=BLUE, size=26)
text("section-label", 352, 443, 560, 30, "圆柱药材（内部纵剖示意）", size=22)

# Boundary expressions use the paper's outward-positive sign convention.
line("boundary-rule", [(690, 91), (1158, 91)], stroke=GRAY, lw=1.0)
text("robin-heading", 924, 63, 468, 34, "表面 Robin 交换边界", size=24, bold=True)
text("surface-values", 924, 117, 468, 30,
     r"$T_s=T(R,t),\quad C_s=C(R,t)$", size=21)
text("heat-heading", 924, 190, 468, 30, "表面热通量", size=22, ink=ORANGE, align="left")
text("heat-equation", 924, 236, 468, 48,
     r"$q_s=-kT_r(R,t)=h[T_s-T_a(t)]$", size=23, align="left")
text("moisture-heading", 924, 316, 468, 30,
     "表面水分通量", size=22, ink=BLUE, align="left")
text("moisture-equation", 924, 365, 468, 58,
     r"$\dfrac{j_s}{s_0}=-D(C_s)C_r(R,t)=h_m[C_s-C_a(t)]$",
     size=23, align="left")
text("density-definition", 924, 444, 468, 28,
     r"$s_0$：单位体积干物质质量", size=21, align="left")
text("flux-convention", 924, 483, 468, 28,
     "通量均以径向向外为正", size=21, align="left")

line("symmetry-rule", [(113, 477), (591, 477)], stroke=LIGHT, lw=1.0)
text("symmetry-heading", 352, 504, 480, 30, "中心对称边界", size=22)
text("symmetry-equation", 352, 546, 540, 43,
     r"$\dfrac{\partial T}{\partial r}(0,t)=0,\qquad"
     r"\dfrac{\partial C}{\partial r}(0,t)=0$", size=23)

ET.indent(mxfile, space="  ")
ET.ElementTree(mxfile).write(FIG / "fig_q1_model.drawio", encoding="utf-8", xml_declaration=True)
tex_preamble = r"""\documentclass[border=0pt]{standalone}
\usepackage[fontset=windows]{ctex}
\usepackage{amsmath}
\usepackage{tikz}
\usetikzlibrary{arrows.meta}
\pagestyle{empty}
\begin{document}
\begin{tikzpicture}[x=0.44pt,y=-0.44pt]
"""
(FIG / "source" / "fig_q1_model.tex").write_text(
    tex_preamble + rf"\path[use as bounding box] (0,0) rectangle ({WIDTH},{HEIGHT});" + "\n"
    + "\n".join(tikz) + "\n\\end{tikzpicture}\n\\end{document}\n",
    encoding="utf-8",
)
print(f"Created {FIG / 'fig_q1_model.drawio'}")
print(f"Created {FIG / 'source' / 'fig_q1_model.tex'}")
print(f"Editable Draw.io objects: {counter}")
