"""Project filter-validation (ses-02) amplitudes onto frozen HC SRM W and
compute RDM correlations against the existing HC + ses-01 CVD references.

Run as: ``python project_filtered_session.py --subjects 08 09 --session 02 ...``

Pure numpy/scipy — no BrainIAK import, so ``mpirun`` is NOT required.

Expected on-disk inputs (server paths):
    - HC results dir, e.g. ``results/srm_loo_consistent/{ROI}/srm_W.npy``
      and ``rdm_hc_mean.npy`` (saved by rerun_loo_consistent.py).
    - ses-02 amplitudes:
      ``derivatives/full_dataset_C010/sub-{ID}/ses-{S}/{ROI_disk}/amplitudes_procrustes.npy``
      shape ``(6, 8, n_voxels)``.

Outputs (per ROI, written under --output-dir):
    - ``sub-{ID}_ses-{S}_{ROI}_S.npy``        projected shared response (K, 8)
    - ``sub-{ID}_ses-{S}_{ROI}_rdm.npy``      8x8 1 - corr RDM
    - ``srm_rdm_filter_validation.json``      summary: rho/p vs HC mean RDM
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import numpy as np
from scipy.spatial.distance import squareform
from scipy.stats import spearmanr


ROI_DISK = {"V1": "V1", "V2": "V2", "V3": "V3", "V4": "V4", "hV4": "V4"}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--subjects", nargs="+", required=True,
                   help="subject IDs (e.g. 08 09)")
    p.add_argument("--session", required=True, help="session label (e.g. 02)")
    p.add_argument("--rois", nargs="+", default=["V1", "V2", "V3", "V4"])
    p.add_argument("--dataset", default="method3_header_mi")
    p.add_argument("--hc-results-dir", required=True,
                   help="dir containing per-ROI frozen HC SRM W + reference RDM")
    p.add_argument("--amplitudes-root", default="derivatives/full_dataset_C010",
                   help="root of GLM amplitudes output (server: scratch)")
    p.add_argument("--output-dir", required=True)
    p.add_argument("--rdm-metric", choices=["correlation", "euclidean"],
                   default="correlation")
    return p.parse_args()


def load_amplitudes(root: Path, sid: str, session: str, roi: str) -> np.ndarray:
    """Load (6, 8, n_voxels) amplitudes for one subject/session/ROI."""
    roi_dir = ROI_DISK[roi]
    path = root / f"sub-{sid}" / f"ses-{session}" / roi_dir / "amplitudes_procrustes.npy"
    if not path.exists():
        # fall back to flat layout (no ses-XX) for smoke tests
        flat = root / f"sub-{sid}" / roi_dir / "amplitudes_procrustes.npy"
        if flat.exists():
            print(f"  [warn] {path} missing; using flat layout {flat}")
            path = flat
        else:
            raise FileNotFoundError(path)
    arr = np.load(path)
    if arr.ndim != 3 or arr.shape[:2] != (6, 8):
        raise ValueError(f"unexpected amplitudes shape {arr.shape} at {path}")
    return arr  # (runs, colors, voxels)


def load_hc_w(hc_dir: Path, roi: str) -> np.ndarray:
    """Load frozen HC SRM weight matrix (n_voxels, K)."""
    candidates = [
        hc_dir / roi / "srm_W.npy",
        hc_dir / roi / "W_hc_mean.npy",
        hc_dir / f"{roi}_W.npy",
        hc_dir / f"srm_W_{roi}.npy",
    ]
    for c in candidates:
        if c.exists():
            return np.load(c)
    raise FileNotFoundError(
        f"No frozen HC W found for {roi}. Tried: " + ", ".join(str(c) for c in candidates)
    )


def load_hc_rdm(hc_dir: Path, roi: str) -> np.ndarray | None:
    """Load reference HC mean RDM (8, 8) if available; None otherwise."""
    candidates = [
        hc_dir / roi / "rdm_hc_mean.npy",
        hc_dir / f"{roi}_rdm_hc.npy",
        hc_dir / f"rdm_hc_{roi}.npy",
    ]
    for c in candidates:
        if c.exists():
            return np.load(c)
    return None


def project_to_shared(amps: np.ndarray, W: np.ndarray) -> np.ndarray:
    """Run-average amplitudes, then project: S = W.T @ X.

    amps: (runs=6, colors=8, voxels)
    W:    (voxels, K)
    returns: (K, 8) shared-space response
    """
    n_voxels = W.shape[0]
    if amps.shape[2] != n_voxels:
        raise ValueError(
            f"voxel mismatch: amplitudes have {amps.shape[2]}, W expects {n_voxels}"
        )
    X = amps.mean(axis=0).T  # (voxels, 8)
    return W.T @ X           # (K, 8)


def compute_rdm(S: np.ndarray, metric: str) -> np.ndarray:
    """Return 8x8 dissimilarity matrix across the 8 colors."""
    X = S.T  # (8, K)
    if metric == "correlation":
        Xc = X - X.mean(axis=1, keepdims=True)
        norms = np.linalg.norm(Xc, axis=1, keepdims=True)
        norms[norms == 0] = 1
        Xn = Xc / norms
        C = Xn @ Xn.T
        return 1.0 - C
    diff = X[:, None, :] - X[None, :, :]
    return np.linalg.norm(diff, axis=-1)


def rdm_upper(rdm: np.ndarray) -> np.ndarray:
    """Vector of the upper triangle (k=1), 28 entries for 8x8."""
    return squareform(rdm, checks=False)


def main() -> None:
    args = parse_args()
    amps_root = Path(args.amplitudes_root)
    hc_dir = Path(args.hc_results_dir)
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    summary: dict = {
        "subjects": args.subjects,
        "session": args.session,
        "dataset": args.dataset,
        "rdm_metric": args.rdm_metric,
        "rois": {},
    }

    for roi in args.rois:
        print(f"\n[{roi}]")
        try:
            W = load_hc_w(hc_dir, roi)
        except FileNotFoundError as exc:
            print(f"  SKIP: {exc}")
            summary["rois"][roi] = {"status": "skipped", "reason": str(exc)}
            continue
        print(f"  W shape: {W.shape}")
        hc_rdm = load_hc_rdm(hc_dir, roi)
        if hc_rdm is None:
            print(f"  [warn] HC mean RDM not found for {roi}; rho/p will be null")

        roi_summary: dict = {"status": "ok", "subjects": {}}
        for sid in args.subjects:
            try:
                amps = load_amplitudes(amps_root, sid, args.session, roi)
            except FileNotFoundError as exc:
                print(f"  sub-{sid}: amplitudes missing - {exc}")
                roi_summary["subjects"][sid] = {"status": "missing"}
                continue

            S = project_to_shared(amps, W)
            rdm = compute_rdm(S, args.rdm_metric)

            np.save(out / f"sub-{sid}_ses-{args.session}_{roi}_S.npy", S)
            np.save(out / f"sub-{sid}_ses-{args.session}_{roi}_rdm.npy", rdm)

            entry: dict = {
                "status": "ok",
                "n_voxels": int(amps.shape[2]),
                "K": int(W.shape[1]),
                "rdm_mean": float(rdm_upper(rdm).mean()),
            }
            if hc_rdm is not None and hc_rdm.shape == rdm.shape:
                rho, p = spearmanr(rdm_upper(rdm), rdm_upper(hc_rdm))
                entry["rho_vs_hc"] = float(rho)
                entry["p_vs_hc"] = float(p)
            roi_summary["subjects"][sid] = entry
            print(f"  sub-{sid}: {entry}")

        summary["rois"][roi] = roi_summary

    out_json = out / "srm_rdm_filter_validation.json"
    with open(out_json, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nSummary written: {out_json}")


if __name__ == "__main__":
    main()
