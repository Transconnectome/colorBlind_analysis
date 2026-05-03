#!/usr/bin/env python3
"""
loss_redesign_smoke.py — Cycle 1 smoke test for loss/filter redesign.

Goal:
  (1) Re-evaluate existing 2-component grid with new loss terms (L_mag, L_dir).
  (2) Build HC LOO null distribution by running same grid on each HC subject.
  (3) Compute baseline-residualized Δρ to test if specificity recovers.
  (4) Compare CVD vs HC distributions on each new metric.

Usage (local, conda srm):
    python loss_redesign_smoke.py --subjects 08 01 02 03 04 05 06 07 \\
        --roi V4 --family deutan --output_dir ../../results/older_cycles/cycle_loss_redesign

Family choice:
    For CVD subjects use their actual type (sub-08=deutan, sub-09=protan).
    For HC subjects, sweep BOTH families and take the worse case (most-conservative
    HC null).
"""

import argparse
import json
import sys
import time
import numpy as np
from pathlib import Path
from scipy.stats import spearmanr, pearsonr

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve().parent
_PHASE2 = _HERE.parent.parent
_PROJ = _PHASE2.parent.parent
sys.path.insert(0, str(_PHASE2 / 'scripts'))

_FWD = _PROJ / 'analysis' / 'future_phase1_forward_model' / 'scripts'
sys.path.insert(0, str(_FWD))

from utils_forward_model import (
    HC_SUBJECTS, N_CHANNELS, N_RUNS, N_COLORS, HUE_ANGLES,
    load_amplitudes, create_basis_full,
)
from machado_simulator import machado_shifted_hue
from step1_fit_loco_v2 import (
    simulate_mean_hc_wfixed, precompute_hc_W,
    load_cvd_loco_target,
)

CVD_TYPE = {'08': 'deutan', '09': 'protan', '10': 'normal'}
CONF_AXIS = {'protan': 16.0, 'deutan': 150.0, 'normal': 83.0}

LOCAL_DATA = (_PROJ / 'analysis' / 'phase1_procrustes_decoding' / 'results'
              / 'visualization' / 'full_dataset_C010_with_residuals')

# ---------------------------------------------------------------------------
# Loss terms (extends loco_distortion_fit.compute_fit_loss)
# ---------------------------------------------------------------------------
def compute_extended_loss(vuln_sim, vuln_cvd):
    """All proposed scalar metrics for one (sim, target) pair."""
    s = np.asarray(vuln_sim)
    c = np.asarray(vuln_cvd)

    # L_vuln (existing): MSE
    l_vuln = float(np.mean((s - c) ** 2))

    # L_rank (existing): 1 - Spearman
    rho, _ = spearmanr(s, c)
    rho = float(rho) if np.isfinite(rho) else 0.0
    l_rank = 1.0 - rho

    # H2 — L_dir : 1 - Pearson r (uses sign + magnitude)
    if np.std(s) > 0 and np.std(c) > 0:
        r_pearson, _ = pearsonr(s, c)
        r_pearson = float(r_pearson) if np.isfinite(r_pearson) else 0.0
    else:
        r_pearson = 0.0
    l_dir = 1.0 - r_pearson

    # H1 — L_mag : difference of L2 norms
    l_mag = float((np.linalg.norm(s) - np.linalg.norm(c)) ** 2)

    # H1b — Mean-level bias (target-sim mean diff)
    l_bias = float((s.mean() - c.mean()) ** 2)

    # H5 — concentration of rank residual
    rs = np.argsort(np.argsort(s))   # ranks 0..7
    rc = np.argsort(np.argsort(c))
    rank_resid = (rs - rc).astype(float)
    if np.sum(rank_resid ** 2) > 0:
        l_concentration = float(np.max(rank_resid ** 2)
                                / np.sum(rank_resid ** 2))
    else:
        l_concentration = 0.0

    # H4 helper - signed cosine of centered vectors (Pearson without 1- subtraction)
    s_c = s - s.mean()
    c_c = c - c.mean()
    if np.linalg.norm(s_c) > 0 and np.linalg.norm(c_c) > 0:
        cos_centered = float(np.dot(s_c, c_c)
                             / (np.linalg.norm(s_c) * np.linalg.norm(c_c)))
    else:
        cos_centered = 0.0

    # H6 — max-residual penalty
    resid = s - c
    l_max_resid = float(np.max(np.abs(resid)))

    # H7 — top-k vulnerability set Jaccard (k=3 most vulnerable = lowest)
    k = 3
    top_s = set(np.argsort(s)[:k].tolist())
    top_c = set(np.argsort(c)[:k].tolist())
    inter = len(top_s & top_c)
    union = len(top_s | top_c)
    l_topk_jaccard = (1.0 - inter / union) if union > 0 else 1.0

    # H7b — bottom-k (least vulnerable) Jaccard
    bot_s = set(np.argsort(s)[-k:].tolist())
    bot_c = set(np.argsort(c)[-k:].tolist())
    inter_b = len(bot_s & bot_c)
    union_b = len(bot_s | bot_c)
    l_botk_jaccard = (1.0 - inter_b / union_b) if union_b > 0 else 1.0

    return {
        'l_vuln': l_vuln,
        'l_rank': l_rank,
        'spearman_r': rho,
        'l_dir': l_dir,
        'pearson_r': r_pearson,
        'l_mag': l_mag,
        'l_bias': l_bias,
        'l_concentration': l_concentration,
        'cos_centered': cos_centered,
        'l_max_resid': l_max_resid,
        'l_topk_jaccard': l_topk_jaccard,
        'l_botk_jaccard': l_botk_jaccard,
    }


