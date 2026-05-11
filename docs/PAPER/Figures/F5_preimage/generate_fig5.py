"""
Figure 5: The 2-component model yields a bijective stimulus-space filter for both CVD subjects,
          while Machado fails for sub-09 due to arc compression.

Panel A: Hue correction vectors (|δθ|) for each of the 8 training hues — sub-08 and sub-09.
Panel B: Arc collapse comparison — Machado vs 2-component pre-image for sub-09.
Panel C: Filter individuality — per-color correction magnitudes show sub-08 corrects 2-3× more
         than sub-09, with opposite signs at hues 5-8 (cyan→magenta arc).

Data source:
  preimage_2component/sub-{08,09}_V4_2component_preimage.json  (delta_preimage, residuals, stimulus_angles_cielab, preimage_angles)
  preimage/sub-09_V4_machado_1way_preimage.json               (delta_preimage, residuals, preimage_angles)
"""

import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch
from matplotlib.gridspec import GridSpec
import warnings
warnings.filterwarnings("ignore")

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE = ("/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/"
        "Projects/colorBlind_analysis/analysis/future_phase2_filter_optimization/results")

P08_2C  = f"{BASE}/fits/preimage_2component/sub-08_V4_2component_preimage.json"
P09_2C  = f"{BASE}/fits/preimage_2component/sub-09_V4_2component_preimage.json"
P09_MCH = f"{BASE}/fits/preimage/sub-09_V4_machado_1way_preimage.json"

OUT_DIR = ("/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/"
           "Projects/colorBlind_analysis/docs/PAPER/Figures/F5_preimage")

# ── Load data ─────────────────────────────────────────────────────────────────
def load(path):
    with open(path) as f:
        return json.load(f)

d08 = load(P08_2C)
d09 = load(P09_2C)
m09 = load(P09_MCH)

# ── Constants ─────────────────────────────────────────────────────────────────
HUE_NAMES   = ["Red", "Orange", "Yellow", "Green", "Cyan", "Blue", "Purple", "Magenta"]
# Perceptually motivated CIELab hue ring colors for 8 uniform stimuli (L=75, C=40)
# Approximate display-sRGB values for the 8 hues at equal 45° spacing
HUE_COLORS_STIM = [
    "#E84040",   # red    (0°)
    "#E07830",   # orange (45°)
    "#B0A000",   # yellow (90°)
    "#28A828",   # green  (135°)
    "#00A8B0",   # cyan   (180°)
    "#2060D8",   # blue   (225°)
    "#7828D0",   # purple (270°)
    "#C83090",   # magenta(315°)
]

# Subject colors (warm orange = sub-08 deutan, teal = sub-09 protan)
C08 = "#E07840"   # warm orange
C09 = "#2AADA8"   # teal
CGRAY = "#888888" # Machado

N_COLORS = 8
stim_deg  = np.array(d08["stimulus_angles_cielab"])  # 0,45,...,315
theta_rad = np.deg2rad(stim_deg)

delta08 = np.array(d08["delta_preimage"])   # signed corrections sub-08
delta09 = np.array(d09["delta_preimage"])   # signed corrections sub-09

preimage08 = np.array(d08["preimage_angles"])
preimage09 = np.array(d09["preimage_angles"])

machado_preimage = np.array(m09["preimage_angles"])
machado_residuals = np.array(m09["residuals"])
delta_mch = np.array(m09["delta_preimage"])

# Machado exact pass/fail per color
MACHADO_PASS_THRESH = 1.0   # degrees; residuals >1° = fail
mch_fail = machado_residuals > MACHADO_PASS_THRESH  # 4 fail

# ── Global style ───────────────────────────────────────────────────────────────
plt.rcParams.update({
    "font.family":       "sans-serif",
    "font.sans-serif":   ["Helvetica", "Arial", "DejaVu Sans"],
    "font.size":         7,
    "axes.titlesize":    8,
    "axes.labelsize":    7,
    "xtick.labelsize":   6.5,
    "ytick.labelsize":   6.5,
    "axes.linewidth":    0.7,
    "xtick.major.width": 0.7,
    "ytick.major.width": 0.7,
    "xtick.major.size":  3,
    "ytick.major.size":  3,
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "legend.fontsize":   6.5,
    "legend.frameon":    False,
    "figure.dpi":        300,
    "savefig.dpi":       300,
    "savefig.bbox":      "tight",
    "savefig.pad_inches": 0.05,
    "pdf.fonttype":      42,
    "ps.fonttype":       42,
})

