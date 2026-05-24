"""S6': Aggregate per-cell JSONs into SUBSET_REPORT.md + distribution figure.

Inputs:
  results/s6p_hc_subset/{sub-XX}_{ROI}_{RC|2Comp}.json   (8 files)
Outputs:
  results/s6p_hc_subset/SUBSET_REPORT.md
  results/s6p_hc_subset/viz_distribution.png
"""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.stats import wilcoxon

SCRIPT_DIR = Path(__file__).resolve().parent
RESULTS_DIR = SCRIPT_DIR.parent / "results" / "s6p_hc_subset"

CELLS = [
    ('sub-08', 'V1'),
    ('sub-08', 'V4'),
    ('sub-09', 'V1'),
    ('sub-09', 'V4'),
]


def load_records(subject, roi, model_tag):
    path = RESULTS_DIR / f"{subject}_{roi}_{model_tag}.json"
    with open(path) as f:
        return json.load(f)


def cell_paired_stats(rc_data, tc_data):
    """Paired comparison: 2-Comp ρ vs R+C ρ over matched subsets."""
    rc_subsets = rc_data['subsets']
    tc_subsets = tc_data['subsets']
    assert len(rc_subsets) == len(tc_subsets)

    rc_rho = np.array([r['fit']['spearman_rho_best'] for r in rc_subsets])
    tc_rho = np.array([r['fit']['spearman_rho_best'] for r in tc_subsets])
    rc_cos = np.array([r['fit']['cosine_at_spearman_best'] for r in rc_subsets])
    tc_cos = np.array([r['fit']['cosine_at_spearman_best'] for r in tc_subsets])

    diff_rho = tc_rho - rc_rho
    diff_cos = tc_cos - rc_cos
    # 2-Comp better on each subset?
    n_2C_better = int(np.sum(diff_rho > 0))
    n_total = len(diff_rho)
    # Wilcoxon (paired)
    try:
        w_stat, w_p = wilcoxon(diff_rho, alternative='greater',
                                  zero_method='wilcox')
        w_stat = float(w_stat)
        w_p = float(w_p)
    except ValueError:
        w_stat, w_p = float('nan'), float('nan')

    return {
        'n_subsets': n_total,
        'n_2Comp_better_rho': n_2C_better,
        'frac_2Comp_better_rho': n_2C_better / n_total,
        'median_diff_rho_2C_minus_RC': float(np.median(diff_rho)),
        'median_diff_cos_2C_minus_RC': float(np.median(diff_cos)),
        'wilcoxon_W': w_stat,
        'wilcoxon_p_greater': w_p,
    }


def summary_row(data, model_label, key_param):
    """Build one Markdown row of the main table."""
    s = data['summary']
    sp = s['spearman_distribution']
    co = s['cosine_distribution']
    par = s[f'{key_param}_distribution']
    dep = s.get('sub04_dependence')
    if dep is not None:
        dep_str = (f"with={dep['with_sub04_median_spearman']:+.3f} "
                   f"w/o={dep['without_sub04_median_spearman']:+.3f} "
                   f"Δ={dep['delta_spearman']:+.3f}")
        param_dep_str = (f"with={dep['with_sub04_median_param']:.2f} "
                        f"w/o={dep['without_sub04_median_param']:.2f}")
    else:
        dep_str = "n/a"
        param_dep_str = "n/a"

    cell = f"{data['subject']} {data['roi']}"
    return (
        f"| {cell} | {model_label} | {s['n_subsets']} | "
        f"{sp['median']:+.3f} | [{sp['q025']:+.3f}, {sp['q975']:+.3f}] | "
        f"{co['median']:+.3f} | [{co['q025']:+.3f}, {co['q975']:+.3f}] | "
        f"{par['median']:.2f} ± {par['sd']:.2f} | "
        f"{dep_str} | {param_dep_str} |"
    )


