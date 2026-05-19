"""
Shared data loaders & statistics for v8 OHBM figures.

LORO  -> classification accuracy (LDA)  -> Figure 2 Panel A, Figure 1 Panel C
LOCO  -> hue-interpolation MAE (FE)     -> Figure 2 Panel B, Figure 1 Panel D
SRM   -> individual disparities         -> Figure 2 Panel D
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #
PROJ = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis')
LORO_DIR = PROJ / 'analysis/phase3_decoder_comparing/results/loro/procrustes'
LOCO_DIR = PROJ / 'analysis/phase3_decoder_comparing/results/loco/procrustes'
SRM_CSV  = PROJ / 'analysis/phase2_SRM_across_between/results/c010/individual_disparities_long.csv'

HC_SUBS  = [f'sub-{i:02d}' for i in range(1, 8)]
CVD_SUBS = ['sub-08', 'sub-09', 'sub-10']
ALL_SUBS = HC_SUBS + CVD_SUBS
ROI_KEYS = ['V1', 'V2', 'V3', 'V4']        # on-disk keys
ROI_LBLS = ['V1', 'V2', 'V3', 'hV4']        # display labels

# Color conventions (per task spec)
HC_COLOR     = '#1f77b4'
CVD_COLOR    = '#ff7f0e'
SUB08_COLOR  = '#ffbb78'   # light orange (deutan)
SUB09_COLOR  = '#d62728'   # deeper red-orange (protan)
SUB10_COLOR  = '#ffe6c2'   # pale orange (mild)

# 8 isoluminant DKL hue angles (deg, CCW from red 0°)
HUE_ANGLES_DEG = np.arange(0, 360, 45)


# --------------------------------------------------------------------------- #
# LORO loaders
# --------------------------------------------------------------------------- #
def load_loro_subject(sub: str) -> dict:
    fp = LORO_DIR / f'{sub}_performance_raw.json'
    with open(fp) as f:
        return json.load(f)


def loro_acc_per_subject_roi(model: str = 'LDA') -> pd.DataFrame:
    """Return DataFrame: subject, group, roi, mean_acc_exact, mean_mae."""
    rows = []
    for sub in ALL_SUBS:
        d = load_loro_subject(sub)
        grp = d['subject_group']  # HC or CVD
        for roi in ROI_KEYS:
            folds = d['results']['procrustes'][roi][model]
            accs  = [f['acc_exact'] for f in folds]
            maes  = [f['mae']       for f in folds]
            rows.append({
                'subject': sub,
                'group':   grp,
                'roi':     roi,
                'acc':     float(np.mean(accs)),
                'mae':     float(np.mean(maes)),
            })
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# LOCO loaders
# --------------------------------------------------------------------------- #
def load_loco_subject(sub: str) -> dict:
    fp = LOCO_DIR / f'{sub}_loco.json'
    with open(fp) as f:
        return json.load(f)


def loco_mae_per_subject_roi(model: str = 'ForwardEncoding') -> pd.DataFrame:
    """Return DataFrame: subject, group, roi, overall_mae."""
    rows = []
    for sub in ALL_SUBS:
        d = load_loco_subject(sub)
        grp = d['subject_group']
        for roi in ROI_KEYS:
            entry = d['results'][roi][model]
            rows.append({
                'subject': sub,
                'group':   grp,
                'roi':     roi,
                'mae':     float(entry['overall_mae']),
            })
    return pd.DataFrame(rows)


def loco_fold_predictions(sub: str, roi: str, model: str = 'ForwardEncoding'):
    """Return (test_hues_deg [n_colors], pred_hues_deg_mean_over_runs [n_colors],
              all_pred_hues [n_colors x n_runs]) for a given subject/ROI/model.

    Each fold holds out 1 color and predicts it on each of the 6 runs."""
    d = load_loco_subject(sub)
    folds = d['results'][roi][model]['fold_results']
    test_hues = []
    pred_means = []
    pred_all = []
    for f in folds:
        th = float(f['test_hue'])
        preds = np.asarray(f['pred_hues'], dtype=float)
        # circular mean
        mean_pred = _circ_mean_deg(preds)
        test_hues.append(th)
        pred_means.append(mean_pred)
        pred_all.append(preds)
    return (np.asarray(test_hues),
            np.asarray(pred_means),
            np.asarray(pred_all))


def _circ_mean_deg(angles_deg: np.ndarray) -> float:
    a = np.deg2rad(angles_deg)
    s = np.sin(a).mean()
    c = np.cos(a).mean()
    return float(np.rad2deg(np.arctan2(s, c)) % 360)


# --------------------------------------------------------------------------- #
# SRM disparities
# --------------------------------------------------------------------------- #
def load_srm_long() -> pd.DataFrame:
    return pd.read_csv(SRM_CSV)


def srm_crawford_howell(df_long: pd.DataFrame) -> pd.DataFrame:
    """
    Crawford & Howell modified t for each CVD subject vs HC distribution per ROI.
    t = (X_pt - mean_HC) / (SD_HC * sqrt((n+1)/n)), df = n-1.
    """
    from scipy import stats
    out = []
    for roi in ROI_KEYS:
        sub_df = df_long[df_long['roi'] == roi]
        hc = sub_df[sub_df['group'] == 'HC']['disparity'].dropna().values
        n = len(hc)
        if n < 2:
            continue
        m = float(np.mean(hc))
        s = float(np.std(hc, ddof=1))
        for _, row in sub_df[sub_df['group'] == 'CVD'].iterrows():
            x = float(row['disparity'])
            if np.isnan(x) or s == 0:
                t = np.nan
                p = np.nan
                z = np.nan
            else:
                t = (x - m) / (s * np.sqrt((n + 1.0) / n))
                p = 2.0 * (1.0 - stats.t.cdf(abs(t), df=n - 1))
                z = (x - m) / s
            out.append({
                'subject': row['subject_id'],
                'roi':     roi,
                'disparity': x,
                'hc_mean': m,
                'hc_sd':   s,
                'z':       z,
                't':       t,
                'df':      n - 1,
                'p':       p,
            })
    return pd.DataFrame(out)


# --------------------------------------------------------------------------- #
# Group statistics
# --------------------------------------------------------------------------- #
def hedges_g(x: np.ndarray, y: np.ndarray) -> float:
    """Hedges' g with small-sample correction J."""
    nx, ny = len(x), len(y)
    sx, sy = np.std(x, ddof=1), np.std(y, ddof=1)
    sp = np.sqrt(((nx - 1) * sx**2 + (ny - 1) * sy**2) / (nx + ny - 2))
    if sp == 0:
        return np.nan
    d = (np.mean(x) - np.mean(y)) / sp
    df = nx + ny - 2
    J = 1.0 - 3.0 / (4.0 * df - 1.0) if df > 1 else 1.0
    return float(J * d)


