"""S6 (trial-level): Bootstrap CI of g via trial-level resampling.

Improvement over s6_bootstrap_g_ci.py (color-set resample, 사용자 catch 2026-05-22):
  - Sampling unit = individual trial (not color/pair)
  - All 8 colors / 8 pairs always preserved (color set fixed)
  - True measurement-noise uncertainty estimate

JND trials: per pair, resample trial rows with replacement, recompute JND
            as mean(level) over last-half reversal trials (staircase standard).
8AFC trials: per color, resample trial responses, recompute accuracy.

Output: results/s6_bootstrap/g_bootstrap_trial.json
"""
import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from rc_1dof import fit_rc_g
from behav_loss import (
    L_behav_alpha, L_behav_gamma, SIGMA_HC,
    compute_hc_jnd_baseline, HC_8AFC_SUBJS, HC_JND_SUBJS, PAIR_HUES,
)

ROOT = SCRIPT_DIR.parents[2]
DATA_DIR = ROOT / "data" / "behavior"
OUT_DIR = SCRIPT_DIR.parent / "results" / "s6_bootstrap"

CVD_INFO = {
    'sub-08': {'family': 'deutan', 'delta_lambda': 6.0},
    'sub-09': {'family': 'protan', 'delta_lambda': 10.0},
}

# Δλ sensitivity grid (3 sources × 2 families)
DELTA_LAMBDA_BY_FAMILY = {
    'deutan': {'DPS_lit': 6.0, 'Boehm_mid': 8.0, 'JND_Lamb': 6.5},  # sub-08
    'protan': {'DPS_lit': 10.0, 'Boehm_low': 3.0, 'JND_Lamb': 1.5},  # sub-09
}

B_DEFAULT = 1000


# ============================================================================
# Trial-level loaders + JND/accuracy recomputation
# ============================================================================

def load_jnd_trials(subject: str) -> pd.DataFrame:
    csv = DATA_DIR / f"{subject}_jnd_ses1_no_filter_trials.csv"
    return pd.read_csv(csv)


def load_8afc_trials(subject: str) -> pd.DataFrame:
    csv = DATA_DIR / f"{subject}_rsvp_8afc_ses1_run1.csv"
    if not csv.exists():
        return None
    df = pd.read_csv(csv)
    return df[df['rt'] > 0]  # filter negative-RT artifact (sub-08 trial 19)


def jnd_per_pair_from_trials(trials_df: pd.DataFrame, last_n_rev: int = 6) -> dict:
    """JND estimate per pair from trial DataFrame using last-N reversal mean.

    Standard staircase convention: per staircase (sc0, sc1), take last N reversal
    trials, average their level, then average across staircases.
    `mean(level)` over ALL trials is biased (staircase starts high and descends).
    """
    out = {}
    for pair in PAIR_HUES.keys():
        sub = trials_df[trials_df['pair_name'] == pair]
        if len(sub) == 0:
            out[pair] = None
            continue
        vals = []
        for sc_id in sub['staircase_id'].unique():
            sc_sub = sub[sub['staircase_id'] == sc_id].sort_values('trial')
            rev = sc_sub[sc_sub['reversal_count'] > 0]
            last_rev = rev.tail(last_n_rev) if len(rev) >= last_n_rev else rev
            if len(last_rev) > 0:
                vals.append(last_rev['level'].mean())
        out[pair] = float(np.mean(vals)) if vals else None
    return out


def accuracy_per_color_from_trials(trials_df: pd.DataFrame) -> np.ndarray:
    """Accuracy per color from 8AFC trial DataFrame."""
    acc = np.zeros(8)
    n = np.zeros(8)
    for _, row in trials_df.iterrows():
        try:
            i = int(row['stimulus_label'].split('_')[1]) - 1
            acc[i] += int(row['correct'])
            n[i] += 1
        except Exception:
            continue
    return acc / np.maximum(n, 1)


# ============================================================================
# Trial-level resampling
# ============================================================================

def resample_jnd_trials_per_pair(trials_df: pd.DataFrame, rng,
                                    last_n_rev: int = 6) -> dict:
    """Per pair × per staircase, resample reversal trials with replacement,
    recompute JND as last-N reversal mean.

    Resample is done on REVERSAL trial pool (not all trials), preserving the
    staircase psychometric estimator. This matches the summary CSV's jnd_mean
    convention (mean of last-N reversals).
    """
    out = {}
    for pair in PAIR_HUES.keys():
        sub = trials_df[trials_df['pair_name'] == pair]
        if len(sub) == 0:
            out[pair] = None
            continue
        sc_vals = []
        for sc_id in sub['staircase_id'].unique():
            sc_sub = sub[sub['staircase_id'] == sc_id].sort_values('trial')
            rev = sc_sub[sc_sub['reversal_count'] > 0]
            if len(rev) == 0:
                continue
            # Use last-N reversals as the resampling pool
            last_rev = rev.tail(last_n_rev) if len(rev) >= last_n_rev else rev
            idx = rng.choice(len(last_rev), size=len(last_rev), replace=True)
            sc_vals.append(last_rev.iloc[idx]['level'].mean())
        out[pair] = float(np.mean(sc_vals)) if sc_vals else None
    return out


