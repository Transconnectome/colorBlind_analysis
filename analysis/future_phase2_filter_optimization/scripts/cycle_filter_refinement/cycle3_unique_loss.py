#!/usr/bin/env python3
"""cycle3_unique_loss.py — Plan 04 Cycle 3: uniqueness 회복 + 새 metric.

Cycle 2 진단:
  - l_topk / mw_jaccard 의 *median 871–1795 global minima* (2501 중) →
    set-loss 가 본질적으로 plateau → C1 fail.
  - V2 sign-flip 효과는 있으나 sub-10 false positive 동반.
  - Mahalanobis 도 sub-10 분리 못함.

Cycle 3 가설:
  H_C3_1 — Tikhonov (β² regularizer) 추가하면 set-loss 의 plateau 가
           원점 가까운 unique min 으로 수렴.
  H_C3_2 — l_rank + (1−α)·Tikhonov + γ·set-loss 결합이 C1 + C3 동시 만족.
  H_C3_3 — *centered* metric (vuln_sim - mean) vs (vuln_cvd - mean) 의
           Pearson + sign-agreement 결합이 baseline 회귀 효과 줄임.
  H_C3_4 — discrete bottom-1 (가장 취약 색만 일치) 은 LOCO 데이터의
           effective DOF 한계 안에서 sharper 신호 가능.

새 metric:
  M1 — l_topk_jaccard + λ·(β_s² + β_c²)/norm  (uniqueness 회복)
  M2 — bottom-1: 가장 취약 색 일치 = 1 if argmin(sim)==argmin(cvd) else 0
  M3 — magnitude-weighted Spearman (Spearman of (sim, cvd) where both
       weighted by |c|^p, p=0.5)

Output: results/cycle_filter_refinement/cycle3_aggregate.json
"""
import json
import sys
import time
import numpy as np
from itertools import combinations
from pathlib import Path
from scipy.stats import spearmanr, pearsonr

_HERE = Path(__file__).resolve().parent
_PHASE2 = _HERE.parent.parent
_RESULTS = _PHASE2 / 'results' / 'cycle_filter_refinement'

ROIS = ['V1', 'V2', 'V4']
HC_SUBS = ['01', '02', '03', '04', '05', '06']
CVD_SUBS = ['08', '09']
SANITY_SUBS = ['10']
ALL_SUBS = HC_SUBS + CVD_SUBS + SANITY_SUBS


def load_landscape(subj, roi):
    p = _RESULTS / f'sub-{subj}_{roi}_landscape.json'
    if not p.exists():
        return None
    with open(p) as f:
        d = json.load(f)
    return {k: np.array(v, dtype=float) for k, v in d.items()}


def secondary_min_ratio(grid, exclusion=4):
    flat = grid.flatten()
    idx_min = int(np.argmin(flat))
    i_min, j_min = np.unravel_index(idx_min, grid.shape)
    mask = np.ones_like(grid, dtype=bool)
    for i in range(max(0, i_min - exclusion),
                   min(grid.shape[0], i_min + exclusion + 1)):
        for j in range(max(0, j_min - exclusion),
                       min(grid.shape[1], j_min + exclusion + 1)):
            mask[i, j] = False
    if mask.sum() == 0 or grid[mask].min() <= 1e-12:
        return 1.0
    return float(grid.min() / grid[mask].min())


