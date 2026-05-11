#!/usr/bin/env python3
"""
generate_fig1.py — Figure 1 for CVD fMRI paper (v2)
=====================================================
Panels:
  A  Paradigm: 8-hue DKL wheel + RSVP trial sequence
  B  Real ROI flatmap: V1/V2/V3/hV4 on inflated brain
     (nilearn + VTPM Wang 2015 maxprob atlas)
  C  Analysis pipeline: image-based, 5 mini-panels with captions
     [SRM colour space] → [LORO] → [LOCO] → [2-comp model] → [Filter]

Run: conda run -n srm python generate_fig1.py
"""

import io
import warnings
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Wedge, Ellipse
from matplotlib.colors import ListedColormap
from pathlib import Path

warnings.filterwarnings("ignore")

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE   = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis')
OUT    = Path(__file__).parent
ATLAS  = BASE / 'ProbAtlas_v4' / 'subj_vol_all'

FIG2   = BASE / 'docs/PAPER/Figures/F2_loro_loco/fig2_output.png'
FIG4   = BASE / 'docs/PAPER/Figures/F4_twocomp/fig4_output.png'
FIG5   = BASE / 'docs/PAPER/Figures/F5_preimage/fig5_output.png'
CEMB   = BASE / 'analysis/phase1_procrustes_decoding/results/visualization/color_space_embedding_01_V4.png'

# ── STIM_LAB colours ───────────────────────────────────────────────────────────
COLOR_LAB = [
    [59.90,  62.69,   3.78],  # Red
    [64.20,  49.20,  45.58],  # Orange
    [57.27,  13.06,  41.69],  # Yellow
    [69.08, -55.02,  47.38],  # Green
    [74.61, -41.33,  -4.89],  # Cyan
    [69.14, -11.45, -40.91],  # Blue
    [60.68,  19.18, -54.13],  # Purple
    [60.17,  46.82, -40.31],  # Magenta
]
HUE_NAMES = ["Red", "Orange", "Yellow", "Green", "Cyan", "Blue", "Purple", "Magenta"]

def _lab2rgb(L, a, b):
    y = (L + 16)/116; x = a/500 + y; z = y - b/200
    xyz = np.array([x, y, z])
    xyz = np.where(xyz > 0.206893, xyz**3, (xyz - 16/116)/7.787)
    xyz *= [0.95047, 1.0, 1.08883]
    M = np.array([[3.2406, -1.5372, -0.4986],
                  [-0.9689,  1.8758,  0.0415],
                  [0.0557, -0.2040,  1.0570]])
    rgb = M @ xyz
    rgb = np.where(rgb <= 0.0031308, 12.92*rgb, 1.055*rgb**(1/2.4) - 0.055)
    return tuple(np.clip(rgb, 0, 1))

STIM_RGB  = [_lab2rgb(*c) for c in COLOR_LAB]
ROI_COLS  = {'V1': '#1a6faf', 'V2': '#4ca3dd', 'V3': '#92c5de', 'hV4': '#d73027'}
STAGE_COL = {'A': '#2166ac', 'B': '#4dac26', 'C': '#d73027'}

# ── Figure geometry ────────────────────────────────────────────────────────────
MM = 1/25.4
FIG_W, FIG_H = 180*MM, 165*MM

plt.rcParams.update({
    "font.family":  "Arial",
    "font.size":    8,
    "pdf.fonttype": 42,
    "ps.fonttype":  42,
    "figure.dpi":   300,
})

fig = plt.figure(figsize=(FIG_W, FIG_H))
gs  = fig.add_gridspec(
    2, 2,
    left=0.03, right=0.98, top=0.97, bottom=0.03,
    hspace=0.30, wspace=0.20,
    height_ratios=[1.0, 1.0],
    width_ratios=[1.0, 1.0],
)
ax_a = fig.add_subplot(gs[0, 0])
ax_b = fig.add_subplot(gs[0, 1])
ax_c = fig.add_subplot(gs[1, :])
for ax in [ax_a, ax_b, ax_c]:
    ax.set_axis_off()
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)

def _plabel(ax, letter, x=-0.03, y=1.04):
    ax.text(x, y, letter, transform=ax.transAxes,
            fontsize=10, fontweight="bold", va="top", ha="left")


