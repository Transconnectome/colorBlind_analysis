"""exp_atom_decomp_at_zero.py — Neutralization #1: γ vs RDM atom decomposition.

Goal: identify which atom drives the ~20-25° (0,0)-recovery bias in v6 PCA.

For each production candidate, synthesize fake CVD at GT=(0,0) (voxel +
donor real JND, internally consistent at the zero point), then extract the
argmin from THREE combo configurations in the same v6 fit storage:

  - γ-only:   e.g.  "γALL|RDM_|noLOCO"
  - RDM-only: e.g.  "γ_|RDMV1|noLOCO"
  - Joint:    e.g.  "γALL|RDMV1|noLOCO"  (= production combo, baseline)

Each (candidate, donor HC_k, noise realization m) produces three argmins
from the same synth. Compare per-atom-config distributions of |bs|, |bc|,
f10°_origin to attribute the bias to a specific atom.

Total fits: 3 candidates × 7 HCs × M=20 = 420 v6 fits.
Each v6 fit emits all combos; we pull the three relevant labels.

Output: results/redteam/exp_atom_decomp_at_zero.json
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
from neural_loss import (                                        # noqa: E402
    load_amplitudes as _load_amps, ROI_K,
)
from behav_loss import load_jnd_per_pair as _load_jnd            # noqa: E402
from forward_voxel_synth import (                                # noqa: E402
    precompute_per_hc_W,
    estimate_noise_per_hc,
    synthesize_voxel_response,
    synth_provenance,
    SPATIAL_COV_RANK,
    AR1_RHO,
)

_PHASE1_FWD = SCRIPT_DIR.parents[1] / "future_phase1_forward_model" / "scripts"
sys.path.insert(0, str(_PHASE1_FWD))
from utils_forward_model import create_basis_full, HUE_ANGLES   # noqa: E402

OUT = (SCRIPT_DIR.parent / "results" / "redteam"
       / "exp_atom_decomp_at_zero.json")

# ---------------------------------------------------------------------------
HC_ALL = ["sub-01", "sub-02", "sub-03", "sub-04", "sub-05", "sub-06", "sub-07"]
RNG_SEED = 27182                  # parity with B2
M_REALIZATIONS = 20

v6.N_RESAMPLES = 1
v6.SUBSET_SIZE = 5

# For each production combo, we evaluate three atom configurations:
#   joint = production combo (γ + RDM)
#   gamma_only = γ atom only (RDM dropped → '_')
#   rdm_only = RDM atom only (γ dropped → '_')
#
# Combo label format (s10b_v6_pca_rdm.py:283/297):
#   "γ<g_label>|RDM<r_label>|<LOCO|noLOCO>"   with '_' for empty.
CANDIDATES = [
    {"id": "S08-stable",  "subject": "sub-08", "family": "deutan",
     "joint":     "γALL|RDMV1|noLOCO",
     "gamma":     "γALL|RDM_|noLOCO",
     "rdm":       "γ_|RDMV1|noLOCO",
     "production_beta_s": 38.0, "production_beta_c": -10.0},
    {"id": "S08-robust",  "subject": "sub-08", "family": "deutan",
     "joint":     "γOY|RDMV2|noLOCO",
     "gamma":     "γOY|RDM_|noLOCO",
     "rdm":       "γ_|RDMV2|noLOCO",
     "production_beta_s":  6.0, "production_beta_c": -42.0},
    {"id": "S09-primary", "subject": "sub-09", "family": "protan",
     "joint":     "γALL|RDMV1|noLOCO",
     "gamma":     "γALL|RDM_|noLOCO",
     "rdm":       "γ_|RDMV1|noLOCO",
     "production_beta_s":  2.0, "production_beta_c":  24.0},
]

ROIS = list(v6.ROIS)


def _preload_data() -> tuple[dict, dict]:
    all_hc_amps: dict = {}
    for hc in HC_ALL:
        all_hc_amps[hc] = {}
        for roi in ROIS:
            try:
                amp = _load_amps(hc, roi)
                if roi == "V4" and amp.shape[2] < 20:
                    continue
                all_hc_amps[hc][roi] = amp
            except Exception:
                pass
    all_hc_jnd = {hc: _load_jnd(hc) for hc in HC_ALL}
    return all_hc_amps, all_hc_jnd


def _build_synth_zero_amps(hc_k: str, family: str,
                            all_hc_amps: dict,
                            rng: np.random.Generator) -> dict:
    """Synthesize fake CVD voxels at GT=(0,0)."""
    donor_amps = all_hc_amps.get(hc_k, {})
    fake_amps = {}
    for roi in ROIS:
        if roi not in donor_amps:
            continue
        K = ROI_K[roi]
        C_b = create_basis_full(K, basis_type="fe")[HUE_ANGLES.astype(int)]
        W_dict = precompute_per_hc_W({hc_k: donor_amps[roi]}, C_b)
        if hc_k not in W_dict:
            continue
        W_k = W_dict[hc_k]
        noise = estimate_noise_per_hc(donor_amps[roi], W_k, C_b)
        Y_synth = synthesize_voxel_response(
            W_k=W_k, beta_s=0.0, beta_c=0.0, family=family,
            theta_canonical=HUE_ANGLES.astype(float),
            noise_params=noise, rng=rng,
        )
        fake_amps[roi] = Y_synth
    return fake_amps


def _run_v6_zero(subject_label: str, fake_amps_by_roi: dict,
                  pool_amps_by_roi_excl_donor: dict,
                  all_hc_jnd: dict, h_jnd_carrier: str,
                  original_hc_jnd_subjs: list) -> dict:
    """Run v6.fit_subject under monkey-patched loaders. Donor real JND used."""
    o_amps, o_hc, o_jnd = (v6.load_amplitudes, v6.load_hc_pool,
                           v6.load_jnd_per_pair)
    o_jnd_subjs = list(v6.HC_JND_SUBJS)
    o_hc_subjs = list(v6.HC_SUBJS)

    fake_jnd = dict(all_hc_jnd[h_jnd_carrier])

    def p_amps(sid, roi):
        if sid == subject_label:
            return fake_amps_by_roi.get(roi)
        return None

    def p_hc(roi):
        return dict(pool_amps_by_roi_excl_donor.get(roi, {}))

    def p_jnd(sid):
        if sid == subject_label:
            return fake_jnd
        return all_hc_jnd.get(sid)

    v6.load_amplitudes = p_amps
    v6.load_hc_pool = p_hc
    v6.load_jnd_per_pair = p_jnd
    v6.HC_SUBJS = [h for h in HC_ALL if h != h_jnd_carrier]
    v6.HC_JND_SUBJS = [h for h in original_hc_jnd_subjs if h != h_jnd_carrier]
    try:
        storage = v6.fit_subject(subject_label)
    finally:
        v6.load_amplitudes = o_amps
        v6.load_hc_pool = o_hc
        v6.load_jnd_per_pair = o_jnd
        v6.HC_JND_SUBJS = o_jnd_subjs
        v6.HC_SUBJS = o_hc_subjs
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
        "train_loss": (float(r["train_loss"])
                       if r.get("train_loss") is not None else None),
        "boundary": bool(r.get("boundary", False)),
    }


def _summarize_atom(recs: list) -> dict:
    valid = [r for r in recs if r is not None and r.get("beta_s") is not None]
    if not valid:
        return {"n": 0}
    bs = np.array([r["beta_s"] for r in valid], dtype=float)
    bc = np.array([r["beta_c"] for r in valid], dtype=float)
    abs_bs = np.abs(bs); abs_bc = np.abs(bc)
    return {
        "n": int(len(valid)),
        "abs_bs_median": float(np.median(abs_bs)),
        "abs_bc_median": float(np.median(abs_bc)),
        "abs_bs_iqr": float(np.percentile(abs_bs, 75) - np.percentile(abs_bs, 25)),
        "abs_bc_iqr": float(np.percentile(abs_bc, 75) - np.percentile(abs_bc, 25)),
        "abs_bs_p95": float(np.percentile(abs_bs, 95)),
        "abs_bc_p95": float(np.percentile(abs_bc, 95)),
        "frac_within_10deg_origin": float(np.mean(
            (abs_bs < 10.0) & (abs_bc < 10.0))),
        "raw_beta_s": bs.tolist(),
        "raw_beta_c": bc.tolist(),
    }


def run_candidate(cand: dict, all_hc_amps: dict, all_hc_jnd: dict,
                   original_hc_jnd_subjs: list,
                   m_realizations: int = M_REALIZATIONS) -> dict:
    subject_label = cand["subject"]
    family = cand["family"]
    records = {"joint": [], "gamma": [], "rdm": []}
    t0 = time.time()
    for hc_k in HC_ALL:
        donor_amps = all_hc_amps.get(hc_k, {})
        if not donor_amps:
            continue
        pool = {roi: {h: all_hc_amps[h][roi] for h in HC_ALL
                      if h != hc_k and roi in all_hc_amps[h]}
                for roi in ROIS}
        for m in range(m_realizations):
            seed = (RNG_SEED
                    + 7919 * (hash(cand["id"] + hc_k + str(m)) % 99991)) % (2**32)
            rng = np.random.default_rng(seed)
            fake_amps = _build_synth_zero_amps(hc_k, family, all_hc_amps, rng)
            if not fake_amps:
                continue
            try:
                storage = _run_v6_zero(
                    subject_label, fake_amps, pool,
                    all_hc_jnd, hc_k, original_hc_jnd_subjs,
                )
            except Exception as e:
                records["joint"].append({"hc_donor": hc_k, "m": m,
                                          "error": repr(e)})
                continue
            for key in ("joint", "gamma", "rdm"):
                rec = _argmin_record(storage, cand[key])
                if rec is not None:
                    rec["hc_donor"] = hc_k
                    rec["m"] = m
                records[key].append(rec)
    summary = {
        atom: _summarize_atom(records[atom])
        for atom in ("joint", "gamma", "rdm")
    }
    return {
        "candidate": cand,
        "records": records,
        "summary": summary,
        "elapsed_s": round(time.time() - t0, 1),
    }


def main(argv: Optional[list] = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m-realizations", type=int, default=M_REALIZATIONS)
    parser.add_argument("--candidates", type=str, default="all")
    args = parser.parse_args(argv)

    cand_filter = (None if args.candidates == "all"
                   else set(args.candidates.split(",")))
    cands = [c for c in CANDIDATES
             if cand_filter is None or c["id"] in cand_filter]

    print(f"[exp_atom_decomp_at_zero] candidates={[c['id'] for c in cands]}",
          flush=True)
    print(f"  M={args.m_realizations}", flush=True)

    print("[exp_atom_decomp_at_zero] pre-loading data...", flush=True)
    all_hc_amps, all_hc_jnd = _preload_data()
    original_hc_jnd_subjs = list(v6.HC_JND_SUBJS)

    out = {
        "config": {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "seed": RNG_SEED,
            "m_realizations": int(args.m_realizations),
            "candidates": [c["id"] for c in cands],
            "subset_size": v6.SUBSET_SIZE,
            "n_resamples": v6.N_RESAMPLES,
            "spatial_cov_rank": int(SPATIAL_COV_RANK),
            "temporal_ar1_rho": float(AR1_RHO),
            "synth_provenance": synth_provenance(),
            "ROI_K": dict(ROI_K),
            "atoms_compared": ["joint (production)", "gamma-only", "rdm-only"],
            "note": (
                "GT=(0,0) synth voxels + donor REAL JND. Donor real JND is "
                "internally consistent with GT=0 (HC = no shift), so γ-atom "
                "is not biased by synth design; comparison purely reveals "
                "atom-level contribution to the noise-floor argmin bias."
            ),
        },
        "cells": {},
    }
    t_all = time.time()
    for cand in cands:
        print(f"\n=== {cand['id']} ===", flush=True)
        result = run_candidate(cand, all_hc_amps, all_hc_jnd,
                                original_hc_jnd_subjs,
                                m_realizations=args.m_realizations)
        out["cells"][cand["id"]] = result
        for atom in ("joint", "gamma", "rdm"):
            s = result["summary"][atom]
            if s.get("n", 0) > 0:
                print(f"  {atom:8s} n={s['n']:3d} "
                      f"|bs|={s['abs_bs_median']:5.1f}° "
                      f"|bc|={s['abs_bc_median']:5.1f}° "
                      f"f10°={s['frac_within_10deg_origin']:.2f}", flush=True)
        print(f"  elapsed={result['elapsed_s']}s", flush=True)

    out["elapsed_s"] = round(time.time() - t_all, 1)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2, default=str))
    print(f"\nSaved: {OUT}  ({out['elapsed_s']}s total)", flush=True)


if __name__ == "__main__":
    main()
