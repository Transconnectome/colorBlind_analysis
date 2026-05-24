"""S7 analysis: aggregate per-cell JSONs, compute selection metrics, write report.

Inputs: results/s7_loss_combo_subset/cell_*_*.json
Outputs:
  results/s7_loss_combo_subset/aggregated.json
  results/s7_loss_combo_subset/SELECTION_REPORT.md

Stages computed:
  A — single-loss subset stability (RQ1)
  B — loss combination vs single (RQ2, paired Wilcoxon)
  C — λ sweep neural unique contribution (RQ3, paired Wilcoxon)
  D — train-test MSE (RQ4)
"""

import json
import sys
from pathlib import Path

import numpy as np

try:
    from scipy.stats import wilcoxon
    HAVE_SCIPY = True
except ImportError:
    HAVE_SCIPY = False

SCRIPT_DIR = Path(__file__).resolve().parent
RESULTS_DIR = SCRIPT_DIR.parent / "results" / "s7_loss_combo_subset"

COMBO_K = 5  # only subsets where Stage B/C/D are valid

SINGLE_LOSSES = ['L_gamma', 'L_alpha', 'L_LOCO', 'L_RDM']
PAIR_COMBOS = [
    'L_gamma+L_alpha', 'L_gamma+L_LOCO', 'L_gamma+L_RDM',
    'L_alpha+L_LOCO', 'L_alpha+L_RDM', 'L_LOCO+L_RDM',
]
TRIPLE_COMBO = 'L_gamma+L_LOCO+L_RDM'
LAMBDA_PROBES = ['gamma_plus_LOCO', 'gamma_plus_RDM', 'gamma_plus_LOCO_and_RDM']
LAMBDA_VALUES = ['0.00', '0.25', '0.50', '0.75', '1.00']


def percentile_ci(values, level=95):
    """Two-sided percentile CI."""
    arr = np.array([v for v in values if v is not None and np.isfinite(v)])
    if len(arr) < 2:
        return None
    lo = float(np.percentile(arr, (100 - level) / 2))
    hi = float(np.percentile(arr, 100 - (100 - level) / 2))
    return [lo, hi]


def safe_stats(values):
    arr = np.array([v for v in values if v is not None and np.isfinite(v)])
    if len(arr) == 0:
        return {'n': 0, 'median': None, 'mean': None, 'sd': None, 'cov': None, 'ci95': None}
    median = float(np.median(arr))
    mean = float(np.mean(arr))
    sd = float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0
    cov = float(sd / abs(median)) if abs(median) > 1e-10 else None
    return {
        'n': int(len(arr)),
        'median': median,
        'mean': mean,
        'sd': sd,
        'cov': cov,
        'ci95': percentile_ci(arr, 95),
    }


def extract_param_value(fit, model, key):
    """Pull the 'best' parameter from a fit dict structure."""
    if fit is None:
        return None
    if model == 'rc_DPS':
        rc = fit.get('rc', {}).get('DPS_lit')
        if rc is None:
            return None
        return rc.get(key)
    if model == 'rc_Boehm':
        rc = fit.get('rc', {}).get('Boehm_low') or fit.get('rc', {}).get('Boehm_mid')
        if rc is None:
            return None
        return rc.get(key)
    if model == 'rc_JND_Lamb':
        rc = fit.get('rc', {}).get('JND_Lamb')
        if rc is None:
            return None
        return rc.get(key)
    if model == '2comp':
        twc = fit.get('2comp')
        if twc is None:
            return None
        return twc.get(key)
    return None


def extract_test_value(test, model):
    """Pull test loss from test_results substructure (always a scalar or None)."""
    if test is None:
        return None
    if model == 'rc_DPS':
        return test.get('rc', {}).get('DPS_lit')
    if model == 'rc_Boehm':
        return test.get('rc', {}).get('Boehm_low') or test.get('rc', {}).get('Boehm_mid')
    if model == 'rc_JND_Lamb':
        return test.get('rc', {}).get('JND_Lamb')
    if model == '2comp':
        return test.get('2comp')
    return None


def collect_per_subset(subsets_data, k_filter, loss_path, model, value_key='g_best'):
    """Walk subsets, return list of values per subset for one (loss, model, key)."""
    out = []
    for sub in subsets_data:
        if k_filter is not None and sub['k'] != k_filter:
            continue
        fit = sub
        for p in loss_path:
            fit = fit.get(p, {}) if fit is not None else None
        if fit is None:
            out.append(None)
            continue
        val = extract_param_value(fit, model, value_key) if value_key else fit
        out.append(val)
    return out


