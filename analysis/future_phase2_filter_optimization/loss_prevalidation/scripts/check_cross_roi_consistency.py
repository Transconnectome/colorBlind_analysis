#!/usr/bin/env python3
"""
check_cross_roi_consistency.py — Loss prevalidation for Phase 2 filter pipeline.

Three levels of cross-validation:
  Level 1: V2 ↔ hV4 28-pair distortion correlation (cross-ROI consistency)
  Level 2: V2 distortion burden → hV4 LOCO error (per-color, 8 points)
  Level 3: Behavioral JND ↔ V2 distortion (sub-08 only, 8 pairs)

Plus per-subject signal sufficiency assessment (Q2):
  - Split-half reliability of V2 distortion profile
  - Number of pairs with |z| > 1.96
  - Effect size of distortion

Usage:
    conda activate srm
    python scripts/check_cross_roi_consistency.py
"""

import json
import numpy as np
from pathlib import Path
from scipy.stats import spearmanr, pearsonr

# ============================================================================
# Paths
# ============================================================================

BASE = Path(__file__).resolve().parents[2]  # future_phase2_filter_optimization
PREVAL_JSON = (BASE / 'target_prevalidation' / 'results' /
               'filter_pre_validation_results.json')
LOCO_DIR = (BASE.parent / 'future_phase1_forward_model' / 'results' / 'validation')
BEHAV_DIR = Path(__file__).resolve().parents[4] / 'data' / 'behav_pilot'
OUTPUT_DIR = Path(__file__).resolve().parent.parent / 'results'

COLOR_NAMES = ['red', 'orange', 'yellow', 'green',
               'cyan', 'blue', 'purple', 'magenta']
HC_SUBJECTS = ['sub-01', 'sub-02', 'sub-03', 'sub-04',
               'sub-05', 'sub-06', 'sub-07']
CVD_SUBJECTS = ['sub-08', 'sub-09', 'sub-10']


# ============================================================================
# Data Loading
# ============================================================================

def load_preval_data():
    """Load pre-validation pair distances for V2 and hV4."""
    with open(PREVAL_JSON) as f:
        data = json.load(f)

    pair_labels = data['config']['pair_labels']
    out = {}

    for roi_key, roi_label in [('V2', 'V2'), ('hV4', 'hV4')]:
        roi_data = data['results'][roi_key]
        b1 = roi_data['B1_permutation']

        # HC mean pair distances
        hc_dists = []
        for subj in HC_SUBJECTS:
            hc_dists.append(np.array(b1['hc_pair_distances'][subj]))
        hc_mean = np.mean(hc_dists, axis=0)  # (28,)
        hc_std = np.std(hc_dists, axis=0, ddof=1)  # (28,)

        # CVD pair distances + z-scores
        cvd = {}
        for subj in CVD_SUBJECTS:
            cvd[subj] = {
                'distances': np.array(b1['cvd_pair_distances'][subj]),
                'z_scores': np.array(b1['observed_individual_z'][subj]),
                'distortion': (np.array(b1['cvd_pair_distances'][subj])
                               - hc_mean),
            }

        # Split-half data
        b2 = roi_data['B2_split_half']
        split_half = {}
        for method in ['first_last', 'odd_even']:
            split_half[method] = {}
            for subj in CVD_SUBJECTS:
                sh = b2[method]['per_subject_correlation'][subj]
                split_half[method][subj] = {
                    'spearman_r': sh['spearman_r'],
                    'spearman_p': sh['spearman_p'],
                }

        out[roi_label] = {
            'hc_mean': hc_mean,
            'hc_std': hc_std,
            'cvd': cvd,
            'split_half': split_half,
        }

    return out, pair_labels


def load_loco_data():
    """Load per-color hV4 LOCO voxel correlations (ridge_gcv)."""
    loco = {}
    for subj_file in sorted(LOCO_DIR.glob('sub-*_loco.json')):
        subj_id = subj_file.stem.replace('_loco', '')  # e.g., 'sub-08'
        with open(subj_file) as f:
            data = json.load(f)

        if 'V4' not in data:
            continue

        ridge = data['V4'].get('ridge_gcv')
        if ridge is None:
            continue

        per_color = np.array([fold['voxel_corr'] for fold in ridge['folds']])
        loco[subj_id] = {
            'per_color_voxel_corr': per_color,  # (8,)
            'mean_voxel_corr': float(ridge['mean_voxel_corr']),
        }

    return loco