def resample_8afc_trials_per_color(trials_df: pd.DataFrame, rng) -> np.ndarray:
    """Per color, resample trial rows, recompute accuracy."""
    acc = np.zeros(8)
    for i in range(8):
        sub = trials_df[trials_df['stimulus_label'] == f'color_{i+1}']
        if len(sub) == 0:
            acc[i] = 0.0
            continue
        idx = rng.choice(len(sub), size=len(sub), replace=True)
        resampled = sub.iloc[idx]
        acc[i] = float(resampled['correct'].mean())
    return acc


# ============================================================================
# Fit g on resampled trial-level data
# ============================================================================

def fit_g_on_trial_resample(family: str, delta_lambda: float,
                              obs_acc: np.ndarray, jnd_obs: dict,
                              hc_baseline: dict, hc_sd: dict,
                              w_alpha: float, w_gamma: float) -> float:
    def L_behav(delta_rc):
        l_a = L_behav_alpha(delta_rc, obs_acc, SIGMA_HC) if w_alpha > 0 else 0.0
        l_g = L_behav_gamma(delta_rc, jnd_obs, hc_baseline, hc_sd)
        return w_alpha * l_a + w_gamma * l_g
    return fit_rc_g(delta_lambda, family, L_behav)['g_best']


def bootstrap_cvd_g_trial(subject: str, hc_baseline: dict, hc_sd: dict,
                            B: int = B_DEFAULT, seed: int = 42) -> dict:
    info = CVD_INFO[subject]
    fam = info['family']
    dl = info['delta_lambda']

    jnd_trials = load_jnd_trials(subject)
    afc_trials = load_8afc_trials(subject)

    if subject == 'sub-09':
        w_alpha, w_gamma = 0.0, 1.0
    else:
        w_alpha, w_gamma = 0.5, 0.5

    # Also baseline (no resample) g for reference
    obs_acc_orig = accuracy_per_color_from_trials(afc_trials) if afc_trials is not None else np.zeros(8)
    jnd_orig = jnd_per_pair_from_trials(jnd_trials)
    g_orig = fit_g_on_trial_resample(fam, dl, obs_acc_orig, jnd_orig,
                                       hc_baseline, hc_sd, w_alpha, w_gamma)

    rng = np.random.default_rng(seed)
    g_samples = []
    for b in range(B):
        jnd_re = resample_jnd_trials_per_pair(jnd_trials, rng)
        if afc_trials is not None and w_alpha > 0:
            obs_re = resample_8afc_trials_per_color(afc_trials, rng)
        else:
            obs_re = obs_acc_orig
        g = fit_g_on_trial_resample(fam, dl, obs_re, jnd_re, hc_baseline, hc_sd,
                                      w_alpha, w_gamma)
        g_samples.append(g)
    g_arr = np.array(g_samples)
    ci_low, ci_high = np.percentile(g_arr, [2.5, 97.5])

    return {
        'subject': subject,
        'cvd_family': fam,
        'delta_lambda_nm': dl,
        'sampling_unit': 'trial',
        'B': B,
        'g_point_no_resample': float(g_orig),
        'g_mean': float(np.mean(g_arr)),
        'g_median': float(np.median(g_arr)),
        'g_sd': float(np.std(g_arr, ddof=1)),
        'g_ci_95': [float(ci_low), float(ci_high)],
        'fraction_above_1': float(np.mean(g_arr > 1.0)),
        'fraction_above_2': float(np.mean(g_arr > 2.0)),
        'compensation_evidence': bool(ci_low > 1.0),
        'overcompensation_evidence': bool(ci_low > 2.0),
        'g_samples_first20': g_arr.tolist()[:20],
    }


def bootstrap_hc_g_trial(hc_baseline: dict, hc_sd: dict, family: str,
                           delta_lambda: float, B: int = B_DEFAULT,
                           seed: int = 42) -> dict:
    rng = np.random.default_rng(seed)
    all_g = []
    per_hc = {}
    for hc in HC_JND_SUBJS:
        jnd_trials = load_jnd_trials(hc)
        afc_trials = load_8afc_trials(hc) if hc in HC_8AFC_SUBJS else None
        if afc_trials is not None:
            w_alpha, w_gamma = 0.5, 0.5
            obs_orig = accuracy_per_color_from_trials(afc_trials)
        else:
            w_alpha, w_gamma = 0.0, 1.0
            obs_orig = np.zeros(8)

        g_samples = []
        for b in range(B):
            jnd_re = resample_jnd_trials_per_pair(jnd_trials, rng)
            if afc_trials is not None and w_alpha > 0:
                obs_re = resample_8afc_trials_per_color(afc_trials, rng)
            else:
                obs_re = obs_orig
            g = fit_g_on_trial_resample(family, delta_lambda, obs_re, jnd_re,
                                         hc_baseline, hc_sd, w_alpha, w_gamma)
            g_samples.append(g)
        per_hc[hc] = {
            'g_mean': float(np.mean(g_samples)),
            'g_ci_95': [float(np.percentile(g_samples, 2.5)),
                        float(np.percentile(g_samples, 97.5))],
        }
        all_g.extend(g_samples)
    all_g = np.array(all_g)
    return {
        'family': family,
        'delta_lambda_nm': delta_lambda,
        'sampling_unit': 'trial',
        'pool_mean': float(np.mean(all_g)),
        'pool_median': float(np.median(all_g)),
        'pool_sd': float(np.std(all_g, ddof=1)),
        'pool_ci_95': [float(np.percentile(all_g, 2.5)),
                       float(np.percentile(all_g, 97.5))],
        'per_hc': per_hc,
    }


