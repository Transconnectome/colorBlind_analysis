"""
Phase D Multi-point sim — Round 3 on Pipeline 2 final candidates (2026-05-26).

User directive 2026-05-26: drop (β_s=44, β_c=36) (catastrophic agg fit),
verify remaining candidates' identifiability via GT recovery.

Final candidates after advisor closure check:
  - sub-08 (β_s=38, β_c=−10) γALL|RDMV1|noLOCO  [stability candidate]
  - sub-08 (β_s=6,  β_c=−42) γOY|RDMV2|noLOCO   [loss-robust aggregate]
  - sub-09 (β_s=2,  β_c=24)  γALL|RDMV1|noLOCO  [primary]

Pass criterion (DECISION_CRITERIA §4 E3):
  - β_s_iqr < 30°, β_c_iqr < 30°
  - recovery median within ±10° of GT

Inherits methodology from s13_multipoint_validation.py but uses v6 enumeration
(has γALL atom required by S08-stable / S09-primary candidates).

Output: results/s13_multipoint_sim/s13_round3_recovery.json
"""
import json
import sys
import time
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

# Use v6 (has γALL) instead of v4
import s10b_v6_pca_rdm as v6
from rc_1dof import forward_rc
from two_comp import forward_2comp
from neural_loss import load_amplitudes as _orig_load_amps
from behav_loss import load_jnd_per_pair as _orig_load_jnd, HC_JND_SUBJS
from utils_forward_model import create_basis_full, HUE_ANGLES

OUT_DIR = SCRIPT_DIR.parent / "results" / "s13_multipoint_sim"
OUT_DIR.mkdir(parents=True, exist_ok=True)

HC_ALL = ['sub-01', 'sub-02', 'sub-03', 'sub-04', 'sub-05', 'sub-06', 'sub-07']
N_OUTER = 50
N_INNER = 1
v6.N_RESAMPLES = N_INNER
v6.SUBSET_SIZE = 4  # left-one-out gives 6 HCs, 4-train/2-test from 6

RNG_SEED = 27182  # different from previous (13579) for independence


def apply_gt_perturbation(amps, gt_config, hues=None):
    if hues is None:
        hues = np.arange(0, 360, 45, dtype=float)
    if gt_config['model'] == 'rc':
        delta = forward_rc(gt_config['delta_lambda'], gt_config['g'], gt_config['family'])
    else:
        delta = forward_2comp(gt_config['beta_s'], gt_config['beta_c'], gt_config['family'])
    if np.max(np.abs(delta)) < 1e-3:
        return amps.copy()
    K = 8
    C_base = create_basis_full(K, basis_type='fe')[HUE_ANGLES.astype(int)]
    C_shift = create_basis_full(K, basis_type='fe')[((HUE_ANGLES + delta) % 360).astype(int)]
    perturbed = amps.copy()
    for r in range(amps.shape[0]):
        Y = amps[r]  # (8, V_s)
        try:
            Cinv = np.linalg.pinv(C_base)
        except Exception:
            continue
        W = Cinv @ Y
        Y_shift = C_shift @ W
        perturbed[r] = Y_shift
    return perturbed


CANDIDATES = [
    {
        'id': 'S08-stable',
        'subject': 'sub-08',
        'family': 'deutan',
        'model': '2comp',
        'beta_s_gt': 38.0,
        'beta_c_gt': -10.0,
        'combo_label': 'γALL|RDMV1|noLOCO',
    },
    {
        'id': 'S08-robust',
        'subject': 'sub-08',
        'family': 'deutan',
        'model': '2comp',
        'beta_s_gt': 6.0,
        'beta_c_gt': -42.0,
        'combo_label': 'γOY|RDMV2|noLOCO',
    },
    {
        'id': 'S09-primary',
        'subject': 'sub-09',
        'family': 'protan',
        'model': '2comp',
        'beta_s_gt': 2.0,
        'beta_c_gt': 24.0,
        'combo_label': 'γALL|RDMV1|noLOCO',
    },
]

print(f"[s13 Round 3] pre-loading HC data", flush=True)
all_hc_amps = {}
for hc in HC_ALL:
    all_hc_amps[hc] = {}
    for roi in v6.ROIS:
        try:
            all_hc_amps[hc][roi] = _orig_load_amps(hc, roi)
        except Exception:
            pass
all_hc_jnd = {hc: _orig_load_jnd(hc) for hc in HC_ALL}


def summarize_records(records, model):
    if not records:
        return None
    if model == '2comp':
        bs = np.array([r['beta_s'] for r in records])
        bc = np.array([r['beta_c'] for r in records])
        bdy = np.mean([r.get('boundary', False) for r in records])
        return {
            'n': len(records),
            'beta_s_median': float(np.median(bs)),
            'beta_s_iqr': float(np.percentile(bs, 75) - np.percentile(bs, 25)),
            'beta_s_range': [float(bs.min()), float(bs.max())],
            'beta_c_median': float(np.median(bc)),
            'beta_c_iqr': float(np.percentile(bc, 75) - np.percentile(bc, 25)),
            'beta_c_range': [float(bc.min()), float(bc.max())],
            'boundary_rate': float(bdy),
            'all_beta_s': bs.tolist(),
            'all_beta_c': bc.tolist(),
        }
    return None