# Figure dimensions: 180 mm wide × ~120 mm tall
FIG_W = 180 / 25.4   # 7.087 in
FIG_H = 120 / 25.4   # 4.72 in

fig = plt.figure(figsize=(FIG_W, FIG_H))

# Layout: 3 panels A | B | C
# A is wider (correction bars), B and C are equal
gs = GridSpec(1, 3, figure=fig,
              left=0.07, right=0.97, top=0.93, bottom=0.18,
              wspace=0.52,
              width_ratios=[1.35, 1.25, 1.1])

ax_a = fig.add_subplot(gs[0])   # Panel A — correction bar chart
ax_b = fig.add_subplot(gs[1])   # Panel B — arc collapse (polar-ish)
ax_c = fig.add_subplot(gs[2])   # Panel C — filter individuality

# ─────────────────────────────────────────────────────────────────────────────
# PANEL A — Correction vectors |δθ| per hue, both subjects
# ─────────────────────────────────────────────────────────────────────────────
x = np.arange(N_COLORS)
bar_w = 0.35

abs08 = np.abs(delta08)
abs09 = np.abs(delta09)

# Bars with hue-face color, subject-edge color
for i in range(N_COLORS):
    # sub-08 bar (left)
    b08 = ax_a.bar(i - bar_w/2, abs08[i], bar_w,
                   facecolor=HUE_COLORS_STIM[i],
                   edgecolor=C08, linewidth=1.4, alpha=0.9,
                   zorder=3)
    # sub-09 bar (right) — hatched
    b09 = ax_a.bar(i + bar_w/2, abs09[i], bar_w,
                   facecolor=HUE_COLORS_STIM[i],
                   edgecolor=C09, linewidth=1.4, alpha=0.6,
                   hatch="///", zorder=3)

    # Sign annotations (+ or –) above each bar
    sign08 = "+" if delta08[i] > 0 else "−"
    sign09 = "+" if delta09[i] > 0 else "−"
    ax_a.text(i - bar_w/2, abs08[i] + 1.5, sign08,
              ha="center", va="bottom", fontsize=5.5, color=C08, fontweight="bold")
    ax_a.text(i + bar_w/2, abs09[i] + 1.5, sign09,
              ha="center", va="bottom", fontsize=5.5, color=C09, fontweight="bold")

ax_a.set_xticks(x)
ax_a.set_xticklabels(HUE_NAMES, rotation=35, ha="right", fontsize=6)
ax_a.set_ylabel("Correction magnitude |δθ| (°)", fontsize=7)
ax_a.set_ylim(0, 120)
ax_a.set_yticks([0, 30, 60, 90, 120])
ax_a.set_xlim(-0.55, N_COLORS - 0.45)
ax_a.axhline(0, color="black", linewidth=0.5, zorder=1)

# Dashed reference lines at mean for each subject
ax_a.axhline(np.mean(abs08), color=C08, linewidth=1.0, linestyle="--", alpha=0.7, zorder=2)
ax_a.axhline(np.mean(abs09), color=C09, linewidth=1.0, linestyle="--", alpha=0.7, zorder=2)
# Small labels for the mean lines (right side)
ax_a.text(N_COLORS - 0.4, np.mean(abs08) + 1.0, f"x̄={np.mean(abs08):.0f}°",
          ha="right", va="bottom", fontsize=5, color=C08)
ax_a.text(N_COLORS - 0.4, np.mean(abs09) + 1.0, f"x̄={np.mean(abs09):.0f}°",
          ha="right", va="bottom", fontsize=5, color=C09)

