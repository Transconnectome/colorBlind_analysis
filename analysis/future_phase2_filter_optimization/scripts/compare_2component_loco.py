#!/usr/bin/env python3
"""
compare_2component_loco.py — Compare 2-Component LOCO results with existing models.

Reads JSON results from phase_a/ (existing) and phase_a_2component/ (new),
prints comparison table. Cross-references with ΔRDM results from
results/2component_comprehensive_v2/.

Usage (local):
    python scripts/compare_2component_loco.py
"""

import json
import numpy as np
from pathlib import Path

RESULTS_DIR = Path(__file__).resolve().parent.parent / 'results'
PHASE_A = RESULTS_DIR / 'loco_filter' / 'phase_a'
PHASE_A_2C = RESULTS_DIR / 'loco_filter' / 'phase_a_2component'
DRDM_DIR = RESULTS_DIR / '2component_comprehensive_v2'

# ΔRDM reference values (from comprehensive_2component_analysis.py)
DRDM_REF = {
    '08': {'roi': 'V1', 'beta_s': 20, 'beta_c': -18, 'p': 0.053,
           'criterion': 'xnobis_cosine'},
    '09': {'roi': 'V1', 'beta_s': 23, 'beta_c': 3, 'p': 0.007,
           'criterion': 'xnobis_cosine'},
}


def load_json(path):
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


def fmt_p(p):
    if p is None:
        return '  N/A '
    if p < 0.01:
        return f'{p:.4f}**'
    elif p < 0.05:
        return f'{p:.4f}* '
    elif p < 0.10:
        return f'{p:.4f}t '
    else:
        return f'{p:.4f}  '


