#!/usr/bin/env python3
"""
analysis_gradient_profile.py — Forward Model Gradient Profile Analysis.

Verifies the "plateau hypothesis": SRM z-JND discordance arises because
the same cone shift causes endpoint overseparation (high global distance)
AND intermediate gradient flattening (high JND / HYPO).

Method:
  1. Load per-subject ridge_gcv W matrices (6, V_s)
  2. Create FE basis at 1° resolution → (360, 6)
  3. Y_pred(θ) = C(θ) @ W → predicted voxel pattern at each degree
  4. Local gradient(θ) = ||Y(θ+1) - Y(θ)|| (Euclidean)
  5. For each pair: global distance vs mean local gradient
  6. Compare HC mean vs CVD (sub-08)

Output:
  - results/gradient_profile/summary.json
  - figures/gradient_profile_V{1,2,3,4}.png
  - figures/gradient_plateau_verification.png
"""

import sys
import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# ── paths ──────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[1]  # future_phase3_behavioral_analysis/
PROJ = ROOT.parent.parent                    # colorBlind_analysis/
WEIGHT_DIR = PROJ / 'analysis' / 'future_phase1_forward_model' / 'results' / 'subject_weights'
OUT_DIR = ROOT / 'results' / 'gradient_profile'
FIG_DIR = ROOT / 'figures'
OUT_DIR.mkdir(parents=True, exist_ok=True)
FIG_DIR.mkdir(parents=True, exist_ok=True)

# ── add utils path ────────────────────────────────────────────────────
sys.path.insert(0, str(PROJ / 'analysis' / 'future_phase1_forward_model' / 'scripts'))
from utils_forward_model import create_basis_full, N_CHANNELS

# ── constants ─────────────────────────────────────────────────────────
HC_SUBJECTS = [f'{i:02d}' for i in range(1, 8)]
CVD_SUBJECT = '08'  # deutan, behavioral pilot subject

ROIS = ['V1', 'V2', 'V3', 'V4']
HUE_ANGLES = np.array([0, 45, 90, 135, 180, 225, 270, 315])
COLOR_NAMES = ['red', 'orange', 'yellow', 'green', 'cyan', 'blue', 'purple', 'magenta']

# Color pairs matching behavioral JND experiment
# (name_a, name_b, θ_a, θ_b, shorter_arc_start, shorter_arc_end, JND_direction_HC1)
PAIRS = [
    ('red',    'orange',  0,   45,   0,   45,  'HYPER'),
    ('orange', 'yellow',  45,  90,   45,  90,  'HYPO'),
    ('yellow', 'green',   90,  135,  90,  135, 'HYPO'),
    ('green',  'blue',    135, 225,  135, 225, 'HYPER'),
    ('yellow', 'purple',  90,  270,  270, 450, 'HYPO'),  # shorter arc: 270→360→90
    ('blue',   'purple',  225, 270,  225, 270, 'HYPER'),
    ('cyan',   'magenta', 180, 315,  180, 315, 'HYPER'),
    ('red',    'cyan',    0,   180,  0,   180, 'HYPER'),
]

# Colors for plotting
PAIR_COLORS_PLOT = {
    'HYPO':  '#d62728',  # red
    'HYPER': '#2ca02c',  # green
}
COLOR_HEX = {
    'red': '#FF0000', 'orange': '#FF8000', 'yellow': '#FFFF00',
    'green': '#00FF00', 'cyan': '#00FFFF', 'blue': '#0000FF',
    'purple': '#8000FF', 'magenta': '#FF00FF',
}


# ── core computation ──────────────────────────────────────────────────

def load_W(roi, subject):
    """Load ridge_gcv W matrix (n_channels, V_s)."""
    path = WEIGHT_DIR / roi / f'sub-{subject}_W.npy'
    if not path.exists():
        raise FileNotFoundError(f'W not found: {path}')
    return np.load(path)


