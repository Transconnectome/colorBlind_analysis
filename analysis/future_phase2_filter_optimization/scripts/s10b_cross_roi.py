"""S10b: Cross-ROI inclusion screening — per-subject atom-based fitting.

Per-subject admissible atoms (from Phase A precondition):
  sub-08: {γ_OY, γ_YG, γ_YP, RDM_V1, RDM_V2, RDM_V3, RDM_V4, LOCO_V4} = 8 atoms
  sub-09: {γ_GB, RDM_V1, LOCO_V4} = 3 atoms
  sub-10: control (no atoms; descriptive fit at sub-08/09 selected combos only)

Combo enumeration:
  sub-08: 40 = 4 γ × 5 RDM × 2 LOCO  (pragmatic reduction from 2^8=256)
    γ ∈ {OY, YG, YP, mean(OY,YG,YP)}
    RDM ∈ {V1, V2, V3, V4, V1+V4_joint}
    LOCO ∈ {{}, {V4}}
  sub-09: 2^3 = 8 (full powerset of 3 atoms)

For each (combo, model, subset):
  1. Build atom loss closures on subset HC as baseline
  2. Grid evaluate each atom over model param space → atom grids
  3. z-score each grid (within-grid normalization for combo summation)
  4. Composite grid = mean(z-scored atom grids) → argmin → fit params
  5. Test L_γ aggregate on complement HC at fitted params

Output: results/s10_inclusion/cross_roi_results.json + ranking table.
"""
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
COMBO_K = 5  # HC subset size for train

PAIR_KEYS = {
    'OY': 'orange-yellow',
    'YG': 'yellow-green',
    'YP': 'yellow-purple',
    'GB': 'green-blue',
}

SUBJECTS = {
    'sub-08': {'family': 'deutan', 'pairs': ['OY', 'YG', 'YP'], 'rdm_rois': ['V1', 'V2', 'V3', 'V4']},
    'sub-09': {'family': 'protan', 'pairs': ['GB'], 'rdm_rois': ['V1']},
    'sub-10': {'family': 'deutan', 'pairs': [], 'rdm_rois': []},  # control
}


def g_grid():
    return np.arange(G_MIN, G_MAX + 1e-9, G_STEP)


# ============================================================================
# Atom loss factories (return closures: δθ_8vec → scalar loss)
# ============================================================================

def make_gamma_pair_atom(pair_key, cvd_jnd, pool_jnd_subjs):
    """L_γ_pair: single-pair JND z² loss."""
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
    HUES = np.arange(0, 360, 45, dtype=float)

    def loss_fn(delta_8vec):
        perceived = (HUES + delta_8vec) % 360.0
        d_phys = abs(theta_a - theta_b) % 360
        d_phys = min(d_phys, 360 - d_phys)
        d_perc = abs(perceived[i] - perceived[j]) % 360
        d_perc = max(min(d_perc, 360 - d_perc), 1e-3)
        pred = p_base * (d_phys / d_perc)
        return ((pred - p_obs) / p_sd) ** 2

    return loss_fn


def make_rdm_atom(roi, cvd_amp, pool_amps_dict, C_baseline, K):
    """L_RDM_V*: per-ROI 1 − cos(ΔRDM_sim, ΔRDM_obs)."""
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
    """L_LOCO_V4: within-subject LOCO at V4."""
    try:
        C_baseline = create_basis_full(K_v4, basis_type='fe')[HUE_ANGLES.astype(int)]
        loco_W, _ = precompute_loco_W_within(cvd_amp_v4, C_baseline)
    except Exception:
        return None

    def loss_fn(delta_8vec):
        try:
            return L_LOCO(delta_8vec, cvd_amp_v4, loco_W, K_v4)
        except Exception:
            return np.nan

    return loss_fn


# ============================================================================
# Grid evaluation
# ============================================================================

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
    mu = np.nanmean(arr)
    sigma = np.nanstd(arr)
    if not np.isfinite(sigma) or sigma < 1e-10:
        return np.full_like(arr, np.nan)
    return (arr - mu) / sigma


def argmin_rc(arr):
    if np.all(np.isnan(arr)):
        return None
    grid = g_grid()
    idx = int(np.nanargmin(arr))
    return {
        'g_best': float(grid[idx]),
        'loss_best': float(arr[idx]),
        'boundary': bool(idx == 0 or idx == len(grid) - 1),
    }


def argmin_2comp(arr):
    if np.all(np.isnan(arr)):
        return None
    flat = int(np.nanargmin(arr.ravel()))
    i, j = np.unravel_index(flat, arr.shape)
    return {
        'beta_s_best': float(BS_GRID[i]),
        'beta_c_best': float(BC_GRID[j]),
        'loss_best': float(arr[i, j]),
        'boundary': bool(i == 0 or i == len(BS_GRID) - 1 or
                          j == 0 or j == len(BC_GRID) - 1),
    }


