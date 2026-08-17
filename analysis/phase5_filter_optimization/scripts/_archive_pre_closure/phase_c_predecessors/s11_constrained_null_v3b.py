"""
S11 constrained null sim v3b: test sign + LOCO-V4 atom inclusion.

Iteration 2: keep β_c ≤ 0 sign constraint (deutan) AND add LOCO_V4 atom to the
composite. This is NOT a parameter-space constraint — it is a candidate
reconfiguration test that addresses the H3 root cause (RDM atoms are
under-informative for β_s).

Rationale (physiological + statistical):
- The LOCO_V4 atom evaluates per-color voxel-prediction accuracy, which is
  qualitatively different from RDM (pairwise distance structure). It provides
  per-color residuals that constrain individual δθ(c) entries directly, not
  just pairwise.
- Under null GT (CVD == HC), L_LOCO is minimized at δθ=0 (by construction:
  HC voxel patterns are best predicted by zero-distortion model).
- This is the SAME methodology specified by the user in S7 Stage C
  (CLAUDE.md §3): 'λ·L_LOCO probe' to test neural unique contribution.

Pass criterion (same as v3a):
- |β_s median| ≤ 5
- |β_c median| ≤ 5
- IQR_bs < 20, IQR_bc < 20

If this also fails, report C1 is non-identifiable under null regardless of
atom configuration.
"""

import json
import sys
import time
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import s10b_v3_extended as v3
from two_comp import forward_2comp, BS_GRID, BC_GRID
from neural_loss import load_amplitudes as _orig_load_amps, load_hc_pool as _orig_load_hc
from behav_loss import load_jnd_per_pair as _orig_load_jnd

OUT_DIR = SCRIPT_DIR.parent / "results" / "s11_pre_phase_c_null_sim"
OUT_DIR.mkdir(parents=True, exist_ok=True)

HC_ALL = ['sub-01', 'sub-02', 'sub-03', 'sub-04', 'sub-05', 'sub-06', 'sub-07']
N_OUTER = 50
v3.N_RESAMPLES = 1
RNG_SEED = 5678
rng = np.random.default_rng(RNG_SEED)

CVD_FAMILY = 'deutan'

_orig_argmin_2comp = v3.argmin_2comp


def constrained_argmin_2comp(arr):
    if np.all(np.isnan(arr)):
        return None
    masked = arr.copy()
    col_mask = BC_GRID > 0  # deutan β_c ≤ 0
    masked[:, col_mask] = np.nan
    if np.all(np.isnan(masked)):
        return None
    flat = int(np.nanargmin(masked.ravel()))
    i, j = np.unravel_index(flat, masked.shape)
    return {'beta_s': float(BS_GRID[i]), 'beta_c': float(BC_GRID[j]),
            'boundary': bool(i == 0 or i == len(BS_GRID) - 1 or
                              j == 0 or j == len(BC_GRID) - 1)}


v3.argmin_2comp = constrained_argmin_2comp

print(f"[s11 constrained v3b] sign + LOCO_V4 atom, N_OUTER={N_OUTER}", flush=True)
print(f"  Constraint: β_c ≤ 0 (deutan) AND add LOCO_V4 atom to composite", flush=True)

# Pre-load
all_hc_amps = {}
for hc in HC_ALL:
    all_hc_amps[hc] = {}
    for roi in v3.ROIS:
        try:
            all_hc_amps[hc][roi] = _orig_load_amps(hc, roi)
        except Exception:
            pass
all_hc_jnd = {hc: _orig_load_jnd(hc) for hc in HC_ALL}

# Find the LOCO-enabled candidate: γYG|RDMV1+V4|LOCO
combos = v3.enumerate_combos_sub08()
target_label_with_loco = 'γYG|RDMV1+V4|LOCO'
c_loco_idx = next((i for i, c in enumerate(combos) if c['label'] == target_label_with_loco), None)
assert c_loco_idx is not None, f"Combo {target_label_with_loco} not found"
print(f"  target: sub-08 with LOCO = {target_label_with_loco} (combo idx={c_loco_idx})",
      flush=True)

orig_HC_SUBJS = v3.HC_SUBJS

all_fits_2c = []

