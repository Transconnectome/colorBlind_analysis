"""S7 (C) revised — R+C vs 2-Comp δθ agreement (Spearman 대체).

Replaces Spearman ρ with magnitude-aware metrics:
  - Pearson r (linear magnitude correlation)
  - Lin's CCC (agreement with identity line, gold standard for method agreement)
  - MAE / RMSE in degrees
  - Linear regression: 2-Comp = a + b * R+C  (b=1 a=0 → perfect identity)
  - Bland-Altman: per-color (δθ_2C − δθ_RC) vs mean

Bland-Altman:
  - bias = mean(diff)
  - LoA = bias ± 1.96 * SD(diff)
  - per-color outlier flag if |diff − bias| > 1.96 SD

Output:
  - results/s7_convergence/rc_vs_2comp_agreement.json
  - results/s7_convergence/SUMMARY_agreement.md
  - results/s7_convergence/viz_bland_altman.png
"""

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
S5_DIR = ROOT / "results" / "s5_all_paths"
OUT_DIR = ROOT / "results" / "s7_convergence"
OUT_DIR.mkdir(parents=True, exist_ok=True)

COLOR_NAMES = ['red', 'orange', 'yellow', 'green', 'cyan', 'blue', 'purple', 'magenta']
HEX = ['#e02430', '#f08020', '#f0d020', '#40b048', '#30b0b0', '#3060d0', '#7040b0', '#c040a0']

CELLS = [
    ('sub-08', 'V1', 'deutan', 6),
    ('sub-08', 'V4', 'deutan', 6),
    ('sub-09', 'V1', 'protan', 10),
    ('sub-09', 'V4', 'protan', 10),
]


def lins_ccc(x, y):
    """Lin's Concordance Correlation Coefficient.

    CCC = 2 * cov(x,y) / (var_x + var_y + (mean_x - mean_y)^2)
    Range [-1, 1]. 1 = perfect agreement with identity line.
    """
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    mx, my = x.mean(), y.mean()
    vx = x.var(ddof=0)
    vy = y.var(ddof=0)
    sxy = np.mean((x - mx) * (y - my))
    return float(2 * sxy / (vx + vy + (mx - my) ** 2 + 1e-12))


def bootstrap_ccc(x, y, B=2000, rng=None):
    """Bootstrap CI for Lin's CCC via paired index resampling."""
    rng = rng or np.random.default_rng(42)
    n = len(x)
    vals = np.empty(B)
    for b in range(B):
        idx = rng.integers(0, n, n)
        vals[b] = lins_ccc(x[idx], y[idx])
    return float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))


def load_fits(sub, roi, dlam):
    with open(S5_DIR / f"{sub}_{roi}_sigma21.json") as f:
        d = json.load(f)
    rc = next(
        (f for f in d['fits']
         if f['model'] == 'R+C'
         and f['loss_target'] == 'L8_modality_5050'
         and abs(f.get('delta_lambda_nm', 0) - dlam) < 0.5),
        None,
    )
    tc = next(
        (f for f in d['fits']
         if f['model'] == '2-Comp'
         and f['loss_target'] == 'L8_modality_5050'),
        None,
    )
    return rc, tc


