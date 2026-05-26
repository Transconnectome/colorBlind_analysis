"""S10c: sub-09 Top-1 vs Top-2 forward δθ cosine analysis.

Top-1 = γ_GB|RDM_|noLOCO + rc_DPS_lit  (Δλ=10, g_median=1.30)
Top-2 = γ_GB|RDM_|noLOCO + 2comp       (β_s_median=34, β_c_median=-8)

Both fit on the SAME single behavioral atom (L_γ_GB) — different model classes
should both reduce the same scalar constraint, but they parameterize stimulus
space differently. Question: do they produce δθ(c) 8-vectors that point in
similar or different directions?

The s10b_v2 JSON only stores summary stats (median/IQR), so we re-fit the 1000
HC subsets for THIS combo only and dump per-resample (g) for R+C, (β_s, β_c)
for 2-comp. RNG seed and subset order MATCH s10b's sub-09 path (seed = 43,
sorted(rng.choice(7, 5, replace=False)) per draw).

Outputs:
  results/s10_inclusion/sub09_top12_cosine.json
  results/s10_inclusion/sub09_top12_polar.png

Console: cosine at median params, cosine distribution stats, interpretation.
"""
import json
import sys
import time
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from rc_1dof import forward_rc, G_MIN, G_MAX, G_STEP
from two_comp import forward_2comp, BS_GRID, BC_GRID
from behav_loss import HC_JND_SUBJS, load_jnd_per_pair, PAIR_HUES
from s8_loo_train_test import jnd_baseline_from_pool, DELTA_LAMBDA_BY_FAMILY

OUT_DIR = SCRIPT_DIR.parent / "results" / "s10_inclusion"
OUT_DIR.mkdir(parents=True, exist_ok=True)

HC_SUBJS = ['sub-01', 'sub-02', 'sub-03', 'sub-04', 'sub-05', 'sub-06', 'sub-07']
N_RESAMPLES = 1000
SUBSET_SIZE = 5
SUBJECT = 'sub-09'
FAMILY = 'protan'
FOCAL_PAIR = 'green-blue'
GAMMA_PAIR_KEY = 'GB'   # green-blue
DL_TOP1 = DELTA_LAMBDA_BY_FAMILY[FAMILY]['DPS_lit']  # 10 nm
HUES = np.arange(0, 360, 45, dtype=float)


def g_grid():
    return np.arange(G_MIN, G_MAX + G_STEP / 2, G_STEP)


# ---------------------------------------------------------------------------
# Atom — green-blue γ ratio loss (mirrors s10b's make_gamma_pair_atom for 'GB')
# ---------------------------------------------------------------------------

def make_gb_atom(cvd_jnd, train_jnd):
    pair_name = PAIR_HUES['green-blue']   # (135, 225)
    bl, sd = jnd_baseline_from_pool(train_jnd)
    if 'green-blue' not in bl or cvd_jnd.get('green-blue') is None:
        return None
    p_obs = cvd_jnd['green-blue']
    p_base = bl['green-blue']
    p_sd = max(sd['green-blue'], 1e-3)
    theta_a, theta_b = pair_name
    i = int(round(theta_a / 45.0)) % 8
    j = int(round(theta_b / 45.0)) % 8

    def loss_fn(delta_8vec):
        perceived = (HUES + delta_8vec) % 360.0
        d_phys = min(abs(theta_a - theta_b) % 360,
                     360 - abs(theta_a - theta_b) % 360)
        d_perc_raw = abs(perceived[i] - perceived[j]) % 360
        d_perc = max(min(d_perc_raw, 360 - d_perc_raw), 1e-3)
        pred = p_base * (d_phys / d_perc)
        return ((pred - p_obs) / p_sd) ** 2
    return loss_fn


def grid_eval_rc(loss_fn, dl, family):
    grid = g_grid()
    out = np.zeros(len(grid))
    for k, g in enumerate(grid):
        delta = forward_rc(dl, g, family)
        try:
            v = float(loss_fn(delta))
            out[k] = v if np.isfinite(v) else np.nan
        except Exception:
            out[k] = np.nan
    return out


