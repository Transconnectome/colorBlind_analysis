"""fig2_rdm_fit.py — Publication figure: 2-Component model RDM fit quality.

Shows the observed vs. predicted ΔRDM for two CVD subjects, using the EXACT
canonical PCA-K6 correlation-RDM atom from s10b_v6_pca_rdm.make_rdm_atom and
the closure 2-Component forward (two_comp.forward_2comp, A13).

Canonical facts (PIPELINE_2_CLOSURE.md §3 / CLAUDE.md A13):
  - 2-Component forward: δθ(θ)=β_s·cos(θ−90°)+β_c·cos(θ−θ_conf)
        θ_conf protan=16°, deutan=150°
  - sub-08 (deutan): (β_s=+6, β_c=−42), RDM atom on ROI V2
  - sub-09 (protan): (β_s=+2, β_c=+24), RDM atom on ROI V1
  - HC pool = 7 HC subjects (sub-01..07), full pool (load_hc_pool).

Construction (matches s10b make_rdm_atom exactly):
  - PCA top-K=6 voxel scores per (HC, color) mean pattern → 8×8 correlation-RDM
  - HC mean RDM = mean over 7 HC RDMs
  - observed ΔRDM = RDM(CVD) − HC_mean_RDM            (28-d upper triangle)
  - predicted ΔRDM = sim_shifted − HC_mean_RDM, where
        sim_shifted[i,j] = HC_mean_RDM[round(perceived_i/45)%8, round(perceived_j/45)%8]
        perceived = (canonical_hue + δθ) % 360       (forward-synthesized CVD via 2-comp)

This script does NOT fabricate any number. The cosine printed is verified to
match (1 − make_rdm_atom(...)(delta)) to ~1e-9.
"""
from __future__ import annotations
import shutil
import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
from scipy.spatial.distance import squareform

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from two_comp import forward_2comp
from neural_loss import load_amplitudes, load_hc_pool, ROI_K
from utils_forward_model import create_basis_full, HUE_ANGLES
from s10b_v6_pca_rdm import make_rdm_atom

OUT_DIR = SCRIPT_DIR.parent / "results" / "visualizations" / "fig2_rdm_fit"
OUT_DIR.mkdir(parents=True, exist_ok=True)
ICML_FIG_DIR = (SCRIPT_DIR.parents[2] / "docs" / "ICML_workshop" / "figures")

HUES = np.arange(0, 360, 45, dtype=float)
HUE_LABELS = ["red", "orange", "yellow", "green",
              "cyan", "blue", "purple", "magenta"]
K_PCA = 6
TRIU = np.triu_indices(8, k=1)

SUBJECTS = [
    {"id": "08", "subject": "sub-08", "family": "deutan",
     "roi": "V2", "beta_s": 6.0, "beta_c": -42.0,
     "label": "sub-08 (deutan)"},
    {"id": "09", "subject": "sub-09", "family": "protan",
     "roi": "V1", "beta_s": 2.0, "beta_c": 24.0,
     "label": "sub-09 (protan)"},
]


# ---- Construction primitives (identical math to s10b make_rdm_atom) ----
def voxel_pca_components(pattern_8xV, k):
    mp = pattern_8xV - pattern_8xV.mean(axis=0, keepdims=True)
    try:
        U, S, Vt = np.linalg.svd(mp, full_matrices=False)
        k_eff = min(k, U.shape[1])
        return U[:, :k_eff] * S[:k_eff]
    except Exception:
        return mp[:, :k]


