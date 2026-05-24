"""S7 λ optimal analysis — Behavioral + RDM only (사용자 directive 2026-05-24).

For each cell:
  Per λ ∈ {0, 0.25, 0.5, 0.75, 1.0} of probe gamma_plus_RDM:
    (a) CoV across 21 subsets — CI stability
    (b) train-test ratio — generalization (raw, with caveat)
    (c) boundary-hit rate — degeneracy flag

Output: optimal λ per cell + final model-loss selection recommendation.
"""

import json
import sys
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
RESULTS_DIR = SCRIPT_DIR.parent / "results" / "s7_loss_combo_subset"

COMBO_K = 5
LAMBDA_KEYS = ['0.00', '0.25', '0.50', '0.75', '1.00']

# Only Behavioral + RDM combination (사용자 directive: drop LOCO)
PROBE = 'gamma_plus_RDM'


def extract_g_best(fit, model):
    if fit is None:
        return None
    if model == 'rc_DPS':
        rc = fit.get('rc', {}).get('DPS_lit')
        if rc is None:
            return None
        return rc.get('g_best'), rc.get('loss_best'), rc.get('boundary_low'), rc.get('boundary_high')
    elif model == 'rc_Boehm':
        rc = fit.get('rc', {}).get('Boehm_low') or fit.get('rc', {}).get('Boehm_mid')
        if rc is None:
            return None
        return rc.get('g_best'), rc.get('loss_best'), rc.get('boundary_low'), rc.get('boundary_high')
    elif model == 'rc_JND_Lamb':
        rc = fit.get('rc', {}).get('JND_Lamb')
        if rc is None:
            return None
        return rc.get('g_best'), rc.get('loss_best'), rc.get('boundary_low'), rc.get('boundary_high')
    elif model == '2comp':
        twc = fit.get('2comp')
        if twc is None:
            return None
        return twc.get('norm'), twc.get('loss_best'), (twc.get('boundary_bs') or twc.get('boundary_bc')), False
    return None


def extract_test_value(test_data, model):
    if test_data is None:
        return None
    if model.startswith('rc_'):
        src = {'rc_DPS': 'DPS_lit', 'rc_Boehm': 'Boehm_low', 'rc_JND_Lamb': 'JND_Lamb'}[model]
        return test_data.get('rc', {}).get(src)
    elif model == '2comp':
        return test_data.get('2comp')
    return None


def cov_helper(values):
    arr = np.array([v for v in values if v is not None and np.isfinite(v)])
    if len(arr) < 2:
        return None
    med = float(np.median(arr))
    sd = float(np.std(arr, ddof=1))
    if abs(med) < 1e-10:
        return None
    return sd / abs(med)


def analyze_cell_lambda_sweep(cell_data, model='rc_DPS'):
    """For one cell, compute per-λ stats (only k=5 subsets)."""
    subsets = [s for s in cell_data['subsets'] if s['k'] == COMBO_K]
    if not subsets:
        return None

    per_lambda = {}
    for lam in LAMBDA_KEYS:
        params = []
        train_losses = []
        test_losses = []
        boundaries = []

        for s in subsets:
            lf = s.get('lambda_fits', {}).get(PROBE, {})
            fit = lf.get(lam)
            ex = extract_g_best(fit, model)
            if ex is None or ex[0] is None:
                params.append(None)
                train_losses.append(None)
                boundaries.append(None)
            else:
                g, l, bl, bh = ex
                params.append(g)
                train_losses.append(l)
                boundaries.append(bool(bl or bh))

            # Test loss
            tr_lam = s.get('test_results', {}).get('lambda', {}).get(PROBE, {}).get(lam)
            tl = extract_test_value(tr_lam, model)
            test_losses.append(tl)

        valid_p = [p for p in params if p is not None and np.isfinite(p)]
        valid_t_train = [t for t in train_losses if t is not None and np.isfinite(t)]
        valid_t_test = [t for t in test_losses if t is not None and np.isfinite(t)]
        valid_bdy = [b for b in boundaries if b is not None]

        per_lambda[lam] = {
            'param_median': float(np.median(valid_p)) if valid_p else None,
            'param_sd': float(np.std(valid_p, ddof=1)) if len(valid_p) > 1 else 0.0,
            'param_cov': cov_helper(params),
            'param_ci95': [float(np.percentile(valid_p, 2.5)), float(np.percentile(valid_p, 97.5))] if len(valid_p) >= 2 else None,
            'train_loss_median': float(np.median(valid_t_train)) if valid_t_train else None,
            'test_loss_median': float(np.median(valid_t_test)) if valid_t_test else None,
            'test_minus_train': (float(np.median(valid_t_test)) - float(np.median(valid_t_train)))
                                  if valid_t_train and valid_t_test else None,
            'boundary_rate': float(np.mean(valid_bdy)) if valid_bdy else None,
            'n_valid': len(valid_p),
        }
    return per_lambda