# =============================================================================
# PANEL A — Paradigm (DKL hue wheel + RSVP)
# =============================================================================
ax = ax_a
WCX, WCY = 0.24, 0.52
ROUT, RIN = 0.185, 0.105
DTHETA = 360 / 8

for i, rgb in enumerate(STIM_RGB):
    a_s = 90 - i*DTHETA
    a_e = a_s - DTHETA
    ax.add_patch(Wedge((WCX, WCY), ROUT, a_e, a_s,
                        width=ROUT-RIN, transform=ax.transAxes,
                        facecolor=rgb, edgecolor="white", linewidth=0.8,
                        clip_on=False, zorder=3))
    a_mid = np.deg2rad((a_s + a_e)/2)
    extra = {1: 0.025, 2: 0.022}.get(i, 0.0)
    lr = ROUT + 0.075 + extra
    lx, ly = WCX + lr*np.cos(a_mid), WCY + lr*np.sin(a_mid)
    ha = "left" if lx > WCX+0.01 else ("right" if lx < WCX-0.01 else "center")
    va = "bottom" if ly > WCY+0.01 else ("top" if ly < WCY-0.01 else "center")
    ax.text(lx, ly, HUE_NAMES[i], transform=ax.transAxes,
            fontsize=5.5, ha=ha, va=va, color="#333333")

ax.add_patch(plt.Circle((WCX, WCY), RIN*0.96, transform=ax.transAxes,
                          facecolor="white", edgecolor="none", zorder=4, clip_on=False))
ax.text(WCX, WCY, "DKL\nhue\nwheel", transform=ax.transAxes,
        fontsize=5.5, ha="center", va="center", color="#555555",
        linespacing=1.3, zorder=5)
ax.text(WCX, WCY - ROUT - 0.06,
        "8 isoluminant hues\n(DKL space, 45° spacing)",
        transform=ax.transAxes, fontsize=5.5,
        ha="center", va="top", color="#333333", style="italic", linespacing=1.3)
ax.plot([0.47, 0.47], [0.06, 0.96], transform=ax.transAxes,
        color="#e0e0e0", lw=0.5, clip_on=False)

SEQ_X0, SEQ_CY = 0.52, 0.56
SQ_W, SQ_H, SQ_GAP = 0.068, 0.092, 0.010
ax.text(SEQ_X0-0.07, SEQ_CY+SQ_H/2+0.05, "Fixation",
        transform=ax.transAxes, fontsize=6, ha="center", va="bottom", color="#555555")
ax.text(SEQ_X0-0.07, SEQ_CY, "+", transform=ax.transAxes,
        fontsize=14, ha="center", va="center", color="black")
ax.annotate("", xy=(SEQ_X0+0.01, SEQ_CY), xytext=(SEQ_X0-0.025, SEQ_CY),
            xycoords="axes fraction",
            arrowprops=dict(arrowstyle="-|>", color="#777777", lw=0.8))
for k, idx in enumerate([0, 3, 1, 6, 4]):
    x0 = SEQ_X0 + k*(SQ_W+SQ_GAP)
    ax.add_patch(FancyBboxPatch((x0, SEQ_CY-SQ_H/2), SQ_W, SQ_H,
                                 boxstyle="round,pad=0.004",
                                 transform=ax.transAxes,
                                 facecolor=STIM_RGB[idx], edgecolor="none",
                                 clip_on=False, zorder=3))
ax.text(SEQ_X0 + 5*(SQ_W+SQ_GAP)+0.005, SEQ_CY, "…",
        transform=ax.transAxes, fontsize=10, va="center", color="#888888")
brace_y = SEQ_CY - SQ_H/2 - 0.045
ax.annotate("", xy=(SEQ_X0, brace_y), xytext=(SEQ_X0+SQ_W, brace_y),
            xycoords="axes fraction",
            arrowprops=dict(arrowstyle="<->", color="#666666", lw=0.7))
ax.text((SEQ_X0 + SEQ_X0+SQ_W)/2, brace_y-0.03, "1 trial",
        transform=ax.transAxes, fontsize=5.5, ha="center", va="top", color="#666666")