def grid_eval_2comp(loss_fn, family):
    out = np.zeros((len(BS_GRID), len(BC_GRID)))
    for i, bs in enumerate(BS_GRID):
        for j, bc in enumerate(BC_GRID):
            delta = forward_2comp(bs, bc, family)
            try:
                v = float(loss_fn(delta))
                out[i, j] = v if np.isfinite(v) else np.nan
            except Exception:
                out[i, j] = np.nan
    return out


def argmin_rc(arr):
    if np.all(np.isnan(arr)):
        return None
    grid = g_grid()
    idx = int(np.nanargmin(arr))
    return {'g': float(grid[idx]),
            'boundary': bool(idx == 0 or idx == len(grid) - 1)}


def argmin_2c(arr):
    if np.all(np.isnan(arr)):
        return None
    flat = int(np.nanargmin(arr.ravel()))
    i, j = np.unravel_index(flat, arr.shape)
    return {'bs': float(BS_GRID[i]), 'bc': float(BC_GRID[j]),
            'boundary': bool(i == 0 or i == len(BS_GRID) - 1 or
                              j == 0 or j == len(BC_GRID) - 1)}


def cos_safe(a, b):
    na = np.linalg.norm(a); nb = np.linalg.norm(b)
    if na < 1e-9 or nb < 1e-9:
        return np.nan
    return float(np.dot(a, b) / (na * nb))


