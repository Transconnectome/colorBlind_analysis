"""S10b v3: Inclusion screening with extended test metrics + storage subset ids.

Changes from v2:
- N_RESAMPLES = 300 (was 1000) — 후보 식별 충분
- Additional test metrics on complement HC baseline:
    * test_focal (per-subject focal pair) — same as v2
    * test_agg (8-pair aggregate L_γ) — same as v2
    * test_V1_RDM (V1 RDM cosine distance) — NEW
    * test_per_pair (8 pair z² individually) — NEW
- Storage: subset_idx + train/test HC ids per fit (post-hoc analysis enabled)
- Combo chunk split via --combo-start / --combo-end (SLURM array support)

Run modes:
  python s10b_v3_extended.py --subject sub-08
  python s10b_v3_extended.py --subject sub-08 --combo-start 0 --combo-end 10
  python s10b_v3_extended.py --subject sub-09
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

from rc_1dof import forward_rc, G_MIN, G_MAX, G_STEP
from two_comp import forward_2comp, BS_GRID, BC_GRID
from neural_loss import (
    load_amplitudes, load_hc_pool, ROI_K,
    precompute_loco_W_within, L_LOCO, L_RDM,
)
from diagnostic_delta_rdm import precompute_hc_W
from behav_loss import (
    load_jnd_per_pair, L_behav_gamma, PAIR_HUES, HC_JND_SUBJS,
)
from utils_forward_model import create_basis_full, HUE_ANGLES
from s8_loo_train_test import jnd_baseline_from_pool, DELTA_LAMBDA_BY_FAMILY

OUT_DIR = SCRIPT_DIR.parent / "results" / "s10_inclusion"
OUT_DIR.mkdir(parents=True, exist_ok=True)

HC_SUBJS = ['sub-01', 'sub-02', 'sub-03', 'sub-04', 'sub-05', 'sub-06', 'sub-07']
ROIS = ['V1', 'V2', 'V3', 'V4']

N_RESAMPLES = 300
SUBSET_SIZE = 5
RNG_SEED = 42

PAIR_KEYS = {'OY': 'orange-yellow', 'YG': 'yellow-green',
              'YP': 'yellow-purple', 'GB': 'green-blue'}

SUBJECTS = {
    'sub-08': {'family': 'deutan', 'pairs': ['OY', 'YG', 'YP'],
                'rdm_rois': ['V1', 'V2', 'V3', 'V4'],
                'focal_pair': 'yellow-purple'},
    'sub-09': {'family': 'protan', 'pairs': ['GB'],
                'rdm_rois': ['V1'],
                'focal_pair': 'green-blue'},
}

K_RC = 1
K_2C = 2
HUES = np.arange(0, 360, 45, dtype=float)


def g_grid():
    return np.arange(G_MIN, G_MAX + 1e-9, G_STEP)


def make_gamma_pair_atom(pair_key, cvd_jnd, pool_jnd_subjs):
    pair_name = PAIR_KEYS[pair_key]
    bl, sd = jnd_baseline_from_pool(pool_jnd_subjs)
    if pair_name not in bl or cvd_jnd.get(pair_name) is None:
        return None
    p_obs = cvd_jnd[pair_name]
    p_base = bl[pair_name]
    p_sd = max(sd[pair_name], 1e-3)
    theta_a, theta_b = PAIR_HUES[pair_name]
    i = int(round(theta_a / 45.0)) % 8
    j = int(round(theta_b / 45.0)) % 8

    def loss_fn(delta_8vec):
        perceived = (HUES + delta_8vec) % 360.0
        d_phys = min(abs(theta_a - theta_b) % 360, 360 - abs(theta_a - theta_b) % 360)
        d_perc_raw = abs(perceived[i] - perceived[j]) % 360
        d_perc = max(min(d_perc_raw, 360 - d_perc_raw), 1e-3)
        pred = p_base * (d_phys / d_perc)
        return ((pred - p_obs) / p_sd) ** 2
    return loss_fn


def make_rdm_atom(roi, cvd_amp, pool_amps_dict, C_baseline, K):
    if len(pool_amps_dict) < 2:
        return None
    try:
        pool_W, _ = precompute_hc_W(pool_amps_dict, C_baseline)
    except Exception:
        return None

    def loss_fn(delta_8vec):
        try:
            return L_RDM(delta_8vec, cvd_amp, pool_amps_dict, pool_W,
                          C_baseline, K, distance='correlation')
        except Exception:
            return np.nan
    return loss_fn


def make_loco_atom(cvd_amp_v4, K_v4):
    try:
        C_b = create_basis_full(K_v4, basis_type='fe')[HUE_ANGLES.astype(int)]
        loco_W, _ = precompute_loco_W_within(cvd_amp_v4, C_b)
    except Exception:
        return None

    def loss_fn(delta_8vec):
        try:
            return L_LOCO(delta_8vec, cvd_amp_v4, loco_W, K_v4)
        except Exception:
            return np.nan
    return loss_fn


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


def zscore_grid(arr):
    arr = np.asarray(arr, dtype=float)
    mu = np.nanmean(arr); s = np.nanstd(arr)
    if not np.isfinite(s) or s < 1e-10:
        return np.full_like(arr, np.nan)
    return (arr - mu) / s


def argmin_rc(arr):
    if np.all(np.isnan(arr)):
        return None
    grid = g_grid()
    idx = int(np.nanargmin(arr))
    return {'g': float(grid[idx]),
            'boundary': bool(idx == 0 or idx == len(grid) - 1)}


def argmin_2comp(arr):
    if np.all(np.isnan(arr)):
        return None
    flat = int(np.nanargmin(arr.ravel()))
    i, j = np.unravel_index(flat, arr.shape)
    return {'beta_s': float(BS_GRID[i]), 'beta_c': float(BC_GRID[j]),
            'boundary': bool(i == 0 or i == len(BS_GRID) - 1 or
                              j == 0 or j == len(BC_GRID) - 1)}


def enumerate_combos_sub08():
    gamma_opts = [['OY'], ['YG'], ['YP'], ['OY', 'YG', 'YP']]
    rdm_opts = [['V1'], ['V2'], ['V3'], ['V4'], ['V1', 'V4']]
    loco_opts = [[], ['V4']]
    out = []
    for g_a, r_r, l in itertools.product(gamma_opts, rdm_opts, loco_opts):
        out.append({'gamma_pairs': g_a, 'rdm_rois': r_r, 'loco_v4': bool(l),
                     'label': f"γ{','.join(g_a)}|RDM{'+'.join(r_r)}|"
                              f"{'LOCO' if l else 'noLOCO'}"})
    return out


def enumerate_combos_sub09():
    out = []
    for inc_g, inc_r, inc_l in itertools.product([False, True], repeat=3):
        if not (inc_g or inc_r or inc_l):
            continue
        out.append({'gamma_pairs': ['GB'] if inc_g else [],
                     'rdm_rois': ['V1'] if inc_r else [],
                     'loco_v4': inc_l,
                     'label': f"γ{'GB' if inc_g else '_'}|"
                              f"RDM{'V1' if inc_r else '_'}|"
                              f"{'LOCO' if inc_l else 'noLOCO'}"})
    return out


def aic_bic(test_loss_focal, k, n=2):
    if test_loss_focal is None or not np.isfinite(test_loss_focal) or test_loss_focal <= 0:
        return None, None
    L_per_n = test_loss_focal / n
    if L_per_n <= 0:
        return None, None
    return float(2 * k + n * np.log(L_per_n)), float(k * np.log(n) + n * np.log(L_per_n))


def fit_subject(subject, combo_start=None, combo_end=None):
    config = SUBJECTS[subject]
    family = config['family']
    dl_sources = DELTA_LAMBDA_BY_FAMILY[family]
    focal_pair = config['focal_pair']
    print(f"\n[{subject}] family={family} focal={focal_pair}", flush=True)

    cvd_amps = {}
    hc_amps_all = {}
    K_by_roi = {}
    C_by_roi = {}
    for roi in ROIS:
        try:
            cvd_amps[roi] = load_amplitudes(subject, roi)
            hc_amps_all[roi] = load_hc_pool(roi)
            K_by_roi[roi] = ROI_K[roi]
            C_by_roi[roi] = create_basis_full(K_by_roi[roi], basis_type='fe')[
                HUE_ANGLES.astype(int)]
        except FileNotFoundError:
            pass

    try:
        cvd_jnd = load_jnd_per_pair(subject)
    except Exception:
        cvd_jnd = None

    combos = (enumerate_combos_sub08() if subject == 'sub-08'
               else enumerate_combos_sub09())
    if combo_start is not None and combo_end is not None:
        combos = combos[combo_start:combo_end]
        print(f"  Combo chunk: [{combo_start}:{combo_end}] = {len(combos)} combos", flush=True)
    print(f"  {len(combos)} combos × {N_RESAMPLES} resamples", flush=True)

    rng = np.random.default_rng(RNG_SEED + (0 if subject == 'sub-08' else 1))
    resample_subsets = []
    for _ in range(N_RESAMPLES):
        sel = rng.choice(len(HC_SUBJS), size=SUBSET_SIZE, replace=False)
        subset = [HC_SUBJS[i] for i in sorted(sel)]
        complement = [h for h in HC_SUBJS if h not in subset]
        resample_subsets.append((subset, complement))

    storage = {c['label']: {
        'config': c,
        **{f'rc_{src}': [] for src in dl_sources},
        '2comp': [],
    } for c in combos}

    # Test V1 RDM helper builder
    def make_test_V1_RDM(complement_pool_amps, C_baseline_v1, K_v1, cvd_v1_amp):
        if 'V1' not in cvd_amps or not complement_pool_amps:
            return None
        if len(complement_pool_amps) < 2:
            return None
        try:
            comp_W, _ = precompute_hc_W(complement_pool_amps, C_baseline_v1)
        except Exception:
            return None

        def fn(delta_8vec):
            try:
                return L_RDM(delta_8vec, cvd_v1_amp, complement_pool_amps,
                              comp_W, C_baseline_v1, K_v1, distance='correlation')
            except Exception:
                return np.nan
        return fn

    def make_test_per_pair(complement_jnd_subjs, cvd_jnd_local):
        try:
            test_bl, test_sd = jnd_baseline_from_pool(complement_jnd_subjs)
        except Exception:
            return None

        def fn(delta_8vec):
            out = {}
            perceived = (HUES + delta_8vec) % 360.0
            for p_name in PAIR_HUES.keys():
                if cvd_jnd_local is None or cvd_jnd_local.get(p_name) is None:
                    out[p_name] = None
                    continue
                if p_name not in test_bl:
                    out[p_name] = None
                    continue
                theta_a, theta_b = PAIR_HUES[p_name]
                i = int(round(theta_a / 45.0)) % 8
                j = int(round(theta_b / 45.0)) % 8
                d_phys = min(abs(theta_a - theta_b) % 360,
                               360 - abs(theta_a - theta_b) % 360)
                d_perc_raw = abs(perceived[i] - perceived[j]) % 360
                d_perc = max(min(d_perc_raw, 360 - d_perc_raw), 1e-3)
                pred = test_bl[p_name] * (d_phys / d_perc)
                sigma = max(test_sd[p_name], 1e-3)
                out[p_name] = float(((pred - cvd_jnd_local[p_name]) / sigma) ** 2)
            return out
        return fn

    t_start = time.time()
    for draw_idx, (subset, complement) in enumerate(resample_subsets):
        train_jnd = [h for h in subset if h in HC_JND_SUBJS]
        test_jnd = [h for h in complement if h in HC_JND_SUBJS]
        if not train_jnd or not test_jnd:
            continue

        atoms = {}
        for p in config['pairs']:
            fn = make_gamma_pair_atom(p, cvd_jnd, train_jnd) if cvd_jnd else None
            if fn is not None:
                atoms[f'gamma_{p}'] = fn
        for roi in config['rdm_rois']:
            if roi in cvd_amps:
                pool_amps = {h: hc_amps_all[roi][h] for h in subset
                              if h in hc_amps_all[roi]}
                if len(pool_amps) >= 2:
                    fn = make_rdm_atom(roi, cvd_amps[roi], pool_amps,
                                         C_by_roi[roi], K_by_roi[roi])
                    if fn is not None:
                        atoms[f'rdm_{roi}'] = fn
        if 'V4' in cvd_amps:
            fn = make_loco_atom(cvd_amps['V4'], K_by_roi['V4'])
            if fn is not None:
                atoms['loco_V4'] = fn

        atom_grids_rc = {src: {} for src in dl_sources}
        for src, dl in dl_sources.items():
            for name, fn in atoms.items():
                atom_grids_rc[src][name] = grid_eval_rc(fn, dl, family)
        atom_grids_2c = {name: grid_eval_2comp(fn, family)
                          for name, fn in atoms.items()}

        # Per-atom TRAIN z-stats (mean, std) for re-normalizing TEST atom values
        train_stats_rc = {src: {} for src in dl_sources}
        for src in dl_sources:
            for name in atoms.keys():
                g = atom_grids_rc[src][name]
                train_stats_rc[src][name] = (float(np.nanmean(g)),
                                             float(np.nanstd(g)))
        train_stats_2c = {}
        for name in atoms.keys():
            g = atom_grids_2c[name]
            train_stats_2c[name] = (float(np.nanmean(g)),
                                    float(np.nanstd(g)))

        # Build TEST atom closures (same forms, but using complement HC pool)
        test_atoms = {}
        for p in config['pairs']:
            fn_test = (make_gamma_pair_atom(p, cvd_jnd, test_jnd)
                       if cvd_jnd else None)
            if fn_test is not None:
                test_atoms[f'gamma_{p}'] = fn_test
        for roi in config['rdm_rois']:
            if roi in cvd_amps:
                test_pool_amps = {h: hc_amps_all[roi][h] for h in complement
                                  if h in hc_amps_all[roi]}
                if len(test_pool_amps) >= 2:
                    fn_test = make_rdm_atom(roi, cvd_amps[roi], test_pool_amps,
                                            C_by_roi[roi], K_by_roi[roi])
                    if fn_test is not None:
                        test_atoms[f'rdm_{roi}'] = fn_test
        if 'V4' in cvd_amps and 'loco_V4' in atoms:
            test_atoms['loco_V4'] = atoms['loco_V4']  # CVD-only, no HC dep

        def composite_train_test(comp_train, atom_names_local, train_stats_for_model,
                                  delta_at_argmin):
            n_a_local = len(atom_names_local)
            flat = comp_train.flatten()
            if np.all(np.isnan(flat)):
                return None, None
            train_loss = float(np.nanmin(flat))
            z_test_parts = []
            for nm in atom_names_local:
                if nm not in train_stats_for_model or nm not in test_atoms:
                    continue
                mu, sd = train_stats_for_model[nm]
                if not np.isfinite(sd) or sd < 1e-10:
                    continue
                try:
                    t_val = float(test_atoms[nm](delta_at_argmin))
                except Exception:
                    continue
                if not np.isfinite(t_val):
                    continue
                z_test_parts.append((t_val - mu) / sd)
            if not z_test_parts:
                return train_loss, None
            test_loss = float(sum(z_test_parts) / np.sqrt(n_a_local))
            return train_loss, test_loss

        # Build test loss closures on TEST (complement) baseline
        test_bl, test_sd = jnd_baseline_from_pool(test_jnd)

        def test_aggregate(delta):
            if cvd_jnd is None:
                return None
            valid = {p: cvd_jnd[p] for p in test_bl.keys()
                     if cvd_jnd.get(p) is not None and test_bl.get(p) is not None}
            if not valid:
                return None
            sd_d = {p: max(test_sd[p], 1e-3) for p in valid}
            try:
                return float(L_behav_gamma(delta, valid, test_bl, sd_d))
            except Exception:
                return None

        focal_theta_a, focal_theta_b = PAIR_HUES[focal_pair]
        f_i = int(round(focal_theta_a / 45.0)) % 8
        f_j = int(round(focal_theta_b / 45.0)) % 8
        focal_d_phys = min(abs(focal_theta_a - focal_theta_b) % 360,
                             360 - abs(focal_theta_a - focal_theta_b) % 360)
        focal_obs = cvd_jnd.get(focal_pair) if cvd_jnd else None
        focal_base = test_bl.get(focal_pair)
        focal_sd_v = max(test_sd.get(focal_pair, 1.0), 1e-3) if focal_pair in test_sd else None

        def test_focal(delta):
            if focal_obs is None or focal_base is None or focal_sd_v is None:
                return None
            perceived = (HUES + delta) % 360.0
            d_perc_raw = abs(perceived[f_i] - perceived[f_j]) % 360
            d_perc = max(min(d_perc_raw, 360 - d_perc_raw), 1e-3)
            pred = focal_base * (focal_d_phys / d_perc)
            return float(((pred - focal_obs) / focal_sd_v) ** 2)

        # Build test V1 RDM closure
        v1_pool = {h: hc_amps_all['V1'][h] for h in complement
                    if 'V1' in hc_amps_all and h in hc_amps_all['V1']}
        test_V1_RDM_fn = make_test_V1_RDM(v1_pool, C_by_roi.get('V1'),
                                            K_by_roi.get('V1', 6),
                                            cvd_amps.get('V1'))

        # Build test per-pair closure
        test_per_pair_fn = make_test_per_pair(test_jnd, cvd_jnd)

        for combo in combos:
            label = combo['label']
            atom_names = []
            for p in combo['gamma_pairs']:
                if f'gamma_{p}' in atoms:
                    atom_names.append(f'gamma_{p}')
            for roi in combo['rdm_rois']:
                if f'rdm_{roi}' in atoms:
                    atom_names.append(f'rdm_{roi}')
            if combo['loco_v4'] and 'loco_V4' in atoms:
                atom_names.append('loco_V4')
            if not atom_names:
                continue

            n_a = len(atom_names)

            for src in dl_sources:
                z_sum = None
                for name in atom_names:
                    z = zscore_grid(atom_grids_rc[src][name])
                    if np.all(np.isnan(z)):
                        z_sum = None; break
                    z_sum = z if z_sum is None else z_sum + z
                if z_sum is None:
                    continue
                comp = z_sum / np.sqrt(n_a)
                fit = argmin_rc(comp)
                if fit is None:
                    continue
                delta = forward_rc(dl_sources[src], fit['g'], family)
                train_loss, test_loss = composite_train_test(
                    comp, atom_names, train_stats_rc[src], delta)
                t_focal = test_focal(delta)
                t_agg = test_aggregate(delta)
                t_v1rdm = test_V1_RDM_fn(delta) if test_V1_RDM_fn else None
                t_pp = test_per_pair_fn(delta) if test_per_pair_fn else None
                aic, bic = aic_bic(t_focal, K_RC, n=2)
                storage[label][f'rc_{src}'].append({
                    'subset_idx': draw_idx,
                    'subset': subset, 'complement': complement,
                    'g': fit['g'], 'boundary': fit['boundary'],
                    'train_loss': train_loss, 'test_loss': test_loss,
                    'test_focal': t_focal, 'test_agg': t_agg,
                    'test_V1_RDM': t_v1rdm, 'test_per_pair': t_pp,
                    'aic': aic, 'bic': bic,
                })

            z_sum = None
            for name in atom_names:
                z = zscore_grid(atom_grids_2c[name])
                if np.all(np.isnan(z)):
                    z_sum = None; break
                z_sum = z if z_sum is None else z_sum + z
            if z_sum is None:
                continue
            comp = z_sum / np.sqrt(n_a)
            fit = argmin_2comp(comp)
            if fit is None:
                continue
            delta = forward_2comp(fit['beta_s'], fit['beta_c'], family)
            train_loss, test_loss = composite_train_test(
                comp, atom_names, train_stats_2c, delta)
            t_focal = test_focal(delta)
            t_agg = test_aggregate(delta)
            t_v1rdm = test_V1_RDM_fn(delta) if test_V1_RDM_fn else None
            t_pp = test_per_pair_fn(delta) if test_per_pair_fn else None
            aic, bic = aic_bic(t_focal, K_2C, n=2)
            storage[label]['2comp'].append({
                'subset_idx': draw_idx,
                'subset': subset, 'complement': complement,
                'beta_s': fit['beta_s'], 'beta_c': fit['beta_c'],
                'boundary': fit['boundary'],
                'train_loss': train_loss, 'test_loss': test_loss,
                'test_focal': t_focal, 'test_agg': t_agg,
                'test_V1_RDM': t_v1rdm, 'test_per_pair': t_pp,
                'aic': aic, 'bic': bic,
            })

        if (draw_idx + 1) % 20 == 0:
            elapsed = time.time() - t_start
            eta = elapsed * (N_RESAMPLES - draw_idx - 1) / (draw_idx + 1)
            print(f"  [{draw_idx + 1}/{N_RESAMPLES}] elapsed={elapsed:.0f}s eta={eta:.0f}s", flush=True)

    return storage


def median_safe(values):
    arr = np.array([v for v in values if v is not None and np.isfinite(v)])
    return float(np.median(arr)) if len(arr) else None


def iqr_safe(values):
    arr = np.array([v for v in values if v is not None and np.isfinite(v)])
    if len(arr) < 2:
        return None
    return float(np.percentile(arr, 75) - np.percentile(arr, 25))


def summarize(storage):
    out = {}
    for label, data in storage.items():
        config = data['config']
        per_model = {}
        for mkey, fits in data.items():
            if mkey == 'config':
                continue
            if not fits:
                per_model[mkey] = None
                continue
            test_focal = [f.get('test_focal') for f in fits]
            test_agg = [f.get('test_agg') for f in fits]
            test_v1rdm = [f.get('test_V1_RDM') for f in fits]
            train_loss_vals = [f.get('train_loss') for f in fits]
            test_loss_vals = [f.get('test_loss') for f in fits]
            boundary = [f.get('boundary', False) for f in fits]
            aic = [f.get('aic') for f in fits]
            bic = [f.get('bic') for f in fits]
            # Per-pair test medians
            per_pair_medians = {}
            for p in PAIR_HUES.keys():
                vals = []
                for f in fits:
                    pp = f.get('test_per_pair')
                    if pp and pp.get(p) is not None:
                        vals.append(pp[p])
                per_pair_medians[p] = median_safe(vals)

            if mkey.startswith('rc'):
                params = [f.get('g') for f in fits]
                param_summary = {
                    'g_median': median_safe(params),
                    'g_iqr': iqr_safe(params),
                }
            else:
                bs = [f.get('beta_s') for f in fits]
                bc = [f.get('beta_c') for f in fits]
                param_summary = {
                    'bs_median': median_safe(bs), 'bc_median': median_safe(bc),
                    'bs_iqr': iqr_safe(bs), 'bc_iqr': iqr_safe(bc),
                }
            per_model[mkey] = {
                'n': len(fits),
                'train_loss_median': median_safe(train_loss_vals),
                'train_loss_iqr': iqr_safe(train_loss_vals),
                'test_loss_median': median_safe(test_loss_vals),
                'test_loss_iqr': iqr_safe(test_loss_vals),
                'test_focal_median': median_safe(test_focal),
                'test_focal_iqr': iqr_safe(test_focal),
                'test_agg_median': median_safe(test_agg),
                'test_agg_iqr': iqr_safe(test_agg),
                'test_V1_RDM_median': median_safe(test_v1rdm),
                'test_V1_RDM_iqr': iqr_safe(test_v1rdm),
                'test_per_pair_medians': per_pair_medians,
                'boundary_rate': float(np.mean(boundary)) if boundary else None,
                'aic_median': median_safe(aic),
                'bic_median': median_safe(bic),
                'param_summary': param_summary,
            }
        out[label] = {'config': config, 'per_model': per_model}
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--subject', type=str, required=True,
                         choices=['sub-08', 'sub-09'])
    parser.add_argument('--combo-start', type=int, default=None)
    parser.add_argument('--combo-end', type=int, default=None)
    args = parser.parse_args()

    print("=" * 100, flush=True)
    print(f"S10b v3 — N={N_RESAMPLES} resample, extended test metrics", flush=True)
    print(f"  Tests: focal + agg + V1-RDM + per-pair (8)", flush=True)
    print(f"  Subject: {args.subject} chunk=[{args.combo_start}:{args.combo_end}]", flush=True)
    print("=" * 100, flush=True)

    t0 = time.time()
    storage = fit_subject(args.subject, args.combo_start, args.combo_end)
    summary = summarize(storage)
    elapsed = round(time.time() - t0, 1)
    print(f"\n[{args.subject}] elapsed: {elapsed}s", flush=True)

    suffix = f"_{args.subject}"
    if args.combo_start is not None:
        suffix += f"_c{args.combo_start:02d}-{args.combo_end:02d}"
    out_file = OUT_DIR / f"s10b_v3_extended_results{suffix}.json"
    with open(out_file, 'w') as f:
        json.dump({'subject': args.subject, 'storage': storage,
                    'summary': summary, 'elapsed': elapsed,
                    'meta': {'N_resamples': N_RESAMPLES, 'subset_size': SUBSET_SIZE,
                              'seed_base': RNG_SEED,
                              'combo_range': [args.combo_start, args.combo_end]}},
                   f, indent=2, default=str)
    print(f"Saved: {out_file}", flush=True)


if __name__ == "__main__":
    main()
