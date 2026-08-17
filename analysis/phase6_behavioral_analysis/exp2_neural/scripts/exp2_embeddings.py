#!/usr/bin/env python3
"""Stage 1 -- exp2 geometry EMBEDDINGS (File 1: raw coords + distance vectors).

Three parallel representations of the 8 colours, each per condition
(nofilter / window / optimal), stored so Stage 2 can cross-reference them:

  procrustes  : voxel-shape, MODEL-FREE (raw mean pattern, 8 x V). Distances are
                Euclidean on the centred+unit-Frobenius config, and correlation
                distance (V-independent, cross-subject comparable).
  srm         : HC-consensus K-dim shared space (canonical K={4,4,3,3}), each
                condition projected as a NEW subject (identical to exp2_convergent).
  fe_latent   : forward-model channel responses via B&H 2009 leave-one-colour-out
                RECONSTRUCTION (non-circular): fit encoding W (gcv) on the other 7,
                project held-out colour into channel space R_c = W @ x_c. 8 x K_FE.

Plus a LOCO interpolation block per condition (continuous decoded hue + adj/exact
sanity vs exp2_decoder_2x2 + sparse 8x8 confusion).

Displacement / agreement / JND correlation are DERIVED in Stage 2 from this file.

Run (production, server):  mpirun -np 1 python exp2_embeddings.py --variant matched --subject 08
Run (local mechanics test): mpirun -np 1 python exp2_embeddings.py --selftest
(brainiak SRM needs MPI init -> mpirun -np 1, per project CLAUDE.md §9.)
"""
import sys
import json
import argparse
import numpy as np
from pathlib import Path
from scipy.linalg import orthogonal_procrustes
from scipy.spatial.distance import pdist

ROOT = Path("/scratch/connectome/haba6030/colorBlind")
HC_C010 = ROOT / "derivatives" / "full_dataset_C010"
# local HC copy (has sub-01..07) -- used only for --selftest
LOCAL_C010 = Path("/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/"
                  "colorBlind_analysis/analysis/phase1_procrustes_decoding/results/"
                  "visualization/full_dataset_C010_with_residuals")
PHASE1 = Path(__file__).resolve().parents[3] / "future_phase1_forward_model" / "scripts"
sys.path.insert(0, str(PHASE1))
from utils_forward_model import create_basis_matrix, HUE_ANGLES, fit_W_ridge, gcv_select_alpha  # noqa
from loco_canonical import loco_forward_readouts  # noqa
from brainiak.funcalign.srm import SRM  # noqa

OUT = Path(__file__).resolve().parent.parent / "results"
HC_SUBJS = ['sub-01', 'sub-02', 'sub-03', 'sub-04', 'sub-05', 'sub-06', 'sub-07']
ROIS = ['V1', 'V2', 'V3', 'V4']
K_SRM = {'V1': 4, 'V2': 4, 'V3': 3, 'V4': 3}
K_FE = 6                                    # FE-6 uniform (Phase-2 neural convention)
CONDITIONS = ['nofilter', 'window', 'optimal']
COLOR_NAMES = ['red', 'orange', 'yellow', 'green', 'cyan', 'blue', 'purple', 'magenta']
TRIU = np.triu_indices(8, k=1)
C8 = create_basis_matrix(HUE_ANGLES, K_FE, basis_type='fe')          # (8, K_FE)
BASIS360 = create_basis_matrix(np.arange(360), K_FE, basis_type='fe')  # (360, K_FE)
# 8 measured JND pairs -> upper-tri index (colour indices 0..7)
JND_PAIRS = [('red', 'orange', 0, 1), ('orange', 'yellow', 1, 2), ('yellow', 'green', 2, 3),
             ('green', 'blue', 3, 5), ('blue', 'purple', 5, 6), ('yellow', 'purple', 2, 6),
             ('cyan', 'magenta', 4, 7), ('red', 'cyan', 0, 4)]


def load_npy(p):
    return np.load(p) if p.exists() else None


def r3(a):
    return np.round(np.asarray(a, float), 6).tolist()


def corr_dist_rdm(P):                       # (8,d) -> (28,)
    return (1.0 - np.corrcoef(P))[TRIU]


def procrustes_normalize(X):                # centre + unit Frobenius
    Xc = X - X.mean(0)
    return Xc / (np.linalg.norm(Xc, 'fro') + 1e-12)


