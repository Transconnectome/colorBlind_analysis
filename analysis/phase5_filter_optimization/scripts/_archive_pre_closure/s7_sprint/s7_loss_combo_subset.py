"""S7: Loss combination + HC subset resample sprint (2026-05-24 USER DIRECTIVE).

Per cell (subject × ROI):
  Stage A — single-loss subset stability (RQ1): 4 losses on k∈{4,5,6} subsets
  Stage B — loss combination value (RQ2): 6 pair + 1 triple, k=5 only
  Stage C — λ sweep neural unique contribution (RQ3): 3 probes × 5 λ, k=5 only
  Stage D — train-test MSE (RQ4): test eval on complement at train-best param
  Stage E — color-perm (RQ5): deferred to post-selection, separate run

Cell list: 3 subjects × 4 ROIs = 12 cells.
SLURM array index ∈ [0, 11] → one cell per task.

Output: results/s7_loss_combo_subset/cell_{idx}_{subject}_{roi}.json
"""

import argparse
import itertools
import json
import sys
import time
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from rc_1dof import g_grid, forward_rc
from two_comp import BS_GRID, BC_GRID, forward_2comp
from neural_loss import (
    load_amplitudes, load_hc_pool, ROI_K,
    precompute_loco_W_within,
)
from diagnostic_delta_rdm import precompute_hc_W
from behav_loss import (
    load_jnd_per_pair, load_8afc_per_color,
    HC_JND_SUBJS,
)
from utils_forward_model import create_basis_full, HUE_ANGLES

from s8_loo_train_test import (
    jnd_baseline_from_pool, make_loss_fns,
    HC_SUBJS, DELTA_LAMBDA_BY_FAMILY,
)

OUT_DIR = SCRIPT_DIR.parent / "results" / "s7_loss_combo_subset"
ROIS = ['V1', 'V2', 'V3', 'V4']
ALL_SUBJECTS = [
    ('sub-08', 'deutan'),
    ('sub-09', 'protan'),
    ('sub-10', 'deutan'),  # near-normal null control
]

SINGLE_LOSSES = ['L_gamma', 'L_alpha', 'L_LOCO', 'L_RDM']
PAIR_COMBOS = [
    ('L_gamma', 'L_alpha'),
    ('L_gamma', 'L_LOCO'),
    ('L_gamma', 'L_RDM'),
    ('L_alpha', 'L_LOCO'),
    ('L_alpha', 'L_RDM'),
    ('L_LOCO', 'L_RDM'),
]
TRIPLE_COMBO = ('L_gamma', 'L_LOCO', 'L_RDM')
LAMBDA_PROBES = {
    'gamma_plus_LOCO': (('L_gamma',), ('L_LOCO',)),
    'gamma_plus_RDM': (('L_gamma',), ('L_RDM',)),
    'gamma_plus_LOCO_and_RDM': (('L_gamma',), ('L_LOCO', 'L_RDM')),
}
LAMBDA_VALUES = [0.0, 0.25, 0.5, 0.75, 1.0]

K_VALUES = [4, 5, 6]
COMBO_K = 5  # only k=5 for combinations + λ sweep

CELLS = [(s, f, r) for (s, f) in ALL_SUBJECTS for r in ROIS]


def zscore_grid(arr):
    arr = np.asarray(arr, dtype=float)
    mu = np.nanmean(arr)
    sigma = np.nanstd(arr)
    if not np.isfinite(sigma) or sigma < 1e-10:
        return np.full_like(arr, np.nan)
    return (arr - mu) / sigma


def grid_eval_rc(loss_fn, dl, family):
    grid = g_grid()
    out = np.zeros(len(grid))
    for i, g in enumerate(grid):
        delta = forward_rc(dl, g, family)
        try:
            v = float(loss_fn(delta))
            out[i] = v if np.isfinite(v) else np.nan
        except Exception:
            out[i] = np.nan
    return out


def grid_eval_2comp(loss_fn, family):
    out = np.zeros((len(BS_GRID), len(BC_GRID)))
    for i, bs in enumerate(BS_GRID):
        for j, bc in enumerate(BC_GRID):
            delta = forward_2comp(bs, bc, family)
            try:
                v = float(loss_fn(delta))
                out[i, j] = v if np.isfinite(v) else np.nan
            except Exception:
                out[i, j] = np.nan
    return out


def argmin_rc_grid(losses_grid):
    if np.all(np.isnan(losses_grid)):
        return None
    grid = g_grid()
    idx = int(np.nanargmin(losses_grid))
    return {
        'g_best': float(grid[idx]),
        'loss_best': float(losses_grid[idx]),
        'boundary_low': bool(idx == 0),
        'boundary_high': bool(idx == len(grid) - 1),
    }