mid_x = SEQ_X0 + 2.0*(SQ_W+SQ_GAP)
top_y = SEQ_CY + SQ_H/2 + 0.06
ax.text(mid_x, top_y, "6 runs × 8 colours / run",
        transform=ax.transAxes, fontsize=6.5, ha="center", va="bottom", color="#333333")
ax.text(mid_x, top_y+0.10, "RSVP — detect oddball target",
        transform=ax.transAxes, fontsize=5.5, ha="center", va="bottom",
        color="#555555", style="italic")
ax.text(0.50, 0.06, "HC: sub-01–07 (N=7)     CVD: sub-08 deutan, sub-09 protan",
        transform=ax.transAxes, fontsize=5.5, ha="center", va="bottom", color="#555555")
_plabel(ax, "A", x=-0.03, y=1.04)


# =============================================================================
# PANEL B — Real ROI flatmap (nilearn + VTPM maxprob atlas)
# =============================================================================
def _render_roi_surface(atlas_dir):
    """Return RGBA array of inflated left-hemisphere posterior view with V1–hV4 coloured.

    Uses perc_VTPM probabilistic atlas (Wang et al. 2015):
      V1 = roi1 (V1v) + roi2 (V1d), V2 = roi3+roi4, V3 = roi5+roi6, hV4 = roi7
    """
    import nibabel as nib
    from nilearn import datasets, surface, plotting

    fsavg = datasets.fetch_surf_fsaverage('fsaverage5')
    n_verts = 10242  # fsaverage5 left hemisphere

    composite = np.zeros(n_verts, dtype=float)
    affine_ref = None

    for roi_val, roi_nums in [(1, [1, 2]), (2, [3, 4]), (3, [5, 6]), (4, [7])]:
        prob_max = None
        for rn in roi_nums:
            img = nib.load(atlas_dir / f'perc_VTPM_vol_roi{rn}_lh.nii.gz')
            d = img.get_fdata().astype(np.float32)
            prob_max = d if prob_max is None else np.maximum(prob_max, d)
            affine_ref = img.affine
        prob_img = nib.Nifti1Image(prob_max, affine_ref)
        tex = surface.vol_to_surf(
            prob_img, fsavg['pial_left'],
            inner_mesh=fsavg['white_left'],
            interpolation='linear', radius=5.0,
        )
        composite[tex > 10] = float(roi_val)   # 10 % probability threshold

    composite[composite < 0.5] = np.nan         # non-ROI → transparent over background

    # Discrete 4-colour map: V1 blue → V2 sky → V3 pale → hV4 red
    cmap = ListedColormap([ROI_COLS['V1'], ROI_COLS['V2'],
                           ROI_COLS['V3'], ROI_COLS['hV4']])

    surf_fig = plotting.plot_surf_stat_map(
        fsavg['infl_left'], composite,
        hemi='left', view='posterior',
        bg_map=fsavg['sulc_left'],
        bg_on_data=True, darkness=0.45,
        cmap=cmap, vmin=0.5, vmax=4.5,
        colorbar=False, title='',
    )
    buf = io.BytesIO()
    surf_fig.savefig(buf, format='png', dpi=180,
                     bbox_inches='tight', facecolor='white')
    buf.seek(0)
    arr = plt.imread(buf)
    plt.close(surf_fig)
    plt.close('all')
    return arr


def _autocrop(arr, threshold=0.98, pad_frac=0.04):
    """Crop whitespace from a rendered RGBA/RGB array."""
    gray = np.mean(arr[:, :, :3], axis=2)
    not_bg = gray < threshold
    rows = np.any(not_bg, axis=1)
    cols = np.any(not_bg, axis=0)
    if not rows.any():
        return arr
    rmin, rmax = np.where(rows)[0][[0, -1]]
    cmin, cmax = np.where(cols)[0][[0, -1]]
    h, w = arr.shape[:2]
    pad_r = max(4, int((rmax - rmin) * pad_frac))
    pad_c = max(4, int((cmax - cmin) * pad_frac))
    return arr[max(0, rmin-pad_r):min(h, rmax+pad_r),
               max(0, cmin-pad_c):min(w, cmax+pad_c)]


ax = ax_b
print("Panel B: rendering nilearn surface…")
try:
    roi_arr = _autocrop(_render_roi_surface(ATLAS))
    ax.imshow(roi_arr, aspect='auto',
              extent=[0.05, 0.95, 0.10, 0.97],
              transform=ax.transAxes, interpolation='bilinear', zorder=2)
    print("  Surface render OK.")
