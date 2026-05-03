#!/usr/bin/env python3
"""cycle5_c8drop.py — Plan 04 Cycle 5 Task 1: c8-drop diagnostic.

가설:
  sub-09 specificity 부재가 c8 magenta 단독 anti-prediction 때문일 가능성.
  MEMORY (Task #21): V1 z=-5.59, hV4 z=-3.23, V2 z=-5.38 — c8 drop 시
  V1 ρ=+0.54, hV4 ρ=+0.21 회복.

설계:
  - cycle1 landscape 의 grid 정의 (β_s ∈ [0,80] step 2, β_c ∈ [-60,60] step 2)
    재사용. 단 vuln_sim/vuln_cvd 모두 c8(index=7) 제거 후 7-color 로 loss 재계산.
  - ROI: V1, V2, V4. all subjects (HC 6 + CVD 2 + sub-10 sanity).
  - HC LOO-pool: subj 가 HC 면 자기 자신 제외.
  - Loss: l_topk_jaccard (k=3, 7-color 위에서), mw_jaccard_loss, l_rank, l_dir.
  - Tikhonov: λ=0.2 (cycle3 추천 단독 V4 best λ).

출력:
  results/cycles/cycle5_c8drop_aggregate.json
  - sub-08, sub-09, sub-10 각 ROI 의 z, p_emp (8-color vs 7-color 비교)
  - baseline_rho 8 vs 7
  - HC null 분포

CLAUDE.md 규칙 7: sub-10 분석 제외; 단 sanity 만.
"""

import json
import sys
import time
import numpy as np
from pathlib import Path
from scipy.stats import spearmanr, pearsonr

_HERE = Path(__file__).resolve().parent
_PHASE2 = _HERE.parent.parent
_PROJ = _PHASE2.parent.parent
sys.path.insert(0, str(_PHASE2 / 'scripts'))
sys.path.insert(0, str(_PHASE2 / 'scripts' / 'older_cycles/cycle_loss_redesign'))

_FWD = _PROJ / 'analysis' / 'future_phase1_forward_model' / 'scripts'
sys.path.insert(0, str(_FWD))

from utils_forward_model import (
    HC_SUBJECTS, N_CHANNELS, N_RUNS, N_COLORS, HUE_ANGLES,
    load_amplitudes, create_basis_full,
)
from step1_fit_loco_v2 import (
    simulate_mean_hc_wfixed, precompute_hc_W, load_cvd_loco_target,
)
from loss_redesign_smoke import get_2component_design

CVD_TYPE = {'08': 'deutan', '09': 'protan', '10': 'normal'}
LOCAL_DATA = (_PROJ / 'analysis' / 'phase1_procrustes_decoding' / 'results'
              / 'visualization' / 'full_dataset_C010_with_residuals')

ROIS = ['V1', 'V2', 'V4']
HC_SUBS = ['01', '02', '03', '04', '05', '06']
CVD_SUBS = ['08', '09']
SANITY_SUBS = ['10']
ALL_SUBS = HC_SUBS + CVD_SUBS + SANITY_SUBS