def argmin_2comp_grid(losses_grid):
    if np.all(np.isnan(losses_grid)):
        return None
    flat_idx = int(np.nanargmin(losses_grid.ravel()))
    i, j = np.unravel_index(flat_idx, losses_grid.shape)
    return {
        'beta_s_best': float(BS_GRID[i]),
        'beta_c_best': float(BC_GRID[j]),
        'loss_best': float(losses_grid[i, j]),
        'norm': float(np.sqrt(BS_GRID[i] ** 2 + BC_GRID[j] ** 2)),
        'boundary_bs': bool(i == 0 or i == len(BS_GRID) - 1),
        'boundary_bc': bool(j == 0 or j == len(BC_GRID) - 1),
    }


def evaluate_loss_at_fit(loss_fn, family, fit_dict, model, dl_sources):
    """Evaluate a single loss closure at a fitted parameter point."""
    if fit_dict is None:
        return None
    try:
        if model == 'rc':
            dl = dl_sources[fit_dict['src']]
            g = fit_dict['g_best']
            delta = forward_rc(dl, g, family)
        else:
            delta = forward_2comp(fit_dict['beta_s_best'], fit_dict['beta_c_best'], family)
        v = float(loss_fn(delta))
        return v if np.isfinite(v) else None
    except Exception:
        return None


def compute_train_grids(subject_data, subset, family, dl_sources, C_baseline, K, hc_amps_all):
    """Build train loss closures for a HC subset + compute full grids for 4 single losses."""
    pool_amps = {h: hc_amps_all[h] for h in subset if h in hc_amps_all}
    if len(pool_amps) < 2:
        return None, None
    pool_jnd_subjs = [h for h in subset if h in HC_JND_SUBJS]
    if not pool_jnd_subjs:
        return None, None
    pool_jnd_baseline, pool_jnd_sd = jnd_baseline_from_pool(pool_jnd_subjs)
    pool_hc_W, _ = precompute_hc_W(pool_amps, C_baseline)

    cvd_loss_fns = make_loss_fns(
        subject_data['amp'], subject_data['jnd'], subject_data['_8afc'],
        subject_data['loco_W'],
        pool_amps, pool_jnd_baseline, pool_jnd_sd,
        pool_hc_W, C_baseline, K, family,
    )

    grids = {}
    for loss_name in SINGLE_LOSSES:
        fn = cvd_loss_fns[loss_name]
        try:
            test = fn(np.zeros(8))
            if not np.isfinite(test):
                grids[loss_name] = None
                continue
        except Exception:
            grids[loss_name] = None
            continue

        rc_grids = {src: grid_eval_rc(fn, dl, family) for src, dl in dl_sources.items()}
        twc_grid = grid_eval_2comp(fn, family)
        grids[loss_name] = {'rc': rc_grids, '2comp': twc_grid}

    return grids, cvd_loss_fns


def build_test_loss_fns(subject_data, complement, family, dl_sources, C_baseline, K, hc_amps_all):
    """Build test loss closures using HC complement as reference."""
    comp_amps = {h: hc_amps_all[h] for h in complement if h in hc_amps_all}
    if len(comp_amps) < 1:
        return None
    comp_jnd_subjs = [h for h in complement if h in HC_JND_SUBJS]
    if not comp_jnd_subjs:
        return None
    comp_jnd_baseline, comp_jnd_sd = jnd_baseline_from_pool(comp_jnd_subjs)
    comp_hc_W, _ = precompute_hc_W(comp_amps, C_baseline)
    test_loss_fns = make_loss_fns(
        subject_data['amp'], subject_data['jnd'], subject_data['_8afc'],
        subject_data['loco_W'],
        comp_amps, comp_jnd_baseline, comp_jnd_sd,
        comp_hc_W, C_baseline, K, family,
    )
    return test_loss_fns


def fit_single_losses(grids, dl_sources):
    out = {}
    for loss_name in SINGLE_LOSSES:
        gd = grids.get(loss_name)
        if gd is None:
            out[loss_name] = None
            continue
        rc_results = {}
        for src in dl_sources:
            res = argmin_rc_grid(gd['rc'][src])
            if res is not None:
                res['src'] = src
            rc_results[src] = res
        twc = argmin_2comp_grid(gd['2comp'])
        out[loss_name] = {'rc': rc_results, '2comp': twc}
    return out


def fit_combination(grids, combo_names, dl_sources):
    if any(grids.get(n) is None for n in combo_names):
        return None
    rc_results = {}
    for src in dl_sources:
        z_grids = [zscore_grid(grids[n]['rc'][src]) for n in combo_names]
        if any(np.all(np.isnan(z)) for z in z_grids):
            rc_results[src] = None
            continue
        combo_grid = np.nansum(z_grids, axis=0)
        res = argmin_rc_grid(combo_grid)
        if res is not None:
            res['src'] = src
        rc_results[src] = res

    z2c = [zscore_grid(grids[n]['2comp']) for n in combo_names]
    if any(np.all(np.isnan(z)) for z in z2c):
        twc = None
    else:
        combo_2c = np.nansum(z2c, axis=0)
        twc = argmin_2comp_grid(combo_2c)
    return {'rc': rc_results, '2comp': twc}


