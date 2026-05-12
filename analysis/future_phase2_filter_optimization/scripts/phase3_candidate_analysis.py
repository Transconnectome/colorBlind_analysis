"""phase3_candidate_analysis.py — Phase 2→3 transition candidate evaluation.

Pipeline:
1. Define candidate filters from loss inventory + manual additions
2. Build sub-08 perception map from raw_behav.md + canonical pre-image data
3. For each candidate:
   - CURRENT formula: compute pre-image and forward angles for c1-c8
   - Predict sub-08 perception by interpolating perception map
   - Score P1 (col4 hits HC target), P2a (col2 hits sub-08 actual), P2b (sub-08 reports HC target)
   - Run HC specificity (boot_frac)
4. Combine scores, rank, output top candidates

Outputs:
- results/phase3_candidates/candidates_summary.json
- results/phase3_candidates/perception_map.json
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

from forward_models.two_component import (
    forward_2comp, pre_image_2comp, dt_2comp_8colors
)
from hc_specificity_check import load_hc_norms, hc_specificity_check

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
OUTDIR = _PHASE2_DIR / "results" / "phase3_candidates"
OUTDIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Sub-08 deutan parameters
# ---------------------------------------------------------------------------
CVD = "deutan"
TARGET_THETAS = np.array([0, 45, 90, 135, 180, 225, 270, 315], dtype=float)

# HC target colors (what should be perceived at each angle)
HC_TARGETS = {
    0: "red", 45: "orange", 90: "yellow", 135: "green",
    180: "cyan", 225: "sky", 270: "blue", 315: "magenta",
}

# Sub-08 actual perception at original CIELab angles (raw_behav.md §Original)
SUB08_ORIGINAL = {
    0:   "pinkish_red",      # "빨강에 분홍 섞인"
    45:  "light_red",        # "연한 빨강"
    90:  "yellowgreen",      # "연두"
    135: "yellow",           # "노랑"
    180: "warm_ivory",       # "웜톤 아이보리"
    225: "sky",              # "하늘"
    270: "darker_sky",       # "더 진한 하늘"
    315: "deep_blue",        # "진파랑"
}

# ---------------------------------------------------------------------------
# Perception map: (CIELab angle, sub-08 perceived color category)
# ---------------------------------------------------------------------------
# Compiled from:
#   (a) raw_behav.md §Original at angles 0,45,...,315
#   (b) Canonical (β_s=38, β_c=-14) col4 pre-image angles + sub-08 reports
#       (CIELab convention pre-image from behav_validation.md §3)
#   (c) V4-only OLD formula (β_s=38, β_c=+7) col4 reports
#   (d) Cycle14 (β_s=58, β_c=-36) col4 reports
#
# Each entry: (theta_cielab_deg, perception_category)
# Categories use a discrete vocabulary mapped to angle bins via PERCEPT_TO_HC.
PERCEPTION_DATA = [
    # ── (a) Original (no filter) — sub-08 looking at L*=75/C*=40 ring at θ ──
    (0.0,   "pinkish_red"),
    (45.0,  "light_red"),
    (90.0,  "yellowgreen"),
    (135.0, "yellow"),
    (180.0, "warm_ivory"),
    (225.0, "sky"),
    (270.0, "darker_sky"),
    (315.0, "deep_blue"),
]

# We will programmatically extend this with canonical/V4-only/cycle14 col4 perceptions
# after computing their pre-image angles.

# Sub-08 reports for filter col4 (what they saw, indexed by target color c1-c8)
CANONICAL_REPORTS = {
    1: "pure_red",       # "분홍기 줄고 순수한 빨강"
    2: "slight_green",   # "약간 초록, 색 옅음"
    3: "yellow",         # "C4와 같은 노랑"
    4: "yellow",         # "C3와 같은 노랑"
    5: "sky",            # "C6와 같은 하늘"
    6: "sky",            # "C5와 같은 하늘"
    7: "darker_blue",    # "더 짙은 파랑"
    8: "deep_blue",      # "변화 없음" = original c8 perception
}
V4ONLY_OLD_REPORTS = {
    # Note: primary.png used OLD CIELab-direct formula
    1: None,             # "언급 없음"
    2: "darker_red",     # "더 짙은 빨강"
    3: "light_orange",   # "연한 주황"
    4: "light_yellowgreen",   # "연한 연두"
    5: "very_light_yellowgreen",  # "완전 옅은 연두"
    6: "darker_sky",     # "더 진한 하늘"
    7: "very_deep_blue", # "완전 짙은 파랑"
    8: "purple_pink",    # "핑크빛 섞인 보라"
}
CYCLE14_REPORTS = {
    1: "pink",           # "보라→핑크" (note: directional, took final state)
    2: "lighter_orange", # "더 옅은 주황"
    3: "yellow",         # "연한 주황→노랑"
    4: "warm_ivory",     # "연둣빛 노랑→웜톤 아이보리"
    5: "sky",            # "웜톤 아이보리→하늘"
    6: "darker_sky",     # "약간 진한 하늘"
    7: "sky",            # "파랑→하늘"
    8: "blue",           # "진한 파랑→파랑"
}

# Map of perception category → which HC target color it represents
PERCEPT_TO_HC = {
    "pinkish_red": "red",          # close-but-not-clean red
    "light_red": "red",
    "pure_red": "red",
    "darker_red": "red",
    "pink": "red",                  # adjacent
    "light_orange": "orange",
    "lighter_orange": "orange",
    "yellow": "yellow",
    "yellowgreen": "yellow",        # closer to yellow than green for sub-08
    "light_yellowgreen": "yellow",
    "very_light_yellowgreen": "yellow",
    "warm_ivory": "warm_ivory",     # unique sub-08 percept (collapses cyan + green)
    "slight_green": "green",
    "sky": "sky",
    "cyan": "cyan",
    "blue": "blue",
    "darker_blue": "blue",
    "darker_sky": "sky",            # sub-08 sees blue as deeper sky
    "very_deep_blue": "blue",
    "deep_blue": "blue",
    "purple_pink": "magenta",
    "purple": "magenta",
    "magenta": "magenta",
}

# Fuzzy partial-credit map: how close is perception to HC target?
# 1.0 = exact match, 0.5 = partial (same family, off shade), 0 = wrong
def percept_match_score(percept: str, target_color: str) -> float:
    """Return 1.0/0.5/0.0 for full/partial/no match against HC target."""
    if percept is None:
        return 0.0
    mapped = PERCEPT_TO_HC.get(percept, "unknown")
    if mapped == target_color:
        return 1.0
    # Adjacency: each color has neighbors that get partial credit
    adjacency = {
        "red":     {"orange": 0.5, "magenta": 0.5},
        "orange":  {"red": 0.5, "yellow": 0.5},
        "yellow":  {"orange": 0.5, "green": 0.5, "warm_ivory": 0.3},
        "green":   {"yellow": 0.5, "cyan": 0.5},
        "cyan":    {"green": 0.5, "sky": 0.7, "warm_ivory": 0.3},
        "sky":     {"cyan": 0.7, "blue": 0.5},
        "blue":    {"sky": 0.5, "magenta": 0.3},
        "magenta": {"blue": 0.3, "red": 0.5},
        "warm_ivory": {"yellow": 0.3, "cyan": 0.3},
    }
    return adjacency.get(target_color, {}).get(mapped, 0.0)


# ---------------------------------------------------------------------------
# OLD CIELab-direct formula for V4-only primary.png pre-image
# ---------------------------------------------------------------------------
THETA_CONF_CIELAB_DEUTAN = 150.0  # OLD formula uses CIELab confusion axis directly

def dt_old_formula(theta_cielab: float, beta_s: float, beta_c: float) -> float:
    """OLD CIELab-direct formula (no Stockman h_base conversion)."""
    return (beta_s * np.cos(np.radians(theta_cielab - 90.0))
            + beta_c * np.cos(np.radians(theta_cielab - THETA_CONF_CIELAB_DEUTAN)))

def pre_image_old(theta_target: float, beta_s: float, beta_c: float,
                  n_grid: int = 1440) -> tuple[float, float]:
    grid = np.linspace(0.0, 360.0, n_grid, endpoint=False)
    def residual(t):
        forward = (t + dt_old_formula(t, beta_s, beta_c)) % 360.0
        d = forward - theta_target
        return ((d + 180.0) % 360.0) - 180.0
    res = np.array([residual(t) for t in grid])
    i = int(np.argmin(np.abs(res)))
    return float(grid[i]), float(res[i])


# ---------------------------------------------------------------------------
# Build extended perception map
# ---------------------------------------------------------------------------
def build_perception_map() -> list[tuple[float, str]]:
    """Combine §Original + 3 filter pre-image data into one (angle, percept) map."""
    pmap = list(PERCEPTION_DATA)  # start with §Original anchors

    # Canonical (β_s=38, β_c=-14) — CURRENT formula
    for i, theta_t in enumerate(TARGET_THETAS, start=1):
        theta_pre, _ = pre_image_2comp(theta_t, CVD, 38.0, -14.0)
        pmap.append((theta_pre, CANONICAL_REPORTS[i]))

    # V4-only OLD formula (β_s=38, β_c=+7) — what sub-08 actually saw in primary.png
    for i, theta_t in enumerate(TARGET_THETAS, start=1):
        if V4ONLY_OLD_REPORTS[i] is None:
            continue
        theta_pre, _ = pre_image_old(theta_t, 38.0, 7.0)
        pmap.append((theta_pre, V4ONLY_OLD_REPORTS[i]))

    # Cycle14 (β_s=58, β_c=-36) — CURRENT formula
    for i, theta_t in enumerate(TARGET_THETAS, start=1):
        theta_pre, _ = pre_image_2comp(theta_t, CVD, 58.0, -36.0)
        pmap.append((theta_pre, CYCLE14_REPORTS[i]))

    return pmap


# ---------------------------------------------------------------------------
# Predict sub-08 perception at arbitrary CIELab angle via nearest-neighbor
# (with circular distance) over perception map
# ---------------------------------------------------------------------------
def predict_perception(theta_query: float, pmap: list[tuple[float, str]],
                       k: int = 3) -> str:
    """Nearest-neighbor (k=3) plurality vote on perception map."""
    angles = np.array([p[0] for p in pmap])
    percepts = [p[1] for p in pmap]
    diffs = np.abs(((angles - theta_query) + 180.0) % 360.0 - 180.0)
    idx_sorted = np.argsort(diffs)
    nearest_k = idx_sorted[:k]
    # Weighted by inverse distance
    votes: dict[str, float] = {}
    for idx in nearest_k:
        w = 1.0 / max(diffs[idx], 1.0)
        votes[percepts[idx]] = votes.get(percepts[idx], 0.0) + w
    return max(votes.items(), key=lambda x: x[1])[0]


# ---------------------------------------------------------------------------
# Score a candidate (β_s, β_c)
# ---------------------------------------------------------------------------
def score_candidate(beta_s: float, beta_c: float,
                    pmap: list[tuple[float, str]],
                    hc_norms: list[float]) -> dict:
    """Compute P2a, P1, P2b, HC specificity for a candidate."""

    rows = []  # per-color records
    for i, theta_t in enumerate(TARGET_THETAS, start=1):
        theta_pre, _ = pre_image_2comp(theta_t, CVD, beta_s, beta_c)
        theta_cvd, dt = forward_2comp(theta_t, CVD, beta_s, beta_c)

        # P2a: predicted sub-08 perception at theta_cvd should match SUB08_ORIGINAL[theta_t]
        col2_predicted = predict_perception(theta_cvd, pmap)
        sub08_actual = SUB08_ORIGINAL[int(theta_t)]
        p2a_score = 1.0 if PERCEPT_TO_HC.get(col2_predicted) == PERCEPT_TO_HC.get(sub08_actual) else (
            0.5 if col2_predicted == sub08_actual else 0.0)
        # Use the percept_match if same family
        p2a_score = max(p2a_score,
            percept_match_score(col2_predicted, PERCEPT_TO_HC.get(sub08_actual, "")))

        # P1: predicted sub-08 perception at theta_pre should match HC target
        col4_predicted = predict_perception(theta_pre, pmap)
        target_color = HC_TARGETS[int(theta_t)]
        p1_score = percept_match_score(col4_predicted, target_color)

        # P2b: would sub-08 verbally report HC target? (same as P1 for our prediction model)
        # P2b is more conservative — needs a clean match
        p2b_score = 1.0 if PERCEPT_TO_HC.get(col4_predicted) == target_color else 0.0

        rows.append({
            "color": f"c{i}",
            "theta": int(theta_t),
            "theta_pre": round(theta_pre, 1),
            "theta_cvd": round(theta_cvd, 1),
            "dt": round(dt, 1),
            "col2_pred": col2_predicted,
            "sub08_actual": sub08_actual,
            "p2a": p2a_score,
            "col4_pred": col4_predicted,
            "target": target_color,
            "p1": p1_score,
            "p2b": p2b_score,
        })

    p2a_total = sum(r["p2a"] for r in rows)
    p1_total = sum(r["p1"] for r in rows)
    p2b_total = sum(r["p2b"] for r in rows)

    spec = hc_specificity_check(beta_s, beta_c, hc_norms, n_boot=10000)

    return {
        "beta_s": beta_s,
        "beta_c": beta_c,
        "norm": spec["cvd_norm"],
        "boot_frac": spec["boot_frac"],
        "verdict": spec["verdict"],
        "p2a": round(p2a_total, 2),
        "p1": round(p1_total, 2),
        "p2b": round(p2b_total, 2),
        "rows": rows,
    }


# ---------------------------------------------------------------------------
# Candidate definitions (sub-08 deutan, V4 unless noted)
# ---------------------------------------------------------------------------
CANDIDATES = [
    # Existing tested
    {"name": "Canonical",     "beta_s": 38.0, "beta_c": -14.0, "source": "phase_a L_LOCO (PASS §3)"},
    {"name": "V4-only_CURRENT","beta_s": 38.0, "beta_c": 7.0,  "source": "cycle10d z_combined (CURRENT formula)"},
    {"name": "Cycle14",       "beta_s": 58.0, "beta_c": -36.0, "source": "mw_jaccard / cycle14 / l_topk_jaccard"},
    # Loss-inventory derived (unique)
    {"name": "l_rank",        "beta_s": 74.0, "beta_c": -60.0, "source": "l_rank / spearman_r argmin"},
    {"name": "l_dir",         "beta_s": 78.0, "beta_c": -60.0, "source": "l_dir / pearson_r argmax"},
    {"name": "norm_resid",    "beta_s": 76.0, "beta_c": -60.0, "source": "norm_resid argmin"},
    {"name": "l_mag",         "beta_s": 44.0, "beta_c": 58.0,  "source": "l_mag argmin"},
    {"name": "sign_agree",    "beta_s": 10.0, "beta_c": 58.0,  "source": "sign_agree argmax"},
    {"name": "phase_a_V1",    "beta_s": 50.0, "beta_c": -14.0, "source": "phase_a V1 canonical"},
    {"name": "cycle12_xroi",  "beta_s": 68.0, "beta_c": -38.0, "source": "cycle12 V4+V1 cross-ROI"},
    {"name": "cycle15_opt3",  "beta_s": 58.0, "beta_c": -28.0, "source": "cycle15 mw_jaccard(V4)+mw_jaccard(V1)"},
    {"name": "cycle15_opt4",  "beta_s": 70.0, "beta_c": -52.0, "source": "cycle15 mw_jaccard(V4)+spearman(V4)"},
    # Proposed exploration: scaled / interpolated
    {"name": "scaled_canonical","beta_s": 50.0, "beta_c": -20.0, "source": "Canonical scaled to ~54° norm"},
    {"name": "mid_canonical_cycle14","beta_s": 48.0, "beta_c": -25.0, "source": "midpoint Canonical-Cycle14"},
]


def main() -> None:
    print("Loading HC norms...")
    hc_norms = load_hc_norms("V4")
    print(f"HC V4 norms: {hc_norms}")

    print("\nBuilding perception map...")
    pmap = build_perception_map()
    print(f"  {len(pmap)} (angle, percept) anchors")
    # Save perception map
    with open(OUTDIR / "perception_map.json", "w") as f:
        json.dump([{"theta": round(a, 2), "percept": p} for (a, p) in pmap],
                  f, indent=2, ensure_ascii=False)

    print(f"\nScoring {len(CANDIDATES)} candidates...")
    results = []
    for cand in CANDIDATES:
        print(f"  {cand['name']:<22} (β_s={cand['beta_s']:>5.1f}, β_c={cand['beta_c']:>+6.1f})", end="  ")
        result = score_candidate(cand["beta_s"], cand["beta_c"], pmap, hc_norms)
        result["name"] = cand["name"]
        result["source"] = cand["source"]
        results.append(result)
        print(f"P2a={result['p2a']:.2f} P1={result['p1']:.2f} P2b={result['p2b']:.2f} "
              f"norm={result['norm']:.1f} boot_frac={result['boot_frac']:.3f} {result['verdict']}")

    # Aggregate score: 0.4*P1 + 0.3*P2b + 0.2*P2a + 0.1*spec
    # P1 most important (filter actually works), P2b second (sub-08 verbal),
    # P2a third (simulator accuracy), HC spec descriptive bonus
    for r in results:
        r["agg_score"] = round(
            0.4 * r["p1"] / 8.0 +
            0.3 * r["p2b"] / 8.0 +
            0.2 * r["p2a"] / 8.0 +
            0.1 * r["boot_frac"], 4)
    results.sort(key=lambda r: r["agg_score"], reverse=True)

    print("\n=== RANKED CANDIDATES ===")
    for i, r in enumerate(results, 1):
        print(f"  {i:>2}. {r['name']:<22} agg={r['agg_score']:.4f} "
              f"P2a={r['p2a']:.2f} P1={r['p1']:.2f} P2b={r['p2b']:.2f} "
              f"norm={r['norm']:.1f} {r['verdict']}")

    with open(OUTDIR / "candidates_summary.json", "w") as f:
        json.dump({"sub": "sub-08", "cvd": CVD, "candidates": results},
                  f, indent=2, ensure_ascii=False)
    print(f"\nWrote {OUTDIR / 'candidates_summary.json'}")


if __name__ == "__main__":
    main()