def find_optimal_lambda(lambda_stats):
    """Optimal λ = lowest CoV AND non-boundary AND reasonable test-train ratio."""
    candidates = []
    for lam, st in lambda_stats.items():
        if st['param_cov'] is None:
            continue
        if st['boundary_rate'] is not None and st['boundary_rate'] > 0.5:
            continue  # >50% boundary = degenerate
        candidates.append({
            'lambda': lam,
            'cov': st['param_cov'],
            'test_minus_train': st['test_minus_train'],
            'param_median': st['param_median'],
            'boundary_rate': st['boundary_rate'],
        })
    if not candidates:
        return None
    # Sort by CoV ascending (most stable first)
    candidates.sort(key=lambda c: (c['cov'] if c['cov'] is not None else 1e9))
    return candidates


def main():
    cell_files = sorted(RESULTS_DIR.glob("cell_*.json"))
    print(f"Analyzing {len(cell_files)} cells (Behavioral + RDM only, probe={PROBE})\n")

    results = {}
    for fp in cell_files:
        with open(fp) as f:
            cell = json.load(f)
        key = f"{cell['subject']}_{cell['roi']}"
        results[key] = {}
        for model in ['rc_DPS', '2comp']:
            lstats = analyze_cell_lambda_sweep(cell, model=model)
            if lstats is None:
                continue
            optimal = find_optimal_lambda(lstats)
            results[key][model] = {
                'per_lambda': lstats,
                'optimal_ranked': optimal,
            }

    # Print summary
    print("=" * 88)
    print(f"Per-cell λ sweep: probe={PROBE} (Behavioral + RDM)")
    print("=" * 88)
    for key, m_res in results.items():
        print(f"\n[{key}]")
        for model, r in m_res.items():
            print(f"  {model}:")
            print(f"    λ    | param_med | CoV    | bdy_rate | test−train | n")
            for lam, st in r['per_lambda'].items():
                pm = st['param_median']
                cov = st['param_cov']
                br = st['boundary_rate']
                tt = st['test_minus_train']
                n = st['n_valid']
                pm_s = f"{pm:8.3f}" if pm is not None else "    NA  "
                cov_s = f"{cov:.4f}" if cov is not None else "  NA   "
                br_s = f"{br:.2f}" if br is not None else "  NA  "
                tt_s = f"{tt:+8.3f}" if tt is not None else "    NA  "
                print(f"    {lam} | {pm_s} | {cov_s} | {br_s}     | {tt_s}  | {n}")
            opt = r['optimal_ranked']
            if opt:
                top = opt[0]
                print(f"    → OPTIMAL λ (by CoV, non-boundary): λ={top['lambda']} "
                      f"(g={top['param_median']:.3f}, CoV={top['cov']:.4f}, "
                      f"bdy={top['boundary_rate']:.2f}, test−train={top['test_minus_train']:+.3f})")
            else:
                print(f"    → All λ degenerate (boundary)")

    out_json = RESULTS_DIR / "lambda_optimal_behav_rdm.json"
    with open(out_json, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nSaved: {out_json}")


if __name__ == "__main__":
    main()
