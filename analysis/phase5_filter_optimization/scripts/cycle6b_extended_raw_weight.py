"""
Cycle 6b - (Extended raw-weight composite — γ_focal retained, γ_all + α·RDM swept)
==================================================================================
User directive 2026-05-26:
    "cycle6_raw_weight.py 확장. 다만 γ_focal은 제거하지 않고, 새로운 model candidate
     나타난다면 (γ_all + α·RDM) raw weight 재정리 시도"

Extension over cycle6_raw_weight.py:
  - γ_focal (test_focal_median) atom 포함 (cycle6 원본은 γ_all + RDM만)
  - α (RDM weight) sweep 확장: 0, 25, 50, 100, 200, 400
  - β (γ_focal weight) sweep: 0, 1, 2, 5 (focal 강조 정도)
  - Composite: w_focal · γ_focal + w_all · γ_all + α · RDM (raw, no z-score)
  - Pipeline 자체 (HC subset split, atom 계산, train/test) 재실행 불필요 — v6 JSON 그대로 활용
  - 새 후보 등장 여부 확인 (vs cycle6 원본 A/B/C 결과)

Output:
  - results/s10_inclusion/cycle6b_extended_composite_{sub-08,sub-09}.json
  - Stdout summary: scheme별 top-8 cells + new candidate identification
"""
from __future__ import annotations
import itertools
import json
from pathlib import Path

OUT_ROOT = Path(__file__).parent.parent
RESULTS = OUT_ROOT / "results" / "s10_inclusion"

# Weight grid: (w_focal, w_all, w_RDM)
# w_focal ∈ {0, 1, 2, 5}  — γ_focal strength
# w_all   ∈ {0, 1}        — γ_all on/off
# w_RDM   ∈ {0, 25, 50, 100, 200, 400} — RDM scale ratio
WEIGHT_GRID = [
    (wf, wa, wr)
    for wf, wa, wr in itertools.product([0, 1, 2, 5], [0, 1], [0, 25, 50, 100, 200, 400])
    if (wf, wa, wr) != (0, 0, 0)  # skip all-zero
]

# Reference schemes from cycle6 (for new-candidate comparison)
CYCLE6_BASELINE_SCHEMES = {
    "A_γall": (0, 1, 0),
    "B_γall+50RDM": (0, 1, 50),
    "C_γall+200RDM": (0, 1, 200),
}


def scheme_label(wf: int, wa: int, wr: int) -> str:
    parts = []
    if wf > 0:
        parts.append(f"{wf}γfocal")
    if wa > 0:
        parts.append(f"{wa}γall")
    if wr > 0:
        parts.append(f"{wr}RDM")
    return "+".join(parts) if parts else "ZERO"


def model_label(mn: str) -> str:
    if mn.startswith("rc_"):
        return f"R+C {mn[3:]}"
    return mn


def fmt_params(ps: dict) -> str:
    if "g_median" in ps:
        return f"g={ps['g_median']:.2f}"
    if "bs_median" in ps:
        return f"(βs={ps['bs_median']:.0f}, βc={ps['bc_median']:.0f})"
    if "beta_s_median" in ps:
        return f"(βs={ps.get('beta_s_median', 0):.0f}, βc={ps.get('beta_c_median', 0):.0f})"
    return "-"


def param_key(ps: dict) -> str:
    """Canonical key for de-duplicating same-parameter rows across cells."""
    if "g_median" in ps:
        return f"RC|g={ps['g_median']:.2f}"
    bs = ps.get("bs_median", ps.get("beta_s_median", None))
    bc = ps.get("bc_median", ps.get("beta_c_median", None))
    if bs is not None and bc is not None:
        return f"2C|bs={int(bs)},bc={int(bc)}"
    return "?"


def extract_rows(json_path: Path) -> list[dict]:
    """Extract per-cell × per-model rows with raw atom values.

    Includes BOTH LOCO and noLOCO cells (cycle6 원본은 noLOCO만; extension은 LOCO
    cells도 포함 단 LOCO atom raw 값이 없으므로 γ_focal/γ_all/RDM raw만 사용).
    """
    with json_path.open() as f:
        d = json.load(f)
    summ = d["summary"]
    rows: list[dict] = []
    for cname, c in summ.items():
        is_loco = ("LOCO" in cname) and ("noLOCO" not in cname)
        for mn, mres in c.get("per_model", {}).items():
            if mres is None:
                continue
            focal = mres.get("test_focal_median", None)
            agg = mres.get("test_agg_median", None)
            rdm = mres.get("test_V1_RDM_median", None)
            # require at least one raw atom value
            if focal is None and agg is None and rdm is None:
                continue
            rows.append({
                "combo": cname,
                "model": mn,
                "is_loco_cell": is_loco,
                "focal": focal,
                "agg": agg,
                "rdm": rdm,
                "bdy": mres.get("boundary_rate", None),
                "param_summary": mres.get("param_summary", {}),
                "param_key": param_key(mres.get("param_summary", {})),
                "train_loss_median": mres.get("train_loss_median", None),
                "test_loss_median": mres.get("test_loss_median", None),
                "test_loss_iqr": mres.get("test_loss_iqr", None),
            })
    return rows


