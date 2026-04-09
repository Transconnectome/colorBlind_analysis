#!/usr/bin/env python3
"""
analyze_ccc_and_metrics.py — CCC analysis + alternative metric evaluation on ΔRDM sim results.

Computes:
1. CCC (Lin's Concordance Correlation Coefficient) for all 48 sim combinations
2. Hypergeometric test for worst-3 overlap
3. Weighted Spearman (extreme-weighted)
4. MSE-based metrics
5. HC LOCO baseline comparison

All computed from existing vuln_synthetic / vuln_observed in results/sim/.
"""

import json
import numpy as np
from pathlib import Path
from itertools import permutations
from scipy.stats import spearmanr, hypergeom
from scipy.spatial.distance import cosine as cosine_dist
import warnings

warnings.filterwarnings('ignore', category=RuntimeWarning)

# ============================================================================
# Paths
# ============================================================================
SIM_DIR = Path(__file__).resolve().parent.parent / 'results' / 'sim'
FWD_RESULTS = Path(__file__).resolve().parent.parent.parent.parent / 'future_phase1_forward_model' / 'results'
COLOR_NAMES = ['red', 'orange', 'yellow', 'green', 'cyan', 'blue', 'purple', 'magenta']

# ============================================================================
# Metric functions
# ============================================================================

def lin_ccc(x, y):
    """Lin's Concordance Correlation Coefficient (1989).

    CCC = (2 * ρ * σ_x * σ_y) / (σ_x² + σ_y² + (μ_x - μ_y)²)

    where ρ = Pearson correlation, σ = standard deviation, μ = mean.

    Properties:
    - Range: [-1, 1]
    - CCC = 1 iff perfect agreement (x_i = y_i for all i)
    - CCC = ρ only when σ_x = σ_y and μ_x = μ_y (no scale/location shift)
    - CCC < ρ when scale or location differs (penalizes bias)

    Interpretation:
    - CCC captures both PATTERN correlation (ρ) and SCALE agreement (σ, μ)
    - High ρ but low CCC → correct ranking but wrong magnitude
    - This is critical for filter design: we need magnitude-correct predictions

    Reference: Lin, L.I.-K. (1989). A concordance correlation coefficient to
    evaluate reproducibility. Biometrics, 45(1), 255-268.
    """
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    mx, my = np.mean(x), np.mean(y)
    sx, sy = np.std(x, ddof=0), np.std(y, ddof=0)

    if sx < 1e-12 or sy < 1e-12:
        return 0.0

    rho = np.corrcoef(x, y)[0, 1]
    if not np.isfinite(rho):
        return 0.0

    ccc = (2 * rho * sx * sy) / (sx**2 + sy**2 + (mx - my)**2)
    return float(ccc)


def weighted_spearman(x, y, weight_type='extreme'):
    """Spearman weighted by extreme values (worst colors matter more).

    weight_type:
    - 'extreme': w_i = |rank_i - median_rank|  (emphasizes top/bottom)
    - 'worst': w_i = max(0, median_rank - rank_i)  (emphasizes worst only)
    """
    from scipy.stats import rankdata
    rx = rankdata(x)
    ry = rankdata(y)
    n = len(x)
    median_rank = (n + 1) / 2

    if weight_type == 'extreme':
        w = np.abs(rx - median_rank) + np.abs(ry - median_rank)
    elif weight_type == 'worst':
        w = np.maximum(0, median_rank - rx) + np.maximum(0, median_rank - ry)
    else:
        w = np.ones(n)

    w = w / w.sum()

    # Weighted correlation
    mx = np.average(rx, weights=w)
    my = np.average(ry, weights=w)
    cov = np.average((rx - mx) * (ry - my), weights=w)
    sx = np.sqrt(np.average((rx - mx)**2, weights=w))
    sy = np.sqrt(np.average((ry - my)**2, weights=w))

    if sx < 1e-12 or sy < 1e-12:
        return 0.0
    return float(cov / (sx * sy))


def profile_mse(x, y):
    """Mean Squared Error between profiles (scale-sensitive)."""
    return float(np.mean((np.asarray(x) - np.asarray(y))**2))