# ---- SRM (identical to exp2_convergent) ----
def project_new_subject(srm, new_data):
    S = srm.s_
    W_init = new_data @ np.linalg.pinv(S)
    U, _, Vt = np.linalg.svd(W_init, full_matrices=False)
    return U @ Vt


def align_cond(srm, mean_8xV):
    return (project_new_subject(srm, mean_8xV.T).T @ mean_8xV.T).T   # (8,k)


# ---- FE-latent: B&H leave-one-colour-out reconstruction ----
def fe_latent_coords(amp):                  # amp (n_runs,8,V) -> (8,K_FE)
    n_runs, n_col, V = amp.shape
    amp_mean = amp.mean(0)
    R = np.zeros((n_col, K_FE))
    for c in range(n_col):
        train = [k for k in range(n_col) if k != c]
        C_train = np.tile(C8[train], (n_runs, 1))            # (n_runs*7, K)
        X_train = amp[:, train, :].reshape(-1, V)            # (n_runs*7, V)
        alpha, _ = gcv_select_alpha(C_train, X_train)
        W = fit_W_ridge(C_train, X_train, alpha)             # (K, V)
        R[c] = W @ amp_mean[c]                               # (K,) channel response
    return R


def decode_from_R(R):                       # (8,K) -> decoded hue deg per colour
    dec = np.full(8, np.nan)
    for c in range(8):
        r = R[c]
        if np.std(r) < 1e-12:
            continue
        corrs = np.array([np.corrcoef(r, BASIS360[h])[0, 1] for h in range(360)])
        if not np.all(np.isnan(corrs)):
            dec[c] = float(np.nanargmax(corrs))
    return dec


def circ_dist(a, b):
    d = np.abs(np.asarray(a, float) - np.asarray(b, float))
    return np.minimum(d, 360 - d)


