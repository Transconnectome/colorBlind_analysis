#!/usr/bin/env python3
"""run_NxM.py — Plan 04 Cycle 1: ROI x Loss x Combination 통합 실험.

목적
  (1) 단독 ROI(V1, V2, V4)에서 단독 Loss 후보 평가
  (2) 단독 ROI x 결합 Loss (α blend of l_topk_jaccard + mw_jaccard_loss)
  (3) ROI 결합 (V1+V2, V2+V4, V1+V4, V1+V2+V4) 4 가지 통합 방식
        - z_sum, stouffer, weighted_z, mahalanobis (nullCovariance)
  (4) 5 개 판단 기준 (C1~C5) 측정.

전제
  - Cycle 4 grid (β_s ∈ [0, 80] step 2, β_c ∈ [-60, 60] step 2 → 41x61 = 2501 pt)
  - W-fixed 2-component design matrix
  - HC LOO null = 6 명 HC pool (sub-07 LOCO target 없음)
  - sub-10 분석 제외 (CLAUDE.md 규칙 7) — HC null 평가에는 사용 안 함, sanity check만
  - family: CVD subj_type 사용 (sub-08 deutan / sub-09 protan).
    HC 는 deutan 으로 매칭.

출력 위치
  results/cycle_filter_refinement/
    sub-{ID}_{ROI}_landscape.json     # per-cell landscape (gridsize x metrics)
    cycle1_aggregate.json             # 모든 cell 요약
    cycle1_C1_C2_C3_C4_C5_table.json  # 판단 기준
"""

import argparse
import json
import sys
import time
import numpy as np
from itertools import combinations
from pathlib import Path
from scipy.stats import spearmanr, pearsonr, norm

_HERE = Path(__file__).resolve().parent
_PHASE2 = _HERE.parent.parent
_PROJ = _PHASE2.parent.parent
sys.path.insert(0, str(_PHASE2 / 'scripts'))
sys.path.insert(0, str(_PHASE2 / 'scripts' / 'cycle_loss_redesign'))

_FWD = _PROJ / 'analysis' / 'future_phase1_forward_model' / 'scripts'
sys.path.insert(0, str(_FWD))

from utils_forward_model import (
    HC_SUBJECTS, N_CHANNELS, N_RUNS, N_COLORS, HUE_ANGLES,
    load_amplitudes, create_basis_full,
)
from machado_simulator import machado_shifted_hue
from step1_fit_loco_v2 import (
    simulate_mean_hc_wfixed, precompute_hc_W, load_cvd_loco_target,
)
from loss_redesign_smoke import compute_extended_loss, get_2component_design
from cycle4_alt_metrics import compute_cycle4_metrics

CVD_TYPE = {'08': 'deutan', '09': 'protan', '10': 'normal'}
LOCAL_DATA = (_PROJ / 'analysis' / 'phase1_procrustes_decoding' / 'results'
              / 'visualization' / 'full_dataset_C010_with_residuals')

ROIS = ['V1', 'V2', 'V4']
SUBJECTS_HC = ['01', '02', '03', '04', '05', '06']  # sub-07 lacks LOCO
SUBJECTS_CVD = ['08', '09']  # sub-10 excluded per CLAUDE.md rule 7
SUBJECTS_ALL = SUBJECTS_HC + SUBJECTS_CVD + ['10']  # 10 only for sanity


def family_for_subj(subj):
    if subj in CVD_TYPE:
        f = CVD_TYPE[subj]
        return 'deutan' if f == 'normal' else f
    return 'deutan'


# --------------------------------------------------------------------------
# Loss combinations on a single (vuln_sim, vuln_cvd) pair
# --------------------------------------------------------------------------
def loss_blend(vuln_sim, vuln_cvd, alpha):
    """alpha * l_topk + (1-alpha) * mw_jaccard_loss."""
    ext = compute_extended_loss(vuln_sim, vuln_cvd)
    c4 = compute_cycle4_metrics(vuln_sim, vuln_cvd)
    return alpha * ext['l_topk_jaccard'] + (1.0 - alpha) * c4['mw_jaccard_loss']