def cosine_similarity(x, y):
    """Cosine similarity (direction-only, scale-invariant)."""
    x, y = np.asarray(x), np.asarray(y)
    norm_x, norm_y = np.linalg.norm(x), np.linalg.norm(y)
    if norm_x < 1e-12 or norm_y < 1e-12:
        return 0.0
    return float(np.dot(x, y) / (norm_x * norm_y))


def hypergeom_worst3_pvalue(overlap, n_total=8, k_select=3):
    """P-value for worst-3 overlap via hypergeometric distribution.

    H0: worst-3 are drawn independently
    P(overlap >= k) = sum_{i=k}^{min(3,3)} P(X=i)

    hypergeom(M=8, n=3, N=3): X ~ number of "observed worst-3" in "synthetic worst-3"
    """
    # P(X >= overlap)
    p = hypergeom.sf(overlap - 1, n_total, k_select, k_select)
    return float(p)


# ============================================================================
# Permutation tests
# ============================================================================

def perm_test_exact(metric_func, synthetic, observed, higher_is_better=True):
    """Exact permutation test (8! = 40320) for any metric function."""
    obs_val = metric_func(synthetic, observed)

    count = 0
    total = 0
    for perm in permutations(range(8)):
        perm_val = metric_func(np.asarray(synthetic)[list(perm)], observed)
        total += 1
        if higher_is_better:
            if perm_val >= obs_val:
                count += 1
        else:  # lower is better (e.g., MSE)
            if perm_val <= obs_val:
                count += 1

    p = (count + 1) / (total + 1)
    return obs_val, p


# ============================================================================
# Load observed LOCO
# ============================================================================

def load_observed_loco(sub_id, roi):
    """Load observed CVD LOCO from forward model validation results."""
    loco_path = FWD_RESULTS / 'validation' / f'sub-{sub_id}_loco.json'
    if not loco_path.exists():
        return None

    with open(loco_path) as f:
        data = json.load(f)

    roi_key = roi
    if roi_key not in data:
        return None

    folds = data[roi_key]['ridge_gcv']['folds']
    vuln = np.zeros(8)
    for fold in folds:
        vuln[fold['test_color']] = fold['voxel_corr']
    return vuln


def load_hc_loco(roi):
    """Load HC LOCO from forward model validation results."""
    hc_vulns = {}
    for sub_id in ['01', '02', '03', '04', '05', '06', '07']:
        loco_path = FWD_RESULTS / 'validation' / f'sub-{sub_id}_loco.json'
        if not loco_path.exists():
            continue
        with open(loco_path) as f:
            data = json.load(f)
        roi_key = roi
        if roi_key not in data:
            continue
        folds = data[roi_key]['ridge_gcv']['folds']
        vuln = np.zeros(8)
        for fold in folds:
            vuln[fold['test_color']] = fold['voxel_corr']
        hc_vulns[sub_id] = vuln
    return hc_vulns


# ============================================================================
# Main analysis
# ============================================================================

