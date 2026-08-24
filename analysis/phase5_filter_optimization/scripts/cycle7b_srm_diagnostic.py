"""
Cycle 7b - (SRM full trial diagnostic, sub-08 V2 + V4, sub-09 V1)
=================================================================
User directive (2026-05-26): "srm full trial, as srm can project each participants
into single common dimension so it can reduce noises and facilitate comparison".

Goal: Empirically compare SRM-aligned RDM cosine (HC mean vs CVD) against Cycle 5
A2 PCA-aligned RDM cosine. Hypothesis: SRM 의 *joint HC-pool optimization* (vs PCA
의 per-subject decomposition) 가 noise-reduce → cleaner CVD-HC separation.

Implementation: BrainIAK SRM (n_iter=20, features=K). HC pool 7 subjects training,
CVD shared response via fixed-S least-squares + orthogonalization (post-hoc transform).

Cells:
- sub-08 V2 (user-specified: "sub-08's V2 가 SRM 이면 more significant 할수도")
- sub-08 V4 (Cycle 5 best-PCA cell for sub-08)
- sub-09 V1 (Cycle 5 best-PCA cell for sub-09)
- sub-10 V1 (negative control)
- sub-10 V2 (negative control)

K values (project memory): V1=4, V2=4, V3=3, V4=3
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
from time import time
from typing import Dict, List, Tuple

import numpy as np
from brainiak.funcalign.srm import SRM
from scipy.spatial.distance import pdist
from scipy.stats import pearsonr

ROOT_AMPL = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/phase1_procrustes_decoding/results/visualization/full_dataset_C010_with_residuals')
OUT_DIR = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/phase5_filter_optimization/results/s10_inclusion')

HC_SUBJECTS = [f'sub-0{i}' for i in range(1, 8)]
ROI_K = {'V1': 4, 'V2': 4, 'V3': 3, 'V4': 3}

CELLS = [
    ('sub-08', 'V2'),
    ('sub-08', 'V4'),
    ('sub-09', 'V1'),
    ('sub-10', 'V1'),
    ('sub-10', 'V2'),
]


def load_subject_mean(sid: str, roi: str) -> np.ndarray:
    """Return (n_voxels, n_conds=8) array — mean over 6 runs, transposed for BrainIAK."""
    p = ROOT_AMPL / sid / roi / 'amplitudes_procrustes.npy'
    a = np.load(p)  # (6, 8, n_vox)
    mean_amp = a.mean(axis=0)  # (8, n_vox)
    return mean_amp.T  # (n_vox, 8)


def fit_w_to_shared(x: np.ndarray, s: np.ndarray, n_iter: int = 30) -> np.ndarray:
    """
    Given fixed shared response S (K, T) and subject data X (n_vox, T), solve
    orthogonal W (n_vox, K) minimizing ||X - W S||_F^2 with W^T W = I.

    Procrustes-style: SVD(X S^T) = U D V^T → W = U V^T.
    """
    xst = x @ s.T  # (n_vox, K)
    u, _, vt = np.linalg.svd(xst, full_matrices=False)
    return u @ vt  # (n_vox, K)


def rdm_cosine(x: np.ndarray) -> np.ndarray:
    """X shape (K, n_conds): pairwise cosine distance among conditions."""
    return pdist(x.T, metric='cosine')


def srm_atom_for_cell(cvd_id: str, roi: str, n_iter: int = 20, seed: int = 0) -> Dict:
    """
    SRM training on HC pool (7 subjects), CVD W learned via fixed-S Procrustes.
    Returns:
      - cvd_rdm_shared: shared-space RDM (1 − cosine) for CVD
      - hc_mean_rdm_shared: HC mean shared RDM
      - rdm_cosine: cosine similarity between CVD and HC mean RDM (1 − dist for atom)
      - atom_loss: 1 − rdm_cosine (smaller = more CVD-HC similar; align with Cycle 5 A2)
      - per_hc_rdm_cosine: per-HC-vs-pool-mean for null baseline
    """
    K = ROI_K[roi]
    rng = np.random.default_rng(seed)

    # 1. Load HC pool data
    hc_data: List[np.ndarray] = []
    for h in HC_SUBJECTS:
        hc_data.append(load_subject_mean(h, roi))

    # 2. Train SRM on full HC pool
    srm = SRM(n_iter=n_iter, features=K, rand_seed=seed)
    srm.fit(hc_data)
    s_shared = srm.s_  # (K, 8)
    w_hc = srm.w_  # list of (n_vox_i, K)

    # 3. Project HC subjects to shared space (already done by srm.transform on training data is identity? — recompute)
    hc_shared_responses = []  # list of (K, 8)
    for x, w in zip(hc_data, w_hc):
        hc_shared_responses.append(w.T @ x)
    hc_rdms = np.array([rdm_cosine(r) for r in hc_shared_responses])  # (7, n_pairs)
    hc_mean_rdm = hc_rdms.mean(axis=0)  # mean across HCs

    # 4. CVD: solve W_cvd via Procrustes against fixed S
    x_cvd = load_subject_mean(cvd_id, roi)
    w_cvd = fit_w_to_shared(x_cvd, s_shared)  # (n_vox, K)
    cvd_shared = w_cvd.T @ x_cvd  # (K, 8)
    cvd_rdm = rdm_cosine(cvd_shared)

    # 5. RDM cosine similarity (CVD vs HC mean)
    # atom_loss = 1 - cosine_similarity(rdm_cvd, rdm_hc_mean)
    cos_sim = float(np.dot(cvd_rdm, hc_mean_rdm) / (np.linalg.norm(cvd_rdm) * np.linalg.norm(hc_mean_rdm) + 1e-12))
    atom_loss = 1.0 - cos_sim

    # 6. Per-HC vs pool-mean (LOO-style baseline for null distribution)
    per_hc_atom = []
    for i in range(len(HC_SUBJECTS)):
        held = hc_rdms[i]
        rest_mean = np.delete(hc_rdms, i, axis=0).mean(axis=0)
        cs = float(np.dot(held, rest_mean) / (np.linalg.norm(held) * np.linalg.norm(rest_mean) + 1e-12))
        per_hc_atom.append(1.0 - cs)
    per_hc_atom = np.array(per_hc_atom)

    # 7. Pearson correlation of RDMs (additional summary)
    pear_r, _ = pearsonr(cvd_rdm, hc_mean_rdm)

    return {
        'cvd_id': cvd_id,
        'roi': roi,
        'K': K,
        'atom_loss_cvd': atom_loss,
        'cos_sim_cvd_vs_hc_mean': cos_sim,
        'pearson_r_cvd_vs_hc_mean': float(pear_r),
        'per_hc_atom_loss': per_hc_atom.tolist(),
        'per_hc_atom_mean': float(per_hc_atom.mean()),
        'per_hc_atom_std': float(per_hc_atom.std(ddof=1)),
        'separation_z': float((atom_loss - per_hc_atom.mean()) / (per_hc_atom.std(ddof=1) + 1e-12)),
        'n_hc_subjects': len(HC_SUBJECTS),
        'n_iter': n_iter,
        'seed': seed,
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    results = []
    for cvd_id, roi in CELLS:
        t0 = time()
        try:
            res = srm_atom_for_cell(cvd_id, roi)
            res['elapsed_s'] = time() - t0
            results.append(res)
            print(f"\n[{cvd_id} {roi}] K={res['K']}")
            print(f"  CVD atom_loss = {res['atom_loss_cvd']:.4f}")
            print(f"  HC LOO mean   = {res['per_hc_atom_mean']:.4f} ± {res['per_hc_atom_std']:.4f}")
            print(f"  separation z  = {res['separation_z']:+.3f}")
            print(f"  Pearson r     = {res['pearson_r_cvd_vs_hc_mean']:+.3f}")
            print(f"  elapsed       = {res['elapsed_s']:.1f}s")
        except Exception as e:
            print(f"[{cvd_id} {roi}] FAILED: {e}", file=sys.stderr)
            results.append({'cvd_id': cvd_id, 'roi': roi, 'error': str(e)})

    out_path = OUT_DIR / 'cycle7b_srm_diagnostic.json'
    with out_path.open('w') as f:
        json.dump({
            'cells': CELLS,
            'k_per_roi': ROI_K,
            'hc_subjects': HC_SUBJECTS,
            'results': results,
        }, f, indent=2, default=str)
    print(f"\n→ {out_path.name}")

    # Print summary table
    print("\n========== Cycle 7b SRM Summary ==========")
    print(f"{'subj':8s}  {'ROI':4s}  {'K':2s}  {'CVD':>8s}  {'HC mean':>8s}  {'HC std':>8s}  {'sep z':>8s}  {'r':>8s}")
    for r in results:
        if 'error' in r:
            print(f"  {r['cvd_id']}  {r['roi']}  ERROR: {r['error']}")
            continue
        print(f"  {r['cvd_id']}  {r['roi']:4s}  {r['K']:2d}  "
              f"{r['atom_loss_cvd']:8.4f}  {r['per_hc_atom_mean']:8.4f}  "
              f"{r['per_hc_atom_std']:8.4f}  {r['separation_z']:+8.3f}  "
              f"{r['pearson_r_cvd_vs_hc_mean']:+8.3f}")


if __name__ == '__main__':
    main()
