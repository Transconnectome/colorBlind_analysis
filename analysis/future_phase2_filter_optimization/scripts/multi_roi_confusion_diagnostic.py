"""multi_roi_confusion_diagnostic.py — Per-pair cc-matrix deviation across V1, V2, V4.

Advisor-approved sensitivity check (2026-05-17). Tests whether the per-pair color
confusion structure observed at V4 (sub-08 cyan-violet z=+2.49, pink-green z=+1.51;
sub-09 green-violet z=+3.13) is consistent across cortical hierarchy.

Output: per-ROI per-subject per-pair Δ-similarity and z-scores.
No fitting. No loss. Descriptive only.
"""
from __future__ import annotations
import json
import numpy as np
from pathlib import Path

C010 = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/'
            'analysis/phase1_procrustes_decoding/results/visualization/'
            'full_dataset_C010_with_residuals')
HC = ['01','02','03','04','05','06','07']
COLORS = ['pink','red-orange','olive','green','cyan','sky-cyan','sky-blue','violet']

def load_amps(sid, roi):
    p = C010 / f'sub-{sid}' / roi / 'amplitudes_procrustes.npy'
    return np.load(p) if p.exists() else None

def cc_matrix(amps, n_vox):
    m = amps.mean(axis=0)[:, :n_vox]
    n = m.shape[0]
    M = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            M[i,j] = np.corrcoef(m[i], m[j])[0,1]
    return M

def analyze_roi(roi):
    amps = {sid: load_amps(sid, roi) for sid in HC+['08','09','10']}
    amps = {k:v for k,v in amps.items() if v is not None}
    if not amps: return None
    n_vox = min(a.shape[2] for a in amps.values())
    M = {sid: cc_matrix(amps[sid], n_vox) for sid in amps}
    hc_pool = np.mean([M[s] for s in HC if s in M], axis=0)
    hc_std  = np.std ([M[s] for s in HC if s in M], axis=0, ddof=1)
    return {'M': M, 'hc_pool': hc_pool, 'hc_std': hc_std, 'n_vox': n_vox, 'roi': roi}


def report_pairs(res, sid, top_k=5):
    M_subj = res['M'].get(sid)
    if M_subj is None: return None
    delta = M_subj - res['hc_pool']
    z = delta / (res['hc_std'] + 1e-9)
    iu, ju = np.triu_indices(8, k=1)
    pair_z = [(int(iu[i]), int(ju[i]), float(delta[iu[i], ju[i]]), float(z[iu[i], ju[i]]))
              for i in range(len(iu))]
    # Sort by z (top confusion = highest +z; top distinction = lowest -z)
    pair_z_pos = sorted(pair_z, key=lambda x: x[3], reverse=True)[:top_k]
    pair_z_neg = sorted(pair_z, key=lambda x: x[3])[:top_k]
    return {'top_conf': pair_z_pos, 'top_dist': pair_z_neg, 'all_pairs': pair_z}


def main():
    results = {}
    for roi in ['V1','V2','V4']:
        res = analyze_roi(roi)
        if res is None:
            print(f'{roi}: no data'); continue
        results[roi] = res
        print(f'\n{"="*80}\n{roi}  (n_vox = {res["n_vox"]}, HC pool n={sum(1 for s in HC if s in res["M"])})\n{"="*80}')
        for sid in ['08','09','10']:
            r = report_pairs(res, sid)
            if r is None:
                print(f'\nsub-{sid}: missing data in {roi}')
                continue
            grp = 'CVD' if sid in ['08','09'] else 'normal-control'
            print(f'\nsub-{sid} ({grp}):')
            print(f'  TOP CONFUSION (CVD similarity > HC):')
            for a, b, d, zv in r['top_conf']:
                sig = '★★' if abs(zv)>2.5 else ('★' if abs(zv)>1.96 else ('~' if abs(zv)>1.5 else ''))
                print(f'    c{a+1}({COLORS[a]:>10}) ↔ c{b+1}({COLORS[b]:>10}):  Δsim={d:+.3f}, z={zv:+.2f} {sig}')

    # Cross-ROI consistency table: focus on key confusions identified at V4
    print(f'\n{"="*80}\nCROSS-ROI CONSISTENCY: V4 top confusions, checked at V1/V2\n{"="*80}')
    # V4 key pairs per subject
    v4_key_pairs = {
        '08': [(4,7), (0,1), (2,4), (0,3)],  # cyan-violet, pink-red-orange, olive-cyan, pink-green
        '09': [(3,7), (0,1), (0,2), (2,5)],  # green-violet, pink-red-orange, pink-olive, olive-sky-cyan
    }
    for sid in ['08','09','10']:
        if sid not in v4_key_pairs and sid != '10': continue
        print(f'\nsub-{sid}:')
        pairs = v4_key_pairs.get(sid, v4_key_pairs['08'])  # use sub-08 pairs for sub-10 sanity
        print(f'{"pair":<32} {"V1 Δsim/z":<20} {"V2 Δsim/z":<20} {"V4 Δsim/z":<20}')
        print('-'*100)
        for a, b in pairs:
            row = [f'c{a+1}({COLORS[a]}) ↔ c{b+1}({COLORS[b]})']
            for roi in ['V1','V2','V4']:
                if roi not in results or sid not in results[roi]['M']:
                    row.append('NA')
                    continue
                M = results[roi]['M'][sid]
                hc_pool = results[roi]['hc_pool']
                hc_std = results[roi]['hc_std']
                d = M[a,b] - hc_pool[a,b]
                z = d / (hc_std[a,b] + 1e-9)
                sig = '★★' if abs(z)>2.5 else ('★' if abs(z)>1.96 else ('~' if abs(z)>1.5 else ''))
                row.append(f'{d:+.2f}/z={z:+.2f}{sig}')
            print(f'{row[0]:<32} {row[1]:<20} {row[2]:<20} {row[3]:<20}')

    # Aggregate Mahalanobis L_dir per ROI per subject (CVD-HC separation power)
    print(f'\n{"="*80}\nAGGREGATE L_dir_weighted per ROI per subject\n{"="*80}')
    print(f'{"subj":<10} {"V1":<14} {"V2":<14} {"V4":<14}')
    for sid in sorted(HC + ['08','09','10']):
        row = [f'sub-{sid}']
        for roi in ['V1','V2','V4']:
            if roi not in results or sid not in results[roi]['M']:
                row.append('NA')
                continue
            M = results[roi]['M'][sid]
            hc_pool = results[roi]['hc_pool']
            hc_std = results[roi]['hc_std']
            iu, ju = np.triu_indices(8, k=1)
            delta = (M - hc_pool)[iu, ju]
            w = 1.0 / (hc_std[iu, ju] + 1e-9)
            L_dir = float(np.mean(w * delta**2))
            grp = 'HC' if sid in HC else ('CVD' if sid in ['08','09'] else 'norm')
            row.append(f'{L_dir:.3f} ({grp})')
        print(f'{row[0]:<10} {row[1]:<14} {row[2]:<14} {row[3]:<14}')

    # Save results
    save = {roi: {
        'n_vox': res['n_vox'],
        'subjects_present': sorted(res['M'].keys()),
        'top_conf_per_cvd': {sid: report_pairs(res, sid)['top_conf'] if report_pairs(res, sid) else None
                              for sid in ['08','09','10'] if sid in res['M']},
    } for roi, res in results.items()}
    out = Path(__file__).parent.parent / 'results' / 'multi_roi_confusion.json'
    json.dump(save, open(out, 'w'), indent=2)
    print(f'\nWrote {out}')


if __name__ == '__main__':
    main()
