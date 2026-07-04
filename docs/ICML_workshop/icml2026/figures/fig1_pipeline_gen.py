#!/usr/bin/env python3
"""fig1_pipeline REV4 — SVG scaffold generator (SD4H ICML poster / LinkedIn).
Crisp vector text + exact LAYOUT SPEC coordinates. See fig1_prompt.md."""
import math, os, subprocess

W, H = 1600, 1000
HUES = ["#E23B33", "#F08A2D", "#F4C918", "#4CA43C",
        "#35BFD3", "#2E6FC9", "#7A3FB0", "#D23E97"]
# even angles (deg), red at top going clockwise
ANG = [90, 45, 0, -45, -90, -135, 180, 135]
FONT = 'font-family="Helvetica,Arial,sans-serif"'
S = []  # svg element buffer
def add(x): S.append(x)

def disc(cx, cy, r, fill, sw=2):
    return f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="{fill}" stroke="#333" stroke-width="{sw}"/>'

def text(x, y, s, size=20, w="bold", fill="#1a1a1a", anchor="middle"):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-weight="{w}" '
            f'text-anchor="{anchor}" fill="{fill}" {FONT}>{s}</text>')

def arrow(x1, y1, x2, y2, color="#333", w=3, dash=""):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{color}" stroke-width="{w}"{d} marker-end="url(#ah)"/>')

def hue_circle(cx, cy, R, warp=False, dr=22):
    """draw ring + 8 hue discs. warp=True => elliptical + angular dilation."""
    out = []
    if warp:
        rx, ry = R, R*0.78
        # ring path (ellipse, rotated slightly)
        out.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" '
                   f'transform="rotate(-12 {cx} {cy})" fill="none" stroke="#9aa" stroke-width="3"/>')
        for h, a in zip(HUES, ANG):
            phi = a + 34*math.sin(math.radians(a-20))   # angular dilation
            rr = math.radians(phi-12)
            x = cx + rx*math.cos(rr); y = cy - ry*math.sin(rr)
            out.append(disc(x, y, dr, h))
    else:
        out.append(f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="none" stroke="#9aa" stroke-width="3"/>')
        for h, a in zip(HUES, ANG):
            rr = math.radians(a)
            x = cx + R*math.cos(rr); y = cy - R*math.sin(rr)
            out.append(disc(x, y, dr, h))
    return "".join(out)

# ---------- defs ----------
add(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
add('<defs><marker id="ah" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto" '
    'markerUnits="strokeWidth"><path d="M0,0 L8,3 L0,6 z" fill="#333"/></marker>'
    '<marker id="ah2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto" '
    'markerUnits="strokeWidth"><path d="M0,0 L7,3 L0,6 z" fill="#555"/></marker></defs>')
add(f'<rect width="{W}" height="{H}" fill="#ffffff"/>')

# =================== TOP PANEL ===================
# (a) structural distortion : x 40-780
add(text(185, 60, "(a)  structural distortion", 22, "bold", anchor="middle"))
add(hue_circle(185, 250, 105, warp=False))
add(text(185, 400, "HC", 30, "bold"))
add(arrow(320, 250, 470, 250, w=4))
add(text(395, 235, "CVD distortion", 18, "bold"))
add(hue_circle(635, 250, 105, warp=True))
add(text(635, 400, "CVD", 30, "bold", fill="#b3261e"))

# (c) 2-component model : x 820-1560
add(text(1250, 60, "(c)  2-component cortical model", 22, "bold"))
mcx, mcy, mR = 1330, 255, 108
add(hue_circle(mcx, mcy, mR, warp=False, dr=18))
# two axes through center
for ang, lbl, lx, ly in [(28, "component 1", mcx+mR+70, mcy-70),
                         (118, "component 2", mcx-mR-70, mcy-70)]:
    rr = math.radians(ang); ex = mR+34
    x1 = mcx-ex*math.cos(rr); y1 = mcy+ex*math.sin(rr)
    x2 = mcx+ex*math.cos(rr); y2 = mcy-ex*math.sin(rr)
    add(f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" stroke="#222" '
        f'stroke-width="2.5" marker-start="url(#ah2)" marker-end="url(#ah2)"/>')
    add(text(lx, ly, lbl, 15, "bold", anchor="middle"))
# input icons feeding model (behavioral / neural)
# behavioral: two chips + double arrow
bx, by = 905, 175
add(f'<rect x="{bx-34}" y="{by-20}" width="34" height="40" fill="{HUES[0]}" stroke="#333"/>')
add(f'<rect x="{bx+8}" y="{by-20}" width="34" height="40" fill="{HUES[3]}" stroke="#333"/>')
add(f'<line x1="{bx-40}" y1="{by+34}" x2="{bx+48}" y2="{by+34}" stroke="#555" stroke-width="2.5" '
    'marker-start="url(#ah2)" marker-end="url(#ah2)"/>')
add(text(bx+4, by+58, "behavioral", 15, "bold"))
# neural: small circle + warped circle + distance arrows
nx, ny = 905, 330
add(f'<circle cx="{nx-18}" cy="{ny}" r="26" fill="none" stroke="#9aa" stroke-width="2.5"/>')
add(f'<ellipse cx="{nx+40}" cy="{ny}" rx="26" ry="19" fill="none" stroke="#9aa" stroke-width="2.5"/>')
for k in range(4):
    aa = math.radians(90+k*90)
    add(disc(nx-18+22*math.cos(aa), ny-22*math.sin(aa), 6, HUES[k*2]))
    add(disc(nx+40+22*math.cos(aa), ny-15*math.sin(aa), 6, HUES[k*2]))
add(f'<line x1="{nx-18}" y1="{ny-22}" x2="{nx-18}" y2="{ny+22}" stroke="#555" stroke-width="1.8" '
    'marker-start="url(#ah2)" marker-end="url(#ah2)"/>')
add(text(nx+8, ny+52, "neural", 15, "bold"))
# arrows from icons into model
add(arrow(bx+58, by+10, mcx-mR-30, mcy-30, w=2.5))
add(arrow(nx+70, ny, mcx-mR-30, mcy+30, w=2.5))

# divider
add(f'<line x1="40" y1="470" x2="1560" y2="470" stroke="#d0d0d0" stroke-width="2"/>')

# =================== BOTTOM PANEL ===================
BOX = [(40, 367, "#2E6FC9", "Response"),
       (437, 764, "#E1A32E", "Diagnose"),
       (834, 1161, "#7A3FB0", "Simulate"),
       (1231, 1558, "#4CA43C", "Correct")]
BODY_T, BODY_B, HDR_B = 560, 960, 620
for (x0, x1, col, name) in BOX:
    cx = (x0+x1)/2
    # body
    add(f'<rect x="{x0}" y="{HDR_B}" width="{x1-x0}" height="{BODY_B-HDR_B}" rx="16" '
        f'fill="#ffffff" stroke="{col}" stroke-width="2.5"/>')
    # header bar
    add(f'<rect x="{x0}" y="{BODY_T}" width="{x1-x0}" height="{HDR_B-BODY_T}" rx="16" fill="{col}"/>')
    add(f'<rect x="{x0}" y="{HDR_B-16}" width="{x1-x0}" height="16" fill="{col}"/>')
    add(text(cx, BODY_T+40, name, 26, "bold", fill="#ffffff"))

# --- B1 Response: brain + hue strip ---
c1 = 203
add(f'<path d="M{c1-55} 720 q-18 -34 14 -50 q6 -26 40 -22 q22 -22 48 -2 q30 -6 34 24 '
    f'q22 14 6 40 q10 24 -18 30 q-14 20 -40 8 q-24 14 -42 -6 q-30 2 -30 -22 z" '
    f'fill="#e9e6ef" stroke="#8a86a0" stroke-width="2.5"/>')
add(f'<path d="M{c1-30} 690 q20 20 0 44 M{c1+6} 682 q-14 26 8 48 M{c1+34} 694 q-18 18 2 40" '
    f'fill="none" stroke="#8a86a0" stroke-width="2"/>')
for i, h in enumerate(HUES):
    add(f'<rect x="{c1-96+i*24}" y="788" width="22" height="26" fill="{h}" stroke="#333" stroke-width="1"/>')
add(text(c1, 862, "fMRI hue responses", 17, "bold"))
add(text(c1, 886, "V1–hV4", 17, "bold"))

# --- B2 Diagnose: LOCO manifold + RDM ---
c2 = 600
# LOCO manifold (arc + dots + held-out)
add(f'<path d="M{c2-120} 700 Q{c2} 640 {c2+120} 700" fill="none" stroke="#666" stroke-width="2.5"/>')
loco_x = [c2-120, c2-80, c2-40, c2+40, c2+80, c2+120]
loco_h = [HUES[0],HUES[1],HUES[2],HUES[4],HUES[5],HUES[6]]
for xx, h in zip(loco_x, loco_h):
    t = (xx-(c2-120))/240.0
    yy = 700 - (1-4*(t-0.5)**2)*60
    add(disc(xx, yy, 9, h))
# held-out (green) lifted above dashed, arrow down to predicted spot
add(f'<circle cx="{c2}" cy="638" r="9" fill="none" stroke="{HUES[3]}" stroke-width="2.5" stroke-dasharray="3,3"/>')
add(arrow(c2, 650, c2, 686, color="#888", w=2, dash="4,3"))
add(disc(c2, 640-0, 0, "none"))  # noop keep
add(text(c2, 742, "leave-one-color-out", 16, "bold"))
# RDM : circle + warped circle + distance arrows
rc1x, rc2x, ry0 = c2-58, c2+58, 830
add(f'<circle cx="{rc1x}" cy="{ry0}" r="30" fill="none" stroke="#9aa" stroke-width="2"/>')
add(f'<ellipse cx="{rc2x}" cy="{ry0}" rx="30" ry="21" fill="none" stroke="#9aa" stroke-width="2"/>')
for k in range(4):
    aa = math.radians(45+k*90)
    add(disc(rc1x+25*math.cos(aa), ry0-25*math.sin(aa), 6, HUES[k*2]))
    add(disc(rc2x+25*math.cos(aa), ry0-17*math.sin(aa), 6, HUES[k*2]))
add(f'<line x1="{rc1x-18}" y1="{ry0-18}" x2="{rc1x+18}" y2="{ry0+18}" stroke="#555" stroke-width="1.8" '
    'marker-start="url(#ah2)" marker-end="url(#ah2)"/>')
add(f'<line x1="{rc2x-18}" y1="{ry0+15}" x2="{rc2x+18}" y2="{ry0-15}" stroke="#555" stroke-width="1.8" '
    'marker-start="url(#ah2)" marker-end="url(#ah2)"/>')
add(text(c2, 892, "pairwise distance (shared space)", 15, "bold"))

# --- B3 Simulate: HC circle -> model -> warped circle ---
c3 = 997
add(hue_circle(c3-95, 720, 46, warp=False, dr=9))
add(f'<rect x="{c3-30}" y="695" width="60" height="50" rx="8" fill="#efe8f7" stroke="#7A3FB0" stroke-width="2"/>')
add(text(c3, 725, "model", 13, "bold", fill="#7A3FB0"))
add(arrow(c3-45, 720, c3-32, 720, w=2.5))
add(arrow(c3+32, 720, c3+45, 720, w=2.5))
add(hue_circle(c3+95, 720, 46, warp=True, dr=9))
add(text(c3, 850, "simulate the", 20, "bold"))
add(text(c3, 876, "distortion", 20, "bold"))

# --- B4 Correct: dull -> lens -> vivid ---
c4 = 1394
dull = ["#9c8f6f","#a89670","#b0a05a","#8a9a72","#7fae b8".replace(" ",""),"#7f93c0","#9b83b0","#b083a0"]
for i, h in enumerate(HUES):
    add(f'<rect x="{c4-96+i*24}" y="672" width="22" height="24" fill="#a49c86" stroke="#333" stroke-width="1"/>')
add(f'<ellipse cx="{c4}" cy="760" rx="66" ry="26" fill="#eaf3ff" stroke="#4CA43C" stroke-width="2.5"/>')
add(text(c4, 766, "filter", 16, "bold", fill="#2f7d2a"))
add(arrow(c4, 700, c4, 734, w=2.5))
add(arrow(c4, 786, c4, 820, w=2.5))
for i, h in enumerate(HUES):
    add(f'<rect x="{c4-96+i*24}" y="824" width="22" height="24" fill="{h}" stroke="#333" stroke-width="1"/>')
add(text(c4, 892, "color-correction filter", 16, "bold"))

# --- inter-box arrows + labels ---
def gap_arrow(xa, xb, l1, l2=None):
    ym = 780
    add(arrow(xa+8, ym, xb-8, ym, w=3.5))
    xm = (xa+xb)/2
    if l2:
        add(text(xm, ym-24, l1, 13, "bold")); add(text(xm, ym-8, l2, 13, "bold"))
    else:
        add(text(xm, ym-12, l1, 13, "bold"))
gap_arrow(367, 437, "dimensionality", "reduction")
gap_arrow(764, 834, "inverse", "inference")
gap_arrow(1161, 1231, "invert")

add('</svg>')
svg = "\n".join(S)
here = os.path.dirname(os.path.abspath(__file__))
svg_path = os.path.join(here, "fig1_pipeline_v4.svg")
with open(svg_path, "w") as f:
    f.write(svg)
print("wrote", svg_path)

# try to rasterize
png_path = os.path.join(here, "fig1_pipeline_v4.png")
try:
    import cairosvg
    cairosvg.svg2png(url=svg_path, write_to=png_path, output_width=1600, output_height=1000, background_color="white")
    print("wrote", png_path, "(cairosvg)")
except Exception as e:
    for tool in (["rsvg-convert","-w","1600","-h","1000","-o",png_path,svg_path],
                 ["inkscape",svg_path,"--export-type=png","--export-filename="+png_path,"-w","1600"]):
        try:
            subprocess.run(tool, check=True, capture_output=True); print("wrote", png_path, "via", tool[0]); break
        except Exception:
            continue
    else:
        print("no rasterizer; SVG only. cairosvg err:", e)
