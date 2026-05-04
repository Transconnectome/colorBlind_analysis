#!/usr/bin/env python3
"""
build_loss_inventory.py — Loss variant inventory with HC sanity check.

For each loss variant (single-ROI metric or cross-ROI combination), compute
the argmin/argmax (β_s, β_c) per subject, then evaluate HC sanity:
  - HC mean ||(β_s, β_c)||  (should be near 0 if loss captures CVD signal)
  - CVD ||(β_s, β_c)||
  - Ratio = CVD_norm / HC_mean_norm  (should be > 1)

Output:
  results/inventory/loss_inventory.csv  — flat row-per-(loss, subject, ROI)
  results/inventory/loss_inventory.md   — summary table + interpretation
"""

import json
import csv
import sys
from pathlib import Path
import numpy as np

ROOT = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/'
            'colorBlind_analysis/analysis/future_phase2_filter_optimization')
RES = ROOT / 'results'
LANDSCAPE_DIR = RES / 'cycles'

OUT_CSV = RES / 'inventory' / 'loss_inventory.csv'
OUT_MD = RES / 'inventory' / 'loss_inventory.md'

HC = ['01', '02', '03', '04', '05', '06']
CVD = ['08', '09']
ROIS = ['V1', 'V2', 'V4']

_BS = np.arange(0.0, 81.0, 2.0)   # 41
_BC = np.arange(-60.0, 61.0, 2.0)  # 61
LAM = 0.2
_BS_GRID, _BC_GRID = np.meshgrid(_BS, _BC, indexing='ij')
NORM_GRID = (_BS_GRID / 80.0) ** 2 + (_BC_GRID / 60.0) ** 2

# Per-subject metrics (single-ROI) — evaluated as argmin or argmax
SINGLE_METRICS = {
    'l_rank':           ('argmin', 'V4', '1 - Spearman ρ (V4)'),
    'l_topk_jaccard':   ('argmin', 'V4', 'Top-K Jaccard distance (V4)'),
    'l_dir':            ('argmin', 'V4', 'Directional loss (V4)'),
    'mw_jaccard_loss':  ('argmin', 'V4', 'Mann-Whitney Jaccard (V4)'),
    'l_mag':            ('argmin', 'V4', 'Magnitude loss (V4)'),
    'norm_resid':       ('argmin', 'V4', 'Normalized residual (V4)'),
    'sign_agree':       ('argmax', 'V4', 'Sign agreement fraction (V4)'),
    'spearman_r':       ('argmax', 'V4', 'Spearman ρ (V4)'),
    'pearson_r':        ('argmax', 'V4', 'Pearson r (V4)'),
    'l_rank_V1':        ('argmin', 'V1', '1 - Spearman ρ (V1)'),
    'l_topk_V1':        ('argmin', 'V1', 'Top-K Jaccard distance (V1)'),
}

# Cross-ROI loss combinations (use cycle12/cycle14 source data)
def cycle12_loss(subj, alpha=1.0, beta=1.0):
    """L = α·l_topk(V4) + β·l_rank(V1) + 0.2·Tikh."""
    p_v4 = LANDSCAPE_DIR / f'sub-{subj}_V4_landscape.json'
    p_v1 = LANDSCAPE_DIR / f'sub-{subj}_V1_landscape.json'
    if not p_v4.exists() or not p_v1.exists():
        return None
    with open(p_v4) as f:
        L_topk = np.array(json.load(f)['l_topk_jaccard'])
    with open(p_v1) as f:
        L_rank = np.array(json.load(f)['l_rank'])
    L = alpha * L_topk + beta * L_rank + LAM * NORM_GRID
    idx = np.unravel_index(np.argmin(L), L.shape)
    return float(_BS[idx[0]]), float(_BC[idx[1]])


def cycle14_loss(subj, alpha=1.0, beta=1.0):
    """L = α·l_topk(V4) + β·(1-cos(ΔRDM_V1)) + 0.2·Tikh.

    Reads precomputed Cycle 14 result (only sub-08, 09 available).
    For HC, returns None — V1 RDM landscape not precomputed.
    """
    if subj not in ('08', '09'):
        return None
    p = RES / 'cycles' / 'cycle14_v1_rdm_cross.json'
    if not p.exists():
        return None
    with open(p) as f:
        d = json.load(f)
    if subj not in d['per_subject']:
        return None
    key = f'a{alpha}_b{beta}'
    e = d['per_subject'][subj]['cross_rdm_weights'].get(key)
    if not e:
        return None
    return float(e['bs']), float(e['bc'])


