"""build_uncertainty_summary.py — Effective uncertainty on production argmins.

Synthesizes the redteam v6 PCA RDM verification results into a single
"production estimate ± effective uncertainty" deliverable for each of the
3 candidates.

Inputs (results/redteam/):
  - param_recovery_voxel_v6_pca_v2.json   (consistent synth_jnd, 420 fits)
  - param_recovery_voxel_v6_pca.json      (v1 — donor's real JND; comparison)
  - null_within_hc_loo_v6_pca.json        (B1=21, B2=420 fits)
  - null_label_permutation_v6_pca.json    (1000 perms × 3 cands = 3000 fits)
  - verdict_matrix_v6_pca_v2.json         (analyze_verification output)

The deliverable answers:

  "what can we claim about the production (β_s, β_c) point estimate?"

For each candidate, report
  - production argmin (point estimate)
  - B2-derived effective uncertainty (|bs|_med, |bc|_med at GT=(0,0))
  - v2 recovery bias_axis (corrected for synth bug)
  - Source C p-value (label permutation)
  - B1 specificity rank (real HC as fake CVD)

Outputs (results/redteam/):
  - uncertainty_summary.json
  - uncertainty_summary.md
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
REDTEAM_DIR = SCRIPT_DIR.parent / "results" / "redteam"

V1_REC = REDTEAM_DIR / "param_recovery_voxel_v6_pca.json"
V2_REC = REDTEAM_DIR / "param_recovery_voxel_v6_pca_v2.json"
LOO = REDTEAM_DIR / "null_within_hc_loo_v6_pca.json"
PERM = REDTEAM_DIR / "null_label_permutation_v6_pca.json"
VERDICT = REDTEAM_DIR / "verdict_matrix_v6_pca_v2.json"

OUT_JSON = REDTEAM_DIR / "uncertainty_summary.json"
OUT_MD = REDTEAM_DIR / "uncertainty_summary.md"

CANDIDATES = [
    {"id": "S08-stable",  "subject": "sub-08", "family": "deutan",
     "combo_label": "γALL|RDMV1|noLOCO",
     "prod_bs": 38.0, "prod_bc": -10.0},
    {"id": "S08-robust",  "subject": "sub-08", "family": "deutan",
     "combo_label": "γOY|RDMV2|noLOCO",
     "prod_bs":  6.0, "prod_bc": -42.0},
    {"id": "S09-primary", "subject": "sub-09", "family": "protan",
     "combo_label": "γALL|RDMV1|noLOCO",
     "prod_bs":  2.0, "prod_bc":  24.0},
]


def _load(p): return json.loads(p.read_text())


def _agg_cells(rec_data: dict, cand_id: str) -> dict:
    cells = [v for k, v in rec_data.get("cells", {}).items()
             if k.startswith(f"{cand_id}_mag1.0_") and v.get("n", 0) > 0]
    if not cells:
        return {"n_donors": 0}
    bbs = np.array([c["bias_bs"] for c in cells], dtype=float)
    bbc = np.array([c["bias_bc"] for c in cells], dtype=float)
    f10 = np.array([c["frac_within_10deg"] for c in cells], dtype=float)
    f5 = np.array([c["frac_within_5deg"] for c in cells], dtype=float)
    return {
        "n_donors": int(len(cells)),
        "bias_bs_median": float(np.median(bbs)),
        "bias_bc_median": float(np.median(bbc)),
        "bias_bs_iqr": float(np.percentile(bbs, 75) - np.percentile(bbs, 25)),
        "bias_bc_iqr": float(np.percentile(bbc, 75) - np.percentile(bbc, 25)),
        "abs_bias_bs_mean": float(np.mean(np.abs(bbs))),
        "abs_bias_bc_mean": float(np.mean(np.abs(bbc))),
        "f10_mean": float(np.mean(f10)),
        "f5_mean": float(np.mean(f5)),
    }


def _b2_uncertainty(loo_data: dict, cand_id: str) -> dict:
    """Effective uncertainty from B2 (synth GT=(0,0), n=140 per cand)."""
    cell = loo_data.get("cells", {}).get(cand_id, {})
    s = cell.get("B2_summary", {})
    bs = np.array(s.get("raw_beta_s", []), dtype=float)
    bc = np.array(s.get("raw_beta_c", []), dtype=float)
    if bs.size == 0:
        return {"n": 0}
    return {
        "n": int(bs.size),
        "abs_bs_median": float(np.median(np.abs(bs))),
        "abs_bs_iqr": float(np.percentile(np.abs(bs), 75) - np.percentile(np.abs(bs), 25)),
        "abs_bc_median": float(np.median(np.abs(bc))),
        "abs_bc_iqr": float(np.percentile(np.abs(bc), 75) - np.percentile(np.abs(bc), 25)),
        "bs_p95": float(np.percentile(np.abs(bs), 95)),
        "bc_p95": float(np.percentile(np.abs(bc), 95)),
        "frac_within_10deg_origin": float(np.mean(
            (np.abs(bs) < 10.0) & (np.abs(bc) < 10.0))),
    }


def _perm_p(perm_data: dict, verdict_data: dict, cand_id: str) -> dict:
    cell = perm_data.get("cells", {}).get(cand_id, {})
    s = cell.get("summary", {})
    v = verdict_data.get("per_candidate", {}).get(cand_id, {})
    sig = v.get("within_subject_sig", {})
    return {
        "p_perm": sig.get("p_perm"),
        "n_perm": sig.get("n_perm"),
        "real_loss": sig.get("real_loss"),
        "perm_loss_5pct": sig.get("perm_loss_5pct"),
    }


def _b1_specificity(verdict_data: dict, cand_id: str) -> dict:
    v = verdict_data.get("per_candidate", {}).get(cand_id, {})
    spec = v.get("specificity", {})
    return {
        "rank_distance": spec.get("rank_distance"),
        "n_HC_carriers": spec.get("n_HC_carriers"),
    }


def main() -> None:
    v1_rec = _load(V1_REC)
    v2_rec = _load(V2_REC)
    loo = _load(LOO)
    perm = _load(PERM)
    verdict = _load(VERDICT)

    out = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "deliverable": (
            "Effective uncertainty on production v6 PCA RDM 2-component argmin. "
            "B2-derived uncertainty is the load-bearing measure because it is "
            "free of synth-design contamination (synth voxels AND synth JND "
            "both at GT=(0,0) where donor's real JND is internally consistent)."
        ),
        "candidates": {},
    }

    for cand in CANDIDATES:
        cid = cand["id"]
        b2 = _b2_uncertainty(loo, cid)
        v2_agg = _agg_cells(v2_rec, cid)
        v1_agg = _agg_cells(v1_rec, cid)
        perm_p = _perm_p(perm, verdict, cid)
        b1_spec = _b1_specificity(verdict, cid)
        out["candidates"][cid] = {
            "production_argmin": [cand["prod_bs"], cand["prod_bc"]],
            "combo_label": cand["combo_label"],
            "subject": cand["subject"],
            "family": cand["family"],
            "effective_uncertainty_B2": b2,
            "recovery_v2_consistent_synth": v2_agg,
            "recovery_v1_donor_jnd": v1_agg,
            "label_perm_C": perm_p,
            "specificity_B1": b1_spec,
        }

    OUT_JSON.write_text(json.dumps(out, indent=2, default=str))
    print(f"Saved JSON: {OUT_JSON}")

    # Markdown
    lines = [
        "# Production argmin: effective uncertainty (v6 PCA RDM, redteam verification)",
        "",
        f"_Generated: {out['generated_at']}_",
        "",
        "## Bottom line",
        "",
        "The B2 synthesis (GT=(0,0) with donor's real JND — internally consistent "
        "at the zero point, no synth design contamination) places the v6 2-component "
        "composite's argmin **~20° away from origin in β_s and ~25° away in β_c, with "
        "f10°=0.00** across all 3 candidates (n=140 each). This is the load-bearing "
        "evidence that the v6 composite cannot localize zero from zero data.",
        "",
        "The v2 recovery (corrected synth_jnd) restores partial identifiability on the "
        "**extreme axis** of each candidate (β_c bias 30.9→4.7° for S08-robust; β_s "
        "bias 17→7.6° for S08-stable), but the modest axis remains noise-dominated. "
        "S09-primary (small GT (2,24)) sits below noise floor — synth fix even hurts "
        "slightly because the JND signal becomes another noise source rather than a "
        "constraint.",
        "",
        "Source C (label permutation, N=1000): production loss is **not** in the "
        "lower-tail of label-shuffled distribution for any candidate (p=0.17–0.87). "
        "The production fit is no better than what random label shuffling achieves.",
        "",
        "## Per-candidate summary",
        "",
        "| Candidate | Production argmin | B2 uncertainty (|bs|_med / |bc|_med at GT=0) | v2 mean f10° | Source C p_perm | B1 rank |",
        "|---|---|---|---|---|---|",
    ]
    for cid, cd in out["candidates"].items():
        b2 = cd["effective_uncertainty_B2"]
        v2a = cd["recovery_v2_consistent_synth"]
        pc = cd["label_perm_C"]
        bs1 = cd["specificity_B1"]
        prod = cd["production_argmin"]
        lines.append(
            f"| **{cid}** | ({prod[0]:+.0f}, {prod[1]:+.0f}) "
            f"| {b2.get('abs_bs_median', '—'):.0f}° / {b2.get('abs_bc_median', '—'):.0f}° "
            f"(IQR {b2.get('abs_bs_iqr', '—'):.0f} / {b2.get('abs_bc_iqr', '—'):.0f}) "
            f"| {v2a.get('f10_mean', float('nan')):.2f} "
            f"| {pc.get('p_perm', '—'):.3f} (n={pc.get('n_perm')}) "
            f"| {bs1.get('rank_distance', '—'):.3f} |"
        )

    lines.extend([
        "",
        "## Interpretation",
        "",
        "**What can be claimed**:",
        "- Production v6 argmin is a reproducible composite-minimum from the joint γ+RDM atom landscape",
        "- It is a low-dimensional descriptive embedding of CVD pattern features in a 2-coordinate space",
        "- For candidates with extreme parameter values on one axis (S08-robust β_c=-42; S08-stable β_s=38), that axis is partially identifiable above noise floor",
        "",
        "**What cannot be claimed**:",
        "- (β_s, β_c) as physiologically interpretable cone-shift / cortical-rotation magnitudes (any axis < ~20° is in noise floor)",
        "- Specificity vs HC null distribution (B1 rank 0.5–0.875)",
        "- Statistical significance vs label-shuffled null (p_perm 0.17–0.87, all > 0.05)",
        "",
        "**Effective claim form per candidate**:",
        "",
    ])
    for cid, cd in out["candidates"].items():
        b2 = cd["effective_uncertainty_B2"]
        prod = cd["production_argmin"]
        if not b2 or b2.get("n", 0) == 0:
            continue
        bs_unc = b2["abs_bs_median"]
        bc_unc = b2["abs_bc_median"]
        lines.append(
            f"- **{cid}**: v6 argmin places ({prod[0]:+.0f}°, {prod[1]:+.0f}°). "
            f"Effective uncertainty from B2: β_s ±{bs_unc:.0f}°, β_c ±{bc_unc:.0f}°. "
            f"Axes where |argmin| > 2 × B2 uncertainty (potential signal): "
            f"{'β_s ' if abs(prod[0]) > 2*bs_unc else ''}{'β_c' if abs(prod[1]) > 2*bc_unc else ''}"
            f"{'NONE' if abs(prod[0]) <= 2*bs_unc and abs(prod[1]) <= 2*bc_unc else ''}"
        )

    lines.extend([
        "",
        "## What the v1→v2 fix proved",
        "",
        "v1 used donor HC's REAL JND as the fake CVD JND, which is approximately at "
        "GT=0 behaviourally even when synth voxels were at GT≠0. This created a γ-atom "
        "pull toward δ=0 that compounded with the voxel-driven RDM atom signal toward "
        "δ=GT. v2 synthesizes JND consistent with GT via pool baseline × (d_phys/d_perc(GT)) "
        "+ N(0, pool_sd). The v2 vs v1 differences show:",
        "",
        "- **S08-robust β_c bias 30.9° → 4.7°** — pipeline can recover β_c near GT=-42° when synth is consistent",
        "- **S08-stable β_s bias 17.0° → 7.6°** — pipeline can recover β_s near GT=38° when synth is consistent",
        "- **S09-primary slightly worse in v2** — confirms small GT values (|GT|<20°) sit below noise floor; consistent JND adds noise without constraint",
        "",
        "The fix demonstrates that **identifiability is axis-asymmetric and SNR-thresholded**, "
        "not uniformly impossible. Production candidates straddle the threshold — extreme axes "
        "are identifiable, moderate axes are not.",
        "",
        "## Methodological notes",
        "",
        "- B2 effective uncertainty draws on n=140 realizations (7 donors × M=20 noise) per candidate at GT=(0,0).",
        "- v2 recovery uses n=140 realizations at GT=(prod_bs, prod_bc) with consistent synth_jnd.",
        "- Source C uses N=1000 label permutations with HC pool unchanged.",
        "- B1 uses real HC_k amplitudes as fake CVD (7 carriers; deterministic per candidate).",
        "- Verdict table separately at `verdict_matrix_v6_pca_v2.json` / `verdict_matrix_v2.md`.",
        "",
    ])
    OUT_MD.write_text("\n".join(lines))
    print(f"Saved MD:   {OUT_MD}")


if __name__ == "__main__":
    main()
