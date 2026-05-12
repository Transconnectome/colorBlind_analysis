"""Compare 4 rendering options for sub-08 2-comp F0 canonical.

Generates 4 PNG figures, one per option, each 8 rows (c1-c8) × 4 cols
(Original / CVD perceives / Filtered / CVD(Filtered)).

Options:
- A: vivid (current col 1, 3 method) — applied to all 4 columns
- B: PsychoPy lab2rgb + complement (theoretical PsychoPy display) — all 4
- C: current state (col 1,3 vivid, col 2,4 ring with Machado anchor)
- D: PsychoPy lab2rgb on dict directly (no complement) — all 4
"""
import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

_HERE = Path(__file__).resolve()
_PHASE2 = _HERE.parents[2]
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_PHASE2 / 'scripts'))

from visualize_filter_candidates import (
    angle_to_rgb_vivid, lab_to_rgb_display, cvd_response_lab,
    find_preimage, forward_perceived, L_STAR, CHROMA, SUBJECTS,
)

OUT = _PHASE2 / 'results' / 'visualizations' / 'rendering_options_comparison'
OUT.mkdir(parents=True, exist_ok=True)

# Test case: sub-08 2-comp F0 canonical
SUBJ = '08'
CVD = 'deutan'
PARAMS = SUBJECTS[SUBJ]['2comp']  # β_s=38, β_c=-14
DLAM_MACHADO = SUBJECTS[SUBJ]['machado']['delta_lambda']  # 1.5 nm

# c1-c8 only
TIER1 = [(0,'c1 (Red)'),(45,'c2 (Orange)'),(90,'c3 (Yellow)'),
         (135,'c4 (Green)'),(180,'c5 (Cyan)'),(225,'c6 (Blue)'),
         (270,'c7 (Violet)'),(315,'c8 (Magenta)')]


def lab2rgb_psychopy(L, a, b, clip=True):
    """Exact lab2rgb from /Users/jinilkim/.../colorBlind/colorBlind_test.py:95-114."""
    L, a, b = float(L), float(a), float(b)
    y = (L + 16) / 116
    x = a / 500 + y
    z = y - b / 200
    xyz = np.array([x, y, z])
    xyz = np.where(xyz > 0.206893, xyz**3, (xyz - 16/116) / 7.787)
    xyz *= [0.95047, 1.0, 1.08883]
    rgb = np.dot([[3.2406, -1.5372, -0.4986],
                  [-0.9689, 1.8758, 0.0415],
                  [0.0557, -0.2040, 1.0570]], xyz)
    rgb = np.where(rgb <= 0.0031308, 12.92 * rgb, 1.055 * rgb**(1/2.4) - 0.055)
    if clip:
        rgb = np.clip(rgb, 0, 1)
    return rgb


def render_A_vivid(theta, *args, **kwargs):
    """Option A: vivid render at hue θ."""
    return angle_to_rgb_vivid(theta)


def render_B_psychopy_complement(theta, L=L_STAR, *args, **kwargs):
    """Option B: PsychoPy lab2rgb at standard CIElab convention (= complement of dict).

    Dict uses a = -C·cos(θ_label), b = -C·sin(θ_label).
    Display (post-complement) = standard a = +C·cos(θ_label), b = +C·sin(θ_label).
    """
    rad = np.deg2rad(theta)
    a = CHROMA * np.cos(rad)
    b = CHROMA * np.sin(rad)
    return lab2rgb_psychopy(L, a, b)


def render_C_current_col24(theta, L_cvd, *args, **kwargs):
    """Option C col 2/4 (current state): ring at L=L_cvd, C=40."""
    rad = np.deg2rad(theta)
    a = CHROMA * np.cos(rad)
    b = CHROMA * np.sin(rad)
    return lab_to_rgb_display(L_cvd, a, b)


def render_D_psychopy_dict(theta, L=L_STAR, *args, **kwargs):
    """Option D: PsychoPy lab2rgb on dict value directly (no complement).

    Dict values: a = -C·cos(θ_label), b = -C·sin(θ_label).
    """
    rad = np.deg2rad(theta)
    a = -CHROMA * np.cos(rad)
    b = -CHROMA * np.sin(rad)
    return lab2rgb_psychopy(L, a, b)


