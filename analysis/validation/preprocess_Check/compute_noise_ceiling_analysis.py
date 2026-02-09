#!/usr/bin/env python3
"""
Comprehensive Noise Ceiling Analysis for C010+Procrustes Pipeline

Computes detailed noise ceiling metrics matching NOISE_CEILING_CLEAN_SUMMARY.md format

Author: Claude Code
Date: 2026-02-09
"""

import numpy as np
import json
from pathlib import Path
from scipy.stats import spearmanr
import sys

# Configuration
DATA_DIR = Path(__file__).parent / "full_dataset_C010_with_residuals"
OUTPUT_FILE = Path(__file__).parent / "noise_ceiling_analysis.json"

SUBJECTS = ['02', '03', '04', '05', '06', '07', '08', '09', '10', '11']
ROIS = ['V1', 'V2', 'V3', 'V4']

N_COLORS = 8
N_RUNS = 6


# ============================================================================
# Core Functions (from utils/noise_ceiling.py)
# ============================================================================

def compute_split_half_oddeven(amplitudes):
    """
    Compute odd/even split-half noise ceiling (Primary Method)

    Reference: Diedrichsen et al. (2016), Schütt et al. (2021)

    Args:
        amplitudes: (n_runs, n_colors, n_voxels)

    Returns:
        dict with 'corrected' and 'raw' reliability
    """
    n_runs, n_colors, n_voxels = amplitudes.shape

    if n_runs < 4:
        return {'corrected': np.nan, 'raw': np.nan}

    # Split by index
    odd_indices = np.arange(0, n_runs, 2)  # [0, 2, 4]
    even_indices = np.arange(1, n_runs, 2)  # [1, 3, 5]

    # Average within each half
    odd_patterns = amplitudes[odd_indices].mean(axis=0)  # (n_colors, n_voxels)
    even_patterns = amplitudes[even_indices].mean(axis=0)

    # Compute RDMs (correlation distance)
    rdm_odd = 1 - np.corrcoef(odd_patterns)
    rdm_even = 1 - np.corrcoef(even_patterns)

    # Upper triangle vectorization
    mask = np.triu(np.ones_like(rdm_odd, dtype=bool), k=1)
    rdm_odd_vec = rdm_odd[mask]
    rdm_even_vec = rdm_even[mask]

    # Spearman correlation
    r_half, _ = spearmanr(rdm_odd_vec, rdm_even_vec)

    # Spearman-Brown correction
    r_full = 2 * r_half / (1 + r_half) if r_half < 1 else 1.0

    return {'corrected': r_full, 'raw': r_half}


def compute_split_half_random(amplitudes, n_iterations=1000, random_seed=42):
    """
    Compute random split-half noise ceiling (Secondary Method)

    Args:
        amplitudes: (n_runs, n_colors, n_voxels)
        n_iterations: number of random splits
        random_seed: for reproducibility

    Returns:
        dict with 'corrected', 'raw', and 'std'
    """
    n_runs, n_colors, n_voxels = amplitudes.shape

    if n_runs < 4:
        return {'corrected': np.nan, 'raw': np.nan, 'std': np.nan}

    np.random.seed(random_seed)
    correlations = []

    for _ in range(n_iterations):
        # Random permutation
        run_indices = np.random.permutation(n_runs)
        split_point = n_runs // 2

        half1_runs = run_indices[:split_point]
        half2_runs = run_indices[split_point:2*split_point]

        half1_patterns = amplitudes[half1_runs].mean(axis=0)
        half2_patterns = amplitudes[half2_runs].mean(axis=0)

        # RDMs
        rdm1 = 1 - np.corrcoef(half1_patterns)
        rdm2 = 1 - np.corrcoef(half2_patterns)

        # Correlation
        mask = np.triu(np.ones_like(rdm1, dtype=bool), k=1)
        r, _ = spearmanr(rdm1[mask], rdm2[mask])
        correlations.append(r)

    correlations = np.array(correlations)
    correlations = correlations[np.isfinite(correlations)]

    r_half = np.mean(correlations)
    r_std = np.std(correlations)
    r_full = 2 * r_half / (1 + r_half) if r_half < 1 else 1.0

    return {'corrected': r_full, 'raw': r_half, 'std': r_std}