# Legend
legend_elements = [
    mpatches.Patch(facecolor="white", edgecolor=C08, linewidth=1.4,
                   label="sub-08 deutan (β$_s$=38°, β$_c$=−14°)"),
    mpatches.Patch(facecolor="white", edgecolor=C09, linewidth=1.4, hatch="///",
                   label="sub-09 protan (β$_s$=6°, β$_c$=−22°)"),
]
ax_a.legend(handles=legend_elements, loc="upper right", fontsize=5.5,
            handlelength=1.2, handleheight=1.2, labelspacing=0.4)

ax_a.set_title("A  Hue correction magnitudes", loc="left", fontsize=8, fontweight="bold",
               pad=4)
# Put exactness note below the legend, not overlapping
ax_a.text(0.98, 0.57, "Both: 8/8 exact\nresidual < 0.001°",
          transform=ax_a.transAxes, fontsize=5.5, va="top", ha="right",
          color="#444444",
          bbox=dict(boxstyle="round,pad=0.25", facecolor="#f0f8f0", edgecolor="#aaccaa",
                    linewidth=0.6))

# ─────────────────────────────────────────────────────────────────────────────
# PANEL B — Arc collapse: Machado vs 2-component for sub-09
# Shows the mapping stim θ → pre-image θ on two circular number lines
# ─────────────────────────────────────────────────────────────────────────────
# Visual: Horizontal scatter/mapping lines showing collapse
# X-axis = stimulus angle (0–360°), color-coded by hue
# Two rows: Machado pre-images (top), 2-comp pre-images (bottom)
# Lines connect same stimulus to each model's pre-image

ax_b.set_aspect("auto")

STIM = stim_deg
PREIMG_MCH = machado_preimage
PREIMG_2C  = preimage09

# Y positions for two "rows"
Y_MCH  = 0.72
Y_2C   = 0.28
Y_STIM = 0.50   # stimulus row in middle

row_lw = 2.0

# Shade the arc that Machado collapses (approx stimulus range 135–270° → all land at 127°)
ax_b.axvspan(120, 280, ymin=0.65, ymax=1.0, color="#ffdddd", alpha=0.28, zorder=1)
ax_b.text(200, Y_MCH + 0.13, "Arc collapse\n(135°–270°)", ha="center",
          fontsize=5, color="#cc3333", style="italic")

# Draw stimulus points at center row
for i in range(N_COLORS):
    ax_b.scatter(STIM[i], Y_STIM, s=40, color=HUE_COLORS_STIM[i],
                 zorder=5, linewidths=0.5, edgecolors="white")

# Draw Machado pre-image points + connection lines
STIM_WRAPPED = np.array([s % 360 for s in STIM])
PMCH_WRAPPED = np.array([p % 360 for p in PREIMG_MCH])
P2C_WRAPPED  = np.array([p % 360 for p in PREIMG_2C])

for i in range(N_COLORS):
    color_i = HUE_COLORS_STIM[i]
    alpha_i = 0.4 if mch_fail[i] else 0.85

    # Machado pre-image (top row)
    marker_mch = "x" if mch_fail[i] else "o"
    ms_mch = 40 if mch_fail[i] else 35
    ax_b.scatter(PMCH_WRAPPED[i], Y_MCH, s=ms_mch, marker=marker_mch,
                 color=CGRAY if mch_fail[i] else color_i,
                 linewidths=1.3 if mch_fail[i] else 0.5,
                 edgecolors="darkred" if mch_fail[i] else "white",
                 zorder=5, alpha=alpha_i)

    # Thin connector from stim → machado preimage
    ax_b.plot([STIM[i], PMCH_WRAPPED[i]], [Y_STIM, Y_MCH],
              color=CGRAY, linewidth=0.7, alpha=0.5, linestyle="--", zorder=3)

    # 2-component pre-image (bottom row)
    ax_b.scatter(P2C_WRAPPED[i], Y_2C, s=35, marker="o",
                 color=color_i, linewidths=0.5, edgecolors="white",
                 zorder=5)

    # Thin connector from stim → 2-comp preimage
    ax_b.plot([STIM[i], P2C_WRAPPED[i]], [Y_STIM, Y_2C],
              color=C09, linewidth=0.7, alpha=0.55, linestyle="-", zorder=3)

