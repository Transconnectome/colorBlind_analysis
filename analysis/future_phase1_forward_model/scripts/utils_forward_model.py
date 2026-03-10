#!/usr/bin/env python3
"""
utils_forward_model.py — Shared utilities for the Group-Prior Prediction Model.

Constants, data loading, basis functions, fitting, decoding, and metrics.

Convention: W in R^{K x V_s} (channels x voxels), matching existing loco_ridge.py.
"""

import numpy as np
import json
from pathlib import Path
from datetime import datetime

# ============================================================================
# Constants
# ============================================================================

HC_SUBJECTS = [f'{i:02d}' for i in range(1, 8)]   # sub-01..sub-07
CVD_SUBJECTS = [f'{i:02d}' for i in range(8, 11)]  # sub-08..sub-10
ALL_SUBJECTS = HC_SUBJECTS + CVD_SUBJECTS

ROIS = ['V1', 'V2', 'V3', 'V4']
ROI_DIR_MAP = {'hV4': 'V4'}  # hV4 -> V4 on disk

K_VALUES = {'V1': 4, 'V2': 4, 'V3': 3, 'V4': 3}

HUE_ANGLES = np.array([0, 45, 90, 135, 180, 225, 270, 315])
N_RUNS = 6
N_COLORS = 8
N_CHANNELS = 6

LAMBDA_GRID = [0, 0.01, 0.1, 1, 10, 100, 1000]
ALPHA_GRID = [0.001, 0.01, 0.1, 1.0, 10.0, 100.0, 1000.0]

# Default data path (server)
DEFAULT_BASELINE_DIR = Path(
    '/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010'
)

# ============================================================================
# Data Loading
# ============================================================================

def load_amplitudes(baseline_dir, subject, roi):
    """Load Procrustes-aligned amplitudes.

    Args:
        baseline_dir: Path to full_dataset_C010
        subject: Subject ID (e.g., '01')
        roi: ROI name (e.g., 'V1', 'V2', 'V3', 'V4')

    Returns:
        amp: (N_RUNS, N_COLORS, V_s) ndarray
    """
    roi_dir = ROI_DIR_MAP.get(roi, roi)
    path = Path(baseline_dir) / f'sub-{subject}' / roi_dir / 'amplitudes_procrustes.npy'
    if not path.exists():
        raise FileNotFoundError(f'Amplitudes not found: {path}')
    return np.load(path)  # (6, 8, V_s)


# ============================================================================
# Basis Functions (Brouwer & Heeger 2009)
# ============================================================================

def create_basis_full(n_channels=N_CHANNELS, basis_type='fe'):
    """Create full 360-degree basis functions.

    Args:
        n_channels: number of basis channels
        basis_type: 'fe' (half-wave rectified cos^2) or 'lf' (Fourier harmonics)

    Returns:
        basis: (360, n_channels)
    """
    if basis_type == 'fe':
        centers = np.linspace(0, 360, n_channels, endpoint=False)
        hues = np.arange(360)
        basis = np.zeros((360, n_channels))
        for i, c in enumerate(centers):
            dist = np.abs(hues - c)
            dist = np.minimum(dist, 360 - dist)
            resp = np.cos(np.deg2rad(dist))
            basis[:, i] = np.where(resp > 0, resp ** 2, 0.0)
        return basis
    elif basis_type == 'lf':
        if n_channels % 2 != 0:
            raise ValueError(f'LF basis requires even n_channels, got {n_channels}')
        n_harmonics = n_channels // 2
        hues_rad = np.deg2rad(np.arange(360))
        basis = np.zeros((360, n_channels))
        for k in range(n_harmonics):
            basis[:, 2 * k] = np.cos((k + 1) * hues_rad)
            basis[:, 2 * k + 1] = np.sin((k + 1) * hues_rad)
        return basis
    else:
        raise ValueError(f'Unknown basis_type: {basis_type}')


def create_basis_matrix(hue_angles=HUE_ANGLES, n_channels=N_CHANNELS,
                        basis_type='fe'):
    """Design matrix for given hue angles.

    Args:
        hue_angles: (n,) array of hue angles in degrees
        n_channels: number of basis channels
        basis_type: 'fe' or 'lf'

    Returns:
        C: (n, K) design matrix
    """
    basis_full = create_basis_full(n_channels, basis_type=basis_type)
    return basis_full[np.asarray(hue_angles, dtype=int)]


