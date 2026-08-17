"""S7 best-models 4-col visualization.

Best (model, λ) per generalization-test criterion + param-stable intersection:
  sub-08 V1: R+C Boehm_mid (Δλ=8), λ=0.25 composite, g=1.90 (7/7 folds stable)
  sub-09 V2: R+C JND_Lamb (Δλ=1.5), λ=0.50 composite, g=2.10 (6/7 folds stable)

4-col convention (cf. s5_viz_behav_4col.py):
  cols = Original | CVD perceives | Filtered pre-image | CVD(Filtered)
  rows = 8 canonical hues (c1=0°..c8=315°)
"""
import math
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

_THIS = Path(__file__).resolve().parent
sys.path.insert(0, str(_THIS))

from stim_lab_render import render_at_hue
from machado_simulator import machado_shifted_hue_at

OUT = _THIS.parent / 'results' / 's7_loss_combo_subset'
OUT.mkdir(parents=True, exist_ok=True)

HUE_8 = np.array([0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0])
COLOR_LABELS = ['c1 R(0°)', 'c2 O(45°)', 'c3 Y(90°)', 'c4 G(135°)',
                'c5 C(180°)', 'c6 B(225°)', 'c7 P(270°)', 'c8 M(315°)']

matplotlib.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Helvetica', 'Arial', 'DejaVu Sans'],
    'font.size': 8, 'axes.titlesize': 9, 'axes.labelsize': 8,
    'xtick.labelsize': 7, 'ytick.labelsize': 7,
})

BEST_MODELS = [
    {
        'subject': 'sub-08', 'family': 'deutan', 'roi': 'V1',
        'delta_lambda': 8.0, 'g': 1.90, 'src': 'Boehm_mid',
        'lambda_rdm': 0.25, 'test_L_gamma': 1.081,
        'fold_stability': '7/7 folds g=1.90 stable',
    },
    {
        'subject': 'sub-09', 'family': 'protan', 'roi': 'V2',
        'delta_lambda': 1.5, 'g': 2.10, 'src': 'JND_Lamb',
        'lambda_rdm': 0.50, 'test_L_gamma': 0.987,
        'fold_stability': '6/7 folds g=2.10 stable (1 outlier sub-04 hold-out)',
    },
]


def forward_rc_hue(theta, delta_lambda, g, family):
    """θ_perceived = θ + (2 − g) · δθ_Machado(θ; Δλ, family)."""
    theta_shifted = machado_shifted_hue_at(delta_lambda, family, theta)[1].item()
    delta_machado = ((theta_shifted - theta + 180) % 360) - 180
    delta_rc = (2.0 - g) * delta_machado
    return (theta + delta_rc) % 360.0


def inverse_rc_filter(theta_target, delta_lambda, g, family, n_steps=720, tol=0.5):
    """θ_stim such that forward_rc(θ_stim) = θ_target (pre-image search)."""
    candidates = np.arange(0, 360.0, 360.0 / n_steps)
    forwards = np.array([forward_rc_hue(c, delta_lambda, g, family) for c in candidates])
    # Find closest forward to target
    diffs = np.abs((forwards - theta_target + 180) % 360 - 180)
    return float(candidates[np.argmin(diffs)])


