"""S17 SRM-RDM variant: Strict HC LOO (leave-one-HC-out, deterministic 7-fold)
on Phase B v6 SRM-cosine RDM candidates.

Mirror of `s17_hc_loo.py`, but the RDM atom is the SRM-aligned variant from
`s10b_v6_srm_rdm.py` (BrainIAK SRM in shared K-d space) instead of the PCA-based
atom. The SRM module monkey-patches `s10b_v6_pca_rdm.make_rdm_atom` on import,
so we load the SRM module first and then grab the now-replaced atom factory.

Candidates (Phase B v6 SRM-cosine medians, 2-Component model):

  S08-srm-stable    sub-08 deutan   γALL|RDMV1|noLOCO   β_s= 22, β_c=-36
  S08-srm-robust    sub-08 deutan   γOY|RDMV2|noLOCO    β_s=  8, β_c=-42
  S09-srm-primary   sub-09 protan   γALL|RDMV1|noLOCO   β_s= 32, β_c=  0

n=1 RDM test handling
---------------------
The SRM atom requires `len(pool) >= 2` (BrainIAK SRM cannot train on a single
subject). The PCA `make_rdm_atom_n1ok` patch is *not* applied here — for n=1
test pools, the RDM test atom returns None and is silently skipped. This means
`test_loss` may be None for every fold when the candidate has no LOCO atom and
its gamma pairs cannot be evaluated with n=1 (all three SRM candidates are
noLOCO; their `test_loss` will be None for every fold). This does not affect
the primary deliverable (train-grid argmin per fold → bs/bc median/IQR/range).

Output: `results/s10_inclusion/s17_srm_hc_loo_results.json`

Run:
  mpirun -np 1 python3 s17_srm_hc_loo.py
"""
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

# Direct imports
from rc_1dof import forward_rc, G_MIN, G_MAX, G_STEP
from two_comp import forward_2comp, BS_GRID, BC_GRID
from neural_loss import (
    load_amplitudes, load_hc_pool, ROI_K,
    precompute_loco_W_within, L_LOCO,
)
from behav_loss import (
    load_jnd_per_pair, L_behav_gamma, PAIR_HUES, HC_JND_SUBJS,
)
from utils_forward_model import create_basis_full, HUE_ANGLES
from s8_loo_train_test import jnd_baseline_from_pool, DELTA_LAMBDA_BY_FAMILY

# ------------------------------------------------------------------------------
# IMPORT ORDER MATTERS:
#   Load s10b_v6_srm_rdm first (via importlib).
#   On import it triggers `import s10b_v6_pca_rdm as v6` and then runs
#   `v6.make_rdm_atom = make_srm_rdm_atom`. After this, the v6 module's
#   make_rdm_atom IS the SRM variant. We then pull factories off v6.
# ------------------------------------------------------------------------------
_SRM_PATH = SCRIPT_DIR / "s10b_v6_srm_rdm.py"
_spec_srm = importlib.util.spec_from_file_location("s10b_v6_srm_rdm", _SRM_PATH)
_srm_mod = importlib.util.module_from_spec(_spec_srm)
_spec_srm.loader.exec_module(_srm_mod)

# After the SRM module has executed, v6.make_rdm_atom is the SRM variant.
import s10b_v6_pca_rdm as _v6  # noqa: E402

# Defensive check: confirm the monkey-patch took effect.
assert _v6.make_rdm_atom is _srm_mod.make_srm_rdm_atom, (
    "Monkey-patch failed: v6.make_rdm_atom is NOT make_srm_rdm_atom. "
    "Check s10b_v6_srm_rdm.py import-time side effect."
)

make_gamma_pair_atom = _v6.make_gamma_pair_atom
make_rdm_atom = _v6.make_rdm_atom  # = make_srm_rdm_atom (requires n_pool >= 2)
make_loco_atom = _v6.make_loco_atom
grid_eval_rc = _v6.grid_eval_rc
grid_eval_2comp = _v6.grid_eval_2comp
zscore_grid = _v6.zscore_grid
argmin_rc = _v6.argmin_rc
argmin_2comp = _v6.argmin_2comp
g_grid = _v6.g_grid

OUT_DIR = SCRIPT_DIR.parent / "results" / "s10_inclusion"
OUT_DIR.mkdir(parents=True, exist_ok=True)

