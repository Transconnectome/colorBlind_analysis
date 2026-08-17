"""null_label_permutation.py — Source C: within-subject color-label permutation.

For each production candidate, run the v6 fit on a sequence of CVD
amplitude tensors in which the *color labels* have been permuted within each
subject (HC pool untouched). This gives a label-permutation null for the
v6 composite at that combo, controlling for voxel covariance + run structure
of the actual CVD subject.

  For permutation p ∈ {1, ..., N_PERM = 1000}:
    new_amps[run, c, :] = cvd_amp[run, σ_p(c), :]
    storage_p = v6.fit_subject(subject)        # single resample, original HC pool
    record    = storage_p[combo_label]['2comp'][0]

Null distribution: 1000 argmins + losses.

The same random permutation σ_p is applied to ALL ROIs simultaneously
(consistent across the v6 multi-ROI fit). The HC pool is unchanged.

Seed: RNG_SEED = 27182 (parity with Exp 14 / null_within_hc_loo).

DO NOT execute this header. Run via SLURM after review.

Output: results/redteam/null_label_permutation_v6_pca.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import s10b_v6_pca_rdm as v6                                     # noqa: E402
from neural_loss import load_amplitudes as _load_amps            # noqa: E402
from behav_loss import load_jnd_per_pair as _load_jnd            # noqa: E402

OUT = (SCRIPT_DIR.parent / "results" / "redteam"
       / "null_label_permutation_v6_pca.json")

# ---------------------------------------------------------------------------
HC_ALL = ["sub-01", "sub-02", "sub-03", "sub-04", "sub-05", "sub-06", "sub-07"]
RNG_SEED = 27182                  # parity with Exp 14 carrier seed
N_PERM = 1000                      # null draws per candidate

v6.N_RESAMPLES = 1
v6.SUBSET_SIZE = 5                # production-matched

CANDIDATES = [
    {"id": "S08-stable",  "subject": "sub-08", "family": "deutan",
     "combo_label": "γALL|RDMV1|noLOCO",
     "production_beta_s": 38.0, "production_beta_c": -10.0},
    {"id": "S08-robust",  "subject": "sub-08", "family": "deutan",
     "combo_label": "γOY|RDMV2|noLOCO",
     "production_beta_s":  6.0, "production_beta_c": -42.0},
    {"id": "S09-primary", "subject": "sub-09", "family": "protan",
     "combo_label": "γALL|RDMV1|noLOCO",
     "production_beta_s":  2.0, "production_beta_c":  24.0},
]

ROIS = list(v6.ROIS)


# ---------------------------------------------------------------------------
def _preload_subject_amps(subject: str) -> dict:
    out: dict = {}
    for roi in ROIS:
        try:
            amp = _load_amps(subject, roi)
            out[roi] = amp
        except Exception:
            pass
    return out


def _permute_amps(amps_by_roi: dict, perm_indices: np.ndarray) -> dict:
    """Apply the same color-label permutation to every ROI of a subject."""
    out = {}
    for roi, amp in amps_by_roi.items():
        if amp.ndim != 3 or amp.shape[1] != 8:
            out[roi] = amp
            continue
        out[roi] = amp[:, perm_indices, :].copy()
    return out


def _run_v6_with_perm(subject_label: str, fake_amps_by_roi: dict) -> dict:
    """Monkey-patch v6.load_amplitudes for the subject only; HC pool unchanged."""
    o_amps = v6.load_amplitudes

    def p_amps(sid: str, roi: str):
        if sid == subject_label:
            return fake_amps_by_roi.get(roi)
        return _load_amps(sid, roi)

    v6.load_amplitudes = p_amps
    try:
        storage = v6.fit_subject(subject_label)
    finally:
        v6.load_amplitudes = o_amps
    return storage


def _argmin_record(storage: dict, combo_label: str) -> Optional[dict]:
    block = storage.get(combo_label)
    if block is None:
        return None
    recs = block.get("2comp", [])
    if not recs:
        return None
    r = recs[0]
    return {
        "beta_s": float(r["beta_s"]),
        "beta_c": float(r["beta_c"]),
        "train_loss": float(r["train_loss"]) if r.get("train_loss") is not None else None,
        "boundary": bool(r.get("boundary", False)),
    }


# ---------------------------------------------------------------------------
def run_candidate(candidate: dict, n_perm: int,
                  perm_start: int = 0,
                  perm_end: Optional[int] = None) -> dict:
    """Run N_PERM label permutations for one candidate.

    Args:
        candidate: candidate dict.
        n_perm: total number of permutations (controls seed sequence).
        perm_start, perm_end: half-open slice for SLURM array parallelisation.

    Returns:
        dict with raw records and summary.
    """
    subject = candidate["subject"]
    combo_label = candidate["combo_label"]
    end = n_perm if perm_end is None else min(perm_end, n_perm)

    amps_by_roi = _preload_subject_amps(subject)
    if not amps_by_roi:
        return {"candidate": candidate, "error": "no amps loaded",
                "records": []}

    rng_master = np.random.default_rng(RNG_SEED + hash(candidate["id"]) % 99991)
    # pre-draw all permutations so seeds are deterministic across the run
    perms = [rng_master.permutation(8) for _ in range(n_perm)]

    records = []
    t_start = time.time()
    for p in range(perm_start, end):
        sigma = perms[p]
        fake = _permute_amps(amps_by_roi, sigma)
        try:
            storage = _run_v6_with_perm(subject, fake)
            rec = _argmin_record(storage, combo_label)
            if rec is None:
                records.append({"p": p, "sigma": sigma.tolist(),
                                "error": "no record"})
                continue
            rec["p"] = p
            rec["sigma"] = sigma.tolist()
            records.append(rec)
        except Exception as e:
            records.append({"p": p, "sigma": sigma.tolist(),
                            "error": repr(e)})
        if (p + 1 - perm_start) % 20 == 0:
            print(f"  [{candidate['id']}] perm {p + 1 - perm_start}/{end - perm_start} "
                  f"elapsed={time.time() - t_start:.0f}s", flush=True)
    return {
        "candidate": candidate,
        "perm_range": [perm_start, end],
        "records": records,
        "elapsed_s": round(time.time() - t_start, 1),
    }


def _summarize(records: list, production_beta_s: float,
               production_beta_c: float) -> dict:
    valid = [r for r in records
             if "error" not in r and r.get("beta_s") is not None]
    if not valid:
        return {"n": 0}
    bs = np.array([r["beta_s"] for r in valid], dtype=float)
    bc = np.array([r["beta_c"] for r in valid], dtype=float)
    losses = np.array([r["train_loss"] for r in valid
                        if r["train_loss"] is not None], dtype=float)
    return {
        "n": len(valid),
        "beta_s_median": float(np.median(bs)),
        "beta_s_iqr": float(np.percentile(bs, 75) - np.percentile(bs, 25)),
        "beta_c_median": float(np.median(bc)),
        "beta_c_iqr": float(np.percentile(bc, 75) - np.percentile(bc, 25)),
        "loss_median": float(np.median(losses)) if losses.size else None,
        "loss_5pct": float(np.percentile(losses, 5)) if losses.size else None,
        "raw_beta_s": bs.tolist(),
        "raw_beta_c": bc.tolist(),
        "raw_losses": losses.tolist(),
        # NOTE: real-data p-value computed in analyze_verification.py against
        # the production loss_at_argmin (loaded from s10_inclusion results).
        "production_beta_s": production_beta_s,
        "production_beta_c": production_beta_c,
    }


# ---------------------------------------------------------------------------
def main(argv: Optional[list] = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n-perm", type=int, default=N_PERM)
    parser.add_argument("--perm-start", type=int, default=0)
    parser.add_argument("--perm-end", type=int, default=None)
    parser.add_argument("--candidates", type=str, default="all")
    args = parser.parse_args(argv)

    cand_filter = (None if args.candidates == "all"
                   else set(args.candidates.split(",")))
    cands = [c for c in CANDIDATES
             if cand_filter is None or c["id"] in cand_filter]

    print(f"[null_label_permutation] candidates={[c['id'] for c in cands]}",
          flush=True)
    print(f"  N_PERM={args.n_perm} slice=[{args.perm_start},{args.perm_end}]",
          flush=True)

    out = {
        "config": {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "seed": RNG_SEED,
            "n_perm": int(args.n_perm),
            "perm_slice": [args.perm_start, args.perm_end],
            "candidates": [c["id"] for c in cands],
            "subset_size": v6.SUBSET_SIZE,
            "n_resamples": v6.N_RESAMPLES,
            "method": "Label permutation: shuffle CVD's color labels per "
                       "permutation (same σ across ROIs); HC pool unchanged. "
                       "Single v6 fit per permutation.",
        },
        "cells": {},
    }

    t_all = time.time()
    for cand in cands:
        print(f"\n=== {cand['id']} ({cand['subject']}, {cand['combo_label']}) ===",
              flush=True)
        cell = run_candidate(cand, args.n_perm,
                             perm_start=args.perm_start,
                             perm_end=args.perm_end)
        cell["summary"] = _summarize(
            cell["records"],
            cand["production_beta_s"], cand["production_beta_c"],
        )
        out["cells"][cand["id"]] = cell
        n = cell["summary"].get("n", 0)
        print(f"  [{cand['id']}] {n} valid perms; elapsed={cell['elapsed_s']}s",
              flush=True)

    out["elapsed_s"] = round(time.time() - t_all, 1)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    # When run as SLURM array slices, append slice suffix
    suffix = ""
    if args.perm_start != 0 or args.perm_end is not None:
        suffix = f"_p{args.perm_start:04d}-{(args.perm_end or args.n_perm):04d}"
    out_path = OUT.with_name(OUT.stem + suffix + OUT.suffix)
    out_path.write_text(json.dumps(out, indent=2, default=str))
    print(f"\nSaved: {out_path}  ({out['elapsed_s']}s total)", flush=True)


if __name__ == "__main__":
    main()
