#!/usr/bin/env python3
"""cycle6_voxel_diag.py — Plan 04 Cycle 6 Step 1 voxel-level diagnostic.

Goal:
  Identify which (subject, ROI, color) cells are outliers when compared to
  the HC pool, decoupling sub-09 specific signal from sub-10 (near-normal)
  background. n_voxels differs across subjects (V1: 405..858; V4: 16..70),
  so cross-subject voxel-by-voxel z is ill-defined. Instead use:
    (A) per-color *within-subject* scalar signatures
        - mean amplitude across voxels (after run-mean)
        - cross-voxel RMS  (= sqrt(mean(amp**2)))
        - cross-voxel std
        - top-10% voxel mean amplitude (peak-driven signal)
        - blank-relative fraction (signal vs blank scale; not available since
          we don't have blank here, so skipped)
    (B) within-subject 8x8 color RDM (1-pearson on voxel patterns across 8
        colors). RDM is voxel-count-invariant -> comparable across subjects.
    (C) cell-level outlier detection: for each (color_i, color_j) RDM cell
        and for each per-color signature, compute z = (subj - HCmean)/HCstd.
    (D) per-color *aggregate* outlier score: |z| averaged over RDM rows for
        that color + per-color signature z's.

Outputs (per ROI):
  cycle6_voxel_diag/{ROI}_summary.json
    - HC pool stats (mean, std for every signature/RDM cell)
    - per-subject z grid for sub-08, sub-09, sub-10, all HC LOO
    - top-outlier colors per subject
    - sub-09 vs sub-10 separation diagnostics:
       * overlap of outlier colors (Jaccard)
       * per-color z difference (sub09 - sub10)
    - HC sub-04 (anomaly check) z grid; HC sub-02 same

Comparison vs MEMORY task #21:
  MEMORY z's are scalar per-color vuln z's *vs Machado-shifted HC sim* (i.e.,
  not voxel-level). We REPRODUCE those numbers from neural_miss_table.csv as a
  reference, then add complementary voxel-pattern signatures.
"""

import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.stats import pearsonr

_HERE = Path(__file__).resolve().parent
_PHASE2 = _HERE.parent.parent
_PROJ = _PHASE2.parent.parent
sys.path.insert(0, str(_PHASE2 / 'scripts'))

_FWD = _PROJ / 'analysis' / 'future_phase1_forward_model' / 'scripts'
sys.path.insert(0, str(_FWD))

from utils_forward_model import HC_SUBJECTS, N_COLORS, load_amplitudes  # noqa

CVD_TYPE = {'08': 'deutan', '09': 'protan', '10': 'normal'}
LOCAL_DATA = (_PROJ / 'analysis' / 'phase1_procrustes_decoding' / 'results'
              / 'visualization' / 'full_dataset_C010_with_residuals')

ROIS = ['V1', 'V2', 'V4']
HC_SUBS = ['01', '02', '03', '04', '05', '06', '07']
CVD_SUBS = ['08', '09']
SANITY_SUBS = ['10']
ALL_SUBS = HC_SUBS + CVD_SUBS + SANITY_SUBS
COLOR_NAMES = ['red', 'orange', 'yellow', 'green',
               'cyan', 'blue', 'purple', 'magenta']


