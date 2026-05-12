"""phase3_candidate_analysis_v2.py — REVISED candidate evaluation.

Changes from v1:
1. P2a: HC color naming at θ_cvd vs sub-08 verbal's HC-equivalent target
   (was: circular perception-map lookup)
2. Collapse penalty: c5-c8 distinct sub-08 categories + pre-image span
3. c8 magenta anomaly: explicit flag — sub-08 perceives c8 at θ_cvd ≈ 270°
   but CURRENT 2-comp formula predicts θ_cvd ≈ 315-340°. Penalize when
   forward model places c8 in magenta family (HC name ∈ {magenta, pink, red}).

Outputs:
- results/phase3_candidates/candidates_summary_v2.json
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

from forward_models.two_component import forward_2comp, pre_image_2comp
from hc_specificity_check import load_hc_norms, hc_specificity_check

OUTDIR = _PHASE2_DIR / "results" / "phase3_candidates"
OUTDIR.mkdir(parents=True, exist_ok=True)

CVD = "deutan"
TARGET_THETAS = np.array([0, 45, 90, 135, 180, 225, 270, 315], dtype=float)

# ---------------------------------------------------------------------------
# HC color naming at any θ (STIM_LAB rendering)
# ---------------------------------------------------------------------------
# Bins derived from STIM_LAB ideal anchors (0,45,90,...,315) and the actual
# rendered appearance of intermediate angles. HC verbal vocabulary.
HC_NAME_BINS = [
    (-10, 12,  "red"),
    (12,  30,  "red-orange"),
    (30,  60,  "orange"),
    (60,  78,  "yellow-orange"),
    (78,  108, "yellow"),
    (108, 130, "yellow-green"),
    (130, 168, "green"),
    (168, 195, "cyan"),
    (195, 235, "sky"),
    (235, 265, "blue"),
    (265, 295, "violet"),
    (295, 330, "magenta"),
    (330, 350, "pink"),
]
HC_NAMES = sorted({b[2] for b in HC_NAME_BINS})

def hc_name(theta: float) -> str:
    t = theta % 360.0
    if t > 350: return "red"
    for (lo, hi, name) in HC_NAME_BINS:
        if lo <= t < hi:
            return name
    return "red"

# HC family (broader) for collapse counting
HC_FAMILY = {
    "red": "red", "red-orange": "red", "pink": "red",
    "orange": "orange", "yellow-orange": "orange",
    "yellow": "yellow",
    "yellow-green": "green", "green": "green",
    "cyan": "cyan",
    "sky": "blue", "blue": "blue", "violet": "blue",  # collapse axis
    "magenta": "magenta",
}

# Adjacency partial credit
HC_ADJ = {
    "red":         {"pink": 0.8, "red-orange": 0.6, "magenta": 0.4},
    "pink":        {"red": 0.8, "magenta": 0.5},
    "red-orange":  {"red": 0.6, "orange": 0.7},
    "orange":      {"red-orange": 0.7, "yellow-orange": 0.7, "red": 0.3},
    "yellow-orange":{"orange": 0.7, "yellow": 0.7},
    "yellow":      {"yellow-orange": 0.6, "yellow-green": 0.5},
    "yellow-green":{"yellow": 0.5, "green": 0.6},
    "green":       {"yellow-green": 0.6, "cyan": 0.3},
    "cyan":        {"green": 0.3, "sky": 0.7},
    "sky":         {"cyan": 0.7, "blue": 0.6},
    "blue":        {"sky": 0.6, "violet": 0.5},
    "violet":      {"blue": 0.5, "magenta": 0.5},
    "magenta":     {"violet": 0.5, "red": 0.4, "pink": 0.5},
}

def hc_match_score(predicted_name: str, target_name: str) -> float:
    if predicted_name == target_name:
        return 1.0
    return HC_ADJ.get(predicted_name, {}).get(target_name, 0.0)

# ---------------------------------------------------------------------------
# Sub-08 original verbal → HC equivalent name (for P2a comparison)
# ---------------------------------------------------------------------------
# What HC color name does sub-08's verbal correspond to?
# This is the canonical sub-08 deutan distortion pattern.
SUB08_ORIGINAL_HC_EQUIV = {
    0:   "pink",         # "빨강에 분홍 섞인" — pink-red, between red and magenta
    45:  "red",          # "연한 빨강" — deutan signature: orange seen as red
    90:  "yellow-green", # "연두"
    135: "yellow",       # "노랑" — deutan signature: green seen as yellow
    180: "yellow",       # "웜톤 아이보리" — desaturated, closest to warm yellow family
    225: "sky",          # "하늘"
    270: "sky",          # "더 진한 하늘" — sub-08 sees blue as darker sky
    315: "blue",         # "진파랑" — sub-08 sees magenta as deep blue
}

# HC target color (what filter should produce in col4)
HC_TARGETS = {
    0: "red", 45: "orange", 90: "yellow", 135: "green",
    180: "cyan", 225: "sky", 270: "blue", 315: "magenta",
}

# ---------------------------------------------------------------------------
# Perception map (for P1/P2b — what does sub-08 SEE at a given θ stimulus?)
# Same as v1, used to predict col4 outcome.
# ---------------------------------------------------------------------------
SUB08_ORIGINAL = {
    0:   "pinkish_red", 45:  "light_red", 90:  "yellowgreen",
    135: "yellow", 180: "warm_ivory", 225: "sky",
    270: "darker_sky", 315: "deep_blue",
}
CANONICAL_REPORTS = {1:"pure_red",2:"slight_green",3:"yellow",4:"yellow",
                     5:"sky",6:"sky",7:"darker_blue",8:"deep_blue"}
V4ONLY_OLD_REPORTS = {1:None,2:"darker_red",3:"light_orange",4:"light_yellowgreen",
                     5:"very_light_yellowgreen",6:"darker_sky",7:"very_deep_blue",
                     8:"purple_pink"}
CYCLE14_REPORTS = {1:"pink",2:"lighter_orange",3:"yellow",4:"warm_ivory",
                   5:"sky",6:"darker_sky",7:"sky",8:"blue"}
CYCLE12_REPORTS = {1:"pink_red",2:"lighter_orange",3:"yellow",4:"warm_ivory",
                   5:"sky",6:"sky",7:"sky",8:"lighter_blue"}

# Each sub-08 verbal token mapped to HC name (for predict-col4 evaluation)
PERCEPT_TO_HC_NAME = {
    "pinkish_red": "pink", "light_red": "red", "pure_red": "red",
    "darker_red": "red", "pink": "pink", "pink_red": "red",
    "light_orange": "orange", "lighter_orange": "orange",
    "yellow": "yellow", "yellowgreen": "yellow-green",
    "light_yellowgreen": "yellow-green", "very_light_yellowgreen": "yellow-green",
    "warm_ivory": "yellow", "slight_green": "green",
    "sky": "sky", "cyan": "cyan", "blue": "blue", "darker_blue": "blue",
    "darker_sky": "sky", "very_deep_blue": "blue", "deep_blue": "blue",
    "lighter_blue": "blue", "purple_pink": "magenta", "purple": "violet",
    "magenta": "magenta",
}

# ---------------------------------------------------------------------------
# OLD CIELab-direct formula for V4-only primary.png anchors
# ---------------------------------------------------------------------------
THETA_CONF_CIELAB_DEUTAN = 150.0
def dt_old(theta, beta_s, beta_c):
    return (beta_s * np.cos(np.radians(theta - 90.0))
            + beta_c * np.cos(np.radians(theta - THETA_CONF_CIELAB_DEUTAN)))
def pre_image_old(target, beta_s, beta_c, n_grid=1440):
    grid = np.linspace(0, 360, n_grid, endpoint=False)
    def res(t):
        f = (t + dt_old(t, beta_s, beta_c)) % 360
        return ((f - target + 180) % 360) - 180
    r = np.array([res(t) for t in grid])
    i = int(np.argmin(np.abs(r)))
    return float(grid[i]), float(r[i])

def build_perception_map() -> list[tuple[float, str]]:
    pmap = [(float(t), SUB08_ORIGINAL[int(t)]) for t in TARGET_THETAS]
    for i, t in enumerate(TARGET_THETAS, 1):
        p, _ = pre_image_2comp(t, CVD, 38.0, -14.0); pmap.append((p, CANONICAL_REPORTS[i]))
    for i, t in enumerate(TARGET_THETAS, 1):
        if V4ONLY_OLD_REPORTS[i] is None: continue
        p, _ = pre_image_old(t, 38.0, 7.0); pmap.append((p, V4ONLY_OLD_REPORTS[i]))
    for i, t in enumerate(TARGET_THETAS, 1):
        p, _ = pre_image_2comp(t, CVD, 58.0, -36.0); pmap.append((p, CYCLE14_REPORTS[i]))
    # NEW: Cycle12 (β_s=68, β_c=-38) — user added behavioral report
    for i, t in enumerate(TARGET_THETAS, 1):
        p, _ = pre_image_2comp(t, CVD, 68.0, -38.0); pmap.append((p, CYCLE12_REPORTS[i]))
    return pmap

def predict_subj08_percept(theta: float, pmap: list, k: int = 3) -> str:
    angles = np.array([p[0] for p in pmap])
    diffs = np.abs(((angles - theta) + 180.0) % 360.0 - 180.0)
    idx = np.argsort(diffs)[:k]
    votes = {}
    for i in idx:
        w = 1.0 / max(diffs[i], 1.0)
        votes[pmap[i][1]] = votes.get(pmap[i][1], 0) + w
    return max(votes.items(), key=lambda x: x[1])[0]

# ---------------------------------------------------------------------------
# Scoring (revised)
# ---------------------------------------------------------------------------
def score_candidate(beta_s: float, beta_c: float, pmap: list,
                    hc_norms: list[float]) -> dict:
    rows = []
    pre_angles = []
    col4_hc_predictions = []  # for collapse check

    for i, theta_t in enumerate(TARGET_THETAS, 1):
        theta_pre, _ = pre_image_2comp(theta_t, CVD, beta_s, beta_c)
        theta_cvd, dt = forward_2comp(theta_t, CVD, beta_s, beta_c)
        pre_angles.append(theta_pre)

        # ── REVISED P2a ──
        # HC name at θ_cvd (what HC sees in col2) vs sub-08's HC-equivalent verbal
        col2_hc_name = hc_name(theta_cvd)
        sub08_hc_target = SUB08_ORIGINAL_HC_EQUIV[int(theta_t)]
        p2a = hc_match_score(col2_hc_name, sub08_hc_target)

        # ── c8 magenta anomaly flag ──
        c8_anomaly = (i == 8 and col2_hc_name in {"magenta", "pink", "red"})

        # ── P1 / P2b (unchanged: sub-08 perception at θ_pre vs HC target) ──
        col4_subj_percept = predict_subj08_percept(theta_pre, pmap)
        col4_hc_name = PERCEPT_TO_HC_NAME.get(col4_subj_percept, "unknown")
        col4_hc_predictions.append(col4_hc_name)

        target = HC_TARGETS[int(theta_t)]
        p1 = hc_match_score(col4_hc_name, target)
        p2b = 1.0 if col4_hc_name == target else 0.0

        rows.append({
            "color": f"c{i}", "theta": int(theta_t),
            "theta_pre": round(theta_pre, 1),
            "theta_cvd": round(theta_cvd, 1), "dt": round(dt, 1),
            "col2_hc": col2_hc_name, "sub08_hc_target": sub08_hc_target,
            "p2a": p2a, "c8_anomaly": c8_anomaly,
            "col4_subj": col4_subj_percept, "col4_hc": col4_hc_name,
            "target": target, "p1": p1, "p2b": p2b,
        })

    # ── Collapse penalty for c5-c8 ──
    c5_to_c8 = pre_angles[4:8]
    span = max(c5_to_c8) - min(c5_to_c8)
    # adjacent gaps (after sorting)
    sorted_pre = sorted(c5_to_c8)
    gaps = [sorted_pre[i+1] - sorted_pre[i] for i in range(3)]
    min_gap = min(gaps)

    # HC family duplicates in c5-c8 col4 predictions
    c5c8_families = [HC_FAMILY.get(h, h) for h in col4_hc_predictions[4:8]]
    n_unique_families = len(set(c5c8_families))

    # Penalty: 0 if span≥60° and 4 unique families; up to -2.0 for severe collapse
    collapse_penalty = 0.0
    if span < 60: collapse_penalty -= (60 - span) / 30.0
    if min_gap < 12: collapse_penalty -= (12 - min_gap) / 8.0
    if n_unique_families < 4: collapse_penalty -= (4 - n_unique_families) * 0.5

    # c8 anomaly penalty
    c8_anomaly_penalty = -0.5 if rows[7]["c8_anomaly"] else 0.0

    p2a_total = sum(r["p2a"] for r in rows)
    p1_total = sum(r["p1"] for r in rows)
    p2b_total = sum(r["p2b"] for r in rows)

    spec = hc_specificity_check(beta_s, beta_c, hc_norms, n_boot=10000)

    return {
        "beta_s": beta_s, "beta_c": beta_c,
        "norm": spec["cvd_norm"], "boot_frac": spec["boot_frac"],
        "verdict": spec["verdict"],
        "p2a": round(p2a_total, 2),
        "p1": round(p1_total, 2),
        "p2b": round(p2b_total, 2),
        "c5c8_span": round(span, 1),
        "c5c8_min_gap": round(min_gap, 1),
        "c5c8_unique_families": n_unique_families,
        "collapse_penalty": round(collapse_penalty, 2),
        "c8_anomaly_penalty": c8_anomaly_penalty,
        "rows": rows,
    }


CANDIDATES = [
    {"name": "Canonical", "beta_s": 38.0, "beta_c": -14.0, "source": "phase_a L_LOCO (PASS §3)"},
    {"name": "V4-only_CURRENT", "beta_s": 38.0, "beta_c": 7.0, "source": "cycle10d z_combined"},
    {"name": "Cycle14", "beta_s": 58.0, "beta_c": -36.0, "source": "mw_jaccard/cycle14"},
    {"name": "l_rank", "beta_s": 74.0, "beta_c": -60.0, "source": "l_rank/spearman_r"},
    {"name": "l_dir", "beta_s": 78.0, "beta_c": -60.0, "source": "l_dir/pearson_r"},
    {"name": "norm_resid", "beta_s": 76.0, "beta_c": -60.0, "source": "norm_resid"},
    {"name": "l_mag", "beta_s": 44.0, "beta_c": 58.0, "source": "l_mag"},
    {"name": "sign_agree", "beta_s": 10.0, "beta_c": 58.0, "source": "sign_agree"},
    {"name": "phase_a_V1", "beta_s": 50.0, "beta_c": -14.0, "source": "phase_a V1 canonical"},
    {"name": "cycle12_xroi", "beta_s": 68.0, "beta_c": -38.0, "source": "cycle12 V4+V1 cross-ROI"},
    {"name": "cycle15_opt3", "beta_s": 58.0, "beta_c": -28.0, "source": "cycle15 mw_jaccard×2"},
    {"name": "cycle15_opt4", "beta_s": 70.0, "beta_c": -52.0, "source": "cycle15 mw_jaccard+spearman"},
    {"name": "scaled_canonical", "beta_s": 50.0, "beta_c": -20.0, "source": "Canonical ×1.32"},
    {"name": "mid_canonical_cycle14", "beta_s": 48.0, "beta_c": -25.0, "source": "midpoint"},
    # NEW exploratory candidates that emphasize different trade-offs
    {"name": "soft_canonical", "beta_s": 42.0, "beta_c": -16.0, "source": "Canonical ×1.1 (gentle)"},
    {"name": "wide_canonical", "beta_s": 36.0, "beta_c": -22.0, "source": "more confusion, less S"},
    {"name": "S_dominant", "beta_s": 56.0, "beta_c": -14.0, "source": "boost β_s only"},
]


def main():
    print("Loading HC norms..."); hc_norms = load_hc_norms("V4")
    print(f"  V4 norms: {[round(n,1) for n in hc_norms]}")

    print("\nBuilding perception map...")
    pmap = build_perception_map()
    print(f"  {len(pmap)} (angle, percept) anchors (incl. Cycle12)")
    with open(OUTDIR / "perception_map_v2.json", "w") as f:
        json.dump([{"theta": round(a,2), "percept": p} for (a,p) in pmap],
                  f, indent=2, ensure_ascii=False)

    print(f"\nScoring {len(CANDIDATES)} candidates (REVISED methodology)...\n")
    print(f"{'Name':<22} {'b_s':>5} {'b_c':>6} {'P2a':>5} {'P1':>5} {'P2b':>5} "
          f"{'span':>5} {'gap':>4} {'fam':>3} {'pen':>6} {'c8!':>4} {'norm':>5} {'spec':>4}")
    print("-" * 110)
    results = []
    for cand in CANDIDATES:
        r = score_candidate(cand["beta_s"], cand["beta_c"], pmap, hc_norms)
        r["name"] = cand["name"]; r["source"] = cand["source"]
        results.append(r)
        c8a = "Y" if r["rows"][7]["c8_anomaly"] else "-"
        print(f"{cand['name']:<22} {cand['beta_s']:>5.0f} {cand['beta_c']:>+6.0f} "
              f"{r['p2a']:>5.2f} {r['p1']:>5.2f} {r['p2b']:>5.2f} "
              f"{r['c5c8_span']:>5.1f} {r['c5c8_min_gap']:>4.1f} {r['c5c8_unique_families']:>3} "
              f"{r['collapse_penalty']:>6.2f} {c8a:>4} {r['norm']:>5.1f} {r['verdict']:>4}")

    # Aggregate: P2a/P1/P2b out of 8 each, normalized; collapse penalty; spec bonus
    for r in results:
        base = 0.3 * r["p2a"]/8 + 0.30 * r["p1"]/8 + 0.30 * r["p2b"]/8
        bonus = 0.10 * r["boot_frac"]
        pen = (r["collapse_penalty"] + r["c8_anomaly_penalty"]) / 8.0
        r["agg_score"] = round(base + bonus + pen, 4)

    results.sort(key=lambda r: r["agg_score"], reverse=True)
    print("\n=== RANKED (REVISED) ===")
    for i, r in enumerate(results, 1):
        c8a = "c8!" if r["rows"][7]["c8_anomaly"] else "   "
        print(f"  {i:>2}. {r['name']:<22} agg={r['agg_score']:+.4f} "
              f"P2a={r['p2a']:.2f} P1={r['p1']:.2f} P2b={r['p2b']:.2f} "
              f"pen={r['collapse_penalty']:+.2f} {c8a} {r['verdict']}")

    with open(OUTDIR / "candidates_summary_v2.json", "w") as f:
        json.dump({"sub": "sub-08", "cvd": CVD, "methodology": "v2_HC_naming",
                  "candidates": results}, f, indent=2, ensure_ascii=False)
    print(f"\nWrote {OUTDIR / 'candidates_summary_v2.json'}")


if __name__ == "__main__":
    main()
