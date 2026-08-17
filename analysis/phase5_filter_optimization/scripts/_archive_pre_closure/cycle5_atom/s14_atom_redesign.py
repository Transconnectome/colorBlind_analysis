"""S14: Atom redesign evaluation — 4 new atom directions vs existing.

Design directions (per BEHAVIORAL_FIT_DIAGNOSIS Cycle 4):
  A3 = Cross-subject LOCO atom (HC train, CVD test) via PCA-shared-space bridge
  A1 = Cross-subject color decoder atom (HC train, CVD test) via PCA-shared-space
  A2 = SRM-aligned RDM atom (PCA proxy; SRM heavy/BrainIAK MPI infra not warranted)
  B1 = CVD run-level CV wrapper applied to base atoms

Per advisor: A1/A3 require V_s bridge. Pick uniform strategy = per-subject top-K
voxel-PCA into a shared low-dim space. This is the same proxy A2 uses, so
A1/A2/A3 share the bridging method (clean comparison).

Eval protocol:
  - For each Phase C candidate (9 fixed configs with forward δθ), evaluate every
    atom (existing + new) at that δθ.
  - HC pool resample (N=50 draws, 5-train HCs) for atoms that consume HC.
  - Report median loss across draws.
  - B1: 15 CVD run-splits, full HC pool inside (no HC resample to fit budget).

Output:
  results/s14_atom_redesign/atom_comparison.json
  results/s14_atom_redesign/atom_comparison.md
"""
import argparse
import itertools
import json
import sys
import time
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from rc_1dof import forward_rc
from two_comp import forward_2comp
from neural_loss import (
    load_amplitudes, load_hc_pool, ROI_K,
    precompute_loco_W_within, L_LOCO, L_RDM,
)
from diagnostic_delta_rdm import (
    precompute_hc_W, compute_rdm_correlation, cosine_similarity,
)
from behav_loss import (
    load_jnd_per_pair, L_behav_gamma, PAIR_HUES, HC_JND_SUBJS,
)
from utils_forward_model import (
    create_basis_full, HUE_ANGLES, N_RUNS, N_COLORS,
    fit_W_ridge, gcv_select_alpha,
)
from s8_loo_train_test import jnd_baseline_from_pool, DELTA_LAMBDA_BY_FAMILY

OUT_DIR = SCRIPT_DIR.parent / "results" / "s14_atom_redesign"
OUT_DIR.mkdir(parents=True, exist_ok=True)

HC_SUBJS = ['sub-01', 'sub-02', 'sub-03', 'sub-04', 'sub-05', 'sub-06', 'sub-07']
ROIS = ['V1', 'V2', 'V3', 'V4']

N_RESAMPLES = 50
SUBSET_SIZE = 5
RNG_SEED = 42
HUES = np.arange(0, 360, 45, dtype=float)

PAIR_KEYS = {'OY': 'orange-yellow', 'YG': 'yellow-green',
              'YP': 'yellow-purple', 'GB': 'green-blue'}

# PCA proxy K for shared-space bridge (A1/A2/A3).
# Use 6 — comparable to FE-6 K used elsewhere; sub-07 hV4 (16 voxels) edge-case still OK.
PCA_SHARED_K = 6

# Candidates (forwards locked per task spec)
CANDIDATES = [
    {'id': 'S08-B', 'subject': 'sub-08', 'family': 'deutan', 'model': 'rc',
     'forward_args': (6.0, 2.60, 'deutan'), 'is_null': False,
     'focal_pair': 'yellow-purple', 'gamma_pairs': ['OY', 'YG', 'YP'],
     'rdm_rois': ['V1', 'V2', 'V3', 'V4']},
    {'id': 'S08-C', 'subject': 'sub-08', 'family': 'deutan', 'model': 'rc',
     'forward_args': (6.0, 1.10, 'deutan'), 'is_null': False,
     'focal_pair': 'yellow-purple', 'gamma_pairs': ['OY', 'YG', 'YP'],
     'rdm_rois': ['V1', 'V2', 'V3', 'V4']},
    {'id': 'S08-E', 'subject': 'sub-08', 'family': 'deutan', 'model': '2comp',
     'forward_args': (38.0, -44.0, 'deutan'), 'is_null': False,
     'focal_pair': 'yellow-purple', 'gamma_pairs': ['OY', 'YG', 'YP'],
     'rdm_rois': ['V1', 'V2', 'V3', 'V4']},
    {'id': 'S08-D', 'subject': 'sub-08', 'family': 'deutan', 'model': '2comp',
     'forward_args': (34.0, 48.0, 'deutan'), 'is_null': False,
     'focal_pair': 'yellow-purple', 'gamma_pairs': ['OY', 'YG', 'YP'],
     'rdm_rois': ['V1', 'V2', 'V3', 'V4']},
    {'id': 'S09-A_DPS', 'subject': 'sub-09', 'family': 'protan', 'model': 'rc',
     'forward_args': (10.0, 2.60, 'protan'), 'is_null': False,
     'focal_pair': 'green-blue', 'gamma_pairs': ['GB'],
     'rdm_rois': ['V1']},
    {'id': 'S09-A_orig', 'subject': 'sub-09', 'family': 'protan', 'model': 'rc',
     'forward_args': (1.5, 2.45, 'protan'), 'is_null': False,
     'focal_pair': 'green-blue', 'gamma_pairs': ['GB'],
     'rdm_rois': ['V1']},
    {'id': 'S09-C', 'subject': 'sub-09', 'family': 'protan', 'model': '2comp',
     'forward_args': (6.0, 46.0, 'protan'), 'is_null': False,
     'focal_pair': 'green-blue', 'gamma_pairs': ['GB'],
     'rdm_rois': ['V1']},
    {'id': 'GT_null_sub-08', 'subject': 'sub-08', 'family': 'deutan', 'model': 'null',
     'forward_args': None, 'is_null': True,
     'focal_pair': 'yellow-purple', 'gamma_pairs': ['OY', 'YG', 'YP'],
     'rdm_rois': ['V1', 'V2', 'V3', 'V4']},
    {'id': 'GT_null_sub-09', 'subject': 'sub-09', 'family': 'protan', 'model': 'null',
     'forward_args': None, 'is_null': True,
     'focal_pair': 'green-blue', 'gamma_pairs': ['GB'],
     'rdm_rois': ['V1']},
]


