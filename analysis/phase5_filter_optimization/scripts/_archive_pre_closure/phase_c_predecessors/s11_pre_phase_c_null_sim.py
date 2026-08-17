"""
Pre-Phase-C null sanity simulation (advisor #4 fix, 2026-05-25).

Design: bootstrap leave-one-HC-as-CVD.
- 50 outer iterations: each picks 1 random HC as "CVD" (left out),
  remaining 6 HCs as the pool.
- GT: δθ = 0 (CVD = HC) by construction — the test HC is genuinely an HC.
- Each iteration runs sub-08 C1 fit_subject with N_RESAMPLES=1
  (one HC subset draw of 5 from the 6 remaining).

Pass criterion (decided 2026-05-25, advisor #4):
- |β_s median| ≤ 5°
- |β_c median| ≤ 5°
- R+C g median ∈ [1.8, 2.2] across Δλ sources (sanity, not primary —
  null R+C means δθ=0 ⇒ any g consistent if Machado(Δλ) is small,
  but with finite Δλ Machado≠0 so g=2 is required)

Cost: 50 iterations × ~5-10s/fit ≈ 5-10 min.
Output: results/s11_pre_phase_c_null_sim/s11_null_sanity_sub08_C1.json
"""

import json
import sys
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import s10b_v3_extended as v3
from neural_loss import load_amplitudes as _orig_load_amps, load_hc_pool as _orig_load_hc
from behav_loss import load_jnd_per_pair as _orig_load_jnd

OUT_DIR = SCRIPT_DIR.parent / "results" / "s11_pre_phase_c_null_sim"
OUT_DIR.mkdir(parents=True, exist_ok=True)

HC_ALL = ['sub-01', 'sub-02', 'sub-03', 'sub-04', 'sub-05', 'sub-06', 'sub-07']
N_OUTER = 50
v3.N_RESAMPLES = 1  # single inner HC subset draw per iteration

RNG_SEED = 5678
rng = np.random.default_rng(RNG_SEED)

print(f"[s11] Pre-Phase-C null sanity (bootstrap), N_OUTER={N_OUTER}, seed={RNG_SEED}", flush=True)

# Pre-load all HC amps + JND once (reused across iterations)
all_hc_amps = {}
for hc in HC_ALL:
    all_hc_amps[hc] = {}
    for roi in v3.ROIS:
        try:
            all_hc_amps[hc][roi] = _orig_load_amps(hc, roi)
        except Exception:
            pass
all_hc_jnd = {hc: _orig_load_jnd(hc) for hc in HC_ALL}

# Find sub-08 C1 combo index
combos = v3.enumerate_combos_sub08()
target_label = 'γYG|RDMV1+V4|noLOCO'
c1_idx = next((i for i, c in enumerate(combos) if c['label'] == target_label), None)
assert c1_idx is not None, f"Combo {target_label} not found"
print(f"  target: sub-08 C1 = {target_label} (combo idx={c1_idx})", flush=True)

# Also need v3.HC_SUBJS to match the 6 in-pool HCs each iteration
orig_HC_SUBJS = v3.HC_SUBJS

# Collect fits
all_fits_2c = []
all_fits_rc = {'rc_DPS_lit': [], 'rc_Boehm_mid': [], 'rc_JND_Lamb': []}

import time
t_start = time.time()
for it in range(N_OUTER):
    # Random left-out HC
    cvd_hc = HC_ALL[rng.integers(0, len(HC_ALL))]
    pool_hcs = [h for h in HC_ALL if h != cvd_hc]
    # Monkey-patch
    v3.HC_SUBJS = pool_hcs  # 6 HCs
    v3.load_amplitudes = lambda subject, roi, _h=cvd_hc: all_hc_amps[_h].get(roi)
    v3.load_hc_pool = lambda roi, _p=pool_hcs: {h: all_hc_amps[h][roi] for h in _p if roi in all_hc_amps[h]}
    v3.load_jnd_per_pair = lambda subject, _h=cvd_hc: all_hc_jnd[_h]
    v3.SUBSET_SIZE = 4  # 4-train / 2-test from 6 pool (caveat: differs from Phase B 5/2 by 1 train HC)
    # Run fit (1 HC subset draw)
    storage = v3.fit_subject('sub-08', combo_start=c1_idx, combo_end=c1_idx + 1)
    fits_2c = storage[target_label]['2comp']
    if fits_2c:
        all_fits_2c.append(fits_2c[0])
    for src_key in all_fits_rc:
        rc_fits = storage[target_label].get(src_key, [])
        if rc_fits:
            all_fits_rc[src_key].append(rc_fits[0])
    if (it + 1) % 10 == 0:
        elapsed = time.time() - t_start
        eta = elapsed * (N_OUTER - it - 1) / (it + 1)
        print(f"  [{it+1}/{N_OUTER}] cvd={cvd_hc}, elapsed={elapsed:.0f}s, eta={eta:.0f}s", flush=True)