def load_landscape(subj, roi, metric):
    p = LANDSCAPE_DIR / f'sub-{subj}_{roi}_landscape.json'
    if not p.exists():
        return None
    with open(p) as f:
        d = json.load(f)
    if metric not in d:
        return None
    return np.array(d[metric])


def find_extremum(grid, mode):
    if mode == 'argmin':
        idx = np.unravel_index(np.argmin(grid), grid.shape)
    else:
        idx = np.unravel_index(np.argmax(grid), grid.shape)
    return float(_BS[idx[0]]), float(_BC[idx[1]]), float(grid[idx])


def beta_norm(bs, bc):
    """Normalized norm in [0, sqrt(2)] across grid bounds."""
    return float(np.sqrt((bs / 80.0) ** 2 + (bc / 60.0) ** 2))


def beta_norm_raw(bs, bc):
    return float(np.sqrt(bs ** 2 + bc ** 2))


# ============================================================
# Build inventory
# ============================================================

rows = []

# 1. Single-ROI metrics
for loss_name, (mode, default_roi, desc) in SINGLE_METRICS.items():
    metric_key = loss_name
    roi = default_roi
    if loss_name.endswith('_V1'):
        metric_key = loss_name.replace('_V1', '').replace('topk', 'topk_jaccard')
        roi = 'V1'
    elif loss_name.endswith('_V2'):
        metric_key = loss_name.replace('_V2', '').replace('topk', 'topk_jaccard')
        roi = 'V2'

    for subj in HC + CVD:
        grid = load_landscape(subj, roi, metric_key)
        if grid is None:
            continue
        bs, bc, val = find_extremum(grid, mode)
        rows.append({
            'loss_variant': loss_name,
            'description': desc,
            'subject': f'sub-{subj}',
            'role': 'HC' if subj in HC else 'CVD',
            'roi': roi,
            'mode': mode,
            'best_value': round(val, 4),
            'beta_s': bs,
            'beta_c': bc,
            'norm_raw': round(beta_norm_raw(bs, bc), 2),
            'norm_grid': round(beta_norm(bs, bc), 4),
        })

# 2. Cycle 12 cross-ROI loss (default α=β=1)
for subj in HC + CVD:
    res = cycle12_loss(subj, 1.0, 1.0)
    if res is None:
        continue
    bs, bc = res
    rows.append({
        'loss_variant': 'cycle12_cross_roi',
        'description': 'α·l_topk(V4) + β·l_rank(V1) + 0.2·Tikh (α=β=1)',
        'subject': f'sub-{subj}',
        'role': 'HC' if subj in HC else 'CVD',
        'roi': 'V4+V1',
        'mode': 'argmin',
        'best_value': None,
        'beta_s': bs,
        'beta_c': bc,
        'norm_raw': round(beta_norm_raw(bs, bc), 2),
        'norm_grid': round(beta_norm(bs, bc), 4),
    })

# 2.5. Cycle 15 mw_jaccard cross-criterion variants
def cycle15_loss(subj, variant_key, alpha=2.0, beta=1.0):
    """Cycle 15 mw_jaccard cross variants."""
    p = RES / 'cycles' / 'cycle15_mwjaccard_cross.json'
    if not p.exists():
        return None
    with open(p) as f:
        d = json.load(f)
    if variant_key not in d['per_variant']:
        return None
    wkey = f'a{alpha}_b{beta}'
    e = d['per_variant'][variant_key]['per_subject'].get(wkey, {}).get(subj)
    if not e:
        return None
    return float(e['bs']), float(e['bc'])


