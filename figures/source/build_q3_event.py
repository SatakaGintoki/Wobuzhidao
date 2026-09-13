"""Generate matching editable Draw.io and vector TikZ event-flow figures."""

from pathlib import Path
import re
import xml.etree.ElementTree as ET


FIG = Path(__file__).resolve().parents[1]
WIDTH, HEIGHT, UNIT_PT = 850, 900, 0.44
BLUE = "#4358C5"
ORANGE = "#D65244"
GRAY = "#B8B8B8"
INK = "#333333"
mxfile = ET.Element("mxfile", host="app.diagrams.net", agent="Codex", version="24.7.17")
diagram = ET.SubElement(mxfile, "diagram", id="q3-global-event", name="问题三全域达标事件")
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
bounds = {}


def color(hex_color):
    return "{rgb,255:red,%d;green,%d;blue,%d}" % tuple(
        int(hex_color[i:i + 2], 16) for i in (1, 3, 5)
    )


def mathjax(value):
    return re.sub(r"\$([^$]+)\$", lambda m: r"\(" + m.group(1) + r"\)", value)


def tex_label(x, y, value, size=24, ink=INK):
    font_pt = size * UNIT_PT
    tikz.append(
        r"\node[inner sep=0pt,outer sep=0pt,align=center,text=" + color(ink)
        + rf",font={{\fontsize{{{font_pt:.2f}}}{{{font_pt * 1.3:.2f}}}\selectfont}}]"
        + f" at ({x},{y}) " + "{" + value + "};"
    )


def node(name, x, y, w, h, title, detail=None, stroke=BLUE, fill="#EDF8F5",
         diamond=False, rounded=False, size=24, detail_size=23):
    bounds[name] = (x, y, w, h)
    mx_value = mathjax(title)
    if detail:
        mx_value += f'<br><span style="font-size:{detail_size}px">{mathjax(detail)}</span>'
    style = (
        f"shape={'rhombus' if diamond else 'rectangle'};html=1;whiteSpace=wrap;"
        "overflow=visible;align=center;verticalAlign=middle;spacing=0;"
        f"fontFamily=SimSun;fontSize={size};fontColor={INK};"
        f"strokeColor={stroke};fillColor={fill};strokeWidth=1.8;"
        f"rounded={int(rounded)};absoluteArcSize=1;arcSize=12;"
    )
    c = ET.SubElement(root, "mxCell", id=name, value=mx_value, style=style,
                      vertex="1", parent="1")
    ET.SubElement(c, "mxGeometry", x=str(x), y=str(y), width=str(w), height=str(h),
                  **{"as": "geometry"})
    opts = ["draw=" + color(stroke), "fill=" + color(fill), "line width=0.792pt"]
    if rounded:
        opts.append("rounded corners=2.64pt")
    if diamond:
        path = (f"({x + w / 2},{y}) -- ({x + w},{y + h / 2}) -- "
                f"({x + w / 2},{y + h}) -- ({x},{y + h / 2}) -- cycle")
    else:
        path = f"({x},{y}) rectangle ({x + w},{y + h})"
    tikz.append(r"\path[" + ",".join(opts) + "] " + path + ";")
    if detail:
        tex_label(x + w / 2, y + h / 2 - 17, title, size)
        tex_label(x + w / 2, y + h / 2 + 18, detail, detail_size)
    else:
        tex_label(x + w / 2, y + h / 2, title, size)


def endpoint(name, side):
    x, y, w, h = bounds[name]
    fx, fy = {"n": (0.5, 0), "s": (0.5, 1), "w": (0, 0.5), "e": (1, 0.5)}[side]
    return x + w * fx, y + h * fy, fx, fy


def edge(name, source, target, source_side="s", target_side="n", waypoints=(),
         stroke=BLUE):
    sx, sy, exit_x, exit_y = endpoint(source, source_side)
    tx, ty, entry_x, entry_y = endpoint(target, target_side)
    style = (
        "edgeStyle=none;rounded=0;html=1;endArrow=classic;endFill=1;endSize=9;"
        f"strokeColor={stroke};strokeWidth=2;exitX={exit_x};exitY={exit_y};"
        f"entryX={entry_x};entryY={entry_y};exitPerimeter=0;entryPerimeter=0;"
    )
    c = ET.SubElement(root, "mxCell", id=name, style=style, source=source, target=target,
                      edge="1", parent="1")
    g = ET.SubElement(c, "mxGeometry", relative="1", **{"as": "geometry"})
    if waypoints:
        a = ET.SubElement(g, "Array", **{"as": "points"})
        for x, y in waypoints:
            ET.SubElement(a, "mxPoint", x=str(x), y=str(y))
    points = [(sx, sy), *waypoints, (tx, ty)]
    tikz.append(
        r"\draw[draw=" + color(stroke)
        + r",line width=0.88pt,-{Latex[length=4pt,width=3.4pt]}] "
        + " -- ".join(f"({x},{y})" for x, y in points) + ";"
    )


