"""cycle12 wretrained landscape runner (auto-generated)."""
import sys, time, json, os
sys.path.insert(0, "/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/phase5_filter_optimization/scripts")
sys.path.insert(0, "/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/phase5_filter_optimization/scripts/older_cycles/cycle_loss_redesign")
sys.path.insert(0, "/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/phase4_forward_model/scripts")
import numpy as np
from pathlib import Path
from utils_forward_model import load_amplitudes, N_COLORS
from step1_fit_loco_v2 import simulate_mean_hc_loco_legacy, load_cvd_loco_target
from loss_redesign_smoke import get_2component_design, compute_extended_loss

LOCAL_DATA = Path("/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/phase1_procrustes_decoding/results/visualization/full_dataset_C010_with_residuals")
OUT_DIR = Path("/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/phase5_filter_optimization/results/fixedW_onlyTest")
OUT_DIR.mkdir(parents=True, exist_ok=True)
LOG_PATH = OUT_DIR / ".wretrained_sweep.log"

log_f = open(LOG_PATH, "w")
sys.stdout = log_f
sys.stderr = log_f

HC_POOL = ["01","02","03","04","05","06","07"]
CVD_TYPE = {"08":"deutan","09":"protan"}
ALPHA, BETA, LAM = 1.0, 1.0, 0.2
BS_MAX, BC_MAX = 80.0, 60.0
BS_LO, BS_HI, BS_STEP = 0.0, 50.0, 2.0
BC_LO, BC_HI, BC_STEP = -50.0, 50.0, 2.0

bs_arr = np.arange(BS_LO, BS_HI+0.5*BS_STEP, BS_STEP)
bc_arr = np.arange(BC_LO, BC_HI+0.5*BC_STEP, BC_STEP)
n_bs, n_bc = len(bs_arr), len(bc_arr)
n_cells = n_bs * n_bc
print("[grid] bs={}..{} step {} ({} pts); bc={}..{} step {} ({} pts); total={} cells".format(
    bs_arr.min(), bs_arr.max(), BS_STEP, n_bs,
    bc_arr.min(), bc_arr.max(), BC_STEP, n_bc, n_cells), flush=True)

print("[load] HC amplitudes ...", flush=True)
t0 = time.time()
hc_V4 = {s: load_amplitudes(LOCAL_DATA, s, "V4") for s in HC_POOL}
hc_V1 = {s: load_amplitudes(LOCAL_DATA, s, "V1") for s in HC_POOL}
for s in HC_POOL:
    print("  sub-{}: V4={} V1={}".format(s, hc_V4[s].shape, hc_V1[s].shape), flush=True)
print("  load time={:.2f}s".format(time.time()-t0), flush=True)

BS, BC = np.meshgrid(bs_arr, bc_arr, indexing="ij")
Tikh = (BS/BS_MAX)**2 + (BC/BC_MAX)**2