v3.HC_SUBJS = orig_HC_SUBJS

# Analyze 2-comp fits
bs_arr = np.array([f['beta_s'] for f in all_fits_2c])
bc_arr = np.array([f['beta_c'] for f in all_fits_2c])
bdy_2c = np.mean([f.get('boundary', False) for f in all_fits_2c])
print(f"\n=== sub-08 C1 2-comp null-GT recovery (N={len(all_fits_2c)}) ===", flush=True)
print(f"β_s: median={np.median(bs_arr):+.1f}, IQR={np.percentile(bs_arr,75)-np.percentile(bs_arr,25):.1f}, range=[{bs_arr.min():.0f}, {bs_arr.max():.0f}]", flush=True)
print(f"β_c: median={np.median(bc_arr):+.1f}, IQR={np.percentile(bc_arr,75)-np.percentile(bc_arr,25):.1f}, range=[{bc_arr.min():.0f}, {bc_arr.max():.0f}]", flush=True)
print(f"boundary rate: {bdy_2c*100:.0f}%", flush=True)

# Analyze R+C
rc_results = {}
for src_key, fits in all_fits_rc.items():
    if fits:
        g_arr = np.array([f['g'] for f in fits])
        bdy = np.mean([f.get('boundary', False) for f in fits])
        rc_results[src_key] = {
            'n': len(fits),
            'g_median': float(np.median(g_arr)),
            'g_iqr': float(np.percentile(g_arr,75) - np.percentile(g_arr,25)),
            'g_range': [float(g_arr.min()), float(g_arr.max())],
            'boundary_rate': float(bdy),
            'all_g': g_arr.tolist(),
        }
        print(f"R+C {src_key}: g median={np.median(g_arr):.2f}, IQR={np.percentile(g_arr,75)-np.percentile(g_arr,25):.2f}, bdy={bdy*100:.0f}%", flush=True)

# Pass criterion
bs_med = float(np.median(bs_arr)); bc_med = float(np.median(bc_arr))
passed_2c = (abs(bs_med) <= 5) and (abs(bc_med) <= 5)
rc_g_meds = [r['g_median'] for r in rc_results.values()]
passed_rc = all(1.8 <= g <= 2.2 for g in rc_g_meds) if rc_g_meds else False
overall_pass = passed_2c and passed_rc

print(f"\n=== PASS CRITERIA ===", flush=True)
print(f"2-comp |β_s|≤5°, |β_c|≤5°: {'PASS' if passed_2c else 'FAIL'} (β_s={bs_med:+.1f}, β_c={bc_med:+.1f})", flush=True)
print(f"R+C g∈[1.8, 2.2] across sources: {'PASS' if passed_rc else 'FAIL'} (medians={[f'{g:.2f}' for g in rc_g_meds]})", flush=True)
print(f"OVERALL: {'PASS — Phase C ready' if overall_pass else 'FAIL — design needs revision'}", flush=True)

out = {
    'config': {
        'design': 'bootstrap leave-one-HC-as-CVD',
        'N_OUTER': N_OUTER,
        'candidate': target_label,
        'subject': 'sub-08',
        'rng_seed': RNG_SEED,
        'gt_note': 'Each iteration: 1 random HC becomes synthetic CVD (real data, δθ=0 by construction). 6 remaining HCs are pool, 5 sampled per fit.',
    },
    'gt': {'g': 2.0, 'beta_s': 0.0, 'beta_c': 0.0, 'family': 'deutan'},
    '2comp': {
        'n': len(all_fits_2c),
        'beta_s_median': bs_med,
        'beta_s_iqr': float(np.percentile(bs_arr,75) - np.percentile(bs_arr,25)),
        'beta_s_range': [float(bs_arr.min()), float(bs_arr.max())],
        'beta_c_median': bc_med,
        'beta_c_iqr': float(np.percentile(bc_arr,75) - np.percentile(bc_arr,25)),
        'beta_c_range': [float(bc_arr.min()), float(bc_arr.max())],
        'boundary_rate': float(bdy_2c),
        'all_beta_s': bs_arr.tolist(),
        'all_beta_c': bc_arr.tolist(),
    },
    'rc': rc_results,
    'passed_2comp': bool(passed_2c),
    'passed_rc': bool(passed_rc),
    'overall_passed': bool(overall_pass),
}
out_path = OUT_DIR / 's11_null_sanity_sub08_C1.json'
out_path.write_text(json.dumps(out, indent=2))
print(f"\nSaved: {out_path}", flush=True)