# ============================================================================
# Combo enumeration
# ============================================================================

def enumerate_combos_sub08():
    """40 combos: 4 γ × 5 RDM × 2 LOCO."""
    gamma_options = [['OY'], ['YG'], ['YP'], ['OY', 'YG', 'YP']]
    rdm_options = [['V1'], ['V2'], ['V3'], ['V4'], ['V1', 'V4']]
    loco_options = [[], ['V4']]
    out = []
    for g_a, r_r, l in itertools.product(gamma_options, rdm_options, loco_options):
        out.append({
            'gamma_pairs': g_a,
            'rdm_rois': r_r,
            'loco_v4': len(l) > 0,
            'label': f"γ{','.join(g_a)}|RDM{'+'.join(r_r)}|{'LOCO' if l else 'noLOCO'}",
        })
    return out


def enumerate_combos_sub09():
    """8 combos: 2^3 powerset of {γ_GB, RDM_V1, LOCO_V4}."""
    out = []
    for inc_g, inc_r, inc_l in itertools.product([False, True], repeat=3):
        if not (inc_g or inc_r or inc_l):
            continue  # skip empty
        out.append({
            'gamma_pairs': ['GB'] if inc_g else [],
            'rdm_rois': ['V1'] if inc_r else [],
            'loco_v4': inc_l,
            'label': f"γ{'GB' if inc_g else ''}|RDM{'V1' if inc_r else ''}|"
                      f"{'LOCO' if inc_l else 'noLOCO'}",
        })
    return out


# ============================================================================
# Fitting per subject
# ============================================================================

