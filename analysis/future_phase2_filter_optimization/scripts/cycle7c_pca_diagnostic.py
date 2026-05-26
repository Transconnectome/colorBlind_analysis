"""
Cycle 7c - PCA-aligned RDM diagnostic (mirror of cycle7b SRM diagnostic).

Same cells, same HC pool, same metric definitions as cycle7b_srm_diagnostic.py,
but RDMs are built in PCA-aligned space (s10b_v6 convention, K_PCA=6) instead
of BrainIAK-SRM shared space. Use this to test whether SRM vs PCA give the
same CVD-HC separation per cell.

Metric:
  atom_loss  = 1 - cosine(rdm_cvd_vec, rdm_hc_mean_vec)        # 28-d pair vector
  per_hc[i]  = 1 - cosine(rdm_hc_i_vec, mean_over_j!=i(rdm_hc_j_vec))
  sep_z      = (atom_loss - mean(per_hc)) / std(per_hc)

PCA-RDM:
  pattern_8xV (mean over 6 runs)
  -> centered SVD -> top K_PCA=6 component scores (8 x K_PCA)
  -> 8x8 correlation-distance RDM (28-pair vector)
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
from time import time
from typing import List

import numpy as np
from scipy.spatial.distance import pdist
from scipy.stats import pearsonr

ROOT_AMPL = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/'
                 'Projects/colorBlind_analysis/analysis/'
                 'phase1_procrustes_decoding/results/visualization/'
                 'full_dataset_C010_with_residuals')
OUT_DIR = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/'
               'Projects/colorBlind_analysis/analysis/'
               'future_phase2_filter_optimization/results/s10_inclusion')

HC_SUBJECTS = [f'sub-0{i}' for i in range(1, 8)]
ROI_K = {'V1': 4, 'V2': 4, 'V3': 3, 'V4': 3}
K_PCA = 6  # matches s10b_v6 PCA_SHARED_K

CELLS = [
    ('sub-08', 'V2'),
    ('sub-08', 'V4'),
    ('sub-09', 'V1'),
    ('sub-10', 'V1'),
    ('sub-10', 'V2'),
]


def load_mean_pattern(sid: str, roi: str) -> np.ndarray:
    """Return (8, n_vox) — mean over 6 runs."""
    p = ROOT_AMPL / sid / roi / 'amplitudes_procrustes.npy'
    a = np.load(p)  # (6, 8, n_vox)
    return a.mean(axis=0)  # (8, n_vox)


def voxel_pca_scores(pattern_8xV: np.ndarray, k: int) -> np.ndarray:
    mp = pattern_8xV - pattern_8xV.mean(axis=0, keepdims=True)
    U, S, _ = np.linalg.svd(mp, full_matrices=False)
    k_eff = min(k, U.shape[1])
    return U[:, :k_eff] * S[:k_eff]  # (8, k_eff)


def rdm_pca_vec(pattern_8xV: np.ndarray, k: int = K_PCA) -> np.ndarray:
    """8x8 correlation distance over PCA-component scores, returned as 28-d upper triangle."""
    scores = voxel_pca_scores(pattern_8xV, k)
    return pdist(scores, metric='correlation')  # (28,)


def cos_sim(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-12))


def pca_atom_for_cell(cvd_id: str, roi: str) -> dict:
    # HC pool RDMs in PCA-space
    hc_rdms: List[np.ndarray] = []
    hc_kept: List[str] = []
    for h in HC_SUBJECTS:
        try:
            pat = load_mean_pattern(h, roi)
            r = rdm_pca_vec(pat)
            if np.all(np.isfinite(r)):
                hc_rdms.append(r)
                hc_kept.append(h)
        except Exception as e:
            print(f"  HC skip {h} {roi}: {e}", file=sys.stderr)
    if len(hc_rdms) < 2:
        raise RuntimeError(f"HC pool too small for {roi}: {len(hc_rdms)}")
    hc_arr = np.stack(hc_rdms, axis=0)  # (n_hc, 28)
    hc_mean = hc_arr.mean(axis=0)

    # CVD RDM
    cvd_pat = load_mean_pattern(cvd_id, roi)
    cvd_rdm = rdm_pca_vec(cvd_pat)
    atom_loss = 1.0 - cos_sim(cvd_rdm, hc_mean)
    pear_r, _ = pearsonr(cvd_rdm, hc_mean)

    # per-HC LOO atom (each HC vs mean of others)
    per_hc = []
    for i in range(len(hc_kept)):
        held = hc_arr[i]
        rest_mean = np.delete(hc_arr, i, axis=0).mean(axis=0)
        per_hc.append(1.0 - cos_sim(held, rest_mean))
    per_hc = np.array(per_hc)

    return {
        'cvd_id': cvd_id,
        'roi': roi,
        'K_pca': K_PCA,
        'K_srm_reference': ROI_K[roi],
        'atom_loss_cvd': float(atom_loss),
        'cos_sim_cvd_vs_hc_mean': float(1.0 - atom_loss),
        'pearson_r_cvd_vs_hc_mean': float(pear_r),
        'per_hc_atom_loss': per_hc.tolist(),
        'per_hc_atom_mean': float(per_hc.mean()),
        'per_hc_atom_std': float(per_hc.std(ddof=1)),
        'separation_z': float((atom_loss - per_hc.mean()) / (per_hc.std(ddof=1) + 1e-12)),
        'hc_subjects_kept': hc_kept,
        'n_hc_subjects': len(hc_kept),
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    results = []
    for cvd_id, roi in CELLS:
        t0 = time()
        try:
            res = pca_atom_for_cell(cvd_id, roi)
            res['elapsed_s'] = time() - t0
            results.append(res)
            print(f"\n[{cvd_id} {roi}] K_PCA={res['K_pca']} (SRM-K ref={res['K_srm_reference']})")
            print(f"  CVD atom_loss = {res['atom_loss_cvd']:.4f}")
            print(f"  HC LOO mean   = {res['per_hc_atom_mean']:.4f} +/- {res['per_hc_atom_std']:.4f}")
            print(f"  separation z  = {res['separation_z']:+.3f}")
            print(f"  Pearson r     = {res['pearson_r_cvd_vs_hc_mean']:+.3f}")
            print(f"  n_HC kept     = {res['n_hc_subjects']}")
            print(f"  elapsed       = {res['elapsed_s']:.3f}s")
        except Exception as e:
            print(f"[{cvd_id} {roi}] FAILED: {e}", file=sys.stderr)
            results.append({'cvd_id': cvd_id, 'roi': roi, 'error': str(e)})

    out_path = OUT_DIR / 'cycle7c_pca_diagnostic.json'
    with out_path.open('w') as f:
        json.dump({
            'cells': CELLS,
            'k_pca': K_PCA,
            'k_per_roi_srm_reference': ROI_K,
            'hc_subjects': HC_SUBJECTS,
            'results': results,
        }, f, indent=2, default=str)
    print(f"\n-> {out_path.name}")

    # Side-by-side with SRM
    srm_path = OUT_DIR / 'cycle7b_srm_diagnostic.json'
    if srm_path.exists():
        srm = json.loads(srm_path.read_text())
        srm_by_cell = {(r['cvd_id'], r['roi']): r for r in srm['results'] if 'error' not in r}

        print("\n========== PCA vs SRM (atom_loss / sep_z) ==========")
        hdr = f"{'subj':6s} {'ROI':3s} | {'PCA atom':>9s} {'PCA z':>7s} | {'SRM atom':>9s} {'SRM z':>7s} | {'d(atom)':>9s} {'d(z)':>7s}"
        print(hdr)
        print('-' * len(hdr))
        for r in results:
            if 'error' in r:
                continue
            key = (r['cvd_id'], r['roi'])
            s = srm_by_cell.get(key)
            if not s:
                print(f"{r['cvd_id']:6s} {r['roi']:3s} | {r['atom_loss_cvd']:9.4f} {r['separation_z']:+7.3f} |    no SRM ref")
                continue
            d_atom = r['atom_loss_cvd'] - s['atom_loss_cvd']
            d_z = r['separation_z'] - s['separation_z']
            print(f"{r['cvd_id']:6s} {r['roi']:3s} | "
                  f"{r['atom_loss_cvd']:9.4f} {r['separation_z']:+7.3f} | "
                  f"{s['atom_loss_cvd']:9.4f} {s['separation_z']:+7.3f} | "
                  f"{d_atom:+9.4f} {d_z:+7.3f}")


if __name__ == '__main__':
    main()
