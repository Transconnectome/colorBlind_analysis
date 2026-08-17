"""resumable wretrained runner v2."""
import sys, time, json, os
sys.path.insert(0, "/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/future_phase2_filter_optimization/scripts")
sys.path.insert(0, "/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/future_phase2_filter_optimization/scripts/older_cycles/cycle_loss_redesign")
sys.path.insert(0, "/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/future_phase1_forward_model/scripts")
import numpy as np
from pathlib import Path
from utils_forward_model import load_amplitudes, N_COLORS
from step1_fit_loco_v2 import simulate_mean_hc_loco_legacy, load_cvd_loco_target
from loss_redesign_smoke import get_2component_design, compute_extended_loss
LOCAL_DATA = Path("/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/phase1_procrustes_decoding/results/visualization/full_dataset_C010_with_residuals")
OUT_DIR = Path("/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/future_phase2_filter_optimization/results/fixedW_onlyTest")
LOG_PATH = OUT_DIR / ".wretrained_sweep.log"
log_f = open(LOG_PATH, "a"); sys.stdout = log_f; sys.stderr = log_f
SUBJ_ARG = sys.argv[1] if len(sys.argv) > 1 else "08"
HC_POOL = ["01","02","03","04","05","06","07"]
CVD_TYPE = {"08":"deutan","09":"protan"}
ALPHA, BETA, LAM = 1.0, 1.0, 0.2
BS_MAX, BC_MAX = 80.0, 60.0
bs_arr = np.arange(0.0, 50.5, 2.0)
bc_arr = np.arange(-50.0, 50.5, 2.0)
n_bs, n_bc = len(bs_arr), len(bc_arr); n_cells = n_bs*n_bc
BS, BC = np.meshgrid(bs_arr, bc_arr, indexing="ij"); Tikh = (BS/BS_MAX)**2 + (BC/BC_MAX)**2
print("[v2 start] subj=%s grid=%d" % (SUBJ_ARG, n_cells), flush=True)
subj = SUBJ_ARG; fam = CVD_TYPE[subj]
out_landscape = OUT_DIR / ("sub-%s_V4V1_cycle12_wretrained_landscape.json" % subj)
if out_landscape.exists():
    print("[sub-%s] final landscape exists already; skip" % subj, flush=True); sys.exit(0)
cache_path = OUT_DIR / (".cells_sub-%s_wretrained.jsonl" % subj)
cells_done = {}
if cache_path.exists():
    with open(cache_path) as f:
        for line in f:
            c = json.loads(line); cells_done[(c["bs"],c["bc"])] = c
    print("[sub-%s] resumed: %d cached" % (subj, len(cells_done)), flush=True)
t0 = time.time()
hc_V4 = {s: load_amplitudes(LOCAL_DATA, s, "V4") for s in HC_POOL}
hc_V1 = {s: load_amplitudes(LOCAL_DATA, s, "V1") for s in HC_POOL}
print("[load] %.2fs" % (time.time()-t0), flush=True)
v4t = np.asarray(load_cvd_loco_target(subj,"V4"))
v1t = np.asarray(load_cvd_loco_target(subj,"V1"))
cache_f = open(cache_path, "a")
t_start = time.time()
initial_done = len(cells_done); done = initial_done
try:
    for i, bs in enumerate(bs_arr):
        for j, bc in enumerate(bc_arr):
            key = (float(bs), float(bc))
            if key in cells_done: continue
            C_sh,_ = get_2component_design(float(bs), float(bc), fam)
            v_v4,_ = simulate_mean_hc_loco_legacy(hc_V4, C_sh)
            v_v1,_ = simulate_mean_hc_loco_legacy(hc_V1, C_sh)
            m4 = compute_extended_loss(v_v4, v4t)
            m1 = compute_extended_loss(v_v1, v1t)
            cell = {"bs": float(bs), "bc": float(bc),
                "l_topk_V4": float(m4["l_topk_jaccard"]), "l_rank_V1": float(m1["l_rank"]),
                "spearman_r_V4": float(m4["spearman_r"]), "spearman_r_V1": float(m1["spearman_r"]),
                "vuln_sim_V4": [float(x) for x in v_v4], "vuln_sim_V1": [float(x) for x in v_v1]}
            cells_done[key] = cell
            cache_f.write(json.dumps(cell)+"\n"); cache_f.flush(); os.fsync(cache_f.fileno())
            done += 1
            if (done-initial_done) % 50 == 0:
                el = time.time()-t_start
                eta = el / max(done-initial_done,1) * (n_cells-done)
                print("[sub-%s] %d/%d el=%.0fs eta=%.0fs r=%.2fc/s" % (subj, done, n_cells, el, eta, (done-initial_done)/el), flush=True)
