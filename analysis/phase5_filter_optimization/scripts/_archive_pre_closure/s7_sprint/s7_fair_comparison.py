"""S7 fair model comparison — each model at its OWN best composite λ.

Strategy: For fair AIC/BIC, evaluate the SAME loss (L_γ behavioral deviance) at each
model's optimal parameter. This uses L_γ as a common deviance regardless of which
composite was used to FIT the parameter.

Per cell × model:
  1. Look up optimal λ from lambda_optimal_behav_rdm.json
  2. For each k=5 subset, get fitted param at that λ
  3. Recompute L_γ at that param using subset HC as baseline (train) and complement HC (test)
  4. Aggregate: median L_γ_train, median L_γ_test across 21 subsets

Model comparison:
  ΔAIC = 2·(k_2C − k_RC) + (L_γ_2C − L_γ_RC) median
        = 2·1 + Δloss_median
  ΔBIC = log(n_pairs) + Δloss_median, n_pairs=8
  ΔTest = test_L_γ_2C − test_L_γ_RC

Verdict: Δ > +2 → R+C wins; Δ < −2 → 2-comp wins; |Δ| < 2 → tie.

Caveat for sub-08: 2-comp degenerate at all λ → 2-comp formally invalid; comparison flagged.
"""

import itertools
import json
import sys
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from rc_1dof import forward_rc
from two_comp import forward_2comp
from behav_loss import (
    load_jnd_per_pair, L_behav_gamma, PAIR_HUES, HC_JND_SUBJS,
)
from s8_loo_train_test import jnd_baseline_from_pool

RESULTS_DIR = SCRIPT_DIR.parent / "results" / "s7_loss_combo_subset"
OPT_JSON = RESULTS_DIR / "lambda_optimal_behav_rdm.json"

HC_SUBJS = ['sub-01', 'sub-02', 'sub-03', 'sub-04', 'sub-05', 'sub-06', 'sub-07']
COMBO_K = 5
N_PAIRS = 8
K_RC = 1
K_2C = 2
DELTA_LAMBDA = {'deutan': 6.0, 'protan': 10.0}  # DPS_lit


def compute_L_gamma(delta_rc, cvd_jnd, pool_jnd_baseline, pool_jnd_sd):
    """L_γ deviance at a given delta_rc 8-vec, using a specific HC pool baseline."""
    if cvd_jnd is None:
        return None
    valid_pairs = {p: cvd_jnd[p] for p in PAIR_HUES.keys()
                   if cvd_jnd.get(p) is not None and pool_jnd_baseline.get(p) is not None}
    if not valid_pairs:
        return None
    bl = {p: pool_jnd_baseline[p] for p in valid_pairs}
    sd_d = {p: pool_jnd_sd[p] if pool_jnd_sd[p] else 1.0 for p in valid_pairs}
    return float(L_behav_gamma(delta_rc, valid_pairs, bl, sd_d))


def get_optimal_lambda_per_model(subject, roi, opt_data):
    key = f"{subject}_{roi}"
    out = {}
    for model in ['rc_DPS', '2comp']:
        r = opt_data.get(key, {}).get(model, {})
        opt_list = r.get('optimal_ranked', [])
        if opt_list:
            out[model] = opt_list[0]['lambda']  # string key '0.00' etc
        else:
            out[model] = None
    return out


def evaluate_at_optimal(cell_data, optimal_lams, cvd_jnd, family):
    """For each subset, compute L_γ at each model's fitted param (train + test)."""
    dl = DELTA_LAMBDA[family]
    L_gamma_train = {'rc': [], '2c': []}
    L_gamma_test = {'rc': [], '2c': []}
    params_train = {'rc': [], '2c': []}

    for s in cell_data['subsets']:
        if s['k'] != COMBO_K:
            continue
        subset = s['subset']
        complement = s['complement']
        if len(complement) < 1:
            continue

        # Build train + test JND baselines
        train_jnd_subjs = [h for h in subset if h in HC_JND_SUBJS]
        test_jnd_subjs = [h for h in complement if h in HC_JND_SUBJS]
        if not train_jnd_subjs or not test_jnd_subjs:
            continue
        train_bl, train_sd = jnd_baseline_from_pool(train_jnd_subjs)
        test_bl, test_sd = jnd_baseline_from_pool(test_jnd_subjs)

        # R+C at optimal λ
        if optimal_lams['rc_DPS'] is not None:
            lf = s['lambda_fits'].get('gamma_plus_RDM', {}).get(optimal_lams['rc_DPS'], {})
            if lf and lf.get('rc', {}).get('DPS_lit'):
                g = lf['rc']['DPS_lit']['g_best']
                delta = forward_rc(dl, g, family)
                L_tr = compute_L_gamma(delta, cvd_jnd, train_bl, train_sd)
                L_te = compute_L_gamma(delta, cvd_jnd, test_bl, test_sd)
                L_gamma_train['rc'].append(L_tr)
                L_gamma_test['rc'].append(L_te)
                params_train['rc'].append(g)

        # 2-comp at optimal λ
        if optimal_lams['2comp'] is not None:
            lf = s['lambda_fits'].get('gamma_plus_RDM', {}).get(optimal_lams['2comp'], {})
            if lf and lf.get('2comp'):
                bs = lf['2comp']['beta_s_best']
                bc = lf['2comp']['beta_c_best']
                delta = forward_2comp(bs, bc, family)
                L_tr = compute_L_gamma(delta, cvd_jnd, train_bl, train_sd)
                L_te = compute_L_gamma(delta, cvd_jnd, test_bl, test_sd)
                L_gamma_train['2c'].append(L_tr)
                L_gamma_test['2c'].append(L_te)
                params_train['2c'].append((bs, bc))

    return L_gamma_train, L_gamma_test, params_train


