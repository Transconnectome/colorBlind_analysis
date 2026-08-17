"""
Pre-Phase-C null sanity simulation v2 (5-train/2-test exact Phase B mimic).

Design (advisor #4, user retry 2026-05-25):
- 7 synthetic HCs (each with own voxel count, sampled from real HC voxel-level mean/std)
- 1 synthetic CVD (voxel count = sub-01 reference, sampled from sub-01 voxel mean/std)
- SUBSET_SIZE=5, N_RESAMPLES=1 (1 HC subset draw per outer iter)
- 50 outer iterations (different noise realization per iter)
- Synthetic JND = HC mean per pair (null behavioral)
- GT: δθ=0 everywhere (synthetic CVD draws from HC distribution)

Pass criterion (same as v1):
- |β_s median| ≤ 5°
- |β_c median| ≤ 5°
- R+C g median ∈ [1.8, 2.2] across Δλ sources

Cost: 50 outer × ~5-10s/fit ≈ 5-10 min.
Output: results/s11_pre_phase_c_null_sim/s11_null_sanity_sub08_C1_v2.json
"""

import json
import sys
import time
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import s10b_v3_extended as v3
from neural_loss import load_amplitudes as _orig_load_amps, load_hc_pool as _orig_load_hc
from behav_loss import load_jnd_per_pair as _orig_load_jnd, HC_JND_SUBJS

OUT_DIR = SCRIPT_DIR.parent / "results" / "s11_pre_phase_c_null_sim"
OUT_DIR.mkdir(parents=True, exist_ok=True)

HC_ALL = ['sub-01', 'sub-02', 'sub-03', 'sub-04', 'sub-05', 'sub-06', 'sub-07']
CVD_REF_HC = 'sub-01'  # reference for synthetic CVD voxel structure
N_OUTER = 50
v3.N_RESAMPLES = 1
v3.SUBSET_SIZE = 5

RNG_SEED = 91011
rng = np.random.default_rng(RNG_SEED)

print(f"[s11 v2] Pre-Phase-C null sanity (5-train/2-test Phase B mimic), N_OUTER={N_OUTER}", flush=True)

# Pre-load real HC stats per (HC, ROI): mean & std per (color, voxel)
hc_stats = {}
for hc in HC_ALL:
    hc_stats[hc] = {}
    for roi in v3.ROIS:
        try:
            real = _orig_load_amps(hc, roi)
        except Exception:
            continue
        mu = real.mean(axis=0)  # (8, V_s)
        sd = real.std(axis=0, ddof=1)  # (8, V_s)
        n_run = real.shape[0]
        hc_stats[hc][roi] = {'mu': mu, 'sd': sd, 'n_run': n_run, 'V_s': real.shape[2]}

print(f"  pre-loaded HC stats for {len(hc_stats)} subjects × {len(v3.ROIS)} ROIs", flush=True)

# HC mean JND (synthetic null behavioral)
hc_jnds = [_orig_load_jnd(h) for h in HC_JND_SUBJS]
syn_jnd = {}
for p in hc_jnds[0].keys():
    vals = [j[p] for j in hc_jnds if j.get(p) is not None]
    if vals:
        syn_jnd[p] = float(np.mean(vals))

# Find sub-08 C1 combo
combos = v3.enumerate_combos_sub08()
target_label = 'γYG|RDMV1+V4|noLOCO'
c1_idx = next((i for i, c in enumerate(combos) if c['label'] == target_label), None)
assert c1_idx is not None, f"Combo {target_label} not found"

orig_HC_SUBJS = v3.HC_SUBJS

def sample_amp(stats, rng_local):
    """Sample (n_run, 8, V_s) from per-(color, voxel) Gaussian."""
    mu, sd, n_run = stats['mu'], stats['sd'], stats['n_run']
    n_col, V_s = mu.shape
    noise = rng_local.standard_normal((n_run, n_col, V_s))
    return mu[None, :, :] + sd[None, :, :] * noise

all_fits_2c = []
all_fits_rc = {'rc_DPS_lit': [], 'rc_Boehm_mid': [], 'rc_JND_Lamb': []}

t_start = time.time()
for it in range(N_OUTER):
    sim_rng = np.random.default_rng(RNG_SEED + 1 + it)
    # Generate synthetic HCs (each with own voxel count) and synthetic CVD (sub-01 ref voxel)
    syn_hc_amps = {}  # {hc_id: {roi: amps}}
    for hc in HC_ALL:
        syn_hc_amps[hc] = {}
        for roi in v3.ROIS:
            if roi in hc_stats[hc]:
                syn_hc_amps[hc][roi] = sample_amp(hc_stats[hc][roi], sim_rng)
    syn_cvd_amps = {}
    for roi in v3.ROIS:
        if roi in hc_stats[CVD_REF_HC]:
            syn_cvd_amps[roi] = sample_amp(hc_stats[CVD_REF_HC][roi], sim_rng)
    # Monkey-patch
    v3.HC_SUBJS = HC_ALL
    v3.load_amplitudes = lambda subject, roi, _hc=syn_hc_amps, _cvd=syn_cvd_amps: (_cvd[roi] if subject == 'sub-08' else _hc[subject].get(roi))
    v3.load_hc_pool = lambda roi, _hc=syn_hc_amps: {h: _hc[h][roi] for h in HC_ALL if roi in _hc[h]}
    v3.load_jnd_per_pair = lambda subject, _jnd=syn_jnd: _jnd
    # Run fit
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
        print(f"  [{it+1}/{N_OUTER}] elapsed={elapsed:.0f}s eta={eta:.0f}s", flush=True)

v3.HC_SUBJS = orig_HC_SUBJS

bs_arr = np.array([f['beta_s'] for f in all_fits_2c])
bc_arr = np.array([f['beta_c'] for f in all_fits_2c])
bdy_2c = np.mean([f.get('boundary', False) for f in all_fits_2c])
print(f"\n=== sub-08 C1 2-comp null-GT recovery (N={len(all_fits_2c)}, 5-train/2-test) ===", flush=True)
print(f"β_s: median={np.median(bs_arr):+.1f}, IQR={np.percentile(bs_arr,75)-np.percentile(bs_arr,25):.1f}, range=[{bs_arr.min():.0f}, {bs_arr.max():.0f}]", flush=True)
print(f"β_c: median={np.median(bc_arr):+.1f}, IQR={np.percentile(bc_arr,75)-np.percentile(bc_arr,25):.1f}, range=[{bc_arr.min():.0f}, {bc_arr.max():.0f}]", flush=True)
print(f"boundary rate: {bdy_2c*100:.0f}%", flush=True)

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
        'design': '5-train/2-test Phase B exact mimic (HC pool=7, SUBSET_SIZE=5, N_OUTER=50 sim × N_INNER=1)',
        'N_OUTER': N_OUTER,
        'candidate': target_label,
        'subject': 'sub-08',
        'cvd_ref_hc': CVD_REF_HC,
        'rng_seed': RNG_SEED,
        'gt_note': 'Synthetic 7 HCs (own voxel count, MVN per HC) + synthetic CVD (sub-01 voxel ref). δθ=0 by construction (CVD draws from sub-01 voxel distribution).',
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
out_path = OUT_DIR / 's11_null_sanity_sub08_C1_v2.json'
out_path.write_text(json.dumps(out, indent=2))
print(f"\nSaved: {out_path}", flush=True)