def compute_rdm_correlation(scores_8xk):
    n = scores_8xk.shape[0]
    out = np.zeros((n * (n - 1)) // 2)
    idx = 0
    for i in range(n):
        for j in range(i + 1, n):
            a, b = scores_8xk[i], scores_8xk[j]
            am = a - a.mean(); bm = b - b.mean()
            denom = (np.linalg.norm(am) * np.linalg.norm(bm))
            out[idx] = 1.0 - (am @ bm / denom if denom > 1e-9 else 0.0)
            idx += 1
    return out


def build_rdms(cvd_amp, pool_amps_dict, beta_s, beta_c, family):
    """Return (hc_mean_rdm 8x8, obs_dRDM 8x8, pred_dRDM 8x8, delta_8vec)."""
    # HC mean RDM (PC-space)
    hc_rdms = []
    for sid, amp in pool_amps_dict.items():
        mean_pat = amp.mean(axis=0)
        scores = voxel_pca_components(mean_pat, K_PCA)
        hc_rdms.append(squareform(compute_rdm_correlation(scores)))
    hc_rdm_mean = np.mean(np.stack(hc_rdms, axis=0), axis=0)

    # observed: CVD RDM − HC mean
    cvd_mean = cvd_amp.mean(axis=0)
    cvd_scores = voxel_pca_components(cvd_mean, K_PCA)
    cvd_rdm = squareform(compute_rdm_correlation(cvd_scores))
    obs_dRDM = cvd_rdm - hc_rdm_mean

    # predicted: forward-synthesized CVD = HC RDM relabeled by perceived hue
    delta = forward_2comp(beta_s, beta_c, family)
    perceived = (HUES + delta) % 360.0
    sim_shifted = np.zeros((8, 8))
    for i in range(8):
        for j in range(8):
            p_i = int(round(perceived[i] / 45.0)) % 8
            p_j = int(round(perceived[j] / 45.0)) % 8
            sim_shifted[i, j] = hc_rdm_mean[p_i, p_j]
    pred_dRDM = sim_shifted - hc_rdm_mean

    return hc_rdm_mean, obs_dRDM, pred_dRDM, delta


def main():
    print("=" * 80, flush=True)
    print("fig2_rdm_fit — 2-Component RDM fit quality (DATA figure)", flush=True)
    print("=" * 80, flush=True)

    rows = []  # collected per subject for plotting

    for cfg in SUBJECTS:
        subj, roi = cfg["subject"], cfg["roi"]
        bs, bc, fam = cfg["beta_s"], cfg["beta_c"], cfg["family"]
        print(f"\n[{subj}] {cfg['label']} · ROI={roi} · "
              f"(β_s={bs:+.0f}, β_c={bc:+.0f}) {fam}", flush=True)

        cvd_amp = load_amplitudes(subj, roi)
        pool = load_hc_pool(roi)
        assert len(pool) == 7, f"HC pool not 7 for {roi}: {sorted(pool.keys())}"
        C_b = create_basis_full(ROI_K[roi], basis_type='fe')[HUE_ANGLES.astype(int)]

        hc_mean, obs_dRDM, pred_dRDM, delta = build_rdms(
            cvd_amp, pool, bs, bc, fam)
        print(f"  δθ 8-vec: {np.round(delta, 2).tolist()}", flush=True)

        obs_vec = obs_dRDM[TRIU]
        pred_vec = pred_dRDM[TRIU]

        # cosine + Pearson on the same 28-d upper triangle
        n_obs = np.linalg.norm(obs_vec)
        n_pred = np.linalg.norm(pred_vec)
        cosine = float(obs_vec @ pred_vec / (n_obs * n_pred))
        pearson = float(np.corrcoef(obs_vec, pred_vec)[0, 1])

        # HARD CHECK: must match s10b make_rdm_atom (1 − loss)
        atom = make_rdm_atom(roi, cvd_amp, pool, C_b, ROI_K[roi])
        cos_s10b = 1.0 - float(atom(delta))
        assert abs(cosine - cos_s10b) < 1e-9, (
            f"cosine mismatch vs s10b: mine={cosine} s10b={cos_s10b}")
        print(f"  cosine(obs, pred) = {cosine:.6f}  "
              f"[s10b atom check = {cos_s10b:.6f}, Δ={abs(cosine-cos_s10b):.2e}]",
              flush=True)
        print(f"  Pearson r(obs, pred) = {pearson:.6f}", flush=True)

        cfg.update(dict(obs_dRDM=obs_dRDM, pred_dRDM=pred_dRDM,
                        obs_vec=obs_vec, pred_vec=pred_vec,
                        cosine=cosine, pearson=pearson))
        rows.append(cfg)

    # ---------------- Figure: 2 rows × 3 cols ----------------
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))

    # shared diverging scale across the 4 heatmaps, centered at 0
    all_vals = np.concatenate([np.concatenate([r["obs_dRDM"].ravel(),
                                               r["pred_dRDM"].ravel()])
                               for r in rows])
    vmax = float(np.max(np.abs(all_vals)))
    norm = TwoSlopeNorm(vmin=-vmax, vcenter=0.0, vmax=vmax)
    cmap = "RdBu_r"

    def heatmap(ax, M, title):
        im = ax.imshow(M, cmap=cmap, norm=norm)
        ax.set_xticks(range(8)); ax.set_yticks(range(8))
        ax.set_xticklabels(HUE_LABELS, rotation=45, ha="right", fontsize=8)
        ax.set_yticklabels(HUE_LABELS, fontsize=8)
        ax.set_title(title, fontsize=10)
        return im

    last_im = None
    for r, cfg in enumerate(rows):
        row_title = (f"{cfg['label']}  ·  ROI {cfg['roi']}  ·  "
                     f"(β_s={cfg['beta_s']:+.0f}, β_c={cfg['beta_c']:+.0f})")
        last_im = heatmap(axes[r, 0], cfg["obs_dRDM"],
                          f"Observed ΔRDM\n{row_title}")
        heatmap(axes[r, 1], cfg["pred_dRDM"], "Predicted ΔRDM (2-Component)")

        # scatter obs vs pred (28 points)
        ax = axes[r, 2]
        ax.scatter(cfg["obs_vec"], cfg["pred_vec"], s=28,
                   c="#33548f", edgecolors="white", linewidth=0.5, zorder=3)
        lim = max(np.max(np.abs(cfg["obs_vec"])),
                  np.max(np.abs(cfg["pred_vec"]))) * 1.1
        ax.plot([-lim, lim], [-lim, lim], "--", c="grey", lw=0.8, zorder=1)
        ax.axhline(0, c="lightgrey", lw=0.6, zorder=0)
        ax.axvline(0, c="lightgrey", lw=0.6, zorder=0)
        ax.set_xlim(-lim, lim); ax.set_ylim(-lim, lim)
        ax.set_xlabel("Observed ΔRDM (28-d)", fontsize=9)
        ax.set_ylabel("Predicted ΔRDM (28-d)", fontsize=9)
        ax.set_title(f"obs vs pred\ncosine={cfg['cosine']:.3f}  "
                     f"r={cfg['pearson']:.3f}", fontsize=10)
        ax.set_aspect("equal")

    cbar = fig.colorbar(last_im, ax=axes[:, :2].ravel().tolist(),
                        shrink=0.6, pad=0.02, label="ΔRDM (CVD − HC mean)")

    fig.suptitle("2-Component model RDM fit quality "
                 "(PCA-K6 correlation-RDM, 28-d upper triangle)",
                 fontsize=13, y=0.98)

    pdf_path = OUT_DIR / "fig2_rdm_fit.pdf"
    png_path = OUT_DIR / "fig2_rdm_fit.png"
    fig.savefig(pdf_path, bbox_inches="tight")
    fig.savefig(png_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"\nSaved: {pdf_path}", flush=True)
    print(f"Saved: {png_path}", flush=True)

    if ICML_FIG_DIR.exists():
        dest = ICML_FIG_DIR / "fig2_rdm_fit.pdf"
        shutil.copy(pdf_path, dest)
        print(f"Copied: {dest}", flush=True)
    else:
        print(f"WARNING: ICML figures dir not found: {ICML_FIG_DIR}", flush=True)

    print("\n=== VERIFICATION SUMMARY (real computed numbers) ===", flush=True)
    for cfg in rows:
        print(f"  {cfg['subject']} {cfg['family']:7s} ROI {cfg['roi']} "
              f"(β_s={cfg['beta_s']:+.0f}, β_c={cfg['beta_c']:+.0f})  "
              f"cosine={cfg['cosine']:.4f}  r={cfg['pearson']:.4f}", flush=True)


if __name__ == "__main__":
    main()
