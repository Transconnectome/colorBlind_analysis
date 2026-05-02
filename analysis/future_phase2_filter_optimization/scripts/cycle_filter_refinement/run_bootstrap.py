#!/usr/bin/env python3
"""run_bootstrap.py — Plan 04 Cycle 4 (deferred): HC bootstrap variance.

목적
  - 단일 (subj, roi) cell 에 대해 HC 6명 resample (n_boot)
  - 매 boot 에서 mean_HC 재계산 → metric grid 재계산 → best loss + best (β_s,β_c)
  - 분포 IQR / median / 95% CI 산출
  - C2 (variance) 정량화

Output: results/cycle_filter_refinement/bootstrap/sub-{ID}_{ROI}.json

서버 실행 (CPU heavy):
  conda activate nilearn
  --nodelist=node2 --mem=16G --cpus-per-task=4
"""
import argparse
import json
import sys
import time
from pathlib import Path
import numpy as np

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
from step1_fit_loco_v2 import (
    simulate_mean_hc_wfixed, precompute_hc_W, load_cvd_loco_target,
)
from loss_redesign_smoke import compute_extended_loss, get_2component_design
from cycle4_alt_metrics import compute_cycle4_metrics

CVD_TYPE = {'08': 'deutan', '09': 'protan', '10': 'normal'}
LOCAL_DATA = (_PROJ / 'analysis' / 'phase1_procrustes_decoding' / 'results'
              / 'visualization' / 'full_dataset_C010_with_residuals')


def family_for_subj(s):
    if s in CVD_TYPE:
        f = CVD_TYPE[s]
        return 'deutan' if f == 'normal' else f
    return 'deutan'