def load_behavioral_jnd():
    """Load JND data for HC and sub-08."""
    jnd = {}
    for csv_file in BEHAV_DIR.glob('*_jnd_ses1_no_filter_summary.csv'):
        name = csv_file.stem  # e.g., 'HC_jnd_ses1_no_filter_summary'
        label = 'HC' if name.startswith('HC') else 'sub-08'

        pairs = {}
        with open(csv_file) as f:
            header = f.readline().strip().split(',')
            for line in f:
                parts = line.strip().split(',')
                if len(parts) < 7:
                    continue
                pair_name = parts[0]
                jnd_mean = float(parts[3])
                if pair_name not in pairs:
                    pairs[pair_name] = []
                pairs[pair_name].append(jnd_mean)

        # Average across staircases
        jnd[label] = {pair: np.mean(vals) for pair, vals in pairs.items()}

    return jnd


# ============================================================================
# Helper: pair ↔ color mapping
# ============================================================================

def get_pairs_involving_color(color_idx, pair_labels):
    """Return indices of pairs involving a given color."""
    color_name = COLOR_NAMES[color_idx]
    indices = []
    for i, label in enumerate(pair_labels):
        c1, c2 = label.split('-')
        if c1 == color_name or c2 == color_name:
            indices.append(i)
    return indices


def compute_distortion_burden(distortion, color_idx, pair_labels):
    """L2 norm of distortion for pairs involving color c.

    burden(c) = sqrt(Σ_j distortion(c,j)²)
    """
    idx = get_pairs_involving_color(color_idx, pair_labels)
    return float(np.sqrt(np.sum(distortion[idx] ** 2)))


# ============================================================================
# Level 1: V2 ↔ hV4 28-pair distortion correlation
# ============================================================================

def run_level1(preval_data):
    """Cross-ROI consistency: do the same pairs show distortion in V2 and hV4?"""
    print('\n' + '=' * 70)
    print('LEVEL 1: V2 ↔ hV4 28-pair distortion correlation')
    print('=' * 70)

    results = {}
    for subj in CVD_SUBJECTS:
        v2_dist = preval_data['V2']['cvd'][subj]['distortion']
        hv4_dist = preval_data['hV4']['cvd'][subj]['distortion']

        rho, p_rho = spearmanr(v2_dist, hv4_dist)
        r_pear, p_pear = pearsonr(v2_dist, hv4_dist)

        # Also z-scores
        v2_z = preval_data['V2']['cvd'][subj]['z_scores']
        hv4_z = preval_data['hV4']['cvd'][subj]['z_scores']
        rho_z, p_z = spearmanr(v2_z, hv4_z)

        results[subj] = {
            'distortion_spearman_r': float(rho),
            'distortion_spearman_p': float(p_rho),
            'distortion_pearson_r': float(r_pear),
            'distortion_pearson_p': float(p_pear),
            'zscore_spearman_r': float(rho_z),
            'zscore_spearman_p': float(p_z),
        }

        sig = '*' if p_rho < 0.05 else ''
        print(f'\n  {subj}:')
        print(f'    Raw distortion: Spearman r={rho:.3f} (p={p_rho:.4f}) {sig}')
        print(f'                    Pearson  r={r_pear:.3f} (p={p_pear:.4f})')
        print(f'    Z-scores:       Spearman r={rho_z:.3f} (p={p_z:.4f})')

    # Group-level: pool all 3 subjects (84 pairs)
    v2_all = np.concatenate([preval_data['V2']['cvd'][s]['distortion']
                             for s in CVD_SUBJECTS])
    hv4_all = np.concatenate([preval_data['hV4']['cvd'][s]['distortion']
                              for s in CVD_SUBJECTS])
    rho_pool, p_pool = spearmanr(v2_all, hv4_all)
    results['pooled'] = {
        'spearman_r': float(rho_pool),
        'spearman_p': float(p_pool),
        'n': len(v2_all),
    }
    sig = '*' if p_pool < 0.05 else ''
    print(f'\n  Pooled (3 subjects × 28 pairs = 84):')
    print(f'    Spearman r={rho_pool:.3f} (p={p_pool:.4f}) {sig}')

    return results


