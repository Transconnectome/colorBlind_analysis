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
import json as _json
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
OUT    = Path(__file__).parent.parent
ATLAS  = BASE / 'ProbAtlas_v4' / 'subj_vol_all'

FIG2   = BASE / 'docs/PAPER/Figures/fig2_loro_loco.png'
FIG4   = BASE / 'docs/PAPER/Figures/fig4_twocomp.png'
FIG5   = BASE / 'docs/PAPER/Figures/fig5_preimage.png'
# CEMB unused — Stage A uses synthetic scatter (see Panel C section)

# ── Load sub-08 pre-image JSON ─────────────────────────────────────────────────
_P08_JSON = (BASE / 'analysis/future_phase2_filter_optimization/results/fits'
             '/preimage_2component/sub-08_V4_2component_preimage.json')
try:
    with open(_P08_JSON) as _f:
        _P08 = _json.load(_f)
    _THETA_PRED  = _P08.get('forward_model_at_original', {}).get('perceived')  # 8-float list, CVD-perceived angles
    _PREIMAGE    = _P08['preimage_angles']   # list of 8 pre-image angles
    _STIM_ANGLES = _P08.get('stimulus_angles_cielab', [0, 45, 90, 135, 180, 225, 270, 315])
except Exception as _e:
    print(f"  sub-08 JSON not loaded: {_e}")
    _THETA_PRED  = None
    _PREIMAGE    = None
    _STIM_ANGLES = [0, 45, 90, 135, 180, 225, 270, 315]

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

# ── Helper: CIELab angle to RGB ────────────────────────────────────────────────
def _angle_to_rgb(theta_deg, L=65.0, C=40.0):
    """Convert a hue angle on the CIELab a*-b* circle to display RGB."""
    import math
    a = C * math.cos(math.radians(theta_deg))
    b = C * math.sin(math.radians(theta_deg))
    return _lab2rgb(L, a, b)

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
    hspace=0.22, wspace=0.20,
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
WCX, WCY = 0.20, 0.50   # wheel centre — left/centre of left half-panel
ROUT, RIN = 0.155, 0.088  # smaller wheel → more label clearance
DTHETA = 360 / 8
DIVIDER_X = 0.46          # vertical divider between wheel and RSVP sections


def _draw_rsvp_screen(ax, x0, w):
    """RSVP: title + 3 square PsychoPy screenshots (fixation, white K, black K)."""
    from PIL import Image as PilImg

    FIX_PATH  = OUT / 'rsvp_fix.png'
    WHTK_PATH = OUT / 'rsvp_stim_red.png'
    BLKK_PATH = OUT / 'rsvp_stim_kblack.png'

    mid = x0 + w / 2
    # Panel A physical dimensions (mm): width 77.7, height 69.9 → correction for square images
    AX_ASPECT = 77.7 / 69.9

    ax.text(mid, 0.85, "RSVP — detect oddball 'K'",
            transform=ax.transAxes, fontsize=7.5, ha='center', va='top',
            color='black')

    # ── 3 square screenshots filling the width ────────────────────────────────
    margin_l  = 0.01
    margin_r  = 0.01
    arrow_w   = 0.04   # space allocated per inter-image arrow
    n_imgs    = 3
    img_w = (w - margin_l - margin_r - (n_imgs - 1) * arrow_w) / n_imgs
    img_h = img_w * AX_ASPECT   # square in physical mm

    img_y0 = WCY - img_h / 2 + 0.03   # vertically centred, slight upward shift

    img_xs = [x0 + margin_l + i * (img_w + arrow_w) for i in range(n_imgs)]
    labels = ['fixation', 'white K', 'black K']
    paths  = [FIX_PATH, WHTK_PATH, BLKK_PATH]

    for i, (path, cap) in enumerate(zip(paths, labels)):
        lx = img_xs[i]
        if path.exists():
            arr    = np.array(PilImg.open(path).convert('RGB'))
            ax_img = ax.inset_axes([lx, img_y0, img_w, img_h],
                                   transform=ax.transAxes)
            ax_img.imshow(arr, aspect='auto')
            ax_img.set_axis_off()
        else:
            ax.add_patch(mpatches.Rectangle(
                (lx, img_y0), img_w, img_h,
                transform=ax.transAxes,
                facecolor='#dddddd', edgecolor='#999999', linewidth=0.5))
        ax.text(lx + img_w / 2, img_y0 - 0.025, cap,
                transform=ax.transAxes, fontsize=5, ha='center', va='top',
                color='#777777')

    # ── Arrows between screenshots ─────────────────────────────────────────────
    arr_y = img_y0 + img_h / 2
    for i in range(n_imgs - 1):
        ax.annotate("",
                    xy=(img_xs[i+1] - 0.005, arr_y),
                    xytext=(img_xs[i] + img_w + 0.005, arr_y),
                    xycoords='axes fraction',
                    arrowprops=dict(arrowstyle="-|>", color="#777777",
                                    lw=0.8, shrinkA=0, shrinkB=0))

    # ── "6 runs × 8 colours / run" — big, black, prominent ───────────────────
    ax.text(mid, img_y0 - 0.08, "6 runs × 8 colours / run",
            transform=ax.transAxes, fontsize=8, ha='center', va='top',
            color='black', fontweight='bold')


