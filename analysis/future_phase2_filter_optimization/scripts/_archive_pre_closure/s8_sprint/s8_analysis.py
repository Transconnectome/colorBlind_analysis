"""S8 analysis: 5 selection criteria + inter-loss correlation.

Consumes: results/s8_loo_train_test/loo_results.json
Produces:
  - results/s8_loo_train_test/selection_metrics.json
  - results/s8_loo_train_test/inter_loss_correlation.json
  - results/s8_loo_train_test/SELECTION_REPORT.md
"""
import sys
import json
import numpy as np
from pathlib import Path
from itertools import combinations

SCRIPT_DIR = Path(__file__).resolve().parent
OUT_DIR = SCRIPT_DIR.parent / "results" / "s8_loo_train_test"

LOSSES = ['L_gamma', 'L_alpha', 'L_LOCO', 'L_RDM']
DL_SOURCES = {
    'deutan': ['DPS_lit', 'Boehm_mid', 'JND_Lamb'],
    'protan': ['DPS_lit', 'Boehm_low', 'JND_Lamb'],
}


def pearson(x, y):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    mask = np.isfinite(x) & np.isfinite(y)
    if mask.sum() < 3:
        return np.nan
    x = x[mask]; y = y[mask]
    if np.std(x) < 1e-9 or np.std(y) < 1e-9:
        return np.nan
    return float(np.corrcoef(x, y)[0, 1])


def extract_rc_g(fits, loss_name, dl_src):
    if fits is None or fits.get(loss_name) is None:
        return np.nan
    return float(fits[loss_name]['rc'][dl_src]['g_best'])


def extract_2c_norm(fits, loss_name):
    if fits is None or fits.get(loss_name) is None:
        return np.nan
    bs = fits[loss_name]['2comp']['beta_s_best']
    bc = fits[loss_name]['2comp']['beta_c_best']
    return float(np.sqrt(bs ** 2 + bc ** 2))


def extract_2c_bs_bc(fits, loss_name):
    if fits is None or fits.get(loss_name) is None:
        return (np.nan, np.nan)
    return (float(fits[loss_name]['2comp']['beta_s_best']),
            float(fits[loss_name]['2comp']['beta_c_best']))