# Row labels (placed at left, just outside the axes)
ax_b.text(-12, Y_MCH,  "Machado\npre-image", va="center", ha="right", fontsize=6,
          color=CGRAY, fontweight="bold", linespacing=1.2)
ax_b.text(-12, Y_STIM, "Stimulus\n(original)", va="center", ha="right", fontsize=6,
          color="#333333", linespacing=1.2)
ax_b.text(-12, Y_2C,   "2-comp\npre-image",  va="center", ha="right", fontsize=6,
          color=C09, fontweight="bold", linespacing=1.2)

# Highlight the 3-way collapse of Machado in the cyan-blue region
# Residuals 3,4,5 all collapsed to ~127°
collapse_x = np.mean(PMCH_WRAPPED[[3, 4, 5]])
ax_b.annotate("3 hues →\n1 point",
              xy=(PMCH_WRAPPED[4], Y_MCH),
              xytext=(PMCH_WRAPPED[4] + 25, Y_MCH + 0.11),
              fontsize=5.5, color="darkred",
              arrowprops=dict(arrowstyle="->", color="darkred", lw=0.9,
                              connectionstyle="arc3,rad=0.15"),
              ha="left")
# Draw a red ellipse around the collapsed cluster
from matplotlib.patches import Ellipse
ell = Ellipse((PMCH_WRAPPED[4], Y_MCH), width=28, height=0.08,
              edgecolor="darkred", facecolor="none", linewidth=1.0,
              linestyle="--", zorder=6)
ax_b.add_patch(ell)

# Sub-09 residual summary annotation
n_fail_mch = int(np.sum(mch_fail))
n_pass_mch = N_COLORS - n_fail_mch
ax_b.text(182, 0.085, f"Machado: {n_pass_mch}/8 exact (× = residual > 1°)",
          fontsize=5.5, color="#666666", ha="center")
ax_b.text(182, 0.01, f"2-component: 8/8 exact (residual < 0.001°)",
          fontsize=5.5, color=C09, ha="center")

# Formatting
ax_b.set_xlim(-15, 365)
ax_b.set_ylim(-0.12, 0.97)
ax_b.set_xlabel("Hue angle θ (°, CIELab)", fontsize=7)
ax_b.set_xticks([0, 90, 180, 270, 360])
ax_b.set_xticklabels(["0°", "90°", "180°", "270°", "360°"])
ax_b.set_yticks([])
ax_b.spines["left"].set_visible(False)
ax_b.spines["bottom"].set_position(("data", -0.12))

ax_b.set_title("B  Arc collapse: sub-09 pre-image mapping", loc="left", fontsize=8,
               fontweight="bold", pad=4)

# ─────────────────────────────────────────────────────────────────────────────
# PANEL C — Filter individuality
# Shows |δθ| per hue for both subjects (line plot), and signs
# Highlights where corrections diverge in sign (hues 5–8)
# ─────────────────────────────────────────────────────────────────────────────
ax_c_r = ax_c   # reuse axes

x_pos = np.arange(N_COLORS)

# Signed bar plot: sub-08 above 0 (negative → downward), sub-09 separately
# Use a mirrored lollipop/signed bar approach
for i in range(N_COLORS):
    # Draw signed correction as bars from 0
    ax_c_r.bar(i - 0.18, delta08[i], 0.30,
               facecolor=HUE_COLORS_STIM[i], edgecolor=C08, linewidth=1.3,
               alpha=0.85, zorder=3)
    ax_c_r.bar(i + 0.18, delta09[i], 0.30,
               facecolor=HUE_COLORS_STIM[i], edgecolor=C09, linewidth=1.3,
               alpha=0.55, hatch="///", zorder=3)

# Highlight sign-divergent region (hues 5-8, index 4-7)
ax_c_r.axvspan(3.45, 7.55, color="#ffe8c0", alpha=0.35, zorder=0,
               label="Opposite signs (sub-08 vs sub-09)")
ax_c_r.text(5.5, 18, "Opposite\ncorrection\ndirections",
            ha="center", va="bottom", fontsize=5.5, color="#996600")