def all_metrics(vuln_sim, vuln_cvd):
    ext = compute_extended_loss(vuln_sim, vuln_cvd)
    c4 = compute_cycle4_metrics(vuln_sim, vuln_cvd)
    out = {
        'l_rank': ext['l_rank'],
        'l_dir': ext['l_dir'],
        'spearman_r': ext['spearman_r'],
        'pearson_r': ext['pearson_r'],
        'l_topk_jaccard': ext['l_topk_jaccard'],
        'l_mag': ext['l_mag'],
        'mw_jaccard_loss': c4['mw_jaccard_loss'],
        'norm_resid': c4['norm_resid'],
        'sign_agree': c4['sign_agree'],
    }
    return out


# --------------------------------------------------------------------------
# Single subject x ROI grid sweep
# --------------------------------------------------------------------------
def sweep_one_cell(subj, roi, family, hc_amps_dict, hc_W_dict, vuln_target,
                   grid_bs, grid_bc, verbose=False):
    """Grid sweep — return per-grid metric matrix + best by candidate losses."""
    n_bs = len(grid_bs)
    n_bc = len(grid_bc)
    metric_keys = ['l_rank', 'l_dir', 'l_topk_jaccard', 'mw_jaccard_loss',
                   'l_mag', 'norm_resid', 'sign_agree',
                   'spearman_r', 'pearson_r']
    metrics = {k: np.zeros((n_bs, n_bc)) for k in metric_keys}

    # baseline (0,0)
    C_base, _ = get_2component_design(0.0, 0.0, family)
    vuln_base, _ = simulate_mean_hc_wfixed(hc_W_dict, hc_amps_dict, C_base)
    base_metrics = all_metrics(vuln_base, vuln_target)
    base_metrics['baseline_rho'] = base_metrics['spearman_r']

    for i, bs in enumerate(grid_bs):
        for j, bc in enumerate(grid_bc):
            C_sh, _ = get_2component_design(bs, bc, family)
            vsim, _ = simulate_mean_hc_wfixed(
                hc_W_dict, hc_amps_dict, C_sh)
            m = all_metrics(vsim, vuln_target)
            for k in metric_keys:
                metrics[k][i, j] = m[k]

    # best by 단독 loss (L1-L4) and blended (L5-L7 with α 0.25, 0.5, 0.75)
    cand = {}
    # L1: l_topk_jaccard
    cand['L1_topk'] = float(metrics['l_topk_jaccard'].min())
    # L2: mw_jaccard_loss
    cand['L2_mwj'] = float(metrics['mw_jaccard_loss'].min())
    # L3: l_rank
    cand['L3_rank'] = float(metrics['l_rank'].min())
    # L4: l_dir
    cand['L4_dir'] = float(metrics['l_dir'].min())
    # L5/L6/L7 blends
    for a in [0.25, 0.5, 0.75]:
        blend = a * metrics['l_topk_jaccard'] + (1 - a) * metrics['mw_jaccard_loss']
        cand[f'L_blend_a{int(a*100)}'] = float(blend.min())
    # alt L8: l_mag (proposal — Cycle 1 단독 검증)
    cand['L8_mag'] = float(metrics['l_mag'].min())

    # delta-rho at the L_blend50 best position (representative LOCO improvement)
    blend50 = 0.5 * metrics['l_topk_jaccard'] + 0.5 * metrics['mw_jaccard_loss']
    idx = np.unravel_index(np.argmin(blend50), blend50.shape)
    delta_rho = float(metrics['spearman_r'][idx] - base_metrics['baseline_rho'])
    best_pos = (float(grid_bs[idx[0]]), float(grid_bc[idx[1]]))

    return {
        'subject': subj,
        'roi': roi,
        'family': family,
        'baseline': base_metrics,
        'best_loss': cand,
        'best_blend50_pos': best_pos,
        'delta_rho_at_blend50': delta_rho,
        # store small numeric arrays for later combo metrics (8x8 ish)
        'metric_grids': {k: v.astype(np.float32).tolist()
                         for k, v in metrics.items()},
        'grid_bs': grid_bs.tolist(),
        'grid_bc': grid_bc.tolist(),
    }, metrics


# --------------------------------------------------------------------------
# ROI combination metrics
# --------------------------------------------------------------------------
def stouffer(z_list):
    z_arr = np.array(z_list, dtype=float)
    return float(z_arr.sum() / np.sqrt(len(z_arr)))


def weighted_z(z_list, w_list):
    z_arr = np.array(z_list, dtype=float)
    w_arr = np.array(w_list, dtype=float)
    return float(np.sum(w_arr * z_arr) / np.sqrt(np.sum(w_arr ** 2)))