def fit_lambda_probe(grids, behav_names, neural_names, lam, dl_sources):
    needed = list(behav_names) + list(neural_names)
    if any(grids.get(n) is None for n in needed):
        return None
    rc_results = {}
    for src in dl_sources:
        z_behav = sum(zscore_grid(grids[n]['rc'][src]) for n in behav_names)
        z_neural = sum(zscore_grid(grids[n]['rc'][src]) for n in neural_names)
        if np.all(np.isnan(z_behav)) or np.all(np.isnan(z_neural)):
            rc_results[src] = None
            continue
        combo = (1.0 - lam) * z_behav + lam * z_neural
        res = argmin_rc_grid(combo)
        if res is not None:
            res['src'] = src
        rc_results[src] = res

    z_behav_2c = sum(zscore_grid(grids[n]['2comp']) for n in behav_names)
    z_neural_2c = sum(zscore_grid(grids[n]['2comp']) for n in neural_names)
    if np.all(np.isnan(z_behav_2c)) or np.all(np.isnan(z_neural_2c)):
        twc = None
    else:
        combo_2c = (1.0 - lam) * z_behav_2c + lam * z_neural_2c
        twc = argmin_2comp_grid(combo_2c)
    return {'rc': rc_results, '2comp': twc}


def test_eval_for_combo(test_loss_fns, fit_results, component_names, family, dl_sources):
    """Sum of component test losses at the train-fitted parameter."""
    out = {'rc': {}, '2comp': None}
    if fit_results is None or test_loss_fns is None:
        return out
    for src in dl_sources:
        rc_fit = fit_results.get('rc', {}).get(src) if isinstance(fit_results.get('rc'), dict) else None
        if rc_fit is None:
            out['rc'][src] = None
            continue
        total = 0.0
        ok = True
        for n in component_names:
            fn = test_loss_fns.get(n)
            if fn is None:
                ok = False
                break
            v = evaluate_loss_at_fit(fn, family, rc_fit, 'rc', dl_sources)
            if v is None:
                ok = False
                break
            total += v
        out['rc'][src] = float(total) if ok else None

    twc_fit = fit_results.get('2comp')
    if twc_fit is not None:
        total = 0.0
        ok = True
        for n in component_names:
            fn = test_loss_fns.get(n)
            if fn is None:
                ok = False
                break
            v = evaluate_loss_at_fit(fn, family, twc_fit, '2comp', dl_sources)
            if v is None:
                ok = False
                break
            total += v
        out['2comp'] = float(total) if ok else None
    return out