def compute_rdm_reliability(amplitudes):
    """
    Compute RDM reliability (same as metrics.json)

    Args:
        amplitudes: (n_runs, n_colors, n_voxels)

    Returns:
        float: RDM reliability
    """
    results_random = compute_split_half_random(amplitudes, n_iterations=100)
    results_oddeven = compute_split_half_oddeven(amplitudes)

    # Average of raw correlations
    rdm_reliability = (results_random['raw'] + results_oddeven['raw']) / 2

    return rdm_reliability


# ============================================================================
# Data Loading
# ============================================================================

def load_all_data():
    """Load all subject-ROI data"""
    all_data = {}

    for subject in SUBJECTS:
        for roi in ROIS:
            data_path = DATA_DIR / f"sub-{subject}" / roi

            if not data_path.exists():
                continue

            # Load amplitudes
            amplitudes_raw = np.load(data_path / "amplitudes_raw.npy")
            amplitudes_proc = np.load(data_path / "amplitudes_procrustes.npy")

            # Load metrics
            with open(data_path / "metrics.json", 'r') as f:
                metrics = json.load(f)

            key = f"sub-{subject}_{roi}"
            all_data[key] = {
                'subject': subject,
                'roi': roi,
                'amplitudes_raw': amplitudes_raw,
                'amplitudes_proc': amplitudes_proc,
                'metrics': metrics
            }

    return all_data


# ============================================================================
# Comprehensive Analysis
# ============================================================================