# --------------------------------------------------------------------------
# Loss helpers (replicate compute_extended_loss + cycle4_metrics for arbitrary
# color subset)
# --------------------------------------------------------------------------
def compute_losses_subset(vuln_sim, vuln_cvd, k=3):
    """Restricted-to-subset loss values (l_topk, mw_jaccard, l_rank, l_dir,
    spearman_r). Inputs are ALREADY sliced to the desired subset (length n).
    """
    s = np.asarray(vuln_sim, dtype=float)
    c = np.asarray(vuln_cvd, dtype=float)
    n = len(s)
    k_use = min(k, n - 1)  # ensure at least 1 left out

    # l_rank, l_dir, spearman_r
    rho, _ = spearmanr(s, c)
    rho = float(rho) if np.isfinite(rho) else 0.0
    if np.std(s) > 0 and np.std(c) > 0:
        rp, _ = pearsonr(s, c)
        rp = float(rp) if np.isfinite(rp) else 0.0
    else:
        rp = 0.0

    # l_topk_jaccard (k_use most-vulnerable = lowest)
    top_s = set(np.argsort(s)[:k_use].tolist())
    top_c = set(np.argsort(c)[:k_use].tolist())
    inter = len(top_s & top_c)
    union = len(top_s | top_c)
    l_topk = (1.0 - inter / union) if union > 0 else 1.0

    # mw_jaccard (depth-weighted, replicate cycle4 definition)
    top_c_idx = np.argsort(c)[:k_use]
    top_s_idx = np.argsort(s)[:k_use]
    intersect = np.intersect1d(top_c_idx, top_s_idx)
    w_c = np.maximum(-c[top_c_idx], 0.0)
    if w_c.sum() > 0:
        num = float(sum(max(-c[idx], 0.0) for idx in intersect))
        mw_j = num / float(w_c.sum())
    else:
        inter_n = len(set(top_c_idx) & set(top_s_idx))
        union_n = len(set(top_c_idx) | set(top_s_idx))
        mw_j = inter_n / union_n if union_n > 0 else 0.0
    mw_j_loss = 1.0 - mw_j

    return {
        'l_topk_jaccard': l_topk,
        'mw_jaccard_loss': mw_j_loss,
        'l_rank': 1.0 - rho,
        'l_dir': 1.0 - rp,
        'spearman_r': rho,
        'pearson_r': rp,
        'k_used': k_use,
        'n_colors': n,
    }


def family_for_subj(s):
    if s in CVD_TYPE:
        f = CVD_TYPE[s]
        return 'deutan' if f == 'normal' else f
    return 'deutan'


# --------------------------------------------------------------------------
# Per-subject grid sweep — record full landscape for both 8-col and 7-col
# --------------------------------------------------------------------------
def sweep_subject(subj, roi, family, pool_W, pool_amps, vuln_target,
                  grid_bs, grid_bc, drop_idx=7):
    """Return per-grid metric arrays for both 8-color and 7-color (drop c8)."""
    n_bs, n_bc = len(grid_bs), len(grid_bc)
    keys = ['l_topk_jaccard', 'mw_jaccard_loss', 'l_rank', 'l_dir', 'spearman_r']
    g8 = {k: np.zeros((n_bs, n_bc)) for k in keys}
    g7 = {k: np.zeros((n_bs, n_bc)) for k in keys}

    keep_idx = [i for i in range(N_COLORS) if i != drop_idx]
    vuln_target_7 = vuln_target[keep_idx]

    # baseline
    C_base, _ = get_2component_design(0.0, 0.0, family)
    vuln_base, _ = simulate_mean_hc_wfixed(pool_W, pool_amps, C_base)
    base_8 = compute_losses_subset(vuln_base, vuln_target)
    base_7 = compute_losses_subset(vuln_base[keep_idx], vuln_target_7)

    for i, bs in enumerate(grid_bs):
        for j, bc in enumerate(grid_bc):
            C_sh, _ = get_2component_design(bs, bc, family)
            vsim, _ = simulate_mean_hc_wfixed(pool_W, pool_amps, C_sh)
            m8 = compute_losses_subset(vsim, vuln_target)
            m7 = compute_losses_subset(vsim[keep_idx], vuln_target_7)
            for k in keys:
                g8[k][i, j] = m8[k]
                g7[k][i, j] = m7[k]
    return {
        'grid_8color': g8,
        'grid_7color': g7,
        'baseline_8color': base_8,
        'baseline_7color': base_7,
        'vuln_target': vuln_target.tolist(),
        'vuln_baseline': vuln_base.tolist(),
    }


