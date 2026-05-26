"""S12 Phase C — Weight sweep on 2-simplex Dirichlet (3-atom) / 1-simplex (2-atom).

Operates WITHOUT prior or smoothing penalty (decision locked: Task #50/#52/#53).
Uses Phase B v3 atoms (γ pair JND, RDM per ROI, LOCO V4) and the Phase C composite:

    L_composite(δθ; w) = Σ_a w_a · z_a(L_a(δθ))

with Σ w_a = 1 (simplex constraint). NO `1/√n_a` normalization — weights already sum to 1.

Per-candidate Δλ is fixed (NOT swept):
    sub-08 C3 → DPS_lit (6.0 nm deutan)
    sub-09 C2 → JND_Lamb (1.5 nm protan)
    2-comp candidates have no Δλ.

For each (candidate × weight cell), runs N_RESAMPLES = 100 HC 5/2 subset draws.

Storage (per fit):
    subset, complement, g or (beta_s, beta_c), boundary, train_loss, test_loss,
    test_focal, test_agg, test_V1_RDM, test_per_pair, aic, bic

The Phase-B-compatible test_* fields use the complement HC pool exactly as v3
(s10b_v3_extended.py). The new train_loss/test_loss use the Phase C composite
(no √n_a factor).

Loop structure (per advisor #3):
    for candidate:
        for resample r=1..N:
            build atoms once (expensive)
            grid-eval each atom once (expensive)
            compute per-atom z-scored grids once (expensive)
            for weight_cell w:                    # cheap dot products
                comp = Σ w_a · z_grid_a
                argmin → record
"""
import argparse
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

OUT_DIR = SCRIPT_DIR.parent / "results" / "s12_phase_c"
OUT_DIR.mkdir(parents=True, exist_ok=True)

HC_SUBJS = ['sub-01', 'sub-02', 'sub-03', 'sub-04', 'sub-05', 'sub-06', 'sub-07']
ROIS = ['V1', 'V2', 'V3', 'V4']

N_RESAMPLES = 100
SUBSET_SIZE = 5
RNG_SEED = 42

K_RC = 1
K_2C = 2
HUES = np.arange(0, 360, 45, dtype=float)


# ---------------------------------------------------------------------------
# Candidate definitions (locked per PIPELINE_UPDATED_0524.md §S5.1)
# ---------------------------------------------------------------------------

CANDIDATES = {
    'sub-08': [
        {
            'id': 'C1',
            'label': 'γYG|RDMV1+V4|noLOCO',
            'model': '2comp',
            'family': 'deutan',
            'dl_source': None,
            'gamma_pairs': ['YG'],
            'rdm_rois': ['V1', 'V4'],
            'loco_v4': False,
            'atom_names': ['gamma_YG', 'rdm_V1', 'rdm_V4'],
            'focal_pair': 'yellow-purple',
        },
        {
            'id': 'C2',
            'label': 'γYG|RDMV2|LOCO',
            'model': '2comp',
            'family': 'deutan',
            'dl_source': None,
            'gamma_pairs': ['YG'],
            'rdm_rois': ['V2'],
            'loco_v4': True,
            'atom_names': ['gamma_YG', 'rdm_V2', 'loco_V4'],
            'focal_pair': 'yellow-purple',
        },
        {
            'id': 'C3',
            'label': 'γOY|RDMV2|LOCO',
            'model': 'rc',
            'family': 'deutan',
            'dl_source': 'DPS_lit',
            'gamma_pairs': ['OY'],
            'rdm_rois': ['V2'],
            'loco_v4': True,
            'atom_names': ['gamma_OY', 'rdm_V2', 'loco_V4'],
            'focal_pair': 'yellow-purple',
        },
    ],
    'sub-09': [
        {
            'id': 'C2',
            'label': 'γGB|RDMV1|noLOCO',
            'model': 'rc',
            'family': 'protan',
            'dl_source': 'JND_Lamb',
            'gamma_pairs': ['GB'],
            'rdm_rois': ['V1'],
            'loco_v4': False,
            'atom_names': ['gamma_GB', 'rdm_V1'],
            'focal_pair': 'green-blue',
        },
    ],
}