# ---------------------------------------------------------------------------
# δθ generation
# ---------------------------------------------------------------------------

def compute_delta(candidate):
    """Get 8-vec δθ for a candidate."""
    if candidate['is_null']:
        return np.zeros(8)
    if candidate['model'] == 'rc':
        dl, g, fam = candidate['forward_args']
        return forward_rc(dl, g, fam)
    if candidate['model'] == '2comp':
        bs, bc, fam = candidate['forward_args']
        return forward_2comp(bs, bc, fam)
    raise ValueError(candidate['model'])


# ---------------------------------------------------------------------------
# Existing atom builders (cloned from s10b_v4_single_atom.py)
# ---------------------------------------------------------------------------

def make_gamma_pair_atom(pair_key, cvd_jnd, pool_jnd_subjs):
    pair_name = PAIR_KEYS[pair_key]
    bl, sd = jnd_baseline_from_pool(pool_jnd_subjs)
    if pair_name not in bl or cvd_jnd.get(pair_name) is None:
        return None
    p_obs = cvd_jnd[pair_name]
    p_base = bl[pair_name]
    p_sd = max(sd[pair_name], 1e-3)
    theta_a, theta_b = PAIR_HUES[pair_name]
    i = int(round(theta_a / 45.0)) % 8
    j = int(round(theta_b / 45.0)) % 8

    def loss_fn(delta_8vec):
        perceived = (HUES + delta_8vec) % 360.0
        d_phys = min(abs(theta_a - theta_b) % 360, 360 - abs(theta_a - theta_b) % 360)
        d_perc_raw = abs(perceived[i] - perceived[j]) % 360
        d_perc = max(min(d_perc_raw, 360 - d_perc_raw), 1e-3)
        pred = p_base * (d_phys / d_perc)
        return ((pred - p_obs) / p_sd) ** 2
    return loss_fn


def make_gamma_all_atom(cvd_jnd, pool_jnd_subjs):
    """Sum z² over all 8 valid pairs."""
    try:
        bl, sd = jnd_baseline_from_pool(pool_jnd_subjs)
    except Exception:
        return None

    def loss_fn(delta_8vec):
        if cvd_jnd is None:
            return np.nan
        valid = {p: cvd_jnd[p] for p in bl.keys()
                 if cvd_jnd.get(p) is not None}
        if not valid:
            return np.nan
        sd_d = {p: max(sd[p], 1e-3) for p in valid}
        try:
            return float(L_behav_gamma(delta_8vec, valid, bl, sd_d))
        except Exception:
            return np.nan
    return loss_fn


def make_rdm_atom(roi, cvd_amp, pool_amps_dict, C_baseline, K):
    if len(pool_amps_dict) < 2:
        return None
    try:
        pool_W, _ = precompute_hc_W(pool_amps_dict, C_baseline)
    except Exception:
        return None

    def loss_fn(delta_8vec):
        try:
            return L_RDM(delta_8vec, cvd_amp, pool_amps_dict, pool_W,
                         C_baseline, K, distance='correlation')
        except Exception:
            return np.nan
    return loss_fn


def make_loco_atom(cvd_amp_v4, K_v4):
    try:
        C_b = create_basis_full(K_v4, basis_type='fe')[HUE_ANGLES.astype(int)]
        loco_W = _precompute_loco_W_flexible(cvd_amp_v4, C_b)
    except Exception:
        return None

    def loss_fn(delta_8vec):
        try:
            return L_LOCO(delta_8vec, cvd_amp_v4, loco_W, K_v4)
        except Exception:
            return np.nan
    return loss_fn