def run_one_candidate_at_gt(cand, gt_label, gt_config, n_outer=N_OUTER):
    family = cand['family']
    rng = np.random.default_rng(RNG_SEED + hash(cand['id'] + gt_label) % 99991)
    subject = cand['subject']

    # Find combo using v6 enumeration
    combos = (v6.enumerate_combos_sub08() if subject == 'sub-08'
              else v6.enumerate_combos_sub09())
    target = next((c for c in combos if c['label'] == cand['combo_label']), None)
    if target is None:
        print(f"  [{cand['id']}/{gt_label}] WARN: combo {cand['combo_label']} not in v6 — SKIP",
              flush=True)
        return None
    print(f"  combo: {target['label']}", flush=True)

    records = []
    t_start = time.time()
    for it in range(n_outer):
        cvd_hc = HC_ALL[rng.integers(0, len(HC_ALL))]
        pool_hcs = [h for h in HC_ALL if h != cvd_hc]

        # Apply GT to cvd_hc amps
        perturbed = {}
        for roi in v6.ROIS:
            if roi in all_hc_amps[cvd_hc]:
                perturbed[roi] = apply_gt_perturbation(all_hc_amps[cvd_hc][roi], gt_config)

        # Monkey-patch v6 loaders
        v6.HC_SUBJS = pool_hcs
        original_load_amps = v6.load_amplitudes
        original_load_hc = v6.load_hc_pool
        original_load_jnd = v6.load_jnd_per_pair

        def patched_load_amps(sid, roi):
            if sid == subject:
                return perturbed.get(roi)
            return all_hc_amps.get(sid, {}).get(roi)

        def patched_load_hc(roi):
            return {h: all_hc_amps[h][roi] for h in pool_hcs if roi in all_hc_amps[h]}

        def patched_load_jnd(sid):
            if sid == subject:
                # Use cvd_hc's JND as the perturbed CVD's JND (proxy null)
                return all_hc_jnd.get(cvd_hc)
            return all_hc_jnd.get(sid)

        v6.load_amplitudes = patched_load_amps
        v6.load_hc_pool = patched_load_hc
        v6.load_jnd_per_pair = patched_load_jnd

        try:
            storage = v6.fit_subject(subject)
            # Extract the target combo's 2comp records
            label = target['label']
            if label in storage:
                for r in storage[label].get('2comp', []):
                    records.append(r)
        except Exception as e:
            print(f"  [{cand['id']}/{gt_label} iter {it}] ERROR: {e}", flush=True)
        finally:
            v6.load_amplitudes = original_load_amps
            v6.load_hc_pool = original_load_hc
            v6.load_jnd_per_pair = original_load_jnd

        if (it + 1) % 10 == 0:
            elapsed = time.time() - t_start
            print(f"    iter {it+1}/{n_outer} elapsed={elapsed:.0f}s", flush=True)

    return summarize_records(records, cand['model'])


def build_gt_set(cand):
    gts = []
    if cand['model'] == '2comp':
        gts.append(('null_b0', {'model': '2comp', 'family': cand['family'],
                                'beta_s': 0.0, 'beta_c': 0.0}))
        gts.append((f"fit_bs{cand['beta_s_gt']:.0f}_bc{cand['beta_c_gt']:.0f}",
                    {'model': '2comp', 'family': cand['family'],
                     'beta_s': cand['beta_s_gt'], 'beta_c': cand['beta_c_gt']}))
    return gts


def main():
    print(f"[s13 Round 3] N_OUTER={N_OUTER}, {len(CANDIDATES)} candidates", flush=True)
    results = {}
    t0 = time.time()
    for cand in CANDIDATES:
        cid = cand['id']
        print(f"\n=== [{cid}] {cand['combo_label']} subject={cand['subject']} "
              f"GT=(βs={cand['beta_s_gt']:.0f}, βc={cand['beta_c_gt']:.0f}) ===", flush=True)
        gts = build_gt_set(cand)
        results[cid] = {'config': cand, 'gt_runs': []}
        for gt_label, gt_config in gts:
            print(f"  [{cid} GT: {gt_label}]", flush=True)
            res = run_one_candidate_at_gt(cand, gt_label, gt_config)
            if res is not None:
                res['gt_label'] = gt_label
                res['gt_config'] = gt_config
                results[cid]['gt_runs'].append(res)
                print(f"  -> βs={res['beta_s_median']:+.0f}±{res['beta_s_iqr']:.0f}, "
                      f"βc={res['beta_c_median']:+.0f}±{res['beta_c_iqr']:.0f}, "
                      f"bdy={res['boundary_rate']*100:.0f}%", flush=True)
    total = round(time.time() - t0, 1)
    print(f"\n[s13 Round 3] total elapsed: {total}s", flush=True)
    out_path = OUT_DIR / 's13_round3_recovery.json'
    out_path.write_text(json.dumps(results, indent=2))
    print(f"Saved: {out_path}", flush=True)


if __name__ == '__main__':
    main()