t_start = time.time()
for it in range(N_OUTER):
    cvd_hc = HC_ALL[rng.integers(0, len(HC_ALL))]
    pool_hcs = [h for h in HC_ALL if h != cvd_hc]
    v3.HC_SUBJS = pool_hcs
    v3.load_amplitudes = lambda subject, roi, _h=cvd_hc: all_hc_amps[_h].get(roi)
    v3.load_hc_pool = lambda roi, _p=pool_hcs: {h: all_hc_amps[h][roi]
                                                  for h in _p if roi in all_hc_amps[h]}
    v3.load_jnd_per_pair = lambda subject, _h=cvd_hc: all_hc_jnd[_h]
    v3.SUBSET_SIZE = 4
    storage = v3.fit_subject('sub-08', combo_start=c_loco_idx, combo_end=c_loco_idx + 1)
    fits_2c = storage[target_label_with_loco]['2comp']
    if fits_2c:
        all_fits_2c.append(fits_2c[0])
    if (it + 1) % 10 == 0:
        elapsed = time.time() - t_start
        eta = elapsed * (N_OUTER - it - 1) / (it + 1)
        print(f"  [{it+1}/{N_OUTER}] cvd={cvd_hc}, elapsed={elapsed:.0f}s, "
              f"eta={eta:.0f}s", flush=True)

v3.HC_SUBJS = orig_HC_SUBJS
v3.argmin_2comp = _orig_argmin_2comp

bs_arr = np.array([f['beta_s'] for f in all_fits_2c])
bc_arr = np.array([f['beta_c'] for f in all_fits_2c])
bdy_2c = float(np.mean([f.get('boundary', False) for f in all_fits_2c]))
print(f"\n=== sub-08 with LOCO + sign constraint (N={len(all_fits_2c)}) ===", flush=True)
print(f"β_s: median={np.median(bs_arr):+.1f}, "
      f"IQR={np.percentile(bs_arr,75)-np.percentile(bs_arr,25):.1f}, "
      f"range=[{bs_arr.min():.0f}, {bs_arr.max():.0f}]", flush=True)
print(f"β_c: median={np.median(bc_arr):+.1f}, "
      f"IQR={np.percentile(bc_arr,75)-np.percentile(bc_arr,25):.1f}, "
      f"range=[{bc_arr.min():.0f}, {bc_arr.max():.0f}]", flush=True)
print(f"boundary rate: {bdy_2c*100:.0f}%", flush=True)

bs_med = float(np.median(bs_arr)); bc_med = float(np.median(bc_arr))
bs_iqr = float(np.percentile(bs_arr, 75) - np.percentile(bs_arr, 25))
bc_iqr = float(np.percentile(bc_arr, 75) - np.percentile(bc_arr, 25))
passed_med = (abs(bs_med) <= 5) and (abs(bc_med) <= 5)
passed_iqr = (bs_iqr < 20) and (bc_iqr < 20)
passed_2c = passed_med and passed_iqr

print(f"\n=== PASS CRITERIA ===", flush=True)
print(f"|β_s med|≤5° & |β_c med|≤5°: {'PASS' if passed_med else 'FAIL'} "
      f"(β_s={bs_med:+.1f}, β_c={bc_med:+.1f})", flush=True)
print(f"IQR<20 both axes: {'PASS' if passed_iqr else 'FAIL'} "
      f"(IQR_bs={bs_iqr:.1f}, IQR_bc={bc_iqr:.1f})", flush=True)
print(f"OVERALL: {'PASS — LOCO+sign rescues null' if passed_2c else 'FAIL'}", flush=True)

out = {
    'config': {
        'design': 'bootstrap leave-one-HC-as-CVD with β_c≤0 + LOCO_V4 atom',
        'N_OUTER': N_OUTER,
        'candidate': target_label_with_loco,
        'subject': 'sub-08',
        'rng_seed': RNG_SEED,
        'constraint': 'beta_c_le_0_and_loco_v4_added',
    },
    'gt': {'beta_s': 0.0, 'beta_c': 0.0, 'family': 'deutan'},
    '2comp': {
        'n': len(all_fits_2c),
        'beta_s_median': bs_med, 'beta_s_iqr': bs_iqr,
        'beta_s_range': [float(bs_arr.min()), float(bs_arr.max())],
        'beta_c_median': bc_med, 'beta_c_iqr': bc_iqr,
        'beta_c_range': [float(bc_arr.min()), float(bc_arr.max())],
        'boundary_rate': bdy_2c,
        'all_beta_s': bs_arr.tolist(),
        'all_beta_c': bc_arr.tolist(),
    },
    'pass_criterion': {
        'medians_ok': passed_med,
        'iqr_ok': passed_iqr,
        'both': passed_2c,
    },
}
out_path = OUT_DIR / 's11_null_constrained_betac_sign_plus_loco.json'
out_path.write_text(json.dumps(out, indent=2))
print(f"\nSaved: {out_path}", flush=True)