# ---------------------------------------------------------------------------
# Weight grids
# ---------------------------------------------------------------------------

WEIGHTS_3ATOM = [
    (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0),            # vertices
    (0.5, 0.5, 0.0), (0.5, 0.0, 0.5), (0.0, 0.5, 0.5),            # edge midpoints
    (0.6, 0.2, 0.2), (0.2, 0.6, 0.2), (0.2, 0.2, 0.6),            # off-vertex
    (1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0),                              # centroid
]

WEIGHTS_2ATOM = [
    (1.0, 0.0), (0.75, 0.25), (0.5, 0.5), (0.25, 0.75), (0.0, 1.0),
]


def get_weight_grid(n_atoms):
    if n_atoms == 3:
        return WEIGHTS_3ATOM
    if n_atoms == 2:
        return WEIGHTS_2ATOM
    raise ValueError(f"No weight grid for n_atoms={n_atoms}")


# ---------------------------------------------------------------------------
# Atom builders (cloned from s10b_v3_extended.py)
# ---------------------------------------------------------------------------

PAIR_KEYS = {'OY': 'orange-yellow', 'YG': 'yellow-green',
              'YP': 'yellow-purple', 'GB': 'green-blue'}


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


# ---------------------------------------------------------------------------
# Grid evaluation
# ---------------------------------------------------------------------------

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
            'boundary': bool(idx == 0 or idx == len(grid) - 1),
            'idx': idx}


def argmin_2comp(arr):
    if np.all(np.isnan(arr)):
        return None
    flat = int(np.nanargmin(arr.ravel()))
    i, j = np.unravel_index(flat, arr.shape)
    return {'beta_s': float(BS_GRID[i]), 'beta_c': float(BC_GRID[j]),
            'boundary': bool(i == 0 or i == len(BS_GRID) - 1 or
                              j == 0 or j == len(BC_GRID) - 1),
            'idx': (int(i), int(j))}


def aic_bic(test_loss_focal, k, n=2):
    if test_loss_focal is None or not np.isfinite(test_loss_focal) or test_loss_focal <= 0:
        return None, None
    L_per_n = test_loss_focal / n
    if L_per_n <= 0:
        return None, None
    return float(2 * k + n * np.log(L_per_n)), float(k * np.log(n) + n * np.log(L_per_n))


# ---------------------------------------------------------------------------
# Main per-subject driver
# ---------------------------------------------------------------------------

