#!/usr/bin/env python3
"""
cycle4_alt_metrics.py — Cycle 4: extended grid + alternative metrics.

목적:
  (1) β_s, β_c grid를 ±80(β_s) / ±60(β_c)로 확장하여 best param이 grid 내부에
      안정적으로 머무는지(boundary-stability) 검증.
  (2) 새 metric A/C/F 구현 + HC null 분포 vs CVD 분리도 평가.
       A. magnitude-weighted top-k Jaccard
       C. normalized vuln-residual L2 (||r|| / ||c||)
       F. per-color sign-agreement count (0..8 → /8)
  (3) 각 metric의 baseline_rho 의존성 측정.

Reuses:
  - loss_redesign_smoke.compute_extended_loss (existing 8 metrics)
  - step1_fit_loco_v2.{precompute_hc_W, simulate_mean_hc_wfixed,
                       load_cvd_loco_target}
  - utils_forward_model.{load_amplitudes, create_basis_full, HC_SUBJECTS, ...}

Local conda env: srm
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
sys.path.insert(0, str(_HERE))

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
from loss_redesign_smoke import (
    compute_extended_loss, get_2component_design,
)

CVD_TYPE = {'08': 'deutan', '09': 'protan', '10': 'normal'}
CONF_AXIS = {'protan': 16.0, 'deutan': 150.0, 'normal': 83.0}

LOCAL_DATA = (_PROJ / 'analysis' / 'phase1_procrustes_decoding' / 'results'
              / 'visualization' / 'full_dataset_C010_with_residuals')


# ---------------------------------------------------------------------------
# New Cycle-4 metrics (A, C, F)
# ---------------------------------------------------------------------------
def compute_cycle4_metrics(vuln_sim, vuln_cvd, k=3):
    """Cycle-4 alt metrics.

    Args:
        vuln_sim, vuln_cvd: 1-D arrays of shape (8,)
        k: top-k for Jaccard variants (default 3 = bottom-3 most-vulnerable)

    Returns:
        dict with:
            mw_jaccard      : magnitude-weighted Jaccard (A)
            mw_jaccard_loss : 1 - mw_jaccard
            norm_resid      : ||sim - cvd|| / ||cvd||  (C)
            sign_agree      : fraction of colours where sign(sim)==sign(cvd) (F)
            sign_agree_centered : same but on (vuln - mean) so it tests above/
                                  below-mean agreement (rank-aware)
    """
    s = np.asarray(vuln_sim, dtype=float)
    c = np.asarray(vuln_cvd, dtype=float)

    # ---- A. Magnitude-weighted top-k Jaccard --------------------------------
    # Weight w_i for CVD's most-vulnerable colours: w_i = max(0, -c_i) so that
    # MORE-vulnerable (more-negative) colours dominate. We then sum over colour
    # indices that are simultaneously in top-k of CVD AND top-k of sim. The
    # union sum is over CVD top-k only — matches how a clinician would weight
    # "did the model recover the same depth on the same colours?".
    top_c_idx = np.argsort(c)[:k]            # CVD's k most vulnerable
    top_s_idx = np.argsort(s)[:k]            # sim's k most vulnerable
    intersect = np.intersect1d(top_c_idx, top_s_idx)
    # Weight: depth of CVD on each top-k color (always positive)
    w_c = np.maximum(-c[top_c_idx], 0.0)
    if w_c.sum() > 0:
        # Numerator: weight on intersected colours (still using CVD's depth)
        num = 0.0
        for idx in intersect:
            # add this color's CVD weight if it is in top_c
            if idx in top_c_idx:
                num += float(max(-c[idx], 0.0))
        mw_jaccard = num / float(w_c.sum())
    else:
        # CVD has no negative vuln in top-k → fallback to plain Jaccard
        inter_n = len(set(top_c_idx) & set(top_s_idx))
        union_n = len(set(top_c_idx) | set(top_s_idx))
        mw_jaccard = inter_n / union_n if union_n > 0 else 0.0
    mw_jaccard_loss = 1.0 - mw_jaccard

    # ---- C. Normalized residual L2 ------------------------------------------
    resid = s - c
    norm_c = np.linalg.norm(c)
    if norm_c > 0:
        norm_resid = float(np.linalg.norm(resid) / norm_c)
    else:
        norm_resid = float(np.linalg.norm(resid))

    # ---- F. Sign agreement --------------------------------------------------
    # Raw sign on the full vuln vector (a colour above 0 is well-decoded;
    # below 0 means LOCO is broken on that colour).
    sgn_s = np.sign(s)
    sgn_c = np.sign(c)
    # Treat exact zero as matching anything (no penalty)
    match = ((sgn_s == sgn_c) | (sgn_s == 0) | (sgn_c == 0)).astype(int)
    sign_agree = float(match.mean())

    # Centered version: above- vs below-CVD-mean. This is rank-aware in the
    # binary sense — it asks "does sim place the same colours above-mean as
    # CVD does?" — a Pearson-like binary metric.
    sc = s - s.mean()
    cc = c - c.mean()
    match_c = ((np.sign(sc) == np.sign(cc)) | (np.sign(sc) == 0)
               | (np.sign(cc) == 0)).astype(int)
    sign_agree_centered = float(match_c.mean())

    return {
        'mw_jaccard': mw_jaccard,
        'mw_jaccard_loss': mw_jaccard_loss,
        'norm_resid': norm_resid,
        'sign_agree': sign_agree,
        'sign_agree_centered': sign_agree_centered,
    }


# ---------------------------------------------------------------------------
# Per-subject extended grid run
# ---------------------------------------------------------------------------
def run_grid(subj, roi, family, hc_amps_dict, hc_W_dict, vuln_target,
             grid_bs, grid_bc, verbose=False):
    """Sweep extended (β_s, β_c) grid for ONE subject.

    Records per-grid: original 8 metrics + 5 cycle-4 metrics.
    Returns landscape + best-by-criterion + boundary diagnostics.
    """
    # Baseline at (0, 0)
    C_baseline, _ = get_2component_design(0.0, 0.0, family)
    vuln_baseline, _ = simulate_mean_hc_wfixed(
        hc_W_dict, hc_amps_dict, C_baseline)
    base_ext = compute_extended_loss(vuln_baseline, vuln_target)
    base_c4 = compute_cycle4_metrics(vuln_baseline, vuln_target)

    landscape = []
    for bs in grid_bs:
        for bc in grid_bc:
            C_shift, _ = get_2component_design(bs, bc, family)
            vuln_sim, _ = simulate_mean_hc_wfixed(
                hc_W_dict, hc_amps_dict, C_shift)
            ext = compute_extended_loss(vuln_sim, vuln_target)
            c4 = compute_cycle4_metrics(vuln_sim, vuln_target)
            entry = {'bs': float(bs), 'bc': float(bc), **ext, **c4}
            landscape.append(entry)

    # Best-by-criterion
    crit_min = ['l_rank', 'l_dir', 'l_vuln', 'l_mag', 'l_max_resid',
                'l_topk_jaccard', 'mw_jaccard_loss', 'norm_resid']
    crit_max = ['sign_agree', 'sign_agree_centered']
    best_by_criterion = {}
    for k in crit_min:
        best_by_criterion[k] = min(landscape, key=lambda e: e[k])
    for k in crit_max:
        best_by_criterion[k] = max(landscape, key=lambda e: e[k])

    # Boundary diagnostic: distance from grid edge (lower = closer to boundary)
    bs_max = float(np.max(np.abs(grid_bs)))
    bc_max = float(np.max(np.abs(grid_bc)))
    boundary = {}
    for cname, e in best_by_criterion.items():
        d_bs = bs_max - abs(e['bs'])
        d_bc = bc_max - abs(e['bc'])
        boundary[cname] = {
            'bs_dist_to_edge': float(d_bs),
            'bc_dist_to_edge': float(d_bc),
            'on_boundary': bool(d_bs < 1e-6 or d_bc < 1e-6),
        }

    primary = best_by_criterion['l_rank']
    out = {
        'subject': subj,
        'roi': roi,
        'family': family,
        'baseline': {
            'rho': base_ext['spearman_r'],
            'pearson': base_ext['pearson_r'],
            **base_c4,
            'l_topk_jaccard': base_ext['l_topk_jaccard'],
            'l_mag': base_ext['l_mag'],
        },
        'best_grid': primary,
        'best_by_criterion': {k: {kk: v[kk] for kk in
                                  ('bs', 'bc', 'l_vuln', 'l_rank', 'l_dir',
                                   'l_mag', 'l_max_resid', 'l_topk_jaccard',
                                   'mw_jaccard_loss', 'norm_resid',
                                   'sign_agree', 'sign_agree_centered',
                                   'spearman_r', 'pearson_r')
                                  if kk in v}
                              for k, v in best_by_criterion.items()},
        'boundary': boundary,
        'delta_rho': primary['spearman_r'] - base_ext['spearman_r'],
        'delta_pearson': primary['pearson_r'] - base_ext['pearson_r'],
        'vuln_target': vuln_target.tolist(),
        'vuln_baseline': vuln_baseline.tolist(),
        'grid_extent': {'bs': [float(grid_bs.min()), float(grid_bs.max())],
                        'bc': [float(grid_bc.min()), float(grid_bc.max())]},
    }
    if verbose:
        print(f'  sub-{subj} {family}/{roi}: '
              f'baseρ={base_ext["spearman_r"]:+.3f} | '
              f'lrank best (bs={primary["bs"]:.0f},bc={primary["bc"]:.0f}) '
              f'edge_bs={boundary["l_rank"]["bs_dist_to_edge"]:.1f} '
              f'edge_bc={boundary["l_rank"]["bc_dist_to_edge"]:.1f} | '
              f'mw_jacc best (bs={best_by_criterion["mw_jaccard_loss"]["bs"]:.0f},'
              f'bc={best_by_criterion["mw_jaccard_loss"]["bc"]:.0f}) '
              f'mwJ={1-best_by_criterion["mw_jaccard_loss"]["mw_jaccard_loss"]:.2f}')
    return out, landscape


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    p = argparse.ArgumentParser('Cycle 4 — extended grid + alt metrics')
    p.add_argument('--subjects', nargs='+',
                   default=['08', '09', '10', '01', '02', '03', '04', '05', '06'],
                   help='CVD + HC subjects (sub-07 lacks LOCO json → skip)')
    p.add_argument('--roi', default='V4', help="ROI directory name on disk "
                   "(hV4 → 'V4', V1, V2, V3)")
    p.add_argument('--data_dir', default=str(LOCAL_DATA))
    p.add_argument('--output_dir',
                   default=str(_PHASE2 / 'results' / 'older_cycles/cycle_loss_redesign'
                               / 'cycle4_extended'))
    p.add_argument('--bs_step', type=float, default=2.0)
    p.add_argument('--bc_step', type=float, default=2.0)
    p.add_argument('--bs_max', type=float, default=80.0)
    p.add_argument('--bc_max', type=float, default=60.0)
    p.add_argument('--bs_min', type=float, default=0.0,
                   help='β_s lower bound (default 0 — half-grid). '
                        'Set negative to allow opposite sign.')
    p.add_argument('--save_landscape', action='store_true')
    p.add_argument('--smoke', action='store_true')
    args = p.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    data_dir = Path(args.data_dir)
    if not data_dir.exists():
        raise FileNotFoundError(f'{data_dir} not found')

    if args.smoke:
        args.subjects = ['08', '01']
        args.bs_step = 5.0
        args.bc_step = 5.0

    grid_bs = np.arange(args.bs_min, args.bs_max + 0.5 * args.bs_step,
                        args.bs_step)
    grid_bc = np.arange(-args.bc_max, args.bc_max + 0.5 * args.bc_step,
                        args.bc_step)
    print(f'[Grid] bs: [{grid_bs.min()},{grid_bs.max()}] step={args.bs_step}'
          f' n={len(grid_bs)}; '
          f'bc: [{grid_bc.min()},{grid_bc.max()}] step={args.bc_step} '
          f'n={len(grid_bc)} → total={len(grid_bs)*len(grid_bc)}')

    # HC pool
    print('[Init] Loading HC pool ...')
    hc_amps_dict = {}
    for hc in HC_SUBJECTS:
        hc_amps_dict[hc] = load_amplitudes(data_dir, hc, args.roi)
    basis_full = create_basis_full(N_CHANNELS, basis_type='fe')
    C_orig = basis_full[HUE_ANGLES]
    hc_W_dict, _ = precompute_hc_W(hc_amps_dict, C_orig)
    print(f'  W precomputed for {len(hc_W_dict)} HC')

    summary = {}
    t0 = time.time()
    for subj in args.subjects:
        # Family selection (same convention as Cycle 1-3)
        if subj in CVD_TYPE:
            fam = CVD_TYPE[subj]
            if fam == 'normal':
                fam = 'deutan'
        else:
            fam = 'deutan'  # HC null with deutan family — match CVD primary

        # Vuln target — must exist in validation/. If missing, skip subject.
        try:
            vt = load_cvd_loco_target(subj, args.roi)
        except FileNotFoundError:
            print(f'  [skip] sub-{subj}: no LOCO target')
            continue

        # LOO HC pool: remove subj if HC
        if subj in HC_SUBJECTS:
            pool_W = {k: v for k, v in hc_W_dict.items() if k != subj}
            pool_amps = {k: v for k, v in hc_amps_dict.items() if k != subj}
        else:
            pool_W = hc_W_dict
            pool_amps = hc_amps_dict

        out, landscape = run_grid(
            subj, args.roi, fam, pool_amps, pool_W, vt,
            grid_bs, grid_bc, verbose=True)
        out['group'] = 'CVD' if subj in CVD_TYPE else 'HC'
        out['n_pool'] = len(pool_W)
        summary[subj] = out

        with open(out_dir / f'sub-{subj}_{args.roi}_c4.json', 'w') as f:
            json.dump(out, f, indent=2)

        if args.save_landscape:
            with open(out_dir / f'sub-{subj}_{args.roi}_landscape.json', 'w') as f:
                json.dump(landscape, f)

    elapsed = time.time() - t0
    print(f'\n[Done] elapsed = {elapsed:.1f}s')

    # -------------------- Aggregate --------------------
    cvd_rows = [s for s in summary.values() if s['group'] == 'CVD']
    hc_rows = [s for s in summary.values() if s['group'] == 'HC']

    # CVD vs HC specificity per criterion
    crit_min = ['l_rank', 'l_dir', 'l_vuln', 'l_mag', 'l_topk_jaccard',
                'mw_jaccard_loss', 'norm_resid']
    crit_max = ['sign_agree', 'sign_agree_centered']

    spec_table = {}
    if hc_rows:
        for k in crit_min + crit_max:
            hc_vals = np.array([h['best_by_criterion'][k][k] for h in hc_rows])
            cvd_dict = {}
            for c in cvd_rows:
                cv = c['best_by_criterion'][k][k]
                if k in crit_min:
                    pe = float((np.sum(hc_vals <= cv) + 1) / (len(hc_vals) + 1))
                else:
                    pe = float((np.sum(hc_vals >= cv) + 1) / (len(hc_vals) + 1))
                z = float((cv - hc_vals.mean()) / hc_vals.std()) if hc_vals.std() > 0 else 0.0
                cvd_dict[c['subject']] = {
                    'cvd_value': float(cv),
                    'p_emp': pe,
                    'z': z,
                }
            spec_table[k] = {
                'hc_mean': float(hc_vals.mean()),
                'hc_std': float(hc_vals.std()),
                'hc_values': hc_vals.tolist(),
                'cvd': cvd_dict,
            }

    # Boundary stats (per-criterion, per-group)
    boundary_stats = {}
    for k in crit_min + crit_max:
        on_b_cvd = [c['boundary'][k]['on_boundary'] for c in cvd_rows]
        on_b_hc = [h['boundary'][k]['on_boundary'] for h in hc_rows]
        boundary_stats[k] = {
            'cvd_on_boundary': sum(on_b_cvd),
            'cvd_total': len(on_b_cvd),
            'hc_on_boundary': sum(on_b_hc),
            'hc_total': len(on_b_hc),
        }

    # Baseline_rho ↔ best-criterion-value correlation per criterion (HC pool)
    base_corr = {}
    if hc_rows:
        hc_base = np.array([h['baseline']['rho'] for h in hc_rows])
        for k in crit_min + crit_max:
            hc_v = np.array([h['best_by_criterion'][k][k] for h in hc_rows])
            if hc_base.std() > 0 and hc_v.std() > 0:
                r, _ = pearsonr(hc_base, hc_v)
                base_corr[k] = float(r)
            else:
                base_corr[k] = None

    aggregate = {
        'config': {
            'subjects': args.subjects,
            'roi': args.roi,
            'bs_range': [float(grid_bs.min()), float(grid_bs.max())],
            'bc_range': [float(grid_bc.min()), float(grid_bc.max())],
            'bs_step': args.bs_step,
            'bc_step': args.bc_step,
            'grid_size': len(grid_bs) * len(grid_bc),
        },
        'cvd': cvd_rows,
        'hc': hc_rows,
        'specificity_table': spec_table,
        'boundary_stats': boundary_stats,
        'baseline_correlations': base_corr,
    }
    with open(out_dir / 'aggregate.json', 'w') as f:
        json.dump(aggregate, f, indent=2, default=str)
    print(f'[Wrote] {out_dir/"aggregate.json"}')

    # ---------------- Summary table ----------------
    print('\n' + '=' * 110)
    print(f'{"subj":>4} {"grp":>4} {"basρ":>6} {"l_rank":>7} {"mwJac":>7} '
          f'{"normR":>7} {"signA":>6} {"signC":>6} '
          f'{"bs*":>5} {"bc*":>5} {"edge":>5}')
    print('-' * 110)
    for s in sorted(summary.values(),
                    key=lambda x: (x['group'], x['subject'])):
        bg = s['best_grid']
        bb = s['best_by_criterion']
        edge = 'B' if s['boundary']['l_rank']['on_boundary'] else '.'
        line = (f'{s["subject"]:>4} {s["group"]:>4} '
                f'{s["baseline"]["rho"]:>+6.3f} '
                f'{bg["l_rank"]:>7.3f} '
                f'{1-bb["mw_jaccard_loss"]["mw_jaccard_loss"]:>7.3f} '
                f'{bb["norm_resid"]["norm_resid"]:>7.3f} '
                f'{bb["sign_agree"]["sign_agree"]:>6.3f} '
                f'{bb["sign_agree_centered"]["sign_agree_centered"]:>6.3f} '
                f'{bg["bs"]:>5.0f} {bg["bc"]:>5.0f} {edge:>5}')
        print(line)
    print('=' * 110)

    # Specificity printout
    print('\n[Specificity vs HC null]')
    for k in crit_min + crit_max:
        if k not in spec_table:
            continue
        st = spec_table[k]
        msg = (f'  {k:>22}  HCμ={st["hc_mean"]:+.3f}±{st["hc_std"]:.3f}  ')
        for cs, cv in st['cvd'].items():
            msg += f'sub-{cs}: {cv["cvd_value"]:+.3f}(p={cv["p_emp"]:.2f},z={cv["z"]:+.2f}) '
        bcorr = base_corr.get(k)
        if bcorr is not None:
            msg += f' | corr(basρ,best)={bcorr:+.2f}'
        print(msg)

    # Boundary printout
    print('\n[Boundary stability]  on-boundary count / total')
    for k in crit_min + crit_max:
        bs = boundary_stats[k]
        print(f'  {k:>22}  CVD {bs["cvd_on_boundary"]}/{bs["cvd_total"]}  '
              f'HC {bs["hc_on_boundary"]}/{bs["hc_total"]}')


if __name__ == '__main__':
    main()