def analyze_cell(sub, roi, family, dlam):
    rc, tc = load_fits(sub, roi, dlam)
    d_rc = np.array(rc['delta_theta_at_best'])
    d_2c = np.array(tc['delta_theta_at_best'])

    pearson_r, pearson_p = stats.pearsonr(d_rc, d_2c)
    spearman_r, spearman_p = stats.spearmanr(d_rc, d_2c)
    ccc = lins_ccc(d_rc, d_2c)
    ccc_lo, ccc_hi = bootstrap_ccc(d_rc, d_2c)

    diff = d_2c - d_rc
    bias = float(diff.mean())
    sd_diff = float(diff.std(ddof=1))
    loa_lo = bias - 1.96 * sd_diff
    loa_hi = bias + 1.96 * sd_diff
    mae = float(np.mean(np.abs(diff)))
    rmse = float(np.sqrt(np.mean(diff ** 2)))

    # 2-Comp = a + b * R+C
    slope, intercept, _, _, _ = stats.linregress(d_rc, d_2c)
    cos = float(np.dot(d_rc, d_2c) / (np.linalg.norm(d_rc) * np.linalg.norm(d_2c) + 1e-12))

    # Identity-line test: H0 (a=0, b=1) jointly
    # Use SSR identity vs SSR fit, F-test (not exact for n=8 small but indicative)
    y_id = d_rc  # under identity: δθ_2C = δθ_RC
    ssr_id = float(np.sum((d_2c - y_id) ** 2))
    y_fit = intercept + slope * d_rc
    ssr_fit = float(np.sum((d_2c - y_fit) ** 2))

    return {
        'subject': sub, 'roi': roi, 'family': family,
        'g_RC': rc['g_best'], 'beta_s_2C': tc.get('beta_s_best'),
        'beta_c_2C': tc.get('beta_c_best'),
        'delta_theta_RC': d_rc.tolist(),
        'delta_theta_2C': d_2c.tolist(),
        'pearson_r': float(pearson_r), 'pearson_p': float(pearson_p),
        'spearman_r': float(spearman_r), 'spearman_p': float(spearman_p),
        'ccc': float(ccc), 'ccc_ci': [ccc_lo, ccc_hi],
        'cosine': cos,
        'mae_deg': mae, 'rmse_deg': rmse,
        'ba_bias_deg': bias, 'ba_sd_diff': sd_diff,
        'ba_loa_low': loa_lo, 'ba_loa_high': loa_hi,
        'regression_slope': float(slope),
        'regression_intercept': float(intercept),
        'ssr_identity': ssr_id, 'ssr_fit': ssr_fit,
    }


