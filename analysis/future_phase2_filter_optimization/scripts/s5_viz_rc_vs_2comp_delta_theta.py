"""S5 visualization: R+C vs 2-Comp per-color δθ (L8 modality, K=6).

Two panels per (subject, ROI):
  (a) Bar chart side-by-side: δθ per color, R+C vs 2-Comp
  (b) Polar/angular plot: δθ as deviation from each base hue (0°, 45°, ..., 315°)

Output: results/s5_all_paths/viz_rc_vs_2comp_delta_theta_{subject}_{roi}.png
"""

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
S5_DIR = ROOT / "results" / "s5_all_paths"

COLOR_NAMES = ['red', 'orange', 'yellow', 'green', 'cyan', 'blue', 'purple', 'magenta']
BASE_HUES = np.arange(0, 360, 45)
HEX = ['#e02430', '#f08020', '#f0d020', '#40b048', '#30b0b0', '#3060d0', '#7040b0', '#c040a0']

CELLS = [
    ('sub-08', 'V1', 'deutan', 6),
    ('sub-08', 'V4', 'deutan', 6),
    ('sub-09', 'V1', 'protan', 10),
    ('sub-09', 'V4', 'protan', 10),
]


def load_fit(sub, roi, dlam):
    with open(S5_DIR / f"{sub}_{roi}_sigma21.json") as f:
        d = json.load(f)
    rc = next(
        (f for f in d['fits']
         if f['model'] == 'R+C'
         and f['loss_target'] == 'L8_modality_5050'
         and abs(f.get('delta_lambda_nm', 0) - dlam) < 0.5),
        None,
    )
    tc = next(
        (f for f in d['fits']
         if f['model'] == '2-Comp'
         and f['loss_target'] == 'L8_modality_5050'),
        None,
    )
    return rc, tc


def panel_bar(ax, d_rc, d_2c, sub, roi, rc_lbl, tc_lbl):
    x = np.arange(8)
    w = 0.38
    ax.bar(x - w / 2, d_rc, w, label=f'R+C ({rc_lbl})', color='#4a78c4', edgecolor='black', linewidth=0.5)
    ax.bar(x + w / 2, d_2c, w, label=f'2-Comp ({tc_lbl})', color='#d97a3e', edgecolor='black', linewidth=0.5)
    for i, (a, b) in enumerate(zip(d_rc, d_2c)):
        if a * b < 0:
            ax.axvspan(i - 0.5, i + 0.5, alpha=0.12, color='red', zorder=0)
    ax.axhline(0, color='black', linewidth=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels(COLOR_NAMES, rotation=30, ha='right', fontsize=9)
    ax.set_ylabel('δθ (deg)')
    ax.set_title(f'{sub} {roi} — per-color δθ (L8 modality, K=6)\n'
                 f'red shading = sign disagreement', fontsize=10)
    ax.legend(loc='upper right', fontsize=8)
    ax.grid(True, alpha=0.3, axis='y')


def panel_polar(ax, d_rc, d_2c, sub, roi):
    theta_base = np.deg2rad(BASE_HUES)
    r_base = np.ones(8) * 1.0

    # base ring
    ax.plot(theta_base, r_base, 'o-', color='gray', markersize=8, linewidth=1.5, label='HC base')
    for i, (t, c) in enumerate(zip(theta_base, HEX)):
        ax.scatter(t, 1.0, color=c, s=80, zorder=5, edgecolors='black', linewidth=0.5)

    # R+C shifted
    theta_rc = theta_base + np.deg2rad(d_rc)
    ax.scatter(theta_rc, r_base * 1.15, marker='^', color='#4a78c4', s=70,
               label='R+C', zorder=4, edgecolors='black', linewidth=0.5)
    for i, (t0, t1) in enumerate(zip(theta_base, theta_rc)):
        ax.plot([t0, t1], [1.0, 1.15], '-', color='#4a78c4', alpha=0.5, linewidth=1)

    # 2-Comp shifted
    theta_2c = theta_base + np.deg2rad(d_2c)
    ax.scatter(theta_2c, r_base * 1.3, marker='s', color='#d97a3e', s=70,
               label='2-Comp', zorder=4, edgecolors='black', linewidth=0.5)
    for i, (t0, t1) in enumerate(zip(theta_base, theta_2c)):
        ax.plot([t0, t1], [1.0, 1.3], '-', color='#d97a3e', alpha=0.5, linewidth=1)

    ax.set_ylim(0, 1.5)
    ax.set_yticks([])
    ax.set_theta_zero_location('E')
    ax.set_theta_direction(1)
    ax.set_xticks(theta_base)
    ax.set_xticklabels([f'c{i+1}\n{n}' for i, n in enumerate(COLOR_NAMES)], fontsize=8)
    ax.set_title(f'{sub} {roi} — angular shift\n(inner: HC base, mid: R+C, outer: 2-Comp)',
                 fontsize=10, pad=15)
    ax.legend(loc='lower right', bbox_to_anchor=(1.15, -0.05), fontsize=8)


def main():
    fig, axes = plt.subplots(4, 2, figsize=(13, 18),
                              gridspec_kw={'width_ratios': [1.4, 1]})

    for row, (sub, roi, family, dlam) in enumerate(CELLS):
        rc, tc = load_fit(sub, roi, dlam)
        if rc is None or tc is None:
            print(f"  ⚠ {sub} {roi}: fit missing")
            continue
        d_rc = np.array(rc['delta_theta_at_best'])
        d_2c = np.array(tc['delta_theta_at_best'])

        g = rc['g_best']
        bs = tc.get('beta_s_best', np.nan)
        bc = tc.get('beta_c_best', np.nan)
        rc_lbl = f"Δλ={dlam},g={g:.2f}"
        tc_lbl = f"βs={bs:.0f}°,βc={bc:+.0f}°"

        # bar
        panel_bar(axes[row, 0], d_rc, d_2c, sub, roi, rc_lbl, tc_lbl)
        # polar (need projection switch)
        axes[row, 1].remove()
        ax_pol = fig.add_subplot(4, 2, row * 2 + 2, projection='polar')
        panel_polar(ax_pol, d_rc, d_2c, sub, roi)

        cos = float(np.dot(d_rc, d_2c) / (np.linalg.norm(d_rc) * np.linalg.norm(d_2c) + 1e-12))
        mae = float(np.mean(np.abs(d_rc - d_2c)))
        sa = int(sum(1 for a, b in zip(d_rc, d_2c) if a * b >= 0))
        axes[row, 0].text(0.02, 0.97,
                          f"cos={cos:+.2f}  MAE={mae:.1f}°  sign={sa}/8",
                          transform=axes[row, 0].transAxes,
                          fontsize=9, va='top',
                          bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.7))

    fig.suptitle("S5 — R+C vs 2-Comp per-color δθ comparison (L8 modality, K=6)",
                 fontsize=13, y=0.995)
    plt.tight_layout(rect=[0, 0, 1, 0.98])

    out = S5_DIR / "viz_rc_vs_2comp_delta_theta.png"
    fig.savefig(out, dpi=140, bbox_inches='tight')
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()