for variant, label in [('opt2_v4mwj_v1lrank',
                        '2·mw_jaccard(V4) + 1·l_rank(V1) + 0.2·Tikh'),
                       ('opt3_v4mwj_v1mwj',
                        '1·mw_jaccard(V4) + 1·mw_jaccard(V1) + 0.2·Tikh'),
                       ('opt4_v4mwj_v4spear',
                        '1·mw_jaccard(V4) + 1·(1-spearman_r)(V4) + 0.2·Tikh')]:
    alpha = 2.0 if variant == 'opt2_v4mwj_v1lrank' else 1.0
    for subj in HC + CVD:
        res = cycle15_loss(subj, variant, alpha=alpha, beta=1.0)
        if res is None:
            continue
        bs, bc = res
        rows.append({
            'loss_variant': f'cycle15_{variant}',
            'description': label,
            'subject': f'sub-{subj}',
            'role': 'HC' if subj in HC else 'CVD',
            'roi': 'V4+V1' if 'V1' in variant else 'V4',
            'mode': 'argmin',
            'best_value': None,
            'beta_s': bs, 'beta_c': bc,
            'norm_raw': round(beta_norm_raw(bs, bc), 2),
            'norm_grid': round(beta_norm(bs, bc), 4),
        })


# 3. Cycle 14 cross-ROI RDM (CVD only — HC V1 RDM landscape not precomputed)
for subj in HC + CVD:
    res = cycle14_loss(subj, 1.0, 1.0)
    if res is None:
        rows.append({
            'loss_variant': 'cycle14_cross_roi_rdm',
            'description': 'α·l_topk(V4) + β·(1-cos(ΔRDM_V1)) + 0.2·Tikh (α=β=1)',
            'subject': f'sub-{subj}',
            'role': 'HC' if subj in HC else 'CVD',
            'roi': 'V4+V1',
            'mode': 'argmin',
            'best_value': None,
            'beta_s': None, 'beta_c': None,
            'norm_raw': None, 'norm_grid': None,
        })
        continue
    bs, bc = res
    rows.append({
        'loss_variant': 'cycle14_cross_roi_rdm',
        'description': 'α·l_topk(V4) + β·(1-cos(ΔRDM_V1)) + 0.2·Tikh (α=β=1)',
        'subject': f'sub-{subj}',
        'role': 'HC' if subj in HC else 'CVD',
        'roi': 'V4+V1',
        'mode': 'argmin',
        'best_value': None,
        'beta_s': bs, 'beta_c': bc,
        'norm_raw': round(beta_norm_raw(bs, bc), 2),
        'norm_grid': round(beta_norm(bs, bc), 4),
    })

# 4. Reference: phase_a 2component canonical fits (CVD only — HC fit missing)
PHASE_A_FITS = {
    ('08', 'V4'): (38.0, -14.0, 0.881),
    ('09', 'V4'): (6.0, -22.0, 0.690),
    ('08', 'V1'): (50.0, -14.0, None),  # MEMORY: V1 LOCO p=0.001
    ('09', 'V1'): (23.0, 3.0, None),    # MEMORY
}
for (subj, roi), (bs, bc, sp) in PHASE_A_FITS.items():
    rows.append({
        'loss_variant': 'phase_a_L_LOCO_canonical',
        'description': 'α·L_vuln + β·L_rank + δ·L_rdm + ε·L_smooth (canonical phase_a)',
        'subject': f'sub-{subj}',
        'role': 'CVD',
        'roi': roi,
        'mode': 'argmin (weighted)',
        'best_value': sp,  # spearman ρ at best
        'beta_s': bs, 'beta_c': bc,
        'norm_raw': round(beta_norm_raw(bs, bc), 2),
        'norm_grid': round(beta_norm(bs, bc), 4),
    })
# NOTE: HC phase_a fit missing — flag it
for subj in HC:
    for roi in ['V1', 'V4']:
        rows.append({
            'loss_variant': 'phase_a_L_LOCO_canonical',
            'description': 'α·L_vuln + β·L_rank + δ·L_rdm + ε·L_smooth (canonical phase_a)',
            'subject': f'sub-{subj}',
            'role': 'HC',
            'roi': roi,
            'mode': 'argmin (weighted)',
            'best_value': None,
            'beta_s': None, 'beta_c': None,
            'norm_raw': None, 'norm_grid': None,
        })

# Save CSV
keys = ['loss_variant', 'description', 'subject', 'role', 'roi', 'mode',
        'best_value', 'beta_s', 'beta_c', 'norm_raw', 'norm_grid']
with open(OUT_CSV, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=keys)
    w.writeheader()
    w.writerows(rows)
print(f'Saved CSV: {OUT_CSV} ({len(rows)} rows)')

# ============================================================
# HC sanity check summary per loss variant (with bootstrap)
# ============================================================

