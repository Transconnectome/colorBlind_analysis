"""
Multi-point validation simulation (Task #54, advisor #1 fix, 2026-05-25).

Validates Phase C v2 candidate fits by:
1. Generating synthetic CVD at known GT (each candidate's fitted params)
2. Running same Phase C pipeline on synthetic
3. Comparing fitted params vs GT (recovery test)

GT set (per candidate + null):
- GT_null: g=2 (R+C) or β=0 (2-comp). CVD = HC distribution.
- GT_S08-B: g=2.60, R+C DPS_lit 6nm, deutan
- GT_S08-E: (β_s=38, β_c=−44), 2-comp deutan
- GT_S09-A_DPS: g=2.60, R+C DPS_lit 10nm, protan

Design: bootstrap leave-one-HC-as-CVD (preserves voxel correlation).
For non-null GT: apply GT forward δθ to swap-HC's voxel patterns before fit.
50 outer iterations per (candidate × GT).

Pass criterion per (candidate, GT):
- median fitted params within ±0.2 (g) / ±5° (β) of GT
- recovery IQR < grid_range/4

Cost estimate: ~10-15 min total (3 candidates × ~3-4 GTs × 50 iter × ~5s/iter).
Output: results/s13_multipoint_sim/recovery_*.json
"""

import json
import sys
import time
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import s10b_v4_single_atom as v4
from rc_1dof import forward_rc
from two_comp import forward_2comp
from neural_loss import (
    load_amplitudes as _orig_load_amps,
    load_hc_pool as _orig_load_hc,
)
from behav_loss import load_jnd_per_pair as _orig_load_jnd, HC_JND_SUBJS
from utils_forward_model import create_basis_full, HUE_ANGLES

OUT_DIR = SCRIPT_DIR.parent / "results" / "s13_multipoint_sim"
OUT_DIR.mkdir(parents=True, exist_ok=True)

HC_ALL = ['sub-01', 'sub-02', 'sub-03', 'sub-04', 'sub-05', 'sub-06', 'sub-07']
N_OUTER = 50
N_INNER = 1  # single HC subset draw per outer iter
v4.N_RESAMPLES = N_INNER
v4.SUBSET_SIZE = 4  # left-one-out gives 6 HCs, 4-train/2-test from 6

RNG_SEED = 13579


def apply_gt_perturbation(amps, gt_config, hues=None):
    """Apply forward δθ to voxel pattern via basis interpolation.

    amps: (n_run, 8, V_s)
    Returns perturbed amps after applying δθ shift to color basis.
    """
    if hues is None:
        hues = np.arange(0, 360, 45, dtype=float)
    if gt_config['model'] == 'rc':
        delta = forward_rc(gt_config['delta_lambda'], gt_config['g'], gt_config['family'])
    else:  # 2comp
        delta = forward_2comp(gt_config['beta_s'], gt_config['beta_c'], gt_config['family'])
    # δθ near zero → no perturbation needed
    if np.max(np.abs(delta)) < 1e-3:
        return amps.copy()
    # We rebuild via basis: project amps onto C(θ) basis, then re-synth at θ+δθ
    # Use FE-8 basis (same as Phase B)
    K = 8  # full
    C_base = create_basis_full(K, basis_type='fe')[HUE_ANGLES.astype(int)]  # (8, K)
    C_shift = create_basis_full(K, basis_type='fe')[((HUE_ANGLES + delta) % 360).astype(int)]
    # amps shape: (n_run, 8, V_s). For each run, voxel pattern matrix Y = (8, V_s).
    # Project: weights W = pinv(C_base) @ Y. Re-synth: Y' = C_shift @ W.
    Cinv = np.linalg.pinv(C_base)
    perturbed = np.zeros_like(amps)
    for r in range(amps.shape[0]):
        Y = amps[r]  # (8, V_s)
        W = Cinv @ Y  # (K, V_s)
        Y_shift = C_shift @ W
        perturbed[r] = Y_shift
    return perturbed


