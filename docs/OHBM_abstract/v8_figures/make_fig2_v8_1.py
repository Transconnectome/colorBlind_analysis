"""
Figure 2 v8.1 — OHBM 2026 dissociation narrative (FE-unified).

Changes vs v8:
- Panel A: LORO uses ForwardEncoding (not LDA), chance line at 0.125,
  individual dots overlaid; ylim 0.0-1.0.
- Panel C: REPLACED — HC-only observed LOCO MAE vs label-permutation null
  per ROI. Only hV4 exceeds its null (paired t one-tailed p=.026),
  establishing it as the locus where interpolation is well-defined.
- Panels B, D: unchanged in structure (still FE LOCO + SRM).

[A | B]
[C | D]
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

from _data import (
    ROI_KEYS, ROI_LBLS, HC_SUBS, CVD_SUBS,
    HC_COLOR, CVD_COLOR, SUB08_COLOR, SUB09_COLOR, SUB10_COLOR,
    loro_acc_per_subject_roi, loco_mae_per_subject_roi,
    load_loco_subject,
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
               star_roi: str | None = None,
               trend_roi: str | None = None,
               ylim=None, perm_dir='cvd_greater'):
    """Generic 4-ROI x 2-group bar plot with SEM error bars + individual dots."""
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

    rng = np.random.default_rng(1)
    for i, roi in enumerate(rois):
        hc_v = df[(df['roi'] == roi) & (df['group'] == 'HC')][value_col].values
        cvd_v = df[(df['roi'] == roi) & (df['group'] == 'CVD')][value_col].values
        ax.scatter(np.full_like(hc_v, x[i] - w/2) + rng.uniform(-0.06, 0.06, len(hc_v)),
                   hc_v, s=12, color='white', edgecolor='#0d3b66', linewidth=0.6, zorder=4)
        ax.scatter(np.full_like(cvd_v, x[i] + w/2) + rng.uniform(-0.06, 0.06, len(cvd_v)),
                   cvd_v, s=12, color='white', edgecolor='#7a3a05', linewidth=0.6, zorder=4)

    if yref is not None:
        ax.axhline(yref, ls='--', lw=0.8, color='gray', alpha=0.7)

    ax.set_xticks(x); ax.set_xticklabels(ROI_LBLS, fontsize=10)
    ax.set_ylabel(ylabel, fontsize=10)
    ax.set_title(title, loc='left', fontweight='bold', pad=18, fontsize=10.5)
    if ylim is not None: ax.set_ylim(*ylim)
    ax.legend(loc='upper left', bbox_to_anchor=(0.0, -0.12), ncol=2,
              frameon=False, fontsize=8)

    gc = group_compare(df, value_col, perm_dir)
    # Significance labels: placed near the top of the plot area, larger font
    if ylim is not None:
        y_text = ylim[1] - (ylim[1] - ylim[0]) * 0.06
    else:
        y_text = max([max(hc_means[i] + hc_sems[i], cvd_means[i] + cvd_sems[i])
                      for i in range(len(rois))]) * 1.20

    for i, roi in enumerate(rois):
        row = gc[gc['roi'] == roi].iloc[0]
        p = row['p_perm_1t']
        g = row['g_HC_vs_CVD']
        if star_roi and roi == star_roi:
            label = f'*\np={p:.3f}\n|g|={abs(g):.2f}'
            color = 'black'; weight = 'bold'; fs = 10.5
        elif trend_roi and roi == trend_roi:
            label = f'(trend)\np={p:.3f}'
            color = 'dimgray'; weight = 'bold'; fs = 10
        else:
            label = 'n.s.'
            color = 'dimgray'; weight = 'bold'; fs = 10
        ax.text(x[i], y_text, label, ha='center', va='top',
                fontsize=fs, color=color, fontweight=weight)
    return gc


# --------------------------------------------------------------------------- #
def panel_A(ax):
    """LORO ForwardEncoding accuracy — preserved within HC envelope."""
    df = loro_acc_per_subject_roi('ForwardEncoding')
    gc = _bar_group(ax, df, 'acc',
                    ylabel='LORO classification accuracy (FE)',
                    title='A  LORO classification — preserved (FE-unified readout)',
                    yref=0.125,
                    perm_dir='cvd_less',
                    ylim=(0.0, 1.0))
    return df, gc


def panel_B(ax):
    df = loco_mae_per_subject_roi('ForwardEncoding')
    gc = _bar_group(ax, df, 'mae',
                    ylabel='LOCO MAE (degrees)',
                    title='B  LOCO interpolation — impaired in CVD',
                    yref=90.0,
                    star_roi='V4', trend_roi='V2',
                    perm_dir='cvd_greater',
                    ylim=(0, 160))
    return df, gc


def _hc_null_per_roi():
    """For each ROI, return HC observed mean MAE, HC null mean (avg of per-subject
    null_mean), and a paired one-tailed t-test p (obs < null) across HC subjects."""
    rows = []
    for roi in ROI_KEYS:
        obs_vals = []
        null_means = []
        null_sds = []
        for s in HC_SUBS:
            d = load_loco_subject(s)
            fe = d['results'][roi]['ForwardEncoding']
            obs_vals.append(fe['overall_mae'])
            null_means.append(fe['permutation']['null_mean'])
            null_sds.append(fe['permutation']['null_std'])
        obs = np.asarray(obs_vals)
        nm  = np.asarray(null_means)
        diffs = obs - nm                # negative if obs < null (good interp.)
        t, p2 = stats.ttest_1samp(diffs, 0)
        p_one = p2 / 2 if t < 0 else 1 - p2 / 2  # one-tailed: obs < null
        rows.append({
            'roi': roi,
            'obs_mean': float(obs.mean()),
            'obs_sd':   float(obs.std(ddof=1)),
            'null_mean': float(nm.mean()),
            'null_sd':   float(np.mean(null_sds)),
            't': float(t),
            'p_paired_1t': float(p_one),
            'obs_vals': obs.tolist(),
            'null_vals': nm.tolist(),
        })
    return rows


def panel_C(ax):
    """HC LOCO observed MAE vs label-permutation null per ROI.
    Only hV4 exceeds its null — establishes the locus."""
    rows = _hc_null_per_roi()
    x = np.arange(len(ROI_KEYS))
    w = 0.36

    obs_m = [r['obs_mean'] for r in rows]
    null_m = [r['null_mean'] for r in rows]
    # SEM of observed across HC subjects (n=7)
    obs_sem = [r['obs_sd']/np.sqrt(len(HC_SUBS)) for r in rows]
    # SD of null across subjects (we plot avg null SD as gray band)
    null_sd = [r['null_sd'] for r in rows]

    ax.bar(x - w/2, obs_m, width=w, yerr=obs_sem, capsize=2.5,
           color=HC_COLOR, edgecolor='white', linewidth=0.5,
           label='HC observed (FE)')
    ax.bar(x + w/2, null_m, width=w, yerr=null_sd, capsize=2.5,
           color='lightgray', edgecolor='dimgray', linewidth=0.5,
           label='label-perm null (mean ± avg SD)')

    # individual HC dots overlaid on observed bars
    rng = np.random.default_rng(2)
    for i, r in enumerate(rows):
        ov = np.asarray(r['obs_vals'])
        ax.scatter(np.full_like(ov, x[i] - w/2) + rng.uniform(-0.06, 0.06, len(ov)),
                   ov, s=12, color='white', edgecolor='#0d3b66',
                   linewidth=0.6, zorder=4)

    # chance line (no text label)
    ax.axhline(90.0, ls='--', lw=0.8, color='gray', alpha=0.7)

    # annotate p per ROI — top of plot area, larger font
    ax.set_ylim(0, 135)
    y_text = 135 - 135 * 0.06
    for i, r in enumerate(rows):
        p = r['p_paired_1t']
        if p < 0.05:
            label = f'*\np={p:.3f}'
            color = 'black'; weight = 'bold'; fs = 10.5
        else:
            label = f'n.s.\np={p:.3f}'
            color = 'dimgray'; weight = 'bold'; fs = 10
        ax.text(x[i], y_text, label, ha='center', va='top',
                fontsize=fs, color=color, fontweight=weight)

    ax.set_xticks(x); ax.set_xticklabels(ROI_LBLS, fontsize=10)
    ax.set_ylabel('LOCO MAE (degrees)', fontsize=10)
    ax.set_title('C  HC LOCO vs label-perm null — only hV4 exceeds',
                 loc='left', fontweight='bold', pad=18, fontsize=10.5)
    ax.legend(loc='upper left', bbox_to_anchor=(0.0, -0.12), ncol=2,
              frameon=False, fontsize=8)
    return rows


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
        for roi, xx, yy in zip(ROI_KEYS, xs, ys):
            row = sub[sub['roi'] == roi]
            if len(row):
                p = float(row['p'].values[0])
                if p < 0.05:
                    ax.text(xx, yy + 0.18, f'p={p:.3f}*',
                            fontsize=7, ha='center', color='black')

    ax.axhspan(-2, 2, color=HC_COLOR, alpha=0.08, zorder=0)
    ax.axhline(0, color=HC_COLOR, ls='--', lw=0.7, alpha=0.8)
    ax.text(3.45, 0, 'HC mean', va='center', fontsize=6.5, color=HC_COLOR)
    ax.axhline(2, color='dimgray', ls=':', lw=0.6, alpha=0.7)
    ax.text(3.45, 2, '|z|=2', va='center', fontsize=6.5, color='gray')

    ax.set_xticks(x); ax.set_xticklabels(ROI_LBLS, fontsize=10)
    ax.set_ylabel('SRM disparity z-score\n(Crawford & Howell vs HC ref.)', fontsize=10)
    ax.set_title('D  SRM disparity — individual convergence',
                 loc='left', fontweight='bold', pad=18, fontsize=10.5)
    ax.set_xlim(-0.5, 3.7)
    ax.set_ylim(-3.0, 6.5)
    ax.legend(loc='upper left', bbox_to_anchor=(0.0, -0.12), ncol=3,
              frameon=False, fontsize=8)


# --------------------------------------------------------------------------- #
def main():
    fig, axes = plt.subplots(2, 2, figsize=(10.0, 8.4))
    fig.subplots_adjust(left=0.085, right=0.97, top=0.96, bottom=0.08,
                        hspace=0.72, wspace=0.32)

    df_loro, gc_loro = panel_A(axes[0, 0])
    df_loco, gc_loco = panel_B(axes[0, 1])
    null_rows = panel_C(axes[1, 0])
    panel_D(axes[1, 1])

    fig.savefig(OUT_DIR / 'Figure_2_v8_1.pdf')
    fig.savefig(OUT_DIR / 'Figure_2_v8_1.png', dpi=350)
    plt.close(fig)
    print('Wrote', OUT_DIR / 'Figure_2_v8_1.{pdf,png}')

    out = {
        'loro_group_test_FE': gc_loro.to_dict(orient='records'),
        'loco_group_test_FE': gc_loco.to_dict(orient='records'),
        'hc_null_per_roi':    null_rows,
        'srm_crawford_howell': srm_crawford_howell(load_srm_long()).to_dict(orient='records'),
    }
    with open(OUT_DIR / 'Figure_2_v8_1_numbers.json', 'w') as f:
        json.dump(out, f, indent=2)
    print('Wrote', OUT_DIR / 'Figure_2_v8_1_numbers.json')


if __name__ == '__main__':
    main()