def compute_comprehensive_analysis(all_data):
    """
    Compute comprehensive noise ceiling analysis

    Returns:
        Dictionary with all metrics for markdown generation
    """

    print("Computing comprehensive noise ceiling analysis...")

    results = {
        'summary': {},
        'by_roi': {},
        'by_subject_roi': {},
        'temporal_analysis': {},
        'performance_vs_ceiling': {}
    }

    # Organize by ROI
    roi_data = {roi: [] for roi in ROIS}

    for key, data in all_data.items():
        roi = data['roi']
        roi_data[roi].append((key, data))

    # ========================================================================
    # 1. ROI-level Analysis
    # ========================================================================

    print("\n1. Computing ROI-level statistics...")

    for roi in ROIS:
        pairs = roi_data[roi]
        n_pairs = len(pairs)

        if n_pairs == 0:
            continue

        # Collect metrics
        oddeven_raw = []
        oddeven_proc = []
        random_raw = []
        random_proc = []
        rdm_raw = []
        rdm_proc = []

        for key, data in pairs:
            amplitudes_raw = data['amplitudes_raw']
            amplitudes_proc = data['amplitudes_proc']

            # Odd/even
            oe_raw = compute_split_half_oddeven(amplitudes_raw)
            oe_proc = compute_split_half_oddeven(amplitudes_proc)
            oddeven_raw.append(oe_raw['corrected'])
            oddeven_proc.append(oe_proc['corrected'])

            # Random
            rand_raw = compute_split_half_random(amplitudes_raw, n_iterations=100)
            rand_proc = compute_split_half_random(amplitudes_proc, n_iterations=100)
            random_raw.append(rand_raw['corrected'])
            random_proc.append(rand_proc['corrected'])

            # RDM reliability
            rdm_raw.append(data['metrics']['raw_rdm_reliability'])
            rdm_proc.append(data['metrics']['procrustes_rdm_reliability'])

        # Convert to arrays
        oddeven_raw = np.array(oddeven_raw)
        oddeven_proc = np.array(oddeven_proc)
        random_raw = np.array(random_raw)
        random_proc = np.array(random_proc)
        rdm_raw = np.array(rdm_raw)
        rdm_proc = np.array(rdm_proc)

        # Store ROI statistics
        results['by_roi'][roi] = {
            'n': n_pairs,
            'ceiling_oddeven_raw': {
                'mean': float(np.mean(oddeven_raw)),
                'std': float(np.std(oddeven_raw)),
                'min': float(np.min(oddeven_raw)),
                'max': float(np.max(oddeven_raw)),
                'median': float(np.median(oddeven_raw))
            },
            'ceiling_oddeven_proc': {
                'mean': float(np.mean(oddeven_proc)),
                'std': float(np.std(oddeven_proc)),
                'min': float(np.min(oddeven_proc)),
                'max': float(np.max(oddeven_proc)),
                'median': float(np.median(oddeven_proc))
            },
            'ceiling_random_raw': {
                'mean': float(np.mean(random_raw)),
                'std': float(np.std(random_raw)),
            },
            'ceiling_random_proc': {
                'mean': float(np.mean(random_proc)),
                'std': float(np.std(random_proc)),
            },
            'rdm_reliability_raw': {
                'mean': float(np.mean(rdm_raw)),
                'std': float(np.std(rdm_raw)),
            },
            'rdm_reliability_proc': {
                'mean': float(np.mean(rdm_proc)),
                'std': float(np.std(rdm_proc)),
            },
            'percent_utilized_raw': float(np.mean(rdm_raw) / np.mean(oddeven_raw) * 100) if np.mean(oddeven_raw) > 0 else 0,
            'percent_utilized_proc': float(np.mean(rdm_proc) / np.mean(oddeven_proc) * 100) if np.mean(oddeven_proc) > 0 else 0,
        }

        print(f"  {roi}: n={n_pairs}, ceiling={np.mean(oddeven_proc):.3f}, utilization={results['by_roi'][roi]['percent_utilized_proc']:.1f}%")

    # ========================================================================
    # 2. Subject-ROI Level Analysis
    # ========================================================================

    print("\n2. Computing subject-ROI level statistics...")

    for key, data in all_data.items():
        amplitudes_raw = data['amplitudes_raw']
        amplitudes_proc = data['amplitudes_proc']

        # Compute all metrics
        oe_raw = compute_split_half_oddeven(amplitudes_raw)
        oe_proc = compute_split_half_oddeven(amplitudes_proc)

        rand_raw = compute_split_half_random(amplitudes_raw, n_iterations=100)
        rand_proc = compute_split_half_random(amplitudes_proc, n_iterations=100)

        rdm_raw = data['metrics']['raw_rdm_reliability']
        rdm_proc = data['metrics']['procrustes_rdm_reliability']

        # Method difference (temporal stability indicator)
        method_diff_raw = abs(rand_raw['corrected'] - oe_raw['corrected'])
        method_diff_proc = abs(rand_proc['corrected'] - oe_proc['corrected'])

        # Percent utilized
        pct_util_raw = (rdm_raw / oe_raw['corrected'] * 100) if oe_raw['corrected'] > 0 else 0
        pct_util_proc = (rdm_proc / oe_proc['corrected'] * 100) if oe_proc['corrected'] > 0 else 0

        results['by_subject_roi'][key] = {
            'subject': data['subject'],
            'roi': data['roi'],
            'ceiling_oddeven_raw': oe_raw['corrected'],
            'ceiling_oddeven_proc': oe_proc['corrected'],
            'ceiling_random_raw': rand_raw['corrected'],
            'ceiling_random_proc': rand_proc['corrected'],
            'rdm_reliability_raw': rdm_raw,
            'rdm_reliability_proc': rdm_proc,
            'method_diff_raw': method_diff_raw,
            'method_diff_proc': method_diff_proc,
            'percent_utilized_raw': pct_util_raw,
            'percent_utilized_proc': pct_util_proc,
        }

    # ========================================================================
    # 3. Temporal Analysis (Method Difference)
    # ========================================================================

    print("\n3. Computing temporal stability analysis...")

    method_diffs_raw = []
    method_diffs_proc = []

    for key, metrics in results['by_subject_roi'].items():
        method_diffs_raw.append(metrics['method_diff_raw'])
        method_diffs_proc.append(metrics['method_diff_proc'])

    method_diffs_raw = np.array(method_diffs_raw)
    method_diffs_proc = np.array(method_diffs_proc)

    # Distribution analysis
    results['temporal_analysis'] = {
        'method_diff_raw': {
            'mean': float(np.mean(method_diffs_raw)),
            'std': float(np.std(method_diffs_raw)),
            'median': float(np.median(method_diffs_raw)),
            'min': float(np.min(method_diffs_raw)),
            'max': float(np.max(method_diffs_raw)),
        },
        'method_diff_proc': {
            'mean': float(np.mean(method_diffs_proc)),
            'std': float(np.std(method_diffs_proc)),
            'median': float(np.median(method_diffs_proc)),
            'min': float(np.min(method_diffs_proc)),
            'max': float(np.max(method_diffs_proc)),
        },
        'distribution_raw': {
            'excellent': int(np.sum(method_diffs_raw < 0.05)),
            'good': int(np.sum((method_diffs_raw >= 0.05) & (method_diffs_raw < 0.10))),
            'moderate': int(np.sum((method_diffs_raw >= 0.10) & (method_diffs_raw < 0.15))),
            'poor': int(np.sum(method_diffs_raw >= 0.15)),
        },
        'distribution_proc': {
            'excellent': int(np.sum(method_diffs_proc < 0.05)),
            'good': int(np.sum((method_diffs_proc >= 0.05) & (method_diffs_proc < 0.10))),
            'moderate': int(np.sum((method_diffs_proc >= 0.10) & (method_diffs_proc < 0.15))),
            'poor': int(np.sum(method_diffs_proc >= 0.15)),
        }
    }

    # Top/bottom subject-ROI pairs
    sorted_keys_raw = sorted(results['by_subject_roi'].keys(),
                             key=lambda k: results['by_subject_roi'][k]['method_diff_raw'],
                             reverse=True)

    sorted_keys_proc = sorted(results['by_subject_roi'].keys(),
                              key=lambda k: results['by_subject_roi'][k]['method_diff_proc'],
                              reverse=True)

    results['temporal_analysis']['worst_drift_raw'] = [
        {
            'key': k,
            'subject': results['by_subject_roi'][k]['subject'],
            'roi': results['by_subject_roi'][k]['roi'],
            'method_diff': results['by_subject_roi'][k]['method_diff_raw'],
            'ceiling_random': results['by_subject_roi'][k]['ceiling_random_raw'],
            'ceiling_oddeven': results['by_subject_roi'][k]['ceiling_oddeven_raw'],
        }
        for k in sorted_keys_raw[:10]
    ]

    results['temporal_analysis']['best_stability_raw'] = [
        {
            'key': k,
            'subject': results['by_subject_roi'][k]['subject'],
            'roi': results['by_subject_roi'][k]['roi'],
            'method_diff': results['by_subject_roi'][k]['method_diff_raw'],
            'ceiling_random': results['by_subject_roi'][k]['ceiling_random_raw'],
            'ceiling_oddeven': results['by_subject_roi'][k]['ceiling_oddeven_raw'],
        }
        for k in sorted_keys_raw[-10:]
    ]

    # Same for Procrustes
    results['temporal_analysis']['worst_drift_proc'] = [
        {
            'key': k,
            'subject': results['by_subject_roi'][k]['subject'],
            'roi': results['by_subject_roi'][k]['roi'],
            'method_diff': results['by_subject_roi'][k]['method_diff_proc'],
            'ceiling_random': results['by_subject_roi'][k]['ceiling_random_proc'],
            'ceiling_oddeven': results['by_subject_roi'][k]['ceiling_oddeven_proc'],
        }
        for k in sorted_keys_proc[:10]
    ]

    results['temporal_analysis']['best_stability_proc'] = [
        {
            'key': k,
            'subject': results['by_subject_roi'][k]['subject'],
            'roi': results['by_subject_roi'][k]['roi'],
            'method_diff': results['by_subject_roi'][k]['method_diff_proc'],
            'ceiling_random': results['by_subject_roi'][k]['ceiling_random_proc'],
            'ceiling_oddeven': results['by_subject_roi'][k]['ceiling_oddeven_proc'],
        }
        for k in sorted_keys_proc[-10:]
    ]

    # ========================================================================
    # 4. Summary Statistics
    # ========================================================================

    print("\n4. Computing overall summary...")

    all_ceiling_raw = [m['ceiling_oddeven_raw'] for m in results['by_subject_roi'].values()]
    all_ceiling_proc = [m['ceiling_oddeven_proc'] for m in results['by_subject_roi'].values()]
    all_rdm_raw = [m['rdm_reliability_raw'] for m in results['by_subject_roi'].values()]
    all_rdm_proc = [m['rdm_reliability_proc'] for m in results['by_subject_roi'].values()]
    all_pct_raw = [m['percent_utilized_raw'] for m in results['by_subject_roi'].values()]
    all_pct_proc = [m['percent_utilized_proc'] for m in results['by_subject_roi'].values()]

    results['summary'] = {
        'n_total': len(all_data),
        'n_subjects': len(set(d['subject'] for d in all_data.values())),
        'n_rois': len(ROIS),
        'ceiling_oddeven_raw': {
            'mean': float(np.mean(all_ceiling_raw)),
            'std': float(np.std(all_ceiling_raw)),
            'min': float(np.min(all_ceiling_raw)),
            'max': float(np.max(all_ceiling_raw)),
        },
        'ceiling_oddeven_proc': {
            'mean': float(np.mean(all_ceiling_proc)),
            'std': float(np.std(all_ceiling_proc)),
            'min': float(np.min(all_ceiling_proc)),
            'max': float(np.max(all_ceiling_proc)),
        },
        'rdm_reliability_raw': {
            'mean': float(np.mean(all_rdm_raw)),
            'std': float(np.std(all_rdm_raw)),
        },
        'rdm_reliability_proc': {
            'mean': float(np.mean(all_rdm_proc)),
            'std': float(np.std(all_rdm_proc)),
        },
        'percent_utilized_raw': {
            'mean': float(np.mean(all_pct_raw)),
            'std': float(np.std(all_pct_raw)),
        },
        'percent_utilized_proc': {
            'mean': float(np.mean(all_pct_proc)),
            'std': float(np.std(all_pct_proc)),
        },
    }

    print(f"\n  Total pairs: {results['summary']['n_total']}")
    print(f"  Ceiling (Procrustes): {results['summary']['ceiling_oddeven_proc']['mean']:.3f} ± {results['summary']['ceiling_oddeven_proc']['std']:.3f}")
    print(f"  RDM Reliability (Procrustes): {results['summary']['rdm_reliability_proc']['mean']:.3f} ± {results['summary']['rdm_reliability_proc']['std']:.3f}")
    print(f"  Utilization (Procrustes): {results['summary']['percent_utilized_proc']['mean']:.1f}% ± {results['summary']['percent_utilized_proc']['std']:.1f}%")

    return results


# ============================================================================
# Main
# ============================================================================

def main():
    print(f"\n{'='*80}")
    print(f"Comprehensive Noise Ceiling Analysis: C010+Procrustes Pipeline")
    print(f"{'='*80}\n")

    # Load data
    print("Loading data...")
    all_data = load_all_data()
    print(f"✓ Loaded {len(all_data)} subject-ROI pairs")

    # Compute analysis
    results = compute_comprehensive_analysis(all_data)

    # Save results
    print(f"\nSaving results to: {OUTPUT_FILE}")
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n{'='*80}")
    print(f"✓ Analysis complete!")
    print(f"{'='*80}\n")

    return results


if __name__ == '__main__':
    results = main()
