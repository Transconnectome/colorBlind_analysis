#!/usr/bin/env python3
"""cycle14_v1rdm_only_analysis.py — Single-criterion V1 RDM fit, no α/β.

Per-subject fit (β_s, β_c) = argmin L_rdm_v1 (no V4 mixing, no Tikh).
Compare HC vs CVD distribution per parameter AND as norm.

Family convention: for HC, fit under both deutan AND protan, pick min-L family.
"""
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
JSON = ROOT / 'results' / 'cycles' / 'cycle14_v1_rdm_cross.json'
N_BOOT = 10000
SEED = 42


def boot_ci(values, stat=np.mean, n_boot=N_BOOT, ci=0.95):
    rng = np.random.default_rng(SEED)
    arr = np.array(values, dtype=float)
    n = len(arr)
    boot = np.array([stat(rng.choice(arr, size=n, replace=True))
                     for _ in range(n_boot)])
    lo = float(np.quantile(boot, (1 - ci) / 2))
    hi = float(np.quantile(boot, 1 - (1 - ci) / 2))
    return float(boot.mean()), lo, hi, boot


def main():
    with open(JSON) as f:
        d = json.load(f)
    per_subj = d['per_subject']

    # Extract V1 RDM-only (β_s, β_c) per subject
    rows = []
    for subj, entry in per_subj.items():
        role = entry['role']
        per_fam = entry['per_family']
        # For each family, get v1_rdm_only argmin
        fam_data = {}
        for fam, fdata in per_fam.items():
            v1 = fdata['v1_rdm_only']
            fam_data[fam] = (v1['bs'], v1['bc'], v1['L_rdm'])
        # Pick min-L family
        best_fam = min(fam_data, key=lambda f: fam_data[f][2])
        bs, bc, L = fam_data[best_fam]
        norm = float(np.sqrt(bs ** 2 + bc ** 2))
        rows.append({
            'subj': subj, 'role': role, 'best_family': best_fam,
            'beta_s': float(bs), 'beta_c': float(bc),
            'norm': norm, 'L_rdm': float(L),
            'all_families': fam_data,
        })

    print('=' * 78)
    print('Cycle 14 V1 RDM SOLE-CRITERION fit  (no α/β, no V4 mixing)')
    print('Per-subject (β_s, β_c) = argmin L_rdm_v1, family-symmetric')
    print('=' * 78)
    print(f'\n{"subj":<8}{"role":<5}{"fam":<8}{"β_s":>8}{"β_c":>8}'
          f'{"norm":>8}{"L_rdm":>10}')
    for r in sorted(rows, key=lambda x: (x['role'], x['subj'])):
        print(f"  {r['subj']:<6}{r['role']:<5}{r['best_family']:<8}"
              f"{r['beta_s']:>8.0f}{r['beta_c']:>8.0f}"
              f"{r['norm']:>8.1f}{r['L_rdm']:>10.4f}")

    hc = [r for r in rows if r['role'] == 'HC']
    cvd = [r for r in rows if r['role'] == 'CVD']

    hc_bs = np.array([r['beta_s'] for r in hc])
    hc_bc = np.array([r['beta_c'] for r in hc])
    hc_norm = np.array([r['norm'] for r in hc])

    print('\n' + '=' * 78)
    print('Per-parameter distribution (HC mean ± SD with 95% bootstrap CI)')
    print('=' * 78)
    bs_mean, bs_lo, bs_hi, bs_boot = boot_ci(hc_bs)
    bc_mean, bc_lo, bc_hi, bc_boot = boot_ci(hc_bc)
    bs_abs_mean, bs_abs_lo, bs_abs_hi, bs_abs_boot = boot_ci(np.abs(hc_bs))
    bc_abs_mean, bc_abs_lo, bc_abs_hi, bc_abs_boot = boot_ci(np.abs(hc_bc))
    norm_mean, norm_lo, norm_hi, norm_boot = boot_ci(hc_norm)

    print(f'  HC β_s:    mean={bs_mean:+6.1f}  CI=[{bs_lo:+.1f}, {bs_hi:+.1f}]  '
          f'(signed; should ≈ 0 if HC is null)')
    print(f'  HC |β_s|:  mean={bs_abs_mean:6.1f}  CI=[{bs_abs_lo:.1f}, '
          f'{bs_abs_hi:.1f}]  (magnitude only)')
    print(f'  HC β_c:    mean={bc_mean:+6.1f}  CI=[{bc_lo:+.1f}, {bc_hi:+.1f}]  '
          f'(signed)')
    print(f'  HC |β_c|:  mean={bc_abs_mean:6.1f}  CI=[{bc_abs_lo:.1f}, '
          f'{bc_abs_hi:.1f}]')
    print(f'  HC norm:   mean={norm_mean:6.1f}  CI=[{norm_lo:.1f}, '
          f'{norm_hi:.1f}]')
    print(f'\n  HC β_s individual: {sorted(hc_bs.tolist())}')
    print(f'  HC β_c individual: {sorted(hc_bc.tolist())}')
    print(f'  HC norm individual: {sorted(hc_norm.tolist())}')

    print('\n' + '=' * 78)
    print('CVD vs HC bootstrap test')
    print('=' * 78)
    for r in cvd:
        bs_v = r['beta_s']; bc_v = r['beta_c']; n_v = r['norm']

        # For each param, compute fraction of bootstrap HC values strictly less
        # than CVD (in absolute value, since direction differs by family)
        frac_bs_above = float((bs_abs_boot < abs(bs_v)).sum() / N_BOOT)
        frac_bc_above = float((bc_abs_boot < abs(bc_v)).sum() / N_BOOT)
        frac_norm_above = float((norm_boot < n_v).sum() / N_BOOT)

        emp_p_norm = float((hc_norm >= n_v).sum() / len(hc))

        print(f'\n  {r["subj"]} ({r["best_family"]}):  (β_s, β_c)=({bs_v:.0f},'
              f' {bc_v:+.0f})  norm={n_v:.1f}')
        print(f'    |β_s|={abs(bs_v):5.0f}  vs HC |β_s| mean={bs_abs_mean:.1f}'
              f'  →  P(HC_mean < |CVD β_s|) = {frac_bs_above:.3f}')
        print(f'    |β_c|={abs(bc_v):5.0f}  vs HC |β_c| mean={bc_abs_mean:.1f}'
              f'  →  P(HC_mean < |CVD β_c|) = {frac_bc_above:.3f}')
        print(f'    norm ={n_v:5.1f}  vs HC norm mean={norm_mean:.1f}'
              f'  →  P(HC_mean < CVD norm) = {frac_norm_above:.3f}')
        print(f'    emp_p (rank-based, norm): {emp_p_norm:.2f} ({"sig" if emp_p_norm <= 0.20 else "NS"})')

    print('\n' + '=' * 78)
    print('NOTE: P(HC_mean < CVD) = bootstrap fraction. ≥ 0.975 = strict CI ✓.')
    print('      |β_s|, |β_c| use absolute value because HC has no')
    print('      directional ground truth — only magnitude is informative.')
    print('=' * 78)


if __name__ == '__main__':
    main()