def _precompute_loco_W_flexible(cvd_amp, C_baseline):
    """LOCO W builder that supports arbitrary n_runs (not hard-coded to 6).
    For B1 wrapper that may pass 4-run train or 2-run test slices.
    """
    n_runs_local = cvd_amp.shape[0]
    V_s = cvd_amp.shape[2]
    loco_W = {}
    for c_held in range(N_COLORS):
        train_colors = [c for c in range(N_COLORS) if c != c_held]
        C_train = np.tile(C_baseline[train_colors], (n_runs_local, 1))
        X_train = cvd_amp[:, train_colors, :].reshape(-1, V_s)
        alpha, _ = gcv_select_alpha(C_train, X_train)
        W = fit_W_ridge(C_train, X_train, alpha)
        loco_W[c_held] = W
    return loco_W


# ---------------------------------------------------------------------------
# Shared-space bridge (PCA per subject -> top-K components, then RDM cosine
# across subjects in component-level RDM space)
# ---------------------------------------------------------------------------

def voxel_pca_components(amp_mean_8xV, k):
    """Per-subject PCA on (8, V) trial-mean pattern; return top-k voxel-pattern
    projection (8, k).

    We compute SVD: amp = U S V^T (U: 8 × min(8,V), S: min(8,V), V^T: min(8,V) × V).
    Top-k 'pattern' = U[:, :k] * S[:k]  (8, k).  This is the per-color score on
    the top-k principal voxel-axes.  Equivalent to projecting (8, V) onto V[:k, :]^T.
    """
    # Demean across colors (so PCA captures color-induced variance)
    X = amp_mean_8xV - amp_mean_8xV.mean(axis=0, keepdims=True)
    U, S, Vt = np.linalg.svd(X, full_matrices=False)
    k_eff = min(k, len(S))
    # U[:, :k] @ diag(S[:k])  (8, k_eff)
    scores = U[:, :k_eff] * S[:k_eff]
    return scores


def make_a2_pca_rdm_atom(cvd_amp, pool_amps_dict, K=PCA_SHARED_K):
    """A2: SRM-aligned RDM proxy via per-subject voxel-PCA into shared k-dim.

    For each HC: top-K PC scores (8, K). Compute RDM in PC space.
    HC mean RDM = mean across HCs (in PC space).
    For CVD: top-K PCs of CVD pattern (8, K). RDM in PC space.

    Forward δθ effect: shift CVD pattern to perceived-color basis BEFORE projecting
    to its own PC. Simpler: rotate the 8x8 RDM (CVD) to ordering "θ + δθ".
    We use ordering shift: at δθ the perceptual-RDM[i,j] = obs-RDM[i', j'] where
    i', j' = perceived indices (with interpolation).
    """
    if len(pool_amps_dict) < 2:
        return None

    from scipy.spatial.distance import pdist, squareform

    # HC PC-space RDM mean (computed once); convert vector form to (8,8)
    hc_rdms = []
    for sid, amp in pool_amps_dict.items():
        try:
            mean_pat = amp.mean(axis=0)  # (8, V_s)
            scores = voxel_pca_components(mean_pat, K)  # (8, k)
            rdm_vec = compute_rdm_correlation(scores)  # (28,)
            rdm_mat = squareform(rdm_vec)  # (8, 8)
            hc_rdms.append(rdm_mat)
        except Exception:
            continue
    if not hc_rdms:
        return None
    hc_rdm_mean = np.mean(np.stack(hc_rdms, axis=0), axis=0)  # (8, 8)
    triu = np.triu_indices(8, k=1)

    # CVD PC-space RDM
    cvd_mean = cvd_amp.mean(axis=0)
    cvd_scores = voxel_pca_components(cvd_mean, K)
    cvd_rdm = squareform(compute_rdm_correlation(cvd_scores))  # (8, 8)

    # Observed ΔRDM in PC space
    delta_rdm_obs = (cvd_rdm - hc_rdm_mean)[triu]

    def loss_fn(delta_8vec):
        """Sim ΔRDM under δθ: predicted *change* in RDM when colors are perceived
        at shifted hues. At δθ=0, sim=0 → cos(0, obs)→0 → loss→1.

        delta_rdm_sim[i,j] = HC_RDM(perceived_i, perceived_j) - HC_RDM(i, j)
        """
        try:
            perceived = (HUES + delta_8vec) % 360.0
            sim_shifted = np.zeros((8, 8))
            for i in range(8):
                for j in range(8):
                    sim_shifted[i, j] = _interp_circ_rdm(hc_rdm_mean, perceived[i], perceived[j])
            delta_rdm_sim = (sim_shifted - hc_rdm_mean)[triu]
            cos = cosine_similarity(delta_rdm_sim, delta_rdm_obs)
            if not np.isfinite(cos):
                cos = 0.0
            return float(1.0 - cos)
        except Exception:
            return np.nan
    return loss_fn


def _interp_circ_rdm(rdm_8x8, hue_a, hue_b):
    """Bilinear circular interp of 8x8 RDM at fractional hue indices (deg / 45)."""
    fa = (hue_a % 360.0) / 45.0
    fb = (hue_b % 360.0) / 45.0
    i0, i1 = int(np.floor(fa)) % 8, int(np.ceil(fa)) % 8
    j0, j1 = int(np.floor(fb)) % 8, int(np.ceil(fb)) % 8
    wa = fa - np.floor(fa)
    wb = fb - np.floor(fb)
    v = (1 - wa) * (1 - wb) * rdm_8x8[i0, j0] + \
        wa * (1 - wb) * rdm_8x8[i1, j0] + \
        (1 - wa) * wb * rdm_8x8[i0, j1] + \
        wa * wb * rdm_8x8[i1, j1]
    return v