# CHANGE 1: Red (i=0) centred at 0° = 3 o'clock (east), counterclockwise
for i, rgb in enumerate(STIM_RGB):
    a_s = i * DTHETA - DTHETA/2    # Red: -22.5° to +22.5°
    a_e = i * DTHETA + DTHETA/2
    ax.add_patch(Wedge((WCX, WCY), ROUT, a_s, a_e,
                        width=ROUT-RIN, transform=ax.transAxes,
                        facecolor=rgb, edgecolor="white", linewidth=0.8,
                        clip_on=False, zorder=3))
    a_mid = np.deg2rad(i * DTHETA)   # wedge centre angle
    # Cyan (i=4, 180°) placed outside axes to the left; others kept close to wheel
    lr = ROUT + (0.065 if i == 4 else 0.030)
    lx, ly = WCX + lr*np.cos(a_mid), WCY + lr*np.sin(a_mid)
    ha = "left" if lx > WCX+0.01 else ("right" if lx < WCX-0.01 else "center")
    va = "bottom" if ly > WCY+0.01 else ("top" if ly < WCY-0.01 else "center")
    # Clamp right so labels don't cross divider
    if lx > DIVIDER_X - 0.02:
        lx = DIVIDER_X - 0.02; ha = "right"
    # No left clamp for Cyan — let it appear outside the axes to the left
    if i != 4 and lx < 0.01:
        lx = 0.01; ha = "left"
    t = ax.text(lx, ly, HUE_NAMES[i], transform=ax.transAxes,
                fontsize=5.5, ha=ha, va=va, color="#333333")
    t.set_clip_on(False)

ax.add_patch(plt.Circle((WCX, WCY), RIN*0.96, transform=ax.transAxes,
                          facecolor="white", edgecolor="none", zorder=4, clip_on=False))
ax.text(WCX, WCY, "CIE-Lab\nhue\nwheel", transform=ax.transAxes,
        fontsize=5.5, ha="center", va="center", color="#555555",
        linespacing=1.3, zorder=5)
ax.text(WCX, WCY - ROUT - 0.14,
        "8 isoluminant hues\n(CIE-Lab, 45° spacing)",
        transform=ax.transAxes, fontsize=5.5,
        ha="center", va="top", color="#333333", style="italic", linespacing=1.3)
# Divider between wheel (left) and RSVP (right)
ax.plot([0.46, 0.46], [0.04, 0.96], transform=ax.transAxes,
        color="#e0e0e0", lw=0.5, clip_on=False)

# CHANGE 2: call the new RSVP screen function
_draw_rsvp_screen(ax, DIVIDER_X + 0.01, 1.0 - DIVIDER_X - 0.01)

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
#   [1] LORO schematic
#   [2] LOCO schematic
#   [3] CVD colour simulation (swatch flow)
#   [4] Inverse mapping / pre-image filter (swatch flow)

KEYS  = ['cspace', 'loro', 'loco', 'twocomp', 'filter']