def evaluate_grid_metrics(pool_W, pool_amps, vuln_target, family,
                          grid_bs, grid_bc, lam_tikh=0.0):
    """Sweep grid, return per-grid metric arrays + best l_topk + best blend50."""
    n_bs, n_bc = len(grid_bs), len(grid_bc)
    BS, BC = np.meshgrid(grid_bs, grid_bc, indexing='ij')
    norm_grid = (BS / 80.0) ** 2 + (BC / 60.0) ** 2

    g_topk = np.zeros((n_bs, n_bc))
    g_mwj = np.zeros((n_bs, n_bc))
    g_rho = np.zeros((n_bs, n_bc))
    for i, bs in enumerate(grid_bs):
        for j, bc in enumerate(grid_bc):
            C, _ = get_2component_design(bs, bc, family)
            vsim, _ = simulate_mean_hc_wfixed(pool_W, pool_amps, C)
            ext = compute_extended_loss(vsim, vuln_target)
            c4 = compute_cycle4_metrics(vsim, vuln_target)
            g_topk[i, j] = ext['l_topk_jaccard']
            g_mwj[i, j] = c4['mw_jaccard_loss']
            g_rho[i, j] = ext['spearman_r']
    blend50 = 0.5 * g_topk + 0.5 * g_mwj
    aug = blend50 + lam_tikh * norm_grid
    aug_topk = g_topk + lam_tikh * norm_grid

    out = {}
    out['l_topk'] = float(g_topk.min())
    out['mw_jaccard'] = float(g_mwj.min())
    out['blend50'] = float(blend50.min())
    out['blend50_tikh'] = float(aug.min())
    out['topk_tikh'] = float(aug_topk.min())
    # Best (bs, bc) under blend50_tikh
    idx = np.unravel_index(int(np.argmin(aug)), aug.shape)
    out['best_bs'] = float(grid_bs[idx[0]])
    out['best_bc'] = float(grid_bc[idx[1]])
    out['rho_at_best'] = float(g_rho[idx])
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--subject', required=True)
    p.add_argument('--roi', required=True)
    p.add_argument('--n_boot', type=int, default=200)
    p.add_argument('--bs_step', type=float, default=4.0)  # 더 거친 grid (속도)
    p.add_argument('--bc_step', type=float, default=4.0)
    p.add_argument('--bs_max', type=float, default=80.0)
    p.add_argument('--bc_max', type=float, default=60.0)
    p.add_argument('--lam_tikh', type=float, default=0.1)
    p.add_argument('--data_dir', default=str(LOCAL_DATA))
    p.add_argument('--output_dir',
                   default=str(_PHASE2 / 'results'
                                / 'cycle_filter_refinement' / 'bootstrap'))
    p.add_argument('--seed', type=int, default=42)
    args = p.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(args.seed)

    grid_bs = np.arange(0.0, args.bs_max + 0.5 * args.bs_step, args.bs_step)
    grid_bc = np.arange(-args.bc_max, args.bc_max + 0.5 * args.bc_step,
                        args.bc_step)
    print(f'[Bootstrap] subj={args.subject} roi={args.roi} '
          f'n_boot={args.n_boot} grid={len(grid_bs)*len(grid_bc)}')

    data_dir = Path(args.data_dir)
    fam = family_for_subj(args.subject)

    # Load all HC amps (sub-07 OK if exists for amps; LOCO target 별도)
    hc_amps = {}
    for hc in HC_SUBJECTS:
        try:
            hc_amps[hc] = load_amplitudes(data_dir, hc, args.roi)
        except FileNotFoundError as e:
            print(f'[warn] HC sub-{hc}: {e}')

    # Vuln target
    try:
        vuln_target = load_cvd_loco_target(args.subject, args.roi)
    except FileNotFoundError as e:
        print(f'[skip] {args.subject} {args.roi} missing target: {e}')
        sys.exit(1)

    # Determine pool source per HC LOO if subj is HC
    if args.subject in HC_SUBJECTS:
        full_amps = {k: v for k, v in hc_amps.items() if k != args.subject}
    else:
        full_amps = hc_amps
    hc_subs = list(full_amps.keys())
    print(f'  HC pool size = {len(hc_subs)}')

    # First, evaluate full-pool metric (point estimate)
    basis_full = create_basis_full(N_CHANNELS, basis_type='fe')
    C_orig = basis_full[HUE_ANGLES]
    full_W, _ = precompute_hc_W(full_amps, C_orig)
    point = evaluate_grid_metrics(full_W, full_amps, vuln_target, fam,
                                   grid_bs, grid_bc, lam_tikh=args.lam_tikh)
    print(f'  Point estimate: l_topk={point["l_topk"]:.3f} '
          f'blend50_tikh={point["blend50_tikh"]:.3f} '
          f'best=(bs={point["best_bs"]},bc={point["best_bc"]}) '
          f'ρ@best={point["rho_at_best"]:+.3f}')

    # Bootstrap
    boot_records = []
    t0 = time.time()
    for b in range(args.n_boot):
        # Resample HC with replacement
        boot_subs = list(rng.choice(hc_subs, size=len(hc_subs), replace=True))
        boot_amps = {f'{i}': full_amps[boot_subs[i]] for i in
                     range(len(boot_subs))}
        boot_W, _ = precompute_hc_W(boot_amps, C_orig)
        m = evaluate_grid_metrics(boot_W, boot_amps, vuln_target, fam,
                                   grid_bs, grid_bc, lam_tikh=args.lam_tikh)
        m['boot_id'] = b
        m['hc_chosen'] = boot_subs
        boot_records.append(m)
        if (b + 1) % max(1, args.n_boot // 10) == 0:
            elapsed = time.time() - t0
            print(f'  [{b+1}/{args.n_boot}] elapsed={elapsed:.1f}s')

    # Summarize
    metrics = ['l_topk', 'mw_jaccard', 'blend50', 'blend50_tikh', 'topk_tikh',
               'best_bs', 'best_bc', 'rho_at_best']
    summary = {}
    for k in metrics:
        vals = np.array([r[k] for r in boot_records])
        summary[k] = {
            'mean': float(vals.mean()),
            'median': float(np.median(vals)),
            'std': float(vals.std()),
            'iqr': float(np.percentile(vals, 75)
                          - np.percentile(vals, 25)),
            'ci95': [float(np.percentile(vals, 2.5)),
                      float(np.percentile(vals, 97.5))],
        }

    out = {
        'subject': args.subject,
        'roi': args.roi,
        'family': fam,
        'n_boot': args.n_boot,
        'point_estimate': point,
        'bootstrap_summary': summary,
        'config': {
            'lam_tikh': args.lam_tikh,
            'grid_size': len(grid_bs) * len(grid_bc),
            'bs_step': args.bs_step,
            'bc_step': args.bc_step,
        },
    }
    out_path = out_dir / f'sub-{args.subject}_{args.roi}.json'
    with open(out_path, 'w') as f:
        json.dump(out, f, indent=2)
    print(f'\nWrote {out_path}')
    print('Summary:')
    for k, v in summary.items():
        print(f'  {k}: median={v["median"]:.3f} IQR={v["iqr"]:.3f} '
              f'CI95=[{v["ci95"][0]:.3f}, {v["ci95"][1]:.3f}]')


if __name__ == '__main__':
    main()