def main():
    print('=' * 80)
    print('  2-Component LOCO Results vs Existing Models + ΔRDM Reference')
    print('=' * 80)

    # --- Section 1: hV4 comparison (shift_at_both) ---
    print('\n--- hV4 shift_at_both: 2component vs existing models ---\n')
    print(f'{"Subj":<7} {"Model":<16} {"params":<22} {"rho":>6} '
          f'{"perm_p":>10} {"L_fit":>7} {"CCC":>6}')
    print('-' * 80)

    for subj in ['08', '09']:
        # Existing models
        for model in ['machado_1way', 'rc_opponent', 'fourier_warp']:
            r = load_json(PHASE_A / f'sub-{subj}_V4_{model}.json')
            if r is None:
                continue
            pm = r.get('permutation', {})
            bl = r.get('best_loss', {})
            params_str = str(r.get('best_params', []))
            if len(params_str) > 20:
                params_str = params_str[:19] + '…'
            print(f'sub-{subj} {model:<16} {params_str:<22} '
                  f'{pm.get("spearman_r", 0):>6.3f} '
                  f'{fmt_p(pm.get("label_perm_p"))} '
                  f'{bl.get("l_fit", 0):>7.4f} '
                  f'{pm.get("ccc", 0):>6.3f}')

        # 2component
        r2c = load_json(PHASE_A_2C / f'sub-{subj}_V4_2component.json')
        if r2c:
            pm = r2c.get('permutation', {})
            bl = r2c.get('best_loss', {})
            bp = r2c.get('best_params', [])
            params_str = f'βs={bp[0]:.0f}, βc={bp[1]:.0f}'
            print(f'sub-{subj} {"2component":<16} {params_str:<22} '
                  f'{pm.get("spearman_r", 0):>6.3f} '
                  f'{fmt_p(pm.get("label_perm_p"))} '
                  f'{bl.get("l_fit", 0):>7.4f} '
                  f'{pm.get("ccc", 0):>6.3f}')
        else:
            print(f'sub-{subj} {"2component":<16} {"MISSING":<22}')

        print()

    # --- Section 2: V1 comparison (w_fixed) + ΔRDM cross-reference ---
    print('\n--- V1 w_fixed: 2component LOCO vs ΔRDM reference ---\n')
    print(f'{"Subj":<7} {"Criterion":<12} {"βs":>5} {"βc":>5} '
          f'{"rho/cos":>8} {"p":>10} {"converge?"}')
    print('-' * 70)

    for subj in ['08', '09', '10']:
        # 2component LOCO result
        r2c = load_json(PHASE_A_2C / f'sub-{subj}_V1_2component.json')
        if r2c:
            pm = r2c.get('permutation', {})
            bp = r2c.get('best_params', [0, 0])
            print(f'sub-{subj} {"LOCO":<12} {bp[0]:>5.0f} {bp[1]:>5.0f} '
                  f'{pm.get("spearman_r", 0):>8.3f} '
                  f'{fmt_p(pm.get("label_perm_p"))}')
        else:
            print(f'sub-{subj} {"LOCO":<12} {"MISSING":>5}')

        # ΔRDM reference
        if subj in DRDM_REF:
            ref = DRDM_REF[subj]
            print(f'sub-{subj} {"ΔRDM":<12} {ref["beta_s"]:>5.0f} {ref["beta_c"]:>5.0f} '
                  f'{"":>8} '
                  f'{fmt_p(ref["p"])}', end='')

            # Check convergence
            if r2c:
                bp = r2c.get('best_params', [0, 0])
                bs_diff = abs(bp[0] - ref['beta_s'])
                bc_diff = abs(bp[1] - ref['beta_c'])
                if bs_diff <= 5 and bc_diff <= 5:
                    print(f'  YES (Δβs={bs_diff:.0f}°, Δβc={bc_diff:.0f}°)')
                else:
                    print(f'  NO  (Δβs={bs_diff:.0f}°, Δβc={bc_diff:.0f}°)')
            else:
                print()
        elif subj == '10':
            print(f'sub-{subj} {"ΔRDM":<12} {"(null — no reference)"}')
        print()

    # --- Section 3: Detailed per-color vulnerability comparison ---
    print('\n--- Per-color vulnerability: 2component vs CVD target ---\n')
    colors = ['red', 'orange', 'yellow', 'green',
              'cyan', 'blue', 'purple', 'magenta']

    for subj in ['08', '09']:
        r2c = load_json(PHASE_A_2C / f'sub-{subj}_V4_2component.json')
        if not r2c:
            continue

        mf = load_json(PHASE_A_2C / f'sub-{subj}_V4_manifest.json')
        vuln_cvd = mf.get('vuln_cvd', []) if mf else []
        vuln_sim = r2c.get('best_loss', {}).get('vuln_sim', [])
        dt = r2c.get('best_loss', {}).get('delta_theta', [])

        if not vuln_cvd or not vuln_sim:
            continue

        print(f'  sub-{subj} hV4 2component (βs={r2c["best_params"][0]:.0f}°, '
              f'βc={r2c["best_params"][1]:.0f}°):')
        print(f'  {"color":<8} {"CVD":>7} {"sim":>7} {"diff":>7} {"δθ":>7}')
        for i, c in enumerate(colors):
            diff = vuln_sim[i] - vuln_cvd[i] if i < len(vuln_cvd) else 0
            d = dt[i] if i < len(dt) else 0
            print(f'  {c:<8} {vuln_cvd[i]:>7.3f} {vuln_sim[i]:>7.3f} '
                  f'{diff:>+7.3f} {d:>+7.1f}°')
        print()

    # --- Section 4: Summary verdict ---
    print('=' * 80)
    print('  SUMMARY')
    print('=' * 80)

    for subj in ['08', '09']:
        r_v4 = load_json(PHASE_A_2C / f'sub-{subj}_V4_2component.json')
        r_v1 = load_json(PHASE_A_2C / f'sub-{subj}_V1_2component.json')

        print(f'\nsub-{subj}:')
        if r_v4:
            pm = r_v4['permutation']
            bp = r_v4['best_params']
            sig = '***' if pm['label_perm_p'] < 0.01 else (
                  '**' if pm['label_perm_p'] < 0.05 else (
                  '*' if pm['label_perm_p'] < 0.10 else 'NS'))
            print(f'  hV4 LOCO: βs={bp[0]:.0f}°, βc={bp[1]:.0f}°, '
                  f'ρ={pm["spearman_r"]:.3f}, p={pm["label_perm_p"]:.4f} {sig}')
        if r_v1:
            pm = r_v1['permutation']
            bp = r_v1['best_params']
            sig = '***' if pm['label_perm_p'] < 0.01 else (
                  '**' if pm['label_perm_p'] < 0.05 else (
                  '*' if pm['label_perm_p'] < 0.10 else 'NS'))
            print(f'  V1  LOCO: βs={bp[0]:.0f}°, βc={bp[1]:.0f}°, '
                  f'ρ={pm["spearman_r"]:.3f}, p={pm["label_perm_p"]:.4f} {sig}')
        if subj in DRDM_REF:
            ref = DRDM_REF[subj]
            print(f'  V1  ΔRDM: βs={ref["beta_s"]}°, βc={ref["beta_c"]}°, '
                  f'p={ref["p"]:.3f}')

    # Sub-10 specificity
    r_v1_10 = load_json(PHASE_A_2C / 'sub-10_V1_2component.json')
    print(f'\nsub-10 (specificity null):')
    if r_v1_10:
        pm = r_v1_10['permutation']
        bp = r_v1_10['best_params']
        ok = 'PASS' if pm['label_perm_p'] > 0.10 else 'FAIL'
        print(f'  V1  LOCO: βs={bp[0]:.0f}°, βc={bp[1]:.0f}°, '
              f'ρ={pm["spearman_r"]:.3f}, p={pm["label_perm_p"]:.4f} '
              f'-> specificity {ok}')

    print()


if __name__ == '__main__':
    main()
