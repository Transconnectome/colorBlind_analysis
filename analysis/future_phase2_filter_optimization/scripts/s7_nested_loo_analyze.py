"""Aggregate S7 Nested-LOO per-cell JSONs into a single summary + SELECTION_REPORT_NESTED.md.

Reads:  results/s7_nested_loo/cell_*.json
Writes: results/s7_nested_loo/aggregated.json
        results/s7_nested_loo/SELECTION_REPORT_NESTED.md
"""
import json
import sys
from pathlib import Path
import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
RESULTS_DIR = SCRIPT_DIR.parent / "results" / "s7_nested_loo"
SINGLE_LOO_DIR = SCRIPT_DIR.parent / "results" / "s7_loss_combo_subset"

LAMBDA_KEYS = ['0.00', '0.25', '0.50', '0.75', '1.00']


def fmt(x, p=3):
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "NA"
    if isinstance(x, float):
        return f"{x:.{p}f}"
    return str(x)


def find_optimal_lambda(per_lambda_dict, model_label):
    """Pick optimal λ per model_label by lowest inner CoV among non-degenerate fits."""
    cands = []
    for lk in LAMBDA_KEYS:
        st = per_lambda_dict.get(lk, {})
        cov = st.get('inner_cov_mean')
        bdy = st.get('boundary_rate_mean')
        if cov is None or not np.isfinite(cov):
            continue
        if bdy is not None and bdy > 0.5:
            continue
        cands.append({'lambda': lk, 'cov': cov, 'bdy': bdy, 'st': st})
    if not cands:
        return None
    cands.sort(key=lambda c: c['cov'])
    return cands[0]


