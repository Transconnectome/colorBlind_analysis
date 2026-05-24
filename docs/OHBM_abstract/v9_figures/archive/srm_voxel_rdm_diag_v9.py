"""
Voxel-space RDM diagnostic — does HC mean show a clean circular hue structure
when computed in raw (Procrustes-aligned voxel) space, bypassing SRM?

For each subject × ROI:
  1. Load (6 runs, 8 colors, n_vox) Procrustes-aligned amplitudes
  2. Average across runs -> (8, n_vox)
  3. Correlation-distance RDM (8x8)
  4. HC mean RDM per ROI

If voxel-space RDM is clean & circulant (low near diagonal, high at opposite),
we use it for the SRM single-case panel instead of the SRM-aligned RDM.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial.distance import pdist, squareform

PROJ = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis')
VOX_DIR = PROJ/'analysis/phase1_procrustes_decoding/results/visualization/full_dataset_C010_with_residuals'
OUT = PROJ/'docs/OHBM_abstract/v9_figures'

ROIS = [('V1','V1'),('V2','V2'),('V3','V3'),('V4','hV4')]
HC = [f'sub-{i:02d}' for i in range(1,8)]
CVD = ['sub-08','sub-09','sub-10']
HUE_LABELS = ['Red','Orange','Yellow','Green','Cyan','Blue','Purple','Magenta']
HUE_ANGLES = np.arange(0,360,45)


def load_voxel_pattern(sub, roi):
    """Returns (8 colors, n_vox) — averaged across 6 runs."""
    p = VOX_DIR/sub/roi/'amplitudes_procrustes.npy'
    a = np.load(p)               # (6 runs, 8 colors, n_vox)
    return a.mean(axis=0)        # (8, n_vox)


def rdm_corr(X):
    return squareform(pdist(X, metric='correlation'))


def hue_sep(i, j):
    d = abs(HUE_ANGLES[i] - HUE_ANGLES[j]) % 360
    return min(d, 360-d)


def circulant_r2(rdm: np.ndarray) -> float:
    """How well does this RDM match a circulant template (distance ∝ hue separation)?
       Returns R^2 of a least-squares fit."""
    sep = np.array([[hue_sep(i,j) for j in range(8)] for i in range(8)])
    iu = np.triu_indices(8, k=1)
    x = sep[iu].astype(float)
    y = rdm[iu]
    # Linear fit y = a + b*x
    A = np.vstack([np.ones_like(x), x]).T
    coef, *_ = np.linalg.lstsq(A, y, rcond=None)
    yhat = A @ coef
    ss_res = ((y - yhat)**2).sum()
    ss_tot = ((y - y.mean())**2).sum()
    return 1 - ss_res/ss_tot if ss_tot > 0 else float('nan')


def main():
    fig, axes = plt.subplots(2, 4, figsize=(16, 8.5),
                              constrained_layout=False)
    plt.subplots_adjust(wspace=0.35, hspace=0.45,
                         top=0.92, bottom=0.07, left=0.05, right=0.97)

    diag = []
    for col, (key, lbl) in enumerate(ROIS):
        hc_rdms = []
        for s in HC:
            X = load_voxel_pattern(s, key)
            hc_rdms.append(rdm_corr(X))
        hc_rdms = np.stack(hc_rdms, axis=0)
        hc_mean = hc_rdms.mean(0)
        hc_r2 = circulant_r2(hc_mean)

        cvd_rdms = {s: rdm_corr(load_voxel_pattern(s, key)) for s in CVD}

        # Row 0: HC mean RDM
        ax = axes[0, col]
        im = ax.imshow(hc_mean, cmap='magma')
        ax.set_xticks(range(8)); ax.set_yticks(range(8))
        ax.set_xticklabels(HUE_LABELS, rotation=45, ha='right', fontsize=7)
        ax.set_yticklabels(HUE_LABELS, fontsize=7)
        ax.set_title(f'{lbl} HC mean RDM (voxel space)\ncirculant R²={hc_r2:.2f}',
                     fontsize=10, weight='bold')
        plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

        # Row 1: 1D dissimilarity vs hue separation
        ax = axes[1, col]
        seps = [45, 90, 135, 180]
        def curve(rdm):
            out = {s: [] for s in seps}
            for i in range(8):
                for j in range(i+1, 8):
                    s_ = hue_sep(i, j)
                    if s_ in out:
                        out[s_].append(rdm[i,j])
            return np.array([np.mean(out[s]) for s in seps])

        hc_curves = np.stack([curve(r) for r in hc_rdms], axis=0)
        hc_m = hc_curves.mean(0); hc_sd = hc_curves.std(0, ddof=1)
        ax.fill_between(seps, hc_m-hc_sd, hc_m+hc_sd, color='#1f77b4',
                         alpha=0.18, label='HC ±1 SD')
        ax.plot(seps, hc_m, '-o', color='#1f77b4', lw=2.0, label='HC mean')
        for s, col_, mk, t in [('sub-08','#E07B00','o','deutan'),
                                ('sub-09','#C0223D','s','protan'),
                                ('sub-10','#F5C26E','^','mild')]:
            ax.plot(seps, curve(cvd_rdms[s]), '-', marker=mk, color=col_, lw=1.6,
                    label=f'{s} ({t})')
        ax.set_xlabel('Hue separation (deg)', fontsize=9)
        ax.set_ylabel('Mean correlation distance', fontsize=9)
        ax.set_xticks(seps)
        ax.set_title(f'{lbl}  dissimilarity vs hue separation', fontsize=9, weight='bold')
        ax.grid(alpha=0.25)
        if col == 3:
            ax.legend(fontsize=7, loc='lower right')

        # Per-subject L-M cell diagnostic
        lm = [(0,3),(0,4),(1,3),(1,4)]
        for s in CVD:
            lm_hc  = np.mean([hc_mean[i,j]      for (i,j) in lm])
            lm_cvd = np.mean([cvd_rdms[s][i,j]  for (i,j) in lm])
            diag.append({'roi':lbl,'sub':s,'lm_hc':lm_hc,'lm_cvd':lm_cvd,
                         'delta':lm_cvd-lm_hc, 'hc_r2':hc_r2})

    fig.suptitle('Voxel-space RDM diagnostic (Procrustes-aligned amplitudes, runs averaged)',
                 fontsize=12.5, weight='bold')
    out_png = OUT/'srm_voxel_rdm_diag_v9.png'
    fig.savefig(out_png, dpi=170, bbox_inches='tight')
    print('wrote:', out_png)

    print(f"\n{'ROI':<6}{'sub':<10}{'circR²':>9}{'HC_LM':>9}{'CVD_LM':>9}{'Δ':>9}")
    for d in diag:
        print(f"{d['roi']:<6}{d['sub']:<10}{d['hc_r2']:>8.2f}{d['lm_hc']:>9.3f}"
              f"{d['lm_cvd']:>9.3f}{d['delta']:>+9.3f}")


if __name__ == '__main__':
    main()