def run_candidate(candidate, subject, cvd_amps, hc_amps_all, K_by_roi, C_by_roi,
                   cvd_jnd, n_resamples=N_RESAMPLES, progress_cb=None):
    """Run weight sweep for one candidate.

    Returns dict[weight_tuple_str] = list of fit records.
    """
    family = candidate['family']
    model = candidate['model']
    atom_names_expected = candidate['atom_names']
    focal_pair = candidate['focal_pair']
    n_atoms = len(atom_names_expected)
    weight_grid = get_weight_grid(n_atoms)

    # Δλ for R+C (single source, not swept)
    dl = None
    if model == 'rc':
        dl_dict = DELTA_LAMBDA_BY_FAMILY[family]
        dl = dl_dict[candidate['dl_source']]

    # Resample plan (deterministic; same seed offset by subject in v3)
    rng = np.random.default_rng(RNG_SEED + (0 if subject == 'sub-08' else 1))
    resample_subsets = []
    for _ in range(n_resamples):
        sel = rng.choice(len(HC_SUBJS), size=SUBSET_SIZE, replace=False)
        subset = [HC_SUBJS[i] for i in sorted(sel)]
        complement = [h for h in HC_SUBJS if h not in subset]
        resample_subsets.append((subset, complement))

    # Storage: keyed by weight tuple
    storage = {repr(tuple(w)): [] for w in weight_grid}

    focal_theta_a, focal_theta_b = PAIR_HUES[focal_pair]
    f_i = int(round(focal_theta_a / 45.0)) % 8
    f_j = int(round(focal_theta_b / 45.0)) % 8
    focal_d_phys = min(abs(focal_theta_a - focal_theta_b) % 360,
                        360 - abs(focal_theta_a - focal_theta_b) % 360)
    focal_obs = cvd_jnd.get(focal_pair) if cvd_jnd else None

    t_start = time.time()

    for draw_idx, (subset, complement) in enumerate(resample_subsets):
        train_jnd = [h for h in subset if h in HC_JND_SUBJS]
        test_jnd = [h for h in complement if h in HC_JND_SUBJS]
        if not train_jnd or not test_jnd:
            continue

        # ---- Build TRAIN atoms ----
        train_atoms = {}
        for p in candidate['gamma_pairs']:
            fn = make_gamma_pair_atom(p, cvd_jnd, train_jnd) if cvd_jnd else None
            if fn is not None:
                train_atoms[f'gamma_{p}'] = fn
        for roi in candidate['rdm_rois']:
            if roi in cvd_amps:
                pool_amps = {h: hc_amps_all[roi][h] for h in subset
                              if h in hc_amps_all[roi]}
                if len(pool_amps) >= 2:
                    fn = make_rdm_atom(roi, cvd_amps[roi], pool_amps,
                                         C_by_roi[roi], K_by_roi[roi])
                    if fn is not None:
                        train_atoms[f'rdm_{roi}'] = fn
        if candidate['loco_v4'] and 'V4' in cvd_amps:
            fn = make_loco_atom(cvd_amps['V4'], K_by_roi['V4'])
            if fn is not None:
                train_atoms['loco_V4'] = fn

        # Skip if any expected atom missing
        if not all(a in train_atoms for a in atom_names_expected):
            continue

        # ---- Grid-eval each atom once ----
        if model == 'rc':
            atom_grids = {nm: grid_eval_rc(train_atoms[nm], dl, family)
                           for nm in atom_names_expected}
        else:
            atom_grids = {nm: grid_eval_2comp(train_atoms[nm], family)
                           for nm in atom_names_expected}

        # ---- Per-atom train z-stats (for test_loss re-normalization) ----
        train_stats = {}
        for nm in atom_names_expected:
            g_arr = atom_grids[nm]
            train_stats[nm] = (float(np.nanmean(g_arr)),
                                float(np.nanstd(g_arr)))

        # ---- Pre-compute z-scored grids ----
        z_grids = {nm: zscore_grid(atom_grids[nm]) for nm in atom_names_expected}

        # Bail if any z is all-nan
        if any(np.all(np.isnan(z_grids[nm])) for nm in atom_names_expected):
            continue

        # ---- Build TEST atom closures (complement HC pool) ----
        test_atoms = {}
        for p in candidate['gamma_pairs']:
            fn_test = (make_gamma_pair_atom(p, cvd_jnd, test_jnd)
                       if cvd_jnd else None)
            if fn_test is not None:
                test_atoms[f'gamma_{p}'] = fn_test
        for roi in candidate['rdm_rois']:
            if roi in cvd_amps:
                test_pool = {h: hc_amps_all[roi][h] for h in complement
                              if h in hc_amps_all[roi]}
                if len(test_pool) >= 2:
                    fn_test = make_rdm_atom(roi, cvd_amps[roi], test_pool,
                                            C_by_roi[roi], K_by_roi[roi])
                    if fn_test is not None:
                        test_atoms[f'rdm_{roi}'] = fn_test
        if candidate['loco_v4'] and 'V4' in cvd_amps and 'loco_V4' in train_atoms:
            test_atoms['loco_V4'] = train_atoms['loco_V4']

        # ---- Phase-B-compatible test_* closures ----
        try:
            test_bl, test_sd = jnd_baseline_from_pool(test_jnd)
        except Exception:
            test_bl, test_sd = {}, {}

        focal_base = test_bl.get(focal_pair)
        focal_sd_v = max(test_sd.get(focal_pair, 1.0), 1e-3) if focal_pair in test_sd else None

        def test_focal_fn(delta):
            if focal_obs is None or focal_base is None or focal_sd_v is None:
                return None
            perceived = (HUES + delta) % 360.0
            d_perc_raw = abs(perceived[f_i] - perceived[f_j]) % 360
            d_perc = max(min(d_perc_raw, 360 - d_perc_raw), 1e-3)
            pred = focal_base * (focal_d_phys / d_perc)
            return float(((pred - focal_obs) / focal_sd_v) ** 2)

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

        # V1 RDM test closure (Phase B-compatible probe)
        v1_pool = {h: hc_amps_all['V1'][h] for h in complement
                    if 'V1' in hc_amps_all and h in hc_amps_all['V1']}
        test_V1_RDM_fn = None
        if 'V1' in cvd_amps and len(v1_pool) >= 2:
            try:
                v1_W, _ = precompute_hc_W(v1_pool, C_by_roi['V1'])

                def test_V1_RDM_fn(delta_8vec, _W=v1_W, _pool=v1_pool,
                                    _C=C_by_roi['V1'], _K=K_by_roi['V1'],
                                    _cvd=cvd_amps['V1']):
                    try:
                        return L_RDM(delta_8vec, _cvd, _pool, _W, _C, _K,
                                      distance='correlation')
                    except Exception:
                        return np.nan
            except Exception:
                test_V1_RDM_fn = None

        def test_per_pair_fn(delta):
            out = {}
            perceived = (HUES + delta) % 360.0
            for p_name in PAIR_HUES.keys():
                if cvd_jnd is None or cvd_jnd.get(p_name) is None:
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
                out[p_name] = float(((pred - cvd_jnd[p_name]) / sigma) ** 2)
            return out

        # ---- Loop weight cells (cheap dot products) ----
        for w in weight_grid:
            # composite = Σ w_a · z_grid_a (NO 1/√n_a normalization)
            comp = None
            for nm, wa in zip(atom_names_expected, w):
                if wa == 0.0:
                    continue
                z = z_grids[nm]
                comp = wa * z if comp is None else comp + wa * z
            if comp is None:
                # all-zero weight (shouldn't happen since Σ=1) — skip
                continue

            # argmin on composite grid
            if model == 'rc':
                fit = argmin_rc(comp)
            else:
                fit = argmin_2comp(comp)
            if fit is None:
                continue

            # delta at argmin
            if model == 'rc':
                delta = forward_rc(dl, fit['g'], family)
            else:
                delta = forward_2comp(fit['beta_s'], fit['beta_c'], family)

            # train_loss = composite value at argmin
            if model == 'rc':
                train_loss = float(comp[fit['idx']])
            else:
                ii, jj = fit['idx']
                train_loss = float(comp[ii, jj])

            # test_loss = Σ w_a · z_a(L_a^test(delta))
            # using TRAIN atom z-stats (mu, sd) to standardize test atom values
            test_loss = None
            z_test_parts = []
            for nm, wa in zip(atom_names_expected, w):
                if wa == 0.0:
                    continue
                if nm not in test_atoms or nm not in train_stats:
                    z_test_parts = None
                    break
                mu, sd = train_stats[nm]
                if not np.isfinite(sd) or sd < 1e-10:
                    z_test_parts = None
                    break
                try:
                    t_val = float(test_atoms[nm](delta))
                except Exception:
                    z_test_parts = None
                    break
                if not np.isfinite(t_val):
                    z_test_parts = None
                    break
                z_test_parts.append(wa * (t_val - mu) / sd)
            if z_test_parts is not None and z_test_parts:
                test_loss = float(sum(z_test_parts))

            # Phase-B-compatible probes
            t_focal = test_focal_fn(delta)
            t_agg = test_aggregate(delta)
            t_v1rdm = (float(test_V1_RDM_fn(delta))
                        if test_V1_RDM_fn is not None else None)
            if t_v1rdm is not None and not np.isfinite(t_v1rdm):
                t_v1rdm = None
            t_pp = test_per_pair_fn(delta)

            k_model = K_RC if model == 'rc' else K_2C
            aic, bic = aic_bic(t_focal, k_model, n=2)

            record = {
                'subset_idx': draw_idx,
                'subset': subset, 'complement': complement,
                'weight': list(w),
                'boundary': fit['boundary'],
                'train_loss': train_loss, 'test_loss': test_loss,
                'test_focal': t_focal, 'test_agg': t_agg,
                'test_V1_RDM': t_v1rdm, 'test_per_pair': t_pp,
                'aic': aic, 'bic': bic,
            }
            if model == 'rc':
                record['g'] = fit['g']
            else:
                record['beta_s'] = fit['beta_s']
                record['beta_c'] = fit['beta_c']

            storage[repr(tuple(w))].append(record)

        if progress_cb is not None and (draw_idx + 1) % 10 == 0:
            elapsed = time.time() - t_start
            progress_cb(draw_idx + 1, n_resamples, elapsed)

    return storage