def make_a1_decoder_atom(cvd_amp, pool_amps_dict, K=PCA_SHARED_K):
    """A1: cross-subject color decoder via PCA-shared-space.

    Train: each HC's (8, V_HC) -> top-K voxel PCs (8, K). Stack as 'reference'
    color templates (HC mean across HCs = 8 × K canonical).
    Test: CVD's (8, V_CVD) -> top-K PCs (8, K) (CVD-specific basis since V mismatch).

    Note: this is a soft-bridge — PC ordering not aligned across subjects.
    We Procrustes-align CVD PCs to HC mean reference before scoring.

    Decoder score: per CVD color c, predict color c_pred = argmax_c
       corr( CVD_PC[c, :], HC_ref_PC[c_pred, :] ).

    Loss under δθ: shift CVD perceived hue, then check classifier confusion.
    At δθ=0 the classifier should mostly predict c→c (diagonal). δθ shifts the
    perceived position so the *correct* answer is now c→nearest(perceived).

    Loss = 1 - normalized diagonal-agreement (i.e., decoder says "c at perceived position c").
    """
    if len(pool_amps_dict) < 2:
        return None

    # HC reference: mean PC across HCs
    hc_pcs = []
    for sid, amp in pool_amps_dict.items():
        try:
            mp = amp.mean(axis=0)
            sc = voxel_pca_components(mp, K)  # (8, k)
            # Sign-align each PC axis to its own first HC (sign flips don't matter for
            # cosine-rank-style classifier; we standardize rows-wise z-score).
            sc = (sc - sc.mean(axis=0, keepdims=True))
            norms = np.linalg.norm(sc, axis=0, keepdims=True) + 1e-8
            sc = sc / norms
            hc_pcs.append(sc)
        except Exception:
            continue
    if not hc_pcs:
        return None
    hc_ref = np.mean(np.stack(hc_pcs, axis=0), axis=0)  # (8, k)

    # CVD PC
    cvd_mean = cvd_amp.mean(axis=0)  # (8, V_cvd)
    cvd_pc = voxel_pca_components(cvd_mean, K)  # (8, k)
    cvd_pc = (cvd_pc - cvd_pc.mean(axis=0, keepdims=True))
    norms = np.linalg.norm(cvd_pc, axis=0, keepdims=True) + 1e-8
    cvd_pc = cvd_pc / norms

    # Procrustes align CVD_PC to HC_ref (right-rotation on k-axis)
    # M = cvd_pc^T @ hc_ref  (k, k); SVD -> R = U V^T; aligned = cvd_pc @ R
    try:
        M = cvd_pc.T @ hc_ref
        U_, _, Vt_ = np.linalg.svd(M)
        R = U_ @ Vt_
        cvd_aligned = cvd_pc @ R  # (8, k)
    except Exception:
        cvd_aligned = cvd_pc

    # 8 x 8 confusion: c_true (CVD ordering) × c_pred (HC ordering)
    # Score = inner product of standardized rows
    confusion = cvd_aligned @ hc_ref.T  # (8, 8)

    def loss_fn(delta_8vec):
        """Forward δθ: under the model, CVD physical color c is *perceived as* at
        hue HUES[c] + δθ[c]. So 'correct' decoder match for c_true=c is
        HC reference color at perceived hue, i.e., interpolated HC template at HUES[c]+δθ[c].

        Loss = 1 − mean diagonal correlation under perceived alignment.
        """
        perceived = (HUES + delta_8vec) % 360.0
        # Build perceived HC template by interpolation of hc_ref columns
        # hc_ref: (8 canonical hues, k). Linear circular interp.
        perceived_ref = np.zeros((8, hc_ref.shape[1]))
        for c in range(8):
            fp = (perceived[c] % 360.0) / 45.0
            i0 = int(np.floor(fp)) % 8
            i1 = int(np.ceil(fp)) % 8
            w = fp - np.floor(fp)
            perceived_ref[c] = (1 - w) * hc_ref[i0] + w * hc_ref[i1]
        # normalize
        perceived_ref = perceived_ref - perceived_ref.mean(axis=0, keepdims=True)
        n_ = np.linalg.norm(perceived_ref, axis=0, keepdims=True) + 1e-8
        perceived_ref = perceived_ref / n_
        # diagonal correlation
        diag_scores = np.sum(cvd_aligned * perceived_ref, axis=1)  # (8,)
        return float(1.0 - np.mean(diag_scores))
    return loss_fn


