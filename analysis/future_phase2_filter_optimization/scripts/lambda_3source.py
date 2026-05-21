"""S1: lambda_3source.py — Δλ from 3 sources per CVD subject.

Sources:
  (b) DPS 1992 literature: protan ≈ 10 nm, deutan ≈ 6 nm (PRIMARY)
  (c) Boehm 2014 severity grid: {3, 8, 13} nm (robustness)
  (d) JND-Lamb inverse — Option B: all-pair joint fit (sensitivity supplement only)

Forward model: machado_shifted_hue (Machado 2009 Eq 5/6) from utils_distortion_models.

JND prediction (perceived-space compression/expansion):
  d_phys(p)  = |θ_a − θ_b|  (modular)
  d_perc(p) = |perceived(θ_a) − perceived(θ_b)|  (modular)
  JND_AT_pred(p) = JND_HC_baseline(p) × (d_phys / d_perc)

HC negative control: applying same inverse fit to each HC under protan/deutan assumption
should give Δλ ≈ 0 (no cone shift in HC).
"""
import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from utils_distortion_models import apply_distortion

ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT / "data" / "behavior"
OUT_DIR = SCRIPT_DIR.parent / "results" / "lambda_3source"

# Pair mapping — adjacent (45°), wide (90°), opposite (180°), oblique (135°)
PAIR_HUES = {
    'red-orange':    (  0.0,  45.0),
    'orange-yellow': ( 45.0,  90.0),
    'yellow-green':  ( 90.0, 135.0),
    'green-blue':    (135.0, 225.0),   # skip cyan
    'blue-purple':   (225.0, 270.0),
    'yellow-purple': ( 90.0, 270.0),
    'cyan-magenta':  (180.0, 315.0),
    'red-cyan':      (  0.0, 180.0),
}

DPS_DELTA_LAMBDA = {'protan': 10.0, 'deutan': 6.0}   # nm (DPS 1992 pop mean)
BOEHM_GRID = [3.0, 8.0, 13.0]                          # nm (Boehm 2014 severity grid)

SUBJECTS = {'sub-08': 'deutan', 'sub-09': 'protan'}
HC_SUBJS = ['sub-01', 'sub-02', 'sub-03', 'sub-04', 'sub-05', 'sub-06', 'sub-07']


def hue_dist_mod(a: float, b: float) -> float:
    """Modular hue distance, ∈ [0, 180]."""
    d = abs(a - b) % 360
    return min(d, 360.0 - d)


def predict_jnd_ratio(theta_a: float, theta_b: float, delta_lambda: float,
                      cvd_family: str, baseline_hues: np.ndarray) -> float:
    """Predict JND_AT(p) / JND_HC(p) under cone shift Δλ.

    Both distances computed in *same coord* (Stockman opponent space) to avoid
    coordinate mismatch.

    Args:
        baseline_hues: (8,) Machado output at Δλ=0 (Stockman opponent coord baseline)
    """
    # Forward Machado at Δλ: shifted hue for 8 canonical colors
    shifted_8 = apply_distortion('machado_1way', [delta_lambda], cvd_type=cvd_family)

    # Map theta_a, theta_b to canonical indices (0..7)
    idx_a = int(round(theta_a / 45.0)) % 8
    idx_b = int(round(theta_b / 45.0)) % 8

    # Distances in SAME (Stockman) coord:
    #   d_phys: HC baseline mapping (Δλ=0)
    #   d_perc: CVD shifted mapping (current Δλ)
    d_phys = hue_dist_mod(baseline_hues[idx_a], baseline_hues[idx_b])
    d_perc = hue_dist_mod(shifted_8[idx_a], shifted_8[idx_b])
    d_perc = max(d_perc, 1e-3)
    return d_phys / d_perc


def load_jnd_per_pair(subject: str) -> dict:
    """Mean JND per pair (averaging sc0, sc1 staircases)."""
    df = pd.read_csv(DATA_DIR / f"{subject}_jnd_ses1_no_filter_summary.csv")
    out = {}
    for p in PAIR_HUES.keys():
        sub = df[df['pair_name'] == p]
        out[p] = float(sub['jnd_mean'].mean()) if len(sub) > 0 else None
    return out