def analyze_all_sims():
    """Run comprehensive metric analysis on all sim results."""

    summary_path = SIM_DIR / 'summary.json'
    with open(summary_path) as f:
        summary = json.load(f)

    results = []

    for row in summary['rows']:
        sub = row['subject'].replace('sub-', '')
        roi = row['roi']
        model = row['model']
        metric = row['metric']

        # Load detailed result
        result_dir = SIM_DIR / f'{row["subject"]}_{roi}_{model}_{metric}'
        result_path = result_dir / 'result.json'

        if not result_path.exists():
            continue

        with open(result_path) as f:
            detail = json.load(f)

        vuln_syn = np.array(detail['phase_c']['vuln_synthetic'])
        vuln_obs_raw = detail['phase_c'].get('vuln_observed')

        if vuln_obs_raw is None:
            continue

        vuln_obs = np.array(vuln_obs_raw)

        # --- Existing metrics ---
        spearman_rho = row['loco_spearman']
        spearman_perm_p = row['loco_perm_p']
        rdm_r = row['rdm_pearson_r']
        rdm_p = row['rdm_perm_p']

        # --- New metrics ---
        # 1. CCC
        ccc_val = lin_ccc(vuln_syn, vuln_obs)
        ccc_obs, ccc_perm_p = perm_test_exact(lin_ccc, vuln_syn, vuln_obs, higher_is_better=True)

        # 2. Hypergeometric worst-3
        overlap = row['worst3_overlap']
        hyper_p = hypergeom_worst3_pvalue(overlap)

        # 3. Weighted Spearman
        w_spearman = weighted_spearman(vuln_syn, vuln_obs, 'extreme')
        w_spearman_obs, w_spearman_perm_p = perm_test_exact(
            lambda x, y: weighted_spearman(x, y, 'extreme'),
            vuln_syn, vuln_obs, higher_is_better=True
        )

        # 4. Cosine similarity of vulnerability profiles
        cos_sim = cosine_similarity(vuln_syn, vuln_obs)
        cos_obs, cos_perm_p = perm_test_exact(cosine_similarity, vuln_syn, vuln_obs, higher_is_better=True)

        # 5. Profile MSE
        mse_val = profile_mse(vuln_syn, vuln_obs)

        results.append({
            'subject': row['subject'],
            'cvd_type': row.get('cvd_type', ''),
            'roi': roi,
            'model': model,
            'model_df': row['model_df'],
            'metric': metric,
            # Phase A
            'rdm_r': rdm_r,
            'rdm_p': rdm_p,
            'rdm_sig': row['rdm_sig'],
            # Phase C - existing
            'spearman_rho': spearman_rho,
            'spearman_perm_p': spearman_perm_p,
            'worst3_overlap': overlap,
            # Phase C - new
            'ccc': ccc_val,
            'ccc_perm_p': ccc_perm_p,
            'hyper_p_worst3': hyper_p,
            'weighted_spearman': w_spearman,
            'weighted_spearman_perm_p': w_spearman_perm_p,
            'cosine_sim': cos_sim,
            'cosine_perm_p': cos_perm_p,
            'profile_mse': mse_val,
            # Raw profiles
            'vuln_syn': vuln_syn.tolist(),
            'vuln_obs': vuln_obs.tolist(),
        })

    return results


def analyze_hc_loco_baseline():
    """Compare HC LOCO performance to understand CVD deficit."""
    baseline = {}

    for roi in ['V1', 'V2']:
        hc_vulns = load_hc_loco(roi)
        if not hc_vulns:
            continue

        # HC mean/sd per color
        hc_matrix = np.array([hc_vulns[s] for s in sorted(hc_vulns.keys())])
        hc_mean = hc_matrix.mean(axis=0)
        hc_sd = hc_matrix.std(axis=0, ddof=1)
        hc_grand_mean = hc_matrix.mean()

        cvd_data = {}
        for cvd_sub in ['08', '09', '10']:
            vuln = load_observed_loco(cvd_sub, roi)
            if vuln is not None:
                cvd_mean = vuln.mean()
                # Crawford & Howell t-test for single case vs group
                n_hc = len(hc_vulns)
                t_val = (cvd_mean - hc_grand_mean) / (hc_matrix.mean(axis=1).std(ddof=1) * np.sqrt(1 + 1/n_hc))

                cvd_data[cvd_sub] = {
                    'vuln': vuln.tolist(),
                    'mean': float(cvd_mean),
                    'min': float(vuln.min()),
                    'n_negative': int(np.sum(vuln < 0)),
                    'worst3_colors': [COLOR_NAMES[i] for i in np.argsort(vuln)[:3]],
                    'crawford_t': float(t_val),
                }

        baseline[roi] = {
            'hc_mean_per_color': hc_mean.tolist(),
            'hc_sd_per_color': hc_sd.tolist(),
            'hc_grand_mean': float(hc_grand_mean),
            'hc_per_subject_means': {s: float(hc_vulns[s].mean()) for s in sorted(hc_vulns.keys())},
            'hc_per_subject_profiles': {s: hc_vulns[s].tolist() for s in sorted(hc_vulns.keys())},
            'cvd': cvd_data,
        }

    return baseline