# ============================================================================
# Weight Fitting
# ============================================================================

def fit_W_ols(C, X):
    """OLS encoding weights.

    W = pinv(C) @ X

    Args:
        C: (n, K) design matrix
        X: (n, V_s) voxel patterns

    Returns:
        W: (K, V_s)
    """
    return np.linalg.pinv(C) @ X


def fit_W_ridge(C, X, alpha):
    """Ridge-regularised encoding weights.

    W = (C'C + alpha*I)^{-1} C' X

    Args:
        C: (n, K) design matrix
        X: (n, V_s) voxel patterns
        alpha: ridge penalty

    Returns:
        W: (K, V_s)
    """
    K = C.shape[1]
    return np.linalg.solve(C.T @ C + alpha * np.eye(K), C.T @ X)


def fit_W_prior_ridge(C, X, W0, lam):
    """Prior-centred ridge: minimise ||X - C@W||^2 + lam*||W - W0||^2.

    Closed form: W = (C'C + lam*I)^{-1} (C'X + lam*W0)

    Args:
        C: (n, K) design matrix
        X: (n, V_s) voxel patterns
        W0: (K, V_s) prior weight matrix
        lam: prior penalty (0 = OLS, inf = prior-only)

    Returns:
        W: (K, V_s)
    """
    K = C.shape[1]
    return np.linalg.solve(C.T @ C + lam * np.eye(K), C.T @ X + lam * W0)


def fit_W_ridge_rrr(C, X, alpha, rank):
    """Ridge + Reduced-Rank (SVD truncation).

    Args:
        C: (n, K) design matrix
        X: (n, V_s) voxel patterns
        alpha: ridge penalty
        rank: target rank for W (must be <= K)

    Returns:
        W: (K, V_s) rank-r approximation of ridge solution
    """
    W_full = fit_W_ridge(C, X, alpha)
    U, s, Vt = np.linalg.svd(W_full, full_matrices=False)
    r = min(rank, len(s))
    return (U[:, :r] * s[:r][np.newaxis, :]) @ Vt[:r, :]


def fit_W_smooth_ridge(C, X, alpha, beta):
    """Ridge with circular channel-smoothness penalty.

    min_W ||X - C@W||^2 + alpha*||W||^2 + beta*||D@W||^2
    where D is a circular difference matrix coupling adjacent channels.

    Solution: W = (C'C + alpha*I + beta*D'D)^{-1} C'X

    Args:
        C: (n, K) design matrix
        X: (n, V_s) voxel patterns
        alpha: standard ridge penalty
        beta: smoothness penalty (0 = standard ridge)

    Returns:
        W: (K, V_s)
    """
    K = C.shape[1]
    # Circular difference matrix: D[i,i]=1, D[i,(i+1)%K]=-1
    D = np.zeros((K, K))
    for i in range(K):
        D[i, i] = 1.0
        D[i, (i + 1) % K] = -1.0
    G = C.T @ C + alpha * np.eye(K) + beta * (D.T @ D)
    return np.linalg.solve(G, C.T @ X)


def compute_prior_precision(A_list, R_s):
    """Compute per-voxel prior mean and variance from HC encoding matrices.

    Projects each HC's A_i through the target subject's SRM projection R_s
    to get per-HC weight matrices W_h, then computes element-wise mean/var.

    Args:
        A_list: list of (k, K) encoding matrices from HC subjects
        R_s: (V_s, k) SRM projection matrix for target subject

    Returns:
        W0: (K, V_s) prior mean
        var_W: (K, V_s) prior variance (floored at 1e-6)
    """
    W_stack = np.array([(R_s @ A_h).T for A_h in A_list])  # (n_hc, K, V_s)
    W0 = W_stack.mean(axis=0)           # (K, V_s)
    var_W = W_stack.var(axis=0, ddof=1)  # (K, V_s) unbiased
    var_W = np.maximum(var_W, 1e-6)      # floor to avoid infinite precision
    return W0, var_W


