#!/usr/bin/env python3
"""utils_p4.py — shared helpers for future_phase4_geometry_synthesis (CONSUMER layer).

Reads exp2_neural Stage-1 embedding JSON (coords already computed) and provides:
  - classical MDS (double-centred eigendecomposition -> coords + eigenvalues)
  - RDM from coords (euclidean / correlation)
  - Procrustes decomposition (global gain / rotation / reflection / shape residual)
  - label-permutation null for Procrustes disparity  (PRIMARY discriminator, n=8 circular)
  - anisotropy (eigenvalue spectrum ratios)
  - HC self-consistency loader (canonical SRM loo_consistent JSON)

NO amplitude reload, NO SRM/FE recompute. Pure JSON arithmetic. Runs local.
"""
from __future__ import annotations
import json
import csv
from pathlib import Path
import numpy as np
from scipy.spatial.distance import pdist, squareform
from scipy.linalg import orthogonal_procrustes

# ---------------------------------------------------------------- constants
HERE = Path(__file__).resolve().parent
P4 = HERE.parent
ANALYSIS = P4.parent
EXP2_RES = ANALYSIS / "future_phase3_behavioral_analysis" / "exp2_neural" / "results"
BEHAV_RES = ANALYSIS / "future_phase3_behavioral_analysis" / "results" / "exp2_behavior"
LOO_JSON = (ANALYSIS / "phase2_SRM_across_between" / "results" / "loo_consistent"
            / "20260218_163819" / "loo_consistent_results.json")

ROIS = ['V1', 'V2', 'V3', 'V4']
CONDS = ['nofilter', 'window', 'optimal']
REPRS = ['procrustes', 'srm', 'fe_latent']
COLOR_NAMES = ['red', 'orange', 'yellow', 'green', 'cyan', 'blue', 'purple', 'magenta']
COLOR_HEX = ['#e6194B', '#f58231', '#ffe119', '#3cb44b',
             '#42d4f4', '#4363d8', '#911eb4', '#f032e6']
# ROI dir label: hV4 shown, 'V4' on disk / in JSON
ROI_DISPLAY = {'V1': 'V1', 'V2': 'V2', 'V3': 'V3', 'V4': 'hV4'}


# ---------------------------------------------------------------- IO
def load_stage1(subject: str, variant: str = 'matched') -> dict:
    """Stage-1 embeddings JSON (has raw coords per repr/condition)."""
    f = EXP2_RES / f"exp2_embeddings_sub-{subject}_{variant}.json"
    with open(f) as fh:
        return json.load(fh)


def load_stage2(subject: str, variant: str = 'matched') -> dict:
    f = EXP2_RES / f"exp2_geometry_derived_sub-{subject}_{variant}.json"
    with open(f) as fh:
        return json.load(fh)


def get_coords(d1: dict, roi: str, repr_: str, cond: str | None) -> np.ndarray:
    """(8, K) coords. cond=None -> hc_ref."""
    node = d1['rois'][roi]['embeddings'][repr_]
    block = node['hc_ref'] if cond is None else node['conditions'][cond]
    return np.asarray(block['coords'], float)


def hc_self_consistency() -> dict:
    """Canonical SRM-space HC-HC mean Spearman per ROI (reliability ceiling).
    Returns {'V1':.., 'V2':.., 'V3':.., 'V4':..}. hV4 stored under key 'hV4' in JSON."""
    with open(LOO_JSON) as fh:
        d = json.load(fh)
    out = {}
    keymap = {'V1': 'V1', 'V2': 'V2', 'V3': 'V3', 'V4': 'hV4'}
    for roi, jk in keymap.items():
        try:
            out[roi] = float(d['results'][jk]['rdm_correlations']['hc_hc']['mean'])
        except (KeyError, TypeError):
            out[roi] = None
    return out


def load_jnd(subject: str) -> dict | None:
    """{condition: (8,) jnd per measured pair} from *_jnd_compare.csv.
    Columns: pair_name + per-condition jnd (baseline/window/optimal)."""
    f = BEHAV_RES / f"sub-{subject}_jnd_compare.csv"
    if not f.exists():
        return None
    rows = list(csv.DictReader(open(f)))
    return {'_rows': rows, '_fields': rows[0].keys() if rows else []}