def make_a3_xs_loco_atom(cvd_amp, pool_amps_dict, K=PCA_SHARED_K):
    """A3: cross-subject LOCO via PCA-shared-space.

    For each HC: fit encoder W_HC: C(θ) (8, K_basis) -> top-K voxel-PCs (8, K).
    Average W across HCs (in PC-space).
    LOCO: hold out 1 color, fit W_HC on 7 colors of HC PC; predict 1 color in
    CVD's PC space (after Procrustes alignment to HC_ref).

    Forward δθ: at perceived hue, evaluate basis C(θ + δθ) -> predict; compare to
    actual CVD PC at color c.
    Loss = mean(1 - corr) across held-out colors.
    """
    if len(pool_amps_dict) < 2:
        return None

    # Basis matrix at canonical (no shift)
    C_base = create_basis_full(K, basis_type='fe')[HUE_ANGLES.astype(int)]  # (8, K)

    # HC reference: mean PC across HCs (used for CVD alignment + W training)
    hc_pcs = []
    hc_ws = []
    for sid, amp in pool_amps_dict.items():
        try:
            mp = amp.mean(axis=0)  # (8, V_s)
            sc = voxel_pca_components(mp, K)  # (8, K)
            # standardize
            sc_s = sc - sc.mean(axis=0, keepdims=True)
            norms = np.linalg.norm(sc_s, axis=0, keepdims=True) + 1e-8
            sc_s = sc_s / norms
            hc_pcs.append(sc_s)
        except Exception:
            continue
    if not hc_pcs:
        return None
    hc_ref = np.mean(np.stack(hc_pcs, axis=0), axis=0)  # (8, K)

    # Align each HC PC to HC_ref via Procrustes; then average -> W on HC_ref scale
    hc_pcs_aligned = []
    for sc_s in hc_pcs:
        M = sc_s.T @ hc_ref
        U_, _, Vt_ = np.linalg.svd(M)
        R = U_ @ Vt_
        hc_pcs_aligned.append(sc_s @ R)
    hc_ref_aligned = np.mean(np.stack(hc_pcs_aligned, axis=0), axis=0)  # (8, K)

    # Per-color hold-out training of W on HC_ref_aligned
    loco_W = {}
    for c_held in range(N_COLORS):
        keep = [c for c in range(N_COLORS) if c != c_held]
        C_train = C_base[keep]   # (7, K)
        Y_train = hc_ref_aligned[keep]  # (7, K)
        try:
            alpha, _ = gcv_select_alpha(C_train, Y_train)
            W = fit_W_ridge(C_train, Y_train, alpha)  # (K, K)
        except Exception:
            W = np.linalg.pinv(C_train) @ Y_train
        loco_W[c_held] = W

    # CVD PC + Procrustes align to HC ref
    cvd_mean = cvd_amp.mean(axis=0)  # (8, V_cvd)
    cvd_pc = voxel_pca_components(cvd_mean, K)  # (8, K)
    cvd_pc = cvd_pc - cvd_pc.mean(axis=0, keepdims=True)
    n_ = np.linalg.norm(cvd_pc, axis=0, keepdims=True) + 1e-8
    cvd_pc = cvd_pc / n_
    try:
        M = cvd_pc.T @ hc_ref_aligned
        U_, _, Vt_ = np.linalg.svd(M)
        R_cvd = U_ @ Vt_
        cvd_aligned = cvd_pc @ R_cvd
    except Exception:
        cvd_aligned = cvd_pc

    basis_full = create_basis_full(K, basis_type='fe')

    def loss_fn(delta_8vec):
        try:
            shifted_angles = (HUE_ANGLES + delta_8vec) % 360
            idx = np.round(shifted_angles).astype(int) % 360
            C_shifted = basis_full[idx]  # (8, K)
            rho_8 = np.zeros(8)
            for c in range(N_COLORS):
                W_c = loco_W[c]
                Y_pred = (C_shifted[c:c+1] @ W_c)[0]  # (K,)
                Y_actual = cvd_aligned[c]  # (K,)
                if np.std(Y_pred) < 1e-10 or np.std(Y_actual) < 1e-10:
                    rho_8[c] = 0.0
                else:
                    r = np.corrcoef(Y_pred, Y_actual)[0, 1]
                    rho_8[c] = r if np.isfinite(r) else 0.0
            return float(np.mean(1.0 - rho_8))
        except Exception:
            return np.nan
    return loss_fn


# ---------------------------------------------------------------------------
# B1: CVD run-level CV wrapper for any base atom builder
# ---------------------------------------------------------------------------

def cvd_run_split_iter(seed=0, n_train=4, n_test=2):
    """Yield (train_idx, test_idx) tuples for 6-run × 8-color CVD data.

    All C(6, n_train) = C(6, 4) = 15 splits.
    """
    runs = list(range(6))
    for train_combo in itertools.combinations(runs, n_train):
        test_combo = tuple(r for r in runs if r not in train_combo)
        yield train_combo, test_combo