def main():
    out_dir = _PHASE2 / 'results' / 'cycles'
    out_dir.mkdir(parents=True, exist_ok=True)
    data_dir = Path(LOCAL_DATA)

    grid_bs = np.arange(0.0, 80.0 + 1e-6, 2.0)
    grid_bc = np.arange(-60.0, 60.0 + 1e-6, 2.0)
    BS, BC = np.meshgrid(grid_bs, grid_bc, indexing='ij')
    norm_grid = (BS / 80.0) ** 2 + (BC / 60.0) ** 2
    LAM_TIKH = 0.2  # cycle 3 best for V4 single
    print(f'[Grid] {len(grid_bs)}x{len(grid_bc)}={len(grid_bs)*len(grid_bc)} '
          f'  λ_tikh={LAM_TIKH}')

    aggregate = {
        'config': {
            'cycle': 5,
            'task': 'c8_drop_diagnostic',
            'drop_color_idx': 7,
            'drop_color_name': 'magenta (color_8 / c8)',
            'lam_tikh': LAM_TIKH,
            'k_topk_8color': 3,
            'k_topk_7color': 3,
            'note': 'k=3 retained for both 8/7 — set match 3 of n.',
        },
        'per_subject': {},
        'specificity_per_roi': {},
    }

    t0 = time.time()
    for roi in ROIS:
        print(f'\n=== ROI = {roi} ===')
        # HC pool
        hc_amps = {}
        for hc in HC_SUBJECTS:
            try:
                hc_amps[hc] = load_amplitudes(data_dir, hc, roi)
            except FileNotFoundError as e:
                print(f'  [warn] HC sub-{hc}: {e}')
        basis_full = create_basis_full(N_CHANNELS, basis_type='fe')
        C_orig = basis_full[HUE_ANGLES]
        full_W, _ = precompute_hc_W(hc_amps, C_orig)

        roi_record = {}
        for subj in ALL_SUBS:
            try:
                vt = load_cvd_loco_target(subj, roi)
            except FileNotFoundError:
                print(f'  [skip] sub-{subj} {roi}: no LOCO target')
                continue
            fam = family_for_subj(subj)
            if subj in HC_SUBJECTS:
                pool_W = {k: v for k, v in full_W.items() if k != subj}
                pool_amps = {k: v for k, v in hc_amps.items() if k != subj}
            else:
                pool_W = full_W
                pool_amps = hc_amps
            res = sweep_subject(subj, roi, fam, pool_W, pool_amps, vt,
                                grid_bs, grid_bc, drop_idx=7)
            res['subject'] = subj
            res['family'] = fam
            res['roi'] = roi
            res['group'] = 'CVD' if subj in CVD_TYPE else 'HC'

            # Apply Tikh + extract best per metric, both 8 and 7
            best_summary = {}
            for col_tag, gd, base in [('8color', res['grid_8color'], res['baseline_8color']),
                                       ('7color', res['grid_7color'], res['baseline_7color'])]:
                # l_topk + Tikh
                aug_topk = gd['l_topk_jaccard'] + LAM_TIKH * norm_grid
                idx_t = np.unravel_index(np.argmin(aug_topk), aug_topk.shape)
                best_summary[col_tag] = {
                    'baseline_rho': float(base['spearman_r']),
                    'best_l_topk_tikh': float(aug_topk.min()),
                    'best_l_topk_raw': float(gd['l_topk_jaccard'].min()),
                    'best_mw_jaccard_loss': float(gd['mw_jaccard_loss'].min()),
                    'best_l_rank': float(gd['l_rank'].min()),
                    'best_l_dir': float(gd['l_dir'].min()),
                    'best_pos_topk_tikh': [float(grid_bs[idx_t[0]]),
                                            float(grid_bc[idx_t[1]])],
                    'rho_at_best_topk_tikh': float(gd['spearman_r'][idx_t]),
                }
            res['summary'] = best_summary
            roi_record[subj] = res
            print(f'  sub-{subj}({res["group"]}/{fam}) '
                  f'8col: ρ_base={best_summary["8color"]["baseline_rho"]:+.3f} '
                  f'topk_tikh={best_summary["8color"]["best_l_topk_tikh"]:.3f} | '
                  f'7col: ρ_base={best_summary["7color"]["baseline_rho"]:+.3f} '
                  f'topk_tikh={best_summary["7color"]["best_l_topk_tikh"]:.3f}')

        aggregate['per_subject'][roi] = {
            s: {kk: vv for kk, vv in r.items()
                if kk not in ('grid_8color', 'grid_7color')}
            for s, r in roi_record.items()
        }

        # ---- specificity per ROI per metric per col_tag ----
        spec_roi = {}
        for col_tag in ('8color', '7color'):
            spec_col = {}
            for metric in ('best_l_topk_tikh', 'best_l_topk_raw',
                            'best_mw_jaccard_loss', 'best_l_rank', 'best_l_dir'):
                hc_vals = np.array([
                    roi_record[s]['summary'][col_tag][metric]
                    for s in HC_SUBS if s in roi_record])
                cvd_dict = {}
                for cs in CVD_SUBS + SANITY_SUBS:
                    if cs not in roi_record:
                        continue
                    cv = roi_record[cs]['summary'][col_tag][metric]
                    p = float((np.sum(hc_vals <= cv) + 1)
                              / (len(hc_vals) + 1))
                    z = (cv - hc_vals.mean()) / hc_vals.std() \
                        if hc_vals.std() > 0 else 0.0
                    cvd_dict[cs] = {'value': float(cv),
                                    'p_emp': p, 'z': float(z)}
                spec_col[metric] = {
                    'hc_mean': float(hc_vals.mean()),
                    'hc_std': float(hc_vals.std()),
                    'hc_values': hc_vals.tolist(),
                    'cvd': cvd_dict,
                }
            spec_roi[col_tag] = spec_col
        aggregate['specificity_per_roi'][roi] = spec_roi

    # ---- Save ----
    out_path = out_dir / 'cycle5_c8drop_aggregate.json'
    with open(out_path, 'w') as f:
        json.dump(aggregate, f, indent=2, default=str)
    print(f'\n[Wrote] {out_path}')
    print(f'[Done] elapsed={time.time()-t0:.1f}s')

    # ---- Print summary table ----
    print('\n' + '=' * 100)
    print('=== c8-drop summary (l_topk + Tikh λ=0.2) ===')
    for roi in ROIS:
        if roi not in aggregate['specificity_per_roi']:
            continue
        spec = aggregate['specificity_per_roi'][roi]
        print(f'\n[{roi}]')
        for col_tag in ('8color', '7color'):
            ent = spec[col_tag]['best_l_topk_tikh']
            print(f'  {col_tag}: HCμ={ent["hc_mean"]:+.3f}±{ent["hc_std"]:.3f}')
            for cs in ('08', '09', '10'):
                if cs in ent['cvd']:
                    cv = ent['cvd'][cs]
                    print(f'     sub-{cs}: val={cv["value"]:.3f} '
                          f'z={cv["z"]:+.3f} p={cv["p_emp"]:.3f}')

    # baseline rho table
    print('\n=== baseline_rho per subject (8-color vs 7-color) ===')
    for roi in ROIS:
        if roi not in aggregate['per_subject']:
            continue
        print(f'\n[{roi}]')
        for s in ALL_SUBS:
            if s not in aggregate['per_subject'][roi]:
                continue
            r8 = aggregate['per_subject'][roi][s]['summary']['8color']['baseline_rho']
            r7 = aggregate['per_subject'][roi][s]['summary']['7color']['baseline_rho']
            grp = aggregate['per_subject'][roi][s]['group']
            print(f'  sub-{s}({grp}): ρ_8={r8:+.3f} → ρ_7={r7:+.3f}  Δ={r7-r8:+.3f}')


if __name__ == '__main__':
    main()