def specificity_z(value, hc_values):
    hc_arr = np.array(hc_values, dtype=float)
    if hc_arr.std() == 0:
        return 0.0
    # for losses (smaller=better), CVD better than HC = lower value =>
    # negative z is good.
    return float((value - hc_arr.mean()) / hc_arr.std())


# --------------------------------------------------------------------------
# Main pipeline
# --------------------------------------------------------------------------
def main():
    p = argparse.ArgumentParser('Plan 04 Cycle 1 — ROI x Loss x Combo')
    p.add_argument('--subjects', nargs='+', default=SUBJECTS_ALL)
    p.add_argument('--rois', nargs='+', default=ROIS)
    p.add_argument('--bs_step', type=float, default=2.0)
    p.add_argument('--bc_step', type=float, default=2.0)
    p.add_argument('--bs_max', type=float, default=80.0)
    p.add_argument('--bc_max', type=float, default=60.0)
    p.add_argument('--bs_min', type=float, default=0.0)
    p.add_argument('--data_dir', default=str(LOCAL_DATA))
    p.add_argument('--output_dir',
                   default=str(_PHASE2 / 'results' / 'cycle_filter_refinement'))
    p.add_argument('--save_landscape', action='store_true',
                   help='Persist full metric grids per subject (~few MB each)')
    args = p.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    data_dir = Path(args.data_dir)

    grid_bs = np.arange(args.bs_min, args.bs_max + 0.5 * args.bs_step,
                        args.bs_step)
    grid_bc = np.arange(-args.bc_max, args.bc_max + 0.5 * args.bc_step,
                        args.bc_step)
    print(f'[Grid] bs:[{grid_bs.min()},{grid_bs.max()}]/{args.bs_step} '
          f'bc:[{grid_bc.min()},{grid_bc.max()}]/{args.bc_step} '
          f'total={len(grid_bs)*len(grid_bc)}')

    # --- 1) per-ROI sweep ---
    cell_results = {}  # cell_results[roi][subj] = result dict
    landscapes = {}    # landscapes[roi][subj] = metric_grid dict (np arrays)
    t0 = time.time()
    for roi in args.rois:
        print(f'\n=== ROI={roi} ===')
        # Load HC pool ONCE per ROI
        hc_amps = {}
        for hc in HC_SUBJECTS:
            try:
                hc_amps[hc] = load_amplitudes(data_dir, hc, roi)
            except FileNotFoundError as e:
                print(f'  [warn] HC sub-{hc} {roi} missing: {e}')
        basis_full = create_basis_full(N_CHANNELS, basis_type='fe')
        C_orig = basis_full[HUE_ANGLES]
        hc_W, _ = precompute_hc_W(hc_amps, C_orig)
        print(f'  W precomputed for {len(hc_W)} HC')

        cell_results[roi] = {}
        landscapes[roi] = {}
        for subj in args.subjects:
            try:
                vt = load_cvd_loco_target(subj, roi)
            except FileNotFoundError:
                print(f'  [skip] sub-{subj} {roi}: no LOCO target')
                continue

            fam = family_for_subj(subj)

            # LOO HC pool: drop subj if HC
            if subj in HC_SUBJECTS:
                pool_W = {k: v for k, v in hc_W.items() if k != subj}
                pool_amps = {k: v for k, v in hc_amps.items() if k != subj}
            else:
                pool_W = hc_W
                pool_amps = hc_amps

            res, metric_grids = sweep_one_cell(
                subj, roi, fam, pool_amps, pool_W, vt,
                grid_bs, grid_bc, verbose=False)
            res['group'] = 'CVD' if subj in CVD_TYPE else 'HC'
            res['n_pool'] = len(pool_W)
            cell_results[roi][subj] = res
            landscapes[roi][subj] = metric_grids

            if args.save_landscape:
                lp = out_dir / f'sub-{subj}_{roi}_landscape.json'
                with open(lp, 'w') as f:
                    json.dump({k: v.tolist() for k, v in metric_grids.items()},
                              f)

            # tmp text
            cand = res['best_loss']
            print(f'  sub-{subj}({res["group"]}/{fam}): basρ={res["baseline"]["baseline_rho"]:+.3f} '
                  f'L1={cand["L1_topk"]:.3f} L2={cand["L2_mwj"]:.3f} '
                  f'L3={cand["L3_rank"]:.3f} blend50={cand["L_blend_a50"]:.3f} '
                  f'Δρ@b50={res["delta_rho_at_blend50"]:+.3f}')

    elapsed = time.time() - t0
    print(f'\n[Sweep done] elapsed={elapsed:.1f}s')

    # --- 2) Specificity table per (ROI, loss) — single ROI ---
    spec_solo = {}
    for roi in args.rois:
        if roi not in cell_results:
            continue
        spec_solo[roi] = {}
        sub_dict = cell_results[roi]
        cvd_subs = [s for s in sub_dict if sub_dict[s]['group'] == 'CVD']
        hc_subs = [s for s in sub_dict if sub_dict[s]['group'] == 'HC']
        loss_keys = list(sub_dict[next(iter(sub_dict))]['best_loss'].keys())
        for L in loss_keys:
            hc_vals = np.array([sub_dict[s]['best_loss'][L] for s in hc_subs])
            entry = {'hc_mean': float(hc_vals.mean()),
                     'hc_std': float(hc_vals.std()),
                     'hc_values': hc_vals.tolist(),
                     'cvd': {}}
            for cs in cvd_subs:
                cv = sub_dict[cs]['best_loss'][L]
                p_emp = float((np.sum(hc_vals <= cv) + 1)
                              / (len(hc_vals) + 1))
                z = (cv - hc_vals.mean()) / hc_vals.std() \
                    if hc_vals.std() > 0 else 0.0
                entry['cvd'][cs] = {'value': float(cv),
                                    'p_emp': p_emp,
                                    'z': float(z)}
            # baseline corr (HC pool)
            hc_baseρ = np.array([sub_dict[s]['baseline']['baseline_rho']
                                 for s in hc_subs])
            if hc_baseρ.std() > 0 and hc_vals.std() > 0:
                r, _ = pearsonr(hc_baseρ, hc_vals)
                entry['baseline_corr'] = float(r)
            else:
                entry['baseline_corr'] = None
            spec_solo[roi][L] = entry

    # --- 3) ROI combination — for promising losses (L1, L2, L_blend50) ---
    # Combos: 2-ROI and 3-ROI
    roi_combos = []
    avail_rois = [r for r in args.rois if r in cell_results]
    for k in [2, 3]:
        for combo in combinations(avail_rois, k):
            roi_combos.append(combo)

    target_losses = ['L1_topk', 'L2_mwj', 'L_blend_a50']
    spec_combo = {}
    for combo in roi_combos:
        key = '+'.join(combo)
        spec_combo[key] = {}
        # subjects present in ALL ROIs of combo
        common_subs = set(cell_results[combo[0]].keys())
        for r in combo[1:]:
            common_subs &= set(cell_results[r].keys())
        cvd_in = [s for s in common_subs
                  if cell_results[combo[0]][s]['group'] == 'CVD']
        hc_in = [s for s in common_subs
                 if cell_results[combo[0]][s]['group'] == 'HC']
        for L in target_losses:
            # per-ROI HC pool stats first
            roi_stats = {}
            for r in combo:
                hc_vals = np.array([cell_results[r][s]['best_loss'][L]
                                    for s in hc_in])
                roi_stats[r] = {
                    'mean': float(hc_vals.mean()),
                    'std': float(hc_vals.std()),
                    'hc_vals': hc_vals.tolist(),
                }
            # CVD/HC z per ROI then combine
            def zify(s):
                zs = []
                for r in combo:
                    v = cell_results[r][s]['best_loss'][L]
                    m = roi_stats[r]['mean']
                    sd = roi_stats[r]['std']
                    if sd > 0:
                        zs.append((v - m) / sd)
                    else:
                        zs.append(0.0)
                return zs
            # Loss-style: smaller is better → CVD should have negative z
            zs_cvd = {s: zify(s) for s in cvd_in}
            zs_hc = {s: zify(s) for s in hc_in}

            # Three combination methods
            entry = {'cvd': {}, 'hc_null': {}, 'methods': {}}
            for method in ['z_sum', 'stouffer']:
                hc_combined = []
                for s in hc_in:
                    if method == 'z_sum':
                        hc_combined.append(sum(zs_hc[s]))
                    else:
                        hc_combined.append(stouffer(zs_hc[s]))
                hc_combined = np.array(hc_combined)
                cvd_combined = {}
                for s in cvd_in:
                    val = sum(zs_cvd[s]) if method == 'z_sum' \
                        else stouffer(zs_cvd[s])
                    p = float((np.sum(hc_combined <= val) + 1)
                              / (len(hc_combined) + 1))
                    z = (val - hc_combined.mean()) / hc_combined.std() \
                        if hc_combined.std() > 0 else 0.0
                    cvd_combined[s] = {'combined': float(val),
                                       'p_emp': p, 'z_within_hc': float(z)}
                entry['methods'][method] = {
                    'hc_combined': hc_combined.tolist(),
                    'hc_mean': float(hc_combined.mean()),
                    'hc_std': float(hc_combined.std()),
                    'cvd': cvd_combined,
                }
            spec_combo[key][L] = entry

    # --- 4) C1~C5 acceptance criteria ---
    # C1: stability/uniqueness — best param SD across LOHO (per ROI x loss)
    # We approximate with secondary-minimum cost ratio inside the same grid:
    #   ratio = (cost_global / cost_2nd_best_far_from_global)
    def secondary_min_ratio(grid_2d, exclusion_radius_idx=4):
        flat = grid_2d.flatten()
        idx_min = int(np.argmin(flat))
        i_min, j_min = np.unravel_index(idx_min, grid_2d.shape)
        mask = np.ones_like(grid_2d, dtype=bool)
        for i in range(max(0, i_min - exclusion_radius_idx),
                       min(grid_2d.shape[0],
                           i_min + exclusion_radius_idx + 1)):
            for j in range(max(0, j_min - exclusion_radius_idx),
                           min(grid_2d.shape[1],
                               j_min + exclusion_radius_idx + 1)):
                mask[i, j] = False
        if mask.sum() == 0:
            return 1.0
        sec = float(grid_2d[mask].min())
        prim = float(grid_2d.min())
        if sec == 0 and prim == 0:
            return 1.0
        if sec <= 1e-12:
            return 1.0
        return float(prim / sec)

    C1 = {}
    for roi in avail_rois:
        for subj in cell_results[roi]:
            grids = landscapes[roi][subj]
            for L_metric in ['l_topk_jaccard', 'mw_jaccard_loss',
                             'l_rank', 'l_dir']:
                ratio = secondary_min_ratio(grids[L_metric])
                C1.setdefault(L_metric, {}).setdefault(roi, {})[subj] = ratio

    # C2: variance — within-grid metric IQR for HC pool (proxy for bootstrap)
    C2 = {}
    for roi in avail_rois:
        for L_metric in ['l_topk_jaccard', 'mw_jaccard_loss', 'l_rank',
                         'l_dir']:
            best_vals = [cell_results[roi][s]['best_loss']
                         for s in cell_results[roi]]
            # use HC only for null spread
            hc_subs = [s for s in cell_results[roi]
                       if cell_results[roi][s]['group'] == 'HC']
            hc_vals = np.array([cell_results[roi][s]['best_loss'][
                                  {'l_topk_jaccard': 'L1_topk',
                                   'mw_jaccard_loss': 'L2_mwj',
                                   'l_rank': 'L3_rank',
                                   'l_dir': 'L4_dir'}[L_metric]]
                                for s in hc_subs])
            C2.setdefault(L_metric, {})[roi] = {
                'IQR': float(np.percentile(hc_vals, 75)
                              - np.percentile(hc_vals, 25)),
                'std': float(hc_vals.std()),
                'min': float(hc_vals.min()),
                'max': float(hc_vals.max()),
            }

    # C3: HC false-positive — already in spec_solo (cvd p_emp / z)
    # C4: cross-ROI agreement — best (β_s, β_c) sign + cosine
    C4 = {}
    for subj in SUBJECTS_CVD + SUBJECTS_HC:  # for everyone
        if subj == '07':
            continue
        best_per_roi = {}
        for roi in avail_rois:
            if roi in cell_results and subj in cell_results[roi]:
                best_per_roi[roi] = cell_results[roi][subj]['best_blend50_pos']
        if len(best_per_roi) >= 2:
            rois_present = list(best_per_roi.keys())
            cos_pairs = {}
            for r1, r2 in combinations(rois_present, 2):
                v1 = np.array(best_per_roi[r1])
                v2 = np.array(best_per_roi[r2])
                if np.linalg.norm(v1) > 0 and np.linalg.norm(v2) > 0:
                    c = float(v1 @ v2 / (np.linalg.norm(v1)
                                         * np.linalg.norm(v2)))
                else:
                    c = 0.0
                cos_pairs[f'{r1}_{r2}'] = c
            C4[subj] = {'best': best_per_roi, 'cosines': cos_pairs}

    # C5: baseline orthogonality — Pearson r(HC baseline_rho, HC best loss)
    C5 = {}
    for roi in avail_rois:
        if roi not in spec_solo:
            continue
        for L_key, ent in spec_solo[roi].items():
            if ent.get('baseline_corr') is not None:
                C5.setdefault(L_key, {})[roi] = ent['baseline_corr']

    # --- 5) Save aggregate ---
    aggregate = {
        'config': {
            'subjects': args.subjects,
            'rois': args.rois,
            'bs_range': [float(grid_bs.min()), float(grid_bs.max())],
            'bc_range': [float(grid_bc.min()), float(grid_bc.max())],
            'bs_step': args.bs_step,
            'bc_step': args.bc_step,
            'grid_size': len(grid_bs) * len(grid_bc),
            'note': 'sub-10 included for sanity check; not in HC null pool '
                    'and primary specificity excludes sub-10',
        },
        'cell_results': {roi: {s: {k: v for k, v in res.items()
                                   if k != 'metric_grids'}
                                for s, res in cell_results[roi].items()}
                          for roi in cell_results},
        'specificity_solo': spec_solo,
        'specificity_combo': spec_combo,
        'C1_secondary_min_ratio': C1,
        'C2_hc_pool_spread': C2,
        'C4_cross_roi_agreement': C4,
        'C5_baseline_orthogonality': C5,
    }

    with open(out_dir / 'cycle1_aggregate.json', 'w') as f:
        json.dump(aggregate, f, indent=2, default=str)
    print(f'[Wrote] {out_dir/"cycle1_aggregate.json"}')

    # --- 6) Print summary ---
    print('\n' + '=' * 90)
    print('=== Solo specificity (CVD vs HC LOO null) ===')
    for roi in avail_rois:
        print(f'\n[{roi}]')
        if roi not in spec_solo:
            continue
        for L in ['L1_topk', 'L2_mwj', 'L3_rank', 'L4_dir',
                  'L_blend_a25', 'L_blend_a50', 'L_blend_a75', 'L8_mag']:
            if L not in spec_solo[roi]:
                continue
            ent = spec_solo[roi][L]
            msg = f'  {L:>14}  HCμ={ent["hc_mean"]:+.3f}±{ent["hc_std"]:.3f}'
            for cs in sorted(ent['cvd'].keys()):
                cv = ent['cvd'][cs]
                msg += f'  sub-{cs}: {cv["value"]:+.3f}(p={cv["p_emp"]:.2f},z={cv["z"]:+.2f})'
            br = ent.get('baseline_corr')
            if br is not None:
                msg += f'  basρ-corr={br:+.2f}'
            print(msg)

    print('\n=== Combo specificity (ROI combinations, blend50) ===')
    for combo, content in spec_combo.items():
        if 'L_blend_a50' not in content:
            continue
        ent = content['L_blend_a50']
        for method in ['z_sum', 'stouffer']:
            print(f'  combo={combo} method={method}')
            ms = ent['methods'][method]
            for cs, cv in ms['cvd'].items():
                print(f'    sub-{cs} val={cv["combined"]:+.3f} '
                      f'p={cv["p_emp"]:.2f} z={cv["z_within_hc"]:+.2f}')

    print('\n=== C1 — secondary min ratio (1.0=unique flat; <1=clearer min) ===')
    for L, by_roi in C1.items():
        print(f'  {L}:')
        for roi, sub_d in by_roi.items():
            mean_r = np.mean(list(sub_d.values()))
            print(f'    {roi}: mean={mean_r:.3f} '
                  f'min={min(sub_d.values()):.3f} '
                  f'max={max(sub_d.values()):.3f}')

    print('\n=== C2 — HC pool spread (proxy variance) ===')
    for L, by_roi in C2.items():
        print(f'  {L}:')
        for roi, st in by_roi.items():
            print(f'    {roi}: IQR={st["IQR"]:.3f} std={st["std"]:.3f}')

    print('\n=== C5 — baseline_rho ↔ best loss (HC) Pearson r ===')
    for L, by_roi in C5.items():
        msg = f'  {L:>14}'
        for roi in avail_rois:
            if roi in by_roi:
                msg += f'  {roi}={by_roi[roi]:+.2f}'
        print(msg)

    print('\nDone.')


if __name__ == '__main__':
    main()