HC_SUBJS = ['sub-01', 'sub-02', 'sub-03', 'sub-04', 'sub-05', 'sub-06', 'sub-07']
ROIS = ['V1', 'V2', 'V3', 'V4']
HUES = np.arange(0, 360, 45, dtype=float)


# ------------------------------------------------------------------------------
# Candidate definitions — 3 SRM-cosine RDM cells from Phase B v6.
# ------------------------------------------------------------------------------
CANDIDATES = [
    # ---- sub-08 (deutan, focal=yellow-purple) ----
    {
        'id': 'S08-srm-stable',
        'subject': 'sub-08',
        'family': 'deutan',
        'focal_pair': 'yellow-purple',
        'model': '2comp',
        'combo_label': 'γALL|RDMV1|noLOCO',
        'gamma_pairs': ['ALL'],
        'rdm_rois': ['V1'],
        'loco_v4': False,
        'phase_b_fit': {'beta_s': 22.0, 'beta_c': -36.0},
        'description': 'SRM-cosine stable (multi-pair γ + V1 SRM-RDM)',
    },
    {
        'id': 'S08-srm-robust',
        'subject': 'sub-08',
        'family': 'deutan',
        'focal_pair': 'yellow-purple',
        'model': '2comp',
        'combo_label': 'γOY|RDMV2|noLOCO',
        'gamma_pairs': ['OY'],
        'rdm_rois': ['V2'],
        'loco_v4': False,
        'phase_b_fit': {'beta_s': 8.0, 'beta_c': -42.0},
        'description': 'SRM-cosine robust (OY γ + V2 SRM-RDM)',
    },
    # ---- sub-09 (protan, focal=green-blue) ----
    {
        'id': 'S09-srm-primary',
        'subject': 'sub-09',
        'family': 'protan',
        'focal_pair': 'green-blue',
        'model': '2comp',
        'combo_label': 'γALL|RDMV1|noLOCO',
        'gamma_pairs': ['ALL'],
        'rdm_rois': ['V1'],
        'loco_v4': False,
        'phase_b_fit': {'beta_s': 32.0, 'beta_c': 0.0},
        'description': 'SRM-cosine primary (multi-pair γ + V1 SRM-RDM)',
    },
]


# ------------------------------------------------------------------------------
# Data preloading: load CVD + all HC amps once
# ------------------------------------------------------------------------------
def preload_data(subjects_needed):
    """Preload CVD amps + HC pool amps + JND for all subjects we'll need."""
    cvd_amps_by_subj = {}
    K_by_roi = {}
    C_by_roi = {}
    for s in subjects_needed:
        cvd_amps_by_subj[s] = {}
        for roi in ROIS:
            try:
                cvd_amps_by_subj[s][roi] = load_amplitudes(s, roi)
                if roi not in K_by_roi:
                    K_by_roi[roi] = ROI_K[roi]
                    C_by_roi[roi] = create_basis_full(K_by_roi[roi], basis_type='fe')[
                        HUE_ANGLES.astype(int)]
            except FileNotFoundError:
                pass

    # HC pool (all 7) per ROI
    hc_amps_by_roi = {}
    for roi in ROIS:
        hc_amps_by_roi[roi] = load_hc_pool(roi)

    cvd_jnd_by_subj = {}
    for s in subjects_needed:
        try:
            cvd_jnd_by_subj[s] = load_jnd_per_pair(s)
        except Exception:
            cvd_jnd_by_subj[s] = None

    return cvd_amps_by_subj, hc_amps_by_roi, K_by_roi, C_by_roi, cvd_jnd_by_subj