def median_safe(arr):
    valid = [v for v in arr if v is not None and np.isfinite(v)]
    return float(np.median(valid)) if valid else None


def main():
    cell_files = sorted(RESULTS_DIR.glob("cell_*.json"))
    opt_data = json.loads(OPT_JSON.read_text())

    rows = []
    for fp in cell_files:
        with open(fp) as f:
            cell = json.load(f)
        subject = cell['subject']
        roi = cell['roi']
        family = cell['family']
        key = f"{subject}_{roi}"

        try:
            cvd_jnd = load_jnd_per_pair(subject)
        except Exception:
            continue

        optimal_lams = get_optimal_lambda_per_model(subject, roi, opt_data)
        L_tr, L_te, params_tr = evaluate_at_optimal(cell, optimal_lams, cvd_jnd, family)

        med_L_rc = median_safe(L_tr['rc'])
        med_L_2c = median_safe(L_tr['2c'])
        med_te_rc = median_safe(L_te['rc'])
        med_te_2c = median_safe(L_te['2c'])

        # AIC/BIC on L_γ deviance
        if med_L_rc is not None and med_L_2c is not None:
            d_aic = 2 * (K_2C - K_RC) + (med_L_2c - med_L_rc)
            d_bic = np.log(N_PAIRS) * (K_2C - K_RC) + (med_L_2c - med_L_rc)
        else:
            d_aic = None
            d_bic = None
        d_test = (med_te_2c - med_te_rc) if (med_te_2c is not None and med_te_rc is not None) else None

        # Verdict
        if d_aic is not None:
            v_aic = "R+C" if d_aic > 2 else ("2C" if d_aic < -2 else "tie")
            v_bic = "R+C" if d_bic > 2 else ("2C" if d_bic < -2 else "tie")
        else:
            v_aic = v_bic = "NA"
        if d_test is not None:
            v_test = "R+C" if d_test > 0 else "2C"
        else:
            v_test = "NA"

        flag = ""
        if optimal_lams['2comp'] is None:
            flag = "2C-degenerate"
        elif optimal_lams['rc_DPS'] is None:
            flag = "RC-degenerate"

        rows.append({
            'cell': key,
            'family': family,
            'rc_lambda': optimal_lams['rc_DPS'],
            'tc_lambda': optimal_lams['2comp'],
            'L_gamma_train_RC': med_L_rc,
            'L_gamma_train_2C': med_L_2c,
            'L_gamma_test_RC': med_te_rc,
            'L_gamma_test_2C': med_te_2c,
            'delta_AIC': d_aic,
            'delta_BIC': d_bic,
            'delta_Test': d_test,
            'verdict_AIC': v_aic,
            'verdict_BIC': v_bic,
            'verdict_Test': v_test,
            'flag': flag,
        })

    # Print table
    print("=" * 138)
    print("S7 Fair Model Comparison — L_γ at each model's BEST COMPOSITE λ")
    print("  k_RC=1, k_2C=2, n=8 JND pairs")
    print("  Verdict (Δ>+2: R+C wins; Δ<−2: 2C wins; tie otherwise)")
    print("=" * 138)
    print(f"{'Cell':14s} | {'λ_RC':>5s} | {'λ_2C':>5s} | {'L_γ_RC':>7s} | {'L_γ_2C':>7s} | "
          f"{'TestRC':>7s} | {'Test2C':>7s} | {'ΔAIC':>7s} | {'ΔBIC':>7s} | {'ΔTest':>7s} | Verdict (A/B/T)        | Flag")
    print("-" * 138)
    for r in rows:
        def f(v, w=7, p=3):
            return f"{v:{w}.{p}f}" if v is not None and np.isfinite(v) else f"{'NA':>{w}s}"
        print(f"{r['cell']:14s} | {r['rc_lambda'] or 'NA':>5s} | {r['tc_lambda'] or 'NA':>5s} | "
              f"{f(r['L_gamma_train_RC'])} | {f(r['L_gamma_train_2C'])} | "
              f"{f(r['L_gamma_test_RC'])} | {f(r['L_gamma_test_2C'])} | "
              f"{f(r['delta_AIC'])} | {f(r['delta_BIC'])} | {f(r['delta_Test'])} | "
              f"{r['verdict_AIC']:>4s}/{r['verdict_BIC']:>4s}/{r['verdict_Test']:>4s}     | {r['flag']}")

    out = {'rows': rows, 'meta': {'k_RC': K_RC, 'k_2C': K_2C, 'n_pairs': N_PAIRS}}
    out_json = RESULTS_DIR / "fair_model_comparison.json"
    with open(out_json, 'w') as f:
        json.dump(out, f, indent=2, default=str)
    print(f"\nSaved: {out_json}")


if __name__ == "__main__":
    main()