summary = {}
for subj in ["08","09"]:
    fam = CVD_TYPE[subj]
    print("\n=== sub-{} ({}) wretrained sweep ===".format(subj, fam), flush=True)
    v4t = np.asarray(load_cvd_loco_target(subj,"V4"))
    v1t = np.asarray(load_cvd_loco_target(subj,"V1"))
    print("[target] V4: {}".format(np.round(v4t,3).tolist()), flush=True)
    print("[target] V1: {}".format(np.round(v1t,3).tolist()), flush=True)

    l_topk = np.full((n_bs,n_bc), np.nan)
    l_rank = np.full((n_bs,n_bc), np.nan)
    spear_v4 = np.full((n_bs,n_bc), np.nan)
    spear_v1 = np.full((n_bs,n_bc), np.nan)
    vuln_V4 = np.full((n_bs,n_bc,N_COLORS), np.nan)
    vuln_V1 = np.full((n_bs,n_bc,N_COLORS), np.nan)

    t_start = time.time()
    done = 0
    snap_path = OUT_DIR / ".partial_sub-{}_wretrained.json".format(subj)
    for i, bs in enumerate(bs_arr):
        for j, bc in enumerate(bc_arr):
            C_sh,_ = get_2component_design(float(bs), float(bc), fam)
            v_v4,_ = simulate_mean_hc_loco_legacy(hc_V4, C_sh)
            v_v1,_ = simulate_mean_hc_loco_legacy(hc_V1, C_sh)
            m4 = compute_extended_loss(v_v4, v4t)
            m1 = compute_extended_loss(v_v1, v1t)
            l_topk[i,j] = m4["l_topk_jaccard"]
            l_rank[i,j] = m1["l_rank"]
            spear_v4[i,j] = m4["spearman_r"]
            spear_v1[i,j] = m1["spearman_r"]
            vuln_V4[i,j,:] = v_v4
            vuln_V1[i,j,:] = v_v1
            done += 1
            if done % 50 == 0:
                el = time.time() - t_start
                eta = el/done * (n_cells-done)
                print("[sub-{}] {}/{} elapsed={:.0f}s eta={:.0f}s rate={:.1f}c/s".format(subj, done, n_cells, el, eta, done/el), flush=True)
            if done % 200 == 0:
                L_part = ALPHA*l_topk + BETA*l_rank + LAM*Tikh
                with open(snap_path,"w") as f:
                    json.dump({"subject": subj, "progress": {"done": done, "total": n_cells}, "bs": bs_arr.tolist(), "bc": bc_arr.tolist(), "l_topk_V4": l_topk.tolist(), "l_rank_V1": l_rank.tolist(), "L_total": L_part.tolist()}, f)
    el = time.time() - t_start
    print("[sub-{}] done {} cells in {:.1f}s ({:.1f}ms/cell)".format(subj, n_cells, el, el/n_cells*1000), flush=True)

    L_total = ALPHA*l_topk + BETA*l_rank + LAM*Tikh
    idx = np.unravel_index(np.nanargmin(L_total), L_total.shape)
    i, j = int(idx[0]), int(idx[1])
    best = {
        "bs": float(bs_arr[i]), "bc": float(bc_arr[j]),
        "L_total": float(L_total[i,j]),
        "l_topk_V4": float(l_topk[i,j]),
        "l_rank_V1": float(l_rank[i,j]),
        "tikh": float(LAM*Tikh[i,j]),
        "spearman_r_V4": float(spear_v4[i,j]),
        "spearman_r_V1": float(spear_v1[i,j]),
        "vuln_sim_V4": [float(x) for x in vuln_V4[i,j]],
        "vuln_sim_V1": [float(x) for x in vuln_V1[i,j]],
    }
    print("[sub-{}] argmin: (bs={:.0f}, bc={:+.0f}) L={:.4f} l_topk_V4={:.3f} l_rank_V1={:.3f}".format(subj, best["bs"], best["bc"], best["L_total"], best["l_topk_V4"], best["l_rank_V1"]), flush=True)

    cells = []
    for ii in range(n_bs):
        for jj in range(n_bc):
            cells.append({
                "bs": float(bs_arr[ii]), "bc": float(bc_arr[jj]),
                "l_topk_V4": float(l_topk[ii,jj]),
                "l_rank_V1": float(l_rank[ii,jj]),
                "tikh": float(LAM*Tikh[ii,jj]),
                "l_total": float(L_total[ii,jj]),
                "spearman_r_V4": float(spear_v4[ii,jj]),
                "spearman_r_V1": float(spear_v1[ii,jj]),
                "vuln_sim_V4": [float(x) for x in vuln_V4[ii,jj]],
                "vuln_sim_V1": [float(x) for x in vuln_V1[ii,jj]],
            })
    payload = {
        "meta": {
            "cycle": 12,
            "simulator": "wretrained (simulate_mean_hc_loco_legacy, shift_at_both)",
            "loss": "L_total = alpha*l_topk_jaccard(V4) + beta*l_rank(V1) + lambda*Tikh",
            "alpha": ALPHA, "beta": BETA, "lambda": LAM,
            "tikh_normalization": "(bs/80)^2 + (bc/60)^2",
            "hc_pool": HC_POOL,
            "grid": {
                "bs": bs_arr.tolist(), "bc": bc_arr.tolist(),
                "shape": [n_bs, n_bc], "n_cells": int(L_total.size),
                "bs_bounds": [BS_LO, BS_HI, BS_STEP],
                "bc_bounds": [BC_LO, BC_HI, BC_STEP],
            },
            "roi_topk": "V4", "roi_rank": "V1",
            "cvd_type": CVD_TYPE[subj],
            "elapsed_s": el,
        },
        "argmin": best,
        "vuln_cvd_V4": v4t.tolist(),
        "vuln_cvd_V1": v1t.tolist(),
        "cells": cells,
    }
    out_path = OUT_DIR / "sub-{}_V4V1_cycle12_wretrained_landscape.json".format(subj)
    with open(out_path, "w") as f:
        json.dump(payload, f)
    print("[sub-{}] wrote {}".format(subj, out_path.name), flush=True)
    if snap_path.exists():
        os.remove(snap_path)
    summary[subj] = {
        "best": best,
        "l_total_min": float(np.nanmin(L_total)),
        "l_total_max": float(np.nanmax(L_total)),
        "l_total_median": float(np.nanmedian(L_total)),
        "elapsed_s": el,
    }

sjson = OUT_DIR / "cycle12_wretrained_recompute_summary.json"
with open(sjson,"w") as f:
    json.dump(summary, f, indent=2)
print("\n[done] wrote {}".format(sjson), flush=True)
log_f.close()
