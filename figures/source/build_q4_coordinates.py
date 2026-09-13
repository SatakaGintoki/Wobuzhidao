"""Draw proportional radial shrinkage using a common geometric projection."""

from pathlib import Path
import base64
import math
import re
import urllib.parse
import xml.etree.ElementTree as ET
import zlib


FIG = Path(__file__).resolve().parents[1]
WIDTH, HEIGHT = 1260, 735
BLUE, ORANGE, INK = "#5470DB", "#E6886D", "#333333"
GRAY, LIGHT = "#B8B8B8", "#E5E5E5"
UNIT = 0.44
mxfile = ET.Element("mxfile", host="app.diagrams.net", agent="Codex", version="24.7.17")
diagram = ET.SubElement(mxfile, "diagram", id="q4-material-coordinate", name="收缩与材料坐标")
model = ET.SubElement(
    diagram, "mxGraphModel", dx=str(WIDTH), dy=str(HEIGHT), grid="1", gridSize="10",
    guides="1", tooltips="1", connect="1", arrows="1", fold="1", page="1",
    pageScale="1", pageWidth=str(WIDTH), pageHeight=str(HEIGHT), math="1", shadow="0",
    background="#FFFFFF",
)
root = ET.SubElement(model, "root")
ET.SubElement(root, "mxCell", id="0")
ET.SubElement(root, "mxCell", id="1", parent="0")
tikz = []


def color(value):
    return "{rgb,255:red,%d;green,%d;blue,%d}" % tuple(int(value[i:i + 2], 16) for i in (1, 3, 5))


def point(x, y):
    return f"({x:.3f},{y:.3f})"


def vector_shape(name, points, stroke=BLUE, fill=None, opacity=100, lw=1.7):
    # A native mxGraph stencil retains an editable vector object, not an image.
    xs, ys = zip(*points)
    x0, y0, w, h = min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)
    stencil = ET.Element("shape", name=name, w="100", h="100", aspect="variable", strokewidth="inherit")
    fg = ET.SubElement(stencil, "foreground")
    path = ET.SubElement(fg, "path")
    for i, (x, y) in enumerate(points):
        ET.SubElement(path, "move" if i == 0 else "line",
                      x=f"{100 * (x - x0) / w:.5f}", y=f"{100 * (y - y0) / h:.5f}")
    ET.SubElement(path, "close")
    ET.SubElement(fg, "fillstroke" if fill else "stroke")
    uri_encoded = urllib.parse.quote(ET.tostring(stencil, encoding="unicode"), safe="~()*!.'-")
    compressor = zlib.compressobj(wbits=-15)
    compressed = compressor.compress(uri_encoded.encode()) + compressor.flush()
    encoded = base64.b64encode(compressed).decode()
    style = (f"shape=stencil({encoded});strokeColor={stroke or 'none'};"
             f"fillColor={fill or 'none'};fillOpacity={opacity};strokeWidth={lw};html=1;")
    cell = ET.SubElement(root, "mxCell", id=name, style=style, vertex="1", parent="1")
    ET.SubElement(cell, "mxGeometry", x=f"{x0:.3f}", y=f"{y0:.3f}",
                  width=f"{w:.3f}", height=f"{h:.3f}", **{"as": "geometry"})
    opts = ["draw=" + (color(stroke) if stroke else "none"),
            "fill=" + (color(fill) if fill else "none"),
            f"fill opacity={opacity / 100}", f"line width={lw * UNIT}pt", "line join=round"]
    tikz.append(r"\path[" + ",".join(opts) + "] " + " -- ".join(point(*p) for p in points) + " -- cycle;")