def per_cell_metrics(cell_folds, family):
    """Compute (a)(b)(e) per (loss, model[, dl_src]) for one cell."""
    out = {'rc': {}, '2comp': {}}

    # ---- R+C: per Δλ source × per loss ----
    for dl_src in DL_SOURCES[family]:
        out['rc'][dl_src] = {}
        for loss_name in LOSSES:
            cvd_gs = []
            hc_gs = []
            for f in cell_folds:
                cvd_gs.append(extract_rc_g(f['cvd_fits'], loss_name, dl_src))
                hc_gs.append(extract_rc_g(f['hc_held_out_fits'], loss_name, dl_src))
            cvd_gs = np.array(cvd_gs)
            hc_gs = np.array(hc_gs)

            mask = np.isfinite(cvd_gs)
            if mask.sum() < 3:
                out['rc'][dl_src][loss_name] = None
                continue

            # (a) parameter SD across folds (CVD)
            sd_cvd = float(np.std(cvd_gs[mask], ddof=1)) if mask.sum() > 1 else np.nan
            # (b) separation rate: fraction folds where cvd_g > 95%ile of {hc_g[j] : j != i}
            sep = []
            for i in range(len(cvd_gs)):
                others = np.array([hc_gs[j] for j in range(len(hc_gs)) if j != i and np.isfinite(hc_gs[j])])
                if len(others) < 2 or not np.isfinite(cvd_gs[i]):
                    continue
                thr = np.percentile(others, 95)
                sep.append(1.0 if cvd_gs[i] > thr else 0.0)
            sep_rate = float(np.mean(sep)) if sep else np.nan
            # (e) train-test MSE for held-out HC
            hc_mask = np.isfinite(hc_gs)
            if hc_mask.sum() >= 2:
                hc_mean = float(np.mean(hc_gs[hc_mask]))
                tt_mse = float(np.mean((hc_gs[hc_mask] - hc_mean) ** 2))
            else:
                tt_mse = np.nan
                hc_mean = np.nan

            out['rc'][dl_src][loss_name] = {
                'cvd_g_per_fold': cvd_gs.tolist(),
                'hc_held_out_g_per_fold': hc_gs.tolist(),
                'cvd_g_mean': float(np.mean(cvd_gs[mask])),
                'cvd_g_sd': sd_cvd,                       # (a)
                'separation_rate': sep_rate,              # (b)
                'hc_held_out_mean': hc_mean,
                'train_test_mse': tt_mse,                 # (e)
            }

    # ---- 2-comp: per loss ----
    for loss_name in LOSSES:
        cvd_norms = []
        hc_norms = []
        cvd_bs = []; cvd_bc = []
        hc_bs = []; hc_bc = []
        for f in cell_folds:
            cvd_norms.append(extract_2c_norm(f['cvd_fits'], loss_name))
            hc_norms.append(extract_2c_norm(f['hc_held_out_fits'], loss_name))
            bs, bc = extract_2c_bs_bc(f['cvd_fits'], loss_name)
            cvd_bs.append(bs); cvd_bc.append(bc)
            bs_h, bc_h = extract_2c_bs_bc(f['hc_held_out_fits'], loss_name)
            hc_bs.append(bs_h); hc_bc.append(bc_h)
        cvd_norms = np.array(cvd_norms); hc_norms = np.array(hc_norms)
        cvd_bs = np.array(cvd_bs); cvd_bc = np.array(cvd_bc)
        hc_bs = np.array(hc_bs); hc_bc = np.array(hc_bc)

        mask = np.isfinite(cvd_norms)
        if mask.sum() < 3:
            out['2comp'][loss_name] = None
            continue

        sd_cvd = float(np.std(cvd_norms[mask], ddof=1)) if mask.sum() > 1 else np.nan
        sd_bs = float(np.std(cvd_bs[np.isfinite(cvd_bs)], ddof=1)) if np.isfinite(cvd_bs).sum() > 1 else np.nan
        sd_bc = float(np.std(cvd_bc[np.isfinite(cvd_bc)], ddof=1)) if np.isfinite(cvd_bc).sum() > 1 else np.nan

        sep = []
        for i in range(len(cvd_norms)):
            others = np.array([hc_norms[j] for j in range(len(hc_norms)) if j != i and np.isfinite(hc_norms[j])])
            if len(others) < 2 or not np.isfinite(cvd_norms[i]):
                continue
            thr = np.percentile(others, 95)
            sep.append(1.0 if cvd_norms[i] > thr else 0.0)
        sep_rate = float(np.mean(sep)) if sep else np.nan

        hc_mask = np.isfinite(hc_norms)
        if hc_mask.sum() >= 2:
            hc_mean = float(np.mean(hc_norms[hc_mask]))
            tt_mse = float(np.mean((hc_norms[hc_mask] - hc_mean) ** 2))
        else:
            tt_mse = np.nan
            hc_mean = np.nan

        out['2comp'][loss_name] = {
            'cvd_norm_per_fold': cvd_norms.tolist(),
            'cvd_bs_per_fold': cvd_bs.tolist(),
            'cvd_bc_per_fold': cvd_bc.tolist(),
            'hc_held_out_norm_per_fold': hc_norms.tolist(),
            'cvd_norm_mean': float(np.mean(cvd_norms[mask])),
            'cvd_norm_sd': sd_cvd,                # (a) norm
            'cvd_bs_sd': sd_bs,                   # (a) component
            'cvd_bc_sd': sd_bc,                   # (a) component
            'separation_rate': sep_rate,          # (b)
            'hc_held_out_mean_norm': hc_mean,
            'train_test_mse': tt_mse,             # (e)
        }

    return out


def per_cell_inter_loss_corr(cell_folds, family):
    """Inter-loss Pearson r matrix per (model[, dl_src])."""
    corr = {'rc': {}, '2comp': {}}

    for dl_src in DL_SOURCES[family]:
        vectors = {}
        for loss_name in LOSSES:
            vectors[loss_name] = [extract_rc_g(f['cvd_fits'], loss_name, dl_src)
                                  for f in cell_folds]
        mat = {}
        for l1, l2 in combinations(LOSSES, 2):
            r = pearson(vectors[l1], vectors[l2])
            mat[f"{l1}__{l2}"] = r
        corr['rc'][dl_src] = mat

    vectors = {}
    for loss_name in LOSSES:
        vectors[loss_name] = [extract_2c_norm(f['cvd_fits'], loss_name)
                              for f in cell_folds]
    mat = {}
    for l1, l2 in combinations(LOSSES, 2):
        mat[f"{l1}__{l2}"] = pearson(vectors[l1], vectors[l2])
    corr['2comp'] = mat

    return corr


