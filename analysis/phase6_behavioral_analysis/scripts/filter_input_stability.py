#!/usr/bin/env python
"""
filter_input_stability.py — Stability of *filter-construction inputs* under run reduction.

The filter pipeline (Phase 2) takes the 8-color LOCO ρ profile as its primary input
and fits a 2-component (β_s, β_c) model + pre-image δθ. The question for the 2nd MRI
experiment is NOT whether the filter works (that's downstream validation), but whether
the *profile we'd use to build the filter* would be stable if collected with fewer runs.

For each (subject × ROI × n), comparing each C(6,n) subset's 8-color ρ profile
against the n=6 anchor profile:

  (1) per-color ρ SD across subsets       — how much each color's ρ jiggles
  (2) per-color |bias| vs n=6 anchor      — systematic deviation from full-data value
  (3) profile cosine similarity to anchor — direction (which colors are weighted how)
  (4) profile L2 distance to anchor       — magnitude (absolute scale)
  (5) profile correlation to anchor       — linear agreement (Pearson)

Output: run_count_validation/filter_input_stability.json
"""
from __future__ import annotations

import json
import sys
from itertools import combinations
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[3]
VALID_DIR = PROJECT_ROOT / "analysis" / "phase6_behavioral_analysis" / \
    "run_count_validation"

ROIS = ["V1", "V2", "V3", "V4"]
ALL_SUBJECTS = [f"{i:02d}" for i in range(1, 11)]
N_VALUES = [2, 3, 4, 5, 6]
N_COLORS = 8


def main():
    with open(VALID_DIR / "v1_saturation_loco.json") as f:
        sat = json.load(f)

    out = {"config": {"rois": ROIS, "subjects": ALL_SUBJECTS,
                       "n_values": N_VALUES,
                       "anchor": "n=6 single subset (full-data per-color profile)",
                       "metrics": ["per_color_sd_across_subsets",
                                    "per_color_abs_bias_vs_anchor",
                                    "profile_cosine_to_anchor",
                                    "profile_l2_to_anchor",
                                    "profile_pearson_to_anchor"],
                       "script": __file__},
           "per_roi": {}}

    for roi in ROIS:
        roi_out = {n: {} for n in N_VALUES}
        for subj in ALL_SUBJECTS:
            # Anchor = n=6 single subset's 8-color profile
            anchor = np.array(
                list(sat["per_roi"][roi]["6"][subj].values())[0]["rho_per_color"]
            )
            for n in N_VALUES:
                profiles = np.array(
                    [c["rho_per_color"] for c in
                     sat["per_roi"][roi][str(n)][subj].values()]
                )  # (S, 8)
                S = profiles.shape[0]

                # (1) Per-color SD across subsets
                per_color_sd = profiles.std(axis=0)            # (8,)

                # (2) Per-color |bias| vs anchor — mean across subsets
                per_color_bias = np.abs(profiles - anchor).mean(axis=0)  # (8,)

                # (3) Profile cosine similarity to anchor
                anchor_norm = np.linalg.norm(anchor)
                cosines = []
                for prof in profiles:
                    pn = np.linalg.norm(prof)
                    if pn < 1e-10 or anchor_norm < 1e-10:
                        cosines.append(float("nan"))
                    else:
                        cosines.append(float(np.dot(prof, anchor) / (pn * anchor_norm)))
                cosine_mean = float(np.nanmean(cosines))
                cosine_sd = float(np.nanstd(cosines))

                # (4) Profile L2 distance to anchor
                l2s = [float(np.linalg.norm(prof - anchor)) for prof in profiles]
                l2_mean = float(np.mean(l2s))
                l2_sd = float(np.std(l2s))

                # (5) Profile Pearson to anchor
                pearsons = []
                for prof in profiles:
                    if prof.std() < 1e-10 or anchor.std() < 1e-10:
                        pearsons.append(float("nan"))
                    else:
                        pearsons.append(float(np.corrcoef(prof, anchor)[0, 1]))
                pearson_mean = float(np.nanmean(pearsons))

                roi_out[n][subj] = {
                    "n_subsets": int(S),
                    "anchor_profile": anchor.tolist(),
                    "per_color_sd": per_color_sd.tolist(),
                    "per_color_abs_bias": per_color_bias.tolist(),
                    "profile_cosine_mean": cosine_mean,
                    "profile_cosine_sd": cosine_sd,
                    "profile_l2_mean": l2_mean,
                    "profile_l2_sd": l2_sd,
                    "profile_pearson_mean": pearson_mean,
                    "mean_per_color_sd": float(per_color_sd.mean()),
                    "mean_per_color_bias": float(per_color_bias.mean()),
                }
        out["per_roi"][roi] = roi_out

    out_path = VALID_DIR / "filter_input_stability.json"
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"Saved: {out_path}")

    # Print summary for primary target hV4
    print()
    print("=" * 90)
    print("hV4 (filter primary target) — profile stability vs n=6 anchor")
    print("=" * 90)
    for subj in ["08", "09", "10"]:
        print(f"\nsub-{subj}:")
        print(f"  n  | cos_to_anchor  | L2_to_anchor  | mean_color_SD  | mean_color_|bias|")
        print(f"  ---|----------------|---------------|----------------|------------------")
        for n in N_VALUES:
            d = out["per_roi"]["V4"][n][subj]
            print(f"  {n}  | "
                  f"{d['profile_cosine_mean']:+.3f}±{d['profile_cosine_sd']:.3f} | "
                  f"{d['profile_l2_mean']:.3f}±{d['profile_l2_sd']:.3f}  | "
                  f"{d['mean_per_color_sd']:.3f}          | "
                  f"{d['mean_per_color_bias']:.3f}")


if __name__ == "__main__":
    main()
