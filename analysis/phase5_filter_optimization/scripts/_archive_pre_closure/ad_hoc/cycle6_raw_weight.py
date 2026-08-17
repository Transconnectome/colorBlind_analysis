"""
Cycle 6 - (Raw-weight composite, no z-score)
============================================
Z-score atom-equalization 우회. Phase B v6 candidates 의 raw atom values
(test_agg_median = γ_all, test_V1_RDM_median = RDM cell atom) 추출 후
명시적 weight scheme 으로 composite 재계산 + ranking 변화 확인.

LOCO atom raw value 는 JSON 에 직접 저장 안 됨 (test_loss 에 folded).
따라서 raw composite 은 noLOCO combos 위주 (LOCO double-dipping 우회와 일치).

Weight schemes:
  A. γ_all only (=behavioral-only, raw scale 80~100)  ← Cycle 2 와 동일
  B. γ_all + 50·RDM (equal-magnitude, 50×scale ratio)
  C. γ_all + 200·RDM (RDM-dominant, 200×scale ratio)

Output: BEHAVIORAL_FIT_DIAGNOSIS 의 Cycle 6 섹션에 정리 + JSON dump.
"""
from __future__ import annotations
import json
from pathlib import Path

OUT_ROOT = Path(__file__).parent.parent
RESULTS = OUT_ROOT / "results" / "s10_inclusion"

WEIGHT_SCHEMES = {
    "A_γ_only": (1.0, 0.0),
    "B_γ+50RDM": (1.0, 50.0),
    "C_γ+200RDM": (1.0, 200.0),
}


def model_label(mn: str) -> str:
    if mn.startswith("rc_"):
        return f"R+C {mn[3:]}"
    return mn


def extract_rows(json_path: Path) -> list[dict]:
    with json_path.open() as f:
        d = json.load(f)
    summ = d["summary"]
    rows: list[dict] = []
    for cname, c in summ.items():
        # focus on noLOCO combos for raw scheme (LOCO raw missing, double-dipping concern)
        if "LOCO" in cname and "noLOCO" not in cname:
            continue
        for mn, mres in c.get("per_model", {}).items():
            agg = mres.get("test_agg_median", None)
            rdm = mres.get("test_V1_RDM_median", None)
            if agg is None or rdm is None:
                continue
            row = {
                "combo": cname,
                "model": mn,
                "agg": agg,  # γ_all raw
                "rdm": rdm,  # RDM atom raw (V1/V2/V1+V4 cell-specific stored under V1_RDM key)
                "bdy": mres.get("boundary_rate", None),
                "param_summary": mres.get("param_summary", {}),
            }
            rows.append(row)
    return rows


def compute_composite(rows: list[dict]) -> dict[str, list[dict]]:
    """Compute raw composite under each weight scheme, return ranked rows per scheme."""
    out: dict[str, list[dict]] = {}
    for scheme, (w_g, w_r) in WEIGHT_SCHEMES.items():
        scored = []
        for r in rows:
            score = w_g * r["agg"] + w_r * r["rdm"]
            scored.append({**r, "score": score, "scheme": scheme})
        scored.sort(key=lambda x: x["score"])
        out[scheme] = scored
    return out


def fmt_params(ps: dict) -> str:
    if "g_median" in ps:
        return f"g={ps['g_median']:.2f}"
    if "beta_s_median" in ps:
        return f"(βs={ps.get('beta_s_median', 0):.0f}, βc={ps.get('beta_c_median', 0):.0f})"
    return "-"


def main() -> None:
    for sid in ["sub-08", "sub-09"]:
        path = RESULTS / f"s10b_v6_pca_rdm_results_{sid}.json"
        rows = extract_rows(path)
        result = compute_composite(rows)

        print(f"\n========== {sid} — Cycle 6 raw-weight ranking ==========")
        for scheme, sorted_rows in result.items():
            print(f"\n  --- Scheme {scheme}  (w_γ, w_RDM) = {WEIGHT_SCHEMES[scheme]} ---")
            print(f"  {'rank':4s}  {'score':>10s}  {'γ_all':>8s}  {'RDM':>6s}  {'combo':22s}  {'model':14s}  {'params':22s}  bdy")
            for i, r in enumerate(sorted_rows[:8], 1):
                bdy = f"{r['bdy']*100:.0f}%" if r["bdy"] is not None else "-"
                print(
                    f"  {i:4d}  {r['score']:10.2f}  {r['agg']:8.1f}  {r['rdm']:6.3f}  "
                    f"{r['combo']:22s}  {model_label(r['model']):14s}  "
                    f"{fmt_params(r['param_summary']):22s}  {bdy}"
                )

        # JSON dump
        dump_path = RESULTS / f"cycle6_raw_weight_composite_{sid}.json"
        dump = {
            scheme: [{k: v for k, v in r.items() if k != "param_summary"} | {"params": r.get("param_summary", {})} for r in sorted_rows[:20]]
            for scheme, sorted_rows in result.items()
        }
        with dump_path.open("w") as f:
            json.dump(dump, f, indent=2, default=str)
        print(f"\n  → {dump_path.name}")


if __name__ == "__main__":
    main()
