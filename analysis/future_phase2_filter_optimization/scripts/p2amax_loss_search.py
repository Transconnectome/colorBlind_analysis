"""p2amax_loss_search.py — vuln_sim range diagnostic + 다양한 loss 후보 탐색.

(a) **vuln_sim 0-clustering 진단** — cells가 0 근처에 좁게 분포한다는 가설 검증
    - vuln_sim values range, std, percentile per cell
    - vuln_cvd 범위와 비교
    - P2a-max cell vs L-best cell의 vuln_sim distribution

(b) **새 loss 후보** — vuln_sim 범위 한계 우회 + P2a-max를 argmin으로
    1. l_topk alone (사용자 제안)
    2. Spearman rank loss (scale 무관)
    3. Sign-agreement loss (vuln_sim sign이 vuln_cvd sign과 일치하는 color 수)
    4. Per-color sign + Tikh combo
    5. Worst-color identity (argmin position match)
    6. Rescaled CCC (vuln_sim을 obs range로 rescale 후 CCC)
    7. Categorical: 음/양 색깔 그룹 정확도
    8. l_topk + Tikh

각 loss에 대해 sub-08, sub-09에서 argmin → P2a 도출.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

_THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_THIS_DIR))

from phase3_candidate_analysis_v2 import (
    hc_name, hc_match_score, SUB08_ORIGINAL_HC_EQUIV,
)
from fixedW_onlyTest_p2a_ranking import SUB09_ORIGINAL_HC_EQUIV

OUT = _THIS_DIR.parent / 'results' / 'p2amax_loss_search'
OUT.mkdir(parents=True, exist_ok=True)

HUE_8 = [0, 45, 90, 135, 180, 225, 270, 315]


def forward(theta, bs, bc, phi_c, phi_s=90.0):
    return (theta + bs * np.cos(np.radians(theta - phi_s))
                  + bc * np.cos(np.radians(theta - phi_c))) % 360.0


def p2a_cell(bs, bc, phi_c, target_map):
    total = 0.0; exact = 0
    for theta in HUE_8:
        theta_cvd = forward(float(theta), bs, bc, phi_c)
        pred = hc_name(theta_cvd)
        target = target_map[theta]
        total += hc_match_score(pred, target)
        if pred == target: exact += 1
    return total / 8.0, exact


# ----------------------------------------------------------------------
# Loss definitions (각 (vuln_sim, vuln_obs) 8-vector pair에 대해 적용)
# ----------------------------------------------------------------------
def loss_l_topk_only(sim, obs, K=3):
    """Top-K vulnerable color set Jaccard distance."""
    s_top = set(np.argsort(sim)[:K].tolist())
    o_top = set(np.argsort(obs)[:K].tolist())
    return 1.0 - len(s_top & o_top) / max(1, len(s_top | o_top))


def loss_spearman(sim, obs):
    """1 - Spearman rank correlation (scale-invariant)."""
    if np.std(sim) < 1e-10: return 1.0
    r, _ = spearmanr(sim, obs)
    return float(1.0 - (r if np.isfinite(r) else 0.0))


def loss_sign_agree(sim, obs):
    """1 - fraction of colors where sign(sim) == sign(obs)."""
    s_sign = np.sign(sim); o_sign = np.sign(obs)
    return float(1.0 - np.mean(s_sign == o_sign))


def loss_rescaled_ccc(sim, obs):
    """Rescale sim to obs range, then compute CCC. Avoids 0-clustering bias."""
    if np.std(sim) < 1e-10:
        return 1.0
    sim_r = (sim - sim.mean()) / sim.std() * obs.std() + obs.mean()
    # CCC
    r = np.corrcoef(sim_r, obs)[0, 1]
    if not np.isfinite(r): return 1.0
    msim, mobs = sim_r.mean(), obs.mean()
    ssim, sobs = sim_r.std(),  obs.std()
    denom = ssim**2 + sobs**2 + (msim - mobs)**2
    if denom < 1e-10: return 1.0
    ccc = 2 * r * ssim * sobs / denom
    return float((1 - ccc) / 2)


def loss_argmin_identity(sim, obs):
    """1 if most-vulnerable color id matches, else 0 (binary)."""
    return float(np.argmin(sim) != np.argmin(obs))


def loss_top1_top3_compound(sim, obs):
    """argmin match + top-3 Jaccard (compound)."""
    t1 = loss_argmin_identity(sim, obs)
    t3 = loss_l_topk_only(sim, obs, K=3)
    return 0.5 * t1 + 0.5 * t3


# ----------------------------------------------------------------------
# (a) Diagnostic: vuln_sim 0-clustering
# ----------------------------------------------------------------------
def diagnose_vuln_range(cells, vuln_cvd, p2a_max_bs, p2a_max_bc, axis_label):
    sim_means = []
    sim_stds = []
    sim_ranges = []
    p2a_max_sim = None
    for c in cells:
        sim = np.array(c['vuln_sim'])
        sim_means.append(sim.mean())
        sim_stds.append(sim.std())
        sim_ranges.append(sim.max() - sim.min())
        if abs(c['bs'] - p2a_max_bs) < 0.5 and abs(c['bc'] - p2a_max_bc) < 0.5:
            p2a_max_sim = sim

    sim_means = np.array(sim_means)
    sim_stds = np.array(sim_stds)
    sim_ranges = np.array(sim_ranges)
    obs_range = vuln_cvd.max() - vuln_cvd.min()

    print(f'  vuln_sim diagnostic ({axis_label}):')
    print(f'    Per-cell mean: range=[{sim_means.min():+.3f}, {sim_means.max():+.3f}]  '
          f'overall mean={sim_means.mean():+.3f}')
    print(f'    Per-cell std:  range=[{sim_stds.min():.3f}, {sim_stds.max():.3f}]   '
          f'overall mean={sim_stds.mean():.3f}')
    print(f'    Per-cell range: [{sim_ranges.min():.3f}, {sim_ranges.max():.3f}]   '
          f'mean={sim_ranges.mean():.3f}')
    print(f'    vuln_cvd range: {obs_range:.3f}  (sim range / obs range ratio = '
          f'{sim_ranges.mean()/obs_range:.2f}× — <0.5 = 큰 clustering 한계)')
    if p2a_max_sim is not None:
        print(f'    At P2a-max:   vuln_sim = {p2a_max_sim.round(3).tolist()}')
        print(f'                  vuln_cvd = {vuln_cvd.round(3).tolist()}')


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main():
    files = [
        # (sid, axis_label, axis, p2amax_bs, p2amax_bc, path)
        ('08', 'Stockman150', 150.0, 26, +34, 'results/axis_3way/sub-08_V4_Stockman150_landscape.json'),
        ('09', 'Stockman16',   16.0, 24, -20, 'results/axis_3way/sub-09_V4_Stockman16_landscape.json'),
    ]
    target_maps = {'08': SUB08_ORIGINAL_HC_EQUIV, '09': SUB09_ORIGINAL_HC_EQUIV}

    loss_defs = [
        ('l_topk_only',        loss_l_topk_only),
        ('spearman',            loss_spearman),
        ('sign_agree',          loss_sign_agree),
        ('rescaled_ccc',        loss_rescaled_ccc),
        ('argmin_identity',     loss_argmin_identity),
        ('top1+top3_compound',  loss_top1_top3_compound),
    ]

    for sid, axis_label, axis, pbs, pbc, p in files:
        path = Path(p)
        if not path.exists():
            print(f'SKIP {p}'); continue
        with open(path) as f:
            d = json.load(f)
        cells = d['cells']
        vuln_cvd = np.array(d['vuln_cvd'])
        tmap = target_maps[sid]

        print(f'\n{"="*70}')
        print(f'sub-{sid} axis={axis_label} (θ_conf={d["theta_conf"]}°)')
        print(f'{"="*70}')

        # (a) Diagnostic
        diagnose_vuln_range(cells, vuln_cvd, pbs, pbc, axis_label)

        # (b) Each loss → argmin → P2a
        print(f'\n  Loss search — find argmin then evaluate P2a:')
        print(f'  P2a-max target: bs={pbs}, bc={pbc:+d}  P2a={p2a_cell(pbs, pbc, axis, tmap)[0]:.3f}')
        print(f'  {"loss":<20s}  {"argmin":<12s}  {"L_min":>6s}  {"P2a":>6s}  {"exact":>5s}  {"dist→P2amax":>10s}')

        for loss_name, loss_fn in loss_defs:
            # Evaluate every cell
            best_L = np.inf; best_cell = None
            tied = []
            for c in cells:
                sim = np.array(c['vuln_sim'])
                L_val = loss_fn(sim, vuln_cvd)
                if L_val < best_L - 1e-9:
                    best_L = L_val; best_cell = c; tied = [c]
                elif abs(L_val - best_L) < 1e-9:
                    tied.append(c)

            # If tied, pick smallest amplitude (informative deterministic choice)
            if len(tied) > 1:
                tied.sort(key=lambda cc: cc['bs']**2 + cc['bc']**2)
                best_cell = tied[0]

            bs, bc = best_cell['bs'], best_cell['bc']
            p2a, exact = p2a_cell(bs, bc, axis, tmap)
            dist = np.hypot(bs - pbs, bc - pbc)
            ntied = f'(tied={len(tied)})' if len(tied) > 1 else ''
            print(f'  {loss_name:<20s}  ({bs:>2.0f},{bc:+3.0f}) {ntied:<6s}  '
                  f'{best_L:>6.3f}  {p2a:>5.3f}  {exact:>3d}/8  {dist:>10.1f}')


if __name__ == '__main__':
    main()