MINI_CAP = [
    "SRM-aligned\ncolour space",
    "Leave-one-run-out\n(LORO)",
    "Leave-one-color-out\n(LOCO)",
    "CVD colour\nsimulation",
    "Stimulus-space\nfilter",
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

# ── Mini panel draw functions ────────────────────────────────────────────────
from PIL import Image as PilImage

def _load_crop(src, box):
    """Return numpy RGBA array for the given crop box."""
    img = PilImage.open(src).convert('RGB')
    return np.array(img.crop(box))

def _draw_srm_scatter(ax_mini):
    """Draw a clean synthetic 8-hue scatter representing the SRM shared space.

    Two groups (HC filled circles, CVD open squares) of 8 coloured dots
    arranged in a rough circle — clean and unambiguous, matches the hue wheel.
    """
    ax_mini.set_facecolor('#f8f8f8')
    ax_mini.set_xlim(-1.45, 1.45)
    ax_mini.set_ylim(-1.45, 1.45)

    rng = np.random.default_rng(42)
    angles = np.linspace(0, 2*np.pi, 8, endpoint=False)

    # HC cluster: tight ring
    hc_r = 1.0
    hc_jitter = 0.08
    for a, rgb in zip(angles, STIM_RGB):
        for _ in range(5):   # 5 HC subjects per hue
            dx, dy = rng.normal(0, hc_jitter, 2)
            ax_mini.scatter(hc_r*np.cos(a)+dx, hc_r*np.sin(a)+dy,
                            color=rgb, s=9, zorder=3,
                            edgecolors='none', linewidths=0)

    # CVD points: slightly displaced (deutan/protan shift)
    cvd_r = 0.88
    cvd_jitter = 0.13
    for a, rgb in zip(angles, STIM_RGB):
        for shift in [0.25, -0.18]:   # 2 CVD subjects
            dx, dy = rng.normal(shift*np.cos(a+np.pi/6), cvd_jitter, 2)
            ax_mini.scatter(cvd_r*np.cos(a)+dx, cvd_r*np.sin(a)+dy,
                            color=rgb, s=7, zorder=4,
                            marker='s', edgecolors='#444444', linewidths=0.4)

    # Axis labels
    ax_mini.set_xlabel("", labelpad=1)
    ax_mini.set_ylabel("", labelpad=1)
    ax_mini.tick_params(left=False, bottom=False,
                        labelleft=False, labelbottom=False)
    for sp in ax_mini.spines.values():
        sp.set_color('#cccccc')
        sp.set_linewidth(0.5)
    ax_mini.set_axis_on()

    # Small legend
    ax_mini.scatter([], [], color='#888888', s=9,
                    edgecolors='none', label='HC', zorder=5)
    ax_mini.scatter([], [], color='#888888', s=7, marker='s',
                    edgecolors='#444444', linewidths=0.4, label='CVD', zorder=5)
    ax_mini.legend(fontsize=4.0, frameon=False, loc='lower right',
                   handletextpad=0.2, labelspacing=0.2, borderpad=0.1)


def _grid_base(ax_mini):
    """Shared grid setup: 6 runs (rows) × 8 colours (columns), returns layout dict."""
    ax_mini.set_facecolor('#f5f5f5')
    ax_mini.set_xlim(0, 1); ax_mini.set_ylim(0, 1)
    ax_mini.set_axis_on()
    for sp in ax_mini.spines.values():
        sp.set_color('#cccccc'); sp.set_linewidth(0.5)
    ax_mini.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
    return dict(N_RUNS=6, N_COLORS=8,
                x0=0.14, x1=0.98, y0=0.10, y1=0.83)


def _draw_loro_schematic(ax_mini):
    """LORO: 6 runs (rows) × 8 colours (columns); one run row held out."""
    g = _grid_base(ax_mini)
    N_R, N_C = g['N_RUNS'], g['N_COLORS']
    x0, x1, y0, y1 = g['x0'], g['x1'], g['y0'], g['y1']
    gw, gh = x1-x0, y1-y0
    cw, ch = gw/N_C, gh/N_R
    held = 4   # row index (run 5)

    for r in range(N_R):
        for c in range(N_C):
            x = x0 + c*cw;  y = y0 + (N_R-1-r)*ch
            a = 0.22 if r == held else 1.0
            ax_mini.add_patch(mpatches.Rectangle(
                (x+0.005, y+0.005), cw-0.010, ch-0.010,
                facecolor=STIM_RGB[c], edgecolor='white', linewidth=0.3,
                alpha=a, transform=ax_mini.transAxes, clip_on=True))

    # Red dashed border around held-out ROW
    ry = y0 + (N_R-1-held)*ch
    ax_mini.add_patch(mpatches.Rectangle(
        (x0, ry), gw, ch, fill=False,
        edgecolor='#d73027', linewidth=1.4, linestyle='--',
        transform=ax_mini.transAxes, clip_on=False, zorder=5))

    # Run labels on left
    for r in range(N_R):
        yc = y0 + (N_R-1-r)*ch + ch/2
        col = '#d73027' if r == held else '#888888'
        fw  = 'bold'   if r == held else 'normal'
        ax_mini.text(x0-0.02, yc, f'R{r+1}',
                     transform=ax_mini.transAxes,
                     fontsize=3.8, ha='right', va='center', color=col, fontweight=fw)

    ax_mini.text(0.5, 0.97, 'Leave one run out',
                 transform=ax_mini.transAxes,
                 fontsize=5.5, ha='center', va='top',
                 color=STAGE_COL['B'], fontweight='bold')


def _draw_loco_schematic(ax_mini):
    """LOCO: 6 runs (rows) × 8 colours (columns); one colour column held out."""
    g = _grid_base(ax_mini)
    N_R, N_C = g['N_RUNS'], g['N_COLORS']
    x0, x1, y0, y1 = g['x0'], g['x1'], g['y0'], g['y1']
    gw, gh = x1-x0, y1-y0
    cw, ch = gw/N_C, gh/N_R
    held = 2   # column index (Yellow)

    for r in range(N_R):
        for c in range(N_C):
            x = x0 + c*cw;  y = y0 + (N_R-1-r)*ch
            a = 0.22 if c == held else 1.0
            ax_mini.add_patch(mpatches.Rectangle(
                (x+0.005, y+0.005), cw-0.010, ch-0.010,
                facecolor=STIM_RGB[c], edgecolor='white', linewidth=0.3,
                alpha=a, transform=ax_mini.transAxes, clip_on=True))

    # Red dashed border around held-out COLUMN
    cx_left = x0 + held*cw
    ax_mini.add_patch(mpatches.Rectangle(
        (cx_left, y0), cw, gh, fill=False,
        edgecolor='#d73027', linewidth=1.4, linestyle='--',
        transform=ax_mini.transAxes, clip_on=False, zorder=5))

    # Run labels on left
    for r in range(N_R):
        yc = y0 + (N_R-1-r)*ch + ch/2
        ax_mini.text(x0-0.02, yc, f'R{r+1}',
                     transform=ax_mini.transAxes,
                     fontsize=3.8, ha='right', va='center', color='#888888')

    ax_mini.text(0.5, 0.97, 'Leave one color out',
                 transform=ax_mini.transAxes,
                 fontsize=5.5, ha='center', va='top',
                 color=STAGE_COL['B'], fontweight='bold')


# Key hue indices to display in swatch panels (representative: Red, Yellow, Cyan, Blue)
_SWATCH_IDX = [0, 2, 4, 5]   # indices into the 8-hue array

def _swatch_layout(n, sw_h=0.14, sw_w=0.30):
    """Return (col_left, col_right, arrow_x, gap, swatch_top) for n swatches."""
    label_h  = 0.13   # reserved at top for column headers
    avail    = 1.0 - label_h - 0.04
    gap      = (avail - n * sw_h) / (n + 1)
    swatch_top = 1.0 - label_h
    col_l    = 0.06
    col_r    = 0.60
    arrow_x  = col_l + sw_w + 0.02
    return col_l, col_r, arrow_x, gap, swatch_top, sw_h, sw_w


def _draw_cvd_simulation(ax_mini):
    """CVD forward simulation: Original → CVD predicted."""
    ax_mini.set_facecolor('#ffffff')
    ax_mini.set_xlim(0, 1); ax_mini.set_ylim(0, 1)
    ax_mini.set_axis_off()

    col_l, col_r, arrow_x, gap, swatch_top, sw_h, sw_w = _swatch_layout(len(_SWATCH_IDX))

    for k, idx in enumerate(_SWATCH_IDX):
        y = swatch_top - (k+1)*(sw_h + gap)
        ax_mini.add_patch(mpatches.Rectangle(
            (col_l, y), sw_w, sw_h,
            transform=ax_mini.transAxes,
            facecolor=STIM_RGB[idx], edgecolor='#cccccc', linewidth=0.5))
        cvd_rgb = _angle_to_rgb(_THETA_PRED[idx]) if _THETA_PRED else STIM_RGB[idx]
        ax_mini.add_patch(mpatches.Rectangle(
            (col_r, y), sw_w, sw_h,
            transform=ax_mini.transAxes,
            facecolor=cvd_rgb, edgecolor='#cccccc', linewidth=0.5))
        ax_mini.annotate("",
            xy=(col_r-0.01, y+sw_h/2), xytext=(arrow_x, y+sw_h/2),
            xycoords='axes fraction',
            arrowprops=dict(arrowstyle='-|>', color='#999999', lw=0.7,
                            shrinkA=0, shrinkB=0))

    # Column headers — placed in reserved top 13%
    lbl_y = 0.99
    ax_mini.text(col_l + sw_w/2, lbl_y, 'Original',
                 transform=ax_mini.transAxes, fontsize=4.8, ha='center', va='top',
                 color='#333333', fontweight='bold')
    ax_mini.text(col_r + sw_w/2, lbl_y, 'CVD',
                 transform=ax_mini.transAxes, fontsize=4.8, ha='center', va='top',
                 color='#cc3333', fontweight='bold')


def _draw_inverse_mapping(ax_mini):
    """Inverse mapping: filtered input → CVD perceives as original."""
    ax_mini.set_facecolor('#ffffff')
    ax_mini.set_xlim(0, 1); ax_mini.set_ylim(0, 1)
    ax_mini.set_axis_off()

    col_l, col_r, arrow_x, gap, swatch_top, sw_h, sw_w = _swatch_layout(len(_SWATCH_IDX))

    for k, idx in enumerate(_SWATCH_IDX):
        y = swatch_top - (k+1)*(sw_h + gap)
        filt_rgb = _angle_to_rgb(_PREIMAGE[idx]) if _PREIMAGE else STIM_RGB[idx]
        ax_mini.add_patch(mpatches.Rectangle(
            (col_l, y), sw_w, sw_h,
            transform=ax_mini.transAxes,
            facecolor=filt_rgb, edgecolor='#cccccc', linewidth=0.5))
        ax_mini.add_patch(mpatches.Rectangle(
            (col_r, y), sw_w, sw_h,
            transform=ax_mini.transAxes,
            facecolor=STIM_RGB[idx], edgecolor='#cccccc', linewidth=0.5))
        ax_mini.annotate("",
            xy=(col_r-0.01, y+sw_h/2), xytext=(arrow_x, y+sw_h/2),
            xycoords='axes fraction',
            arrowprops=dict(arrowstyle='-|>', color='#999999', lw=0.7,
                            shrinkA=0, shrinkB=0))

    lbl_y = 0.99
    ax_mini.text(col_l + sw_w/2, lbl_y, 'Filtered',
                 transform=ax_mini.transAxes, fontsize=4.8, ha='center', va='top',
                 color='#333333', fontweight='bold')
    ax_mini.text(col_r + sw_w/2, lbl_y, 'CVD sees',
                 transform=ax_mini.transAxes, fontsize=4.8, ha='center', va='top',
                 color='#2a6e6b', fontweight='bold')


# ── Mini panels and arrows ────────────────────────────────────────────────────
for i, key in enumerate(KEYS):
    x0 = P_X0[i]
    sk = [s[3] for s in STAGES if s[0] <= i <= s[1]][0]
    border_col = STAGE_COL[sk]

    # Mini axes
    ax_mini = ax.inset_axes([x0, P_Y0, P_W, P_H])

    if i == 0:
        # Stage A: synthetic SRM scatter — clean 8-hue circular arrangement
        print("Panel C[0]: drawing synthetic SRM scatter…")
        _draw_srm_scatter(ax_mini)
    elif i == 1:
        _draw_loro_schematic(ax_mini)
    elif i == 2:
        _draw_loco_schematic(ax_mini)
    elif i == 3:
        _draw_cvd_simulation(ax_mini)
    elif i == 4:
        _draw_inverse_mapping(ax_mini)

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
fig.savefig(OUT / "fig1_paradigm.png", dpi=300,
            bbox_inches="tight", facecolor="white")
fig.savefig(OUT / "fig1_paradigm.pdf", dpi=300,
            bbox_inches="tight", facecolor="white")
print(f"Saved: {OUT / 'fig1_paradigm.png'}")
print(f"Saved: {OUT / 'fig1_paradigm.pdf'}")
plt.close(fig)