def print_report(results, baseline):
    """Print formatted analysis report."""

    print("=" * 100)
    print("CCC & Alternative Metric Analysis Report")
    print("=" * 100)

    # --- Section 1: CCC Definition ---
    print("\n## 1. CCC (Lin's Concordance Correlation Coefficient) 정의")
    print()
    print("  공식: CCC = (2 × ρ × σ_x × σ_y) / (σ_x² + σ_y² + (μ_x − μ_y)²)")
    print()
    print("  = ρ × C_b")
    print("  여기서 C_b = 2σ_xσ_y / (σ_x² + σ_y² + (μ_x − μ_y)²)  (bias correction factor)")
    print()
    print("  ρ = Pearson correlation (패턴 일치)")
    print("  C_b = scale/location agreement (크기·위치 일치)")
    print()
    print("  핵심 특성:")
    print("  - CCC ≤ ρ (항상). 등호: σ_x = σ_y, μ_x = μ_y 일 때만")
    print("  - Spearman은 순위만, Pearson은 선형관계만. CCC는 pattern + scale + location 동시 측정")
    print("  - 필터 설계에서는 magnitude-correct prediction이 필요 → CCC가 Spearman보다 적합")
    print()

    # --- Section 2: Full metric comparison table ---
    print("\n## 2. 전체 결과: Phase A sig + Phase C 다중 지표")
    print()

    # Filter to Phase A significant only
    sig_results = [r for r in results if r['rdm_sig']]

    # Sort by CCC descending
    sig_results.sort(key=lambda r: r['ccc'], reverse=True)

    header = f"{'Sub':>6} {'ROI':>3} {'Model':>10} {'Metric':>8} | {'Spearman':>9} {'Sp.p':>6} | {'CCC':>7} {'CCC.p':>6} | {'W.Sp':>6} {'W.p':>6} | {'Cos':>6} {'Cos.p':>6} | {'W3':>2} {'Hyp.p':>6}"
    print(header)
    print("-" * len(header))

    for r in sig_results:
        sp_star = '*' if r['spearman_perm_p'] < 0.05 else ('†' if r['spearman_perm_p'] < 0.10 else '')
        ccc_star = '*' if r['ccc_perm_p'] < 0.05 else ('†' if r['ccc_perm_p'] < 0.10 else '')
        wsp_star = '*' if r['weighted_spearman_perm_p'] < 0.05 else ('†' if r['weighted_spearman_perm_p'] < 0.10 else '')
        cos_star = '*' if r['cosine_perm_p'] < 0.05 else ('†' if r['cosine_perm_p'] < 0.10 else '')
        hyp_star = '*' if r['hyper_p_worst3'] < 0.05 else ('†' if r['hyper_p_worst3'] < 0.10 else '')

        print(f"{r['subject']:>6} {r['roi']:>3} {r['model']:>10} {r['metric']:>8} | "
              f"{r['spearman_rho']:>+7.3f}{sp_star:<2} {r['spearman_perm_p']:>5.3f} | "
              f"{r['ccc']:>+6.3f}{ccc_star:<1} {r['ccc_perm_p']:>5.3f} | "
              f"{r['weighted_spearman']:>+5.3f}{wsp_star:<1} {r['weighted_spearman_perm_p']:>5.3f} | "
              f"{r['cosine_sim']:>+5.3f}{cos_star:<1} {r['cosine_perm_p']:>5.3f} | "
              f"{r['worst3_overlap']:>2} {r['hyper_p_worst3']:>5.3f}{hyp_star}")

    # --- Section 3: CCC vs Spearman comparison ---
    print("\n\n## 3. CCC vs Spearman 비교 — 핵심 조합")
    print()

    key_combos = [
        ('sub-09', 'V2', 'cone_1way', 'cosine'),
        ('sub-09', 'V2', 'cone_3way', 'cosine'),
        ('sub-08', 'V2', 'fourier', 'cosine'),
        ('sub-08', 'V1', 'fourier', 'cosine'),
        ('sub-08', 'V2', 'cone_3way', 'triangle'),
        ('sub-08', 'V2', 'cone_3way', 'corr'),
    ]

    for sub, roi, model, metric in key_combos:
        matches = [r for r in results
                   if r['subject'] == sub and r['roi'] == roi
                   and r['model'] == model and r['metric'] == metric]
        if not matches:
            continue
        r = matches[0]

        # Decompose CCC = ρ × C_b
        vuln_s = np.array(r['vuln_syn'])
        vuln_o = np.array(r['vuln_obs'])
        pearson_r = np.corrcoef(vuln_s, vuln_o)[0, 1]
        cb = r['ccc'] / pearson_r if abs(pearson_r) > 1e-10 else 0.0

        print(f"  {sub} {roi} {model}×{metric}:")
        print(f"    Spearman ρ = {r['spearman_rho']:+.3f} (p={r['spearman_perm_p']:.3f})")
        print(f"    Pearson  r = {pearson_r:+.3f}")
        print(f"    CCC        = {r['ccc']:+.3f} (p={r['ccc_perm_p']:.3f})")
        print(f"    C_b (bias) = {cb:+.3f}  ← {('large bias' if abs(cb) < 0.5 else 'moderate bias' if abs(cb) < 0.8 else 'small bias')}")
        print(f"    vuln_syn range: [{vuln_s.min():.3f}, {vuln_s.max():.3f}], mean={vuln_s.mean():.3f}")
        print(f"    vuln_obs range: [{vuln_o.min():.3f}, {vuln_o.max():.3f}], mean={vuln_o.mean():.3f}")
        print()

    # --- Section 4: HC vs CVD LOCO baseline ---
    print("\n## 4. HC vs CVD LOCO Baseline")
    print()

    for roi in ['V1', 'V2']:
        if roi not in baseline:
            continue
        b = baseline[roi]

        print(f"  {roi}:")
        print(f"    HC grand mean LOCO = {b['hc_grand_mean']:.3f}")
        print(f"    HC per-subject means: {', '.join(f'{s}={v:.3f}' for s, v in sorted(b['hc_per_subject_means'].items()))}")

        for cvd_sub, cvd_info in sorted(b['cvd'].items()):
            deficit = cvd_info['mean'] - b['hc_grand_mean']
            print(f"    sub-{cvd_sub}: mean={cvd_info['mean']:.3f} (Δ={deficit:+.3f}, t={cvd_info['crawford_t']:.2f})")
            print(f"      n_negative={cvd_info['n_negative']}/8, worst3={cvd_info['worst3_colors']}")
            print(f"      profile: {[f'{v:.3f}' for v in cvd_info['vuln']]}")
        print()

    # --- Section 5: Newly significant results (CCC or alternatives) ---
    print("\n## 5. 새로 유의해진 조합 (CCC 또는 대안 지표)")
    print()

    newly_sig = []
    for r in results:
        if not r['rdm_sig']:
            continue

        sp_sig = r['spearman_perm_p'] < 0.05
        ccc_sig = r['ccc_perm_p'] < 0.05
        wsp_sig = r['weighted_spearman_perm_p'] < 0.05
        cos_sig = r['cosine_perm_p'] < 0.05

        new_metrics = []
        if ccc_sig and not sp_sig:
            new_metrics.append(f'CCC={r["ccc"]:+.3f} (p={r["ccc_perm_p"]:.4f})')
        if wsp_sig and not sp_sig:
            new_metrics.append(f'W.Sp={r["weighted_spearman"]:+.3f} (p={r["weighted_spearman_perm_p"]:.4f})')
        if cos_sig and not sp_sig:
            new_metrics.append(f'Cos={r["cosine_sim"]:+.3f} (p={r["cosine_perm_p"]:.4f})')

        if new_metrics:
            newly_sig.append((r, new_metrics))

    if newly_sig:
        for r, metrics in newly_sig:
            print(f"  {r['subject']} {r['roi']} {r['model']}×{r['metric']}: "
                  f"Spearman={r['spearman_rho']:+.3f} (p={r['spearman_perm_p']:.3f} NS)")
            for m in metrics:
                print(f"    → NEW SIG: {m}")
            print()
    else:
        print("  None found (CCC/alternatives did not rescue any NS Spearman result)")
        print()

    # Also check trending → significant upgrades
    print("  Trending → significant upgrades:")
    trending_upgraded = []
    for r in results:
        if not r['rdm_sig']:
            continue

        sp_trending = 0.05 <= r['spearman_perm_p'] < 0.10

        if sp_trending:
            upgrades = []
            if r['ccc_perm_p'] < 0.05:
                upgrades.append(f'CCC p={r["ccc_perm_p"]:.4f}')
            if r['weighted_spearman_perm_p'] < 0.05:
                upgrades.append(f'W.Sp p={r["weighted_spearman_perm_p"]:.4f}')
            if r['cosine_perm_p'] < 0.05:
                upgrades.append(f'Cos p={r["cosine_perm_p"]:.4f}')

            if upgrades:
                trending_upgraded.append((r, upgrades))

    if trending_upgraded:
        for r, upgrades in trending_upgraded:
            print(f"  {r['subject']} {r['roi']} {r['model']}×{r['metric']}: "
                  f"Spearman trending p={r['spearman_perm_p']:.3f}")
            for u in upgrades:
                print(f"    → UPGRADED: {u}")
            print()
    else:
        print("  None found")
        print()

    # --- Section 6: Singularity analysis ---
    print("\n## 6. Singularity 분석: ΔRDM metric 간 δθ 일관성")
    print()

    for sub in ['sub-08', 'sub-09']:
        for roi in ['V1', 'V2']:
            print(f"  {sub} {roi}:")
            sub_results = [r for r in results
                          if r['subject'] == sub and r['roi'] == roi and r['rdm_sig']]

            if not sub_results:
                print("    No Phase A significant results")
                print()
                continue

            # Load delta_theta_deg from detail files
            deltas = {}
            for r in sub_results:
                result_dir = SIM_DIR / f'{r["subject"]}_{roi}_{r["model"]}_{r["metric"]}'
                with open(result_dir / 'result.json') as f:
                    detail = json.load(f)
                key = f"{r['model']}×{r['metric']}"
                deltas[key] = np.array(detail['phase_a']['delta_theta_deg'])

            # Pairwise correlation of delta_theta profiles
            keys = sorted(deltas.keys())
            if len(keys) > 1:
                print(f"    δθ profile correlation matrix ({len(keys)} sig combos):")
                for i, k1 in enumerate(keys):
                    for j, k2 in enumerate(keys):
                        if j > i:
                            r_val = np.corrcoef(deltas[k1], deltas[k2])[0, 1]
                            print(f"      {k1} vs {k2}: r={r_val:.3f}")

            # Check cone_1way δ* consistency across metrics
            cone_1way_deltas = {r['metric']: r for r in sub_results if r['model'] == 'cone_1way'}
            if cone_1way_deltas:
                cone_params = []
                for metric_name, r in sorted(cone_1way_deltas.items()):
                    result_dir = SIM_DIR / f'{r["subject"]}_{roi}_cone_1way_{metric_name}'
                    with open(result_dir / 'result.json') as f:
                        detail = json.load(f)
                    cone_params.append((metric_name, detail['phase_a']['best_params'][0]))

                print(f"    cone_1way δ* across metrics: {', '.join(f'{m}={p:.1f}nm' for m, p in cone_params)}")
                vals = [p for _, p in cone_params]
                print(f"    Range: {min(vals):.1f}–{max(vals):.1f}nm, SD={np.std(vals):.1f}nm")

            print()

    return results, baseline