# ---------------------------------------------------------------------------
# 2-component design matrix (copied from loco_distortion_fit get_shifted_design)
# ---------------------------------------------------------------------------
def get_2component_design(bs, bc, cvd_type):
    hue_base, _, _ = machado_shifted_hue(0.0, cvd_type)
    theta_conf = CONF_AXIS[cvd_type]
    dt = (bs * np.cos(np.radians(hue_base - 90.0))
          + bc * np.cos(np.radians(hue_base - theta_conf)))
    hue_shifted = (hue_base + dt) % 360.0
    basis_full = create_basis_full(N_CHANNELS, basis_type='fe')
    idx = np.round(hue_shifted).astype(int) % 360
    return basis_full[idx], dt


# ---------------------------------------------------------------------------
# Per-subject pseudo-target builder
# ---------------------------------------------------------------------------
def build_pseudo_target(subj, roi, data_dir, fold_data=None):
    """Build per-color vulnerability target.

    For CVD: load from existing pre-computed LOCO json (same as production).
    For HC : compute from local W-fixed prediction error using leave-one-color-out.
             We mimic the CVD target shape so that the fit landscape is comparable.
    """
    try:
        return load_cvd_loco_target(subj, roi, model='ridge_gcv')
    except Exception as e:
        # Some HC may not have validation json; skip
        raise FileNotFoundError(
            f'No LOCO target for sub-{subj}/{roi}: {e}')


