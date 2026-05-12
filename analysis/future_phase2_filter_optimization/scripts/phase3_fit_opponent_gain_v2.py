"""phase3_fit_opponent_gain_v2.py — Path A: joint hue+chroma loss.

Fix v1's scale-invariance problem by matching FULL opponent VECTOR (rg, by)
between predicted (sub-08 perceives stimulus) and target (HC opponent at the
HC-equivalent angle of sub-08's verbal report).

Hue-only loss (v1) was atan2(rg, by) which is scale-invariant under (α·rg, α·by)
— hence 27 tied cells. Joint vector loss includes chroma magnitude → unique
(g_LM, g_S, Δλ).

Loss for each anchor (stim_angle, sub08_verbal):
    LMS_a = stockman(stim_angle) × Machado_shift(Δλ, deutan)
    rg, by = opponent(LMS_a)
    pred = (g_LM·rg, g_S·by)

    target_HC_angle = SUB08_TOKEN_TO_HC_ANGLE[sub08_verbal]
    LMS_HC = stockman(target_HC_angle)  # Δλ=0, normal cones
    target = opponent(LMS_HC)

    loss += ||pred - target||²

Outputs:
- results/phase3_candidates/opponent_gain_fit/fit_result_v2.json
- results/phase3_candidates/opponent_gain_fit/score_grid_v2.json
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
import numpy as np

_THIS_DIR = Path(__file__).resolve().parent
_PHASE2_DIR = _THIS_DIR.parent
sys.path.insert(0, str(_THIS_DIR))
sys.path.insert(0, str(_THIS_DIR / "forward_models"))

from forward_models.opponent_gain import forward_opponent_gain, pre_image_opponent_gain
from machado_simulator import (
    machado_mixed_fundamentals, _load_stockman_grid,
)
from stockman_cone_shift import (
    _compute_spectral_shift_lms, lab_to_xyz, lms_to_opponent,
)

OUTDIR = _PHASE2_DIR / "results" / "phase3_candidates" / "opponent_gain_fit"
OUTDIR.mkdir(parents=True, exist_ok=True)

CVD = "deutan"
L_STAR = 75.0
CHROMA = 40.0

TARGET_THETAS = np.array([0, 45, 90, 135, 180, 225, 270, 315], dtype=float)

HC_TARGETS = {
    0: "red", 45: "orange", 90: "yellow", 135: "green",
    180: "cyan", 225: "sky", 270: "blue", 315: "magenta",
}

# Sub-08 perception token → expected HC angle (where HC sees that color)
SUB08_TOKEN_TO_HC_ANGLE = {
    "pinkish_red": 350.0,
    "light_red": 5.0,
    "pure_red": 0.0,
    "darker_red": 10.0,
    "pink": 345.0,
    "pink_red": 350.0,
    "light_orange": 40.0,
    "lighter_orange": 42.0,
    "darker_orange": 45.0,
    "yellow": 90.0,
    "yellowgreen": 110.0,
    "light_yellowgreen": 105.0,
    "very_light_yellowgreen": 105.0,
    "warm_ivory": 85.0,
    "slight_green": 140.0,
    "green": 135.0,
    "sky": 230.0,
    "cyan": 195.0,
    "blue": 265.0,
    "darker_blue": 270.0,
    "darker_sky": 245.0,
    "very_deep_blue": 270.0,
    "deep_blue": 270.0,
    "lighter_blue": 255.0,
    "purple_pink": 325.0,
    "purple": 295.0,
    "magenta": 315.0,
}


# ---------------------------------------------------------------------------
# Perception map loader (same 39 anchors as v1)
# ---------------------------------------------------------------------------
def load_perception_map() -> list[tuple[float, str]]:
    path = OUTDIR.parent / "perception_map_v2.json"
    with open(path) as f:
        data = json.load(f)
    return [(float(d["theta"]), d["percept"]) for d in data]


# ---------------------------------------------------------------------------
# Opponent vector at angle θ under given Machado Δλ
# ---------------------------------------------------------------------------
def _opponent_vec(theta_cielab: float, delta_lambda: float,
                  cvd_type: str = "deutan") -> tuple[float, float]:
    """Return (rg, by) opponent at θ with Machado Δλ shift."""
    rad = np.deg2rad(float(theta_cielab))
    lab = np.array([[L_STAR, CHROMA * np.cos(rad), CHROMA * np.sin(rad)]])
    xyz = lab_to_xyz(lab)

    wl, L_n, M_n, S_n, _, _, M_xyz2lms = _load_stockman_grid()
    if cvd_type == "normal" or float(delta_lambda) == 0.0:
        L_a, M_a, S_a = L_n, M_n, S_n
    else:
        L_a, M_a, S_a = machado_mixed_fundamentals(
            float(delta_lambda), cvd_type, wl, L_n, M_n, S_n)

    lms = _compute_spectral_shift_lms(wl, L_a, M_a, S_a, M_xyz2lms, xyz)
    rg, by = lms_to_opponent(lms)
    return float(np.ravel(rg)[0]), float(np.ravel(by)[0])


# ---------------------------------------------------------------------------
# Joint vector loss over anchors
# ---------------------------------------------------------------------------
def joint_loss(delta_lambda: float, g_LM: float, g_S: float,
               anchors: list[tuple[float, str]]) -> float:
    total = 0.0
    n_used = 0
    for stim_angle, sub08_token in anchors:
        target_HC = SUB08_TOKEN_TO_HC_ANGLE.get(sub08_token)
        if target_HC is None:
            continue  # skip if token not mapped

        # Predicted opponent under (h)
        rg_m, by_m = _opponent_vec(stim_angle, delta_lambda, "deutan")
        pred_rg = g_LM * rg_m
        pred_by = g_S * by_m

        # Target opponent (HC normal cones at expected HC angle)
        tgt_rg, tgt_by = _opponent_vec(target_HC, 0.0, "deutan")

        # Joint vector L2 loss
        total += (pred_rg - tgt_rg) ** 2 + (pred_by - tgt_by) ** 2
        n_used += 1
    return float(total / max(n_used, 1))


# ---------------------------------------------------------------------------
# Grid search over (Δλ, g_LM, g_S)
# ---------------------------------------------------------------------------
DLAM_GRID = [0.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0]
GLM_GRID = np.round(np.arange(0.20, 1.55, 0.05), 3).tolist()
GS_GRID  = np.round(np.arange(0.50, 1.85, 0.05), 3).tolist()


def grid_search(anchors: list[tuple[float, str]]) -> dict:
    print(f"Grid: Δλ {len(DLAM_GRID)} × g_LM {len(GLM_GRID)} × g_S {len(GS_GRID)}"
          f" = {len(DLAM_GRID) * len(GLM_GRID) * len(GS_GRID)} cells")
    results = []
    best = {"loss": np.inf}
    for dl in DLAM_GRID:
        for glm in GLM_GRID:
            for gs in GS_GRID:
                L = joint_loss(dl, glm, gs, anchors)
                results.append({"dl": dl, "g_LM": glm, "g_S": gs, "loss": L})
                if L < best["loss"]:
                    best = {"loss": L, "dl": dl, "g_LM": glm, "g_S": gs}
        print(f"  Δλ={dl:>5.1f}  done")
    return {"best": best, "all": results}


# ---------------------------------------------------------------------------
# HC name function (from candidate analysis v2) for reporting
# ---------------------------------------------------------------------------
HC_NAME_BINS = [
    (-10, 12,  "red"), (12, 30, "red-orange"), (30, 60, "orange"),
    (60, 78, "yellow-orange"), (78, 108, "yellow"), (108, 130, "yellow-green"),
    (130, 168, "green"), (168, 195, "cyan"), (195, 235, "sky"),
    (235, 265, "blue"), (265, 295, "violet"), (295, 330, "magenta"),
    (330, 350, "pink"),
]

def hc_name(theta: float) -> str:
    t = theta % 360.0
    if t > 350: return "red"
    for (lo, hi, name) in HC_NAME_BINS:
        if lo <= t < hi:
            return name
    return "red"


SUB08_ORIGINAL_HC_EQUIV = {
    0: "pink", 45: "red", 90: "yellow-green", 135: "yellow",
    180: "yellow", 225: "sky", 270: "sky", 315: "blue",
}


def score_at(dl: float, glm: float, gs: float, anchors: list) -> dict:
    """Compute summary metrics for a (dl, glm, gs) cell."""
    # 8-color predictions
    rows = []
    for theta_t in TARGET_THETAS:
        theta_perc, dt = forward_opponent_gain(float(theta_t), CVD, dl, glm, gs)
        theta_pre, resid = pre_image_opponent_gain(float(theta_t), CVD, dl, glm, gs)
        rows.append({
            "color": f"c{int(theta_t/45)+1}",
            "theta": int(theta_t),
            "theta_perceived": round(float(theta_perc), 2),
            "dt": round(float(dt), 2),
            "col2_hc_name": hc_name(theta_perc),
            "sub08_hc_target": SUB08_ORIGINAL_HC_EQUIV.get(int(theta_t), "?"),
            "theta_pre": round(float(theta_pre), 2),
            "pre_residual": round(float(resid), 4),
            "col4_hc_name": HC_TARGETS[int(theta_t)],  # by inverse construction
        })
    # P2a: how many col2_hc_name match sub08_hc_target?
    p2a_exact = sum(1 for r in rows if r["col2_hc_name"] == r["sub08_hc_target"])
    return {"rows": rows, "p2a_exact": p2a_exact}


def main():
    anchors = load_perception_map()
    print(f"Loaded {len(anchors)} anchors")

    used = [(a, t) for (a, t) in anchors if t in SUB08_TOKEN_TO_HC_ANGLE]
    print(f"Anchors used (token mapped): {len(used)}/{len(anchors)}")

    res = grid_search(used)
    print(f"\nBest: Δλ={res['best']['dl']}, g_LM={res['best']['g_LM']}, "
          f"g_S={res['best']['g_S']}, loss={res['best']['loss']:.4f}")

    summary = score_at(res["best"]["dl"], res["best"]["g_LM"],
                       res["best"]["g_S"], used)
    print(f"\n8-color P2a (exact HC name match): {summary['p2a_exact']}/8")
    for r in summary["rows"]:
        print(f"  {r['color']:>3} θ={r['theta']:>3}  θ_p={r['theta_perceived']:>6.1f}  "
              f"col2={r['col2_hc_name']:<14}  target={r['sub08_hc_target']:<14}  "
              f"θ_pre={r['theta_pre']:>6.1f}")

    # Compare to v1 fit (g_LM=0.45, g_S=1.15, Δλ=14)
    v1_loss = joint_loss(14.0, 0.45, 1.15, used)
    v1_summary = score_at(14.0, 0.45, 1.15, used)
    print(f"\nv1 reference (Δλ=14, g_LM=0.45, g_S=1.15):")
    print(f"  joint_loss={v1_loss:.4f}, 8-color P2a={v1_summary['p2a_exact']}/8")

    # Canonical 2-comp reference (β_s=38, β_c=-14) — for comparison
    # We can't compute it here in same units, but report separately later

    out = {
        "method": "v2_joint_vector_loss",
        "subject": "sub-08", "cvd_type": CVD,
        "anchors_used": len(used),
        "best": res["best"],
        "summary_8color": summary["rows"],
        "p2a_exact_match": summary["p2a_exact"],
        "v1_reference": {
            "params": {"dl": 14.0, "g_LM": 0.45, "g_S": 1.15},
            "joint_loss": v1_loss,
            "p2a_exact": v1_summary["p2a_exact"],
        },
    }
    with open(OUTDIR / "fit_result_v2.json", "w") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    with open(OUTDIR / "score_grid_v2.json", "w") as f:
        json.dump({"grid": res["all"]}, f, indent=2)

    print(f"\nWrote {OUTDIR / 'fit_result_v2.json'}")


if __name__ == "__main__":
    main()