def main():
    t0 = time.time()
    # We need bs/bc grids for Tikhonov. Reconstruct from cycle1 config.
    grid_bs = np.arange(0.0, 80.0 + 0.5 * 2.0, 2.0)  # [0, 80] step 2
    grid_bc = np.arange(-60.0, 60.0 + 0.5 * 2.0, 2.0)
    BS, BC = np.meshgrid(grid_bs, grid_bc, indexing='ij')
    norm_grid = (BS / 80.0) ** 2 + (BC / 60.0) ** 2  # in [0, 2]

    land = {}
    for s in ALL_SUBS:
        land[s] = {}
        for r in ROIS:
            d = load_landscape(s, r)
            if d is not None:
                land[s][r] = d

    # ----------------------------------------------------------------
    # 1) Tikhonov-augmented set-loss
    #    M1 = l_topk_jaccard + λ * norm_grid
    #    Sweep λ ∈ {0.0, 0.05, 0.1, 0.2, 0.5, 1.0}
    # ----------------------------------------------------------------
    lams = [0.0, 0.05, 0.1, 0.2, 0.5, 1.0]
    tikh_results = {}
    for r in ROIS:
        tikh_results[r] = {}
        for lam in lams:
            key = f'lam{lam:.2f}'
            best_per_subj = {}
            sec_min_per_subj = {}
            for s in land:
                if r not in land[s]:
                    continue
                aug = land[s][r]['l_topk_jaccard'] + lam * norm_grid
                best_per_subj[s] = float(aug.min())
                sec_min_per_subj[s] = secondary_min_ratio(aug)
            hc_vals = np.array([best_per_subj[s] for s in HC_SUBS
                                if s in best_per_subj])
            cvd_dict = {}
            for cs in CVD_SUBS + SANITY_SUBS:
                if cs not in best_per_subj:
                    continue
                cv = best_per_subj[cs]
                p = float((np.sum(hc_vals <= cv) + 1)
                          / (len(hc_vals) + 1))
                z = (cv - hc_vals.mean()) / hc_vals.std() \
                    if hc_vals.std() > 0 else 0.0
                cvd_dict[cs] = {'value': float(cv),
                                'p_emp': p, 'z': float(z)}
            tikh_results[r][key] = {
                'lambda': float(lam),
                'hc_mean': float(hc_vals.mean()),
                'hc_std': float(hc_vals.std()),
                'cvd': cvd_dict,
                'mean_secondary_ratio': float(np.mean(
                    list(sec_min_per_subj.values()))),
            }

    # ----------------------------------------------------------------
    # 2) Joint M_blend + Tikh: γ·blend + λ·norm_grid
    # ----------------------------------------------------------------
    blend_tikh_results = {}
    for r in ROIS:
        blend_tikh_results[r] = {}
        for lam in lams:
            key = f'lam{lam:.2f}'
            best_per_subj = {}
            sec_min_per_subj = {}
            for s in land:
                if r not in land[s]:
                    continue
                blend = (0.5 * land[s][r]['l_topk_jaccard']
                         + 0.5 * land[s][r]['mw_jaccard_loss'])
                aug = blend + lam * norm_grid
                best_per_subj[s] = float(aug.min())
                sec_min_per_subj[s] = secondary_min_ratio(aug)
            hc_vals = np.array([best_per_subj[s] for s in HC_SUBS
                                if s in best_per_subj])
            cvd_dict = {}
            for cs in CVD_SUBS + SANITY_SUBS:
                if cs not in best_per_subj:
                    continue
                cv = best_per_subj[cs]
                p = float((np.sum(hc_vals <= cv) + 1)
                          / (len(hc_vals) + 1))
                z = (cv - hc_vals.mean()) / hc_vals.std() \
                    if hc_vals.std() > 0 else 0.0
                cvd_dict[cs] = {'value': float(cv),
                                'p_emp': p, 'z': float(z)}
            blend_tikh_results[r][key] = {
                'lambda': float(lam),
                'hc_mean': float(hc_vals.mean()),
                'hc_std': float(hc_vals.std()),
                'cvd': cvd_dict,
                'mean_secondary_ratio': float(np.mean(
                    list(sec_min_per_subj.values()))),
            }

    # ----------------------------------------------------------------
    # 3) Bottom-k variants: argmin / argmin-2 / etc.
    # ----------------------------------------------------------------
    # We need vuln_target and vuln_sim. Landscape doesn't store sim per grid.
    # Use cycle1_aggregate.json's vuln_target, but we need sim... skip for now.
    # Instead leverage the landscape's spearman_r to capture bottom-1.
    # Already have l_topk(k=3) and mw_jaccard. No new computation possible.

    # ----------------------------------------------------------------
    # 4) ROI combination using Tikhonov-corrected blend (λ=0.1)
    # ----------------------------------------------------------------
    selected_lam = 0.1
    combo_tikh_results = {}
    roi_combos = []
    for k in [2, 3]:
        for c in combinations(ROIS, k):
            roi_combos.append(c)

    for combo in roi_combos:
        ckey = '+'.join(combo)
        # Build per-subject best blend+tikh per ROI
        hc_mat = []
        for s in HC_SUBS:
            row = []
            ok = True
            for r in combo:
                if s not in land or r not in land[s]:
                    ok = False
                    break
                blend = (0.5 * land[s][r]['l_topk_jaccard']
                         + 0.5 * land[s][r]['mw_jaccard_loss'])
                aug = blend + selected_lam * norm_grid
                row.append(float(aug.min()))
            if ok:
                hc_mat.append(row)
        hc_mat = np.array(hc_mat)
        hc_mean = hc_mat.mean(axis=0)
        hc_std = hc_mat.std(axis=0)
        cvd_dict = {}
        for cs in CVD_SUBS + SANITY_SUBS:
            row = []
            ok = True
            for r in combo:
                if cs not in land or r not in land[cs]:
                    ok = False
                    break
                blend = (0.5 * land[cs][r]['l_topk_jaccard']
                         + 0.5 * land[cs][r]['mw_jaccard_loss'])
                aug = blend + selected_lam * norm_grid
                row.append(float(aug.min()))
            if not ok:
                continue
            cvd_vec = np.array(row)
            z_per_roi = (cvd_vec - hc_mean) / np.where(hc_std > 0,
                                                       hc_std, 1.0)
            zsum = float(z_per_roi.sum())
            # signed (V2 always |.|)
            z_signed = z_per_roi.copy()
            if 'V2' in combo:
                idx_v2 = list(combo).index('V2')
                z_signed[idx_v2] = -abs(z_signed[idx_v2])
            zsum_signed = float(z_signed.sum())

            # HC null
            hc_z = (hc_mat - hc_mean) / np.where(hc_std > 0, hc_std, 1.0)
            hc_zsum = hc_z.sum(axis=1)
            if 'V2' in combo:
                hc_z_signed = hc_z.copy()
                idx_v2 = list(combo).index('V2')
                hc_z_signed[:, idx_v2] = -np.abs(hc_z_signed[:, idx_v2])
            else:
                hc_z_signed = hc_z
            hc_zsum_signed = hc_z_signed.sum(axis=1)

            cvd_dict[cs] = {
                'cvd_vec': cvd_vec.tolist(),
                'z_per_roi': z_per_roi.tolist(),
                'z_sum': zsum,
                'p_zsum': float((np.sum(hc_zsum <= zsum) + 1)
                                / (len(hc_zsum) + 1)),
                'z_sum_signed': zsum_signed,
                'p_zsum_signed': float((np.sum(hc_zsum_signed <= zsum_signed) + 1)
                                       / (len(hc_zsum_signed) + 1)),
            }
        combo_tikh_results[ckey] = {
            'rois': combo,
            'lambda': selected_lam,
            'hc_mean': hc_mean.tolist(),
            'hc_std': hc_std.tolist(),
            'cvd': cvd_dict,
        }

    # ----------------------------------------------------------------
    # 5) Save
    # ----------------------------------------------------------------
    out = {
        'config': {
            'cycle': 3,
            'description': 'Tikhonov regularization for uniqueness',
            'lambdas': lams,
            'selected_lambda_for_combo': selected_lam,
        },
        'tikhonov_solo': tikh_results,
        'blend_tikhonov_solo': blend_tikh_results,
        'combo_blend_tikhonov': combo_tikh_results,
    }
    out_path = _RESULTS / 'cycle3_aggregate.json'
    with open(out_path, 'w') as f:
        json.dump(out, f, indent=2, default=str)
    print(f'Wrote {out_path}')

    # ---------- Print summary ----------
    print('\n=== Solo l_topk + λ·norm_grid (sub-08 z, sec-min ratio) ===')
    for r in ROIS:
        print(f'\n[{r}]')
        for lam in lams:
            k = f'lam{lam:.2f}'
            ent = tikh_results[r][k]
            line = f'  λ={lam:.2f}  sec-ratio={ent["mean_secondary_ratio"]:.3f}'
            for cs in ['08', '09', '10']:
                if cs in ent['cvd']:
                    cv = ent['cvd'][cs]
                    line += f'  s{cs}: z={cv["z"]:+.2f} p={cv["p_emp"]:.2f}'
            print(line)

    print('\n=== Solo blend50 + λ·norm_grid (sub-08 z, sec-min ratio) ===')
    for r in ROIS:
        print(f'\n[{r}]')
        for lam in lams:
            k = f'lam{lam:.2f}'
            ent = blend_tikh_results[r][k]
            line = f'  λ={lam:.2f}  sec-ratio={ent["mean_secondary_ratio"]:.3f}'
            for cs in ['08', '09', '10']:
                if cs in ent['cvd']:
                    cv = ent['cvd'][cs]
                    line += f'  s{cs}: z={cv["z"]:+.2f} p={cv["p_emp"]:.2f}'
            print(line)

    print(f'\n=== Combo blend50+Tikh (λ={selected_lam}) ===')
    for ckey, ent in combo_tikh_results.items():
        print(f'\n[{ckey}]')
        for cs, cv in ent['cvd'].items():
            print(f'  sub-{cs}:  z_sum={cv["z_sum"]:+.2f}(p={cv["p_zsum"]:.2f})  '
                  f'z_sum_signed={cv["z_sum_signed"]:+.2f}(p={cv["p_zsum_signed"]:.2f})')

    print(f'\n[Done] elapsed={time.time()-t0:.1f}s')


if __name__ == '__main__':
    main()