# ---------------------------------------------------------------------------
# Per-subject grid run
# ---------------------------------------------------------------------------
def run_grid_for_subject(subj, roi, family, hc_amps_dict, hc_W_dict,
                         vuln_target, grid_bs, grid_bc, verbose=False):
    """Sweep 2-component grid for ONE subject.

    Args:
        subj: subject id (e.g. '08')
        roi: ROI dir name on disk ('V4' for hV4)
        family: 'deutan' or 'protan'
        hc_amps_dict: precomputed HC amplitudes (used as W-fixed predictor pool)
        hc_W_dict: precomputed HC ridge weights
        vuln_target: (8,) per-color voxel correlation = LOCO target
        grid_bs / grid_bc: 1D arrays of beta_s and beta_c values

    Returns:
        landscape: list of dicts (per grid point)
        baseline_metrics: dict at (bs=0, bc=0)
        best_metrics: dict at min L_dir grid point (most-positive Pearson)
    """
    # Baseline (delta=0)
    C_baseline, _ = get_2component_design(0.0, 0.0, family)
    vuln_baseline, _ = simulate_mean_hc_wfixed(
        hc_W_dict, hc_amps_dict, C_baseline)
    base_loss = compute_extended_loss(vuln_baseline, vuln_target)

    landscape = []
    for bs in grid_bs:
        for bc in grid_bc:
            C_shifted, dt = get_2component_design(bs, bc, family)
            vuln_sim, _ = simulate_mean_hc_wfixed(
                hc_W_dict, hc_amps_dict, C_shifted)
            ext = compute_extended_loss(vuln_sim, vuln_target)
            entry = {
                'bs': float(bs),
                'bc': float(bc),
                'vuln_sim': vuln_sim.tolist(),
                **ext,
            }
            landscape.append(entry)

    # Find best for multiple criteria (each criterion = a candidate "winner")
    best_by_criterion = {
        'l_rank':         min(landscape, key=lambda e: e['l_rank']),
        'l_dir':          min(landscape, key=lambda e: e['l_dir']),
        'l_vuln':         min(landscape, key=lambda e: e['l_vuln']),
        'l_mag':          min(landscape, key=lambda e: e['l_mag']),
        'l_max_resid':    min(landscape, key=lambda e: e['l_max_resid']),
        'l_topk_jaccard': min(landscape, key=lambda e: e['l_topk_jaccard']),
    }
    best = best_by_criterion['l_rank']  # primary (matches existing pipeline)
    out = {
        'subject': subj,
        'roi': roi,
        'family': family,
        'baseline_rho': base_loss['spearman_r'],
        'baseline_pearson': base_loss['pearson_r'],
        'baseline_l_vuln': base_loss['l_vuln'],
        'baseline_l_mag': base_loss['l_mag'],
        'baseline_l_bias': base_loss['l_bias'],
        'baseline_l_max_resid': base_loss['l_max_resid'],
        'baseline_l_topk_jaccard': base_loss['l_topk_jaccard'],
        'best_grid': best,
        'best_by_criterion': {k: {kk: v[kk] for kk in
                                  ('bs', 'bc', 'l_vuln', 'l_rank', 'l_dir',
                                   'l_mag', 'l_max_resid', 'l_topk_jaccard',
                                   'l_botk_jaccard',
                                   'spearman_r', 'pearson_r')}
                              for k, v in best_by_criterion.items()},
        'delta_rho': best['spearman_r'] - base_loss['spearman_r'],
        'delta_pearson': best['pearson_r'] - base_loss['pearson_r'],
        'delta_l_vuln': best['l_vuln'] - base_loss['l_vuln'],
        'delta_l_mag': best['l_mag'] - base_loss['l_mag'],
        'vuln_target': vuln_target.tolist(),
        'vuln_baseline': vuln_baseline.tolist(),
    }
    if verbose:
        print(f'  sub-{subj} {family}/{roi}: '
              f'baseline ρ={base_loss["spearman_r"]:.3f} '
              f'pearson={base_loss["pearson_r"]:.3f} | '
              f'best ρ={best["spearman_r"]:.3f} '
              f'pearson={best["pearson_r"]:.3f} '
              f'(bs={best["bs"]}, bc={best["bc"]}) | '
              f'Δρ={out["delta_rho"]:+.3f} '
              f'Δr={out["delta_pearson"]:+.3f}')
    return out, landscape


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    p = argparse.ArgumentParser(description='Cycle-1 loss redesign smoke')
    p.add_argument('--subjects', nargs='+',
                   default=['08', '01', '02', '03', '04', '05', '06', '07'],
                   help='Subjects to fit (mix of CVD + HC for null)')
    p.add_argument('--roi', default='V4')
    p.add_argument('--family', default=None,
                   help="If omitted: CVD uses its type, HC uses 'deutan' "
                        '(matches sub-08) for fair comparison')
    p.add_argument('--data_dir', default=str(LOCAL_DATA))
    p.add_argument('--output_dir',
                   default=str(_PHASE2 / 'results' / 'older_cycles/cycle_loss_redesign'))
    p.add_argument('--bs_step', type=float, default=2.0)
    p.add_argument('--bc_step', type=float, default=2.0)
    p.add_argument('--bs_max', type=float, default=50.0,
                   help='Cap on |beta_s| (default 50)')
    p.add_argument('--bc_max', type=float, default=50.0,
                   help='Cap on |beta_c| (default 50)')
    p.add_argument('--save_landscape', action='store_true')
    p.add_argument('--smoke', action='store_true',
                   help='Smoke run: 1 subject, coarser grid (fast)')
    args = p.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    data_dir = Path(args.data_dir)
    if not data_dir.exists():
        raise FileNotFoundError(f'{data_dir} not found')

    if args.smoke:
        args.subjects = args.subjects[:1]
        args.bs_step = 5.0
        args.bc_step = 5.0

    # ----- Build grid -----
    grid_bs = np.arange(0.0, args.bs_max + 0.5 * args.bs_step, args.bs_step)
    grid_bc = np.arange(-args.bc_max, args.bc_max + 0.5 * args.bc_step,
                         args.bc_step)
    print(f'Grid: |bs|={len(grid_bs)}, |bc|={len(grid_bc)}, '
          f'total={len(grid_bs)*len(grid_bc)}')

    # ----- Precompute HC pool (same one used for fitting) -----
    print('Loading HC pool ...')
    hc_amps_dict = {}
    for hc in HC_SUBJECTS:
        hc_amps_dict[hc] = load_amplitudes(data_dir, hc, args.roi)
    basis_full = create_basis_full(N_CHANNELS, basis_type='fe')
    C_original = basis_full[HUE_ANGLES]
    hc_W_dict, hc_alpha_dict = precompute_hc_W(hc_amps_dict, C_original)
    print(f'  W precomputed for {len(hc_W_dict)} HC')

    # ----- Run for each subject -----
    summary = {}
    t0 = time.time()
    for subj in args.subjects:
        # decide family
        if args.family is not None:
            family = args.family
        elif subj in CVD_TYPE:
            family = CVD_TYPE[subj]
            if family == 'normal':
                family = 'deutan'  # for sub-10, treat as deutan-template
        else:
            family = 'deutan'  # HC: use deutan family to match sub-08

        # vulnerability target — note: HC vulnerability comes from the SAME
        # simulator pool. To get a fair LOO-HC null we use the held-out HC's
        # OWN voxel pattern as target while everyone else trains/predicts.
        if subj in CVD_TYPE:
            vuln_target = load_cvd_loco_target(subj, args.roi)
        else:
            # Build LOO HC null: use this HC as held-out target, others as pool
            try:
                vuln_target = load_cvd_loco_target(subj, args.roi)
            except Exception:
                # Fall back: synthesize target from local W-fixed prediction
                # of this HC by other HCs' W, then voxel correlation per color.
                # (rare path — only if json missing)
                amp_test = hc_amps_dict[subj]
                pool = {k: v for k, v in hc_W_dict.items() if k != subj}
                C_test = basis_full[HUE_ANGLES]
                vuln_test, _ = simulate_mean_hc_wfixed(pool, hc_amps_dict, C_test)
                vuln_target = vuln_test
                print(f'  [warn] sub-{subj} target synthesized')
                # fall through

        # ALSO build LOO null for HC subject by REMOVING its own W from pool
        if subj in HC_SUBJECTS:
            pool_W = {k: v for k, v in hc_W_dict.items() if k != subj}
            pool_amps = {k: v for k, v in hc_amps_dict.items() if k != subj}
        else:
            pool_W = hc_W_dict
            pool_amps = hc_amps_dict

        out, landscape = run_grid_for_subject(
            subj, args.roi, family,
            pool_amps, pool_W, vuln_target,
            grid_bs, grid_bc, verbose=True)
        out['group'] = 'CVD' if subj in CVD_TYPE else 'HC'
        out['n_pool'] = len(pool_W)
        summary[subj] = out

        # save per-subject json
        save_path = out_dir / f'sub-{subj}_{args.roi}_loss_redesign.json'
        with open(save_path, 'w') as f:
            json.dump(out, f, indent=2)
        print(f'  saved {save_path.name}')

        if args.save_landscape:
            land_path = out_dir / f'sub-{subj}_{args.roi}_landscape.json'
            with open(land_path, 'w') as f:
                json.dump(landscape, f)

    elapsed = time.time() - t0
    print(f'\nDone in {elapsed:.1f}s')

    # ----- Aggregate summary -----
    cvd_rows = [s for s in summary.values() if s['group'] == 'CVD']
    hc_rows = [s for s in summary.values() if s['group'] == 'HC']

    aggregate = {
        'config': {
            'subjects': args.subjects,
            'roi': args.roi,
            'family_default': args.family,
            'bs_step': args.bs_step,
            'bc_step': args.bc_step,
            'grid_size': len(grid_bs) * len(grid_bc),
        },
        'cvd': cvd_rows,
        'hc': hc_rows,
    }

    # specificity metrics
    if hc_rows and cvd_rows:
        hc_drho = np.array([h['delta_rho'] for h in hc_rows])
        hc_dpear = np.array([h['delta_pearson'] for h in hc_rows])
        hc_dlmag = np.array([h['delta_l_mag'] for h in hc_rows])
        hc_baseline = np.array([h['baseline_rho'] for h in hc_rows])

        for c in cvd_rows:
            # rank within CVD+HC pool
            all_drho = np.concatenate([[c['delta_rho']], hc_drho])
            rank_drho = int(np.sum(all_drho > c['delta_rho']) + 1)
            n = len(all_drho)
            c['emp_p_drho'] = (np.sum(hc_drho >= c['delta_rho']) + 1) / (len(hc_drho) + 1)
            c['emp_p_dpear'] = (np.sum(hc_dpear >= c['delta_pearson']) + 1) / (len(hc_dpear) + 1)
            c['rank_drho_in_pool'] = rank_drho
            # baseline-residualized: regress out baseline_rho dependence using HC
            slope, intercept = np.polyfit(hc_baseline, hc_drho, 1)
            cvd_resid = c['delta_rho'] - (slope * c['baseline_rho'] + intercept)
            hc_resid = hc_drho - (slope * hc_baseline + intercept)
            c['delta_rho_residual'] = float(cvd_resid)
            c['emp_p_drho_residual'] = float(
                (np.sum(hc_resid >= cvd_resid) + 1) / (len(hc_resid) + 1))

        aggregate['hc_summary'] = {
            'baseline_rho': hc_baseline.tolist(),
            'delta_rho': hc_drho.tolist(),
            'delta_pearson': hc_dpear.tolist(),
            'delta_l_mag': hc_dlmag.tolist(),
            'corr_baseline_drho': float(
                np.corrcoef(hc_baseline, hc_drho)[0, 1]) if len(hc_drho) > 1 else None,
            'mean_drho': float(hc_drho.mean()),
            'std_drho': float(hc_drho.std()),
        }

    with open(out_dir / 'aggregate.json', 'w') as f:
        json.dump(aggregate, f, indent=2, default=str)
    print(f'Wrote {out_dir/"aggregate.json"}')

    # Print summary table
    print('\n' + '='*100)
    print(f'{"subj":>4} {"grp":>4} {"basρ":>6} {"Δρ":>6} {"Δr":>6} '
          f'{"Δlmag":>7} {"bestbs":>6} {"bestbc":>6} '
          f'{"resid":>6} {"p_resid":>7}')
    print('-'*100)
    for s in sorted(summary.values(), key=lambda x: (x['group'], x['subject'])):
        bg = s['best_grid']
        line = (f'{s["subject"]:>4} {s["group"]:>4} '
                f'{s["baseline_rho"]:>+6.3f} {s["delta_rho"]:>+6.3f} '
                f'{s["delta_pearson"]:>+6.3f} '
                f'{s["delta_l_mag"]:>+7.4f} '
                f'{bg["bs"]:>6.1f} {bg["bc"]:>6.1f}')
        if 'delta_rho_residual' in s:
            line += (f' {s["delta_rho_residual"]:>+6.3f} '
                     f'{s["emp_p_drho_residual"]:>7.3f}')
        print(line)
    print('='*100)


if __name__ == '__main__':
    main()