# ------------------------------------------------------------------------------
# Per-fold fit for one candidate
# ------------------------------------------------------------------------------
def fit_candidate_fold(cand, held_out_hc, cvd_amps, hc_amps_by_roi,
                        K_by_roi, C_by_roi, cvd_jnd):
    """Single fold: held_out_hc is the test HC, remaining 6 are training pool.

    Returns dict with fit params + train/test loss + boundary flag.

    NOTE (SRM variant): the RDM test atom requires n>=2 (SRM cannot train on
    one subject); with held_out_hc as the sole test HC, the SRM RDM test atom
    returns None and is skipped. For noLOCO candidates this typically means
    test_loss=None for every fold.
    """
    family = cand['family']
    subject = cand['subject']
    train_hcs = [h for h in HC_SUBJS if h != held_out_hc]
    train_jnd_pool = [h for h in train_hcs if h in HC_JND_SUBJS]
    test_jnd_pool = [held_out_hc] if held_out_hc in HC_JND_SUBJS else []

    # Build TRAIN atoms (6-HC pool)
    train_atoms = {}
    for p in cand['gamma_pairs']:
        fn = make_gamma_pair_atom(p, cvd_jnd, train_jnd_pool) if cvd_jnd else None
        if fn is not None:
            train_atoms[f'gamma_{p}'] = fn
    for roi in cand['rdm_rois']:
        if roi in cvd_amps:
            pool_amps = {h: hc_amps_by_roi[roi][h] for h in train_hcs
                          if h in hc_amps_by_roi[roi]}
            if len(pool_amps) >= 2:
                fn = make_rdm_atom(roi, cvd_amps[roi], pool_amps,
                                    C_by_roi[roi], K_by_roi[roi])
                if fn is not None:
                    train_atoms[f'rdm_{roi}'] = fn
    if cand['loco_v4'] and 'V4' in cvd_amps:
        fn = make_loco_atom(cvd_amps['V4'], K_by_roi['V4'])
        if fn is not None:
            train_atoms['loco_V4'] = fn

    if not train_atoms:
        return None

    # Evaluate train atom grids
    is_rc = (cand['model'] == 'rc')
    if is_rc:
        dl = cand['dl_value']
        train_grids = {name: grid_eval_rc(fn, dl, family)
                        for name, fn in train_atoms.items()}
    else:
        train_grids = {name: grid_eval_2comp(fn, family)
                        for name, fn in train_atoms.items()}

    # Per-atom train stats for z-renormalizing test atom values
    train_stats = {name: (float(np.nanmean(g)), float(np.nanstd(g)))
                   for name, g in train_grids.items()}

    # z-sum composite (train)
    n_a = len(train_atoms)
    z_sum = None
    for name in train_atoms:
        z = zscore_grid(train_grids[name])
        if np.all(np.isnan(z)):
            return None
        z_sum = z if z_sum is None else z_sum + z
    comp_train = z_sum / np.sqrt(n_a)

    # Argmin
    if is_rc:
        fit = argmin_rc(comp_train)
    else:
        fit = argmin_2comp(comp_train)
    if fit is None:
        return None

    # Train loss (composite z-sum value at argmin)
    train_loss_val = float(np.nanmin(comp_train))

    # delta at argmin
    if is_rc:
        delta_at_argmin = forward_rc(cand['dl_value'], fit['g'], family)
    else:
        delta_at_argmin = forward_2comp(fit['beta_s'], fit['beta_c'], family)

    # Build TEST atoms (single test HC pool)
    # SRM RDM atom requires n>=2; with n=1 it returns None -> skipped.
    # gamma test atoms also require n>=2 for baseline (see PCA s17 comment).
    test_atoms = {}
    can_build_gamma_test = (cvd_jnd is not None) and (len(test_jnd_pool) >= 2)
    for p in cand['gamma_pairs']:
        if not can_build_gamma_test:
            continue
        fn = make_gamma_pair_atom(p, cvd_jnd, test_jnd_pool)
        if fn is not None:
            test_atoms[f'gamma_{p}'] = fn
    for roi in cand['rdm_rois']:
        if roi in cvd_amps and held_out_hc in hc_amps_by_roi[roi]:
            test_pool = {held_out_hc: hc_amps_by_roi[roi][held_out_hc]}
            # SRM atom returns None for len(pool) < 2 -> n=1 yields None.
            fn = make_rdm_atom(roi, cvd_amps[roi], test_pool,
                                C_by_roi[roi], K_by_roi[roi])
            if fn is not None:
                test_atoms[f'rdm_{roi}'] = fn
    if cand['loco_v4'] and 'loco_V4' in train_atoms:
        # LOCO is HC-independent → reuse train atom
        test_atoms['loco_V4'] = train_atoms['loco_V4']

    # Compute test loss = sum of (test_atom_value - train_mu) / train_sd, scaled by sqrt(n_a)
    z_test_parts = []
    test_atoms_used = []
    for nm in train_atoms.keys():
        if nm not in test_atoms:
            continue
        mu, sd = train_stats[nm]
        if not np.isfinite(sd) or sd < 1e-10:
            continue
        try:
            t_val = float(test_atoms[nm](delta_at_argmin))
        except Exception:
            continue
        if not np.isfinite(t_val):
            continue
        z_test_parts.append((t_val - mu) / sd)
        test_atoms_used.append(nm)
    test_loss_val = (float(sum(z_test_parts) / np.sqrt(len(z_test_parts)))
                     if z_test_parts else None)

    # test_focal & test_agg
    focal_pair = cand['focal_pair']
    if test_jnd_pool:
        try:
            test_bl, test_sd = jnd_baseline_from_pool(test_jnd_pool)
        except Exception:
            test_bl, test_sd = {}, {}
    else:
        test_bl, test_sd = {}, {}

    def _test_focal(delta):
        if cvd_jnd is None or focal_pair not in test_bl:
            return None
        focal_obs = cvd_jnd.get(focal_pair)
        focal_base = test_bl.get(focal_pair)
        if focal_obs is None or focal_base is None:
            return None
        theta_a, theta_b = PAIR_HUES[focal_pair]
        i = int(round(theta_a / 45.0)) % 8
        j = int(round(theta_b / 45.0)) % 8
        d_phys = min(abs(theta_a - theta_b) % 360,
                      360 - abs(theta_a - theta_b) % 360)
        perceived = (HUES + delta) % 360.0
        d_perc_raw = abs(perceived[i] - perceived[j]) % 360
        d_perc = max(min(d_perc_raw, 360 - d_perc_raw), 1e-3)
        pred = focal_base * (d_phys / d_perc)
        sd_raw = test_sd.get(focal_pair)
        sd_v = max(sd_raw if sd_raw is not None else 1e-3, 1e-3)
        return float(((pred - focal_obs) / sd_v) ** 2)

    def _test_agg(delta):
        if cvd_jnd is None or not test_bl:
            return None
        valid = {p: cvd_jnd[p] for p in test_bl.keys()
                 if cvd_jnd.get(p) is not None and test_bl.get(p) is not None}
        if not valid:
            return None
        sd_d = {p: max(test_sd.get(p) if test_sd.get(p) is not None else 1e-3, 1e-3)
                for p in valid}
        bl_filtered = {p: test_bl[p] for p in valid}
        try:
            return float(L_behav_gamma(delta, valid, bl_filtered, sd_d))
        except Exception:
            return None

    t_focal = _test_focal(delta_at_argmin)
    t_agg = _test_agg(delta_at_argmin)

    fold_result = {
        'held_out_hc': held_out_hc,
        'train_hcs': train_hcs,
        'train_loss': train_loss_val,
        'test_loss': test_loss_val,
        'test_focal': t_focal,
        'test_agg': t_agg,
        'boundary': bool(fit.get('boundary', False)),
        'train_atoms_used': list(train_atoms.keys()),
        'test_atoms_used': test_atoms_used,
    }
    if is_rc:
        fold_result['g'] = float(fit['g'])
    else:
        fold_result['beta_s'] = float(fit['beta_s'])
        fold_result['beta_c'] = float(fit['beta_c'])
    return fold_result