CANDIDATES = [
    {
        'id': 'S08-D',
        'subject': 'sub-08',
        'family': 'deutan',
        'model': '2comp',
        'beta_s_gt': 34.0,
        'beta_c_gt': 48.0,
        'combo_label': 'γYP|RDM_|noLOCO',
        'atoms_in_phase_b': ['gamma_YP'],
    },
    {
        'id': 'S09-C',
        'subject': 'sub-09',
        'family': 'protan',
        'model': '2comp',
        'beta_s_gt': 6.0,
        'beta_c_gt': 46.0,
        'combo_label': 'γ_|RDMV1|noLOCO',
        'atoms_in_phase_b': ['rdm_V1'],
    },
]

# Pre-load all HC amps + JND
print(f"[s13] pre-loading HC data", flush=True)
all_hc_amps = {}
for hc in HC_ALL:
    all_hc_amps[hc] = {}
    for roi in v4.ROIS:
        try:
            all_hc_amps[hc][roi] = _orig_load_amps(hc, roi)
        except Exception:
            pass
all_hc_jnd = {hc: _orig_load_jnd(hc) for hc in HC_ALL}
syn_jnd_null = {}
for p in all_hc_jnd[HC_JND_SUBJS[0]].keys():
    vals = [all_hc_jnd[h][p] for h in HC_JND_SUBJS if all_hc_jnd[h].get(p) is not None]
    if vals:
        syn_jnd_null[p] = float(np.mean(vals))


def run_one_candidate_at_gt(cand, gt_label, gt_config, n_outer=N_OUTER):
    """For one (candidate, GT): N_OUTER bootstrap iterations.

    Each iter: random HC -> swap as CVD, apply GT perturbation to its voxel patterns,
    fit candidate's Phase C pipeline, record fitted params.
    """
    family = cand['family']
    rng = np.random.default_rng(RNG_SEED + hash(cand['id'] + gt_label) % 99991)
    subject = cand['subject']

    # Find combo in v4 enumeration
    combos = (v4.enumerate_combos_sub08() if subject == 'sub-08'
              else v4.enumerate_combos_sub09())
    combo_label = cand['combo_label']
    target_combo = next((c for c in combos if c['label'] == combo_label), None)
    if target_combo is None:
        # Try a substitute: for S08-B (γ_|RDMV2|LOCO) the v4 enumeration may use different label
        # Find by atom signature
        target_combo = next(
            (c for c in combos
             if c.get('rdm_rois') == ['V2'] and c.get('loco_v4') is True
             and not c.get('gamma_pairs')),
            None,
        )
        if target_combo is None:
            print(f"  [{cand['id']}/{gt_label}] WARN: combo {combo_label} not found, SKIP", flush=True)
            return None
    c_idx = combos.index(target_combo)
    print(f"  combo idx={c_idx} label={target_combo['label']}", flush=True)

    storage_records = []
    t_start = time.time()
    for it in range(n_outer):
        cvd_hc = HC_ALL[rng.integers(0, len(HC_ALL))]
        pool_hcs = [h for h in HC_ALL if h != cvd_hc]
        # Apply GT perturbation to CVD's amps
        perturbed_amps = {}
        for roi in v4.ROIS:
            if roi in all_hc_amps[cvd_hc]:
                amps = all_hc_amps[cvd_hc][roi]
                perturbed_amps[roi] = apply_gt_perturbation(amps, gt_config)
        # Monkey-patch
        v4.HC_SUBJS = pool_hcs
        v4.load_amplitudes = lambda subject, roi, _p=perturbed_amps: _p.get(roi)
        v4.load_hc_pool = lambda roi, _pool=pool_hcs: {h: all_hc_amps[h][roi] for h in _pool if roi in all_hc_amps[h]}
        v4.load_jnd_per_pair = lambda subject, _h=cvd_hc: all_hc_jnd[_h]
        # Run fit (N_RESAMPLES=1)
        try:
            sub_storage = v4.fit_subject(subject, combo_start=c_idx, combo_end=c_idx + 1)
        except Exception as e:
            print(f"  [{cand['id']}/{gt_label}] iter {it}: FAIL {e}", flush=True)
            continue
        fits = sub_storage[target_combo['label']]
        # Pick the model match
        if cand['model'] == 'rc':
            src = f"rc_{gt_config.get('dl_source_label', cand.get('dl_source_label', 'DPS_lit'))}"
            mfits = fits.get(src, [])
        else:
            mfits = fits.get('2comp', [])
        if mfits:
            storage_records.append(mfits[0])
        if (it + 1) % 10 == 0:
            elapsed = time.time() - t_start
            eta = elapsed * (n_outer - it - 1) / (it + 1)
            print(f"    [{it+1}/{n_outer}] elapsed={elapsed:.0f}s eta={eta:.0f}s", flush=True)

    # Aggregate
    if not storage_records:
        return None
    if cand['model'] == 'rc':
        g_arr = np.array([r['g'] for r in storage_records])
        bdy_rate = np.mean([r.get('boundary', False) for r in storage_records])
        return {
            'gt_label': gt_label, 'gt_config': gt_config,
            'n': len(storage_records),
            'g_median': float(np.median(g_arr)),
            'g_iqr': float(np.percentile(g_arr, 75) - np.percentile(g_arr, 25)),
            'g_range': [float(g_arr.min()), float(g_arr.max())],
            'boundary_rate': float(bdy_rate),
            'all_g': g_arr.tolist(),
        }
    else:
        bs = np.array([r['beta_s'] for r in storage_records])
        bc = np.array([r['beta_c'] for r in storage_records])
        bdy_rate = np.mean([r.get('boundary', False) for r in storage_records])
        return {
            'gt_label': gt_label, 'gt_config': gt_config,
            'n': len(storage_records),
            'beta_s_median': float(np.median(bs)),
            'beta_s_iqr': float(np.percentile(bs, 75) - np.percentile(bs, 25)),
            'beta_c_median': float(np.median(bc)),
            'beta_c_iqr': float(np.percentile(bc, 75) - np.percentile(bc, 25)),
            'boundary_rate': float(bdy_rate),
            'all_beta_s': bs.tolist(),
            'all_beta_c': bc.tolist(),
        }