def fit_subject(subject):
    config = SUBJECTS[subject]
    if not config['pairs'] and not config['rdm_rois']:
        return None  # sub-10 control, no own atoms

    family = config['family']
    dl_sources = DELTA_LAMBDA_BY_FAMILY[family]
    print(f"\n[{subject}] family={family}")

    # Pre-load all ROI data
    cvd_amps = {}
    hc_amps_all = {}
    K_by_roi = {}
    C_by_roi = {}
    for roi in ROIS:
        try:
            cvd_amps[roi] = load_amplitudes(subject, roi)
            hc_amps_all[roi] = load_hc_pool(roi)
            K_by_roi[roi] = ROI_K[roi]
            C_by_roi[roi] = create_basis_full(K_by_roi[roi], basis_type='fe')[HUE_ANGLES.astype(int)]
        except FileNotFoundError:
            print(f"  WARNING: {subject} {roi} amp missing")

    try:
        cvd_jnd = load_jnd_per_pair(subject)
    except Exception:
        cvd_jnd = None

    # Enumerate combos
    if subject == 'sub-08':
        combos = enumerate_combos_sub08()
    elif subject == 'sub-09':
        combos = enumerate_combos_sub09()
    else:
        return None
    print(f"  {len(combos)} combos")

    # HC subsets (k=5)
    subsets = list(itertools.combinations(HC_SUBJS, COMBO_K))
    print(f"  {len(subsets)} subsets")

    combo_results = {c['label']: {
        'config': c, 'rc_DPS_lit': [], 'rc_Boehm_low': [], 'rc_Boehm_mid': [],
        'rc_JND_Lamb': [], '2comp': [],
    } for c in combos}

    for sub_idx, subset in enumerate(subsets):
        subset = list(subset)
        complement = [h for h in HC_SUBJS if h not in subset]

        # Train pool JND
        train_jnd = [h for h in subset if h in HC_JND_SUBJS]
        if not train_jnd:
            continue
        # Test pool JND
        test_jnd = [h for h in complement if h in HC_JND_SUBJS]
        if not test_jnd:
            continue

        # Build atom evaluators on TRAIN pool
        atoms = {}  # name → loss_fn closure
        # γ pairs
        for p in config['pairs']:
            fn = make_gamma_pair_atom(p, cvd_jnd, train_jnd) if cvd_jnd else None
            if fn is not None:
                atoms[f'gamma_{p}'] = fn
        # RDM per ROI
        for roi in config['rdm_rois']:
            if roi in cvd_amps and len(hc_amps_all.get(roi, {})) >= 2:
                pool_amps = {h: hc_amps_all[roi][h] for h in subset if h in hc_amps_all[roi]}
                if len(pool_amps) >= 2:
                    fn = make_rdm_atom(roi, cvd_amps[roi], pool_amps,
                                         C_by_roi[roi], K_by_roi[roi])
                    if fn is not None:
                        atoms[f'rdm_{roi}'] = fn
        # LOCO V4
        if 'V4' in cvd_amps:
            fn = make_loco_atom(cvd_amps['V4'], K_by_roi['V4'])
            if fn is not None:
                atoms['loco_V4'] = fn

        # Grid evaluate atoms (cache across combos)
        atom_grids_rc = {}  # src → atom_name → grid
        for src, dl in dl_sources.items():
            atom_grids_rc[src] = {}
            for name, fn in atoms.items():
                atom_grids_rc[src][name] = grid_eval_rc(fn, dl, family)
        atom_grids_2c = {}
        for name, fn in atoms.items():
            atom_grids_2c[name] = grid_eval_2comp(fn, family)

        # Build test L_γ aggregate AND per-pair (always on complement)
        test_bl, test_sd = jnd_baseline_from_pool(test_jnd)
        def test_L_gamma(delta):
            """Aggregate test L_γ across all pairs."""
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

        # Per-subject focal test pair: γ_GB for sub-09, γ_YP for sub-08
        FOCAL_PAIR = {'sub-08': 'yellow-purple', 'sub-09': 'green-blue'}[subject]
        focal_theta_a, focal_theta_b = PAIR_HUES[FOCAL_PAIR]
        focal_i = int(round(focal_theta_a / 45.0)) % 8
        focal_j = int(round(focal_theta_b / 45.0)) % 8
        focal_d_phys = abs(focal_theta_a - focal_theta_b) % 360
        focal_d_phys = min(focal_d_phys, 360 - focal_d_phys)
        focal_obs = cvd_jnd.get(FOCAL_PAIR) if cvd_jnd else None
        focal_base = test_bl.get(FOCAL_PAIR)
        focal_sd_v = max(test_sd.get(FOCAL_PAIR, 1.0), 1e-3) if FOCAL_PAIR in test_sd else None

        def test_L_gamma_focal(delta):
            """Single-pair test L_γ for focal pair (per-subject specific)."""
            if focal_obs is None or focal_base is None or focal_sd_v is None:
                return None
            HUES = np.arange(0, 360, 45, dtype=float)
            perceived = (HUES + delta) % 360.0
            d_perc = abs(perceived[focal_i] - perceived[focal_j]) % 360
            d_perc = max(min(d_perc, 360 - d_perc), 1e-3)
            pred = focal_base * (focal_d_phys / d_perc)
            return float(((pred - focal_obs) / focal_sd_v) ** 2)

        # Per combo: build composite & fit
        for combo in combos:
            label = combo['label']
            # Identify which atom names this combo uses
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
                continue  # combo's atoms not available

            n_atoms = len(atom_names)

            # R+C fits (per Δλ source)
            for src in dl_sources:
                z_sum = None
                for name in atom_names:
                    grid = atom_grids_rc[src][name]
                    z = zscore_grid(grid)
                    if np.all(np.isnan(z)):
                        z_sum = None
                        break
                    z_sum = z if z_sum is None else z_sum + z
                if z_sum is None:
                    continue
                composite = z_sum / np.sqrt(n_atoms)
                fit = argmin_rc(composite)
                if fit is None:
                    continue
                # Compute test L_γ at fit (aggregate + focal pair)
                delta = forward_rc(dl_sources[src], fit['g_best'], family)
                test_loss = test_L_gamma(delta)
                test_focal = test_L_gamma_focal(delta)
                combo_results[label][f'rc_{src}'].append({
                    'subset_idx': sub_idx, 'g': fit['g_best'],
                    'train_z_loss': fit['loss_best'], 'boundary': fit['boundary'],
                    'test_L_gamma': test_loss, 'test_L_gamma_focal': test_focal,
                })

            # 2-comp fit
            z_sum_2c = None
            for name in atom_names:
                z = zscore_grid(atom_grids_2c[name])
                if np.all(np.isnan(z)):
                    z_sum_2c = None
                    break
                z_sum_2c = z if z_sum_2c is None else z_sum_2c + z
            if z_sum_2c is None:
                continue
            composite_2c = z_sum_2c / np.sqrt(n_atoms)
            fit = argmin_2comp(composite_2c)
            if fit is None:
                continue
            delta = forward_2comp(fit['beta_s_best'], fit['beta_c_best'], family)
            test_loss = test_L_gamma(delta)
            test_focal = test_L_gamma_focal(delta)
            combo_results[label]['2comp'].append({
                'subset_idx': sub_idx,
                'beta_s': fit['beta_s_best'], 'beta_c': fit['beta_c_best'],
                'train_z_loss': fit['loss_best'], 'boundary': fit['boundary'],
                'test_L_gamma': test_loss, 'test_L_gamma_focal': test_focal,
            })

        if (sub_idx + 1) % 5 == 0:
            print(f"    [{sub_idx + 1}/{len(subsets)}] subsets done")

    return combo_results


