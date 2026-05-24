"""
RDM diagnostic — does CVD warp the L-M (red-green) cells specifically?

For each ROI:
  1. Correlation-distance RDM (8x8) per subject from SRM-aligned amplitudes.
  2. HC mean RDM + CVD individual RDMs.
  3. CVD - HC mean difference RDM (highlight L-M cells: red/orange vs green/cyan).
  4. 1D: mean dissimilarity vs hue separation (0/45/90/135/180 deg).

This decides:
  (a) which ROI to feature in the poster RDM panel
  (b) whether the 1D "dissimilarity rises monotonically with hue separation" claim holds
      in HC, and visibly fails (or bumps) in CVD.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial.distance import pdist, squareform

PROJ = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis')
SRM_DIR = PROJ / 'analysis/phase2_SRM_across_between/results/c010/combined_with_aligned'
OUT = PROJ / 'docs/OHBM_abstract/v9_figures'

ROIS = [('V1','V1'),('V2','V2'),('V3','V3'),('V4','hV4')]
HC = [f'sub-{i:02d}' for i in range(1,8)]
CVD = ['sub-08','sub-09','sub-10']

HUE_LABELS = ['Red','Orange','Yellow','Green','Cyan','Blue','Purple','Magenta']
HUE_ANGLES = np.arange(0,360,45)

def rdm_corr(X: np.ndarray) -> np.ndarray:
    """X: (8, k) -> 8x8 correlation-distance RDM."""
    return squareform(pdist(X, metric='correlation'))

def hue_sep_deg(i: int, j: int) -> float:
    d = abs(HUE_ANGLES[i] - HUE_ANGLES[j]) % 360
    return min(d, 360 - d)

def main():
    fig = plt.figure(figsize=(18, 14), constrained_layout=False)
    gs = fig.add_gridspec(5, 4, height_ratios=[1, 1, 1, 1, 1.1], hspace=0.45, wspace=0.3)

    diag_summary = []

    for col, (key, lbl) in enumerate(ROIS):
        data = np.load(SRM_DIR / f'{key}_procrustes_aligned_amplitudes.npy',
                       allow_pickle=True).item()
        hc_rdms = np.stack([rdm_corr(data[s]) for s in HC], axis=0)  # (7,8,8)
        hc_mean_rdm = hc_rdms.mean(0)
        cvd_rdms = {s: rdm_corr(data[s]) for s in CVD}

        # Row 0: HC mean RDM
        ax = fig.add_subplot(gs[0, col])
        im = ax.imshow(hc_mean_rdm, cmap='magma', vmin=0, vmax=hc_mean_rdm.max())
        ax.set_xticks(range(8)); ax.set_yticks(range(8))
        ax.set_xticklabels(HUE_LABELS, rotation=45, ha='right', fontsize=7)
        ax.set_yticklabels(HUE_LABELS, fontsize=7)
        ax.set_title(f'{lbl}  HC mean RDM', fontsize=10, weight='bold')
        plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

        # L-M cells highlight: (Red=0, Orange=1) vs (Green=3, Cyan=4)
        lm_pairs = [(0,3),(0,4),(1,3),(1,4)]
        for (i,j) in lm_pairs:
            ax.add_patch(plt.Rectangle((j-0.5,i-0.5),1,1, fill=False, edgecolor='cyan', lw=1.5))
            ax.add_patch(plt.Rectangle((i-0.5,j-0.5),1,1, fill=False, edgecolor='cyan', lw=1.5))

        # Rows 1-3: CVD individual RDMs
        for r, s in enumerate(CVD, start=1):
            ax = fig.add_subplot(gs[r, col])
            rdm = cvd_rdms[s]
            im = ax.imshow(rdm, cmap='magma', vmin=0, vmax=hc_mean_rdm.max())
            ax.set_xticks(range(8)); ax.set_yticks(range(8))
            ax.set_xticklabels(HUE_LABELS, rotation=45, ha='right', fontsize=6)
            ax.set_yticklabels(HUE_LABELS, fontsize=6)
            stype = {'sub-08':'deutan','sub-09':'protan','sub-10':'mild'}[s]
            ax.set_title(f'{lbl}  {s} ({stype}) RDM', fontsize=9)
            plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
            for (i,j) in lm_pairs:
                ax.add_patch(plt.Rectangle((j-0.5,i-0.5),1,1, fill=False, edgecolor='cyan', lw=1.0))
                ax.add_patch(plt.Rectangle((i-0.5,j-0.5),1,1, fill=False, edgecolor='cyan', lw=1.0))

            # Quantify L-M cell change
            lm_hc = np.mean([hc_mean_rdm[i,j] for (i,j) in lm_pairs])
            lm_cvd = np.mean([rdm[i,j] for (i,j) in lm_pairs])
            diag_summary.append({'roi':lbl, 'sub':s, 'type':stype,
                                 'lm_hc':lm_hc, 'lm_cvd':lm_cvd,
                                 'delta_lm':lm_cvd - lm_hc})

        # Row 4: 1D dissimilarity vs hue separation
        ax = fig.add_subplot(gs[4, col])
        seps_unique = [45, 90, 135, 180]
        def by_sep(rdm):
            out = {sep: [] for sep in seps_unique}
            for i in range(8):
                for j in range(i+1, 8):
                    sep = hue_sep_deg(i, j)
                    if sep in out:
                        out[sep].append(rdm[i,j])
            return np.array([np.mean(out[s]) for s in seps_unique])

        hc_curves = np.stack([by_sep(rdm_corr(data[s])) for s in HC], axis=0)
        hc_mean_curve = hc_curves.mean(0)
        hc_sd_curve = hc_curves.std(0, ddof=1)
        ax.fill_between(seps_unique, hc_mean_curve - hc_sd_curve, hc_mean_curve + hc_sd_curve,
                        color='#1f77b4', alpha=0.18, label='HC ±1 SD')
        ax.plot(seps_unique, hc_mean_curve, '-o', color='#1f77b4', lw=2, label='HC mean')
        cvd_styles = [('sub-08','#E07B00','o','-','deutan'),
                      ('sub-09','#C0223D','s','-','protan'),
                      ('sub-10','#F5C26E','^','--','mild')]
        for s, col_, mk, ls, t in cvd_styles:
            curve = by_sep(rdm_corr(data[s]))
            ax.plot(seps_unique, curve, ls, marker=mk, color=col_, lw=1.6,
                    label=f'{s} ({t})')
        ax.set_xlabel('Hue separation (deg)', fontsize=9)
        ax.set_ylabel('Mean correlation distance', fontsize=9)
        ax.set_xticks(seps_unique)
        ax.set_title(f'{lbl}  dissimilarity vs hue separation', fontsize=9, weight='bold')
        ax.grid(alpha=0.25)
        if col == 3:
            ax.legend(fontsize=7, loc='lower right')

    fig.suptitle('SRM RDM diagnostic — which ROI shows CVD warping at L-M cells?',
                 fontsize=13, weight='bold', y=0.995)
    out_png = OUT / 'srm_rdm_diag_v9.png'
    fig.savefig(out_png, dpi=160, bbox_inches='tight')
    print(f'wrote: {out_png}')

    print('\nL-M cell mean dissimilarity (red/orange vs green/cyan):')
    print(f'{"ROI":<6}{"sub":<10}{"type":<10}{"HC_mean":>10}{"CVD":>10}{"Δ":>10}')
    for d in diag_summary:
        print(f"{d['roi']:<6}{d['sub']:<10}{d['type']:<10}"
              f"{d['lm_hc']:>10.3f}{d['lm_cvd']:>10.3f}{d['delta_lm']:>+10.3f}")

if __name__ == '__main__':
    main()