def make_4col_figure(spec):
    """One subject × ROI: 4 cols (Original | CVD | Filter | CVD(Filter)) × 8 rows."""
    sub = spec['subject']
    fam = spec['family']
    roi = spec['roi']
    dl = spec['delta_lambda']
    g = spec['g']

    fig, axes = plt.subplots(8, 4, figsize=(8, 12), gridspec_kw={'wspace': 0.05, 'hspace': 0.05})
    fig.suptitle(
        f"{sub} ({fam}) {roi} — R+C ({spec['src']} Δλ={dl}nm, g={g:.2f}, λ_RDM={spec['lambda_rdm']:.2f})\n"
        f"Test L_γ={spec['test_L_gamma']:.3f}    Stability: {spec['fold_stability']}",
        fontsize=10, y=0.995,
    )

    for i, theta in enumerate(HUE_8):
        # Col 0: Original (HC perceives the stimulus correctly = θ itself)
        rgb0 = render_at_hue(theta)
        axes[i, 0].imshow(np.asarray(rgb0).reshape(1, 1, 3), aspect='auto')
        axes[i, 0].set_ylabel(f"{COLOR_LABELS[i]}\n(stim θ={theta:.0f}°)", fontsize=7)

        # Col 1: CVD perceives stimulus θ — Machado forward (cone shift only, no compensation)
        theta_cvd = machado_shifted_hue_at(dl, fam, theta)[1].item()
        rgb1 = render_at_hue(theta_cvd)
        axes[i, 1].imshow(np.asarray(rgb1).reshape(1, 1, 3), aspect='auto')

        # Col 2: Filter pre-image — θ_stim such that CVD(filter(θ_stim)) ≈ original θ
        # i.e., apply *inverse* of R+C forward to find a stimulus that, when CVD perceives, looks like θ
        theta_filt = inverse_rc_filter(theta, dl, g, fam)
        rgb2 = render_at_hue(theta_filt)
        axes[i, 2].imshow(np.asarray(rgb2).reshape(1, 1, 3), aspect='auto')

        # Col 3: CVD(Filter applied to original) — forward through both CVD perception and the filter pre-image
        theta_cvd_of_filt = forward_rc_hue(theta_filt, dl, g, fam)
        rgb3 = render_at_hue(theta_cvd_of_filt)
        axes[i, 3].imshow(np.asarray(rgb3).reshape(1, 1, 3), aspect='auto')

        # δθ annotation per row
        delta_rc = (forward_rc_hue(theta, dl, g, fam) - theta + 180) % 360 - 180
        axes[i, 3].set_xlabel(f"δθ={delta_rc:+.1f}°", fontsize=6.5)

        # Hide ticks
        for j in range(4):
            axes[i, j].set_xticks([])
            axes[i, j].set_yticks([])

    # Column headers
    axes[0, 0].set_title('Original\n(stimulus)', fontsize=9)
    axes[0, 1].set_title(f'CVD perceives\n(Machado Δλ={dl}nm)', fontsize=9)
    axes[0, 2].set_title('Filter\n(pre-image)', fontsize=9)
    axes[0, 3].set_title('CVD(Filter)\n(corrected)', fontsize=9)

    plt.tight_layout()
    out_file = OUT / f"S7_BEST_4col_{sub}_{roi}.png"
    plt.savefig(out_file, dpi=160, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {out_file}")
    return out_file


def make_summary_figure(specs):
    """Side-by-side comparison: 2 subjects, 4 cols each, 8 rows."""
    n_models = len(specs)
    fig, axes = plt.subplots(8, 4 * n_models, figsize=(8 * n_models, 12),
                              gridspec_kw={'wspace': 0.05, 'hspace': 0.05})

    for col_offset, spec in enumerate(specs):
        sub = spec['subject']; fam = spec['family']; roi = spec['roi']
        dl = spec['delta_lambda']; g = spec['g']
        c0 = col_offset * 4

        for i, theta in enumerate(HUE_8):
            rgb0 = render_at_hue(theta)
            axes[i, c0].imshow(np.asarray(rgb0).reshape(1, 1, 3), aspect='auto')
            if col_offset == 0:
                axes[i, c0].set_ylabel(f"{COLOR_LABELS[i]}", fontsize=7)

            theta_cvd = machado_shifted_hue_at(dl, fam, theta)[1].item()
            rgb1 = render_at_hue(theta_cvd)
            axes[i, c0 + 1].imshow(np.asarray(rgb1).reshape(1, 1, 3), aspect='auto')

            theta_filt = inverse_rc_filter(theta, dl, g, fam)
            rgb2 = render_at_hue(theta_filt)
            axes[i, c0 + 2].imshow(np.asarray(rgb2).reshape(1, 1, 3), aspect='auto')

            theta_cvd_of_filt = forward_rc_hue(theta_filt, dl, g, fam)
            rgb3 = render_at_hue(theta_cvd_of_filt)
            axes[i, c0 + 3].imshow(np.asarray(rgb3).reshape(1, 1, 3), aspect='auto')

            delta_rc = (forward_rc_hue(theta, dl, g, fam) - theta + 180) % 360 - 180
            axes[i, c0 + 3].set_xlabel(f"δθ={delta_rc:+.1f}°", fontsize=6.5)

            for j in range(4):
                axes[i, c0 + j].set_xticks([])
                axes[i, c0 + j].set_yticks([])

        axes[0, c0].set_title('Original', fontsize=9)
        axes[0, c0 + 1].set_title(f'CVD ({fam})', fontsize=9)
        axes[0, c0 + 2].set_title('Filter', fontsize=9)
        axes[0, c0 + 3].set_title('CVD(Filter)', fontsize=9)

    title = ' | '.join([
        f"{s['subject']} {s['roi']} R+C g={s['g']:.2f} (test L_γ={s['test_L_gamma']:.2f})"
        for s in specs
    ])
    fig.suptitle(title, fontsize=11, y=0.995)
    plt.tight_layout()
    out_file = OUT / "S7_BEST_4col_summary.png"
    plt.savefig(out_file, dpi=160, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {out_file}")


if __name__ == "__main__":
    print("Rendering 4-col best-model figures (S7 generalization-test selection)...")
    for spec in BEST_MODELS:
        make_4col_figure(spec)
    make_summary_figure(BEST_MODELS)
    print("\nDone.")