ax_c_r.axhline(0, color="black", linewidth=0.7, zorder=2)

# Reference lines at mean
ax_c_r.axhline(np.mean(delta08[delta08 > 0]) if np.any(delta08 > 0) else 0,
               color=C08, linewidth=0, alpha=0)  # skip — too noisy
# Mark zero line clearly
ax_c_r.set_yticks([-120, -90, -60, -30, 0, 30])
ax_c_r.set_ylim(-120, 35)

ax_c_r.set_xticks(x_pos)
ax_c_r.set_xticklabels(HUE_NAMES, rotation=35, ha="right", fontsize=6)
ax_c_r.set_ylabel("Signed correction δθ (°)", fontsize=7)
ax_c_r.set_xlim(-0.55, N_COLORS - 0.45)

# Legend
leg_c = [
    mpatches.Patch(facecolor="white", edgecolor=C08, linewidth=1.3, label="sub-08 deutan"),
    mpatches.Patch(facecolor="white", edgecolor=C09, linewidth=1.3, hatch="///",
                   label="sub-09 protan"),
    mpatches.Patch(facecolor="#ffe8c0", edgecolor="none", alpha=0.6,
                   label="Sign disagreement"),
]
ax_c_r.legend(handles=leg_c, loc="lower right", fontsize=5.5,
              handlelength=1.2)

# Cosine similarity annotation
cos_sim = np.dot(delta08, delta09) / (np.linalg.norm(delta08) * np.linalg.norm(delta09))
sign_agree = int(np.sum(np.sign(delta08) == np.sign(delta09)))
ax_c_r.text(0.02, 0.98,
            f"Sub-08 vs sub-09\nfilter cosine sim. = {cos_sim:.2f}\n{sign_agree}/8 sign agreements",
            transform=ax_c_r.transAxes, fontsize=5.5, va="top", ha="left",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#f5f5f5",
                      edgecolor="#cccccc", linewidth=0.6))

ax_c_r.set_title("C  Individual filter profiles", loc="left", fontsize=8,
                 fontweight="bold", pad=4)

# Global figure title intentionally removed — belongs in manuscript caption only

# ─────────────────────────────────────────────────────────────────────────────
# Save
# ─────────────────────────────────────────────────────────────────────────────
out_png = f"{OUT_DIR}/fig5_output.png"
out_pdf = f"{OUT_DIR}/fig5_output.pdf"

fig.savefig(out_png, dpi=300, bbox_inches="tight")
fig.savefig(out_pdf, bbox_inches="tight")
print(f"Saved: {out_png}")
print(f"Saved: {out_pdf}")

# ─────────────────────────────────────────────────────────────────────────────
# Sanity check printout
# ─────────────────────────────────────────────────────────────────────────────
print()
print("── Data sanity check ──────────────────────────────────────")
print(f"sub-08  beta=({d08['phase_a_params'][0]}, {d08['phase_a_params'][1]})")
print(f"        mean|δ|={np.mean(np.abs(delta08)):.1f}°  max={np.max(np.abs(delta08)):.1f}°")
print(f"        exact_pass={d08['tier1_model_consistent']['exact_pass']}")
print(f"        n_residuals<0.001: {np.sum(np.array(d08['residuals'])<0.001)}/8")
print()
print(f"sub-09  beta=({d09['phase_a_params'][0]}, {d09['phase_a_params'][1]})")
print(f"        mean|δ|={np.mean(np.abs(delta09)):.1f}°  max={np.max(np.abs(delta09)):.1f}°")
print(f"        exact_pass={d09['tier1_model_consistent']['exact_pass']}")
print(f"        n_residuals<0.001: {np.sum(np.array(d09['residuals'])<0.001)}/8")
print()
print(f"Machado sub-09  exact_pass={m09['tier1_model_consistent']['exact_pass']}")
print(f"        n_residuals<1°: {np.sum(machado_residuals<1)}/8  (n_fail={np.sum(mch_fail)})")
print()
print(f"sub-08 vs sub-09 cosine similarity: {cos_sim:.3f}")
print(f"Sign agreements: {sign_agree}/8")