def compute_stage_a(subsets_data, k):
    """Single-loss subset stability per (loss, model)."""
    models = ['rc_DPS', '2comp']  # primary models (Boehm/JND_Lamb in supplement)
    out = {}
    for loss in SINGLE_LOSSES:
        for model in models:
            # Collect param best (g_best for rc, norm for 2comp)
            value_key = 'g_best' if model.startswith('rc') else 'norm'
            vals = []
            for sub in subsets_data:
                if sub['k'] != k:
                    continue
                fit = sub['single_fits'].get(loss)
                if fit is None:
                    vals.append(None)
                    continue
                vals.append(extract_param_value(fit, model, value_key))
            stats = safe_stats(vals)
            # SEP rate: param > 1.0 (R+C) or norm > 10 (2-comp, ad hoc cortical threshold)
            sep_threshold = 1.0 if model.startswith('rc') else 10.0
            valid = [v for v in vals if v is not None and np.isfinite(v)]
            sep_rate = float(np.mean(np.array(valid) > sep_threshold)) if valid else None
            # Boundary hit rate
            boundary_low = []
            boundary_high = []
            for sub in subsets_data:
                if sub['k'] != k:
                    continue
                fit = sub['single_fits'].get(loss)
                if fit is None:
                    continue
                if model.startswith('rc'):
                    rc = fit.get('rc', {}).get(model.replace('rc_', '').replace('DPS', 'DPS_lit').replace('Boehm', 'Boehm_low').replace('JND_Lamb', 'JND_Lamb'))
                    if rc is not None:
                        boundary_low.append(rc.get('boundary_low', False))
                        boundary_high.append(rc.get('boundary_high', False))
                else:
                    twc = fit.get('2comp')
                    if twc is not None:
                        boundary_low.append(twc.get('boundary_bs', False) or twc.get('boundary_bc', False))
                        boundary_high.append(False)
            out[f"{loss}|{model}"] = {
                **stats,
                'sep_rate': sep_rate,
                'sep_threshold': sep_threshold,
                'boundary_low_rate': float(np.mean(boundary_low)) if boundary_low else None,
                'boundary_high_rate': float(np.mean(boundary_high)) if boundary_high else None,
            }
    return out


def compute_stage_b(subsets_data):
    """Loss combinations vs L_γ single (paired by subset, k=COMBO_K)."""
    models = ['rc_DPS', '2comp']
    out = {}
    all_combos = PAIR_COMBOS + [TRIPLE_COMBO]
    for combo in all_combos:
        for model in models:
            value_key = 'g_best' if model.startswith('rc') else 'norm'
            combo_vals = []
            single_vals = []  # use L_gamma as baseline
            for sub in subsets_data:
                if sub['k'] != COMBO_K:
                    continue
                cfit = sub['combo_fits'].get(combo)
                sfit = sub['single_fits'].get('L_gamma')
                combo_vals.append(extract_param_value(cfit, model, value_key) if cfit else None)
                single_vals.append(extract_param_value(sfit, model, value_key) if sfit else None)
            # Paired Wilcoxon
            paired = [(c, s) for c, s in zip(combo_vals, single_vals)
                       if c is not None and s is not None and np.isfinite(c) and np.isfinite(s)]
            if len(paired) >= 5 and HAVE_SCIPY:
                cv = np.array([p[0] for p in paired])
                sv = np.array([p[1] for p in paired])
                diff = cv - sv
                if np.allclose(diff, 0):
                    p_val, stat = 1.0, 0.0
                else:
                    try:
                        res = wilcoxon(cv, sv)
                        stat, p_val = float(res.statistic), float(res.pvalue)
                    except Exception:
                        stat, p_val = None, None
                delta_median = float(np.median(diff))
            else:
                stat, p_val = None, None
                delta_median = None
            combo_stats = safe_stats(combo_vals)
            single_stats = safe_stats(single_vals)
            out[f"{combo}|{model}"] = {
                'combo_stats': combo_stats,
                'L_gamma_baseline_stats': single_stats,
                'delta_param_median': delta_median,
                'wilcoxon_stat': stat,
                'wilcoxon_p': p_val,
                'delta_cov': (combo_stats['cov'] - single_stats['cov'])
                              if combo_stats['cov'] is not None and single_stats['cov'] is not None
                              else None,
                'n_paired': len(paired),
            }
    return out