# ------------------------------------------------------------------------------
# Aggregate per-candidate LOO results
# ------------------------------------------------------------------------------
def summarize_candidate(cand, folds):
    """Compute median, IQR, range across the 7 folds + identify outlier holdouts."""
    valid = [f for f in folds if f is not None]
    if not valid:
        return {'n_folds_valid': 0}

    pb_fit = cand.get('phase_b_fit', {})
    is_rc = (cand['model'] == 'rc')

    summary = {
        'n_folds_valid': len(valid),
        'phase_b_v6_fit': pb_fit,
    }

    if is_rc:
        gs = np.array([f['g'] for f in valid if f.get('g') is not None])
        summary['g_median'] = float(np.median(gs))
        summary['g_iqr'] = float(np.percentile(gs, 75) - np.percentile(gs, 25))
        summary['g_min'] = float(np.min(gs))
        summary['g_max'] = float(np.max(gs))
        summary['g_range'] = float(summary['g_max'] - summary['g_min'])
        pb_g = pb_fit.get('g')
        if pb_g is not None:
            diffs = [(f['held_out_hc'], abs(f['g'] - pb_g)) for f in valid]
            diffs.sort(key=lambda x: -x[1])
            summary['outlier_ranking'] = [{'held_out_hc': h, 'abs_delta_g': float(d)}
                                          for h, d in diffs]
            summary['outlier_holdouts'] = [h for h, d in diffs if d >= 0.5]
    else:
        bss = np.array([f['beta_s'] for f in valid if f.get('beta_s') is not None])
        bcs = np.array([f['beta_c'] for f in valid if f.get('beta_c') is not None])
        summary['bs_median'] = float(np.median(bss))
        summary['bs_iqr'] = float(np.percentile(bss, 75) - np.percentile(bss, 25))
        summary['bs_min'] = float(np.min(bss))
        summary['bs_max'] = float(np.max(bss))
        summary['bs_range'] = float(summary['bs_max'] - summary['bs_min'])
        summary['bc_median'] = float(np.median(bcs))
        summary['bc_iqr'] = float(np.percentile(bcs, 75) - np.percentile(bcs, 25))
        summary['bc_min'] = float(np.min(bcs))
        summary['bc_max'] = float(np.max(bcs))
        summary['bc_range'] = float(summary['bc_max'] - summary['bc_min'])
        pb_bs = pb_fit.get('beta_s'); pb_bc = pb_fit.get('beta_c')
        if pb_bs is not None and pb_bc is not None:
            diffs = []
            for f in valid:
                d = float(np.hypot(f['beta_s'] - pb_bs, f['beta_c'] - pb_bc))
                diffs.append((f['held_out_hc'], d))
            diffs.sort(key=lambda x: -x[1])
            summary['outlier_ranking'] = [
                {'held_out_hc': h, 'euclid_delta_bsc': float(d)}
                for h, d in diffs
            ]
            summary['outlier_holdouts'] = [h for h, d in diffs if d >= 20.0]

    summary['boundary_rate'] = float(np.mean([f['boundary'] for f in valid]))
    tr_losses = [f['train_loss'] for f in valid if f.get('train_loss') is not None]
    te_losses = [f['test_loss'] for f in valid if f.get('test_loss') is not None]
    summary['train_loss_median'] = float(np.median(tr_losses)) if tr_losses else None
    summary['train_loss_iqr'] = (float(np.percentile(tr_losses, 75) - np.percentile(tr_losses, 25))
                                  if len(tr_losses) >= 2 else None)
    summary['test_loss_median'] = float(np.median(te_losses)) if te_losses else None
    summary['test_loss_iqr'] = (float(np.percentile(te_losses, 75) - np.percentile(te_losses, 25))
                                 if len(te_losses) >= 2 else None)
    tf = [f['test_focal'] for f in valid if f.get('test_focal') is not None]
    ta = [f['test_agg'] for f in valid if f.get('test_agg') is not None]
    summary['test_focal_median'] = float(np.median(tf)) if tf else None
    summary['test_agg_median'] = float(np.median(ta)) if ta else None

    return summary