# ============================================================================
# Save results
# ============================================================================

def save_results(results, baseline):
    """Save comprehensive results to JSON."""
    output = {
        'description': 'CCC & alternative metric analysis on ΔRDM simulation results',
        'metrics_computed': {
            'ccc': 'Lin\'s Concordance Correlation Coefficient: 2ρσ_xσ_y / (σ_x² + σ_y² + (μ_x - μ_y)²)',
            'weighted_spearman': 'Extreme-value-weighted Spearman (worst+best colors upweighted)',
            'cosine_sim': 'Cosine similarity of vulnerability profiles',
            'hyper_p_worst3': 'Hypergeometric p-value for worst-3 overlap',
            'profile_mse': 'Mean squared error between vulnerability profiles',
        },
        'results': results,
        'hc_cvd_baseline': baseline,
    }

    output_path = SIM_DIR / 'ccc_analysis.json'
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2, default=str)
    print(f"\nSaved to {output_path}")


if __name__ == '__main__':
    print("Loading sim results and computing CCC + alternative metrics...")
    print("(Exact permutation: 8! = 40,320 per metric per combination — this takes ~5-10 minutes)\n")

    results = analyze_all_sims()
    baseline = analyze_hc_loco_baseline()

    print_report(results, baseline)
    save_results(results, baseline)