finally:
    cache_f.close()
# build final landscape from cells_done
l_topk = np.full((n_bs,n_bc), np.nan); l_rank = np.full((n_bs,n_bc), np.nan)
spear_v4 = np.full((n_bs,n_bc), np.nan); spear_v1 = np.full((n_bs,n_bc), np.nan)
vuln_V4 = np.full((n_bs,n_bc,N_COLORS), np.nan); vuln_V1 = np.full((n_bs,n_bc,N_COLORS), np.nan)
for i, bs in enumerate(bs_arr):
    for j, bc in enumerate(bc_arr):
        c = cells_done.get((float(bs), float(bc)))
        if c is None: continue
        l_topk[i,j] = c["l_topk_V4"]; l_rank[i,j] = c["l_rank_V1"]
        spear_v4[i,j] = c["spearman_r_V4"]; spear_v1[i,j] = c["spearman_r_V1"]
        vuln_V4[i,j,:] = c["vuln_sim_V4"]; vuln_V1[i,j,:] = c["vuln_sim_V1"]
if np.isnan(l_topk).any():
    n_missing = int(np.isnan(l_topk).sum())
    print("[sub-%s] INCOMPLETE %d cells missing; rerun to finish" % (subj, n_missing), flush=True)
    sys.exit(0)
L_total = ALPHA*l_topk + BETA*l_rank + LAM*Tikh
idx = np.unravel_index(np.nanargmin(L_total), L_total.shape)
i, j = int(idx[0]), int(idx[1])
best = {"bs": float(bs_arr[i]), "bc": float(bc_arr[j]),
    "L_total": float(L_total[i,j]), "l_topk_V4": float(l_topk[i,j]), "l_rank_V1": float(l_rank[i,j]),
    "tikh": float(LAM*Tikh[i,j]), "spearman_r_V4": float(spear_v4[i,j]), "spearman_r_V1": float(spear_v1[i,j]),
    "vuln_sim_V4": [float(x) for x in vuln_V4[i,j]], "vuln_sim_V1": [float(x) for x in vuln_V1[i,j]]}
print("[sub-%s] argmin: (bs=%.0f,bc=%+.0f) L=%.4f" % (subj, best["bs"], best["bc"], best["L_total"]), flush=True)
cells = []
for ii in range(n_bs):
    for jj in range(n_bc):
        cells.append({"bs": float(bs_arr[ii]), "bc": float(bc_arr[jj]),
            "l_topk_V4": float(l_topk[ii,jj]), "l_rank_V1": float(l_rank[ii,jj]),
            "tikh": float(LAM*Tikh[ii,jj]), "l_total": float(L_total[ii,jj]),
            "spearman_r_V4": float(spear_v4[ii,jj]), "spearman_r_V1": float(spear_v1[ii,jj]),
            "vuln_sim_V4": [float(x) for x in vuln_V4[ii,jj]],
            "vuln_sim_V1": [float(x) for x in vuln_V1[ii,jj]]})
payload = {"meta": {"cycle":12, "simulator":"wretrained (simulate_mean_hc_loco_legacy, shift_at_both)",
    "loss":"L_total = alpha*l_topk_jaccard(V4) + beta*l_rank(V1) + lambda*Tikh",
    "alpha":ALPHA,"beta":BETA,"lambda":LAM,"tikh_normalization":"(bs/80)^2 + (bc/60)^2","hc_pool":HC_POOL,
    "grid":{"bs":bs_arr.tolist(),"bc":bc_arr.tolist(),"shape":[n_bs,n_bc],"n_cells":int(L_total.size),"bs_bounds":[0.0,50.0,2.0],"bc_bounds":[-50.0,50.0,2.0]},
    "roi_topk":"V4","roi_rank":"V1","cvd_type":CVD_TYPE[subj]},
    "argmin":best,"vuln_cvd_V4":v4t.tolist(),"vuln_cvd_V1":v1t.tolist(),"cells":cells}
with open(out_landscape,"w") as f: json.dump(payload, f)
print("[sub-%s] wrote %s" % (subj, out_landscape.name), flush=True)
log_f.close()
