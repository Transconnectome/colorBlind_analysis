"""
s15 — OOS re-analysis of Phase B v6 candidates (DECISION_CRITERIA Layer A + E1)
=============================================================================
Per DECISION_CRITERIA_2026-05-26.md.

Layer A prerequisites:
  - P1 (fit/eval atom separation): enforced by atom-type bookkeeping
  - P2 (HC-subset robustness): rank-based, top 50% by |test_loss_iqr / test_loss_median|
    (user Q2 answer 2026-05-26)

Layer B evidence axis E1 (behavioral generalize, pair-level):
  - γ_focal cells (γYG, γOY, γYP, γGB, ...): Σ z² over non-focal pairs (held-out)
  - γALL cells: test_loss_median (user Q3: loss-robust ranking)
  - no-γ cells: Σ z² over all 8 pairs (none used in fit; full behavioral OOS)

No refit; pure re-analysis of existing v6 JSON.

Output: results/oos_reanalysis_v1/{sub-08,sub-09}_e1_p2.json + ranked CSVs
"""
from __future__ import annotations
import json
import math
import re
from pathlib import Path
from typing import Dict, List, Tuple

OUT_ROOT = Path(__file__).parent.parent
IN_DIR = OUT_ROOT / "results" / "s10_inclusion"
OUT_DIR = OUT_ROOT / "results" / "oos_reanalysis_v1"

PAIR_KEYS = [
    "red-orange",
    "orange-yellow",
    "yellow-green",
    "green-blue",
    "blue-purple",
    "yellow-purple",
    "cyan-magenta",
    "red-cyan",
]

GAMMA_PAIR_MAP = {
    "OY": "orange-yellow",
    "YG": "yellow-green",
    "YP": "yellow-purple",
    "GB": "green-blue",
}


def parse_combo_name(name: str) -> Dict:
    """Parse e.g. 'γOY|RDMV2|noLOCO' or 'γOY,YG,YP|RDMV2|noLOCO' or 'γALL|...' or 'γ_|RDM_|LOCO'."""
    parts = name.split("|")
    if len(parts) != 3:
        return {"gamma_pairs": [], "rdm_rois": [], "loco": False, "valid": False}

    gpart = parts[0].lstrip("γ")
    if gpart == "_":
        gamma_pairs: List[str] = []
        gamma_type = "none"
    elif gpart == "ALL":
        gamma_pairs = ["ALL"]
        gamma_type = "all"
    else:
        gamma_pairs = gpart.split(",")
        gamma_type = "focal"

    rdm_part = parts[1].lstrip("RDM")
    if rdm_part == "_":
        rdm_rois: List[str] = []
    else:
        rdm_rois = rdm_part.split("+")

    loco = parts[2] == "LOCO"

    return {
        "gamma_pairs": gamma_pairs,
        "gamma_type": gamma_type,
        "rdm_rois": rdm_rois,
        "loco": loco,
        "valid": True,
    }


def compute_e1(per_pair: Dict[str, float], parsed: Dict) -> Tuple[float, str]:
    """Return (E1_score, source_label) per spec."""
    if parsed["gamma_type"] == "focal":
        focal_pair_names = {GAMMA_PAIR_MAP[p] for p in parsed["gamma_pairs"] if p in GAMMA_PAIR_MAP}
        held_out = [p for p in PAIR_KEYS if p not in focal_pair_names]
        s = sum(per_pair.get(p, 0.0) for p in held_out)
        return s, f"non_focal_{len(held_out)}pairs"
    elif parsed["gamma_type"] == "none":
        s = sum(per_pair.get(p, 0.0) for p in PAIR_KEYS)
        return s, "all_8pairs_no_gamma_fit"
    elif parsed["gamma_type"] == "all":
        return float("nan"), "deferred_to_test_loss_median"
    else:
        return float("nan"), "unknown"


def compute_p2_sort_key(test_loss_iqr: float, test_loss_median: float, loco: bool) -> tuple:
    """
    User directive 2026-05-26:
      1. Primary: median (ascending, lower = better)
      2. Secondary: iqr (ascending, lower = better) — only for noLOCO cells
         LOCO cells: IQR=0 by construction (within-CVD, no HC pool variation) →
         use +inf as tiebreak so LOCO cells don't get fake stability advantage
    """
    if test_loss_median is None:
        med = float("inf")
    else:
        med = test_loss_median
    if loco:
        # LOCO cells: IQR irrelevant per user — push to tiebreak max
        return (med, float("inf"))
    if test_loss_iqr is None:
        return (med, float("inf"))
    return (med, test_loss_iqr)


