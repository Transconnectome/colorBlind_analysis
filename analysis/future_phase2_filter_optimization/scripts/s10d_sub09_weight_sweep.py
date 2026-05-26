"""S10d: sub-09 (γ_GB + RDM_V1) 1-D weight sweep.

Composite loss: L_combo(δθ; w) = (1 − w) · z(L_γ_GB(δθ)) + w · z(L_RDM_V1(δθ))

w ∈ {0.0, 0.1, ..., 1.0} (11 points).

For each (w, resample, model):
  1. Build atom evaluators on TRAIN HC subset (size 5, seed 43 + 1)
  2. Z-score each atom's grid → z_GB(grid), z_RDM(grid)
  3. Composite = (1-w) · z_GB + w · z_RDM
  4. argmin → fitted param (g for R+C; β_s, β_c for 2-comp)
  5. Test L_γ_GB on complement HC (focal); track boundary

Outputs:
  results/s10_inclusion/sub09_weight_sweep.json    (per-w summary)
  results/s10_inclusion/sub09_weight_sweep.png     (focal/boundary plots)

w=0 should reproduce Top-1 (γ_GB alone): R+C g≈2.60 focal≈0.62; 2-comp (34,-8) focal≈0.65
w=1 should reproduce RDM_V1-alone:        R+C g≈2.20 focal large; 2-comp (2,+50) focal≈3.9
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
from neural_loss import load_amplitudes, load_hc_pool, ROI_K, L_RDM
from diagnostic_delta_rdm import precompute_hc_W
from behav_loss import HC_JND_SUBJS, load_jnd_per_pair, PAIR_HUES
from utils_forward_model import create_basis_full, HUE_ANGLES
from s8_loo_train_test import jnd_baseline_from_pool, DELTA_LAMBDA_BY_FAMILY
from s10b_v2_resample import (
    make_gamma_pair_atom, make_rdm_atom,
    grid_eval_rc, grid_eval_2comp,
    argmin_rc, argmin_2comp, zscore_grid,
)

OUT_DIR = SCRIPT_DIR.parent / "results" / "s10_inclusion"
OUT_DIR.mkdir(parents=True, exist_ok=True)

HC_SUBJS = ['sub-01', 'sub-02', 'sub-03', 'sub-04', 'sub-05', 'sub-06', 'sub-07']
N_RESAMPLES = 1000
SUBSET_SIZE = 5
SUBJECT = 'sub-09'
FAMILY = 'protan'
FOCAL_PAIR = 'green-blue'
DL = DELTA_LAMBDA_BY_FAMILY[FAMILY]['DPS_lit']  # 10 nm
ROI = 'V1'
HUES = np.arange(0, 360, 45, dtype=float)
W_GRID = np.linspace(0.0, 1.0, 11)


def median_safe(values):
    arr = np.array([v for v in values if v is not None and np.isfinite(v)])
    return float(np.median(arr)) if len(arr) else None


def iqr_safe(values):
    arr = np.array([v for v in values if v is not None and np.isfinite(v)])
    if len(arr) < 2:
        return None
    return float(np.percentile(arr, 75) - np.percentile(arr, 25))


def main():
    t0 = time.time()
    cvd_jnd = load_jnd_per_pair(SUBJECT)
    cvd_amp = load_amplitudes(SUBJECT, ROI)
    hc_amps_v1 = load_hc_pool(ROI)
    K_v1 = ROI_K[ROI]
    C_v1 = create_basis_full(K_v1, basis_type='fe')[HUE_ANGLES.astype(int)]

    print(f"[{SUBJECT}] weight sweep: γ_GB + RDM_V1, weights {W_GRID.tolist()}")
    print(f"  Δλ = {DL} nm ({FAMILY}, DPS_lit), V1 K = {K_v1}")

    rng = np.random.default_rng(42 + 1)
    resample_subsets = []
    for _ in range(N_RESAMPLES):
        sel = rng.choice(len(HC_SUBJS), size=SUBSET_SIZE, replace=False)
        subset = [HC_SUBJS[i] for i in sorted(sel)]
        complement = [h for h in HC_SUBJS if h not in subset]
        resample_subsets.append((subset, complement))

    focal_theta_a, focal_theta_b = PAIR_HUES[FOCAL_PAIR]
    f_i = int(round(focal_theta_a / 45.0)) % 8
    f_j = int(round(focal_theta_b / 45.0)) % 8
    focal_d_phys = min(abs(focal_theta_a - focal_theta_b) % 360,
                       360 - abs(focal_theta_a - focal_theta_b) % 360)
    focal_obs = cvd_jnd.get(FOCAL_PAIR)

    # Storage: per-w → per-model → list of (param, focal, bdy) dicts
    storage = {f"{w:.1f}": {
        'rc_DPS_lit': [], '2comp': []} for w in W_GRID}

    for draw_idx, (subset, complement) in enumerate(resample_subsets):
        train_jnd = [h for h in subset if h in HC_JND_SUBJS]
        test_jnd = [h for h in complement if h in HC_JND_SUBJS]
        if not train_jnd or not test_jnd:
            continue

        # Build atoms on TRAIN
        gb_atom = make_gamma_pair_atom('GB', cvd_jnd, train_jnd)
        if gb_atom is None:
            continue
        pool_amps = {h: hc_amps_v1[h] for h in subset if h in hc_amps_v1}
        if len(pool_amps) < 2:
            continue
        rdm_atom = make_rdm_atom(ROI, cvd_amp, pool_amps, C_v1, K_v1)
        if rdm_atom is None:
            continue

        # Pre-compute z-scored grids ONCE per draw, then sweep w
        rc_gb = grid_eval_rc(gb_atom, DL, FAMILY)
        rc_rdm = grid_eval_rc(rdm_atom, DL, FAMILY)
        c2_gb = grid_eval_2comp(gb_atom, FAMILY)
        c2_rdm = grid_eval_2comp(rdm_atom, FAMILY)

        z_rc_gb = zscore_grid(rc_gb)
        z_rc_rdm = zscore_grid(rc_rdm)
        z_c2_gb = zscore_grid(c2_gb)
        z_c2_rdm = zscore_grid(c2_rdm)
        if (np.all(np.isnan(z_rc_gb)) or np.all(np.isnan(z_rc_rdm)) or
                np.all(np.isnan(z_c2_gb)) or np.all(np.isnan(z_c2_rdm))):
            continue

        # Test pool for focal
        test_bl, test_sd = jnd_baseline_from_pool(test_jnd)
        focal_base = test_bl.get(FOCAL_PAIR)
        focal_sd_v = (max(test_sd.get(FOCAL_PAIR, 1.0), 1e-3)
                       if FOCAL_PAIR in test_sd else None)

        def test_focal(delta):
            if focal_obs is None or focal_base is None or focal_sd_v is None:
                return None
            perceived = (HUES + delta) % 360.0
            dp_raw = abs(perceived[f_i] - perceived[f_j]) % 360
            d_perc = max(min(dp_raw, 360 - dp_raw), 1e-3)
            pred = focal_base * (focal_d_phys / d_perc)
            return float(((pred - focal_obs) / focal_sd_v) ** 2)

        for w in W_GRID:
            wkey = f"{w:.1f}"
            # R+C composite
            comp_rc = (1.0 - w) * z_rc_gb + w * z_rc_rdm
            fit_rc = argmin_rc(comp_rc)
            d_rc = forward_rc(DL, fit_rc['g'], FAMILY)
            t_rc = test_focal(d_rc)
            storage[wkey]['rc_DPS_lit'].append({
                'g': fit_rc['g'],
                'boundary': fit_rc['boundary'],
                'focal': t_rc,
            })

            # 2-comp composite
            comp_c2 = (1.0 - w) * z_c2_gb + w * z_c2_rdm
            fit_c2 = argmin_2comp(comp_c2)
            d_c2 = forward_2comp(fit_c2['beta_s'], fit_c2['beta_c'], FAMILY)
            t_c2 = test_focal(d_c2)
            storage[wkey]['2comp'].append({
                'bs': fit_c2['beta_s'], 'bc': fit_c2['beta_c'],
                'boundary': fit_c2['boundary'],
                'focal': t_c2,
            })

        if (draw_idx + 1) % 200 == 0:
            elapsed = time.time() - t0
            eta = elapsed * (N_RESAMPLES - draw_idx - 1) / (draw_idx + 1)
            print(f"  [{draw_idx + 1}/{N_RESAMPLES}] elapsed={elapsed:.0f}s eta={eta:.0f}s")

    # Summarize per-w
    summary = {}
    print(f"\n{'='*100}")
    print(f"sub-09 weight sweep — γ_GB (w_GB = 1-w) + RDM_V1 (w_RDM = w)")
    print(f"{'='*100}")
    print(f"{'w':>5s} | {'model':>10s} | {'n':>4s} | {'param med':>16s} | "
          f"{'param IQR':>10s} | {'focal med':>10s} | {'focal IQR':>10s} | {'bdy':>5s}")
    print('-' * 100)

    for w in W_GRID:
        wkey = f"{w:.1f}"
        summary[wkey] = {}
        for model in ['rc_DPS_lit', '2comp']:
            fits = storage[wkey][model]
            if not fits:
                summary[wkey][model] = None
                continue
            focals = [f['focal'] for f in fits]
            bdys = [f.get('boundary', False) for f in fits]
            bdy_rate = float(np.mean(bdys)) if bdys else None
            f_med = median_safe(focals)
            f_iqr = iqr_safe(focals)
            if model.startswith('rc'):
                gs = [f['g'] for f in fits]
                pm = median_safe(gs); pi = iqr_safe(gs)
                param_str = f"g={pm:.3f}" if pm is not None else "NA"
                iqr_str = f"{pi:.3f}" if pi is not None else "NA"
                summary[wkey][model] = {
                    'n': len(fits), 'g_median': pm, 'g_iqr': pi,
                    'focal_median': f_med, 'focal_iqr': f_iqr,
                    'boundary_rate': bdy_rate,
                }
            else:
                bss = [f['bs'] for f in fits]
                bcs = [f['bc'] for f in fits]
                bs_m = median_safe(bss); bc_m = median_safe(bcs)
                bs_i = iqr_safe(bss); bc_i = iqr_safe(bcs)
                param_str = (f"({bs_m:.0f},{bc_m:+.0f})"
                              if bs_m is not None else "NA")
                iqr_str = (f"{bs_i:.0f}/{bc_i:.0f}"
                            if bs_i is not None else "NA")
                summary[wkey][model] = {
                    'n': len(fits),
                    'bs_median': bs_m, 'bc_median': bc_m,
                    'bs_iqr': bs_i, 'bc_iqr': bc_i,
                    'focal_median': f_med, 'focal_iqr': f_iqr,
                    'boundary_rate': bdy_rate,
                }
            f_med_s = f"{f_med:.3f}" if f_med is not None else "NA"
            f_iqr_s = f"{f_iqr:.2f}" if f_iqr is not None else "NA"
            bdy_s = f"{bdy_rate:.3f}" if bdy_rate is not None else "NA"
            print(f"{w:>5.1f} | {model:>10s} | {len(fits):>4d} | "
                  f"{param_str:>16s} | {iqr_str:>10s} | "
                  f"{f_med_s:>10s} | {f_iqr_s:>10s} | {bdy_s:>5s}")

    # Save JSON
    out = {
        'subject': SUBJECT, 'family': FAMILY,
        'delta_lambda_nm': DL,
        'rdm_roi': ROI, 'K_rdm': K_v1,
        'focal_pair': FOCAL_PAIR,
        'n_resamples': N_RESAMPLES,
        'weight_grid': W_GRID.tolist(),
        'summary': summary,
        'elapsed_sec': round(time.time() - t0, 1),
    }
    out_json = OUT_DIR / "sub09_weight_sweep.json"
    with open(out_json, 'w') as f:
        json.dump(out, f, indent=2)
    print(f"\nSaved: {out_json}")

    # Plot
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        ws = list(W_GRID)
        fig, axes = plt.subplots(2, 2, figsize=(13, 9))

        # 1) focal vs w, both models
        ax = axes[0, 0]
        for model, color, marker in [('rc_DPS_lit', 'C0', 'o'),
                                       ('2comp', 'C3', 's')]:
            f_med = [summary[f"{w:.1f}"][model]['focal_median']
                      if summary[f"{w:.1f}"][model] else np.nan for w in ws]
            f_iqr = [summary[f"{w:.1f}"][model]['focal_iqr']
                      if summary[f"{w:.1f}"][model] else np.nan for w in ws]
            ax.errorbar(ws, f_med, yerr=f_iqr, marker=marker, color=color,
                         label=model, capsize=3, lw=1.5)
        ax.set_xlabel('w (RDM_V1 weight; 1-w = γ_GB weight)')
        ax.set_ylabel('test L_γ_GB on complement HC (focal)')
        ax.set_title('focal test loss vs weight\n(median ± IQR)')
        ax.set_yscale('log')
        ax.axhline(0.64, color='gray', ls=':', alpha=0.5, label='Phase B Top-1/2 (≈0.64)')
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)

        # 2) boundary rate vs w
        ax = axes[0, 1]
        for model, color, marker in [('rc_DPS_lit', 'C0', 'o'),
                                       ('2comp', 'C3', 's')]:
            bdy = [summary[f"{w:.1f}"][model]['boundary_rate']
                    if summary[f"{w:.1f}"][model] else np.nan for w in ws]
            ax.plot(ws, bdy, marker=marker, color=color, label=model, lw=1.5)
        ax.set_xlabel('w (RDM_V1 weight; 1-w = γ_GB weight)')
        ax.set_ylabel('boundary rate')
        ax.set_title('Parameter boundary rate vs weight')
        ax.set_ylim(-0.05, 1.05)
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)

        # 3) R+C g vs w
        ax = axes[1, 0]
        g_med = [summary[f"{w:.1f}"]['rc_DPS_lit']['g_median']
                  if summary[f"{w:.1f}"]['rc_DPS_lit'] else np.nan for w in ws]
        g_iqr = [summary[f"{w:.1f}"]['rc_DPS_lit']['g_iqr']
                  if summary[f"{w:.1f}"]['rc_DPS_lit'] else np.nan for w in ws]
        ax.errorbar(ws, g_med, yerr=g_iqr, marker='o', color='C0',
                     capsize=3, lw=1.5)
        ax.axhline(2.0, color='gray', ls='--', alpha=0.5,
                    label='g=2 (full compensation)')
        ax.axhline(1.0, color='gray', ls=':', alpha=0.4,
                    label='g=1 (HC pass-through)')
        ax.set_xlabel('w (RDM_V1 weight)')
        ax.set_ylabel('R+C g (median ± IQR)')
        ax.set_title('R+C cortical gain g vs weight')
        ax.set_ylim(G_MIN - 0.1, G_MAX + 0.1)
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)

        # 4) 2-comp β_s, β_c vs w
        ax = axes[1, 1]
        bs_med = [summary[f"{w:.1f}"]['2comp']['bs_median']
                   if summary[f"{w:.1f}"]['2comp'] else np.nan for w in ws]
        bc_med = [summary[f"{w:.1f}"]['2comp']['bc_median']
                   if summary[f"{w:.1f}"]['2comp'] else np.nan for w in ws]
        bs_iqr = [summary[f"{w:.1f}"]['2comp']['bs_iqr']
                   if summary[f"{w:.1f}"]['2comp'] else np.nan for w in ws]
        bc_iqr = [summary[f"{w:.1f}"]['2comp']['bc_iqr']
                   if summary[f"{w:.1f}"]['2comp'] else np.nan for w in ws]
        ax.errorbar(ws, bs_med, yerr=bs_iqr, marker='s', color='C2',
                     capsize=3, lw=1.5, label='β_s')
        ax.errorbar(ws, bc_med, yerr=bc_iqr, marker='^', color='C3',
                     capsize=3, lw=1.5, label='β_c')
        ax.axhline(50, color='red', ls=':', alpha=0.5,
                    label='+50 grid boundary')
        ax.axhline(-50, color='red', ls=':', alpha=0.5)
        ax.set_xlabel('w (RDM_V1 weight)')
        ax.set_ylabel('2-comp parameter (median ± IQR)')
        ax.set_title('2-component parameters vs weight')
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)

        plt.suptitle(f'sub-09: (γ_GB + RDM_V1) weight sweep, '
                      f'{N_RESAMPLES}× size-5 HC resample\n'
                      f'L_combo(δθ;w) = (1-w)·z(L_γ_GB) + w·z(L_RDM_V1)',
                      fontsize=11)
        plt.tight_layout()
        out_png = OUT_DIR / "sub09_weight_sweep.png"
        plt.savefig(out_png, dpi=150, bbox_inches='tight')
        print(f"Saved: {out_png}")
    except Exception as e:
        print(f"[viz] failed: {e}")

    print(f"\nTotal elapsed: {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