def render_distribution_figure():
    """4-panel histogram: rows = subjects, cols = ROIs. Show R+C and 2-Comp Spearman ρ.
    Color-code by sub-04 inclusion.
    """
    fig, axes = plt.subplots(2, 2, figsize=(13, 9), sharex=True)
    for irow, subject in enumerate(['sub-08', 'sub-09']):
        for icol, roi in enumerate(['V1', 'V4']):
            ax = axes[irow, icol]
            rc = load_records(subject, roi, 'RC')
            tc = load_records(subject, roi, '2Comp')
            rc_rho = np.array([r['fit']['spearman_rho_best']
                                for r in rc['subsets']])
            tc_rho = np.array([r['fit']['spearman_rho_best']
                                for r in tc['subsets']])
            rc_w04 = np.array([r['includes_sub04'] for r in rc['subsets']])
            tc_w04 = np.array([r['includes_sub04'] for r in tc['subsets']])

            bins = np.linspace(-0.4, 1.0, 30)
            # R+C — solid bars
            ax.hist(rc_rho[rc_w04], bins=bins, alpha=0.55, color='#d62728',
                    label='R+C w/ sub-04', edgecolor='black', linewidth=0.4)
            ax.hist(rc_rho[~rc_w04], bins=bins, alpha=0.55, color='#1f77b4',
                    label='R+C w/o sub-04', edgecolor='black', linewidth=0.4)
            # 2-Comp — hatched
            ax.hist(tc_rho[tc_w04], bins=bins, alpha=0.55, color='#d62728',
                    hatch='///', edgecolor='black',
                    label='2-Comp w/ sub-04', linewidth=0.4, fill=False)
            ax.hist(tc_rho[~tc_w04], bins=bins, alpha=0.55, color='#1f77b4',
                    hatch='///', edgecolor='black',
                    label='2-Comp w/o sub-04', linewidth=0.4, fill=False)

            # Median markers
            ax.axvline(np.median(rc_rho), color='#d62728', linestyle='-',
                        linewidth=1.5, label=f'R+C med={np.median(rc_rho):+.3f}')
            ax.axvline(np.median(tc_rho), color='#1f77b4', linestyle='--',
                        linewidth=1.5, label=f'2C med={np.median(tc_rho):+.3f}')
            ax.axvline(0, color='gray', linestyle=':', linewidth=0.8)

            n = rc['n_subsets']
            ax.set_title(f"{subject} {roi}  (n={n} subsets, "
                         f"Δλ={rc['delta_lambda_nm']:.0f}nm)")
            ax.set_xlabel('Spearman ρ (ΔRDM_sim, ΔRDM_obs)')
            ax.set_ylabel('Subset count')
            ax.legend(loc='upper left', fontsize=7, ncol=1)
            ax.grid(True, alpha=0.3)
    fig.suptitle("S6': HC subset resample — Spearman ρ distribution per cell",
                  fontsize=12, fontweight='bold')
    fig.tight_layout()
    out_path = RESULTS_DIR / 'viz_distribution.png'
    fig.savefig(out_path, dpi=140, bbox_inches='tight')
    plt.close(fig)
    print(f"Saved figure: {out_path}")