# ---------------------------------------------------------------- geometry
def rdm_from_coords(coords: np.ndarray, metric: str) -> np.ndarray:
    """(8,8) RDM. metric in {'eucl','corr'}."""
    m = {'eucl': 'euclidean', 'corr': 'correlation'}[metric]
    return squareform(pdist(coords, metric=m))


def classical_mds(D: np.ndarray, ndim: int = 2):
    """Classical MDS (PCoA). Returns (coords (n,ndim), eigvals_all (n,), stress_frac).

    Double-centre B = -1/2 J D^2 J, eigendecompose. Deterministic (unlike SMACOF).
    eigvals give per-axis variance -> anisotropy for free.
    stress_frac = 1 - (sum top-ndim positive eig / sum all positive eig).
    """
    D = np.asarray(D, float)
    n = D.shape[0]
    J = np.eye(n) - np.ones((n, n)) / n
    B = -0.5 * J @ (D ** 2) @ J
    B = (B + B.T) / 2.0
    w, V = np.linalg.eigh(B)
    order = np.argsort(w)[::-1]
    w, V = w[order], V[:, order]
    pos = w.clip(min=0)
    L = np.sqrt(pos[:ndim])
    coords = V[:, :ndim] * L
    tot = pos.sum()
    stress = 1.0 - (pos[:ndim].sum() / tot) if tot > 0 else np.nan
    return coords, w, float(stress)


def procrustes_decompose(X: np.ndarray, Y: np.ndarray) -> dict:
    """Align Y onto X. Decompose the X<->Y difference into interpretable parts.

    global_gain   : ||Yc||_F / ||Xc||_F   (isotropic scale ratio before norm)
    rotation_deg  : optimal rotation angle (2D) that best maps Xn->Yn
    reflection    : det(R) < 0
    disparity     : shape residual after centre+unit-Frob+rotation (0..1, scipy-style M^2)
    per_point     : residual norm per colour after alignment
    aniso_X/aniso_Y : eig1/eig2 aspect ratio of each config (from own coords)
    """
    X, Y = np.asarray(X, float), np.asarray(Y, float)
    Xc, Yc = X - X.mean(0), Y - Y.mean(0)
    nX = np.linalg.norm(Xc); nY = np.linalg.norm(Yc)
    global_gain = float(nY / (nX + 1e-12))
    Xn = Xc / (nX + 1e-12)
    Yn = Yc / (nY + 1e-12)
    R, _ = orthogonal_procrustes(Xn, Yn)
    resid = Xn @ R - Yn
    disparity = float(np.sum(resid ** 2))
    per_point = [float(np.linalg.norm(r)) for r in resid]
    refl = bool(np.linalg.det(R) < 0)
    rot_deg = None
    if R.shape == (2, 2):
        rot_deg = float(np.degrees(np.arctan2(R[1, 0], R[0, 0])))

    def aspect(C):
        Cc = C - C.mean(0)
        s = np.linalg.svd(Cc, compute_uv=False)
        return float(s[0] / (s[1] + 1e-12)) if len(s) > 1 else np.nan
    return {'global_gain': global_gain, 'rotation_deg': rot_deg, 'reflection': refl,
            'disparity': disparity, 'per_point': per_point,
            'aniso_X': aspect(X), 'aniso_Y': aspect(Y)}


def procrustes_disparity(X: np.ndarray, Y: np.ndarray) -> float:
    X, Y = np.asarray(X, float), np.asarray(Y, float)
    Xc, Yc = X - X.mean(0), Y - Y.mean(0)
    Xn = Xc / (np.linalg.norm(Xc) + 1e-12)
    Yn = Yc / (np.linalg.norm(Yc) + 1e-12)
    R, _ = orthogonal_procrustes(Xn, Yn)
    return float(np.sum((Xn @ R - Yn) ** 2))


def label_perm_null(X: np.ndarray, Y: np.ndarray, n_perm: int = 2000, seed: int = 0):
    """PRIMARY discriminator. Shuffle colour labels of Y, recompute disparity.
    p = P(null <= observed). Low p -> the SPECIFIC colour correspondence matters
    (not just 'two circles align'). Returns (observed, p, null_mean)."""
    rng = np.random.default_rng(seed)
    obs = procrustes_disparity(X, Y)
    n = X.shape[0]
    null = np.empty(n_perm)
    for i in range(n_perm):
        perm = rng.permutation(n)
        null[i] = procrustes_disparity(X, Y[perm])
    p = float((np.sum(null <= obs) + 1) / (n_perm + 1))
    return obs, p, float(null.mean())