def build_gt_set(cand):
    """Return list of (gt_label, gt_config) for this candidate."""
    gts = []
    # Null GT
    if cand['model'] == 'rc':
        gts.append(('null_g2', {'model': 'rc', 'family': cand['family'],
                                'delta_lambda': cand['delta_lambda'], 'g': 2.0,
                                'dl_source_label': cand['dl_source_label']}))
        # Fit-point GT
        gts.append((f"fit_g{cand['g_gt']}", {'model': 'rc', 'family': cand['family'],
                                              'delta_lambda': cand['delta_lambda'],
                                              'g': cand['g_gt'],
                                              'dl_source_label': cand['dl_source_label']}))
    else:
        gts.append(('null_b0', {'model': '2comp', 'family': cand['family'],
                                'beta_s': 0.0, 'beta_c': 0.0}))
        gts.append((f"fit_bs{cand['beta_s_gt']:.0f}_bc{cand['beta_c_gt']:.0f}",
                    {'model': '2comp', 'family': cand['family'],
                     'beta_s': cand['beta_s_gt'], 'beta_c': cand['beta_c_gt']}))
    return gts


def main():
    print(f"[s13] multi-point validation, N_OUTER={N_OUTER}, {len(CANDIDATES)} candidates", flush=True)
    results = {}
    t0 = time.time()
    for cand in CANDIDATES:
        cid = cand['id']
        print(f"\n=== [{cid}] {cand['combo_label']} subject={cand['subject']} ===", flush=True)
        gts = build_gt_set(cand)
        results[cid] = {'config': cand, 'gt_runs': []}
        for gt_label, gt_config in gts:
            print(f"  [{cid} GT: {gt_label}]", flush=True)
            res = run_one_candidate_at_gt(cand, gt_label, gt_config)
            if res is not None:
                results[cid]['gt_runs'].append(res)
                if 'g_median' in res:
                    print(f"  -> g_med={res['g_median']:.2f} ± {res['g_iqr']:.2f}, "
                          f"bdy={res['boundary_rate']*100:.0f}%", flush=True)
                else:
                    print(f"  -> βs={res['beta_s_median']:+.0f}±{res['beta_s_iqr']:.0f}, "
                          f"βc={res['beta_c_median']:+.0f}±{res['beta_c_iqr']:.0f}, "
                          f"bdy={res['boundary_rate']*100:.0f}%", flush=True)
    total = round(time.time() - t0, 1)
    print(f"\n[s13] total elapsed: {total}s", flush=True)
    out_path = OUT_DIR / 's13_multipoint_recovery.json'
    out_path.write_text(json.dumps(results, indent=2))
    print(f"Saved: {out_path}", flush=True)


if __name__ == '__main__':
    main()