def render_report():
    """Build SUBSET_REPORT.md with the main table + per-cell sub-04 dependence."""
    lines = []
    lines.append("# S6' HC Subset Resample — Spearman-Primary Report")
    lines.append("")
    lines.append("**Design**: For each (subject, ROI), enumerate all C(n,k) HC "
                  "subsets for k∈{4,5,6}, recompute hc_W, ΔRDM_obs, and ΔRDM_sim "
                  "from subset only, then refit R+C 1-DOF (g grid, Δλ_DPS fixed) "
                  "and 2-Component (β_s, β_c symmetric grid step 2). Loss = "
                  "1 − Spearman ρ (Nili 2014 primary metric). Cosine recorded as "
                  "secondary.")
    lines.append("")
    lines.append("**Note on V4 cells**: `load_hc_pool` drops sub-07 a priori "
                  "(16 voxels → degenerate RDM). V4 effective n=6 HCs → C(6,k) "
                  "subsets k∈{4,5,6} = 15+6+1 = **22 subsets**, NOT 63. V1 cells "
                  "have full n=7 → 35+21+7 = 63 subsets.")
    lines.append("")
    lines.append("## Main table")
    lines.append("")
    lines.append("| Cell | Model | n | Spearman ρ median | Spearman ρ 95% CI | "
                  "Cosine median | Cosine 95% CI | Param median ± SD | "
                  "Sub-04 effect (Δρ median) | Sub-04 param effect |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for subject, roi in CELLS:
        rc = load_records(subject, roi, 'RC')
        tc = load_records(subject, roi, '2Comp')
        lines.append(summary_row(rc, 'R+C', 'g_best'))
        lines.append(summary_row(tc, '2-Comp', 'beta_s_best'))
    lines.append("")

    # Paired comparison
    lines.append("## Paired comparison (2-Comp vs R+C, per-subset matched)")
    lines.append("")
    lines.append("| Cell | n | 2-Comp ρ > R+C ρ | Median Δρ (2C − R+C) | "
                  "Median Δcos | Wilcoxon W (greater) | Wilcoxon p |")
    lines.append("|---|---|---|---|---|---|---|")
    paired_all = {}
    for subject, roi in CELLS:
        rc = load_records(subject, roi, 'RC')
        tc = load_records(subject, roi, '2Comp')
        ps = cell_paired_stats(rc, tc)
        paired_all[(subject, roi)] = ps
        lines.append(
            f"| {subject} {roi} | {ps['n_subsets']} | "
            f"{ps['n_2Comp_better_rho']}/{ps['n_subsets']} "
            f"({100*ps['frac_2Comp_better_rho']:.1f}%) | "
            f"{ps['median_diff_rho_2C_minus_RC']:+.3f} | "
            f"{ps['median_diff_cos_2C_minus_RC']:+.3f} | "
            f"{ps['wilcoxon_W']:.1f} | "
            f"{ps['wilcoxon_p_greater']:.4f} |"
        )
    lines.append("")

    # Key paper-relevant questions
    lines.append("## Paper-relevant verdicts")
    lines.append("")

    # Q1: 2-Comp robustness — is 95% CI of Spearman ρ above 0?
    lines.append("### Q1 — 2-Comp robustness: Is Spearman ρ 95% CI > 0?")
    lines.append("")
    lines.append("| Cell | Model | 95% CI [q025, q975] | CI excludes 0? |")
    lines.append("|---|---|---|---|")
    for subject, roi in CELLS:
        for model_label, tag, key in [('R+C', 'RC', 'g_best'),
                                        ('2-Comp', '2Comp', 'beta_s_best')]:
            d = load_records(subject, roi, tag)
            sp = d['summary']['spearman_distribution']
            excl = sp['q025'] > 0
            mark = '✓' if excl else '✗'
            lines.append(
                f"| {subject} {roi} | {model_label} | "
                f"[{sp['q025']:+.3f}, {sp['q975']:+.3f}] | {mark} |"
            )
    lines.append("")

    # Q2: Cosine vs Spearman concordance
    lines.append("### Q2 — Cosine vs Spearman concordance: same model ranking?")
    lines.append("")
    lines.append("Compare median Spearman ρ and median cosine: does 2-Comp > R+C "
                  "hold under both metrics?")
    lines.append("")
    lines.append("| Cell | R+C med ρ | 2C med ρ | 2C > R+C (ρ) | "
                  "R+C med cos | 2C med cos | 2C > R+C (cos) | Concordant? |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for subject, roi in CELLS:
        rc = load_records(subject, roi, 'RC')
        tc = load_records(subject, roi, '2Comp')
        rcs = rc['summary']['spearman_distribution']['median']
        tcs = tc['summary']['spearman_distribution']['median']
        rcc = rc['summary']['cosine_distribution']['median']
        tcc = tc['summary']['cosine_distribution']['median']
        s_win = tcs > rcs
        c_win = tcc > rcc
        concord = '✓' if (s_win == c_win) else '✗'
        lines.append(
            f"| {subject} {roi} | {rcs:+.3f} | {tcs:+.3f} | "
            f"{'2C' if s_win else 'R+C'} | "
            f"{rcc:+.3f} | {tcc:+.3f} | "
            f"{'2C' if c_win else 'R+C'} | {concord} |"
        )
    lines.append("")

    # Q3: sub-04 dependence
    lines.append("### Q3 — Sub-04 outlier dependence")
    lines.append("")
    lines.append("Δρ = median(ρ | sub-04 in subset) − median(ρ | sub-04 absent). "
                  "Positive Δρ means inclusion of sub-04 boosts fit. V4 k=6 "
                  "subset is unique by construction (n=6 HCs, no sub-04 exclusion "
                  "possible at k=6 for V4 since sub-07 already dropped). For "
                  "V4-without-sub-04 we only have k∈{4,5}.")
    lines.append("")
    lines.append("| Cell | Model | with sub-04 med ρ | w/o sub-04 med ρ | Δρ |")
    lines.append("|---|---|---|---|---|")
    for subject, roi in CELLS:
        for model_label, tag in [('R+C', 'RC'), ('2-Comp', '2Comp')]:
            d = load_records(subject, roi, tag)
            dep = d['summary'].get('sub04_dependence')
            if dep is None:
                lines.append(f"| {subject} {roi} | {model_label} | n/a | n/a | n/a |")
            else:
                lines.append(
                    f"| {subject} {roi} | {model_label} | "
                    f"{dep['with_sub04_median_spearman']:+.3f} | "
                    f"{dep['without_sub04_median_spearman']:+.3f} | "
                    f"{dep['delta_spearman']:+.3f} |"
                )
    lines.append("")

    # Q4: Paper claim — robustly > 0?
    lines.append("### Q4 — Paper-grade claim: 2-Comp Spearman ρ robustly > 0?")
    lines.append("")
    for subject, roi in CELLS:
        tc = load_records(subject, roi, '2Comp')
        sp = tc['summary']['spearman_distribution']
        ok = sp['q025'] > 0
        verdict = ("**PASS** (95% CI strictly above 0)" if ok else
                    "**FAIL** (95% CI includes 0)")
        lines.append(
            f"- **{subject} {roi}**: median ρ = {sp['median']:+.3f}, "
            f"95% CI [{sp['q025']:+.3f}, {sp['q975']:+.3f}] → {verdict}"
        )
    lines.append("")

    # Q5 — paired sign test summary
    lines.append("### Q5 — 2-Comp vs R+C paired comparison (Wilcoxon)")
    lines.append("")
    for subject, roi in CELLS:
        ps = paired_all[(subject, roi)]
        verdict = "✓" if ps['wilcoxon_p_greater'] < 0.05 else "✗"
        lines.append(
            f"- **{subject} {roi}**: 2-Comp better in "
            f"{ps['n_2Comp_better_rho']}/{ps['n_subsets']} subsets, "
            f"median Δρ = {ps['median_diff_rho_2C_minus_RC']:+.3f}, "
            f"Wilcoxon (greater) p = {ps['wilcoxon_p_greater']:.4f} {verdict}"
        )
    lines.append("")

    # Boundary diagnostics (advisor flag)
    lines.append("## Boundary-hit diagnostics (2-Comp)")
    lines.append("")
    lines.append("Fraction of subsets whose 2-Comp grid optimum lands on the "
                  "[−50, +50] boundary (β_s or β_c). High rates indicate the "
                  "Spearman-best is being pushed beyond the search box and the "
                  "median/CI estimates are *clipped*. Treat with caution.")
    lines.append("")
    lines.append("| Cell | n | β_s boundary | β_c boundary |")
    lines.append("|---|---|---|---|")
    for subject, roi in CELLS:
        d = load_records(subject, roi, '2Comp')
        n = d['n_subsets']
        bbs = sum(1 for r in d['subsets'] if r['fit']['boundary_bs'])
        bbc = sum(1 for r in d['subsets'] if r['fit']['boundary_bc'])
        lines.append(
            f"| {subject} {roi} | {n} | {bbs}/{n} ({100*bbs/n:.0f}%) | "
            f"{bbc}/{n} ({100*bbc/n:.0f}%) |"
        )
    lines.append("")

    # Notes
    lines.append("## Implementation notes")
    lines.append("")
    lines.append("- C_baseline = `create_basis_full(K=6, 'fe')[HUE_ANGLES.astype(int)]` "
                  "(matches `s5_all_paths_fit.py` L4 convention).")
    lines.append("- 2-Comp grid: symmetric β_s ∈ [−50, +50] (51 pts), β_c ∈ [−50, +50] (51 pts), step 2°. "
                  "This is wider than the `two_comp.BS_GRID` (β_s ∈ [0, 50]) used elsewhere — "
                  "deliberate to let resampling reveal sign-reversed solutions.")
    lines.append("- R+C grid: g ∈ [0, 3] step 0.05 (61 pts), Δλ fixed at DPS lit "
                  "(sub-08=6 nm, sub-09=10 nm).")
    lines.append("- Spearman ρ: `scipy.stats.spearmanr` default (average ranks for ties). "
                  "Degenerate (constant) inputs handled by returning ρ=0.")
    lines.append("- Cosine: `np.dot(a,b) / (||a||·||b||)`, 0 if either vector is zero.")
    lines.append("- σ=21° not applicable here (L4 has no σ dependence — purely δθ-driven).")
    lines.append("")
    lines.append("## Files")
    lines.append("")
    lines.append("- Per-cell × model JSON: `{subject}_{ROI}_{RC|2Comp}.json`")
    lines.append("- Master summary: `master_summary.json`")
    lines.append("- This report: `SUBSET_REPORT.md`")
    lines.append("- Distribution figure: `viz_distribution.png`")

    out_path = RESULTS_DIR / 'SUBSET_REPORT.md'
    with open(out_path, 'w') as f:
        f.write('\n'.join(lines))
    print(f"Saved report: {out_path}")


def main():
    render_report()
    render_distribution_figure()


if __name__ == "__main__":
    main()