# ---------------------------------------------------------------------------
def per_color_signatures(amps):
    """amps: (R, C, V). Return per-color scalar signatures.

    Returns dict of name -> (C,) array.
      - mean_amp: mean across voxels (after run-mean)  [magnitude scale]
      - rms_amp:  RMS across voxels
      - std_amp:  std across voxels
      - top10_mean: mean of top-10% voxels (peak)
      - run_consistency: across-run mean Pearson on the mean-color pattern
    """
    R, C, V = amps.shape
    mean_pat = amps.mean(axis=0)  # (C, V), run-averaged
    sig = {
        'mean_amp':  mean_pat.mean(axis=1),
        'rms_amp':   np.sqrt((mean_pat ** 2).mean(axis=1)),
        'std_amp':   mean_pat.std(axis=1),
    }
    # top-10% voxels per color
    k_top = max(1, int(round(V * 0.10)))
    top10 = np.zeros(C)
    for c in range(C):
        v = mean_pat[c]
        idx = np.argsort(-v)[:k_top]
        top10[c] = v[idx].mean()
    sig['top10_mean'] = top10
    # Run consistency: mean pairwise corr across runs of each color's voxel
    # pattern (scalar per color)
    rc = np.zeros(C)
    for c in range(C):
        mat = amps[:, c, :]  # (R, V)
        if V < 2:
            rc[c] = 0.0
            continue
        cs = []
        for i in range(R):
            for j in range(i + 1, R):
                if mat[i].std() > 0 and mat[j].std() > 0:
                    r, _ = pearsonr(mat[i], mat[j])
                    cs.append(r if np.isfinite(r) else 0.0)
        rc[c] = float(np.mean(cs)) if cs else 0.0
    sig['run_consistency'] = rc
    return sig


def color_rdm(amps):
    """8x8 RDM = 1 - Pearson on run-averaged voxel patterns."""
    pat = amps.mean(axis=0)  # (C, V)
    C = pat.shape[0]
    rdm = np.zeros((C, C))
    for i in range(C):
        for j in range(C):
            if i == j:
                continue
            if pat[i].std() == 0 or pat[j].std() == 0:
                rdm[i, j] = 1.0
                continue
            r, _ = pearsonr(pat[i], pat[j])
            r = r if np.isfinite(r) else 0.0
            rdm[i, j] = 1.0 - r
    return rdm


# ---------------------------------------------------------------------------
def hc_pool_stats(per_subject_data, exclude=None):
    """Aggregate HC pool stats. Optionally LOO exclude one HC.

    per_subject_data: dict subj -> {'sigs': {name: (C,)}, 'rdm': (C,C)}
    Return: dict with keys 'sigs_mu','sigs_sd','rdm_mu','rdm_sd', plus
    raw HC arrays for diagnostic.
    """
    hc_keys = [s for s in HC_SUBS if s in per_subject_data and s != exclude]
    sigs_stack = {}
    for k in per_subject_data[hc_keys[0]]['sigs']:
        arr = np.stack([per_subject_data[s]['sigs'][k] for s in hc_keys])
        sigs_stack[k] = arr  # (n_HC, C)
    rdm_stack = np.stack([per_subject_data[s]['rdm'] for s in hc_keys])
    return {
        'hc_subs': hc_keys,
        'sigs_mu': {k: v.mean(0) for k, v in sigs_stack.items()},
        'sigs_sd': {k: v.std(0, ddof=1) for k, v in sigs_stack.items()},
        'sigs_raw': {k: v for k, v in sigs_stack.items()},
        'rdm_mu':  rdm_stack.mean(0),
        'rdm_sd':  rdm_stack.std(0, ddof=1),
        'rdm_raw': rdm_stack,
    }


def z_against_pool(stat, mu, sd, eps=1e-9):
    sd_safe = np.where(sd < eps, eps, sd)
    return (stat - mu) / sd_safe