def embed_condition(amp, srm):
    """One condition -> the three embeddings + LOCO block."""
    mean = amp.mean(0)                                       # (8,V)
    Pn = procrustes_normalize(mean)
    proc = {'coords': r3(mean), 'dist_eucl': r3(pdist(Pn)), 'dist_corr': r3(corr_dist_rdm(mean))}
    sc = align_cond(srm, mean)                              # (8,K_srm)
    srm_e = {'coords': r3(sc), 'dist_eucl': r3(pdist(sc)), 'dist_corr': r3(corr_dist_rdm(sc))}
    R = fe_latent_coords(amp)                               # (8,K_FE)
    fe_e = {'coords': r3(R), 'dist_eucl': r3(pdist(R)), 'dist_corr': r3(corr_dist_rdm(R))}

    dec = decode_from_R(R)
    true_hue = np.asarray(HUE_ANGLES, float)
    ols = loco_forward_readouts(amp, C8, BASIS360, decoder='ols', tasks=('adj', 'exact'))
    conf = np.zeros((8, 8), int)
    for c in range(8):
        if not np.isnan(dec[c]):
            conf[c, int(round(dec[c] / 45.0)) % 8] += 1
    loco = {'true_hue': r3(true_hue), 'decoded_hue': r3(dec),
            'hue_error_deg': r3(circ_dist(true_hue, dec)),
            'adj_acc': float(np.mean(ols['adj'])), 'exact_acc': float(np.mean(ols['exact'])),
            'confusion': conf.tolist()}
    return proc, srm_e, fe_e, loco


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--variant', default='matched', choices=['native', 'matched'])
    ap.add_argument('--subject', default='08')
    ap.add_argument('--selftest', action='store_true',
                    help='local mechanics test: HC 01-04 as ref, 05/06/07 as pseudo-conditions')
    args = ap.parse_args()

    if args.selftest:
        base_hc = LOCAL_C010
        hc_list = ['sub-01', 'sub-02', 'sub-03', 'sub-04']
        cond_src = {'nofilter': (LOCAL_C010, 'sub-05'), 'window': (LOCAL_C010, 'sub-06'),
                    'optimal': (LOCAL_C010, 'sub-07')}
        tag = 'selftest'
    else:
        base_hc = HC_C010
        hc_list = HC_SUBJS
        exp2_dir = ROOT / "derivatives" / ("full_dataset_C010_exp2" if args.variant == 'native'
                                           else "full_dataset_C010_exp2_matched")
        subj = f"sub-{args.subject}"
        tag = f"{subj}_{args.variant}"  # condition amps resolved per-ROI in the loop

    out = {'subject': tag, 'variant': args.variant, 'selftest': args.selftest,
           'color_names': COLOR_NAMES,
           'jnd_pairs': [{'name': f'{a}-{b}', 'i': i, 'j': j} for a, b, i, j in JND_PAIRS],
           'rois': {}}

    for roi in ROIS:
        print(f"\n{'='*64}\nROI {roi}\n{'='*64}")
        # HC means for SRM fit
        hc_amps = []
        for s in hc_list:
            a = load_npy(base_hc / s / roi / "amplitudes_procrustes.npy")
            if a is None or (roi == 'V4' and a.shape[2] < 20):
                continue
            hc_amps.append(a)
        if len(hc_amps) < 2:
            print(f"  skip {roi}: <2 HC")
            continue
        hc_means = [a.mean(0) for a in hc_amps]
        k = K_SRM[roi]
        srm = SRM(n_iter=10, features=k, rand_seed=0)
        srm.fit([m.T for m in hc_means])
        hc_aligned = [(w.T @ m.T).T for w, m in zip(srm.w_, hc_means)]     # (8,k)
        hc_ref_srm = np.mean(np.array(hc_aligned), axis=0)                 # (8,k)
        hc_ref_fe = np.mean([fe_latent_coords(a) for a in hc_amps], axis=0)  # (8,K_FE)
        hc_ref_proc_corr = np.mean([corr_dist_rdm(m) for m in hc_means], axis=0)

        # resolve condition amps
        conds = {}
        if args.selftest:
            for c, (bdir, s) in cond_src.items():
                a = load_npy(bdir / s / roi / "amplitudes_procrustes.npy")
                if a is not None and not (roi == 'V4' and a.shape[2] < 20):
                    conds[c] = a
        else:
            nf = load_npy(HC_C010 / subj / roi / "amplitudes_procrustes.npy")
            if nf is not None:
                conds['nofilter'] = nf
            for c in ['window', 'optimal']:
                a = load_npy(exp2_dir / subj / c / roi / "amplitudes_procrustes.npy")
                if a is not None:
                    conds[c] = a

        roi_res = {'k_srm': k, 'k_fe': K_FE, 'hc_n': len(hc_amps),
                   'n_voxels': int(hc_means[0].shape[1]),
                   'embeddings': {
                       'procrustes': {'hc_ref': {'dist_corr': r3(hc_ref_proc_corr)}, 'conditions': {}},
                       'srm': {'hc_ref': {'coords': r3(hc_ref_srm), 'dist_eucl': r3(pdist(hc_ref_srm)),
                                          'dist_corr': r3(corr_dist_rdm(hc_ref_srm))}, 'conditions': {}},
                       'fe_latent': {'hc_ref': {'coords': r3(hc_ref_fe), 'dist_eucl': r3(pdist(hc_ref_fe)),
                                                'dist_corr': r3(corr_dist_rdm(hc_ref_fe))}, 'conditions': {}}},
                   'loco': {}}
        for c, amp in conds.items():
            proc, srm_e, fe_e, loco = embed_condition(amp, srm)
            roi_res['embeddings']['procrustes']['conditions'][c] = {**proc,
                'n_runs': int(amp.shape[0]), 'n_voxels': int(amp.shape[2])}
            roi_res['embeddings']['srm']['conditions'][c] = srm_e
            roi_res['embeddings']['fe_latent']['conditions'][c] = fe_e
            roi_res['loco'][c] = loco
            print(f"  {c:9s} n_runs={amp.shape[0]} V={amp.shape[2]:4d} | "
                  f"adj={loco['adj_acc']:.3f} exact={loco['exact_acc']:.3f} | "
                  f"srmRDMd(corr) mean={np.mean(srm_e['dist_corr']):.3f} "
                  f"feRDMd mean={np.mean(fe_e['dist_corr']):.3f}")
        out['rois'][roi] = roi_res

    OUT.mkdir(parents=True, exist_ok=True)
    outp = OUT / f"exp2_embeddings_{tag}.json"
    outp.write_text(json.dumps(out, indent=1))
    print(f"\nSAVED {outp}")


if __name__ == "__main__":
    main()
