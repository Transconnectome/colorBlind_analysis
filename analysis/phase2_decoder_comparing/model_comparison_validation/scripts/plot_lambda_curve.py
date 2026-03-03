#!/usr/bin/env python3
"""Plot λ-MAE curve from GP fixed-mode results.

Checks whether the λ-MAE relationship is monotonic or has a local minimum.

Usage:
    python plot_lambda_curve.py --results_dir results/FE_group_prior/loco_fixed
    python plot_lambda_curve.py --results_dir results/FE_group_prior/loco_fixed --save fig.png
"""
import argparse
import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

HC = [f"{i:02d}" for i in range(1, 8)]
CVD = [f"{i:02d}" for i in range(8, 11)]


def load_fixed_results(results_dir):
    """Load all gp_loco_fixed_sub-*.json files."""
    results_dir = Path(results_dir)
    data = {}
    for f in sorted(results_dir.glob("gp_loco_fixed_sub-*.json")):
        with open(f) as fh:
            d = json.load(fh)
        subj = f.stem.split("sub-")[1]
        data[subj] = d
    return data


def extract_lambda_mae(data):
    """Extract {roi: {subj: {lambda: mae}}} from fixed-mode results."""
    out = {}
    for subj, d in data.items():
        for roi, roi_data in d["results"].items():
            if roi not in out:
                out[roi] = {}
            subj_key = f"sub-{subj}"
            if subj_key not in roi_data:
                continue
            sr = roi_data[subj_key]
            baseline = sr["baseline"]
            curve = {"baseline": baseline}
            for key, val in sr.items():
                if key.startswith("lambda_"):
                    lam = float(key.replace("lambda_", ""))
                    curve[lam] = val["mean_mae"]
            out[roi][subj] = curve
    return out


def plot_curves(lambda_mae, save_path=None):
    rois = sorted(lambda_mae.keys())
    fig, axes = plt.subplots(1, len(rois), figsize=(5 * len(rois), 5), sharey=True)
    if len(rois) == 1:
        axes = [axes]

    for ax, roi in zip(axes, rois):
        hc_curves, cvd_curves = [], []

        for subj, curve in sorted(lambda_mae[roi].items()):
            lambdas = sorted([k for k in curve if k != "baseline"])
            maes = [curve[l] for l in lambdas]
            baseline = curve["baseline"]
            group = "HC" if subj in HC else "CVD"
            color = "steelblue" if group == "HC" else "crimson"
            alpha = 0.3

            ax.plot(lambdas, maes, color=color, alpha=alpha, linewidth=1)

            if group == "HC":
                hc_curves.append(maes)
            else:
                cvd_curves.append(maes)

        # Group means
        lambdas_ref = sorted([k for k in list(lambda_mae[roi].values())[0] if k != "baseline"])
        if hc_curves:
            hc_mean = np.mean(hc_curves, axis=0)
            ax.plot(lambdas_ref, hc_mean, color="steelblue", linewidth=2.5,
                    label=f"HC mean (n={len(hc_curves)})")
            min_idx = np.argmin(hc_mean)
            ax.axvline(lambdas_ref[min_idx], color="steelblue", linestyle="--",
                       alpha=0.5, linewidth=1)
            ax.annotate(f"λ*={lambdas_ref[min_idx]:.2f}\n{hc_mean[min_idx]:.1f}°",
                        (lambdas_ref[min_idx], hc_mean[min_idx]),
                        textcoords="offset points", xytext=(8, -15),
                        fontsize=8, color="steelblue")

        if cvd_curves:
            cvd_mean = np.mean(cvd_curves, axis=0)
            ax.plot(lambdas_ref, cvd_mean, color="crimson", linewidth=2.5,
                    label=f"CVD mean (n={len(cvd_curves)})")
            min_idx = np.argmin(cvd_mean)
            ax.axvline(lambdas_ref[min_idx], color="crimson", linestyle="--",
                       alpha=0.5, linewidth=1)
            ax.annotate(f"λ*={lambdas_ref[min_idx]:.2f}\n{cvd_mean[min_idx]:.1f}°",
                        (lambdas_ref[min_idx], cvd_mean[min_idx]),
                        textcoords="offset points", xytext=(8, -15),
                        fontsize=8, color="crimson")

        ax.axhline(90, color="gray", linestyle=":", alpha=0.5, label="chance (90°)")
        ax.set_title(roi, fontsize=14)
        ax.set_xlabel("λ  (0=group, 1=individual)")
        if ax == axes[0]:
            ax.set_ylabel("LOCO MAE (°)")
        ax.legend(fontsize=8, loc="upper left")
        ax.set_xlim(-0.02, 1.02)

    fig.suptitle("Group Prior λ–MAE Curve (LOCO, leakage-fixed)", fontsize=14, y=1.02)
    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"Saved to {save_path}")
    else:
        plt.show()

    # Print monotonicity analysis
    print("\n=== Monotonicity Analysis ===")
    for roi in rois:
        lambdas_ref = sorted([k for k in list(lambda_mae[roi].values())[0] if k != "baseline"])
        for group_name, subj_list in [("HC", HC), ("CVD", CVD)]:
            curves = []
            for subj, curve in lambda_mae[roi].items():
                if subj in subj_list:
                    curves.append([curve[l] for l in lambdas_ref])
            if not curves:
                continue
            mean_curve = np.mean(curves, axis=0)
            min_idx = int(np.argmin(mean_curve))
            is_monotonic = all(mean_curve[i] <= mean_curve[i + 1]
                               for i in range(len(mean_curve) - 1))
            trend = "monotonic ↗" if is_monotonic else f"local min at λ={lambdas_ref[min_idx]:.2f}"
            print(f"  {roi} {group_name}: λ*={lambdas_ref[min_idx]:.2f} "
                  f"({mean_curve[min_idx]:.1f}°) — {trend}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--results_dir", required=True)
    parser.add_argument("--save", default=None, help="Save path for figure")
    args = parser.parse_args()

    data = load_fixed_results(args.results_dir)
    if not data:
        print(f"No results found in {args.results_dir}")
        raise SystemExit(1)

    lambda_mae = extract_lambda_mae(data)
    plot_curves(lambda_mae, save_path=args.save)