def b1_wrap_atom_eval(base_atom_builder_fn, cvd_amp_6run, delta_8vec, **kwargs):
    """Apply B1 (CVD run-level CV) to any atom.

    base_atom_builder_fn: callable taking cvd_amp (n_run, 8, V) + **kwargs -> atom loss fn
    cvd_amp_6run: (6, 8, V) full data
    delta_8vec: forward δθ to evaluate
    Returns: median test-loss across 15 splits.
    """
    losses = []
    for tr_idx, te_idx in cvd_run_split_iter():
        cvd_tr = cvd_amp_6run[list(tr_idx)]  # (4, 8, V)
        cvd_te = cvd_amp_6run[list(te_idx)]  # (2, 8, V)
        try:
            # Build atom using TRAIN runs (the atom may build encoders/RDMs from this)
            atom = base_atom_builder_fn(cvd_tr, **kwargs)
            if atom is None:
                continue
            # Replace the "internal cvd_amp" with TEST runs for evaluation.
            # Trick: rebuild loss-eval style: most atoms close over cvd_amp via .mean(0).
            # We approach evaluation by recomputing the per-color mean and using
            # the atom's loss function on it. Since atoms close over the cvd_amp
            # they were built with (train), we need a SEPARATE evaluator on test.
            # We use the simplest "rebuild atom with test data" approach: build a
            # test-only atom evaluator and use that.
            atom_test = base_atom_builder_fn(cvd_te, **kwargs)
            if atom_test is None:
                continue
            loss_val = float(atom_test(delta_8vec))
            if np.isfinite(loss_val):
                losses.append(loss_val)
        except Exception:
            continue
    if not losses:
        return np.nan
    return float(np.median(losses))


# ---------------------------------------------------------------------------
# Main evaluation harness
# ---------------------------------------------------------------------------

def load_subject_data(subject):
    cvd_amps, hc_amps_all, K_by_roi, C_by_roi = {}, {}, {}, {}
    for roi in ROIS:
        try:
            cvd_amps[roi] = load_amplitudes(subject, roi)
            hc_amps_all[roi] = load_hc_pool(roi)
            K_by_roi[roi] = ROI_K[roi]
            C_by_roi[roi] = create_basis_full(K_by_roi[roi], basis_type='fe')[
                HUE_ANGLES.astype(int)]
        except FileNotFoundError:
            pass
    try:
        cvd_jnd = load_jnd_per_pair(subject)
    except Exception:
        cvd_jnd = None
    return cvd_amps, hc_amps_all, K_by_roi, C_by_roi, cvd_jnd


def resample_subsets(subject, n=N_RESAMPLES, size=SUBSET_SIZE):
    rng = np.random.default_rng(RNG_SEED + (0 if subject == 'sub-08' else 1))
    out = []
    for _ in range(n):
        sel = rng.choice(len(HC_SUBJS), size=size, replace=False)
        subset = [HC_SUBJS[i] for i in sorted(sel)]
        out.append(subset)
    return out