# ============================================================================
# Level 2: V2 distortion burden → hV4 LOCO error
# ============================================================================

def run_level2(preval_data, loco_data, pair_labels):
    """V2 distortion burden predicts hV4 LOCO failure?"""
    print('\n' + '=' * 70)
    print('LEVEL 2: V2 distortion burden → hV4 LOCO error (8 colors)')
    print('=' * 70)

    results = {}
    for subj in CVD_SUBJECTS:
        if subj not in loco_data:
            print(f'  {subj}: SKIP (no LOCO data)')
            continue

        v2_dist = preval_data['V2']['cvd'][subj]['distortion']
        loco_corr = loco_data[subj]['per_color_voxel_corr']  # (8,)

        # Compute V2 burden per color: L2 norm of distortion for pairs involving c
        v2_burden = np.array([
            compute_distortion_burden(v2_dist, c, pair_labels)
            for c in range(8)
        ])

        # hV4 LOCO error: lower voxel_corr = worse interpolation
        # Expect: higher V2 burden → lower LOCO corr → negative correlation
        rho, p_rho = spearmanr(v2_burden, loco_corr)
        r_pear, p_pear = pearsonr(v2_burden, loco_corr)

        results[subj] = {
            'v2_burden': v2_burden.tolist(),
            'hv4_loco_corr': loco_corr.tolist(),
            'spearman_r': float(rho),
            'spearman_p': float(p_rho),
            'pearson_r': float(r_pear),
            'pearson_p': float(p_pear),
        }

        sig = '*' if p_rho < 0.05 else ''
        print(f'\n  {subj} (mean LOCO = {loco_data[subj]["mean_voxel_corr"]:.3f}):')
        print(f'    Spearman r={rho:.3f} (p={p_rho:.4f}) {sig}')
        print(f'    Pearson  r={r_pear:.3f} (p={p_pear:.4f})')
        print(f'    Per-color:')
        print(f'    {"Color":>8s}  {"V2_burden":>10s}  {"hV4_LOCO":>9s}')
        for c in range(8):
            print(f'    {COLOR_NAMES[c]:>8s}  {v2_burden[c]:10.4f}  '
                  f'{loco_corr[c]:+9.3f}')

    # Pooled across subjects (24 color-observations)
    v2_all = []
    loco_all = []
    for subj in CVD_SUBJECTS:
        if subj not in loco_data:
            continue
        v2_dist = preval_data['V2']['cvd'][subj]['distortion']
        v2_all.extend([compute_distortion_burden(v2_dist, c, pair_labels)
                       for c in range(8)])
        loco_all.extend(loco_data[subj]['per_color_voxel_corr'].tolist())

    if v2_all:
        rho_pool, p_pool = spearmanr(v2_all, loco_all)
        results['pooled'] = {
            'spearman_r': float(rho_pool),
            'spearman_p': float(p_pool),
            'n': len(v2_all),
        }
        sig = '*' if p_pool < 0.05 else ''
        print(f'\n  Pooled (3 × 8 = 24 color-obs):')
        print(f'    Spearman r={rho_pool:.3f} (p={p_pool:.4f}) {sig}')

    return results


# ============================================================================
# Level 3: Behavioral JND ↔ V2 distortion (sub-08 only)
# ============================================================================

