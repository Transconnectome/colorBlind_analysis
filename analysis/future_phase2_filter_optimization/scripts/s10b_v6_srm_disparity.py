"""S10b v6 SRM-Disparity variant.

Replaces the RDM atom with the **canonical SRM family** used in
`phase2_SRM_across_between/rerun_loo_consistent.py`:

    disparity(X, Y) = ||X_n @ R - Y_n||_F
        X_c = X - mean,  X_n = X_c / ||X_c||_F
        R = optimal orthogonal rotation via orthogonal_procrustes(X_n, Y_n)

Forward model δθ effect:
    perceived[i] = (HUES[i] + δ[i]) % 360
    perm[i]      = round(perceived[i] / 45) % 8
    sim_hc[:, i] = hc_mean_shared[:, perm[i]]   # HC pattern permuted by perceived color
    loss(δ)      = disparity(cvd_shared, sim_hc)

At δ=0, sim_hc = hc_mean_shared and loss = disparity(cvd_shared, hc_mean_shared)
= the LOO-style baseline that gave sub-08 V2 p=0.040* in canonical analysis.
At the correct δ, sim_hc should align with cvd_shared → disparity drops.

All other v6 structure unchanged (γ atoms / LOCO atom / 300 resamples / combos /
RC + 2-comp grids / train-test split / test_V1_RDM diagnostic).

Run:
  python s10b_v6_srm_disparity.py --subject sub-08
  python s10b_v6_srm_disparity.py --subject sub-09
"""
from __future__ import annotations
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
from brainiak.funcalign.srm import SRM
from scipy.linalg import orthogonal_procrustes

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import s10b_v6_pca_rdm as v6  # noqa: E402


def _procrustes_disparity(X: np.ndarray, Y: np.ndarray) -> float:
    """Mirror of phase2_SRM_across_between/rerun_loo_consistent.py.

    X, Y shape (n_conditions, n_features). Returns Frobenius residual after
    center, unit-Frobenius-norm, and optimal orthogonal rotation.
    Range: [0, sqrt(2)]; 0 = identical structure, ~1.41 = orthogonal.
    """
    X_c = X - X.mean(axis=0)
    Y_c = Y - Y.mean(axis=0)
    nx = np.linalg.norm(X_c, 'fro')
    ny = np.linalg.norm(Y_c, 'fro')
    if nx < 1e-10 or ny < 1e-10:
        return np.nan
    X_n = X_c / nx
    Y_n = Y_c / ny
    R, _ = orthogonal_procrustes(X_n, Y_n)
    return float(np.linalg.norm(X_n @ R - Y_n, 'fro'))


def make_srm_disparity_atom(roi, cvd_amp, pool_amps_dict, C_baseline, K):
    """Drop-in replacement for v6 PCA-RDM atom — SRM Procrustes-disparity family.

    Pipeline per call:
      1. HC pool mean-over-runs -> (n_vox, 8) tensors
      2. BrainIAK SRM(K=ROI_K, n_iter=20, seed=0) on HC pool
      3. HC subjects projected to shared space -> mean over HCs -> (K, 8)
      4. CVD via fixed-S Procrustes -> (K, 8) shared
      5. loss(δ): permute HC mean's color columns by perceived-color index,
         compute disparity vs CVD shared. δ=0 baseline = canonical disparity.
    """
    if len(pool_amps_dict) < 2:
        return None
    try:
        hc_data = []
        for sid, amp in pool_amps_dict.items():
            mean_pat = amp.mean(axis=0)  # (8, n_vox)
            hc_data.append(mean_pat.T)   # (n_vox, 8)
        srm = SRM(n_iter=20, features=int(K), rand_seed=0)
        srm.fit(hc_data)
        w_hc = srm.w_  # list of (n_vox_i, K)

        # HC shared patterns -> mean shared pattern (K, 8)
        hc_shared_list = [w.T @ x for x, w in zip(hc_data, w_hc)]
        hc_mean_shared = np.mean(np.stack(hc_shared_list, axis=0), axis=0)  # (K, 8)

        # CVD: Procrustes against fixed S
        s_shared = srm.s_  # (K, 8)
        x_cvd = cvd_amp.mean(axis=0).T  # (n_vox, 8)
        xst = x_cvd @ s_shared.T
        u_, _, vt_ = np.linalg.svd(xst, full_matrices=False)
        w_cvd = u_ @ vt_  # (n_vox, K)
        cvd_shared = w_cvd.T @ x_cvd  # (K, 8)
    except Exception:
        return None

    HUES = v6.HUES
    # (n_conditions=8, n_features=K) layout for disparity
    cvd_T = cvd_shared.T  # (8, K)

    def loss_fn(delta_8vec):
        try:
            perceived = (HUES + delta_8vec) % 360.0
            perm = np.array([int(round(perceived[i] / 45.0)) % 8
                              for i in range(8)])
            sim_hc = hc_mean_shared[:, perm]  # (K, 8) — color-permuted HC mean
            return _procrustes_disparity(cvd_T, sim_hc.T)
        except Exception:
            return np.nan

    return loss_fn


# Monkey-patch v6 so fit_subject(...) uses SRM-disparity atom
v6.make_rdm_atom = make_srm_disparity_atom


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--subject', required=True,
                        choices=['sub-08', 'sub-09'])
    parser.add_argument('--combo-start', type=int, default=None)
    parser.add_argument('--combo-end', type=int, default=None)
    args = parser.parse_args()

    print('=' * 100, flush=True)
    print('S10b v6 SRM-Disparity (mirror of v6 PCA-RDM, RDM atom -> Procrustes disparity)',
          flush=True)
    print(f'  Subject: {args.subject}  chunk=[{args.combo_start}:{args.combo_end}]',
          flush=True)
    print(f'  N_resamples: {v6.N_RESAMPLES}', flush=True)
    print('=' * 100, flush=True)

    t0 = time.time()
    storage = v6.fit_subject(args.subject, args.combo_start, args.combo_end)
    summary = v6.summarize(storage)
    elapsed = round(time.time() - t0, 1)
    print(f'\n[{args.subject}] elapsed: {elapsed}s', flush=True)

    suffix = f'_{args.subject}'
    if args.combo_start is not None:
        suffix += f'_c{args.combo_start:02d}-{args.combo_end:02d}'
    out_file = v6.OUT_DIR / f's10b_v6_srm_disparity_results{suffix}.json'
    with open(out_file, 'w') as f:
        json.dump({
            'subject': args.subject, 'storage': storage,
            'summary': summary, 'elapsed': elapsed,
            'meta': {
                'N_resamples': v6.N_RESAMPLES,
                'subset_size': v6.SUBSET_SIZE,
                'seed_base': v6.RNG_SEED,
                'combo_range': [args.combo_start, args.combo_end],
                'rdm_method': 'SRM_disparity (canonical phase2_SRM family)',
                'disparity_definition':
                    'Frobenius residual after center, unit-norm, optimal rotation',
            },
        }, f, indent=2, default=str)
    print(f'Saved: {out_file}', flush=True)


if __name__ == '__main__':
    main()