def write_summary(results, out_path):
    lines = []
    lines.append("# S7 (C) revised — R+C vs 2-Comp δθ agreement metrics\n")
    lines.append("**Replaces Spearman** (rank-only, n=8 inadequate) with magnitude-aware metrics. "
                 "Primary metric: **Lin's CCC** (concordance with identity line y=x).\n")
    lines.append("## CCC interpretation (Lin 1989)\n"
                 "- < 0.90 poor agreement\n"
                 "- 0.90–0.95 moderate\n"
                 "- 0.95–0.99 substantial\n"
                 "- ≥ 0.99 almost perfect\n\n")

    lines.append("## Main results table\n")
    lines.append("| cell | Pearson r | Spearman ρ | **CCC** | CCC 95% CI | cos | MAE (°) | RMSE (°) | slope | intercept |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for r in results:
        lines.append(
            f"| {r['subject']} {r['roi']} | "
            f"{r['pearson_r']:+.3f} | "
            f"{r['spearman_r']:+.3f} | "
            f"**{r['ccc']:+.3f}** | "
            f"[{r['ccc_ci'][0]:+.2f}, {r['ccc_ci'][1]:+.2f}] | "
            f"{r['cosine']:+.2f} | "
            f"{r['mae_deg']:.1f} | "
            f"{r['rmse_deg']:.1f} | "
            f"{r['regression_slope']:+.2f} | "
            f"{r['regression_intercept']:+.1f}° |"
        )
    lines.append("")

    lines.append("## Bland-Altman per cell\n")
    lines.append("| cell | bias (°) | SD(diff) | LoA low (°) | LoA high (°) |")
    lines.append("|---|---|---|---|---|")
    for r in results:
        lines.append(
            f"| {r['subject']} {r['roi']} | "
            f"{r['ba_bias_deg']:+.2f} | "
            f"{r['ba_sd_diff']:.2f} | "
            f"{r['ba_loa_low']:+.2f} | "
            f"{r['ba_loa_high']:+.2f} |"
        )
    lines.append("")

    lines.append("## Per-color residual diff = (δθ_2C − δθ_RC)\n")
    lines.append("| cell | " + " | ".join(COLOR_NAMES) + " |")
    lines.append("|---|" + "|".join(["---"] * 8) + "|")
    for r in results:
        diff = np.array(r['delta_theta_2C']) - np.array(r['delta_theta_RC'])
        lines.append(f"| {r['subject']} {r['roi']} | "
                     + " | ".join(f"{v:+.1f}" for v in diff)
                     + " |")
    lines.append("")

    lines.append("## Interpretation\n")
    lines.append("CCC threshold for paper-defensible 'two models = same distortion': ≥ 0.95.\n")

    for r in results:
        verdict = ("✅ substantial" if r['ccc'] >= 0.95 else
                   "✓ moderate" if r['ccc'] >= 0.90 else
                   "⚠ poor" if r['ccc'] >= 0.5 else
                   "✗ disagreement")
        lines.append(f"- **{r['subject']} {r['roi']}**: CCC={r['ccc']:+.3f} → {verdict}. "
                     f"Slope={r['regression_slope']:+.2f} (1.0=identity), "
                     f"bias={r['ba_bias_deg']:+.2f}°.")
    lines.append("")

    out_path.write_text("\n".join(lines))


def make_bland_altman_viz(results, out_path):
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    for ax, r in zip(axes.flat, results):
        d_rc = np.array(r['delta_theta_RC'])
        d_2c = np.array(r['delta_theta_2C'])
        mean = (d_rc + d_2c) / 2
        diff = d_2c - d_rc

        ax.axhline(r['ba_bias_deg'], color='blue', linestyle='--', linewidth=1.2,
                   label=f"bias={r['ba_bias_deg']:+.2f}°")
        ax.axhline(r['ba_loa_high'], color='red', linestyle=':', linewidth=1.0,
                   label=f"±1.96 SD = ±{1.96*r['ba_sd_diff']:.1f}°")
        ax.axhline(r['ba_loa_low'], color='red', linestyle=':', linewidth=1.0)
        ax.axhline(0, color='black', linewidth=0.5)
        ax.fill_between([-50, 50], r['ba_loa_low'], r['ba_loa_high'],
                         alpha=0.07, color='red')

        for i, (m, d, c) in enumerate(zip(mean, diff, HEX)):
            ax.scatter(m, d, color=c, s=110, edgecolors='black', linewidth=0.7, zorder=3)
            ax.annotate(COLOR_NAMES[i], (m, d), fontsize=7,
                         xytext=(4, 4), textcoords='offset points')

        ax.set_xlabel('Mean (δθ_RC + δθ_2C)/2  (°)')
        ax.set_ylabel('Diff (δθ_2C − δθ_RC)  (°)')
        ax.set_title(f"{r['subject']} {r['roi']}  CCC={r['ccc']:+.3f}  "
                     f"slope={r['regression_slope']:+.2f}",
                     fontsize=10)
        ax.legend(loc='upper right', fontsize=8)
        ax.grid(True, alpha=0.3)
        xlim = max(np.abs(mean).max() * 1.2, 50)
        ax.set_xlim(-xlim, xlim)
        ylim = max(np.abs(diff).max() * 1.3, 30)
        ax.set_ylim(-ylim, ylim)

    fig.suptitle("S7 (C) — Bland-Altman per-color (R+C vs 2-Comp δθ)",
                 fontsize=13, y=0.995)
    plt.tight_layout(rect=[0, 0, 1, 0.97])
    fig.savefig(out_path, dpi=140, bbox_inches='tight')


def main():
    results = []
    for sub, roi, family, dlam in CELLS:
        r = analyze_cell(sub, roi, family, dlam)
        results.append(r)
        print(f"{sub} {roi}: Pearson={r['pearson_r']:+.3f}  CCC={r['ccc']:+.3f}  "
              f"slope={r['regression_slope']:+.2f}  MAE={r['mae_deg']:.1f}°  "
              f"BA bias={r['ba_bias_deg']:+.2f}°")

    (OUT_DIR / "rc_vs_2comp_agreement.json").write_text(json.dumps(results, indent=2))
    write_summary(results, OUT_DIR / "SUMMARY_agreement.md")
    make_bland_altman_viz(results, OUT_DIR / "viz_bland_altman.png")
    print(f"\nSaved: {OUT_DIR}/{{rc_vs_2comp_agreement.json, SUMMARY_agreement.md, viz_bland_altman.png}}")


if __name__ == "__main__":
    main()