def run_level3(preval_data, jnd_data, pair_labels):
    """Behavioral JND ratio vs V2 distortion for sub-08."""
    print('\n' + '=' * 70)
    print('LEVEL 3: Behavioral JND ↔ V2 distortion (sub-08)')
    print('=' * 70)

    if 'HC' not in jnd_data or 'sub-08' not in jnd_data:
        print('  SKIP: behavioral data not available')
        return {}

    hc_jnd = jnd_data['HC']
    cvd_jnd = jnd_data['sub-08']

    v2_dist = preval_data['V2']['cvd']['sub-08']['distortion']

    # Match JND pairs to V2 pair indices
    matched_jnd_ratio = []
    matched_v2_dist = []
    matched_labels = []

    for pair_name in cvd_jnd:
        # JND pair names: e.g., 'orange-yellow', 'red-cyan'
        # V2 pair labels: same format
        if pair_name in pair_labels:
            idx = pair_labels.index(pair_name)
        else:
            # Try reversed order
            parts = pair_name.split('-')
            reversed_name = f'{parts[1]}-{parts[0]}'
            if reversed_name in pair_labels:
                idx = pair_labels.index(reversed_name)
            else:
                continue

        if pair_name in hc_jnd and hc_jnd[pair_name] > 0:
            jnd_ratio = cvd_jnd[pair_name] / hc_jnd[pair_name]
            matched_jnd_ratio.append(jnd_ratio)
            matched_v2_dist.append(v2_dist[idx])
            matched_labels.append(pair_name)

    matched_jnd_ratio = np.array(matched_jnd_ratio)
    matched_v2_dist = np.array(matched_v2_dist)

    if len(matched_jnd_ratio) < 4:
        print(f'  SKIP: only {len(matched_jnd_ratio)} matched pairs')
        return {}

    rho, p_rho = spearmanr(matched_jnd_ratio, matched_v2_dist)
    r_pear, p_pear = pearsonr(matched_jnd_ratio, matched_v2_dist)

    # Also: JND ratio vs absolute V2 distortion
    rho_abs, p_abs = spearmanr(matched_jnd_ratio, np.abs(matched_v2_dist))

    results = {
        'n_matched_pairs': len(matched_labels),
        'matched_pairs': matched_labels,
        'jnd_ratio': matched_jnd_ratio.tolist(),
        'v2_distortion': matched_v2_dist.tolist(),
        'spearman_r': float(rho),
        'spearman_p': float(p_rho),
        'pearson_r': float(r_pear),
        'pearson_p': float(p_pear),
        'abs_spearman_r': float(rho_abs),
        'abs_spearman_p': float(p_abs),
    }

    sig = '*' if p_rho < 0.05 else ''
    print(f'\n  Matched {len(matched_labels)} pairs:')
    print(f'    Spearman r={rho:.3f} (p={p_rho:.4f}) {sig} (signed distortion)')
    print(f'    Spearman r={rho_abs:.3f} (p={p_abs:.4f}) (|distortion|)')
    print(f'\n    {"Pair":>16s}  {"JND_ratio":>10s}  {"V2_dist":>10s}')
    for i, label in enumerate(matched_labels):
        direction = 'CVD worse' if matched_jnd_ratio[i] > 1.2 else (
            'CVD better' if matched_jnd_ratio[i] < 0.8 else 'similar')
        print(f'    {label:>16s}  {matched_jnd_ratio[i]:10.2f}  '
              f'{matched_v2_dist[i]:+10.4f}  {direction}')

    return results


# ============================================================================
# Q2: Per-subject signal sufficiency
# ============================================================================

def run_signal_assessment(preval_data, pair_labels):
    """Assess whether each CVD subject has sufficient V2 distortion signal."""
    print('\n' + '=' * 70)
    print('SIGNAL SUFFICIENCY: Per-subject V2 distortion assessment')
    print('=' * 70)

    results = {}
    for subj in CVD_SUBJECTS:
        z = preval_data['V2']['cvd'][subj]['z_scores']
        dist = preval_data['V2']['cvd'][subj]['distortion']

        # 1. Pairs outside HC range
        n_sig = int(np.sum(np.abs(z) > 1.96))
        n_trending = int(np.sum(np.abs(z) > 1.5))

        # 2. Split-half reliability
        sh_fl = preval_data['V2']['split_half']['first_last'][subj]
        sh_oe = preval_data['V2']['split_half']['odd_even'][subj]
        mean_sh_r = (sh_fl['spearman_r'] + sh_oe['spearman_r']) / 2

        # 3. Effect size: mean |distortion| / HC std
        hc_std = preval_data['V2']['hc_std']
        # Avoid division by zero
        safe_std = np.where(hc_std > 0, hc_std, 1.0)
        effect_sizes = np.abs(dist) / safe_std
        mean_effect = float(np.mean(effect_sizes))
        max_effect = float(np.max(effect_sizes))

        # 4. Top distorted pairs
        top_idx = np.argsort(np.abs(z))[::-1][:5]
        top_pairs = [(pair_labels[i], float(z[i])) for i in top_idx]

        # Verdict
        sufficient = n_sig >= 3 and mean_sh_r > 0.5
        verdict = 'SUFFICIENT' if sufficient else 'INSUFFICIENT'

        results[subj] = {
            'n_pairs_sig': n_sig,
            'n_pairs_trending': n_trending,
            'split_half_mean_r': float(mean_sh_r),
            'split_half_first_last': sh_fl,
            'split_half_odd_even': sh_oe,
            'mean_effect_size': mean_effect,
            'max_effect_size': max_effect,
            'top_5_pairs': top_pairs,
            'verdict': verdict,
        }

        print(f'\n  {subj}:')
        print(f'    |z| > 1.96: {n_sig}/28 pairs')
        print(f'    |z| > 1.50: {n_trending}/28 pairs')
        print(f'    Split-half mean r: {mean_sh_r:.3f}')
        print(f'      first_last: r={sh_fl["spearman_r"]:.3f} '
              f'(p={sh_fl["spearman_p"]:.4f})')
        print(f'      odd_even:   r={sh_oe["spearman_r"]:.3f} '
              f'(p={sh_oe["spearman_p"]:.4f})')
        print(f'    Mean effect size (|d|/SD): {mean_effect:.2f}')
        print(f'    Max effect size: {max_effect:.2f}')
        print(f'    Top 5 pairs: '
              + ', '.join(f'{p} (z={z:.1f})' for p, z in top_pairs))
        print(f'    → {verdict}')

    return results


