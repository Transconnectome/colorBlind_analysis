"""exp_gt_grid_sweep.py — Neutralization #2: identifiability landscape.

Goal: map where in (β_s, β_c) the v6 PCA pipeline can recover GT vs cannot.

For each (β_s, β_c) ∈ GT_GRID, synthesize voxel + GT-consistent fake JND
(same recipe as param_recovery_voxel_v2), and run v6 fit. M=20 noise
realizations × 7 HC donors per grid point.

Each candidate's family + production combo dictates the (subject_label,
combo_label, θ_conf). The grid spans realistic 2-component magnitudes.

GT_GRID (default 5×5 = 25 points; explicit list to keep readable):
  β_s ∈ { 0,  10, 20, 30, 40}
  β_c ∈ {-40, -20,  0, 20, 40}

Per grid point: 7 HC × M=20 = 140 fits.
Per candidate: 25 × 140 = 3500 fits.
Recommended: run candidates in separate SLURM tasks (--candidates).

Output: results/redteam/exp_gt_grid_sweep_<candidate>.json
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
    synthesize_fake_jnd,
    synth_provenance,
    SPATIAL_COV_RANK,
    AR1_RHO,
)
from s8_loo_train_test import jnd_baseline_from_pool             # noqa: E402

_PHASE1_FWD = SCRIPT_DIR.parents[1] / "future_phase1_forward_model" / "scripts"
sys.path.insert(0, str(_PHASE1_FWD))
from utils_forward_model import create_basis_full, HUE_ANGLES   # noqa: E402

# ---------------------------------------------------------------------------
HC_ALL = ["sub-01", "sub-02", "sub-03", "sub-04", "sub-05", "sub-06", "sub-07"]
RNG_SEED = 31337
M_REALIZATIONS = 20

v6.N_RESAMPLES = 1
v6.SUBSET_SIZE = 5

# Default GT grid: 5 × 5 = 25 points
GT_GRID_BS = [0.0, 10.0, 20.0, 30.0, 40.0]
GT_GRID_BC = [-40.0, -20.0, 0.0, 20.0, 40.0]

CANDIDATES = [
    {"id": "S08-stable",  "subject": "sub-08", "family": "deutan",
     "combo_label": "γALL|RDMV1|noLOCO"},
    {"id": "S08-robust",  "subject": "sub-08", "family": "deutan",
     "combo_label": "γOY|RDMV2|noLOCO"},
    {"id": "S09-primary", "subject": "sub-09", "family": "protan",
     "combo_label": "γALL|RDMV1|noLOCO"},
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


def _build_synth_amps(hc_k: str, family: str,
                       gt_bs: float, gt_bc: float,
                       all_hc_amps: dict,
                       rng: np.random.Generator) -> dict:
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
            W_k=W_k, beta_s=gt_bs, beta_c=gt_bc, family=family,
            theta_canonical=HUE_ANGLES.astype(float),
            noise_params=noise, rng=rng,
        )
        fake_amps[roi] = Y_synth
    return fake_amps


def _build_synth_jnd(family: str, gt_bs: float, gt_bc: float,
                      pool_jnd_subjs: list,
                      rng: np.random.Generator) -> dict:
    bl, sd = jnd_baseline_from_pool(pool_jnd_subjs)
    return synthesize_fake_jnd(
        beta_s=gt_bs, beta_c=gt_bc, family=family,
        pool_jnd_baseline=bl, pool_jnd_sd=sd, rng=rng,
        theta_canonical=HUE_ANGLES.astype(float),
    )


def _run_v6(subject_label: str, fake_amps_by_roi: dict, fake_jnd: dict,
             pool_amps_by_roi_excl_donor: dict,
             all_hc_jnd: dict, h_jnd_carrier: str,
             original_hc_jnd_subjs: list) -> dict:
    o_amps, o_hc, o_jnd = (v6.load_amplitudes, v6.load_hc_pool,
                           v6.load_jnd_per_pair)
    o_jnd_subjs = list(v6.HC_JND_SUBJS)
    o_hc_subjs = list(v6.HC_SUBJS)

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
    }


def run_grid_point(cand: dict, gt_bs: float, gt_bc: float,
                    all_hc_amps: dict, all_hc_jnd: dict,
                    original_hc_jnd_subjs: list,
                    m_realizations: int) -> dict:
    subject_label = cand["subject"]
    family = cand["family"]
    combo_label = cand["combo_label"]

    records = []
    for hc_k in HC_ALL:
        donor_amps = all_hc_amps.get(hc_k, {})
        if not donor_amps:
            continue
        pool = {roi: {h: all_hc_amps[h][roi] for h in HC_ALL
                       if h != hc_k and roi in all_hc_amps[h]}
                for roi in ROIS}
        for m in range(m_realizations):
            seed = (RNG_SEED + 7919 * (hash(
                cand["id"] + hc_k + f"{gt_bs:.0f}_{gt_bc:.0f}" + str(m)
            ) % 99991)) % (2**32)
            rng = np.random.default_rng(seed)
            fake_amps = _build_synth_amps(
                hc_k, family, gt_bs, gt_bc, all_hc_amps, rng,
            )
            if not fake_amps:
                continue
            pool_jnd_subjs = [h for h in original_hc_jnd_subjs if h != hc_k]
            fake_jnd = _build_synth_jnd(
                family, gt_bs, gt_bc, pool_jnd_subjs, rng,
            )
            try:
                storage = _run_v6(
                    subject_label, fake_amps, fake_jnd, pool,
                    all_hc_jnd, hc_k, original_hc_jnd_subjs,
                )
            except Exception as e:
                records.append({"hc": hc_k, "m": m, "error": repr(e)})
                continue
            rec = _argmin_record(storage, combo_label)
            if rec is None:
                records.append({"hc": hc_k, "m": m, "error": "no record"})
                continue
            rec["hc"] = hc_k
            rec["m"] = m
            records.append(rec)

    valid = [r for r in records
             if "error" not in r and r.get("beta_s") is not None]
    if not valid:
        return {"gt": [gt_bs, gt_bc], "n": 0, "records": records}
    bs = np.array([r["beta_s"] for r in valid], dtype=float)
    bc = np.array([r["beta_c"] for r in valid], dtype=float)
    return {
        "gt": [gt_bs, gt_bc],
        "n": len(valid),
        "recovered_bs_median": float(np.median(bs)),
        "recovered_bc_median": float(np.median(bc)),
        "recovered_bs_iqr": float(np.percentile(bs, 75) - np.percentile(bs, 25)),
        "recovered_bc_iqr": float(np.percentile(bc, 75) - np.percentile(bc, 25)),
        "bias_bs": float(np.median(bs) - gt_bs),
        "bias_bc": float(np.median(bc) - gt_bc),
        "distance_from_GT": float(np.sqrt(
            (np.median(bs) - gt_bs) ** 2 + (np.median(bc) - gt_bc) ** 2)),
        "frac_within_5deg": float(np.mean(
            (np.abs(bs - gt_bs) < 5.0) & (np.abs(bc - gt_bc) < 5.0))),
        "frac_within_10deg": float(np.mean(
            (np.abs(bs - gt_bs) < 10.0) & (np.abs(bc - gt_bc) < 10.0))),
        "raw_beta_s": bs.tolist(),
        "raw_beta_c": bc.tolist(),
    }


def main(argv: Optional[list] = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m-realizations", type=int, default=M_REALIZATIONS)
    parser.add_argument("--candidates", type=str, default="all")
    parser.add_argument("--bs-grid", type=str,
                        default=",".join(str(x) for x in GT_GRID_BS))
    parser.add_argument("--bc-grid", type=str,
                        default=",".join(str(x) for x in GT_GRID_BC))
    parser.add_argument("--out-suffix", type=str, default="")
    args = parser.parse_args(argv)

    bs_grid = [float(x) for x in args.bs_grid.split(",")]
    bc_grid = [float(x) for x in args.bc_grid.split(",")]
    cand_filter = (None if args.candidates == "all"
                   else set(args.candidates.split(",")))
    cands = [c for c in CANDIDATES
             if cand_filter is None or c["id"] in cand_filter]

    print(f"[exp_gt_grid_sweep] candidates={[c['id'] for c in cands]}",
          flush=True)
    print(f"  GT grid bs={bs_grid} bc={bc_grid}  total={len(bs_grid)*len(bc_grid)}",
          flush=True)
    print(f"  M={args.m_realizations}", flush=True)

    print("[exp_gt_grid_sweep] pre-loading data...", flush=True)
    all_hc_amps, all_hc_jnd = _preload_data()
    original_hc_jnd_subjs = list(v6.HC_JND_SUBJS)

    for cand in cands:
        out_path = (SCRIPT_DIR.parent / "results" / "redteam"
                    / f"exp_gt_grid_sweep_{cand['id']}{args.out_suffix}.json")
        out = {
            "config": {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "seed": RNG_SEED,
                "m_realizations": int(args.m_realizations),
                "bs_grid": bs_grid,
                "bc_grid": bc_grid,
                "candidate": cand,
                "subset_size": v6.SUBSET_SIZE,
                "n_resamples": v6.N_RESAMPLES,
                "spatial_cov_rank": int(SPATIAL_COV_RANK),
                "temporal_ar1_rho": float(AR1_RHO),
                "synth_provenance": synth_provenance(),
                "ROI_K": dict(ROI_K),
                "note": (
                    "Identifiability landscape map. GT-consistent fake JND "
                    "(same as param_recovery_voxel v2). 25 (β_s, β_c) GT "
                    "points × 7 HC × M noise realizations."
                ),
            },
            "points": [],
        }
        t0 = time.time()
        print(f"\n=== {cand['id']} ===", flush=True)
        for gt_bs in bs_grid:
            for gt_bc in bc_grid:
                tp = time.time()
                pt = run_grid_point(cand, gt_bs, gt_bc,
                                      all_hc_amps, all_hc_jnd,
                                      original_hc_jnd_subjs,
                                      args.m_realizations)
                pt["elapsed_s"] = round(time.time() - tp, 1)
                out["points"].append(pt)
                if pt.get("n", 0) > 0:
                    print(f"  GT=({gt_bs:+.0f},{gt_bc:+.0f}) "
                          f"n={pt['n']:3d} "
                          f"bias=({pt['bias_bs']:+.1f},{pt['bias_bc']:+.1f}) "
                          f"f10°={pt['frac_within_10deg']:.2f} "
                          f"[{pt['elapsed_s']}s]", flush=True)
                else:
                    print(f"  GT=({gt_bs:+.0f},{gt_bc:+.0f}) n=0 SKIPPED",
                          flush=True)
        out["elapsed_s"] = round(time.time() - t0, 1)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(out, indent=2, default=str))
        print(f"Saved: {out_path}  ({out['elapsed_s']}s)", flush=True)


if __name__ == "__main__":
    main()