# ---------------------------------------------------------------------------
def main():
    out_dir = _PHASE2 / 'results' / 'cycles' / 'cycle6_voxel_diag'
    out_dir.mkdir(parents=True, exist_ok=True)
    data_dir = Path(LOCAL_DATA)

    aggregate = {
        'config': {
            'cycle': 6,
            'step': 1,
            'task': 'voxel_level_diagnostic',
            'rois': ROIS,
            'hc_subs': HC_SUBS,
            'cvd_subs': CVD_SUBS,
            'sanity_subs': SANITY_SUBS,
            'colors': COLOR_NAMES,
            'note': ('n_voxels differs across subjects -> using within-subject '
                     'per-color scalar signatures + 8x8 RDM (voxel-count '
                     'invariant) for cross-subject comparison.'),
        },
        'per_roi': {},
    }

    t0 = time.time()
    for roi in ROIS:
        print(f'\n=== ROI = {roi} ===')
        per_sub = {}
        for s in ALL_SUBS:
            try:
                amps = load_amplitudes(data_dir, s, roi)
            except FileNotFoundError:
                print(f'  [skip] sub-{s} {roi}: no amplitudes')
                continue
            sigs = per_color_signatures(amps)
            rdm = color_rdm(amps)
            per_sub[s] = {
                'n_voxels': int(amps.shape[2]),
                'sigs': sigs,
                'rdm': rdm,
            }
            print(f'  sub-{s} V={amps.shape[2]:>4d} '
                  f"mean(rms)={sigs['rms_amp'].mean():+.3f} "
                  f"runc={sigs['run_consistency'].mean():+.3f}")

        # --- LOO HC pool stats for each query subject ---
        roi_results = {
            'per_subject': {},
            'sub09_vs_sub10': {},
            'hc_anomaly': {},
        }
        for query in ALL_SUBS:
            if query not in per_sub:
                continue
            exclude = query if query in HC_SUBS else None
            pool = hc_pool_stats(per_sub, exclude=exclude)
            sigs_z = {}
            for k in per_sub[query]['sigs']:
                stat = per_sub[query]['sigs'][k]
                sigs_z[k] = z_against_pool(stat, pool['sigs_mu'][k],
                                            pool['sigs_sd'][k])
            rdm_z = z_against_pool(per_sub[query]['rdm'],
                                   pool['rdm_mu'], pool['rdm_sd'])
            # per-color aggregate |z|: signature mean + RDM row mean
            sig_abs = np.stack([np.abs(sigs_z[k]) for k in sigs_z], axis=0)
            sig_abs_mean = sig_abs.mean(axis=0)  # (C,)
            rdm_row_abs = np.abs(rdm_z).mean(axis=1)  # (C,)
            agg = sig_abs_mean + rdm_row_abs  # (C,)
            top_outlier = np.argsort(-agg)[:3].tolist()  # indices

            roi_results['per_subject'][query] = {
                'group': ('CVD' if query in CVD_TYPE
                          and CVD_TYPE[query] != 'normal'
                          else ('SANITY' if query == '10' else 'HC')),
                'n_voxels': per_sub[query]['n_voxels'],
                'sigs_z': {k: v.tolist() for k, v in sigs_z.items()},
                'rdm_z': rdm_z.tolist(),
                'sig_abs_mean_per_color': sig_abs_mean.tolist(),
                'rdm_row_abs_per_color': rdm_row_abs.tolist(),
                'agg_per_color': agg.tolist(),
                'top_outlier_colors': [{'idx': int(i),
                                        'name': COLOR_NAMES[i],
                                        'agg_z': float(agg[i])}
                                        for i in top_outlier],
                'pool_excluded': exclude,
                'pool_n_hc': len(pool['hc_subs']),
            }

        # --- sub-09 vs sub-10 separation ---
        if '09' in per_sub and '10' in per_sub:
            r9 = roi_results['per_subject']['09']
            r10 = roi_results['per_subject']['10']
            agg9 = np.array(r9['agg_per_color'])
            agg10 = np.array(r10['agg_per_color'])
            top9 = set([d['idx'] for d in r9['top_outlier_colors']])
            top10 = set([d['idx'] for d in r10['top_outlier_colors']])
            jacc = (len(top9 & top10) / len(top9 | top10)
                    if top9 | top10 else 0.0)
            uniq9 = sorted(top9 - top10)
            uniq10 = sorted(top10 - top9)
            shared = sorted(top9 & top10)
            roi_results['sub09_vs_sub10'] = {
                'jaccard_top3': float(jacc),
                'shared_top_colors': [{'idx': i, 'name': COLOR_NAMES[i]}
                                       for i in shared],
                'sub09_unique': [{'idx': i, 'name': COLOR_NAMES[i]}
                                  for i in uniq9],
                'sub10_unique': [{'idx': i, 'name': COLOR_NAMES[i]}
                                  for i in uniq10],
                'agg_diff_per_color_09minus10':
                    (agg9 - agg10).tolist(),
                'agg_diff_argmax_idx': int(np.argmax(agg9 - agg10)),
                'agg_diff_argmax_name':
                    COLOR_NAMES[int(np.argmax(agg9 - agg10))],
                'agg_diff_argmin_idx': int(np.argmin(agg9 - agg10)),
                'agg_diff_argmin_name':
                    COLOR_NAMES[int(np.argmin(agg9 - agg10))],
            }

        # --- HC anomaly: how do sub-04 / sub-02 look on this metric? ---
        for s in ('04', '02'):
            if s in roi_results['per_subject']:
                r = roi_results['per_subject'][s]
                agg = np.array(r['agg_per_color'])
                roi_results['hc_anomaly'][s] = {
                    'agg_max': float(agg.max()),
                    'agg_mean': float(agg.mean()),
                    'top_color': r['top_outlier_colors'][0],
                    'all_top3': r['top_outlier_colors'],
                }

        # write per-ROI json
        roi_path = out_dir / f'{roi}_summary.json'
        with open(roi_path, 'w') as f:
            json.dump(roi_results, f, indent=2, default=str)
        aggregate['per_roi'][roi] = {
            'top_outliers': {s: roi_results['per_subject'][s]['top_outlier_colors']
                              for s in roi_results['per_subject']},
            'sub09_vs_sub10': roi_results['sub09_vs_sub10'],
            'hc_anomaly': roi_results['hc_anomaly'],
        }
        print(f'  [wrote] {roi_path.name}')

    out_path = out_dir / 'aggregate.json'
    with open(out_path, 'w') as f:
        json.dump(aggregate, f, indent=2, default=str)
    print(f'\n[Wrote] {out_path}')
    print(f'[Done] elapsed={time.time()-t0:.1f}s')

    # ---- Print summary tables ----
    print('\n' + '=' * 100)
    print('=== Top-3 outlier colors per (ROI, subject) ===')
    for roi in ROIS:
        print(f'\n[{roi}]')
        for s in ALL_SUBS:
            top = aggregate['per_roi'][roi]['top_outliers'].get(s)
            if not top:
                continue
            grp = ('CVD' if s in CVD_SUBS else
                   ('SAN' if s in SANITY_SUBS else 'HC'))
            tag = ' '.join(f'{d["name"]}({d["agg_z"]:.2f})' for d in top)
            print(f'  sub-{s}({grp}): {tag}')

    print('\n=== sub-09 vs sub-10 separation (top-3 Jaccard) ===')
    for roi in ROIS:
        d = aggregate['per_roi'][roi].get('sub09_vs_sub10')
        if not d:
            continue
        u9 = ','.join(x['name'] for x in d['sub09_unique']) or '-'
        u10 = ','.join(x['name'] for x in d['sub10_unique']) or '-'
        sh = ','.join(x['name'] for x in d['shared_top_colors']) or '-'
        print(f'  [{roi}] J={d["jaccard_top3"]:.2f}  '
              f'shared={sh}  sub09_only={u9}  sub10_only={u10}  '
              f'argmax(09-10)={d["agg_diff_argmax_name"]}')

    print('\n=== HC anomaly check (sub-04, sub-02 max |z|) ===')
    for roi in ROIS:
        han = aggregate['per_roi'][roi].get('hc_anomaly', {})
        for s in ('04', '02'):
            if s in han:
                e = han[s]
                print(f'  [{roi}] sub-{s}: agg_max={e["agg_max"]:.2f} '
                      f'top={e["top_color"]["name"]}({e["top_color"]["agg_z"]:.2f})')


if __name__ == '__main__':
    main()