def empirical_p_one_sided(hc_norms, cvd_norm):
    """Fraction of HC subjects with norm >= CVD_norm (one-sided)."""
    if not hc_norms or cvd_norm is None:
        return None
    n_above = sum(1 for h in hc_norms if h >= cvd_norm)
    return n_above / len(hc_norms)


def bootstrap_hc_mean(hc_norms, n_boot=10000, seed=42):
    """Bootstrap HC mean norm distribution."""
    if not hc_norms:
        return None
    rng = np.random.default_rng(seed)
    n = len(hc_norms)
    means = np.empty(n_boot)
    for i in range(n_boot):
        idx = rng.integers(0, n, n)
        means[i] = np.mean([hc_norms[k] for k in idx])
    return {
        'mean': float(np.mean(means)),
        'sd': float(np.std(means)),
        'ci_lo': float(np.percentile(means, 2.5)),
        'ci_hi': float(np.percentile(means, 97.5)),
        'samples': means,
    }


def bootstrap_cvd_vs_hc(hc_norms, cvd_norm, n_boot=10000, seed=42):
    """Fraction of bootstrap HC means that fall BELOW CVD norm.

    Higher fraction → CVD more clearly distinct from HC mean.
    """
    if not hc_norms or cvd_norm is None:
        return None
    boot = bootstrap_hc_mean(hc_norms, n_boot, seed)
    return float(np.mean(boot['samples'] < cvd_norm))

# Aggregate per (loss_variant, roi)
summary = {}
for r in rows:
    if r['norm_raw'] is None:
        continue
    key = (r['loss_variant'], r['roi'])
    if key not in summary:
        summary[key] = {'description': r['description'],
                        'hc_norms': [], 'cvd_norms': {},
                        'hc_params': [], 'cvd_params': {}}
    if r['role'] == 'HC':
        summary[key]['hc_norms'].append(r['norm_raw'])
        summary[key]['hc_params'].append((r['subject'], r['beta_s'],
                                          r['beta_c']))
    else:
        summary[key]['cvd_norms'][r['subject']] = r['norm_raw']
        summary[key]['cvd_params'][r['subject']] = (r['beta_s'], r['beta_c'])