def fit_W_mixed_ridge_prior(C, X, W0, alpha, lam):
    """Mixed ridge + prior: independent data and prior penalties.

    min_W ||X - C@W||^2 + alpha*||W||^2 + lam*||W - W0||^2
    Solution: W = (C'C + (alpha+lam)*I)^{-1} (C'X + lam*W0)

    Args:
        C: (n, K) design matrix
        X: (n, V_s) voxel patterns
        W0: (K, V_s) prior weight matrix
        alpha: data ridge penalty
        lam: prior penalty

    Returns:
        W: (K, V_s)
    """
    K = C.shape[1]
    return np.linalg.solve(
        C.T @ C + (alpha + lam) * np.eye(K),
        C.T @ X + lam * W0
    )


def fit_W_bayes_prior(C, X, W0, var_W, gamma):
    """Bayesian prior with per-element precision from HC variance.

    Per-voxel solve: w_v = (C'C + diag(gamma / var_W[:, v]))^{-1}
                           (C'x_v + diag(gamma / var_W[:, v]) @ w0_v)

    Args:
        C: (n, K) design matrix
        X: (n, V_s) voxel patterns
        W0: (K, V_s) prior mean
        var_W: (K, V_s) prior variance
        gamma: global precision scale

    Returns:
        W: (K, V_s)
    """
    K, V_s = W0.shape
    CtC = C.T @ C        # (K, K)
    CtX = C.T @ X        # (K, V_s)
    W = np.zeros((K, V_s))

    for v in range(V_s):
        prec_v = gamma / var_W[:, v]         # (K,) per-channel precision
        Lambda_v = np.diag(prec_v)           # (K, K)
        lhs = CtC + Lambda_v
        rhs = CtX[:, v] + Lambda_v @ W0[:, v]
        W[:, v] = np.linalg.solve(lhs, rhs)

    return W


def fit_W_smooth_prior(C, X, W0, alpha, lam):
    """Channel-smooth ridge with group prior.

    min_W ||X - C@W||^2 + alpha*||D@W||^2 + lam*||W - W0||^2
    Solution: W = (C'C + alpha*D'D + lam*I)^{-1} (C'X + lam*W0)

    Args:
        C: (n, K) design matrix
        X: (n, V_s) voxel patterns
        W0: (K, V_s) prior weight matrix
        alpha: smoothness penalty
        lam: prior penalty

    Returns:
        W: (K, V_s)
    """
    K = C.shape[1]
    D = np.zeros((K, K))
    for i in range(K):
        D[i, i] = 1.0
        D[i, (i + 1) % K] = -1.0
    G = C.T @ C + alpha * (D.T @ D) + lam * np.eye(K)
    return np.linalg.solve(G, C.T @ X + lam * W0)


# ============================================================================
# Prediction & Decoding
# ============================================================================

def predict_patterns(W, C_test):
    """Predict voxel patterns.

    Args:
        W: (K, V_s)
        C_test: (n, K) design matrix for test conditions

    Returns:
        Y_hat: (n, V_s)
    """
    return C_test @ W


def decode_hue(W, basis_full, X_test):
    """Decode hue via correlation template matching.

    Args:
        W: (K, V_s) encoding weights
        basis_full: (360, K) full basis functions
        X_test: (n, V_s) test patterns

    Returns:
        pred_hues: (n,) predicted hue angles in degrees
    """
    channel_resp = W @ X_test.T  # (K, n)
    n = X_test.shape[0]
    pred_hues = np.zeros(n)
    for i in range(n):
        resp = channel_resp[:, i]
        if np.std(resp) == 0:
            pred_hues[i] = np.nan
            continue
        corrs = np.array([np.corrcoef(resp, basis_full[h])[0, 1]
                          for h in range(360)])
        if np.all(np.isnan(corrs)):
            pred_hues[i] = np.nan
        else:
            pred_hues[i] = np.nanargmax(corrs)
    return pred_hues


# ============================================================================
# Metrics
# ============================================================================

def circular_distance(y_true, y_pred):
    """Circular distance in degrees (0-180).

    Args:
        y_true, y_pred: arrays of hue angles (degrees)

    Returns:
        dist: same shape, values in [0, 180]
    """
    diff = np.abs(np.asarray(y_true, dtype=float) - np.asarray(y_pred, dtype=float))
    return np.minimum(diff, 360 - diff)