def compute_gradient_profile(W, basis_full):
    """Compute gradient profile: ||Y(θ+1) - Y(θ)|| for θ=0..359.

    Args:
        W: (K, V_s) encoding weights
        basis_full: (360, K) full basis

    Returns:
        gradient: (360,) Euclidean distance between adjacent degree predictions
    """
    # Y_pred = basis_full @ W → (360, V_s)
    Y_all = basis_full @ W  # (360, V_s)

    # Circular gradient: distance between θ and θ+1
    Y_shifted = np.roll(Y_all, -1, axis=0)  # Y(θ+1)
    gradient = np.sqrt(np.sum((Y_shifted - Y_all) ** 2, axis=1))  # (360,)

    return gradient


def compute_pair_metrics(gradient, Y_all, pair):
    """Compute global distance and mean local gradient for a color pair.

    Args:
        gradient: (360,) gradient profile
        Y_all: (360, V_s) predicted patterns
        pair: tuple (name_a, name_b, θ_a, θ_b, arc_start, arc_end, jnd_dir)

    Returns:
        dict with global_dist, mean_gradient, arc_span
    """
    name_a, name_b, theta_a, theta_b, arc_start, arc_end, jnd_dir = pair

    # Global distance: ||Y(θ_A) - Y(θ_B)||
    global_dist = np.sqrt(np.sum((Y_all[theta_a] - Y_all[theta_b]) ** 2))

    # Mean local gradient along shorter arc
    if arc_end > 360:
        # Wraps around (e.g., yellow-purple: 270→360→90)
        indices = list(range(arc_start, 360)) + list(range(0, arc_end - 360))
    else:
        indices = list(range(arc_start, arc_end))

    arc_gradients = gradient[indices]
    mean_grad = float(np.mean(arc_gradients))
    arc_span = len(indices)

    return {
        'global_dist': float(global_dist),
        'mean_gradient': mean_grad,
        'arc_span': arc_span,
        'gradient_profile': arc_gradients.tolist(),
    }


# ── main ──────────────────────────────────────────────────────────────