def compute_score(r: dict, wf: int, wa: int, wr: int) -> float | None:
    """Raw weighted sum. Returns None if required atom missing."""
    score = 0.0
    if wf > 0:
        if r["focal"] is None:
            return None
        score += wf * r["focal"]
    if wa > 0:
        if r["agg"] is None:
            return None
        score += wa * r["agg"]
    if wr > 0:
        if r["rdm"] is None:
            return None
        score += wr * r["rdm"]
    return score


def is_collapse(train_loss, test_med, test_iqr):
    """Advisor 권고 collapse criterion."""
    if train_loss is None or test_med is None or test_iqr is None:
        return False
    if test_iqr > 50:
        return True
    if (train_loss < 0) != (test_med < 0) and abs(test_med - train_loss) > 5:
        return True
    return False


def top_rows_for_scheme(rows: list[dict], wf: int, wa: int, wr: int,
                        top_n: int = 10) -> list[dict]:
    scored = []
    for r in rows:
        s = compute_score(r, wf, wa, wr)
        if s is None:
            continue
        scored.append({**r, "score": s})
    scored.sort(key=lambda x: x["score"])
    return scored[:top_n]


def collect_unique_top_candidates(rows: list[dict], top_n_per_scheme: int = 5,
                                   bdy_max: float = 0.5,
                                   filter_collapse: bool = True) -> dict[str, dict]:
    """Across ALL weight schemes, collect every unique param-key that lands in top-N
    of at least one scheme. Returns {param_key: {model, params, schemes_top, ...}}.
    """
    unique: dict[str, dict] = {}
    for wf, wa, wr in WEIGHT_GRID:
        top = top_rows_for_scheme(rows, wf, wa, wr, top_n_per_scheme)
        for rank, r in enumerate(top, 1):
            # Filter degeneracy
            if r["bdy"] is not None and r["bdy"] >= bdy_max:
                continue
            if filter_collapse and is_collapse(r["train_loss_median"],
                                                r["test_loss_median"],
                                                r["test_loss_iqr"]):
                continue
            pk = r["param_key"]
            if pk not in unique:
                unique[pk] = {
                    "param_key": pk,
                    "model": r["model"],
                    "param_summary": r["param_summary"],
                    "schemes_top": [],
                    "best_score": r["score"],
                    "best_scheme": scheme_label(wf, wa, wr),
                    "best_combo": r["combo"],
                    "best_rank": rank,
                    "train_loss_median": r["train_loss_median"],
                    "test_loss_median": r["test_loss_median"],
                    "test_loss_iqr": r["test_loss_iqr"],
                    "focal": r["focal"], "agg": r["agg"], "rdm": r["rdm"],
                    "bdy": r["bdy"],
                }
            unique[pk]["schemes_top"].append({
                "scheme": scheme_label(wf, wa, wr),
                "weights": [wf, wa, wr],
                "combo": r["combo"],
                "rank": rank,
                "score": r["score"],
            })
            if r["score"] < unique[pk]["best_score"]:
                unique[pk]["best_score"] = r["score"]
                unique[pk]["best_scheme"] = scheme_label(wf, wa, wr)
                unique[pk]["best_combo"] = r["combo"]
                unique[pk]["best_rank"] = rank
    return unique


def cycle6_baseline_candidates(rows: list[dict], top_n: int = 8) -> set[str]:
    """Run cycle6 baseline schemes (A/B/C) and return the set of param_keys that
    appeared in their top-N. Used to identify NEW candidates introduced by
    the extended grid."""
    baseline_keys: set[str] = set()
    for scheme, (wf, wa, wr) in CYCLE6_BASELINE_SCHEMES.items():
        top = top_rows_for_scheme(rows, wf, wa, wr, top_n)
        for r in top:
            baseline_keys.add(r["param_key"])
    return baseline_keys