def compute_hc_baseline() -> tuple:
    """HC pool JND baseline (mean ± SD) per pair across N=7 HC."""
    hc_data = [load_jnd_per_pair(s) for s in HC_SUBJS]
    baseline = {}
    sd = {}
    for p in PAIR_HUES.keys():
        vals = [d[p] for d in hc_data if d[p] is not None]
        baseline[p] = float(np.mean(vals))
        sd[p] = float(np.std(vals, ddof=1))
    return baseline, sd


def jnd_lamb_inverse_fit(subject: str, cvd_family: str,
                          hc_baseline: dict, hc_sd: dict,
                          delta_max: float = 30.0,
                          delta_step: float = 0.5) -> dict:
    """Option B: all-pair joint fit. Returns Δλ_JND-Lamb + diagnostics."""
    jnd_obs = load_jnd_per_pair(subject)
    delta_grid = np.arange(0.0, delta_max + delta_step, delta_step)
    losses = np.zeros_like(delta_grid)

    # Precompute Stockman-coord baseline (Δλ=0) for this CVD family
    baseline_hues = apply_distortion('machado_1way', [0.0], cvd_type=cvd_family)

    per_pair_pred_at_best = {}
    for i, dl in enumerate(delta_grid):
        loss = 0.0
        n_used = 0
        for pair, (theta_a, theta_b) in PAIR_HUES.items():
            if jnd_obs[pair] is None:
                continue
            ratio = predict_jnd_ratio(theta_a, theta_b, dl, cvd_family, baseline_hues)
            jnd_pred = hc_baseline[pair] * ratio
            sigma_p = max(hc_sd[pair], 1e-3)
            loss += ((jnd_pred - jnd_obs[pair]) / sigma_p) ** 2
            n_used += 1
        losses[i] = loss / max(n_used, 1)  # mean weighted MSE

    best_idx = int(np.argmin(losses))
    best_dl = float(delta_grid[best_idx])

    # Per-pair prediction at best Δλ
    for pair, (theta_a, theta_b) in PAIR_HUES.items():
        if jnd_obs[pair] is None:
            per_pair_pred_at_best[pair] = None
            continue
        ratio = predict_jnd_ratio(theta_a, theta_b, best_dl, cvd_family, baseline_hues)
        per_pair_pred_at_best[pair] = {
            'jnd_obs': jnd_obs[pair],
            'jnd_pred': hc_baseline[pair] * ratio,
            'hc_baseline': hc_baseline[pair],
            'hc_sd': hc_sd[pair],
            'ratio': ratio,
        }

    return {
        'delta_lambda': best_dl,
        'loss_at_best': float(losses[best_idx]),
        'loss_at_zero': float(losses[0]),
        'improvement_over_null': float(losses[0] - losses[best_idx]),
        'boundary_hit_low': bool(best_idx == 0),
        'boundary_hit_high': bool(best_idx == len(delta_grid) - 1),
        'monotonic': bool(np.all(np.diff(losses[: best_idx + 1]) <= 0) if best_idx > 0 else True),
        'loss_curve_finite': bool(np.all(np.isfinite(losses))),
        'grid_min': float(delta_grid[0]),
        'grid_max': float(delta_grid[-1]),
        'grid_step': float(delta_step),
        'per_pair_at_best': per_pair_pred_at_best,
    }


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 78)
    print("S1: lambda_3source.py — Δλ from 3 sources")
    print("=" * 78)

    # HC baseline
    hc_baseline, hc_sd = compute_hc_baseline()
    print("\nHC pool JND baseline (N=7, mean ± SD per pair):")
    for p in PAIR_HUES.keys():
        print(f"  {p:18s}: {hc_baseline[p]:.4f} ± {hc_sd[p]:.4f}")

    # Per CVD subject
    all_results = {}
    for subject, cvd_family in SUBJECTS.items():
        print(f"\n--- {subject} ({cvd_family}) ---")
        d_fit = jnd_lamb_inverse_fit(subject, cvd_family, hc_baseline, hc_sd)
        result = {
            'subject': subject,
            'cvd_family': cvd_family,
            'sources': {
                'b_dps_lit': {
                    'delta_lambda': DPS_DELTA_LAMBDA[cvd_family],
                    'source': 'DeMarco, Pokorny, Smith 1992 (population mean cone shift)',
                    'note': 'PRIMARY — literature anchor',
                },
                'c_boehm_grid': {
                    'delta_lambda_grid': BOEHM_GRID,
                    'source': 'Boehm et al. 2014 (Lamb 1995 cone fundamentals severity grid)',
                    'note': 'Robustness check',
                },
                'd_jnd_lamb': {
                    **d_fit,
                    'source': 'Per-subject JND all-pair joint fit via Machado forward model',
                    'note': 'Sensitivity supplement ONLY (dual-role caveat: JND also L_behav_γ target)',
                },
            },
        }
        all_results[subject] = result

        out_path = OUT_DIR / f"{subject}_lambda.json"
        with open(out_path, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"  (b) DPS lit:    Δλ = {DPS_DELTA_LAMBDA[cvd_family]:.2f} nm")
        print(f"  (c) Boehm grid: Δλ ∈ {BOEHM_GRID}")
        print(f"  (d) JND-Lamb:   Δλ = {d_fit['delta_lambda']:.2f} nm "
              f"(loss {d_fit['loss_at_best']:.4f}, null loss {d_fit['loss_at_zero']:.4f})")
        if d_fit['boundary_hit_high']:
            print("    ⚠ Boundary hit (upper) — increase grid_max")
        if d_fit['boundary_hit_low']:
            print("    ⚠ Boundary hit (lower) — fit pushed to Δλ=0")
        print(f"  Saved: {out_path}")

    # HC negative control: apply same fit logic to each HC under protan/deutan assumption
    print("\n--- HC negative control ---")
    hc_negative = []
    for hc in HC_SUBJS:
        for fam in ['protan', 'deutan']:
            try:
                r = jnd_lamb_inverse_fit(hc, fam, hc_baseline, hc_sd)
                hc_negative.append({
                    'subject': hc, 'cvd_family_assumed': fam,
                    'delta_lambda': r['delta_lambda'],
                    'loss_at_best': r['loss_at_best'],
                    'loss_at_zero': r['loss_at_zero'],
                    'boundary_hit_low': r['boundary_hit_low'],
                    'boundary_hit_high': r['boundary_hit_high'],
                })
            except Exception as e:
                print(f"  {hc} ({fam}): ERROR {e}")

    neg_path = OUT_DIR / "hc_negative_control.json"
    with open(neg_path, 'w') as f:
        json.dump(hc_negative, f, indent=2)
    print(f"\nSaved HC negative control: {neg_path}")

    # Summary
    print("\n" + "=" * 78)
    print("Validation summary")
    print("=" * 78)
    for fam in ['protan', 'deutan']:
        hc_dls = [h['delta_lambda'] for h in hc_negative
                  if h['cvd_family_assumed'] == fam]
        boundary_low_n = sum(1 for h in hc_negative
                             if h['cvd_family_assumed'] == fam and h['boundary_hit_low'])
        print(f"\nHC pool under {fam} assumption (N={len(hc_dls)}):")
        print(f"  Δλ mean = {np.mean(hc_dls):.2f} ± {np.std(hc_dls):.2f} nm")
        print(f"  Range = [{min(hc_dls):.2f}, {max(hc_dls):.2f}] nm")
        print(f"  Δλ=0 boundary hits = {boundary_low_n}/{len(hc_dls)}")
        print(f"  → Expected ≈ 0 if forward model valid")

    print(f"\nAll results in: {OUT_DIR}")


if __name__ == "__main__":
    main()