def branch_label(name, x, y, value, ink):
    c = ET.SubElement(
        root, "mxCell", id=name, value=value, vertex="1", parent="1",
        style=("text;html=1;strokeColor=none;fillColor=none;align=center;"
               f"verticalAlign=middle;spacing=0;fontFamily=SimSun;fontSize=23;fontColor={ink};"),
    )
    ET.SubElement(c, "mxGeometry", x=str(x - 20), y=str(y - 14), width="40", height="28",
                  **{"as": "geometry"})
    tex_label(x, y, value, size=23, ink=ink)


node("input", 330, 30, 470, 82, "输入环境与初始状态",
     r"$T_a(t),\ C_a(t);\quad T(r,0),\ C(r,0)$", stroke=GRAY, fill="#F6F6F6", rounded=True)
node("integrate", 330, 143, 470, 84, r"联合求解 $T(r,t)$、$C(r,t)$",
     "环形有限体积 + 隐式 BDF")
node("maximum", 330, 259, 470, 82, "计算全域最大含水率",
     r"$M_h(t)=\max_i C_i(t)$")
node("crossing", 330, 363, 470, 154, "是否出现向下穿越？",
     r"$M_h(t):\ >0.15\ \longrightarrow\ \leq0.15$",
     stroke=ORANGE, fill="#FAE9E6", diamond=True, detail_size=22)
node("continue", 50, 410, 200, 60, "继续积分", stroke=GRAY, fill="#F6F6F6")
node("root", 330, 550, 470, 82, "局部精算并求根",
     r"$M_h(t_*)=0.15$")
node("report-time", 330, 664, 470, 96, "选取严格达标报告时刻",
     r"$t_{\mathrm{rep}}>t_*,\quad M_h(t_{\mathrm{rep}})<0.15$",
     stroke=ORANGE, fill="#FAE9E6")
node("verify", 330, 792, 470, 82, "网格、时间与收支复核",
     r"同一 $t_{\mathrm{rep}}$，以未舍入值核对达标", rounded=True, detail_size=22)

edge("input-to-integrate", "input", "integrate")
edge("integrate-to-maximum", "integrate", "maximum")
edge("maximum-to-crossing", "maximum", "crossing")
edge("crossing-no", "crossing", "continue", "w", "e", stroke=GRAY)
edge("continue-to-integrate", "continue", "integrate", "w", "w",
     waypoints=[(24, 440), (24, 185)], stroke=GRAY)
edge("crossing-yes", "crossing", "root", stroke=ORANGE)
edge("root-to-report", "root", "report-time")
edge("report-to-verify", "report-time", "verify", stroke=ORANGE)
branch_label("no-label", 290, 420, "否", INK)
branch_label("yes-label", 587, 534, "是", INK)

ET.indent(mxfile, space="  ")
ET.ElementTree(mxfile).write(FIG / "fig_flow_q3.drawio", encoding="utf-8", xml_declaration=True)
preamble = r"""\documentclass[border=0pt]{standalone}
\usepackage[fontset=windows]{ctex}
\usepackage{amsmath}
\usepackage{tikz}
\usetikzlibrary{arrows.meta}
\pagestyle{empty}
\begin{document}
\begin{tikzpicture}[x=0.44pt,y=-0.44pt]
"""
(FIG / "source" / "fig_flow_q3.tex").write_text(
    preamble + rf"\path[use as bounding box] (0,0) rectangle ({WIDTH},{HEIGHT});" + "\n"
    + "\n".join(tikz) + "\n\\end{tikzpicture}\n\\end{document}\n", encoding="utf-8",
)
print("Created figures/fig_flow_q3.drawio and figures/source/fig_flow_q3.tex")
print(f"Process nodes: {len(bounds)}; linked edges: 8")