# ------------------------------------------------------------------------------
# Main
# ------------------------------------------------------------------------------
def main():
    print("=" * 100, flush=True)
    print("S17 SRM — Strict HC LOO (7-fold) on Phase B v6 SRM-cosine RDM candidates",
          flush=True)
    print(f"  {len(CANDIDATES)} candidates × {len(HC_SUBJS)} folds", flush=True)
    print(f"  RDM atom: {make_rdm_atom.__module__}.{make_rdm_atom.__name__}",
          flush=True)
    print("=" * 100, flush=True)

    t0 = time.time()

    subjects_needed = sorted({c['subject'] for c in CANDIDATES})
    cvd_amps_by_subj, hc_amps_by_roi, K_by_roi, C_by_roi, cvd_jnd_by_subj = \
        preload_data(subjects_needed)

    results = {'candidates': [], 'meta': {
        'design': 'strict HC LOO 7-fold (SRM-cosine RDM atom)',
        'rdm_atom_module': 's10b_v6_srm_rdm.make_srm_rdm_atom',
        'rdm_method': 'SRM_BrainIAK (K=ROI_K, n_iter=20, seed=0)',
        'rdm_distance': 'correlation (1 - centered cosine of K-d shared cols)',
        'n_train_hcs_per_fold': 6,
        'n_test_hcs_per_fold': 1,
        'hc_subjects': HC_SUBJS,
        'rdm_test_handling': 'SRM atom requires n>=2; n=1 test pool → RDM test atom skipped (returns None)',
        'gamma_test_handling': 'jnd_baseline_from_pool requires n>=2; n=1 → gamma test atom skipped (matches PCA s17)',
        'loco_atom_invariance': True,
        'loco_atom_note': 'LOCO atom is CVD-internal (HC-independent); same value across folds (none of the 3 SRM candidates use loco_v4)',
        'test_loss_caveat': 'For noLOCO candidates with n=1 test pool, ALL test atoms are skipped → test_loss=None for every fold. Primary deliverable = train-grid argmin (bs/bc median/IQR/range).',
        'phase_b_v6_comparison': 'param IQR not directly comparable to 5/2 × 300 resamples; range [min,max] is more honest stability indicator for n=7',
    }}

    for cand in CANDIDATES:
        t_cand = time.time()
        cvd_amps = cvd_amps_by_subj[cand['subject']]
        cvd_jnd = cvd_jnd_by_subj[cand['subject']]
        print(f"\n[{cand['id']}] {cand['subject']} {cand['model']} {cand['combo_label']}",
              flush=True)
        folds = []
        for held_out_hc in HC_SUBJS:
            fold = fit_candidate_fold(
                cand, held_out_hc, cvd_amps, hc_amps_by_roi,
                K_by_roi, C_by_roi, cvd_jnd)
            if fold is None:
                print(f"  fold {held_out_hc}: SKIPPED (no train atoms or fit failed)",
                      flush=True)
            else:
                tl = fold['test_loss']
                tl_str = 'None' if tl is None else f"{tl:.4f}"
                if cand['model'] == 'rc':
                    print(f"  fold {held_out_hc}: g={fold['g']:.3f} "
                          f"train_loss={fold['train_loss']:.4f} "
                          f"test_loss={tl_str} "
                          f"boundary={fold['boundary']}", flush=True)
                else:
                    print(f"  fold {held_out_hc}: bs={fold['beta_s']:.1f} bc={fold['beta_c']:.1f} "
                          f"train_loss={fold['train_loss']:.4f} "
                          f"test_loss={tl_str} "
                          f"boundary={fold['boundary']}", flush=True)
            folds.append(fold)

        summary = summarize_candidate(cand, folds)
        cand_record = {
            'id': cand['id'],
            'subject': cand['subject'],
            'family': cand['family'],
            'model': cand['model'],
            'combo_label': cand['combo_label'],
            'gamma_pairs': cand['gamma_pairs'],
            'rdm_rois': cand['rdm_rois'],
            'loco_v4': cand['loco_v4'],
            'description': cand['description'],
            'phase_b_v6_fit': cand.get('phase_b_fit', {}),
            'loo_folds': folds,
            'summary': summary,
        }
        if cand['model'] == 'rc':
            cand_record['dl_src'] = cand['dl_src']
            cand_record['dl_value'] = cand['dl_value']
        results['candidates'].append(cand_record)
        print(f"  -- summary: {summary}", flush=True)
        print(f"  elapsed: {time.time() - t_cand:.1f}s", flush=True)

    elapsed = round(time.time() - t0, 1)
    results['meta']['elapsed_sec'] = elapsed
    results['meta']['n_candidates'] = len(CANDIDATES)

    out_file = OUT_DIR / "s17_srm_hc_loo_results.json"
    with open(out_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n[done] elapsed={elapsed}s  saved={out_file}", flush=True)

    # --- Final summary table to stdout ---
    print("\n" + "=" * 100, flush=True)
    print("FINAL SUMMARY TABLE", flush=True)
    print("=" * 100, flush=True)
    print(f"{'id':<20} {'subj':<8} {'PhaseB v6 (bs,bc)':<22} "
          f"{'LOO bs (med,iqr,range)':<32} {'LOO bc (med,iqr,range)':<32} {'outlier HC':<15}",
          flush=True)
    print("-" * 130, flush=True)
    for c in results['candidates']:
        s = c['summary']
        pbv = c['phase_b_v6_fit']
        pb_str = f"({pbv.get('beta_s', '-'):>4}, {pbv.get('beta_c', '-'):>4})"
        bs_str = (f"{s.get('bs_median', float('nan')):>5.1f}, "
                  f"{s.get('bs_iqr', float('nan')):>5.1f}, "
                  f"[{s.get('bs_min', float('nan')):>5.1f},{s.get('bs_max', float('nan')):>5.1f}]")
        bc_str = (f"{s.get('bc_median', float('nan')):>5.1f}, "
                  f"{s.get('bc_iqr', float('nan')):>5.1f}, "
                  f"[{s.get('bc_min', float('nan')):>5.1f},{s.get('bc_max', float('nan')):>5.1f}]")
        outliers = s.get('outlier_holdouts', [])
        out_str = ','.join(outliers) if outliers else '-'
        print(f"{c['id']:<20} {c['subject']:<8} {pb_str:<22} "
              f"{bs_str:<32} {bc_str:<32} {out_str:<15}", flush=True)


if __name__ == "__main__":
    main()