def main():
    t0 = time.time()
    cvd_jnd = load_jnd_per_pair(SUBJECT)

    # RNG seed and subset order MUST match s10b sub-09 path:
    #   rng = np.random.default_rng(RNG_SEED + (0 if 'sub-08' else 1)) = seed 43
    rng = np.random.default_rng(42 + 1)
    resample_subsets = []
    for _ in range(N_RESAMPLES):
        sel = rng.choice(len(HC_SUBJS), size=SUBSET_SIZE, replace=False)
        subset = [HC_SUBJS[i] for i in sorted(sel)]
        complement = [h for h in HC_SUBJS if h not in subset]
        resample_subsets.append((subset, complement))

    print(f"[{SUBJECT}] re-fitting γ_GB-only combo, both models, N={N_RESAMPLES}")
    print(f"  Δλ Top-1 = {DL_TOP1} nm ({FAMILY}, DPS_lit)")

    g_list = []
    bs_list = []
    bc_list = []
    cos_list = []
    rc_focal = []
    c2_focal = []

    # focal test fn pre-build
    focal_theta_a, focal_theta_b = PAIR_HUES[FOCAL_PAIR]
    f_i = int(round(focal_theta_a / 45.0)) % 8
    f_j = int(round(focal_theta_b / 45.0)) % 8
    focal_d_phys = min(abs(focal_theta_a - focal_theta_b) % 360,
                       360 - abs(focal_theta_a - focal_theta_b) % 360)
    focal_obs = cvd_jnd.get(FOCAL_PAIR) if cvd_jnd else None

    for draw_idx, (subset, complement) in enumerate(resample_subsets):
        train_jnd = [h for h in subset if h in HC_JND_SUBJS]
        test_jnd = [h for h in complement if h in HC_JND_SUBJS]
        if not train_jnd or not test_jnd:
            g_list.append(None); bs_list.append(None); bc_list.append(None)
            cos_list.append(None); rc_focal.append(None); c2_focal.append(None)
            continue

        # Build train-pool γ_GB atom
        atom = make_gb_atom(cvd_jnd, train_jnd)
        if atom is None:
            g_list.append(None); bs_list.append(None); bc_list.append(None)
            cos_list.append(None); rc_focal.append(None); c2_focal.append(None)
            continue

        # R+C
        rc_arr = grid_eval_rc(atom, DL_TOP1, FAMILY)
        rc_fit = argmin_rc(rc_arr)

        # 2-comp
        c2_arr = grid_eval_2comp(atom, FAMILY)
        c2_fit = argmin_2c(c2_arr)

        if rc_fit is None or c2_fit is None:
            g_list.append(None); bs_list.append(None); bc_list.append(None)
            cos_list.append(None); rc_focal.append(None); c2_focal.append(None)
            continue

        g_list.append(rc_fit['g'])
        bs_list.append(c2_fit['bs'])
        bc_list.append(c2_fit['bc'])

        d_rc = forward_rc(DL_TOP1, rc_fit['g'], FAMILY)
        d_c2 = forward_2comp(c2_fit['bs'], c2_fit['bc'], FAMILY)
        cos_list.append(cos_safe(d_rc, d_c2))

        # focal test on test_jnd
        test_bl, test_sd = jnd_baseline_from_pool(test_jnd)
        focal_base = test_bl.get(FOCAL_PAIR)
        focal_sd_v = max(test_sd.get(FOCAL_PAIR, 1.0), 1e-3) if FOCAL_PAIR in test_sd else None
        if focal_obs is not None and focal_base is not None and focal_sd_v is not None:
            for d, lst in [(d_rc, rc_focal), (d_c2, c2_focal)]:
                perceived = (HUES + d) % 360.0
                dp_raw = abs(perceived[f_i] - perceived[f_j]) % 360
                d_perc = max(min(dp_raw, 360 - dp_raw), 1e-3)
                pred = focal_base * (focal_d_phys / d_perc)
                lst.append(float(((pred - focal_obs) / focal_sd_v) ** 2))
        else:
            rc_focal.append(None); c2_focal.append(None)

        if (draw_idx + 1) % 200 == 0:
            elapsed = time.time() - t0
            eta = elapsed * (N_RESAMPLES - draw_idx - 1) / (draw_idx + 1)
            print(f"  [{draw_idx + 1}/{N_RESAMPLES}] elapsed={elapsed:.0f}s eta={eta:.0f}s")

    # --- Sanity check vs s10b ---
    def med_iqr(arr):
        a = np.array([x for x in arr if x is not None and np.isfinite(x)])
        if len(a) == 0:
            return None, None
        return float(np.median(a)), float(np.percentile(a, 75) - np.percentile(a, 25))

    g_med, g_iqr = med_iqr(g_list)
    bs_med, bs_iqr = med_iqr(bs_list)
    bc_med, bc_iqr = med_iqr(bc_list)
    rc_focal_med, rc_focal_iqr = med_iqr(rc_focal)
    c2_focal_med, c2_focal_iqr = med_iqr(c2_focal)

    print(f"\n[sanity vs s10b] R+C g_median: re-fit={g_med:.3f} (IQR {g_iqr:.3f}) | "
          f"s10b=1.300 (IQR 0.150)")
    print(f"[sanity vs s10b] 2-comp β_s: re-fit={bs_med:.2f} (IQR {bs_iqr:.2f}) | "
          f"s10b=34.00 (IQR 18.00)")
    print(f"[sanity vs s10b] 2-comp β_c: re-fit={bc_med:.2f} (IQR {bc_iqr:.2f}) | "
          f"s10b=-8.00 (IQR 42.00)")
    print(f"[sanity vs s10b] R+C focal: re-fit={rc_focal_med:.3f} | s10b=0.640")
    print(f"[sanity vs s10b] 2comp focal: re-fit={c2_focal_med:.3f} | s10b=0.646")

    # --- Cosine analyses ---
    # 1. Median-param cosine
    d_rc_med = forward_rc(DL_TOP1, g_med, FAMILY)
    d_c2_med = forward_2comp(bs_med, bc_med, FAMILY)
    cos_at_median = cos_safe(d_rc_med, d_c2_med)
    # 2. Per-resample cosine distribution
    cos_arr = np.array([c for c in cos_list if c is not None and np.isfinite(c)])
    cos_med = float(np.median(cos_arr))
    cos_iqr = float(np.percentile(cos_arr, 75) - np.percentile(cos_arr, 25))
    cos_p05 = float(np.percentile(cos_arr, 5))
    cos_p95 = float(np.percentile(cos_arr, 95))
    cos_mean = float(np.mean(cos_arr))
    cos_sd = float(np.std(cos_arr, ddof=1))
    frac_above_08 = float(np.mean(cos_arr > 0.8))
    frac_above_05 = float(np.mean(cos_arr > 0.5))
    frac_below_05 = float(np.mean(cos_arr < 0.5))
    frac_below_0  = float(np.mean(cos_arr < 0.0))

    print(f"\n=== COSINE SIMILARITY (Top-1 R+C vs Top-2 2-comp δθ 8-vec) ===")
    print(f"  At median params:        cos = {cos_at_median:+.4f}")
    print(f"  Per-resample (n={len(cos_arr)}):")
    print(f"    median = {cos_med:+.4f}  IQR = {cos_iqr:.4f}")
    print(f"    mean   = {cos_mean:+.4f}  SD  = {cos_sd:.4f}")
    print(f"    5th–95th pct = [{cos_p05:+.4f}, {cos_p95:+.4f}]")
    print(f"    fraction(cos > 0.80) = {frac_above_08:.3f}  (\"similar direction\")")
    print(f"    fraction(cos > 0.50) = {frac_above_05:.3f}")
    print(f"    fraction(cos < 0.50) = {frac_below_05:.3f}  (\"different direction\")")
    print(f"    fraction(cos < 0.00) = {frac_below_0 :.3f}  (\"opposite half-plane\")")

    # Interpretation
    if cos_at_median > 0.8 and frac_above_08 > 0.5:
        verdict = ("SIMILAR direction at median AND robust across HC resamples "
                   "(>50% of draws have cos > 0.8). Two mechanisms produce "
                   "near-coincident δθ(c).")
    elif cos_at_median > 0.5:
        verdict = ("MODERATE similarity at median; check IQR/p05-p95 to see if "
                   "the agreement is sample-dependent. If frac(cos<0.5) > 0.25 "
                   "the agreement is fragile.")
    elif abs(cos_at_median) < 0.3:
        verdict = ("NEAR-ORTHOGONAL δθ vectors. The two models reduce the same "
                   "scalar γ_GB constraint via essentially independent stimulus-"
                   "space distortions. Cosine of ~0 means the 7 non-GB color "
                   "shifts move in unrelated directions between R+C and 2-comp.")
    elif cos_at_median < -0.5:
        verdict = ("OPPOSITE direction — the two models point δθ(c) in negatively "
                   "correlated directions. They fit the same green-blue pair via "
                   "antiparallel filter prescriptions.")
    else:
        verdict = ("WEAK negative similarity; not interpretable as agreement.")

    print(f"\n  VERDICT: {verdict}")

    # --- JSON dump ---
    out = {
        'subject': SUBJECT,
        'family': FAMILY,
        'top1': {'model': 'rc_DPS_lit', 'delta_lambda_nm': DL_TOP1,
                 'param_median': {'g': g_med, 'g_iqr': g_iqr},
                 'focal_median': rc_focal_med, 'focal_iqr': rc_focal_iqr,
                 'delta_theta_at_median': d_rc_med.tolist()},
        'top2': {'model': '2comp',
                 'param_median': {'bs': bs_med, 'bs_iqr': bs_iqr,
                                  'bc': bc_med, 'bc_iqr': bc_iqr},
                 'focal_median': c2_focal_med, 'focal_iqr': c2_focal_iqr,
                 'delta_theta_at_median': d_c2_med.tolist()},
        'cosine': {
            'at_median_params': cos_at_median,
            'n_resamples': int(len(cos_arr)),
            'median': cos_med, 'iqr': cos_iqr,
            'mean': cos_mean, 'sd': cos_sd,
            'pct_05': cos_p05, 'pct_95': cos_p95,
            'frac_above_080': frac_above_08,
            'frac_above_050': frac_above_05,
            'frac_below_050': frac_below_05,
            'frac_below_000': frac_below_0,
            'distribution': cos_arr.tolist(),
        },
        'sanity_vs_s10b': {
            's10b_top1_g_median': 1.30, 's10b_top1_g_iqr': 0.15,
            's10b_top1_focal_median': 0.640,
            's10b_top2_bs_median': 34.0, 's10b_top2_bs_iqr': 18.0,
            's10b_top2_bc_median': -8.0, 's10b_top2_bc_iqr': 42.0,
            's10b_top2_focal_median': 0.646,
        },
        'verdict': verdict,
        'hues_deg': HUES.tolist(),
        'elapsed_sec': round(time.time() - t0, 1),
    }
    out_json = OUT_DIR / "sub09_top12_cosine.json"
    with open(out_json, 'w') as f:
        json.dump(out, f, indent=2)
    print(f"\nSaved: {out_json}")

    # --- Polar plot ---
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(1, 2, figsize=(12, 6),
                                  subplot_kw={'projection': 'polar'})

        # Left: δθ vectors as length-on-radial axis at 8 hues
        ax = axes[0]
        hues_rad = np.deg2rad(HUES)
        # Plot bars of |δθ| with sign as color
        for i, h in enumerate(hues_rad):
            ax.plot([h, h], [0, d_rc_med[i]], color='C0', lw=3,
                     label='Top1 R+C' if i == 0 else None)
            ax.plot([h, h], [0, d_c2_med[i]], color='C3', lw=2, ls='--',
                     label='Top2 2-comp' if i == 0 else None)
            ax.plot(h, d_rc_med[i], 'o', color='C0', ms=8)
            ax.plot(h, d_c2_med[i], 's', color='C3', ms=8)
        ax.set_theta_zero_location('E')
        ax.set_theta_direction(1)  # counter-clockwise (matches HUE convention)
        ax.set_title(f'δθ(c) at median params\n'
                      f'R+C g={g_med:.2f}, 2comp (β_s={bs_med:.0f}, β_c={bc_med:.0f})\n'
                      f'cos(median) = {cos_at_median:+.3f}', fontsize=10)
        ax.legend(loc='upper right', bbox_to_anchor=(1.25, 1.10), fontsize=9)
        # Mark color labels
        color_names = ['red', 'orange', 'yellow', 'green', 'cyan', 'blue',
                        'purple', 'magenta']
        ax.set_xticks(hues_rad)
        ax.set_xticklabels(color_names, fontsize=8)

        # Right: cosine distribution histogram (polar = a non-projection sub)
        ax2 = axes[1]
        ax2.remove()
        ax2 = fig.add_subplot(1, 2, 2)
        ax2.hist(cos_arr, bins=50, color='gray', edgecolor='black', alpha=0.7)
        ax2.axvline(cos_at_median, color='C0', lw=2,
                     label=f'cos@median = {cos_at_median:+.3f}')
        ax2.axvline(cos_med, color='C3', lw=2, ls='--',
                     label=f'median of cos = {cos_med:+.3f}')
        ax2.axvline(0.8, color='green', lw=1, ls=':', alpha=0.6)
        ax2.axvline(0.5, color='orange', lw=1, ls=':', alpha=0.6)
        ax2.axvline(0.0, color='red', lw=1, ls=':', alpha=0.6)
        ax2.set_xlabel('cosine(Top-1 δθ, Top-2 δθ)')
        ax2.set_ylabel(f'count (n={len(cos_arr)} resamples)')
        ax2.set_title(f'Per-resample cosine\n'
                      f'IQR={cos_iqr:.3f}, [5–95]=[{cos_p05:+.2f},{cos_p95:+.2f}]\n'
                      f'frac>0.8={frac_above_08:.2f}, <0.5={frac_below_05:.2f}',
                      fontsize=10)
        ax2.legend(fontsize=9)
        ax2.grid(True, alpha=0.3)

        plt.suptitle(f'sub-09 Top-1 (R+C) vs Top-2 (2-comp) — same γ_GB atom, '
                      f'different mechanism', fontsize=11)
        plt.tight_layout()
        out_png = OUT_DIR / "sub09_top12_polar.png"
        plt.savefig(out_png, dpi=150, bbox_inches='tight')
        print(f"Saved: {out_png}")
    except Exception as e:
        print(f"[viz] failed: {e}")

    print(f"\nTotal elapsed: {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
