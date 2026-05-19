"""
Figure 2 v8 — OHBM 2026 dissociation narrative.

[A | B]
[C | D]

A: LORO LDA accuracy (HC vs CVD) per ROI — both groups comparable (n.s.).
B: LOCO MAE (HC vs CVD) per ROI — hV4 dissociation (p=.017, g=1.69).
C: hV4 individual scatter (LOCO MAE).
D: SRM per-subject disparity (Crawford & Howell z).
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

from _data import (
    ROI_KEYS, ROI_LBLS, HC_SUBS, CVD_SUBS,
    HC_COLOR, CVD_COLOR, SUB08_COLOR, SUB09_COLOR, SUB10_COLOR,
    loro_acc_per_subject_roi, loco_mae_per_subject_roi,
    load_srm_long, srm_crawford_howell,
    group_compare,
)

OUT_DIR = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/docs/OHBM_abstract/figures/v8')
OUT_DIR.mkdir(parents=True, exist_ok=True)

mpl.rcParams.update({
    'font.family': 'Helvetica',
    'font.size': 9,
    'axes.linewidth': 0.8,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'pdf.fonttype': 42,
    'ps.fonttype':  42,
})


# --------------------------------------------------------------------------- #
def _bar_group(ax, df, value_col, ylabel, title, *,
               yref: float | None = None,
               yref_label: str = '',
               annotate: dict[str, str] | None = None,
               star_roi: str | None = None,
               trend_roi: str | None = None,
               ylim=None, perm_dir='cvd_greater'):
    """Generic 4-ROI x 2-group bar plot with SEM error bars."""
    rois = ROI_KEYS
    x = np.arange(len(rois))
    w = 0.36

    hc_means, hc_sems = [], []
    cvd_means, cvd_sems = [], []
    for roi in rois:
        hc = df[(df['roi'] == roi) & (df['group'] == 'HC')][value_col].values
        cvd = df[(df['roi'] == roi) & (df['group'] == 'CVD')][value_col].values
        hc_means.append(np.mean(hc));   hc_sems.append(np.std(hc, ddof=1)/np.sqrt(len(hc)))
        cvd_means.append(np.mean(cvd)); cvd_sems.append(np.std(cvd, ddof=1)/np.sqrt(len(cvd)))

    ax.bar(x - w/2, hc_means,  width=w, yerr=hc_sems,  capsize=2.5,
           color=HC_COLOR, edgecolor='white', linewidth=0.5, label='HC (n=7)')
    ax.bar(x + w/2, cvd_means, width=w, yerr=cvd_sems, capsize=2.5,
           color=CVD_COLOR, edgecolor='white', linewidth=0.5, label='CVD (n=3)')

    # subject dots overlaid
    for i, roi in enumerate(rois):
        hc_v = df[(df['roi'] == roi) & (df['group'] == 'HC')][value_col].values
        cvd_v = df[(df['roi'] == roi) & (df['group'] == 'CVD')][value_col].values
        ax.scatter(np.full_like(hc_v, x[i] - w/2) + np.random.uniform(-0.06, 0.06, len(hc_v)),
                   hc_v, s=10, color='white', edgecolor='#0d3b66', linewidth=0.6, zorder=4)
        ax.scatter(np.full_like(cvd_v, x[i] + w/2) + np.random.uniform(-0.06, 0.06, len(cvd_v)),
                   cvd_v, s=10, color='white', edgecolor='#7a3a05', linewidth=0.6, zorder=4)

    if yref is not None:
        ax.axhline(yref, ls='--', lw=0.8, color='gray', alpha=0.7)
        if yref_label:
            ax.text(len(rois) - 0.5, yref, yref_label, ha='right', va='bottom',
                    fontsize=7, color='gray')

    ax.set_xticks(x); ax.set_xticklabels(ROI_LBLS)
    ax.set_ylabel(ylabel); ax.set_title(title, loc='left', fontweight='bold')
    if ylim is not None: ax.set_ylim(*ylim)
    ax.legend(loc='lower right', frameon=False, fontsize=7)

    # annotate significance — place ABOVE each bar pair using the local ymax
    gc = group_compare(df, value_col, perm_dir)
    for i, roi in enumerate(rois):
        row = gc[gc['roi'] == roi].iloc[0]
        p = row['p_perm_1t']
        g = row['g_HC_vs_CVD']
        ymax = max(hc_means[i] + hc_sems[i], cvd_means[i] + cvd_sems[i])
        if star_roi and roi == star_roi:
            label = f'*\np={p:.3f}\n|g|={abs(g):.2f}'
            color = 'black'; weight = 'bold'
        elif trend_roi and roi == trend_roi:
            label = f'(trend)\np={p:.3f}'
            color = 'dimgray'; weight = 'normal'
        else:
            label = 'n.s.'
            color = 'dimgray'; weight = 'normal'

        # Use a y position computed from data range (not ylim) so labels
        # always sit just above the highest error bar of each pair.
        if ylim is not None:
            yspan = ylim[1] - ylim[0]
            y_text = min(ymax + yspan*0.04, ylim[1] - yspan*0.04)
        else:
            y_text = ymax * 1.04
        ax.text(x[i], y_text, label, ha='center', va='bottom',
                fontsize=7, color=color, fontweight=weight)
    return gc


# --------------------------------------------------------------------------- #
def panel_A(ax):
    df = loro_acc_per_subject_roi('LDA')
    gc = _bar_group(ax, df, 'acc',
                    ylabel='LDA classification accuracy',
                    title='A  LORO classification — preserved',
                    yref=0.125, yref_label='chance (1/8)',
                    perm_dir='cvd_less',
                    ylim=(0.0, 1.10))
    return df, gc


def panel_B(ax):
    df = loco_mae_per_subject_roi('ForwardEncoding')
    gc = _bar_group(ax, df, 'mae',
                    ylabel='LOCO MAE (degrees)',
                    title='B  LOCO interpolation — impaired in CVD',
                    yref=90.0, yref_label='chance (90°)',
                    star_roi='V4', trend_roi='V2',
                    perm_dir='cvd_greater',
                    ylim=(0, 145))
    return df, gc


def panel_C(ax, df_loco):
    """hV4 individual scatter."""
    sub_order = HC_SUBS + CVD_SUBS
    hv4 = df_loco[df_loco['roi'] == 'V4'].set_index('subject')

    # HC strip
    hc_vals = [hv4.loc[s, 'mae'] for s in HC_SUBS]
    cvd_vals = {s: hv4.loc[s, 'mae'] for s in CVD_SUBS}

    rng = np.random.default_rng(0)
    hc_x = rng.uniform(-0.12, 0.12, len(hc_vals))
    ax.scatter(hc_x, hc_vals, s=42, color=HC_COLOR, edgecolor='white',
               linewidth=0.7, zorder=3, label='HC')
    # HC mean ± SD
    m = np.mean(hc_vals); sd = np.std(hc_vals, ddof=1)
    ax.hlines(m, -0.3, 0.3, color=HC_COLOR, lw=1.4, zorder=2)
    ax.add_patch(plt.Rectangle((-0.3, m - sd), 0.6, 2*sd, color=HC_COLOR, alpha=0.15, zorder=1))

    # CVD
    cvd_x = {'sub-08': 1.0, 'sub-09': 1.0, 'sub-10': 1.0}
    cvd_colors = {'sub-08': SUB08_COLOR, 'sub-09': SUB09_COLOR, 'sub-10': SUB10_COLOR}
    cvd_labels = {'sub-08': 'sub-08 (deutan)',
                  'sub-09': 'sub-09 (protan)',
                  'sub-10': 'sub-10 (mild)'}
    for i, s in enumerate(CVD_SUBS):
        x = 1.0 + (i - 1) * 0.18
        ax.scatter([x], [cvd_vals[s]], s=70, color=cvd_colors[s],
                   edgecolor='black', linewidth=0.6, zorder=4)
        ax.annotate(cvd_labels[s],
                    xy=(x, cvd_vals[s]),
                    xytext=(x + 0.18, cvd_vals[s]),
                    fontsize=7, va='center',
                    arrowprops=dict(arrowstyle='-', lw=0.4, color='gray'))

    ax.axhline(90, ls='--', lw=0.8, color='gray', alpha=0.7)
    ax.text(1.85, 90, ' chance', va='bottom', fontsize=7, color='gray')

    ax.set_xticks([0, 1])
    ax.set_xticklabels(['HC (n=7)', 'CVD (n=3)'])
    ax.set_xlim(-0.6, 2.4)
    ax.set_ylabel('LOCO MAE at hV4 (degrees)')
    ax.set_title('C  hV4 LOCO — individual subjects', loc='left', fontweight='bold')
    ax.set_ylim(40, 115)
    # HC stats annotation
    ax.text(-0.3, m + sd + 1, f'HC mean ± SD\n{m:.1f} ± {sd:.1f}°',
            ha='left', va='bottom', fontsize=7, color=HC_COLOR)


def panel_D(ax):
    """SRM individual disparity (z-scores vs HC reference) per ROI."""
    ch = srm_crawford_howell(load_srm_long())
    sub_colors = {'sub-08': SUB08_COLOR, 'sub-09': SUB09_COLOR, 'sub-10': SUB10_COLOR}
    sub_marker = {'sub-08': 'o', 'sub-09': 's', 'sub-10': '^'}

    x = np.arange(len(ROI_KEYS))
    offsets = {'sub-08': -0.18, 'sub-09': 0.0, 'sub-10': 0.18}
    for s in CVD_SUBS:
        sub = ch[ch['subject'] == s]
        ys = []
        for roi in ROI_KEYS:
            row = sub[sub['roi'] == roi]
            ys.append(float(row['z'].values[0]) if len(row) else np.nan)
        xs = x + offsets[s]
        ax.plot(xs, ys, lw=0.6, color='gray', alpha=0.5, zorder=1)
        ax.scatter(xs, ys, s=55, color=sub_colors[s], edgecolor='black',
                   linewidth=0.6, marker=sub_marker[s], zorder=3,
                   label={'sub-08': 'sub-08 (deutan)',
                          'sub-09': 'sub-09 (protan)',
                          'sub-10': 'sub-10 (mild)'}[s])
        # annotate strong points
        for roi, xx, yy in zip(ROI_KEYS, xs, ys):
            row = sub[sub['roi'] == roi]
            if len(row):
                p = float(row['p'].values[0])
                if p < 0.05:
                    ax.text(xx, yy + 0.18, f'p={p:.3f}*',
                            fontsize=7, ha='center', color='black')

    # HC reference band: |z|<=2
    ax.axhspan(-2, 2, color=HC_COLOR, alpha=0.08, zorder=0)
    ax.axhline(0, color=HC_COLOR, ls='--', lw=0.7, alpha=0.8)
    ax.text(3.45, 0, 'HC mean', va='center', fontsize=6.5, color=HC_COLOR)
    ax.axhline(2, color='dimgray', ls=':', lw=0.6, alpha=0.7)
    ax.text(3.45, 2, '|z|=2', va='center', fontsize=6.5, color='gray')

    ax.set_xticks(x); ax.set_xticklabels(ROI_LBLS)
    ax.set_ylabel('SRM disparity z-score\n(Crawford & Howell vs HC ref.)')
    ax.set_title('D  SRM disparity — individual', loc='left', fontweight='bold')
    ax.set_xlim(-0.5, 3.7)
    ax.legend(loc='upper left', frameon=False, fontsize=7)


# --------------------------------------------------------------------------- #
def main():
    fig, axes = plt.subplots(2, 2, figsize=(9.4, 7.6))
    fig.subplots_adjust(left=0.085, right=0.97, top=0.94, bottom=0.07,
                        hspace=0.42, wspace=0.30)

    df_loro, gc_loro = panel_A(axes[0, 0])
    df_loco, gc_loco = panel_B(axes[0, 1])
    panel_C(axes[1, 0], df_loco)
    panel_D(axes[1, 1])

    fig.suptitle('Figure 2.  Discrimination preserved (LORO) vs interpolation impaired (LOCO).',
                 fontsize=10, fontweight='bold', x=0.085, y=0.985, ha='left')

    fig.savefig(OUT_DIR / 'Figure_2_v8.pdf')
    fig.savefig(OUT_DIR / 'Figure_2_v8.png', dpi=350)
    plt.close(fig)
    print('Wrote', OUT_DIR / 'Figure_2_v8.{pdf,png}')

    # also dump numbers
    out = {
        'loro_group_test': gc_loro.to_dict(orient='records'),
        'loco_group_test': gc_loco.to_dict(orient='records'),
        'srm_crawford_howell': srm_crawford_howell(load_srm_long()).to_dict(orient='records'),
    }
    with open(OUT_DIR / 'Figure_2_v8_numbers.json', 'w') as f:
        json.dump(out, f, indent=2)
    print('Wrote', OUT_DIR / 'Figure_2_v8_numbers.json')


if __name__ == '__main__':
    main()