def main(B: int = B_DEFAULT):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 78)
    print(f"S6 (trial-level + Δλ sensitivity): Bootstrap CI of g — B={B}")
    print(f"  Sampling unit: individual trial (JND staircase + 8AFC responses)")
    print(f"  Color set: fixed 8 colors / 8 pairs (never resampled)")
    print(f"  Δλ sources: DPS lit, Boehm grid, JND-Lamb per family")
    print("=" * 78)

    hc_baseline, hc_sd = compute_hc_jnd_baseline()

    cvd_results = {}
    for subj in ['sub-08', 'sub-09']:
        info = CVD_INFO[subj]
        fam = info['family']
        dl_sources = DELTA_LAMBDA_BY_FAMILY[fam]
        cvd_results[subj] = {'family': fam, 'by_source': {}}
        print(f"\n=== {subj} ({fam}) trial-level bootstrap × Δλ sources ===")
        for src_name, dl in dl_sources.items():
            # Override CVD_INFO temporarily for fit
            CVD_INFO[subj]['delta_lambda'] = dl
            r = bootstrap_cvd_g_trial(subj, hc_baseline, hc_sd, B=B)
            cvd_results[subj]['by_source'][src_name] = {**r, 'delta_lambda_source': src_name}
            print(f"  {src_name} (Δλ={dl}): g_pt={r['g_point_no_resample']:.2f}  "
                  f"mean={r['g_mean']:.2f}±{r['g_sd']:.2f}  CI=[{r['g_ci_95'][0]:.2f}, {r['g_ci_95'][1]:.2f}]  "
                  f"P(g>1)={r['fraction_above_1']:.2f}")
        # Restore default Δλ
        CVD_INFO[subj]['delta_lambda'] = dl_sources['DPS_lit']

    print(f"\n=== HC pool trial-level bootstrap × Δλ sources ===")
    hc_pool_results = {}
    for fam, dl_sources in DELTA_LAMBDA_BY_FAMILY.items():
        hc_pool_results[fam] = {'by_source': {}}
        for src_name, dl in dl_sources.items():
            r = bootstrap_hc_g_trial(hc_baseline, hc_sd, fam, dl, B=B)
            hc_pool_results[fam]['by_source'][src_name] = {**r, 'delta_lambda_source': src_name}
            print(f"  {fam} {src_name} (Δλ={dl}): pool_mean={r['pool_mean']:.2f}±{r['pool_sd']:.2f}  "
                  f"CI=[{r['pool_ci_95'][0]:.2f}, {r['pool_ci_95'][1]:.2f}]")

    print(f"\n{'=' * 78}\nCVD vs HC pool comparison (trial-level × Δλ sources)\n{'=' * 78}")
    for subj, r_cvd_all in cvd_results.items():
        fam = r_cvd_all['family']
        print(f"\n{subj} ({fam}):")
        for src_name, r_cvd in r_cvd_all['by_source'].items():
            r_hc = hc_pool_results[fam]['by_source'][src_name]
            cvd_lo, cvd_hi = r_cvd['g_ci_95']
            hc_lo, hc_hi = r_hc['pool_ci_95']
            ci_sep = (cvd_lo > hc_hi) or (cvd_hi < hc_lo)
            print(f"  {src_name}: CVD CI=[{cvd_lo:.2f}, {cvd_hi:.2f}] "
                  f"HC CI=[{hc_lo:.2f}, {hc_hi:.2f}]  separated={ci_sep}  "
                  f"Δ(mean)={r_cvd['g_mean']-r_hc['pool_mean']:+.2f}")

    out = {
        'cvd_bootstrap_trial': cvd_results,
        'hc_pool_bootstrap_trial': hc_pool_results,
        'B': B,
        'sampling_unit': 'trial',
        'delta_lambda_sources': DELTA_LAMBDA_BY_FAMILY,
        'notes': ('JND: mean(level) over per-pair resampled trial rows. '
                  '8AFC: mean(correct) over per-color resampled trial rows. '
                  '8 colors / 8 pairs always preserved. '
                  'Δλ sensitivity: 3 sources × 2 families.'),
    }
    with open(OUT_DIR / "g_bootstrap_trial.json", 'w') as f:
        json.dump(out, f, indent=2, default=str)
    print(f"\nSaved: {OUT_DIR / 'g_bootstrap_trial.json'}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--B', type=int, default=B_DEFAULT)
    args = parser.parse_args()
    main(B=args.B)