def analyze_subject(sid: str) -> Dict:
    path = IN_DIR / f"s10b_v6_pca_rdm_results_{sid}.json"
    with path.open() as f:
        d = json.load(f)
    summary = d["summary"]

    rows: List[Dict] = []
    for combo_name, c in summary.items():
        parsed = parse_combo_name(combo_name)
        for model, mres in c.get("per_model", {}).items():
            per_pair = mres.get("test_per_pair_medians", {})
            test_loss_median = mres.get("test_loss_median", None)
            test_loss_iqr = mres.get("test_loss_iqr", None)
            param = mres.get("param_summary", {})

            e1, e1_source = compute_e1(per_pair, parsed) if per_pair else (float("nan"), "no_pair_data")
            p2_key = compute_p2_sort_key(test_loss_iqr, test_loss_median, parsed["loco"])

            if "g_median" in param:
                pstr = f"g={param['g_median']:.2f}"
                model_kind = "R+C"
            elif "bs_median" in param:
                pstr = f"βs={param['bs_median']:.0f},βc={param['bc_median']:.0f}"
                model_kind = "2-comp"
            else:
                pstr = "-"
                model_kind = "?"

            rows.append({
                "combo": combo_name,
                "model": model,
                "model_kind": model_kind,
                "gamma_type": parsed["gamma_type"],
                "rdm_rois": parsed["rdm_rois"],
                "loco": parsed["loco"],
                "params": pstr,
                "test_loss_median": test_loss_median,
                "test_loss_iqr": test_loss_iqr,
                "p2_sort_key": p2_key,
                "test_agg_median": mres.get("test_agg_median", None),
                "e1_score": e1,
                "e1_source": e1_source,
                "boundary_rate": mres.get("boundary_rate", None),
            })

    # P2 prerequisite: lexicographic sort by (median asc, IQR asc); LOCO IQR=+inf
    # top 50% pass
    rows_p2_sorted = sorted(rows, key=lambda r: r["p2_sort_key"])
    n_keep = max(1, len(rows_p2_sorted) // 2)
    p2_threshold_key = rows_p2_sorted[n_keep - 1]["p2_sort_key"] if rows_p2_sorted else (float("inf"), float("inf"))
    for i, r in enumerate(rows_p2_sorted):
        r["p2_rank"] = i + 1
        r["p2_pass"] = i < n_keep

    # E1 ranking within p2-pass set, split by gamma_type for proper comparison
    e1_focal = [r for r in rows_p2_sorted if r["p2_pass"] and r["gamma_type"] in ("focal", "none") and not math.isnan(r["e1_score"])]
    e1_all = [r for r in rows_p2_sorted if r["p2_pass"] and r["gamma_type"] == "all"]

    e1_focal_sorted = sorted(e1_focal, key=lambda r: r["e1_score"])  # lower = better
    e1_all_sorted = sorted(e1_all, key=lambda r: r["test_loss_median"] if r["test_loss_median"] is not None else float("inf"))

    for i, r in enumerate(e1_focal_sorted):
        r["e1_rank_focal"] = i + 1
    for i, r in enumerate(e1_all_sorted):
        r["e1_rank_all"] = i + 1

    return {
        "subject": sid,
        "n_candidates_total": len(rows),
        "p2_method": "lexicographic_median_iqr_LOCO_iqr_inf",
        "n_p2_pass": sum(1 for r in rows_p2_sorted if r["p2_pass"]),
        "all_rows_sorted_by_p2": rows_p2_sorted,
        "e1_focal_top_ranking": e1_focal_sorted,
        "e1_all_top_ranking": e1_all_sorted,
    }


def fmt_row(r: Dict, key: str = "e1") -> str:
    med = f"{r['test_loss_median']:+.3f}" if r['test_loss_median'] is not None else "—"
    iqr_v = r['test_loss_iqr']
    if r['loco']:
        iqr = "n/a"
    elif iqr_v is None:
        iqr = "—"
    else:
        iqr = f"{iqr_v:.2f}"
    bdy = f"{r['boundary_rate']*100:.0f}%" if r['boundary_rate'] is not None else "-"
    if key == "e1":
        e1v = f"{r['e1_score']:.2f}" if not math.isnan(r['e1_score']) else "—"
    else:
        e1v = med
    return (
        f"  {r['p2_rank']:>3d}  {r['combo']:24s}  {r['model_kind']:6s}  "
        f"{r['params']:20s}  med={med} iqr={iqr}  e1={e1v}  bdy={bdy}  fit={r['gamma_type']}|RDM={'+'.join(r['rdm_rois']) or '-'}|LOCO={r['loco']}"
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for sid in ["sub-08", "sub-09"]:
        res = analyze_subject(sid)
        out_path = OUT_DIR / f"{sid}_e1_p2.json"
        with out_path.open("w") as f:
            json.dump(res, f, indent=2, default=str)

        print(f"\n========== {sid} OOS Re-Analysis (P2 lexicographic median,iqr + E1) ==========")
        print(f"  Total candidates: {res['n_candidates_total']}")
        print(f"  P2 sort: (median asc, iqr asc) — LOCO cells use iqr=+inf (user 2026-05-26)")
        print(f"  P2 top 50% pass: {res['n_p2_pass']}")

        print(f"\n  --- E1 ranking (focal + no-γ candidates, lower = better generalization) ---")
        for r in res["e1_focal_top_ranking"][:12]:
            print(fmt_row(r, "e1"))

        if res["e1_all_top_ranking"]:
            print(f"\n  --- E1 (γALL candidates, by test_loss_median ascending) ---")
            for r in res["e1_all_top_ranking"][:10]:
                print(fmt_row(r, "loss"))

        print(f"\n  → {out_path}")


if __name__ == "__main__":
    main()