# Build markdown
with open(OUT_MD, 'w') as f:
    f.write('# Loss Inventory & HC Sanity Check\n\n')
    f.write('Generated: 2026-05-03 by `build_loss_inventory.py`\n\n')
    f.write('## Sanity check principle\n\n')
    f.write('A "useful" loss should give HC subjects (β_s, β_c) ≈ (0, 0) '
            '(no compensation needed) and CVD subjects non-trivial '
            '(β_s, β_c) (compensation needed).\n\n')
    f.write('Quantitative metric:\n\n')
    f.write('  - **HC_mean_norm** = mean(||(β_s, β_c)||) over HC subjects\n')
    f.write('  - **CVD/HC ratio** = CVD_norm / HC_mean_norm\n')
    f.write('  - **Threshold**: ratio > 1 means CVD distortion > HC noise; '
            'ratio < 1 means loss is fitting noise (HC and CVD '
            'indistinguishable).\n\n')

    f.write('## Summary table — point estimates\n\n')
    f.write('| Loss variant | ROI | HC_mean_norm | sub-08_norm | '
            'sub-08/HC | sub-09_norm | sub-09/HC | Verdict (point) |\n')
    f.write('|---|---|---:|---:|---:|---:|---:|---|\n')

    rows_md = []
    bootstrap_rows = []
    for (loss, roi), s in sorted(summary.items()):
        if not s['hc_norms']:
            continue
        hc_mean = float(np.mean(s['hc_norms']))
        hc_n = len(s['hc_norms'])
        s08 = s['cvd_norms'].get('sub-08')
        s09 = s['cvd_norms'].get('sub-09')

        ratio_08 = (s08 / hc_mean) if (s08 is not None and hc_mean > 0.1) \
            else None
        ratio_09 = (s09 / hc_mean) if (s09 is not None and hc_mean > 0.1) \
            else None

        if ratio_08 and ratio_09:
            if ratio_08 > 1.5 and ratio_09 > 1.5:
                verdict = '✓ both CVD > HC'
            elif ratio_08 > 1.0 and ratio_09 > 1.0:
                verdict = '~ both CVD ≥ HC'
            elif ratio_08 > 1.0 or ratio_09 > 1.0:
                verdict = '× partial (one CVD < HC)'
            else:
                verdict = '✗ CVD < HC (loss captures noise)'
        else:
            verdict = '? insufficient data'

        rows_md.append((loss, roi, hc_mean, s08, ratio_08, s09, ratio_09,
                        verdict, hc_n))
        bootstrap_rows.append((loss, roi, s, hc_n))
        s08_str = f'{s08:.1f}' if s08 is not None else '—'
        s09_str = f'{s09:.1f}' if s09 is not None else '—'
        r08_str = f'{ratio_08:.2f}' if ratio_08 is not None else '—'
        r09_str = f'{ratio_09:.2f}' if ratio_09 is not None else '—'
        f.write(f'| `{loss}` | {roi} | {hc_mean:.1f} (n={hc_n}) | '
                f'{s08_str} | {r08_str} | {s09_str} | {r09_str} | '
                f'{verdict} |\n')

    # ============================================================
    # Statistical sanity (bootstrap + rank-based empirical p)
    # ============================================================
    f.write('\n## Summary table — statistical sanity (bootstrap + rank)\n\n')
    f.write('Per user critique 2026-05-03: HC pool of n=6 sensitive to '
            'outliers (sub-04 in particular).\n\n')
    f.write('- **emp_p**: fraction of HC subjects with norm ≥ CVD norm '
            '(rank-based; lower = CVD more outlier above HC distribution; '
            'sig threshold ~0.20 = at most 1/6 HC above)\n')
    f.write('- **boot_HC_CI**: 95% bootstrap CI of HC mean norm (10000 '
            'resamples, with replacement)\n')
    f.write('- **CVD>boot_mean frac**: fraction of bootstrap HC means below '
            'CVD norm (higher = more reliably distinct)\n\n')
    f.write('| Loss variant | ROI | boot_HC_CI | sub-08 | sub-09 | sub-08 emp_p | sub-08 CVD>boot | sub-09 emp_p | sub-09 CVD>boot | Stat verdict |\n')
    f.write('|---|---|---|---:|---:|---:|---:|---:|---:|---|\n')

    stat_rows = []
    for (loss, roi, s, hc_n) in bootstrap_rows:
        boot = bootstrap_hc_mean(s['hc_norms'])
        ci_str = f"[{boot['ci_lo']:.1f}, {boot['ci_hi']:.1f}]"
        s08 = s['cvd_norms'].get('sub-08')
        s09 = s['cvd_norms'].get('sub-09')
        ep_08 = empirical_p_one_sided(s['hc_norms'], s08)
        ep_09 = empirical_p_one_sided(s['hc_norms'], s09)
        bf_08 = bootstrap_cvd_vs_hc(s['hc_norms'], s08)
        bf_09 = bootstrap_cvd_vs_hc(s['hc_norms'], s09)

        # CI-based stat verdict (robust to single outliers like sub-04):
        # CVD norm vs bootstrap CI of HC mean.
        # - CVD > ci_hi → significantly above HC mean (one-sided 95%)
        # - CVD inside CI → not distinct
        # Equivalent: bootstrap fraction (HC means below CVD) ≥ 0.975
        SIG_FRAC = 0.975  # one-sided (CVD > HC mean) at α=0.025
        sig08 = (bf_08 is not None and bf_08 >= SIG_FRAC)
        sig09 = (bf_09 is not None and bf_09 >= SIG_FRAC)
        # Marginal zone (0.90 ≤ frac < 0.975) — CVD likely above but not sig
        marg08 = (bf_08 is not None and 0.90 <= bf_08 < SIG_FRAC)
        marg09 = (bf_09 is not None and 0.90 <= bf_09 < SIG_FRAC)
        if sig08 and sig09:
            sv = '✓✓ both CVD > HC bootstrap CI'
        elif sig08 and marg09:
            sv = '✓+~ sub-08 sig, sub-09 marginal'
        elif marg08 and sig09:
            sv = '✓+~ sub-09 sig, sub-08 marginal'
        elif sig08 or sig09:
            sv = '✓ one CVD sig (other inside CI)'
        elif marg08 and marg09:
            sv = '~~ both marginal'
        elif marg08 or marg09:
            sv = '~ one marginal'
        else:
            sv = '✗ neither sig (inside HC CI)'

        s08_str = f'{s08:.1f}' if s08 is not None else '—'
        s09_str = f'{s09:.1f}' if s09 is not None else '—'
        ep08_str = f'{ep_08:.2f} ({int(ep_08*hc_n)}/{hc_n})' if ep_08 is not None else '—'
        ep09_str = f'{ep_09:.2f} ({int(ep_09*hc_n)}/{hc_n})' if ep_09 is not None else '—'
        bf08_str = f'{bf_08:.2f}' if bf_08 is not None else '—'
        bf09_str = f'{bf_09:.2f}' if bf_09 is not None else '—'

        f.write(f'| `{loss}` | {roi} | {ci_str} | {s08_str} | {s09_str} | '
                f'{ep08_str} | {bf08_str} | {ep09_str} | {bf09_str} | '
                f'{sv} |\n')
        stat_rows.append((loss, roi, sv, ep_08, ep_09, bf_08, bf_09))

    f.write('\n## Per-subject details (HC dispersion check)\n\n')
    for (loss, roi), s in sorted(summary.items()):
        if not s['hc_params']:
            continue
        f.write(f'\n### `{loss}` @ {roi}\n\n')
        f.write(f'_{s["description"]}_\n\n')
        f.write('| Subject | role | (β_s, β_c) | norm |\n')
        f.write('|---|---|---|---:|\n')
        for sname, bs, bc in sorted(s['hc_params']):
            n = float(np.sqrt(bs ** 2 + bc ** 2))
            f.write(f'| {sname} | HC | ({bs:.0f}, {bc:.0f}) | {n:.1f} |\n')
        for sname in sorted(s['cvd_params'].keys()):
            bs, bc = s['cvd_params'][sname]
            n = float(np.sqrt(bs ** 2 + bc ** 2))
            f.write(f'| {sname} | **CVD** | **({bs:.0f}, {bc:.0f})** | '
                    f'**{n:.1f}** |\n')

    f.write('\n## Verdict legend\n\n')
    f.write('- **✓ both CVD > HC** (ratio > 1.5): Loss meaningfully separates '
            'CVD from HC. Good candidate.\n')
    f.write('- **~ both CVD ≥ HC** (1.0 < ratio ≤ 1.5): Marginal. CVD slightly '
            'larger but within HC variability range.\n')
    f.write('- **× partial** (one CVD < HC): Loss works for one subject but not '
            'the other. Subject-specific applicability.\n')
    f.write('- **✗ CVD < HC** (both ratios < 1): Loss is fitting noise. HC '
            'subjects look more "compensation-needing" than actual CVD '
            'subjects. **REJECT for filter selection.**\n')

    f.write('\n## Notes\n\n')
    f.write('- Phase A canonical (`L_LOCO`) HC fits not in this inventory — '
            'requires re-running `loco_distortion_fit.py` for sub-01..07. '
            'Currently flagged as missing.\n')
    f.write('- Cycle 14 cross-ROI RDM HC values not computed (V1 RDM landscape '
            'only generated for sub-08, 09 in cycle14 script).\n')
    f.write('- Grid bounds: β_s ∈ [0, 80] step 2, β_c ∈ [-60, 60] step 2 '
            '(41 × 61 = 2501 points).\n')
    f.write('- All landscapes computed on local data '
            '(`full_dataset_C010_with_residuals`); server canonical phase_a '
            'fits use raw `full_dataset_C010` (different).\n')

print(f'Saved MD: {OUT_MD}')

# Console summary
print('\n=== HC SANITY VERDICT (point estimate) ===')
for r in rows_md:
    loss, roi, hc, s08, r08, s09, r09, verd, n = r
    print(f'  {loss:<28s} @ {roi:<6s} {verd}')

print('\n=== STATISTICAL SANITY (rank-based emp_p) ===')
for (loss, roi, sv, ep08, ep09, bf08, bf09) in stat_rows:
    ep08s = f'{ep08:.2f}' if ep08 is not None else '—'
    ep09s = f'{ep09:.2f}' if ep09 is not None else '—'
    print(f'  {loss:<28s} @ {roi:<6s} '
          f'sub08 ep_p={ep08s}, sub09 ep_p={ep09s}  →  {sv}')