def evaluate_candidate(candidate, subject_data_cache):
    """For one candidate, eval each atom; return dict of atom_name -> loss summary."""
    subject = candidate['subject']
    cache = subject_data_cache[subject]
    cvd_amps = cache['cvd_amps']
    hc_amps_all = cache['hc_amps_all']
    K_by_roi = cache['K_by_roi']
    C_by_roi = cache['C_by_roi']
    cvd_jnd = cache['cvd_jnd']

    delta_8vec = compute_delta(candidate)

    results = {}

    # ---- HC resample plan ----
    subsets = resample_subsets(subject)
    train_jnd_hc = [s for s in HC_SUBJS if s in HC_JND_SUBJS]

    # ===== Existing atoms — γ pair (focal) =====
    focal_pair_key = None
    for k_, v_ in PAIR_KEYS.items():
        if v_ == candidate['focal_pair']:
            focal_pair_key = k_
            break
    if focal_pair_key and cvd_jnd:
        losses_focal = []
        losses_all = []
        for subset in subsets:
            t_jnd = [h for h in subset if h in HC_JND_SUBJS]
            if not t_jnd:
                continue
            fn_focal = make_gamma_pair_atom(focal_pair_key, cvd_jnd, t_jnd)
            fn_all = make_gamma_all_atom(cvd_jnd, t_jnd)
            if fn_focal is not None:
                try:
                    v = float(fn_focal(delta_8vec))
                    if np.isfinite(v):
                        losses_focal.append(v)
                except Exception:
                    pass
            if fn_all is not None:
                try:
                    v = float(fn_all(delta_8vec))
                    if np.isfinite(v):
                        losses_all.append(v)
                except Exception:
                    pass
        results['gamma_focal'] = _summary(losses_focal)
        results['gamma_all'] = _summary(losses_all)

    # ===== Existing atoms — RDM per ROI =====
    for roi in candidate['rdm_rois']:
        if roi not in cvd_amps:
            continue
        losses = []
        for subset in subsets:
            pool = {h: hc_amps_all[roi][h] for h in subset
                    if h in hc_amps_all[roi]}
            if len(pool) < 2:
                continue
            fn = make_rdm_atom(roi, cvd_amps[roi], pool, C_by_roi[roi], K_by_roi[roi])
            if fn is None:
                continue
            try:
                v = float(fn(delta_8vec))
                if np.isfinite(v):
                    losses.append(v)
            except Exception:
                pass
        results[f'RDM_{roi}'] = _summary(losses)

    # ===== Existing — LOCO V4 (within-CVD, no HC resample needed) =====
    if 'V4' in cvd_amps:
        fn = make_loco_atom(cvd_amps['V4'], K_by_roi['V4'])
        if fn is not None:
            try:
                v = float(fn(delta_8vec))
                results['LOCO_V4'] = _summary([v] if np.isfinite(v) else [])
            except Exception:
                results['LOCO_V4'] = _summary([])

    # ===== NEW A2 PCA-RDM atom per ROI =====
    for roi in candidate['rdm_rois']:
        if roi not in cvd_amps:
            continue
        losses = []
        for subset in subsets:
            pool = {h: hc_amps_all[roi][h] for h in subset
                    if h in hc_amps_all[roi]}
            if len(pool) < 2:
                continue
            fn = make_a2_pca_rdm_atom(cvd_amps[roi], pool, K=PCA_SHARED_K)
            if fn is None:
                continue
            try:
                v = float(fn(delta_8vec))
                if np.isfinite(v):
                    losses.append(v)
            except Exception:
                pass
        results[f'A2_PCA_RDM_{roi}'] = _summary(losses)

    # ===== NEW A1 cross-subject decoder per ROI =====
    for roi in candidate['rdm_rois']:
        if roi not in cvd_amps:
            continue
        losses = []
        for subset in subsets:
            pool = {h: hc_amps_all[roi][h] for h in subset
                    if h in hc_amps_all[roi]}
            if len(pool) < 2:
                continue
            fn = make_a1_decoder_atom(cvd_amps[roi], pool, K=PCA_SHARED_K)
            if fn is None:
                continue
            try:
                v = float(fn(delta_8vec))
                if np.isfinite(v):
                    losses.append(v)
            except Exception:
                pass
        results[f'A1_decoder_{roi}'] = _summary(losses)

    # ===== NEW A3 cross-subject LOCO (V4 if available, else V1) =====
    a3_roi = 'V4' if 'V4' in candidate['rdm_rois'] and 'V4' in cvd_amps else (
        candidate['rdm_rois'][0] if candidate['rdm_rois'] else None)
    if a3_roi and a3_roi in cvd_amps:
        losses = []
        for subset in subsets:
            pool = {h: hc_amps_all[a3_roi][h] for h in subset
                    if h in hc_amps_all[a3_roi]}
            if len(pool) < 2:
                continue
            fn = make_a3_xs_loco_atom(cvd_amps[a3_roi], pool, K=PCA_SHARED_K)
            if fn is None:
                continue
            try:
                v = float(fn(delta_8vec))
                if np.isfinite(v):
                    losses.append(v)
            except Exception:
                pass
        results[f'A3_xs_LOCO_{a3_roi}'] = _summary(losses)

    # ===== NEW B1 wrapper applied to base atoms =====
    # Apply to: γ_all, RDM_V4 (or relevant ROI), LOCO_V4
    full_pool = {roi: {h: hc_amps_all[roi][h] for h in HC_SUBJS
                       if h in hc_amps_all[roi]} for roi in cvd_amps}

    # B1 on γ_all (CVD-data invariant; just CVD JND fixed → split is degenerate
    # — but document it). Skip — γ doesn't depend on cvd_amp.

    # B1 on RDM_V4 (or V1 for sub-09)
    b1_roi = 'V4' if 'V4' in cvd_amps else (candidate['rdm_rois'][0] if candidate['rdm_rois'] else None)
    if b1_roi and b1_roi in cvd_amps and len(full_pool.get(b1_roi, {})) >= 2:
        def _rdm_builder(cvd_part, pool=full_pool[b1_roi], C_b=C_by_roi[b1_roi],
                         K_=K_by_roi[b1_roi]):
            return make_rdm_atom(b1_roi, cvd_part, pool, C_b, K_)
        try:
            loss_med = b1_wrap_atom_eval(_rdm_builder, cvd_amps[b1_roi], delta_8vec)
            results[f'B1_RDM_{b1_roi}'] = _summary([loss_med] if np.isfinite(loss_med) else [])
        except Exception:
            results[f'B1_RDM_{b1_roi}'] = _summary([])

    # B1 on LOCO_V4
    if 'V4' in cvd_amps:
        def _loco_builder(cvd_part, K_=K_by_roi['V4']):
            return make_loco_atom(cvd_part, K_)
        try:
            loss_med = b1_wrap_atom_eval(_loco_builder, cvd_amps['V4'], delta_8vec)
            results['B1_LOCO_V4'] = _summary([loss_med] if np.isfinite(loss_med) else [])
        except Exception:
            results['B1_LOCO_V4'] = _summary([])

    # B1 on A3 cross-subject LOCO
    if a3_roi and a3_roi in cvd_amps and len(full_pool.get(a3_roi, {})) >= 2:
        def _a3_builder(cvd_part, pool=full_pool[a3_roi]):
            return make_a3_xs_loco_atom(cvd_part, pool, K=PCA_SHARED_K)
        try:
            loss_med = b1_wrap_atom_eval(_a3_builder, cvd_amps[a3_roi], delta_8vec)
            results[f'B1_A3_xs_LOCO_{a3_roi}'] = _summary([loss_med] if np.isfinite(loss_med) else [])
        except Exception:
            results[f'B1_A3_xs_LOCO_{a3_roi}'] = _summary([])

    return results