def line(name, points, stroke=INK, lw=1.6, arrow=False, both=False, dashdot=False):
    cell = ET.SubElement(
        root, "mxCell", id=name, edge="1", parent="1",
        style=(f"edgeStyle=none;rounded=0;strokeColor={stroke};strokeWidth={lw};"
               f"dashed={int(dashdot)};dashPattern=12 4 2 4;"
               f"startArrow={'classic' if both else 'none'};"
               f"endArrow={'classic' if arrow or both else 'none'};startFill=1;endFill=1;endSize=8;startSize=8;"),
    )
    g = ET.SubElement(cell, "mxGeometry", relative="1", **{"as": "geometry"})
    for p, role in [(points[0], "sourcePoint"), (points[-1], "targetPoint")]:
        ET.SubElement(g, "mxPoint", x=str(p[0]), y=str(p[1]), **{"as": role})
    if len(points) > 2:
        a = ET.SubElement(g, "Array", **{"as": "points"})
        for x, y in points[1:-1]:
            ET.SubElement(a, "mxPoint", x=str(x), y=str(y))
    opts = ["draw=" + color(stroke), f"line width={lw * UNIT}pt"]
    if dashdot:
        opts.append("dash pattern=on 5.28pt off 1.76pt on 0.88pt off 1.76pt")
    tip = "{Latex[length=3.7pt,width=3pt]}"
    if both:
        opts.append(tip + "-" + tip)
    elif arrow:
        opts.append("-" + tip)
    tikz.append(r"\draw[" + ",".join(opts) + "] " + " -- ".join(point(*p) for p in points) + ";")


def text(name, x, y, w, value, size=26, ink=INK, bold=False, height=38):
    mxvalue = re.sub(r"\$([^$]+)\$", lambda m: r"\(" + m.group(1) + r"\)", value)
    cell = ET.SubElement(
        root, "mxCell", id=name, value=mxvalue, vertex="1", parent="1",
        style=("text;html=1;strokeColor=none;fillColor=none;whiteSpace=wrap;overflow=visible;"
               "align=center;verticalAlign=middle;spacing=0;fontFamily=SimSun;"
               f"fontSize={size};fontColor={ink};fontStyle={int(bold)};"),
    )
    ET.SubElement(cell, "mxGeometry", x=str(x - w / 2), y=str(y - height / 2),
                  width=str(w), height=str(height), **{"as": "geometry"})
    font = rf"\fontsize{{{size * UNIT:.2f}}}{{{size * UNIT * 1.3:.2f}}}\selectfont"
    if bold:
        font += r"\bfseries"
    tikz.append(r"\node[inner sep=0pt,outer sep=0pt,text=" + color(ink) + ",font={" + font
                + "}] at " + point(x, y) + " {" + value + "};")


AX = (1.0, 0.0)
UP = (0.0, -1.0)
LENGTH = 304.0


def add(a, b, scale=1):
    return a[0] + b[0] * scale, a[1] + b[1] * scale


def ring(center, radius):
    return [add(add(center, AX, radius * 0.38 * math.cos(2 * math.pi * i / 120)),
                UP, radius * math.sin(2 * math.pi * i / 120)) for i in range(120)]


def dot(name, p, ink=ORANGE, size=4.5):
    pts = [(p[0] + size * math.cos(i * math.pi / 12), p[1] + size * math.sin(i * math.pi / 12))
           for i in range(24)]
    vector_shape(name, pts, stroke=ink, fill=ink, lw=1)


def cylinder(prefix, rear, radius):
    front = add(rear, AX, LENGTH)
    rear_up, rear_down = add(rear, UP, radius), add(rear, UP, -radius)
    front_up, front_down = add(front, UP, radius), add(front, UP, -radius)
    vector_shape(prefix + "-section", [rear_up, front_up, front_down, rear_down],
                 stroke=None, fill="#96B7FC", opacity=22)
    vector_shape(prefix + "-rear", ring(rear, radius), stroke=BLUE, fill="#96B7FC", opacity=16)
    vector_shape(prefix + "-front", ring(front, radius), stroke=BLUE, fill="#96B7FC", opacity=20)
    line(prefix + "-top", [rear_up, front_up], stroke=BLUE, lw=2)
    line(prefix + "-bottom", [rear_down, front_down], stroke=BLUE, lw=2)
    line(prefix + "-axis", [add(rear, AX, -radius * 0.38 - 12),
                            add(front, AX, radius * 0.38 + 12)], stroke="#909090", dashdot=True)
    return front, front_up, front_down