def main():
    basis_full = create_basis_full(N_CHANNELS, basis_type='fe')  # (360, 6)

    results = {}

    for roi in ROIS:
        print(f'\n=== {roi} ===')
        results[roi] = {'hc_subjects': {}, 'cvd': {}, 'pairs': {}}

        # -- HC subjects --
        hc_gradients = []
        hc_pair_metrics = {p[0]+'-'+p[1]: [] for p in PAIRS}

        for subj in HC_SUBJECTS:
            try:
                W = load_W(roi, subj)
            except FileNotFoundError:
                print(f'  skip sub-{subj} (no W)')
                continue

            grad = compute_gradient_profile(W, basis_full)
            Y_all = basis_full @ W
            hc_gradients.append(grad)

            for pair in PAIRS:
                pname = f'{pair[0]}-{pair[1]}'
                m = compute_pair_metrics(grad, Y_all, pair)
                hc_pair_metrics[pname].append(m)

            results[roi]['hc_subjects'][subj] = {
                'gradient_mean': float(np.mean(grad)),
                'gradient_std': float(np.std(grad)),
            }

        hc_grad_mean = np.mean(hc_gradients, axis=0)  # (360,)
        hc_grad_std = np.std(hc_gradients, axis=0)
        n_hc = len(hc_gradients)

        # -- CVD subject --
        W_cvd = load_W(roi, CVD_SUBJECT)
        cvd_grad = compute_gradient_profile(W_cvd, basis_full)
        Y_cvd = basis_full @ W_cvd

        results[roi]['cvd']['gradient_mean'] = float(np.mean(cvd_grad))

        # -- Per-pair comparison --
        print(f'  {"Pair":<18} {"HC glob":>8} {"CVD glob":>9} {"G ratio":>8} '
              f'{"HC grad":>8} {"CVD grad":>9} {"Gr ratio":>9} {"JND":>6} {"Plateau?":>9}')
        print('  ' + '-' * 95)

        for pair in PAIRS:
            pname = f'{pair[0]}-{pair[1]}'
            jnd_dir = pair[6]

            # HC mean metrics
            hc_globals = [m['global_dist'] for m in hc_pair_metrics[pname]]
            hc_grads = [m['mean_gradient'] for m in hc_pair_metrics[pname]]
            hc_global_mean = np.mean(hc_globals)
            hc_grad_mean_pair = np.mean(hc_grads)

            # CVD metrics
            cvd_m = compute_pair_metrics(cvd_grad, Y_cvd, pair)

            # Ratios
            global_ratio = cvd_m['global_dist'] / hc_global_mean if hc_global_mean > 0 else np.nan
            grad_ratio = cvd_m['mean_gradient'] / hc_grad_mean_pair if hc_grad_mean_pair > 0 else np.nan

            # Plateau test: global_ratio > 1 AND grad_ratio < 1
            is_plateau = global_ratio > 1.0 and grad_ratio < 1.0

            plateau_str = 'YES' if is_plateau else 'no'

            print(f'  {pname:<18} {hc_global_mean:>8.3f} {cvd_m["global_dist"]:>9.3f} '
                  f'{global_ratio:>8.2f} {hc_grad_mean_pair:>8.4f} {cvd_m["mean_gradient"]:>9.4f} '
                  f'{grad_ratio:>9.3f} {jnd_dir:>6} {plateau_str:>9}')

            results[roi]['pairs'][pname] = {
                'jnd_direction': jnd_dir,
                'hc_global_dist_mean': float(hc_global_mean),
                'hc_global_dist_sd': float(np.std(hc_globals)),
                'cvd_global_dist': float(cvd_m['global_dist']),
                'global_ratio': float(global_ratio),
                'hc_mean_gradient_mean': float(hc_grad_mean_pair),
                'hc_mean_gradient_sd': float(np.std(hc_grads)),
                'cvd_mean_gradient': float(cvd_m['mean_gradient']),
                'gradient_ratio': float(grad_ratio),
                'is_plateau': bool(is_plateau),
                'arc_span_deg': int(pair[5] - pair[4]) if pair[5] <= 360 else int(pair[5] - pair[4]),
            }

        # -- Figure: Full gradient profile per ROI --
        fig, ax = plt.subplots(figsize=(10, 4))
        theta = np.arange(360)
        ax.fill_between(theta, hc_grad_mean - hc_grad_std, hc_grad_mean + hc_grad_std,
                         alpha=0.2, color='steelblue', label='HC SD')
        ax.plot(theta, hc_grad_mean, 'steelblue', lw=2, label=f'HC mean (n={n_hc})')
        ax.plot(theta, cvd_grad, '#d62728', lw=2, label='CVD (sub-08)')

        # Mark color positions
        for i, (angle, cname) in enumerate(zip(HUE_ANGLES, COLOR_NAMES)):
            ax.axvline(angle, color=COLOR_HEX[cname], alpha=0.5, lw=1, ls='--')
            ax.text(angle, ax.get_ylim()[1] if i == 0 else max(hc_grad_mean.max(), cvd_grad.max()) * 1.05,
                    cname, ha='center', va='bottom', fontsize=7, color=COLOR_HEX[cname])

        # Shade HYPO pairs
        for pair in PAIRS:
            if pair[6] == 'HYPO':
                arc_s, arc_e = pair[4], pair[5]
                if arc_e > 360:
                    ax.axvspan(arc_s, 360, alpha=0.08, color='red')
                    ax.axvspan(0, arc_e - 360, alpha=0.08, color='red')
                else:
                    ax.axvspan(arc_s, arc_e, alpha=0.08, color='red')

        ax.set_xlabel('Hue angle (deg)')
        ax.set_ylabel('Local gradient ||Y(θ+1) - Y(θ)||')
        ax.set_title(f'{roi}: Forward Model Gradient Profile (HC vs CVD)')
        ax.legend(loc='upper right', fontsize=8)
        ax.set_xlim(0, 360)
        fig.tight_layout()
        fig.savefig(FIG_DIR / f'gradient_profile_{roi}.png', dpi=150)
        plt.close(fig)
        print(f'  Saved: figures/gradient_profile_{roi}.png')

    # -- Summary figure: Plateau verification scatter --
    fig, axes = plt.subplots(2, 2, figsize=(10, 9))
    axes = axes.flatten()

    for idx, roi in enumerate(ROIS):
        ax = axes[idx]
        pairs_data = results[roi]['pairs']

        for pname, pd in pairs_data.items():
            color = PAIR_COLORS_PLOT[pd['jnd_direction']]
            marker = 's' if pd['is_plateau'] else 'o'
            ax.scatter(pd['global_ratio'], pd['gradient_ratio'],
                       c=color, marker=marker, s=80, edgecolors='k', lw=0.5, zorder=3)
            ax.annotate(pname, (pd['global_ratio'], pd['gradient_ratio']),
                        fontsize=6, ha='left', va='bottom', xytext=(3, 3),
                        textcoords='offset points')

        # Reference lines
        ax.axhline(1.0, color='gray', ls=':', alpha=0.5)
        ax.axvline(1.0, color='gray', ls=':', alpha=0.5)

        # Shade plateau quadrant (global > 1, gradient < 1)
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        ax.fill_between([1.0, max(xlim[1], 3)], 0, 1.0,
                         alpha=0.08, color='red', label='Plateau zone')
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)

        ax.set_xlabel('Global distance ratio (CVD/HC)')
        ax.set_ylabel('Mean gradient ratio (CVD/HC)')
        ax.set_title(f'{roi}')

        # Legend
        from matplotlib.lines import Line2D
        legend_elements = [
            Line2D([0], [0], marker='o', color='w', markerfacecolor='#d62728',
                   markersize=8, label='HYPO'),
            Line2D([0], [0], marker='o', color='w', markerfacecolor='#2ca02c',
                   markersize=8, label='HYPER'),
        ]
        ax.legend(handles=legend_elements, fontsize=7, loc='upper left')

    fig.suptitle('Plateau Hypothesis Verification: Global Distance vs Local Gradient\n'
                 '(CVD/HC ratio; plateau = global>1 & gradient<1)',
                 fontsize=11)
    fig.tight_layout()
    fig.savefig(FIG_DIR / 'gradient_plateau_verification.png', dpi=150)
    plt.close(fig)
    print(f'\nSaved: figures/gradient_plateau_verification.png')

    # -- Save results JSON --
    with open(OUT_DIR / 'summary.json', 'w') as f:
        json.dump(results, f, indent=2)
    print(f'Saved: results/gradient_profile/summary.json')

    # -- Final concordance summary --
    print('\n\n=== CONCORDANCE SUMMARY ===')
    print(f'{"ROI":<5} {"Plateau+HYPO":>13} {"Plateau+HYPER":>14} '
          f'{"NoPlateau+HYPO":>15} {"NoPlateau+HYPER":>16}')
    print('-' * 70)

    for roi in ROIS:
        counts = {'p_hypo': 0, 'p_hyper': 0, 'np_hypo': 0, 'np_hyper': 0}
        for pname, pd in results[roi]['pairs'].items():
            is_p = pd['is_plateau']
            is_hypo = pd['jnd_direction'] == 'HYPO'
            if is_p and is_hypo:
                counts['p_hypo'] += 1
            elif is_p and not is_hypo:
                counts['p_hyper'] += 1
            elif not is_p and is_hypo:
                counts['np_hypo'] += 1
            else:
                counts['np_hyper'] += 1

        total = sum(counts.values())
        concordant = counts['p_hypo'] + counts['np_hyper']
        print(f'{roi:<5} {counts["p_hypo"]:>13} {counts["p_hyper"]:>14} '
              f'{counts["np_hypo"]:>15} {counts["np_hyper"]:>16}  '
              f'concordance={concordant}/{total}')


if __name__ == '__main__':
    main()