def voxel_pattern_correlation(Y_pred, Y_real):
    """Per-condition voxel pattern correlation.

    Args:
        Y_pred: (n_cond, V_s)
        Y_real: (n_cond, V_s)

    Returns:
        r: (n_cond,) Pearson r per condition
    """
    n = Y_pred.shape[0]
    r = np.zeros(n)
    for i in range(n):
        c = np.corrcoef(Y_pred[i], Y_real[i])
        r[i] = c[0, 1] if np.isfinite(c[0, 1]) else 0.0
    return r


def explained_variance(Y_pred, Y_real):
    """R-squared per condition.

    R^2 = 1 - ||Y - Y_hat||^2 / ||Y - Y_bar||^2

    Args:
        Y_pred: (n_cond, V_s)
        Y_real: (n_cond, V_s)

    Returns:
        r2: (n_cond,) R^2 per condition
    """
    n = Y_pred.shape[0]
    r2 = np.zeros(n)
    for i in range(n):
        ss_res = np.sum((Y_real[i] - Y_pred[i]) ** 2)
        ss_tot = np.sum((Y_real[i] - Y_real[i].mean()) ** 2)
        r2[i] = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
    return r2


def compute_rdm(patterns, metric='correlation'):
    """Compute representational dissimilarity matrix.

    Args:
        patterns: (n_cond, V) — condition x feature
        metric: 'correlation' or 'euclidean'

    Returns:
        rdm: (n_cond, n_cond) symmetric distance matrix
    """
    from scipy.spatial.distance import pdist, squareform
    if metric == 'correlation':
        return squareform(pdist(patterns, 'correlation'))
    else:
        return squareform(pdist(patterns, metric))


def rdm_upper_tri(rdm):
    """Extract upper triangle of RDM as a vector."""
    mask = np.triu(np.ones(rdm.shape, dtype=bool), k=1)
    return rdm[mask]


# ============================================================================
# GCV Alpha Selection
# ============================================================================

def gcv_select_alpha(C, Y, alpha_grid=ALPHA_GRID):
    """Select Ridge alpha via Generalized Cross-Validation.

    Args:
        C: (n, K) design matrix
        Y: (n, V_s) response matrix
        alpha_grid: list of candidate alphas

    Returns:
        best_alpha, gcv_scores (dict)
    """
    n = C.shape[0]
    U, s, Vt = np.linalg.svd(C, full_matrices=False)
    gcv_scores = {}
    for alpha in alpha_grid:
        d = s ** 2 / (s ** 2 + alpha)
        Y_hat = (U * d[np.newaxis, :]) @ (U.T @ Y)
        residuals = Y - Y_hat
        tr_H = np.sum(d)
        denom = (1 - tr_H / n) ** 2
        gcv = np.mean(residuals ** 2) / denom if denom > 0 else np.inf
        gcv_scores[alpha] = float(gcv)
    best_alpha = min(gcv_scores, key=gcv_scores.get)
    return best_alpha, gcv_scores


# ============================================================================
# SRM Helpers
# ============================================================================

def project_new_subject(srm_model, new_data):
    """Project a new subject into the SRM shared space via SVD.

    Matches the implementation in rerun_loo_consistent.py.

    Args:
        srm_model: Fitted BrainIAK SRM model
        new_data: (V_s, n_conditions) voxel data (transposed beta)

    Returns:
        W_new: (V_s, k) orthonormal projection matrix
    """
    S = srm_model.s_
    W_init = new_data @ np.linalg.pinv(S)
    U, _, Vt = np.linalg.svd(W_init, full_matrices=False)
    return U @ Vt


# ============================================================================
# I/O
# ============================================================================

def save_config(output_dir, **kwargs):
    """Save config.json with run metadata."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    config = {'timestamp': datetime.now().isoformat()}
    config.update(kwargs)
    with open(output_dir / 'config.json', 'w') as f:
        json.dump(config, f, indent=2, default=str)


def get_subject_group(subject):
    """Return 'HC' or 'CVD'."""
    return 'HC' if subject in HC_SUBJECTS else 'CVD'