text("initial-heading", 265, 40, 450, r"初始状态 $t=0$", size=28, bold=True)
text("current-heading", 981, 40, 450, r"收缩后 $t>0$", size=28, bold=True)
text("initial-coordinate", 265, 83, 460, r"物理坐标 $0\leq r\leq R_0$", size=25)
text("current-coordinate", 981, 83, 470, r"材料坐标 $\xi=r/R(t)\in[0,1]$", size=25)

left_rear, right_rear = (91, 320), (814, 320)
R0_SCREEN, RT_SCREEN, XI_POINT = 112, 78.4, 0.60
left_front, left_top, left_bottom = cylinder("initial", left_rear, R0_SCREEN)
right_front, right_top, right_bottom = cylinder("contracted", right_rear, RT_SCREEN)

# Place the corresponding particle in the same interior axial cross-section.
AXIAL_FRACTION = 0.50
left_origin = add(left_rear, AX, LENGTH * AXIAL_FRACTION)
right_origin = add(right_rear, AX, LENGTH * AXIAL_FRACTION)
left_particle = add(left_origin, UP, R0_SCREEN * XI_POINT)
right_particle = add(right_origin, UP, RT_SCREEN * XI_POINT)
line("initial-r0", [left_origin, left_particle], stroke=ORANGE, lw=2.1, arrow=True)
line("current-r", [right_origin, right_particle], stroke=ORANGE, lw=2.1, arrow=True)
dot("initial-origin", left_origin, ink=INK, size=3.2)
dot("current-origin", right_origin, ink=INK, size=3.2)
dot("initial-particle", left_particle)
dot("current-particle", right_particle)
text("initial-particle-name", left_particle[0] + 35, left_particle[1] - 7, 60, r"$P_0$", ink=ORANGE)
text("current-particle-name", right_particle[0] + 43, right_particle[1] - 5, 85, r"$P(t)$", ink=ORANGE)
text("initial-r-label", left_origin[0] + 31, (left_origin[1] + left_particle[1]) / 2 + 4,
     50, r"$r_0$", ink=ORANGE)
text("current-r-label", right_origin[0] + 43, (right_origin[1] + right_particle[1]) / 2 + 5,
     65, r"$r(t)$", ink=ORANGE)

left_radial = add(left_rear, AX, 55)
right_radial = add(right_rear, AX, 55)
line("initial-radius", [left_radial, add(left_radial, UP, R0_SCREEN)], lw=1.9, arrow=True)
line("current-radius", [right_radial, add(right_radial, UP, RT_SCREEN)], lw=1.9, arrow=True)
text("initial-radius-label", left_radial[0] + 24, left_radial[1] - 60, 65, r"$R_0$", size=28)
text("current-radius-label", right_radial[0] + 30, right_radial[1] - 44, 80, r"$R(t)$", size=27)

text("proportional-label", 619, 176, 310, "比例径向收缩", size=27)
text("velocity", 619, 224, 340, r"$v(r,t)=\dfrac{R'(t)}{R(t)}r$", size=26, height=58)
line("shrink-direction", [(488, 287), (747, 287)], stroke=ORANGE, lw=3.2, arrow=True)
text("position-map", 619, 342, 345, r"$r(t)=\dfrac{R(t)}{R_0}r_0$", size=26, height=58)
text("velocity-sign", 619, 389, 300, r"$R'(t)<0,\quad v(r,t)<0\ (r>0)$", size=24)

text("surface-factor", 1001, 145, 420, r"表面梯度因子 $R(t)^{-1}$", size=25, ink=ORANGE)
surface_factor_point = add(add(right_rear, AX, 220), UP, RT_SCREEN)
line("surface-factor-leader", [(997, 169), (997, 211), surface_factor_point], stroke=ORANGE, lw=1.5)
dot("surface-factor-point", surface_factor_point, size=2.7)
text("interior-factor-label", 980, 344, 200, "内部扩散因子", size=24, ink=BLUE)
text("interior-factor", 980, 378, 165, r"$R(t)^{-2}$", size=28, ink=BLUE)