def make_figure(option_name, render_col1, render_col3, render_col2, render_col4,
                use_machado_for_L, title_suffix):
    """Generate one figure with c1-c8 × 4 columns."""
    rows = TIER1
    n = len(rows)
    fig, axes = plt.subplots(n, 4, figsize=(8.5, 0.55*n + 1.8),
                             gridspec_kw={'hspace': 0.08, 'wspace': 0.08})
    fig.suptitle(
        f'Option {option_name} — sub-{SUBJ} ({CVD}), 2-comp (β_s=38°, β_c=-14°)\n'
        f'{title_suffix}',
        fontsize=10, y=0.995)
    for ax, t in zip(axes[0], ['Original', 'CVD perceives',
                                'Filtered (pre-image)', 'CVD(Filtered)']):
        ax.set_title(t, fontsize=9)

    for i, (theta, label) in enumerate(rows):
        ax_row = axes[i]
        # Pre-image and perceived hues (2-comp)
        theta_pre, _ = find_preimage(theta, '2comp', CVD, PARAMS)
        theta_cvd, dt = forward_perceived(theta, '2comp', CVD, PARAMS)
        theta_cvd_pre, _ = forward_perceived(theta_pre, '2comp', CVD, PARAMS)

        # L* per column (2-comp: ΔL*=0; Machado anchor: hue-dependent ΔL*)
        if use_machado_for_L:
            L_cvd = float(cvd_response_lab(theta, CVD, DLAM_MACHADO)[0])
            L_cvd_pre = float(cvd_response_lab(theta_pre, CVD, DLAM_MACHADO)[0])
        else:
            L_cvd = L_STAR  # 2-comp: no ΔL*
            L_cvd_pre = L_STAR

        rgb1 = render_col1(theta, L=L_STAR)
        rgb2 = render_col2(theta_cvd, L_cvd=L_cvd, L=L_cvd)
        rgb3 = render_col3(theta_pre, L=L_STAR)
        rgb4 = render_col4(theta_cvd_pre, L_cvd=L_cvd_pre, L=L_cvd_pre)

        ax_row[0].add_patch(Rectangle((0,0), 1, 1, color=rgb1))
        ax_row[1].add_patch(Rectangle((0,0), 1, 1, color=rgb2))
        ax_row[2].add_patch(Rectangle((0,0), 1, 1, color=rgb3))
        ax_row[3].add_patch(Rectangle((0,0), 1, 1, color=rgb4))

        ax_row[0].text(-0.05, 0.5, f'{label}\nθ = {int(theta)}°',
                       ha='right', va='center', fontsize=7,
                       transform=ax_row[0].transAxes)
        ax_row[1].text(0.5, -0.02, f'δθ = {dt:+.1f}°',
                       ha='center', va='top', fontsize=7,
                       transform=ax_row[1].transAxes)
        ax_row[2].text(0.5, -0.02,
                       f'θ_pre = {int(theta_pre)}°',
                       ha='center', va='top', fontsize=7,
                       transform=ax_row[2].transAxes)

        for a in ax_row:
            a.set_xticks([]); a.set_yticks([])
            a.set_xlim(0,1); a.set_ylim(0,1)
            for sp in a.spines.values():
                sp.set_edgecolor('black')

    plt.subplots_adjust(left=0.16, right=0.98, top=0.92, bottom=0.04)
    outpath = OUT / f'option_{option_name}_sub08_2comp.png'
    fig.savefig(outpath, dpi=140, bbox_inches='tight')
    plt.close(fig)
    print(f'  → {outpath.name}')
    return outpath


print('Generating 4 rendering option comparisons...')
print()

# Option A — vivid for all 4 columns (no Machado, hue-only rotation)
make_figure(
    'A_vivid',
    render_col1=render_A_vivid, render_col3=render_A_vivid,
    render_col2=render_A_vivid, render_col4=render_A_vivid,
    use_machado_for_L=False,
    title_suffix='angle_to_rgb_vivid for all 4 columns (no ΔL*; 2-comp δθ only)',
)

# Option B — PsychoPy lab2rgb + complement, all 4 columns
make_figure(
    'B_psychopy_complement',
    render_col1=render_B_psychopy_complement,
    render_col3=render_B_psychopy_complement,
    render_col2=render_B_psychopy_complement,
    render_col4=render_B_psychopy_complement,
    use_machado_for_L=False,
    title_suffix='PsychoPy lab2rgb at L=75, C=40, standard CIElab hue (post-complement)',
)

# Option C — current state (col 1,3 vivid, col 2,4 ring with Machado anchor)
make_figure(
    'C_current_state',
    render_col1=render_A_vivid, render_col3=render_A_vivid,
    render_col2=render_C_current_col24, render_col4=render_C_current_col24,
    use_machado_for_L=True,
    title_suffix='Current: col1,3 vivid; col2,4 L=75±Machado, C=40 (Q1 BUG: Machado used in 2-comp viz)',
)

# Option D — PsychoPy lab2rgb without complement (dict directly)
make_figure(
    'D_psychopy_no_complement',
    render_col1=render_D_psychopy_dict,
    render_col3=render_D_psychopy_dict,
    render_col2=render_D_psychopy_dict,
    render_col4=render_D_psychopy_dict,
    use_machado_for_L=False,
    title_suffix='PsychoPy lab2rgb on dict directly (no complement; hue ≠ label)',
)

print()
print(f'Output dir: {OUT}')
