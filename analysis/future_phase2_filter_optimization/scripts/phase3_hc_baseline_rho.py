"""phase3_hc_baseline_rho.py — compute baseline_rho for each HC LOO under OLD formula.

For each HC i in {01..06}:
  - pool = other 5 HCs
  - vuln_sim_base = simulate_mean_hc_loco_legacy(pool, C_orig)   # β=0 (no shift)
  - vuln_target = load HC i's own LOCO vulnerability
  - baseline_rho = spearmanr(vuln_sim_base, vuln_target)

Output: results/old_formula/hc_baseline_rho.csv + summary print

Goal: verify hypothesis that high HC baseline_rho (≈ 0.7-0.95) is the common cause
behind both (a) σ_sim ceiling, and (b) HC norm > CVD norm specificity reversal.
"""
from __future__ import annotations
import csv
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr, pearsonr

_THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_THIS_DIR))

from old_formula_refit import (
    HC_SUBJECTS, N_CHANNELS, HUE_ANGLES,
    load_amplitudes, load_cvd_loco_target, create_basis_full,
    simulate_mean_hc_loco_legacy,
    LOCAL_DATA, SERVER_DATA,
)

OUTDIR = _THIS_DIR.parent / 'results' / 'old_formula'
OUTDIR.mkdir(parents=True, exist_ok=True)

HC_POOL_AVAILABLE = ['01', '02', '03', '04', '05', '06']


def main():
    data_dir = SERVER_DATA if SERVER_DATA.exists() else LOCAL_DATA
    basis_full = create_basis_full(N_CHANNELS, basis_type='fe')
    C_orig = basis_full[HUE_ANGLES]

    rows = []
    print('Computing HC LOO baseline_rho under OLD formula (β=0, V4)...\n')
    t0 = time.time()
    for target in HC_POOL_AVAILABLE:
        pool = [s for s in HC_POOL_AVAILABLE if s != target]
        hc_amps = {s: load_amplitudes(data_dir, s, 'V4') for s in pool}
        vuln_target = load_cvd_loco_target(target, 'V4')
        vuln_sim_base, _ = simulate_mean_hc_loco_legacy(hc_amps, C_orig)

        rho_s, _ = spearmanr(vuln_sim_base, vuln_target)
        r_p, _ = pearsonr(vuln_sim_base, vuln_target)
        l_vuln_0 = float(np.mean((vuln_sim_base - vuln_target) ** 2)) / 4.0
        l_rank_0 = (1.0 - rho_s) / 2.0
        l_fit_0 = l_vuln_0 + 0.5 * l_rank_0

        row = {
            'hc_subject': f'sub-{target}',
            'pool': ','.join(pool),
            'baseline_spearman_rho': float(rho_s),
            'baseline_pearson_r': float(r_p),
            'l_vuln_at_beta0': l_vuln_0,
            'l_rank_at_beta0': l_rank_0,
            'l_fit_at_beta0': l_fit_0,
            'vuln_target_mean': float(np.mean(vuln_target)),
            'vuln_target_std': float(np.std(vuln_target)),
            'vuln_sim_base_mean': float(np.mean(vuln_sim_base)),
            'vuln_sim_base_std': float(np.std(vuln_sim_base)),
        }
        rows.append(row)
        print(f'sub-{target}: ρ_spearman={rho_s:+.3f}  r_pearson={r_p:+.3f}  '
              f'L_fit(β=0)={l_fit_0:.4f}  '
              f'(target σ={row["vuln_target_std"]:.3f}, sim σ={row["vuln_sim_base_std"]:.3f})')

    # CVD reference (sub-08 V4 baseline)
    cvd_amps = {s: load_amplitudes(data_dir, s, 'V4') for s in HC_POOL_AVAILABLE}
    cvd_target = load_cvd_loco_target('08', 'V4')
    vuln_sim_cvd, _ = simulate_mean_hc_loco_legacy(cvd_amps, C_orig)
    cvd_rho_s, _ = spearmanr(vuln_sim_cvd, cvd_target)
    cvd_r_p, _ = pearsonr(vuln_sim_cvd, cvd_target)
    print(f'\n[REF] sub-08 CVD (pool=all 6 HCs): ρ_spearman={cvd_rho_s:+.3f}  r_pearson={cvd_r_p:+.3f}')

    # Save CSV
    csv_path = OUTDIR / 'hc_baseline_rho.csv'
    with open(csv_path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(list(rows[0].keys()))
        for r in rows:
            w.writerow([r[k] for k in rows[0].keys()])
        # Add CVD ref row
        w.writerow(['sub-08-CVD-REF', ','.join(HC_POOL_AVAILABLE),
                    float(cvd_rho_s), float(cvd_r_p),
                    float(np.mean((vuln_sim_cvd - cvd_target) ** 2)) / 4.0,
                    (1.0 - cvd_rho_s) / 2.0,
                    None,
                    float(np.mean(cvd_target)), float(np.std(cvd_target)),
                    float(np.mean(vuln_sim_cvd)), float(np.std(vuln_sim_cvd))])
    print(f'\nWrote {csv_path}')

    # Summary stats
    hc_rhos_s = [r['baseline_spearman_rho'] for r in rows]
    summary = {
        'hc_baseline_rho_spearman': {
            'values': hc_rhos_s,
            'mean': float(np.mean(hc_rhos_s)),
            'std': float(np.std(hc_rhos_s, ddof=1)),
            'min': float(np.min(hc_rhos_s)),
            'max': float(np.max(hc_rhos_s)),
        },
        'cvd_baseline_rho_spearman': float(cvd_rho_s),
        'hypothesis_check': {
            'all_hc_above_cvd': bool(all(r > cvd_rho_s for r in hc_rhos_s)),
            'hc_mean_minus_cvd': float(np.mean(hc_rhos_s) - cvd_rho_s),
        },
        'elapsed_sec': float(time.time() - t0),
    }
    json_path = OUTDIR / 'hc_baseline_rho_summary.json'
    with open(json_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f'Wrote {json_path}')
    print(f'\nHC mean baseline ρ = {summary["hc_baseline_rho_spearman"]["mean"]:.3f} '
          f'(range [{summary["hc_baseline_rho_spearman"]["min"]:.3f}, '
          f'{summary["hc_baseline_rho_spearman"]["max"]:.3f}])')
    print(f'CVD sub-08 baseline ρ = {cvd_rho_s:+.3f}')
    print(f'HC > CVD: {summary["hypothesis_check"]["all_hc_above_cvd"]}')


if __name__ == '__main__':
    main()
