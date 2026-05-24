"""
LOCO confusion matrices — "which colors get confused with which?"

For each subject:
  - 8 held-out colors x 6 runs = 48 predicted angles per subject per ROI
  - Bin each predicted angle to nearest of 8 hues (45° bins)
  - 8x8 confusion: row=true held-out hue, col=predicted hue (nearest of 8)
  - Row-normalize so each row sums to 1

HC mean: should be diagonal-heavy with adjacent-color confusion bands
        (good interpolation puts predictions back near the true hue).
CVD (sub-09 protan): expected off-diagonal pattern, especially red<->green.
sub-10 (mild): closer to HC mean (specificity control).

Colors are arranged in canonical circular order (Red → Magenta = 0° → 315°).

ROIs shown: hV4 (LOCO locus, group dissociation) and V1 (sub-09 strongest individual).
"""
from __future__ import annotations
from pathlib import Path
import json
import numpy as np
import matplotlib.pyplot as plt

PROJ = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis')
LOCO_DIR = PROJ/'analysis/phase3_decoder_comparing/results/loco/procrustes'
OUT = PROJ/'docs/OHBM_abstract/v9_figures'

HUE_LABELS = ['Red','Orange','Yellow','Green','Cyan','Blue','Purple','Magenta']
HUE_ANGLES = np.arange(0, 360, 45)
HC = [f'sub-{i:02d}' for i in range(1,8)]
CVD = ['sub-08','sub-09','sub-10']


def load_loco(sub, roi):
    with open(LOCO_DIR/f'{sub}_loco.json') as f:
        d = json.load(f)
    return d['results'][roi]['ForwardEncoding']['fold_results']


def bin_to_8(angle: float) -> int:
    """Nearest of 8 canonical hues. Returns 0..7."""
    return int(round((angle % 360) / 45.0)) % 8


def confusion(sub, roi):
    """Returns 8x8 row-normalized matrix."""
    folds = load_loco(sub, roi)
    M = np.zeros((8,8), dtype=float)
    for fr in folds:
        true_idx = bin_to_8(fr['test_hue'])
        for p in fr['pred_hues']:
            M[true_idx, bin_to_8(float(p))] += 1
    row_sums = M.sum(1, keepdims=True)
    row_sums[row_sums == 0] = 1
    return M / row_sums


def plot_matrix(ax, M, title, *, cmap='viridis', vmin=0, vmax=1, show_cbar=True):
    im = ax.imshow(M, cmap=cmap, vmin=vmin, vmax=vmax, aspect='equal')
    # Highlight diagonal
    for k in range(8):
        ax.add_patch(plt.Rectangle((k-0.5, k-0.5), 1, 1, fill=False,
                                    edgecolor='white', lw=1.2, zorder=10))
    ax.set_xticks(range(8)); ax.set_yticks(range(8))
    ax.set_xticklabels(HUE_LABELS, rotation=45, ha='right', fontsize=8)
    ax.set_yticklabels(HUE_LABELS, fontsize=8)
    ax.set_xlabel('Predicted hue', fontsize=9)
    ax.set_ylabel('True (held-out) hue', fontsize=9)
    ax.set_title(title, fontsize=10.5, weight='bold')
    if show_cbar:
        plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    return im


def main():
    # For both V1 and hV4: 4 columns x 2 rows
    # Row 1: hV4 (LOCO locus)
    # Row 2: V1   (sub-09 SRM locus)
    # Columns: HC mean | sub-08 deutan | sub-09 protan | sub-10 mild
    rois = [('V4','hV4'),('V1','V1')]
    fig, axes = plt.subplots(2, 4, figsize=(17, 9))
    plt.subplots_adjust(wspace=0.35, hspace=0.45, left=0.05, right=0.97,
                         top=0.92, bottom=0.07)

    for r, (key, lbl) in enumerate(rois):
        # HC mean confusion
        hc_M = np.mean([confusion(s, key) for s in HC], axis=0)
        plot_matrix(axes[r,0], hc_M,
                    f'{lbl} — HC mean (n=7)\ndiagonal = correct')
        # CVD
        for c, sub in enumerate(CVD, start=1):
            M = confusion(sub, key)
            stype = {'sub-08':'deutan','sub-09':'protan','sub-10':'mild'}[sub]
            plot_matrix(axes[r,c], M,
                        f'{lbl} — {sub} ({stype})')

    fig.suptitle('LOCO confusion matrices — which held-out hues get put back where?\n'
                 '(row = true held-out hue, column = predicted hue binned to nearest of 8)',
                 fontsize=13, weight='bold', y=0.99)
    out = OUT/'loco_confusion_v9_draft.png'
    fig.savefig(out, dpi=180, bbox_inches='tight')
    print('wrote:', out)

    # Print diag values for quick read
    print('\nDiagonal accuracy per ROI x subject (mean of diag):')
    for key, lbl in rois:
        hc_diag = np.mean([np.mean(np.diag(confusion(s, key))) for s in HC])
        print(f'  {lbl} HC mean diag={hc_diag:.2f}')
        for s in CVD:
            d = np.mean(np.diag(confusion(s, key)))
            print(f'    {s}: diag={d:.2f}')


if __name__ == '__main__':
    main()