except Exception as exc:
    print(f"  nilearn render failed ({exc}); using schematic fallback.")
    # ── Schematic fallback ──────────────────────────────────────────────────
    ax.add_patch(Ellipse((0.50, 0.52), 0.80, 0.72,
                          transform=ax.transAxes,
                          facecolor="#f2ede8", edgecolor="#999999",
                          linewidth=0.9, clip_on=False, zorder=1))
    for t in [np.linspace(0.06, 0.35, 40), None]:
        if t is None: break
        ax.plot(0.5 + 0.28*np.cos(t*np.pi), 0.52 + 0.22*np.sin(t*np.pi),
                transform=ax.transAxes, color="#c0b8b0", lw=0.9, zorder=2)
    for roi, (cx, cy, rx, ry) in {
        "V1":  (0.79, 0.51, 0.065, 0.113),
        "V2":  (0.66, 0.46, 0.058, 0.100),
        "V3":  (0.55, 0.43, 0.053, 0.090),
        "hV4": (0.41, 0.33, 0.068, 0.088),
    }.items():
        ax.add_patch(Ellipse((cx, cy), 2*rx, 2*ry, transform=ax.transAxes,
                              facecolor=ROI_COLS[roi], edgecolor="white",
                              linewidth=0.7, alpha=0.88, zorder=3, clip_on=False))
        ax.text(cx, cy, roi, transform=ax.transAxes,
                fontsize=7.5, ha="center", va="center",
                color="white", fontweight="bold", zorder=4)

# ROI legend (2 columns)
ax.legend(
    handles=[mpatches.Patch(facecolor=ROI_COLS[r], label=r,
                             edgecolor='white', linewidth=0.5)
             for r in ['V1', 'V2', 'V3', 'hV4']],
    loc='upper left', fontsize=5.5, frameon=False,
    handlelength=0.9, handleheight=0.7,
    labelspacing=0.25, borderpad=0.2,
    ncol=2, columnspacing=0.5,
    bbox_to_anchor=(0.01, 0.99),
)
ax.text(0.50, 0.04,
        "V1 → V2 → V3 → hV4  (retinotopic hierarchy)",
        transform=ax.transAxes, fontsize=6, ha="center", va="bottom",
        color="#444444", style="italic")
_plabel(ax, "B", x=-0.06, y=1.04)


# =============================================================================
# PANEL C — Image-based analysis pipeline
# =============================================================================
# 5 mini-panels:
#   [0] SRM colour space  (Phase 1 embedding, after Procrustes)
#   [1] LORO bars          (F2 Panel A)
#   [2] LOCO bars          (F2 Panel B)
#   [3] 2-comp landscape   (F4 Panel C)
#   [4] Pre-image filter   (F5 Panel A)

# Pixel crop regions (x0, y0, x1, y1) — 0-indexed, top-left origin
CROPS = {
    'cspace': (CEMB, (3000, 80, 5850, 2560)),   # right panel "After Procrustes"
    'loro':   (FIG2, (20,  20,  660, 950)),
    'loco':   (FIG2, (680, 20, 1350, 950)),
    'twocomp':(FIG4, (1400,  0, 2190, 1405)),
    'filter': (FIG5, (20,   20,  680, 1220)),
}
KEYS  = ['cspace', 'loro', 'loco', 'twocomp', 'filter']

MINI_CAP = [
    "SRM-aligned\ncolour space",
    "Discrimination\n(LORO, LDA acc.)",
    "Interpolation\n(LOCO, adj. acc.)",
    "2-component\nmodel fit",
    "Pre-image\nfilter (δθ)",
]

# Stage groups: (first_idx, last_idx, label, colour_key)
STAGES = [
    (0, 0, "Stage A — Alignment",          'A'),
    (1, 2, "Stage B — Decoding",           'B'),
    (3, 4, "Stage C — Modelling & Filter", 'C'),
]

# ── Layout constants (in ax_c fraction) ─────────────────────────────────────
N = 5
P_W  = 0.148   # panel width
P_H  = 0.68    # panel height
P_Y0 = 0.14    # panel bottom y (leaves room for caption below)
GAP  = 0.036   # gap between panels
LM   = (1.0 - N*P_W - (N-1)*GAP) / 2   # left margin ≈ 0.026
P_X0 = [LM + i*(P_W + GAP) for i in range(N)]