def compute_stage_c(subsets_data):
    """λ sweep — λ=0 vs λ=0.5 and λ=0 vs λ=1.0 paired Wilcoxon."""
    models = ['rc_DPS', '2comp']
    out = {}
    for probe in LAMBDA_PROBES:
        for model in models:
            value_key = 'g_best' if model.startswith('rc') else 'norm'
            lambda_vals = {l: [] for l in LAMBDA_VALUES}
            for sub in subsets_data:
                if sub['k'] != COMBO_K:
                    continue
                pf = sub['lambda_fits'].get(probe, {})
                for lam in LAMBDA_VALUES:
                    fit = pf.get(lam)
                    lambda_vals[lam].append(
                        extract_param_value(fit, model, value_key) if fit else None
                    )
            # Pair λ=0 vs λ=0.5 and λ=0 vs λ=1.0
            cmp_pairs = [('0.00', '0.50'), ('0.00', '1.00')]
            probe_out = {'per_lambda_stats': {lam: safe_stats(lambda_vals[lam]) for lam in LAMBDA_VALUES}}
            for la, lb in cmp_pairs:
                pairs = [(a, b) for a, b in zip(lambda_vals[la], lambda_vals[lb])
                          if a is not None and b is not None and np.isfinite(a) and np.isfinite(b)]
                if len(pairs) >= 5 and HAVE_SCIPY:
                    av = np.array([p[0] for p in pairs])
                    bv = np.array([p[1] for p in pairs])
                    diff = bv - av
                    if np.allclose(diff, 0):
                        stat, p_val = 0.0, 1.0
                    else:
                        try:
                            res = wilcoxon(av, bv)
                            stat, p_val = float(res.statistic), float(res.pvalue)
                        except Exception:
                            stat, p_val = None, None
                    delta_median = float(np.median(diff))
                else:
                    stat, p_val = None, None
                    delta_median = None
                probe_out[f"lambda_{la}_vs_{lb}"] = {
                    'delta_median': delta_median,
                    'wilcoxon_stat': stat,
                    'wilcoxon_p': p_val,
                    'n_paired': len(pairs),
                }
            out[f"{probe}|{model}"] = probe_out
    return out


def compute_stage_d(subsets_data):
    """Train-test MSE (RQ4). MSE_test_median + overfit ratio."""
    models = ['rc_DPS', '2comp']
    out = {}
    all_configs = (
        [('single', l) for l in SINGLE_LOSSES] +
        [('combo', c) for c in PAIR_COMBOS + [TRIPLE_COMBO]]
    )
    for cfg_type, cfg_name in all_configs:
        for model in models:
            train_losses = []
            test_losses = []
            for sub in subsets_data:
                if sub['k'] != COMBO_K:
                    continue
                if cfg_type == 'single':
                    train_fit = sub['single_fits'].get(cfg_name)
                else:
                    train_fit = sub['combo_fits'].get(cfg_name)
                train_loss = extract_param_value(train_fit, model, 'loss_best')

                test_loss = None
                if cfg_type == 'single':
                    test_data = sub['test_results']['single'].get(cfg_name)
                else:
                    test_data = sub['test_results']['combo'].get(cfg_name)
                if test_data is not None:
                    test_loss = extract_test_value(test_data, model)

                train_losses.append(train_loss)
                test_losses.append(test_loss)

            train_stats = safe_stats(train_losses)
            test_stats = safe_stats(test_losses)
            # Overfit ratio
            overfit_ratio = None
            if (test_stats['median'] is not None and train_stats['median'] is not None
                    and train_stats['sd'] is not None and train_stats['sd'] > 1e-10):
                overfit_ratio = (test_stats['median'] - train_stats['median']) / train_stats['sd']
            out[f"{cfg_type}|{cfg_name}|{model}"] = {
                'train_stats': train_stats,
                'test_stats': test_stats,
                'overfit_ratio': overfit_ratio,
                'n_subsets': COMBO_K,
            }
    return out


def compute_cell_pass(stage_a, stage_b, stage_c, stage_d):
    """Apply pass criteria from S7 design to find consensus candidates."""
    passes = []
    for key, sa in stage_a.items():
        loss, model = key.split('|')
        # RQ1 (single stability): CoV < 0.10, SEP ≥ 0.80, CI width < 0.5 (R+C) or 30 (2-comp)
        cov_ok = sa.get('cov') is not None and sa['cov'] < 0.10
        sep_ok = sa.get('sep_rate') is not None and sa['sep_rate'] >= 0.80
        ci = sa.get('ci95')
        ci_threshold = 0.5 if model.startswith('rc') else 30.0
        ci_ok = ci is not None and (ci[1] - ci[0]) < ci_threshold
        rq1 = cov_ok and sep_ok and ci_ok

        # RQ4: stage_d single
        sd_key = f"single|{loss}|{model}"
        sd = stage_d.get(sd_key, {})
        overfit = sd.get('overfit_ratio')
        rq4 = overfit is not None and abs(overfit) < 1.5

        passes.append({
            'loss': loss,
            'model': model,
            'cfg_type': 'single',
            'RQ1_pass': rq1,
            'RQ4_pass': rq4,
            'all_pass': rq1 and rq4,
            'cov': sa.get('cov'),
            'sep_rate': sa.get('sep_rate'),
            'ci95': ci,
            'overfit_ratio': overfit,
        })

    return passes