def median_safe(values):
    arr = np.array([v for v in values if v is not None and np.isfinite(v)])
    return float(np.median(arr)) if len(arr) else None


def summarize_subject(subject, combo_results):
    """Aggregate per-combo statistics: median test L_γ, boundary rate, n."""
    summary = {}
    for label, data in combo_results.items():
        summary[label] = {'config': data['config']}
        for model_key in ['rc_DPS_lit', 'rc_Boehm_low', 'rc_Boehm_mid',
                           'rc_JND_Lamb', '2comp']:
            fits = data.get(model_key, [])
            test_losses = [f['test_L_gamma'] for f in fits]
            test_focal_losses = [f.get('test_L_gamma_focal') for f in fits]
            params = [f.get('g', None) if model_key.startswith('rc')
                       else (f.get('beta_s'), f.get('beta_c')) for f in fits]
            valid_params = [p for p in params if p is not None
                             and (not isinstance(p, tuple) or p[0] is not None)]
            boundary = [f.get('boundary', False) for f in fits]
            summary[label][model_key] = {
                'median_test_L_gamma': median_safe(test_losses),
                'median_test_L_focal': median_safe(test_focal_losses),
                'iqr_test_L_gamma': (
                    float(np.percentile([t for t in test_losses if t is not None],
                                          75) -
                          np.percentile([t for t in test_losses if t is not None],
                                          25))
                    if len([t for t in test_losses if t is not None]) >= 2 else None
                ),
                'param_summary': (
                    {'g_median': median_safe([p for p in params if p is not None]),
                      'g_sd': float(np.std([p for p in params if p is not None], ddof=1))
                            if len([p for p in params if p is not None]) >= 2 else None}
                    if model_key.startswith('rc') else
                    {'bs_median': float(np.median([p[0] for p in valid_params])) if valid_params else None,
                      'bc_median': float(np.median([p[1] for p in valid_params])) if valid_params else None}
                ),
                'boundary_rate': float(np.mean(boundary)) if boundary else None,
                'n_subsets': len(fits),
            }
    return summary


def main():
    print("=" * 100)
    print("S10b Cross-ROI Inclusion Screening — per-subject atom-based fits")
    print("=" * 100)

    all_results = {}
    for subject in ['sub-08', 'sub-09']:
        t0 = time.time()
        cr = fit_subject(subject)
        if cr is None:
            continue
        all_results[subject] = {
            'combo_results': cr,
            'summary': summarize_subject(subject, cr),
            'elapsed': round(time.time() - t0, 1),
        }
        print(f"  {subject} elapsed: {all_results[subject]['elapsed']}s")

    out_file = OUT_DIR / "cross_roi_results.json"
    with open(out_file, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\nSaved: {out_file}")

    # Ranking table
    print("\n" + "=" * 120)
    print("RANKING — median test L_γ per (subject, combo, model)")
    print("=" * 120)
    for subject, data in all_results.items():
        print(f"\n[{subject}]")
        # Collect (label, model, median, boundary, n) tuples
        rows = []
        for label, smry in data['summary'].items():
            for model_key in ['rc_DPS_lit', 'rc_Boehm_low', 'rc_Boehm_mid',
                               'rc_JND_Lamb', '2comp']:
                m = smry[model_key]
                if m['median_test_L_gamma'] is not None and m['n_subsets'] >= 10:
                    rows.append({
                        'label': label, 'model': model_key,
                        'median_agg': m['median_test_L_gamma'],
                        'median_focal': m.get('median_test_L_focal'),
                        'iqr': m['iqr_test_L_gamma'],
                        'boundary': m['boundary_rate'],
                        'n': m['n_subsets'],
                    })
        # Filter stable (boundary < 0.5)
        stable = [r for r in rows if r['boundary'] is not None and r['boundary'] < 0.5]
        print(f"  Top 10 STABLE (boundary < 0.5, sorted by median focal test L_γ):")
        stable.sort(key=lambda r: (r['median_focal'] if r['median_focal'] is not None else 1e9))
        print(f"  {'#':>3s} | {'Combo':40s} | {'Model':14s} | "
              f"{'agg':>7s} | {'focal':>7s} | bdy | n")
        print("  " + "-" * 110)
        for rank, r in enumerate(stable[:10], start=1):
            f_s = f"{r['median_focal']:.3f}" if r['median_focal'] is not None else "NA"
            print(f"  {rank:3d} | {r['label']:40s} | {r['model']:14s} | "
                  f"{r['median_agg']:7.2f} | {f_s:>7s} | {r['boundary']:.2f} | {r['n']}")


if __name__ == "__main__":
    t0 = time.time()
    main()
    print(f"\nTotal elapsed: {time.time() - t0:.1f}s")