def main():
    in_path = OUT_DIR / "loo_results.json"
    print(f"Loading {in_path}")
    with open(in_path) as f:
        d = json.load(f)

    metrics = {}
    corr = {}
    for subject, sd in d['results'].items():
        family = sd['family']
        metrics[subject] = {'family': family, 'rois': {}}
        corr[subject] = {'family': family, 'rois': {}}
        for roi, cell in sd['rois'].items():
            metrics[subject]['rois'][roi] = per_cell_metrics(cell['folds'], family)
            corr[subject]['rois'][roi] = per_cell_inter_loss_corr(cell['folds'], family)

    with open(OUT_DIR / "selection_metrics.json", 'w') as f:
        json.dump(metrics, f, indent=2, default=str)
    with open(OUT_DIR / "inter_loss_correlation.json", 'w') as f:
        json.dump(corr, f, indent=2, default=str)
    print(f"Saved: selection_metrics.json + inter_loss_correlation.json")

    # ---- Build markdown report ----
    lines = []
    lines.append("# S8 Selection Report — Model-Loss Pair LOO+Train-Test")
    lines.append("")
    lines.append("**Sprint date**: 2026-05-23. Phase 2 model-loss selection RE-OPENED.")
    lines.append("**Design**: 4 losses × 2 models × 4 ROIs × 2 CVD × 7 LOO HC folds.")
    lines.append("**Losses**: L_γ (JND), L_α (8AFC), L_LOCO (within-W voxel), L_RDM (HC-pool ΔRDM cos)")
    lines.append("")
    lines.append("## Metrics")
    lines.append("- (a) `cvd_param_sd`: parameter SD across 7 LOO folds (stability)")
    lines.append("- (b) `separation_rate`: fraction of folds CVD > 95th %ile of held-out HC")
    lines.append("- (e) `train_test_mse`: variance of held-out HC parameter across folds (generalization)")
    lines.append("- (d) inter-loss Pearson r: convergence between loss vectors over 7 folds")
    lines.append("")

    for subject in d['results']:
        family = d['results'][subject]['family']
        lines.append(f"## {subject} ({family})")
        lines.append("")
        for roi in d['results'][subject]['rois']:
            lines.append(f"### {roi}")
            lines.append("")
            # R+C table (DPS_lit only for compactness; full per Δλ in JSON)
            dl_src = 'DPS_lit'
            lines.append(f"#### R+C 1-DOF (Δλ = {dl_src})")
            lines.append("| Loss | mean g | SD (a) | sep rate (b) | HC mean | train-test MSE (e) |")
            lines.append("|---|---|---|---|---|---|")
            for ln in LOSSES:
                m = metrics[subject]['rois'][roi]['rc'][dl_src].get(ln)
                if m is None:
                    lines.append(f"| {ln} | – | – | – | – | – |")
                    continue
                lines.append(f"| {ln} | {m['cvd_g_mean']:.2f} | {m['cvd_g_sd']:.2f} | "
                             f"{m['separation_rate']:.2f} | {m['hc_held_out_mean']:.2f} | "
                             f"{m['train_test_mse']:.3f} |")
            lines.append("")
            # 2-comp table
            lines.append("#### 2-Component (β_s, β_c)")
            lines.append("| Loss | mean norm | norm SD (a) | β_s SD | β_c SD | sep rate (b) | HC mean | train-test MSE (e) |")
            lines.append("|---|---|---|---|---|---|---|---|")
            for ln in LOSSES:
                m = metrics[subject]['rois'][roi]['2comp'].get(ln)
                if m is None:
                    lines.append(f"| {ln} | – | – | – | – | – | – | – |")
                    continue
                lines.append(f"| {ln} | {m['cvd_norm_mean']:.1f} | {m['cvd_norm_sd']:.1f} | "
                             f"{m['cvd_bs_sd']:.1f} | {m['cvd_bc_sd']:.1f} | "
                             f"{m['separation_rate']:.2f} | {m['hc_held_out_mean_norm']:.1f} | "
                             f"{m['train_test_mse']:.2f} |")
            lines.append("")
            # Inter-loss correlation
            lines.append("#### Inter-loss Pearson r (R+C g, Δλ=DPS_lit)")
            c_rc = corr[subject]['rois'][roi]['rc'][dl_src]
            lines.append("| Pair | r |")
            lines.append("|---|---|")
            for k, v in c_rc.items():
                r_str = "nan" if (v is None or not np.isfinite(v)) else f"{v:.2f}"
                lines.append(f"| {k.replace('__', ' ↔ ')} | {r_str} |")
            lines.append("")
            lines.append("#### Inter-loss Pearson r (2-comp norm)")
            c_2c = corr[subject]['rois'][roi]['2comp']
            lines.append("| Pair | r |")
            lines.append("|---|---|")
            for k, v in c_2c.items():
                r_str = "nan" if (v is None or not np.isfinite(v)) else f"{v:.2f}"
                lines.append(f"| {k.replace('__', ' ↔ ')} | {r_str} |")
            lines.append("")
        lines.append("---")
        lines.append("")

    with open(OUT_DIR / "SELECTION_REPORT.md", 'w') as f:
        f.write("\n".join(lines))
    print(f"Saved: SELECTION_REPORT.md")


if __name__ == "__main__":
    main()