def process_cell(subject, family, roi):
    print(f"[CELL] {subject} {family} {roi}", flush=True)
    K = ROI_K[roi]
    C_baseline = create_basis_full(K, basis_type='fe')[HUE_ANGLES.astype(int)]
    dl_sources = DELTA_LAMBDA_BY_FAMILY[family]

    # Load subject data
    cvd_amp = load_amplitudes(subject, roi)
    cvd_jnd = load_jnd_per_pair(subject)
    try:
        cvd_8afc = load_8afc_per_color(subject)
    except Exception:
        cvd_8afc = None
    cvd_loco_W, _ = precompute_loco_W_within(cvd_amp, C_baseline)

    subject_data = {
        'amp': cvd_amp, 'jnd': cvd_jnd, '_8afc': cvd_8afc, 'loco_W': cvd_loco_W,
    }

    hc_amps_all = load_hc_pool(roi)
    available_hc = list(hc_amps_all.keys())

    # Enumerate subsets (only over available HC)
    subsets_to_run = []
    for k in K_VALUES:
        for subset in itertools.combinations(HC_SUBJS, k):
            subsets_to_run.append((k, list(subset)))
    print(f"  Total subsets: {len(subsets_to_run)}", flush=True)

    subset_results = []
    for counter, (k, subset) in enumerate(subsets_to_run, start=1):
        t0 = time.time()
        complement = [h for h in HC_SUBJS if h not in subset]

        # Build train grids + closures
        grids, _train_fns = compute_train_grids(
            subject_data, subset, family, dl_sources,
            C_baseline, K, hc_amps_all,
        )
        if grids is None:
            continue

        # Stage A: single fits
        single_fits = fit_single_losses(grids, dl_sources)

        # Stage B: combinations (k=5 only)
        combo_fits = {}
        if k == COMBO_K:
            for combo in PAIR_COMBOS + [TRIPLE_COMBO]:
                name = '+'.join(combo)
                combo_fits[name] = fit_combination(grids, combo, dl_sources)

        # Stage C: λ sweep (k=5 only)
        lambda_fits = {}
        if k == COMBO_K:
            for probe_name, (behav, neural) in LAMBDA_PROBES.items():
                lambda_fits[probe_name] = {}
                for lam in LAMBDA_VALUES:
                    lambda_fits[probe_name][f"{lam:.2f}"] = fit_lambda_probe(
                        grids, behav, neural, lam, dl_sources,
                    )

        # Stage D: test eval on complement at train-best param
        test_results = {'single': {}, 'combo': {}, 'lambda': {}}
        if len(complement) >= 1:
            test_fns = build_test_loss_fns(
                subject_data, complement, family, dl_sources,
                C_baseline, K, hc_amps_all,
            )
            if test_fns is not None:
                for loss_name in SINGLE_LOSSES:
                    fit = single_fits.get(loss_name)
                    if fit is not None:
                        test_results['single'][loss_name] = test_eval_for_combo(
                            test_fns, fit, [loss_name], family, dl_sources,
                        )
                if k == COMBO_K:
                    for combo in PAIR_COMBOS + [TRIPLE_COMBO]:
                        name = '+'.join(combo)
                        fit = combo_fits.get(name)
                        if fit is not None:
                            test_results['combo'][name] = test_eval_for_combo(
                                test_fns, fit, list(combo), family, dl_sources,
                            )
                    for probe_name, (behav, neural) in LAMBDA_PROBES.items():
                        test_results['lambda'][probe_name] = {}
                        for lam in LAMBDA_VALUES:
                            lk = f"{lam:.2f}"
                            fit = lambda_fits[probe_name].get(lk)
                            if fit is not None:
                                components = list(behav) + list(neural)
                                test_results['lambda'][probe_name][lk] = test_eval_for_combo(
                                    test_fns, fit, components, family, dl_sources,
                                )

        subset_results.append({
            'k': k,
            'subset': subset,
            'complement': complement,
            'single_fits': single_fits,
            'combo_fits': combo_fits,
            'lambda_fits': lambda_fits,
            'test_results': test_results,
            'elapsed_s': round(time.time() - t0, 2),
        })

        if counter % 10 == 0:
            print(f"  [{counter}/{len(subsets_to_run)}] k={k} elapsed={round(time.time() - t0, 2)}s", flush=True)

    return {
        'subject': subject,
        'family': family,
        'roi': roi,
        'K': K,
        'available_hc': available_hc,
        'design': {
            'K_values': K_VALUES,
            'combo_k': COMBO_K,
            'single_losses': SINGLE_LOSSES,
            'pair_combos': ['+'.join(c) for c in PAIR_COMBOS],
            'triple_combo': '+'.join(TRIPLE_COMBO),
            'lambda_probes': {k: {'behav': list(v[0]), 'neural': list(v[1])} for k, v in LAMBDA_PROBES.items()},
            'lambda_values': LAMBDA_VALUES,
            'delta_lambda_sources': DELTA_LAMBDA_BY_FAMILY[family],
        },
        'subsets': subset_results,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cell-idx', type=int, default=None,
                        help='SLURM array task index (0..11). If omitted, sequential local mode.')
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if args.cell_idx is not None:
        if args.cell_idx < 0 or args.cell_idx >= len(CELLS):
            print(f"ERROR: cell-idx {args.cell_idx} out of range [0, {len(CELLS) - 1}]")
            sys.exit(1)
        subject, family, roi = CELLS[args.cell_idx]
        print(f"[S7 ARRAY] cell {args.cell_idx}: {subject} {family} {roi}", flush=True)
        t0 = time.time()
        result = process_cell(subject, family, roi)
        result['total_secs'] = round(time.time() - t0, 1)
        out_file = OUT_DIR / f"cell_{args.cell_idx:02d}_{subject}_{roi}.json"
        with open(out_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        print(f"\n[DONE] {out_file} ({result['total_secs']}s)", flush=True)
    else:
        print(f"[S7 LOCAL] {len(CELLS)} cells sequentially", flush=True)
        t0 = time.time()
        for idx, (subject, family, roi) in enumerate(CELLS):
            t_cell = time.time()
            result = process_cell(subject, family, roi)
            result['total_secs'] = round(time.time() - t_cell, 1)
            out_file = OUT_DIR / f"cell_{idx:02d}_{subject}_{roi}.json"
            with open(out_file, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            print(f"  [{idx + 1}/{len(CELLS)}] {out_file} ({result['total_secs']}s)", flush=True)
        print(f"\n[DONE] Total {round(time.time() - t0, 1)}s", flush=True)


if __name__ == "__main__":
    main()