ax = ax_c

# ── Stage brackets above panels ─────────────────────────────────────────────
bkt_y    = P_Y0 + P_H + 0.04   # bracket line y
label_y  = bkt_y + 0.075        # text above bracket

for (fi, li, slabel, sk) in STAGES:
    col   = STAGE_COL[sk]
    x_lo  = P_X0[fi]
    x_hi  = P_X0[li] + P_W
    x_mid = (x_lo + x_hi) / 2
    # Bracket line
    ax.plot([x_lo, x_hi], [bkt_y, bkt_y],
            transform=ax.transAxes, color=col, lw=1.0, solid_capstyle='round')
    ax.plot([x_lo, x_lo], [bkt_y, bkt_y - 0.03],
            transform=ax.transAxes, color=col, lw=1.0)
    ax.plot([x_hi, x_hi], [bkt_y, bkt_y - 0.03],
            transform=ax.transAxes, color=col, lw=1.0)
    ax.text(x_mid, label_y, slabel,
            transform=ax.transAxes,
            fontsize=5.8, ha='center', va='bottom',
            color=col, fontweight='bold')

# ── Mini panels and arrows ────────────────────────────────────────────────────
from PIL import Image as PilImage

def _load_crop(src, box):
    """Return numpy RGBA array for the given crop box."""
    img = PilImage.open(src).convert('RGB')
    return np.array(img.crop(box))

for i, key in enumerate(KEYS):
    src, box = CROPS[key]
    x0 = P_X0[i]
    sk = [s[3] for s in STAGES if s[0] <= i <= s[1]][0]
    border_col = STAGE_COL[sk]

    # Mini axes
    ax_mini = ax.inset_axes([x0, P_Y0, P_W, P_H])
    ax_mini.set_axis_off()

    try:
        arr = _load_crop(src, box)
        ax_mini.imshow(arr, aspect='auto', extent=[0, 1, 0, 1],
                       interpolation='bilinear')
    except Exception as e:
        print(f"  crop '{key}' failed: {e}")
        ax_mini.add_patch(FancyBboxPatch((0.02, 0.02), 0.96, 0.96,
                                          boxstyle="round,pad=0.02",
                                          facecolor='#eeeeee',
                                          edgecolor='#cccccc', lw=0.5))
        ax_mini.text(0.5, 0.5, key, ha='center', va='center',
                     fontsize=7, color='#888888')

    # Coloured border matching stage
    for spine_pos in ['top', 'bottom', 'left', 'right']:
        ax_mini.spines[spine_pos].set_visible(True)
        ax_mini.spines[spine_pos].set_color(border_col)
        ax_mini.spines[spine_pos].set_linewidth(1.2)
        ax_mini.spines['top'].set_visible(True)

    # Caption below
    ax.text(x0 + P_W/2, P_Y0 - 0.02, MINI_CAP[i],
            transform=ax.transAxes,
            fontsize=5.5, ha='center', va='top',
            color='#333333', linespacing=1.3)

    # Arrow to next panel
    if i < N - 1:
        arr_x0 = P_X0[i] + P_W + 0.004
        arr_x1 = P_X0[i+1] - 0.006
        arr_y  = P_Y0 + P_H * 0.52
        ax.annotate("",
                    xy=(arr_x1, arr_y), xytext=(arr_x0, arr_y),
                    xycoords="axes fraction",
                    arrowprops=dict(arrowstyle="-|>", color="#555555",
                                    lw=0.9, shrinkA=0, shrinkB=0))

_plabel(ax, "C", x=-0.012, y=1.06)


# =============================================================================
# Save
# =============================================================================
OUT.mkdir(parents=True, exist_ok=True)
fig.savefig(OUT / "fig1_output.png", dpi=300,
            bbox_inches="tight", facecolor="white")
fig.savefig(OUT / "fig1_output.pdf", dpi=300,
            bbox_inches="tight", facecolor="white")
print(f"Saved: {OUT / 'fig1_output.png'}")
print(f"Saved: {OUT / 'fig1_output.pdf'}")
plt.close(fig)