def process_cell_file(filepath):
    with open(filepath, 'r') as f:
        data = json.load(f)
    subsets = data['subsets']

    stage_a_k4 = compute_stage_a(subsets, k=4)
    stage_a_k5 = compute_stage_a(subsets, k=5)
    stage_a_k6 = compute_stage_a(subsets, k=6)
    stage_b = compute_stage_b(subsets)
    stage_c = compute_stage_c(subsets)
    stage_d = compute_stage_d(subsets)
    passes = compute_cell_pass(stage_a_k5, stage_b, stage_c, stage_d)

    return {
        'subject': data['subject'],
        'family': data['family'],
        'roi': data['roi'],
        'K': data['K'],
        'stage_a_k4': stage_a_k4,
        'stage_a_k5': stage_a_k5,
        'stage_a_k6': stage_a_k6,
        'stage_b': stage_b,
        'stage_c': stage_c,
        'stage_d': stage_d,
        'cell_pass_summary': passes,
    }


def main():
    cell_files = sorted(RESULTS_DIR.glob("cell_*.json"))
    print(f"Found {len(cell_files)} cell files")
    if not cell_files:
        print("No cell files. Run s7_loss_combo_subset.py first.")
        sys.exit(0)

    aggregated = {}
    for fp in cell_files:
        print(f"  Processing {fp.name}...")
        cell_result = process_cell_file(fp)
        key = f"{cell_result['subject']}_{cell_result['roi']}"
        aggregated[key] = cell_result

    out_json = RESULTS_DIR / "aggregated.json"
    with open(out_json, 'w') as f:
        json.dump(aggregated, f, indent=2, default=str)
    print(f"Saved {out_json}")

    # Write SELECTION_REPORT.md
    lines = ["# S7 Selection Report (Stage A–D)", ""]
    lines.append(f"Cells: {len(aggregated)}")
    lines.append(f"Subsets per cell: k=4 (35) + k=5 (21) + k=6 (7) = 63")
    lines.append(f"Stage B/C/D evaluated at k={COMBO_K}")
    lines.append("")

    lines.append("## RQ1+RQ4 PASS candidates (single losses, k=5)")
    lines.append("")
    for key, cell in aggregated.items():
        passes = [p for p in cell['cell_pass_summary'] if p['all_pass']]
        if not passes:
            continue
        lines.append(f"### {key}")
        for p in passes:
            lines.append(f"- **{p['loss']} × {p['model']}**: CoV={p['cov']:.3f}, "
                         f"SEP={p['sep_rate']:.2f}, CI95={p['ci95']}, "
                         f"Overfit ratio={p['overfit_ratio']:.2f}")
        lines.append("")

    lines.append("## Per-cell Stage A (single, k=5) summary")
    for key, cell in aggregated.items():
        lines.append(f"### {key}")
        lines.append("| Loss × Model | n | median | SD | CoV | SEP | CI95 | bdy_low | bdy_high |")
        lines.append("|---|---|---|---|---|---|---|---|---|")
        def fmt(v, spec='.3f'):
            if v is None or (isinstance(v, float) and not np.isfinite(v)):
                return 'NA'
            return format(v, spec)

        for lm, s in cell['stage_a_k5'].items():
            ci_str = f"[{s['ci95'][0]:.2f},{s['ci95'][1]:.2f}]" if s.get('ci95') else "—"
            lines.append(
                f"| {lm} | {s['n']} | "
                f"{fmt(s['median'])} | {fmt(s['sd'])} | "
                f"{fmt(s['cov'])} | "
                f"{fmt(s['sep_rate'], '.2f')} | "
                f"{ci_str} | "
                f"{fmt(s['boundary_low_rate'], '.2f')} | "
                f"{fmt(s['boundary_high_rate'], '.2f')} |"
            )
        lines.append("")

    out_md = RESULTS_DIR / "SELECTION_REPORT.md"
    with open(out_md, 'w') as f:
        f.write('\n'.join(lines))
    print(f"Saved {out_md}")


if __name__ == "__main__":
    main()