# ---------------------------------------------------------------------------
# Summary helpers
# ---------------------------------------------------------------------------

def median_safe(values):
    arr = np.array([v for v in values if v is not None and np.isfinite(v)])
    return float(np.median(arr)) if len(arr) else None


def iqr_safe(values):
    arr = np.array([v for v in values if v is not None and np.isfinite(v)])
    if len(arr) < 2:
        return None
    return float(np.percentile(arr, 75) - np.percentile(arr, 25))


def summarize(storage, model):
    out = {}
    for wkey, fits in storage.items():
        if not fits:
            out[wkey] = None
            continue
        train_loss_vals = [f.get('train_loss') for f in fits]
        test_loss_vals = [f.get('test_loss') for f in fits]
        test_focal = [f.get('test_focal') for f in fits]
        test_agg = [f.get('test_agg') for f in fits]
        test_v1rdm = [f.get('test_V1_RDM') for f in fits]
        boundary = [f.get('boundary', False) for f in fits]
        aic = [f.get('aic') for f in fits]
        bic = [f.get('bic') for f in fits]

        if model == 'rc':
            params = [f.get('g') for f in fits]
            param_summary = {
                'g_median': median_safe(params),
                'g_iqr': iqr_safe(params),
            }
        else:
            bs = [f.get('beta_s') for f in fits]
            bc = [f.get('beta_c') for f in fits]
            param_summary = {
                'bs_median': median_safe(bs),
                'bc_median': median_safe(bc),
                'bs_iqr': iqr_safe(bs),
                'bc_iqr': iqr_safe(bc),
            }

        per_pair_medians = {}
        for p in PAIR_HUES.keys():
            vals = []
            for f in fits:
                pp = f.get('test_per_pair')
                if pp and pp.get(p) is not None:
                    vals.append(pp[p])
            per_pair_medians[p] = median_safe(vals)

        out[wkey] = {
            'n': len(fits),
            'weight': fits[0]['weight'],
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
    return out


# ---------------------------------------------------------------------------
# Per-subject orchestrator
# ---------------------------------------------------------------------------

def load_subject_data(subject):
    cvd_amps, hc_amps_all, K_by_roi, C_by_roi = {}, {}, {}, {}
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
    return cvd_amps, hc_amps_all, K_by_roi, C_by_roi, cvd_jnd


def run_subject(subject, only_candidate=None, n_resamples=N_RESAMPLES):
    print(f"\n[{subject}] loading data...", flush=True)
    cvd_amps, hc_amps_all, K_by_roi, C_by_roi, cvd_jnd = load_subject_data(subject)
    if not cvd_amps:
        raise RuntimeError(f"No CVD amplitudes loaded for {subject}")

    candidates = CANDIDATES[subject]
    if only_candidate:
        candidates = [c for c in candidates if c['id'] == only_candidate]
        if not candidates:
            raise ValueError(f"Candidate {only_candidate} not in {subject}")

    all_storage = {}
    all_summary = {}
    n_cells_total = sum(len(get_weight_grid(len(c['atom_names'])))
                         for c in candidates)
    print(f"  candidates: {[c['id'] for c in candidates]}", flush=True)
    print(f"  total weight cells: {n_cells_total} × N={n_resamples} resamples", flush=True)

    t_subject = time.time()
    for cand in candidates:
        t_cand = time.time()
        n_atoms = len(cand['atom_names'])
        weight_grid = get_weight_grid(n_atoms)
        print(f"\n  [{cand['id']}] {cand['label']} model={cand['model']} "
              f"dl_source={cand['dl_source']} n_atoms={n_atoms} "
              f"n_weights={len(weight_grid)}", flush=True)

        def progress_cb(done, total, elapsed):
            eta = elapsed * (total - done) / max(done, 1)
            print(f"    resample [{done}/{total}] elapsed={elapsed:.0f}s eta={eta:.0f}s",
                  flush=True)

        storage = run_candidate(cand, subject, cvd_amps, hc_amps_all,
                                  K_by_roi, C_by_roi, cvd_jnd,
                                  n_resamples=n_resamples,
                                  progress_cb=progress_cb)
        summary = summarize(storage, cand['model'])
        all_storage[cand['id']] = {'config': cand, 'storage': storage}
        all_summary[cand['id']] = {'config': cand, 'summary': summary}

        t_done = time.time() - t_cand
        print(f"  [{cand['id']}] DONE elapsed={t_done:.0f}s", flush=True)

    elapsed_subject = time.time() - t_subject
    return all_storage, all_summary, elapsed_subject


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--subject', type=str, required=True,
                         choices=['sub-08', 'sub-09'])
    parser.add_argument('--candidate', type=str, default=None,
                         help='Optional: run only this candidate id (e.g. C1)')
    parser.add_argument('--n-resamples', type=int, default=N_RESAMPLES)
    parser.add_argument('--out-suffix', type=str, default='',
                         help='Optional output filename suffix')
    args = parser.parse_args()

    print("=" * 100, flush=True)
    print(f"S12 Phase C — weight sweep (no prior/smoothing)", flush=True)
    print(f"  Subject: {args.subject}  candidate={args.candidate}  N={args.n_resamples}",
          flush=True)
    print("=" * 100, flush=True)

    t0 = time.time()
    all_storage, all_summary, elapsed_subject = run_subject(
        args.subject, args.candidate, args.n_resamples)
    elapsed_total = round(time.time() - t0, 1)
    print(f"\n[{args.subject}] total elapsed: {elapsed_total}s", flush=True)

    suffix = args.out_suffix
    if args.candidate:
        suffix = f"_{args.candidate}{suffix}"
    out_file = OUT_DIR / f"sweep_{args.subject}{suffix}.json"
    with open(out_file, 'w') as f:
        json.dump({'subject': args.subject,
                    'candidate_filter': args.candidate,
                    'candidates': all_storage,
                    'summary': all_summary,
                    'elapsed_total': elapsed_total,
                    'meta': {
                        'n_resamples': args.n_resamples,
                        'subset_size': SUBSET_SIZE,
                        'seed_base': RNG_SEED,
                        'weights_3atom': WEIGHTS_3ATOM,
                        'weights_2atom': WEIGHTS_2ATOM,
                        'note': 'Phase C — Σ w_a·z(L_a), NO 1/√n_a normalization. '
                                 'No prior/smoothing penalty (locked).',
                    }},
                   f, indent=2, default=str)
    print(f"Saved: {out_file}", flush=True)


if __name__ == "__main__":
    main()