def exact_perm_p_onetail(hc: np.ndarray, cvd: np.ndarray,
                         direction: str = 'cvd_greater') -> float:
    """Exact one-tailed permutation p (CVD mean > HC mean by default)."""
    from itertools import combinations
    all_v = np.concatenate([hc, cvd])
    n = len(all_v); k = len(hc)
    obs = np.mean(cvd) - np.mean(hc)
    cnt = tot = 0
    for idx in combinations(range(n), k):
        mask = np.zeros(n, dtype=bool); mask[list(idx)] = True
        d = np.mean(all_v[~mask]) - np.mean(all_v[mask])
        if direction == 'cvd_greater':
            if d >= obs: cnt += 1
        else:
            if d <= obs: cnt += 1
        tot += 1
    return cnt / tot


def group_compare(df: pd.DataFrame, value_col: str,
                  perm_direction: str = 'cvd_greater') -> pd.DataFrame:
    """Per-ROI Welch's t-test + exact permutation + Hedges' g."""
    from scipy import stats
    rows = []
    for roi in ROI_KEYS:
        hc = df[(df['roi'] == roi) & (df['group'] == 'HC')][value_col].values
        cvd = df[(df['roi'] == roi) & (df['group'] == 'CVD')][value_col].values
        t, p2 = stats.ttest_ind(hc, cvd, equal_var=False)
        p_perm = exact_perm_p_onetail(hc, cvd, perm_direction)
        g = hedges_g(hc, cvd)
        rows.append({
            'roi':         roi,
            'hc_mean':     float(np.mean(hc)),
            'hc_sd':       float(np.std(hc, ddof=1)),
            'cvd_mean':    float(np.mean(cvd)),
            'cvd_sd':      float(np.std(cvd, ddof=1)),
            't':           float(t),
            'p_welch_2t':  float(p2),
            'p_perm_1t':   float(p_perm),
            'g_HC_vs_CVD': float(g),
            'n_hc':        len(hc),
            'n_cvd':       len(cvd),
        })
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# Helper: convert hue angle (deg) -> sRGB approx of the 8 stimulus colors
# --------------------------------------------------------------------------- #
def hue_deg_to_srgb(deg: float) -> Tuple[float, float, float]:
    """Approximate the 8 isoluminant DKL stimuli on a unit-saturation ring.
    Returns (r,g,b) in [0,1]."""
    import colorsys
    # The 8 stimulus angles map to (red, orange, yellow, green, cyan, blue, purple, magenta)
    # We use HSV with V chosen to keep apparent luminance moderate.
    h = (deg % 360) / 360.0
    rgb = colorsys.hsv_to_rgb(h, 0.62, 0.95)
    return rgb


if __name__ == '__main__':
    print('LORO accuracies (LDA):')
    print(loro_acc_per_subject_roi('LDA').pivot(index='subject', columns='roi', values='acc'))
    print('\nLOCO MAE (ForwardEncoding):')
    print(loco_mae_per_subject_roi('ForwardEncoding').pivot(index='subject', columns='roi', values='mae'))
    print('\nLORO group test (LDA acc, perm: CVD<HC):')
    print(group_compare(loro_acc_per_subject_roi('LDA'), 'acc', 'cvd_less'))
    print('\nLOCO group test (FE MAE, perm: CVD>HC):')
    print(group_compare(loco_mae_per_subject_roi('ForwardEncoding'), 'mae', 'cvd_greater'))
    print('\nSRM C&H per CVD:')
    print(srm_crawford_howell(load_srm_long()))