for prefix, rear, front in [("initial", left_rear, left_front), ("current", right_rear, right_front)]:
    p0, p1 = add(rear, UP, -160), add(front, UP, -160)
    line(prefix + "-length", [p0, p1], stroke=GRAY, both=True, lw=1.3)
    line(prefix + "-length-left-tick", [add(p0, UP, 10), add(p0, UP, -10)], stroke=GRAY, lw=1.2)
    line(prefix + "-length-right-tick", [add(p1, UP, 10), add(p1, UP, -10)], stroke=GRAY, lw=1.2)
    text(prefix + "-length-label", (p0[0] + p1[0]) / 2, 505, 300,
         r"$L=0.25\,\mathrm{m}$（不变）", size=24)

line("mapping-rule", [(55, 543), (1205, 543)], stroke=LIGHT, lw=1.1)
text("material-point-heading", 305, 583, 500, "同一材料点的相对位置不变", size=25)
text("material-point-invariant", 305, 634, 540,
     r"$\xi=\dfrac{r_0}{R_0}=\dfrac{r(t)}{R(t)}=\mathrm{const}$", size=27, height=60)
text("fixed-domain", 305, 688, 480, r"固定计算区间 $0\leq\xi\leq1$", size=24)

text("gradient-identity", 930, 585, 550,
     r"$\partial_r=\dfrac{1}{R(t)}\partial_\xi$", size=26, height=60)
text("diffusion-identity", 930, 659, 600,
     r"$\dfrac{1}{r}\partial_r(rD\partial_r)=\dfrac{1}{R^2(t)\xi}\partial_\xi(\xi D\partial_\xi)$",
     size=26, height=70)

ET.indent(mxfile, space="  ")
ET.ElementTree(mxfile).write(FIG / "fig_q4_coordinates.drawio", encoding="utf-8", xml_declaration=True)
parsed_cells = ET.parse(FIG / "fig_q4_coordinates.drawio").findall(".//mxCell")
assert len({c.get("id") for c in parsed_cells}) == len(parsed_cells)
stencil_count = 0
for c in parsed_cells:
    style = c.get("style", "")
    match = re.search(r"shape=stencil\(([^)]+)\)", style)
    if match:
        raw = zlib.decompress(base64.b64decode(match.group(1)), wbits=-15).decode()
        assert ET.fromstring(urllib.parse.unquote(raw)).tag == "shape"
        stencil_count += 1
assert 0 < AXIAL_FRACTION < 1 and 0 < XI_POINT < 1
assert math.isclose(math.dist(left_origin, left_particle) / R0_SCREEN,
                    math.dist(right_origin, right_particle) / RT_SCREEN, abs_tol=1e-12)
assert math.isclose(math.dist(left_rear, left_origin), math.dist(right_rear, right_origin), abs_tol=1e-12)
assert left_rear[1] == left_front[1] == right_rear[1] == right_front[1]
assert math.isclose(surface_factor_point[1], right_rear[1] - RT_SCREEN, abs_tol=1e-12)
preamble = r"""\documentclass[border=0pt]{standalone}
\usepackage[fontset=windows]{ctex}
\usepackage{amsmath}
\usepackage{tikz}
\usetikzlibrary{arrows.meta}
\pagestyle{empty}
\begin{document}
\begin{tikzpicture}[x=0.44pt,y=-0.44pt]
"""
(FIG / "source" / "fig_q4_coordinates.tex").write_text(
    preamble + rf"\path[use as bounding box] (0,0) rectangle ({WIDTH},{HEIGHT});" + "\n"
    + "\n".join(tikz) + "\n\\end{tikzpicture}\n\\end{document}\n", encoding="utf-8",
)
print("Created figures/fig_q4_coordinates.drawio and figures/source/fig_q4_coordinates.tex")
print(f"Editable objects: {len(root) - 2}; illustrative radius ratio: {RT_SCREEN / R0_SCREEN:.2f}")
print(f"Validated {stencil_count} embedded vector stencils and invariant material-point ratio")
print(f"Internal axial fraction: {AXIAL_FRACTION:.2f}; particle radial fraction: {XI_POINT:.2f}")