# ============================================================================
# Main
# ============================================================================

def main():
    print('Loading data...')
    preval_data, pair_labels = load_preval_data()
    loco_data = load_loco_data()
    jnd_data = load_behavioral_jnd()

    print(f'  Pre-validation: V2 ({len(preval_data["V2"]["cvd"])} CVD), '
          f'hV4 ({len(preval_data["hV4"]["cvd"])} CVD)')
    print(f'  LOCO: {len(loco_data)} subjects')
    print(f'  JND: {list(jnd_data.keys())}')

    # Run analyses
    level1 = run_level1(preval_data)
    level2 = run_level2(preval_data, loco_data, pair_labels)
    level3 = run_level3(preval_data, jnd_data, pair_labels)
    signal = run_signal_assessment(preval_data, pair_labels)

    # Summary verdict
    print('\n' + '=' * 70)
    print('VERDICT SUMMARY')
    print('=' * 70)

    l1_pass = any(level1[s].get('distortion_spearman_p', 1) < 0.05
                  for s in CVD_SUBJECTS)
    l1_pool = level1.get('pooled', {}).get('spearman_p', 1) < 0.05

    l2_pass = any(level2.get(s, {}).get('spearman_p', 1) < 0.05
                  for s in CVD_SUBJECTS)

    print(f'  Level 1 (V2↔hV4 pair distortion):')
    print(f'    Any individual significant: {l1_pass}')
    print(f'    Pooled significant: {l1_pool}')
    if l1_pass or l1_pool:
        print(f'    → PASS: Cross-ROI consistency confirmed')
    else:
        print(f'    → FAIL: V2 and hV4 distortions may be independent')

    print(f'  Level 2 (V2 burden → hV4 LOCO):')
    print(f'    Any individual significant: {l2_pass}')
    if l2_pass:
        print(f'    → PASS: V2 distortion predicts hV4 interpolation failure')
    else:
        print(f'    → CAUTION: V2 burden may not predict hV4 LOCO')

    print(f'  Signal sufficiency:')
    for subj in CVD_SUBJECTS:
        v = signal[subj]['verdict']
        print(f'    {subj}: {v}')

    # Pipeline recommendation
    if l1_pass or l1_pool:
        rec = 'PROCEED with V2-based loss + hV4 LOCO evaluation'
    elif l2_pass:
        rec = 'PROCEED cautiously (V2→LOCO link exists but ROI consistency weak)'
    else:
        rec = 'RECONSIDER: switch to single-ROI (hV4 only) filter design'
    print(f'\n  Recommendation: {rec}')

    # Save results
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    all_results = {
        'level1_cross_roi': level1,
        'level2_burden_loco': level2,
        'level3_behavioral': level3,
        'signal_sufficiency': signal,
        'recommendation': rec,
    }

    out_path = OUTPUT_DIR / 'cross_roi_consistency.json'
    with open(out_path, 'w') as f:
        json.dump(all_results, f, indent=2)
    print(f'\nResults saved to {out_path}')


if __name__ == '__main__':
    main()