def main() -> None:
    summary = {}
    for sid in ["sub-08", "sub-09"]:
        path = RESULTS / f"s10b_v6_pca_rdm_results_{sid}.json"
        if not path.exists():
            print(f"  SKIP {sid}: {path} not found")
            continue
        rows = extract_rows(path)
        baseline_keys = cycle6_baseline_candidates(rows, top_n=8)
        unique = collect_unique_top_candidates(rows, top_n_per_scheme=5,
                                                 bdy_max=0.5,
                                                 filter_collapse=True)

        # Identify NEW candidates (in extended top but not in cycle6 baseline)
        new_keys = set(unique.keys()) - baseline_keys

        print(f"\n========== {sid} — Cycle 6b extended raw-weight ==========")
        print(f"  Total weight schemes evaluated: {len(WEIGHT_GRID)}")
        print(f"  Unique candidates surfacing in any scheme top-5 "
              f"(after bdy<50% + collapse filter): {len(unique)}")
        print(f"  Cycle6 baseline (A/B/C top-8) candidates: {len(baseline_keys)}")
        print(f"  NEW candidates (extended top but not in cycle6 baseline): {len(new_keys)}")

        # Print all unique candidates sorted by best_score
        print(f"\n  --- All unique candidates (across schemes) ---")
        for cand in sorted(unique.values(), key=lambda x: x["best_score"])[:15]:
            tag = "[NEW]" if cand["param_key"] in new_keys else "[base]"
            print(f"  {tag} {cand['param_key']:20s} | best_scheme={cand['best_scheme']:30s}  "
                  f"score={cand['best_score']:.2f} (rank {cand['best_rank']} in that scheme)")
            print(f"        train={cand['train_loss_median']:+.2f} "
                  f"test={cand['test_loss_median']:+.2f}±{cand['test_loss_iqr']:.2f}  "
                  f"focal={cand['focal']:.2f} agg={cand['agg']:.2f} rdm={cand['rdm']:.3f}  "
                  f"bdy={cand['bdy']*100:.0f}%")
            print(f"        appears top-5 in {len(cand['schemes_top'])} of "
                  f"{len(WEIGHT_GRID)} schemes")

        # Print specifically NEW candidates with extra detail
        if new_keys:
            print(f"\n  --- NEW candidates (not in cycle6 baseline) ---")
            for pk in sorted(new_keys, key=lambda k: unique[k]["best_score"]):
                cand = unique[pk]
                print(f"  {cand['param_key']:20s} {model_label(cand['model']):14s} "
                      f"{fmt_params(cand['param_summary']):24s}")
                print(f"     best scheme: {cand['best_scheme']} (rank {cand['best_rank']}) "
                      f"in combo {cand['best_combo']}")
                print(f"     test_med={cand['test_loss_median']:+.2f}±"
                      f"{cand['test_loss_iqr']:.2f}  bdy={cand['bdy']*100:.0f}%")
        else:
            print(f"\n  No NEW candidates — cycle6 baseline + extended grid agree.")

        # JSON dump
        out_path = RESULTS / f"cycle6b_extended_composite_{sid}.json"
        dump = {
            "subject": sid,
            "n_weight_schemes": len(WEIGHT_GRID),
            "weight_grid_spec": {
                "w_focal": [0, 1, 2, 5],
                "w_all": [0, 1],
                "w_RDM": [0, 25, 50, 100, 200, 400],
            },
            "filters": {"bdy_max": 0.5, "collapse_filter": True},
            "cycle6_baseline_keys": sorted(baseline_keys),
            "new_candidates_keys": sorted(new_keys),
            "unique_candidates": [
                {
                    "param_key": pk,
                    "model": c["model"],
                    "param_summary": c["param_summary"],
                    "is_new_vs_cycle6": pk in new_keys,
                    "best_scheme": c["best_scheme"],
                    "best_combo": c["best_combo"],
                    "best_rank": c["best_rank"],
                    "best_score": c["best_score"],
                    "schemes_top_count": len(c["schemes_top"]),
                    "train_loss_median": c["train_loss_median"],
                    "test_loss_median": c["test_loss_median"],
                    "test_loss_iqr": c["test_loss_iqr"],
                    "focal": c["focal"], "agg": c["agg"], "rdm": c["rdm"],
                    "boundary_rate": c["bdy"],
                    "schemes_top": c["schemes_top"],
                }
                for pk, c in sorted(unique.items(), key=lambda x: x[1]["best_score"])
            ],
        }
        with out_path.open("w") as f:
            json.dump(dump, f, indent=2, default=str)
        print(f"\n  → {out_path.name}")
        summary[sid] = {
            "n_unique": len(unique),
            "n_new": len(new_keys),
            "new_keys": sorted(new_keys),
        }

    print(f"\n========== Summary ==========")
    for sid, s in summary.items():
        print(f"  {sid}: {s['n_unique']} unique cand, {s['n_new']} NEW vs cycle6 baseline")
        if s["new_keys"]:
            print(f"    NEW: {s['new_keys']}")


if __name__ == "__main__":
    main()