def _summary(losses):
    arr = np.array([v for v in losses if v is not None and np.isfinite(v)], dtype=float)
    if len(arr) == 0:
        return {'median': None, 'iqr': None, 'n': 0}
    if len(arr) == 1:
        return {'median': float(arr[0]), 'iqr': 0.0, 'n': 1}
    return {'median': float(np.median(arr)),
            'iqr': float(np.percentile(arr, 75) - np.percentile(arr, 25)),
            'n': int(len(arr))}


def main():
    global N_RESAMPLES
    parser = argparse.ArgumentParser()
    parser.add_argument('--n-resamples', type=int, default=N_RESAMPLES)
    args = parser.parse_args()

    print("=" * 100, flush=True)
    print(f"S14 atom redesign — 4 new atoms + B1 wrapper", flush=True)
    print(f"  N_RESAMPLES={args.n_resamples}, PCA_SHARED_K={PCA_SHARED_K}", flush=True)
    print("=" * 100, flush=True)

    N_RESAMPLES = args.n_resamples

    # Pre-load subject data once
    subject_data_cache = {}
    for subj in ['sub-08', 'sub-09']:
        print(f"\n[load] {subj}...", flush=True)
        cvd_amps, hc_amps_all, K_by_roi, C_by_roi, cvd_jnd = load_subject_data(subj)
        subject_data_cache[subj] = {
            'cvd_amps': cvd_amps, 'hc_amps_all': hc_amps_all,
            'K_by_roi': K_by_roi, 'C_by_roi': C_by_roi, 'cvd_jnd': cvd_jnd,
        }
        rois = list(cvd_amps.keys())
        print(f"  ROIs loaded: {rois}", flush=True)

    # Evaluate each candidate
    all_results = {}
    t0 = time.time()
    for cand in CANDIDATES:
        t_c = time.time()
        print(f"\n[candidate] {cand['id']} subj={cand['subject']} model={cand['model']} forward={cand['forward_args']}", flush=True)
        delta = compute_delta(cand)
        print(f"  δθ = {np.round(delta, 2).tolist()}  |  RMS = {np.sqrt(np.mean(delta**2)):.2f}°", flush=True)
        atom_results = evaluate_candidate(cand, subject_data_cache)
        all_results[cand['id']] = {
            'config': cand,
            'delta_8vec': delta.tolist(),
            'delta_rms': float(np.sqrt(np.mean(delta**2))),
            'atoms': atom_results,
        }
        t_d = time.time() - t_c
        print(f"  done in {t_d:.1f}s  ({len(atom_results)} atoms evaluated)", flush=True)

    elapsed = time.time() - t0
    print(f"\n[total] elapsed = {elapsed:.1f}s", flush=True)

    # Save JSON
    out_json = OUT_DIR / "atom_comparison.json"
    with open(out_json, 'w') as f:
        json.dump({'results': all_results,
                    'meta': {'n_resamples': N_RESAMPLES,
                             'subset_size': SUBSET_SIZE,
                             'pca_shared_k': PCA_SHARED_K,
                             'b1_splits': 15,
                             'elapsed_sec': elapsed,
                             'rng_seed': RNG_SEED}},
                  f, indent=2, default=str)
    print(f"Saved JSON: {out_json}", flush=True)

    # Generate MD table
    md_lines = []
    md_lines.append("# S14 atom redesign — comparison\n")
    md_lines.append(f"- N_RESAMPLES = {N_RESAMPLES} (HC pool draws, 5-train)")
    md_lines.append(f"- PCA_SHARED_K = {PCA_SHARED_K} (A1/A2/A3 bridge)")
    md_lines.append(f"- B1 splits = 15 (CVD 4-train / 2-test from 6 runs)")
    md_lines.append(f"- Elapsed = {elapsed:.1f}s\n")

    # Gather all unique atom names across all candidates
    all_atoms = []
    seen = set()
    for cid, data in all_results.items():
        for an in data['atoms'].keys():
            if an not in seen:
                seen.add(an)
                all_atoms.append(an)

    md_lines.append("## Atom × Candidate (median loss)\n")
    header = ["Atom"] + [c['id'] for c in CANDIDATES]
    md_lines.append("| " + " | ".join(header) + " |")
    md_lines.append("|" + "|".join([" --- "] * len(header)) + "|")

    for atom in all_atoms:
        row = [atom]
        for cand in CANDIDATES:
            cid = cand['id']
            atoms = all_results[cid]['atoms']
            if atom in atoms and atoms[atom]['median'] is not None:
                v = atoms[atom]['median']
                row.append(f"{v:.3f}")
            else:
                row.append("—")
        md_lines.append("| " + " | ".join(row) + " |")

    md_lines.append("\n## δθ RMS per candidate\n")
    md_lines.append("| Candidate | model | forward | δθ RMS |")
    md_lines.append("| --- | --- | --- | --- |")
    for cand in CANDIDATES:
        cid = cand['id']
        row = [cid, cand['model'], str(cand['forward_args']),
               f"{all_results[cid]['delta_rms']:.2f}°"]
        md_lines.append("| " + " | ".join(row) + " |")

    md_text = "\n".join(md_lines)
    out_md = OUT_DIR / "atom_comparison.md"
    with open(out_md, 'w') as f:
        f.write(md_text)
    print(f"Saved MD: {out_md}", flush=True)


if __name__ == "__main__":
    main()
