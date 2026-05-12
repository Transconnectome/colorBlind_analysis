"""phase3_fit_opponent_gain.py — Fit two-channel opponent gain (g_LM, g_S)
to sub-08 deutan verbal-percept anchors.

Model:    forward_opponent_gain(θ, 'deutan', Δλ=14, g_LM, g_S)
Anchors:  results/phase3_candidates/perception_map_v2.json (39 (θ, percept))
Score:    loss = − Σ_anchors hc_match_score(predicted_HC, actual_HC_equiv)

Reuses HC binning, HC adjacency, and percept→HC mapping from
phase3_candidate_analysis_v2.py (single source of truth).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

_THIS_DIR = Path(__file__).resolve().parent
_PHASE2_DIR = _THIS_DIR.parent
sys.path.insert(0, str(_THIS_DIR))
sys.path.insert(0, str(_THIS_DIR / 'forward_models'))

from forward_models.opponent_gain import (
    forward_opponent_gain,
    pre_image_opponent_gain,
)
from phase3_candidate_analysis_v2 import (
    HC_NAME_BINS,  # noqa: F401  (kept for downstream consistency)
    HC_TARGETS,
    PERCEPT_TO_HC_NAME,
    SUB08_ORIGINAL_HC_EQUIV,
    hc_match_score,
    hc_name,
)

OUTDIR = _PHASE2_DIR / 'results' / 'phase3_candidates' / 'opponent_gain_fit'
OUTDIR.mkdir(parents=True, exist_ok=True)

PERCEPTION_MAP = _PHASE2_DIR / 'results' / 'phase3_candidates' / 'perception_map_v2.json'

CVD = 'deutan'
DELTA_LAMBDA = 14.0  # deutan population prior (fixed per task spec)
TARGET_THETAS = np.array([0, 45, 90, 135, 180, 225, 270, 315], dtype=float)


def load_anchors() -> list[dict]:
    with open(PERCEPTION_MAP) as f:
        data = json.load(f)
    out = []
    for row in data:
        hc_eq = PERCEPT_TO_HC_NAME.get(row['percept'])
        if hc_eq is None:
            # Unknown verbal token — skip; should not occur with v2 map.
            continue
        out.append({
            'theta': float(row['theta']),
            'percept': row['percept'],
            'percept_hc_equiv': hc_eq,
        })
    return out


def score_grid(anchors: list[dict], g_LM_grid: np.ndarray,
               g_S_grid: np.ndarray) -> dict:
    """Sweep (g_LM, g_S) grid; return per-cell total loss + best cell.

    Loss = − Σ hc_match_score across anchors.
    """
    n_anchors = len(anchors)
    nG = g_LM_grid.size
    nS = g_S_grid.size
    score = np.zeros((nG, nS), dtype=float)

    # Per-anchor predicted hue & HC for the best cell are populated after argmax.
    print(f'  Sweeping {nG}×{nS}={nG*nS} (g_LM, g_S) cells over '
          f'{n_anchors} anchors...', flush=True)

    for i, gLM in enumerate(g_LM_grid):
        for j, gS in enumerate(g_S_grid):
            total = 0.0
            for a in anchors:
                th_p, _ = forward_opponent_gain(
                    a['theta'], CVD, DELTA_LAMBDA, float(gLM), float(gS))
                pred_hc = hc_name(th_p)
                total += hc_match_score(pred_hc, a['percept_hc_equiv'])
            score[i, j] = total  # match score (higher = better)

    # Argmax of match score; if multiple cells tie, choose the one closest
    # to (g_LM, g_S) = (1, 1) (unity prior — atan2(g_S·by, g_LM·rg) is
    # invariant to overall scaling, so the gain MODEL only fixes the ratio
    # g_S / g_LM. Selecting the closest-to-unity tie gives a deterministic,
    # interpretable representative without changing predictions.).
    best_match = float(np.max(score))
    tie_mask = score >= best_match - 1e-9
    tie_indices = np.argwhere(tie_mask)
    dist2 = []
    for (i, j) in tie_indices:
        gLM = float(g_LM_grid[i])
        gS = float(g_S_grid[j])
        dist2.append((gLM - 1.0) ** 2 + (gS - 1.0) ** 2)
    tie_indices = tie_indices[np.argsort(dist2)]
    i_best, j_best = int(tie_indices[0][0]), int(tie_indices[0][1])
    best_g_LM = float(g_LM_grid[i_best])
    best_g_S = float(g_S_grid[j_best])
    best_loss = float(-best_match)
    n_ties = int(tie_mask.sum())
    return {
        'score_grid': score,
        'g_LM_grid': g_LM_grid,
        'g_S_grid': g_S_grid,
        'best_g_LM': best_g_LM,
        'best_g_S': best_g_S,
        'best_match': best_match,
        'best_loss': best_loss,
        'max_possible_match': float(n_anchors),
        'n_ties': n_ties,
        'tie_examples': [
            {'g_LM': float(g_LM_grid[i]), 'g_S': float(g_S_grid[j])}
            for (i, j) in tie_indices[:10]
        ],
    }


def per_anchor_predictions(anchors: list[dict], gLM: float, gS: float) -> list[dict]:
    rows = []
    for a in anchors:
        th_p, dt = forward_opponent_gain(a['theta'], CVD, DELTA_LAMBDA, gLM, gS)
        pred_hc = hc_name(th_p)
        rows.append({
            'theta': round(a['theta'], 2),
            'actual_percept': a['percept'],
            'actual_hc': a['percept_hc_equiv'],
            'predicted_theta': round(th_p, 2),
            'dt': round(dt, 2),
            'predicted_hc': pred_hc,
            'match_score': round(hc_match_score(pred_hc, a['percept_hc_equiv']), 3),
        })
    return rows


def eight_color_forward(gLM: float, gS: float) -> list[dict]:
    rows = []
    for i, theta in enumerate(TARGET_THETAS, 1):
        th_p, dt = forward_opponent_gain(float(theta), CVD, DELTA_LAMBDA, gLM, gS)
        pred_hc = hc_name(th_p)
        actual_hc = SUB08_ORIGINAL_HC_EQUIV[int(theta)]
        rows.append({
            'color': f'c{i}',
            'theta': int(theta),
            'theta_perceived': round(th_p, 2),
            'dt': round(dt, 2),
            'predicted_hc': pred_hc,
            'sub08_actual_hc': actual_hc,
            'match': round(hc_match_score(pred_hc, actual_hc), 3),
        })
    return rows


def eight_color_preimage(gLM: float, gS: float) -> list[dict]:
    rows = []
    for i, theta in enumerate(TARGET_THETAS, 1):
        th_pre, resid = pre_image_opponent_gain(
            float(theta), CVD, DELTA_LAMBDA, gLM, gS)
        # forward(pre-image) sanity
        th_cvd_of_pre, _ = forward_opponent_gain(
            th_pre, CVD, DELTA_LAMBDA, gLM, gS)
        rows.append({
            'target_color': f'c{i}',
            'target_theta': int(theta),
            'theta_pre': round(float(th_pre), 2),
            'residual': round(float(resid), 4),
            'forward_of_pre': round(float(th_cvd_of_pre), 2),
        })
    return rows


def main() -> None:
    anchors = load_anchors()
    print(f'Loaded {len(anchors)} anchors from {PERCEPTION_MAP.name}')

    # Grid resolution: 0.05 step per task spec
    g_LM_grid = np.arange(0.10, 1.50 + 1e-9, 0.05)
    g_S_grid = np.arange(0.50, 2.00 + 1e-9, 0.05)
    print(f'g_LM ∈ [{g_LM_grid[0]:.2f}, {g_LM_grid[-1]:.2f}] step 0.05  '
          f'(n={g_LM_grid.size})')
    print(f'g_S  ∈ [{g_S_grid[0]:.2f}, {g_S_grid[-1]:.2f}] step 0.05  '
          f'(n={g_S_grid.size})')

    sweep = score_grid(anchors, g_LM_grid, g_S_grid)
    gLM, gS = sweep['best_g_LM'], sweep['best_g_S']
    print(f'\nBest cell (closest-to-unity among ties): '
          f'g_LM={gLM:.3f}, g_S={gS:.3f}  '
          f'match={sweep["best_match"]:.2f} / {sweep["max_possible_match"]:.0f}  '
          f'loss={sweep["best_loss"]:+.3f}  ties={sweep["n_ties"]}')
    print('Note: atan2(g_S·by, g_LM·rg) is invariant to overall scaling, '
          'so only the ratio g_S/g_LM is identifiable.')
    print(f'Best ratio g_S / g_LM = {gS / gLM:.3f}')

    # Top-5 grid cells for context
    flat = sweep['score_grid'].ravel()
    top5_idx = np.argsort(flat)[-5:][::-1]
    print('\nTop 5 grid cells (by match score):')
    for k, idx in enumerate(top5_idx, 1):
        i, j = np.unravel_index(int(idx), sweep['score_grid'].shape)
        print(f'  {k}. g_LM={g_LM_grid[i]:.3f}, g_S={g_S_grid[j]:.3f}  '
              f'match={flat[idx]:.2f}')

    per_anchor = per_anchor_predictions(anchors, gLM, gS)
    eight_fwd = eight_color_forward(gLM, gS)
    eight_pre = eight_color_preimage(gLM, gS)

    print('\n8-color forward predictions at best (g_LM, g_S):')
    print(f'  {"col":<4} {"θ":>4} {"θ_p":>7} {"dt":>7} {"pred_hc":<14} '
          f'{"sub08_hc":<14} {"match":>5}')
    for r in eight_fwd:
        print(f'  {r["color"]:<4} {r["theta"]:>4} {r["theta_perceived"]:>7.2f} '
              f'{r["dt"]:>+7.2f} {r["predicted_hc"]:<14} '
              f'{r["sub08_actual_hc"]:<14} {r["match"]:>5.2f}')

    print('\n8-color pre-image at best (g_LM, g_S):')
    print(f'  {"col":<4} {"θ":>4} {"θ_pre":>7} {"resid":>7} {"fwd(pre)":>8}')
    for r in eight_pre:
        print(f'  {r["target_color"]:<4} {r["target_theta"]:>4} '
              f'{r["theta_pre"]:>7.2f} {r["residual"]:>+7.3f} '
              f'{r["forward_of_pre"]:>8.2f}')

    result = {
        'subject': 'sub-08',
        'cvd_type': CVD,
        'delta_lambda': DELTA_LAMBDA,
        'g_LM_grid': [round(float(v), 3) for v in g_LM_grid],
        'g_S_grid': [round(float(v), 3) for v in g_S_grid],
        'best_g_LM': round(gLM, 3),
        'best_g_S': round(gS, 3),
        'best_ratio_gS_over_gLM': round(gS / gLM, 4),
        'best_match': round(sweep['best_match'], 3),
        'best_loss': round(sweep['best_loss'], 3),
        'max_possible_match': sweep['max_possible_match'],
        'n_anchors': len(anchors),
        'n_ties_at_best': sweep['n_ties'],
        'tie_examples': sweep['tie_examples'],
        'identifiability_note': (
            'forward_opponent_gain reduces to atan2(g_S·by, g_LM·rg) modulo '
            'a baseline atan2 offset, so the hue-recovery step depends only '
            'on the ratio g_S / g_LM. Reported (best_g_LM, best_g_S) is the '
            'tied cell closest to (1, 1) by Euclidean distance.'
        ),
        'per_anchor_predictions': per_anchor,
        '8color_summary': eight_fwd,
        'preimage_targets': eight_pre,
    }

    out_json = OUTDIR / 'fit_result.json'
    with open(out_json, 'w') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f'\nWrote {out_json}')

    # Also save the full score grid (compressed for inspection)
    grid_out = OUTDIR / 'score_grid.json'
    with open(grid_out, 'w') as f:
        json.dump({
            'g_LM_grid': [round(float(v), 3) for v in g_LM_grid],
            'g_S_grid': [round(float(v), 3) for v in g_S_grid],
            'score_grid': sweep['score_grid'].round(3).tolist(),
        }, f, indent=2)
    print(f'Wrote {grid_out}')


if __name__ == '__main__':
    main()