def main():
    cell_files = sorted(RESULTS_DIR.glob("cell_*.json"))
    cell_files = [f for f in cell_files if 'smoke' not in f.name]
    print(f"Loading {len(cell_files)} cells...")

    by_key = {}
    for fp in cell_files:
        with open(fp) as f:
            d = json.load(f)
        key = f"{d['subject']}_{d['roi']}"
        by_key[key] = d

    aggregated = {
        'design': 'Nested LOO: 7 outer × C(6,4)=15 inner subsets × 5 λ × (R+C 3 src + 2-comp)',
        'probe': 'gamma_plus_RDM',
        'lambda_values': [0.0, 0.25, 0.5, 0.75, 1.0],
        'cells': {},
    }

    for key, d in by_key.items():
        cell_summary = {
            'subject': d['subject'],
            'family': d['family'],
            'roi': d['roi'],
            'K': d['K'],
            'has_cvd_jnd': d.get('has_cvd_jnd'),
            'n_outer_folds': len(d.get('per_outer_fold', [])),
            'aggregated': d['aggregated'],
            'optimal_per_model': {},
        }
        for model_label, per_lambda in d['aggregated'].items():
            opt = find_optimal_lambda(per_lambda, model_label)
            cell_summary['optimal_per_model'][model_label] = opt
        aggregated['cells'][key] = cell_summary

    out_json = RESULTS_DIR / "aggregated.json"
    with open(out_json, 'w') as f:
        json.dump(aggregated, f, indent=2, default=str)
    print(f"Saved: {out_json}")

    # Build SELECTION_REPORT_NESTED.md
    md = []
    md.append("# S7 Nested-LOO Selection Report")
    md.append("")
    md.append("**Design**: Outer 7-fold LOO over HC × inner C(6,4)=15 subset resample × "
              "5 λ on gamma_plus_RDM probe × (R+C [3 Δλ sources] + 2-comp).")
    md.append("")
    md.append("**Robustness statement**: Inner CoV measures parameter stability on a 6-HC pool that excludes the outer held-out HC; ")
    md.append("test L_γ is evaluated on the held-out HC at the inner-median δθ. ")
    md.append("Lower inner CoV = more stable selection. Test L_γ is a *Crawford-Howell-style specificity check*: ")
    md.append("if fitted (g) or (β_s, β_c) captures real CVD-axis distortion, applying it to HC should INCREASE L_γ relative to HC's near-zero baseline. ")
    md.append("**Lower test L_γ does NOT mean better filter** — it can mean the fit looks HC-like (selection false positive).")
    md.append("")
    md.append("**Comparison with single-LOO S7** (`lambda_optimal_behav_rdm.json`): "
              "single-LOO trains on k=5 subsets within full 7-HC pool and tests on complement (1-2 HC). ")
    md.append("Nested-LOO trains on k=4 within 6-HC pool, tests on outer held-out HC. ")
    md.append("Test denominators differ → numerical L_γ values are not directly comparable; ")
    md.append("only the QUALITATIVE patterns (best λ, model rank by CoV) are compared.")
    md.append("")
    md.append("---")
    md.append("")

    # Per-cell tables
    for key in sorted(by_key.keys()):
        d = by_key[key]
        agg = d['aggregated']
        md.append(f"## {key}  (family={d['family']}, K={d['K']}, JND={'yes' if d.get('has_cvd_jnd') else 'NO'})")
        md.append("")
        for model_label in sorted(agg.keys()):
            md.append(f"### {model_label}")
            md.append("")
            md.append("| λ | param/(β_s,β_c) | inner_CoV_mean | boundary_rate | test_L_γ_mean | n_outer_test |")
            md.append("|---|---|---|---|---|---|")
            for lk in LAMBDA_KEYS:
                st = agg[model_label].get(lk, {})
                if model_label == '2comp':
                    p_str = (f"({fmt(st.get('beta_s_mean_of_medians'), 1)}, "
                             f"{fmt(st.get('beta_c_mean_of_medians'), 1)})")
                else:
                    p_str = fmt(st.get('param_mean_of_medians'), 3)
                md.append(f"| {lk} | {p_str} | {fmt(st.get('inner_cov_mean'), 4)} | "
                          f"{fmt(st.get('boundary_rate_mean'), 2)} | "
                          f"{fmt(st.get('test_L_gamma_mean'), 4)} | "
                          f"{fmt(st.get('n_outer_with_test'), 0)} |")
            md.append("")

        # Optimal selection per model
        md.append("**Optimal λ (lowest inner CoV, non-degenerate boundary_rate ≤ 0.5):**")
        md.append("")
        for model_label in sorted(agg.keys()):
            per_lambda = agg[model_label]
            opt = find_optimal_lambda(per_lambda, model_label)
            if opt is None:
                md.append(f"- {model_label}: ALL degenerate (boundary > 0.5 or no valid fit)")
            else:
                st = opt['st']
                if model_label == '2comp':
                    p_str = (f"(β_s={fmt(st.get('beta_s_mean_of_medians'), 1)}, "
                             f"β_c={fmt(st.get('beta_c_mean_of_medians'), 1)})")
                else:
                    p_str = f"g={fmt(st.get('param_mean_of_medians'), 3)}"
                md.append(f"- **{model_label}**: λ={opt['lambda']}, {p_str}, "
                          f"inner_CoV={fmt(opt['cov'], 4)}, "
                          f"test_L_γ_mean={fmt(st.get('test_L_gamma_mean'), 4)}")
        md.append("")
        md.append("---")
        md.append("")

    # Comparison with single-LOO S7
    single_loo_summary = SINGLE_LOO_DIR / "lambda_optimal_behav_rdm.json"
    if single_loo_summary.exists():
        md.append("## Comparison with single-LOO S7")
        md.append("")
        md.append("Single-LOO source: `results/s7_loss_combo_subset/lambda_optimal_behav_rdm.json`. ")
        md.append("For each cell, we compare nested-LOO optimal λ to single-LOO optimal λ on `rc_DPS` and `2comp`.")
        md.append("")
        md.append("| Cell | Model | Single-LOO opt λ | Single g/(β_s,β_c) | Nested opt λ | Nested g/(β_s,β_c) | Same λ? |")
        md.append("|---|---|---|---|---|---|---|")
        with open(single_loo_summary) as f:
            single = json.load(f)
        for key in sorted(by_key.keys()):
            d = by_key[key]
            single_cell = single.get(key, {})
            for model_label_single in ['rc_DPS', '2comp']:
                if model_label_single == 'rc_DPS':
                    # nested label = rc_DPS_lit
                    model_label_nested = 'rc_DPS_lit'
                else:
                    model_label_nested = '2comp'
                s_data = single_cell.get(model_label_single, {})
                s_opt = s_data.get('optimal_ranked', [])
                s_top = s_opt[0] if s_opt else None
                n_opt = find_optimal_lambda(
                    d['aggregated'].get(model_label_nested, {}), model_label_nested)
                if s_top is None and n_opt is None:
                    continue
                s_lam = s_top['lambda'] if s_top else 'NA'
                s_pm = fmt(s_top.get('param_median'), 2) if s_top else 'NA'
                if n_opt is None:
                    n_lam = 'NA'
                    n_pm = 'NA'
                else:
                    n_lam = n_opt['lambda']
                    nst = n_opt['st']
                    if model_label_nested == '2comp':
                        n_pm = (f"({fmt(nst.get('beta_s_mean_of_medians'), 1)},"
                                f"{fmt(nst.get('beta_c_mean_of_medians'), 1)})")
                    else:
                        n_pm = fmt(nst.get('param_mean_of_medians'), 2)
                same = "yes" if s_lam == n_lam else "NO"
                md.append(f"| {key} | {model_label_single} | {s_lam} | {s_pm} | {n_lam} | {n_pm} | {same} |")
        md.append("")

    md.append("## Notes / Caveats")
    md.append("")
    md.append("- Sub-10 cells (V1–V4) have no JND data → L_γ unavailable. Only λ=1.0 (pure L_RDM) "
              "has fit values via single-loss fallback; other λ are all None.")
    md.append("- HC sub-04 outlier is in the inner pool for 6/7 outer folds. Nested-LOO does NOT remove its influence — ")
    md.append("  it merely de-couples it from the test denominator on the fold where sub-04 is held out.")
    md.append("- Inner k=4 (C(6,4)=15) chosen to match single-LOO k=5 in 'pool minus one' arithmetic; ")
    md.append("  with k=4, inner subsets are more diverse → CoV is upper-bounded relative to single-LOO k=5.")
    md.append("- Test L_γ semantics: test loss closure uses HC_i as TARGET (not CVD subject) with inner_pool as JND baseline. "
              "Evaluates L_γ at median(δθ) from CVD fits. A fitted CVD distortion applied to HC should "
              "yield L_γ HIGHER than baseline (since HC has no distortion). Read direction with care.")
    md.append("- This nested-LOO is a *robustness check*. The PI feedback on double-dipping is only PARTIALLY addressed: ")
    md.append("  inner CoV is double-dip-free, but the data is still the same fMRI dataset. ")
    md.append("  Real validation = separate behavioral filter test (Phase 3).")
    md.append("")

    out_md = RESULTS_DIR / "SELECTION_REPORT_NESTED.md"
    with open(out_md, 'w') as f:
        f.write("\n".join(md))
    print(f"Saved: {out_md}")


if __name__ == "__main__":
    main()
