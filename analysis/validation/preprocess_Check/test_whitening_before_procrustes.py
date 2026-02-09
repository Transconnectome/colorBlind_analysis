#!/usr/bin/env python3
"""
Test Whitening BEFORE Procrustes (Correct Order)

Compare four pipelines:
1. Raw alone
2. Raw → Procrustes (current best)
3. Raw → Whitening → Procrustes (NEW - theoretically correct)
4. Raw → Procrustes → Whitening (tested - failed)
"""

import numpy as np
import json
from pathlib import Path
from scipy.stats import spearmanr
from scipy.linalg import orthogonal_procrustes
from sklearn.covariance import LedoitWolf
# Constants
N_RUNS = 6
N_COLORS = 8
SUBJECTS = [f'sub-{i:02d}' for i in range(1, 11)]
ROIS = ['V1', 'V2', 'V3', 'V4']

# ============================================================================
# Noise Ceiling Functions (implemented directly to avoid import issues)
# ============================================================================

def compute_split_half_reliability(amplitudes, n_iterations=100, random_seed=42):
    """Compute random split-half reliability with Spearman-Brown correction"""
    np.random.seed(random_seed)
    n_runs, n_colors, n_voxels = amplitudes.shape

    if n_runs < 4:
        return {'corrected': np.nan, 'raw': np.nan}

    correlations = []

    for _ in range(n_iterations):
        # Random split of runs
        run_indices = np.random.permutation(n_runs)
        split_point = n_runs // 2

        half1_runs = run_indices[:split_point]
        half2_runs = run_indices[split_point:2*split_point]

        # Average patterns within each half
        half1_patterns = amplitudes[half1_runs].mean(axis=0)
        half2_patterns = amplitudes[half2_runs].mean(axis=0)

        # Compute RDMs
        rdm1 = 1 - np.corrcoef(half1_patterns)
        rdm2 = 1 - np.corrcoef(half2_patterns)

        # Vectorize upper triangle
        mask = np.triu(np.ones_like(rdm1, dtype=bool), k=1)
        rdm1_vec = rdm1[mask]
        rdm2_vec = rdm2[mask]

        # Spearman correlation
        r, _ = spearmanr(rdm1_vec, rdm2_vec)
        correlations.append(r)

    correlations = np.array(correlations)
    correlations = correlations[np.isfinite(correlations)]

    r_half = np.mean(correlations)
    r_corrected = 2 * r_half / (1 + r_half) if r_half < 1 else 1.0

    return {'corrected': r_corrected, 'raw': r_half}


def compute_split_half_odd_even(amplitudes):
    """Compute odd/even split-half reliability with Spearman-Brown correction"""
    n_runs, n_colors, n_voxels = amplitudes.shape

    if n_runs < 4:
        return {'corrected': np.nan, 'raw': np.nan}

    # Split by index: odd (0,2,4) vs even (1,3,5)
    odd_indices = np.arange(0, n_runs, 2)
    even_indices = np.arange(1, n_runs, 2)

    # Average patterns within each group
    odd_patterns = amplitudes[odd_indices].mean(axis=0)
    even_patterns = amplitudes[even_indices].mean(axis=0)

    # Compute RDMs
    rdm_odd = 1 - np.corrcoef(odd_patterns)
    rdm_even = 1 - np.corrcoef(even_patterns)

    # Vectorize upper triangle
    mask = np.triu(np.ones_like(rdm_odd, dtype=bool), k=1)
    rdm_odd_vec = rdm_odd[mask]
    rdm_even_vec = rdm_even[mask]

    # Spearman correlation
    r_half, _ = spearmanr(rdm_odd_vec, rdm_even_vec)

    # Spearman-Brown correction
    r_corrected = 2 * r_half / (1 + r_half) if r_half < 1 else 1.0

    return {'corrected': r_corrected, 'raw': r_half}

# ============================================================================
# Pipeline Functions
# ============================================================================

def apply_procrustes_alignment(amplitudes):
    """Apply Procrustes alignment to align all runs to run 0"""
    n_runs, n_colors, n_voxels = amplitudes.shape
    aligned = np.zeros_like(amplitudes)

    # Reference: first run
    reference = amplitudes[0].copy()
    aligned[0] = reference

    # Align subsequent runs
    for run_idx in range(1, n_runs):
        target = amplitudes[run_idx]

        # Procrustes: find optimal rotation R
        R, scale = orthogonal_procrustes(target.T, reference.T)

        # Apply transformation
        aligned_run = (target.T @ R).T
        aligned[run_idx] = aligned_run

    return aligned

def preprocess_residuals_run_wise(residuals, n_runs=6):
    """Remove run-wise intercepts from residuals"""
    n_samples, n_voxels = residuals.shape

    # Handle variable-length runs
    samples_per_run = n_samples // n_runs
    residuals_centered = residuals.copy()

    for run_idx in range(n_runs):
        start_idx = run_idx * samples_per_run
        end_idx = start_idx + samples_per_run if run_idx < n_runs - 1 else n_samples

        run_residuals = residuals[start_idx:end_idx]
        run_mean = run_residuals.mean(axis=0, keepdims=True)
        residuals_centered[start_idx:end_idx] = run_residuals - run_mean

    return residuals_centered

def estimate_noise_covariance_from_residuals(residuals):
    """Estimate noise covariance using Ledoit-Wolf on residuals"""
    lw = LedoitWolf(assume_centered=False)
    lw.fit(residuals)

    return lw.covariance_, lw.shrinkage_

def whiten_amplitudes(amplitudes, cov_noise):
    """
    Apply whitening transformation to amplitudes

    Args:
        amplitudes: (n_runs, n_colors, n_voxels)
        cov_noise: (n_voxels, n_voxels) - Noise covariance matrix

    Returns:
        amplitudes_whitened: (n_runs, n_colors, n_voxels)
    """
    n_runs, n_colors, n_voxels = amplitudes.shape

    # Compute whitening matrix: W = Σ^(-1/2)
    eigenvalues, eigenvectors = np.linalg.eigh(cov_noise)

    # Regularize small eigenvalues
    eigenvalues = np.maximum(eigenvalues, 1e-10)

    # Whitening matrix: V @ diag(1/sqrt(λ)) @ V.T
    whitening_matrix = eigenvectors @ np.diag(1.0 / np.sqrt(eigenvalues)) @ eigenvectors.T

    # Apply whitening to each run
    amplitudes_whitened = np.zeros_like(amplitudes)

    for run_idx in range(n_runs):
        patterns = amplitudes[run_idx]  # (n_colors, n_voxels)

        # Whiten: patterns_white = patterns @ W
        patterns_whitened = patterns @ whitening_matrix
        amplitudes_whitened[run_idx] = patterns_whitened

    return amplitudes_whitened

def compute_rdm_reliability(amplitudes):
    """Compute RDM reliability using odd/even split"""
    n_runs, n_colors, n_voxels = amplitudes.shape

    # Split runs
    odd_runs = amplitudes[0::2]
    even_runs = amplitudes[1::2]

    # Average within each group
    odd_avg = odd_runs.mean(axis=0)
    even_avg = even_runs.mean(axis=0)

    # Compute RDMs
    rdm_odd = 1 - np.corrcoef(odd_avg)
    rdm_even = 1 - np.corrcoef(even_avg)

    # Vectorize upper triangle
    triu_idx = np.triu_indices(n_colors, k=1)
    rdm_odd_vec = rdm_odd[triu_idx]
    rdm_even_vec = rdm_even[triu_idx]

    # Spearman correlation
    rho, _ = spearmanr(rdm_odd_vec, rdm_even_vec)

    return rho


def analyze_pair(subject, roi, data_dir):
    """Analyze one subject-ROI pair with four pipelines"""
    amp_path = data_dir / subject / roi / 'amplitudes_raw.npy'
    res_path = data_dir / subject / roi / 'residuals_2nd_level.npy'  # NEW: 2nd-level residuals

    if not amp_path.exists():
        print(f"  ❌ Amplitudes not found: {subject}/{roi}")
        return None

    if not res_path.exists():
        print(f"  ⚠️ Residuals not found: {subject}/{roi}")
        return None

    # Load data
    amplitudes_raw = np.load(amp_path)
    residuals = np.load(res_path)

    # Check voxel match
    n_voxels_amp = amplitudes_raw.shape[2]
    n_voxels_res = residuals.shape[1]

    if n_voxels_amp != n_voxels_res:
        print(f"  ❌ Voxel mismatch: amp={n_voxels_amp}, res={n_voxels_res}")
        return None

    n_voxels = n_voxels_amp

    # === PIPELINE 1: RAW ALONE ===
    nc_raw = compute_split_half_odd_even(amplitudes_raw)['corrected']
    rdm_raw = compute_rdm_reliability(amplitudes_raw)

    # === PIPELINE 2: RAW → PROCRUSTES ===
    amplitudes_proc = apply_procrustes_alignment(amplitudes_raw)
    nc_proc = compute_split_half_odd_even(amplitudes_proc)['corrected']
    rdm_proc = compute_rdm_reliability(amplitudes_proc)

    # === PIPELINE 3: RAW → WHITENING → PROCRUSTES (NEW!) ===
    # Step 1: Estimate noise covariance from residuals (correct method)
    residuals_centered = preprocess_residuals_run_wise(residuals, n_runs=6)
    cov_noise, shrinkage = estimate_noise_covariance_from_residuals(residuals_centered)

    # Step 2: Whiten raw amplitudes
    amplitudes_whitened = whiten_amplitudes(amplitudes_raw, cov_noise)

    # Step 3: Procrustes on whitened amplitudes
    amplitudes_white_proc = apply_procrustes_alignment(amplitudes_whitened)
    nc_white_proc = compute_split_half_odd_even(amplitudes_white_proc)['corrected']
    rdm_white_proc = compute_rdm_reliability(amplitudes_white_proc)

    # === PIPELINE 4: RAW → PROCRUSTES → WHITENING (tested, failed) ===
    # Use Procrustes-aligned amplitudes for covariance (wrong method)
    cov_signal, shrinkage_signal = estimate_noise_covariance_from_residuals(
        amplitudes_proc.reshape(-1, n_voxels)
    )
    amplitudes_proc_white = whiten_amplitudes(amplitudes_proc, cov_signal)
    nc_proc_white = compute_split_half_odd_even(amplitudes_proc_white)['corrected']
    rdm_proc_white = compute_rdm_reliability(amplitudes_proc_white)

    # === COMPUTE IMPROVEMENTS ===
    proc_improvement = rdm_proc - rdm_raw
    white_proc_improvement = rdm_white_proc - rdm_raw
    proc_white_improvement = rdm_proc_white - rdm_raw

    results = {
        'subject': subject,
        'roi': roi,
        'n_voxels': n_voxels,

        # Pipeline 1: Raw
        'raw': {
            'nc_oddeven': float(nc_raw),
            'rdm_reliability': float(rdm_raw),
        },

        # Pipeline 2: Raw → Procrustes
        'raw_proc': {
            'nc_oddeven': float(nc_proc),
            'rdm_reliability': float(rdm_proc),
        },

        # Pipeline 3: Raw → Whitening → Procrustes (NEW)
        'raw_white_proc': {
            'nc_oddeven': float(nc_white_proc),
            'rdm_reliability': float(rdm_white_proc),
            'shrinkage': float(shrinkage),
        },

        # Pipeline 4: Raw → Procrustes → Whitening
        'raw_proc_white': {
            'nc_oddeven': float(nc_proc_white),
            'rdm_reliability': float(rdm_proc_white),
            'shrinkage': float(shrinkage_signal),
        },

        # Improvements from raw
        'improvement': {
            'proc': float(proc_improvement),
            'white_proc': float(white_proc_improvement),
            'proc_white': float(proc_white_improvement),
        }
    }

    return results

def main():
    # Server path
    data_dir = Path('/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010_with_residuals')

    print("=" * 80)
    print("Four-Way Pipeline Comparison (with 2nd-level residuals)")
    print("=" * 80)
    print()
    print("Pipelines:")
    print("  1. Raw alone (baseline)")
    print("  2. Raw → Procrustes (current best)")
    print("  3. Raw → Whitening → Procrustes (NEW - theoretically correct)")
    print("  4. Raw → Procrustes → Whitening (tested - failed)")
    print()
    print("Key difference: Using 2nd-level GLM residuals for noise covariance")
    print()
    print("=" * 80)
    print()

    all_results = []

    for subject in SUBJECTS:
        print(f"Processing {subject}...")
        for roi in ROIS:
            result = analyze_pair(subject, roi, data_dir)
            if result is not None:
                all_results.append(result)

                # Print summary
                raw = result['raw']['rdm_reliability']
                proc = result['raw_proc']['rdm_reliability']
                white_proc = result['raw_white_proc']['rdm_reliability']
                proc_white = result['raw_proc_white']['rdm_reliability']

                print(f"  {roi}: {raw:+.3f} → P:{proc:+.3f} | WP:{white_proc:+.3f} | PW:{proc_white:+.3f}")

    print()
    print("=" * 80)

    # === AGGREGATE STATISTICS ===
    raw_rdm = np.array([r['raw']['rdm_reliability'] for r in all_results])
    proc_rdm = np.array([r['raw_proc']['rdm_reliability'] for r in all_results])
    white_proc_rdm = np.array([r['raw_white_proc']['rdm_reliability'] for r in all_results])
    proc_white_rdm = np.array([r['raw_proc_white']['rdm_reliability'] for r in all_results])

    raw_nc = np.array([r['raw']['nc_oddeven'] for r in all_results])
    proc_nc = np.array([r['raw_proc']['nc_oddeven'] for r in all_results])
    white_proc_nc = np.array([r['raw_white_proc']['nc_oddeven'] for r in all_results])
    proc_white_nc = np.array([r['raw_proc_white']['nc_oddeven'] for r in all_results])

    print(f"\n📊 OVERALL STATISTICS ({len(all_results)} pairs)")
    print("=" * 80)

    print("\n1. RDM Reliability by Pipeline")
    print(f"   Raw alone:                {np.mean(raw_rdm):.3f} ± {np.std(raw_rdm):.3f}")
    print(f"   Raw → Procrustes:         {np.mean(proc_rdm):.3f} ± {np.std(proc_rdm):.3f} ({np.mean(proc_rdm - raw_rdm):+.3f})")
    print(f"   Raw → White → Proc:       {np.mean(white_proc_rdm):.3f} ± {np.std(white_proc_rdm):.3f} ({np.mean(white_proc_rdm - raw_rdm):+.3f})")
    print(f"   Raw → Proc → White:       {np.mean(proc_white_rdm):.3f} ± {np.std(proc_white_rdm):.3f} ({np.mean(proc_white_rdm - raw_rdm):+.3f})")

    print("\n2. Noise Ceiling by Pipeline")
    print(f"   Raw alone:                {np.mean(raw_nc):.3f} ± {np.std(raw_nc):.3f}")
    print(f"   Raw → Procrustes:         {np.mean(proc_nc):.3f} ± {np.std(proc_nc):.3f}")
    print(f"   Raw → White → Proc:       {np.mean(white_proc_nc):.3f} ± {np.std(white_proc_nc):.3f}")
    print(f"   Raw → Proc → White:       {np.mean(proc_white_nc):.3f} ± {np.std(proc_white_nc):.3f}")

    print("\n3. Positive RDM Reliability")
    raw_pos = sum(1 for x in raw_rdm if x > 0)
    proc_pos = sum(1 for x in proc_rdm if x > 0)
    white_proc_pos = sum(1 for x in white_proc_rdm if x > 0)
    proc_white_pos = sum(1 for x in proc_white_rdm if x > 0)

    print(f"   Raw alone:                {raw_pos}/{len(all_results)} ({100*raw_pos/len(all_results):.1f}%)")
    print(f"   Raw → Procrustes:         {proc_pos}/{len(all_results)} ({100*proc_pos/len(all_results):.1f}%)")
    print(f"   Raw → White → Proc:       {white_proc_pos}/{len(all_results)} ({100*white_proc_pos/len(all_results):.1f}%)")
    print(f"   Raw → Proc → White:       {proc_white_pos}/{len(all_results)} ({100*proc_white_pos/len(all_results):.1f}%)")

    print("\n4. Comparison: White→Proc vs Proc alone")
    white_proc_better = sum(1 for i in range(len(all_results)) if white_proc_rdm[i] > proc_rdm[i])
    white_proc_diff = white_proc_rdm - proc_rdm

    print(f"   White→Proc better:        {white_proc_better}/{len(all_results)} pairs ({100*white_proc_better/len(all_results):.1f}%)")
    print(f"   Mean difference:          {np.mean(white_proc_diff):+.3f}")
    print(f"   Median difference:        {np.median(white_proc_diff):+.3f}")

    print("\n5. Top 10 Improvements (White→Proc vs Raw)")
    sorted_results = sorted(all_results, key=lambda x: x['improvement']['white_proc'], reverse=True)
    for i, r in enumerate(sorted_results[:10], 1):
        raw = r['raw']['rdm_reliability']
        white_proc = r['raw_white_proc']['rdm_reliability']
        improvement = r['improvement']['white_proc']
        print(f"   {i}. {r['subject']}_{r['roi']}: {raw:+.3f} → {white_proc:+.3f} ({improvement:+.3f})")

    print("\n6. By ROI")
    for roi in ROIS:
        roi_results = [r for r in all_results if r['roi'] == roi]
        roi_raw = np.mean([r['raw']['rdm_reliability'] for r in roi_results])
        roi_proc = np.mean([r['raw_proc']['rdm_reliability'] for r in roi_results])
        roi_white_proc = np.mean([r['raw_white_proc']['rdm_reliability'] for r in roi_results])
        roi_proc_white = np.mean([r['raw_proc_white']['rdm_reliability'] for r in roi_results])

        print(f"   {roi}: Raw {roi_raw:+.3f} | P {roi_proc:+.3f} | WP {roi_white_proc:+.3f} | PW {roi_proc_white:+.3f}")

    # Save results (server path)
    output_dir = Path('/scratch/connectome/haba6030/colorBlind/derivatives')

    # Individual results
    with open(output_dir / 'four_way_comparison_detailed.json', 'w') as f:
        json.dump(all_results, f, indent=2)

    # Summary statistics
    summary = {
        'n_pairs': len(all_results),
        'raw': {
            'rdm_reliability_mean': float(np.mean(raw_rdm)),
            'rdm_reliability_std': float(np.std(raw_rdm)),
            'nc_oddeven_mean': float(np.mean(raw_nc)),
            'positive_count': int(raw_pos),
        },
        'raw_proc': {
            'rdm_reliability_mean': float(np.mean(proc_rdm)),
            'rdm_reliability_std': float(np.std(proc_rdm)),
            'nc_oddeven_mean': float(np.mean(proc_nc)),
            'positive_count': int(proc_pos),
            'improvement_over_raw': float(np.mean(proc_rdm - raw_rdm)),
        },
        'raw_white_proc': {
            'rdm_reliability_mean': float(np.mean(white_proc_rdm)),
            'rdm_reliability_std': float(np.std(white_proc_rdm)),
            'nc_oddeven_mean': float(np.mean(white_proc_nc)),
            'positive_count': int(white_proc_pos),
            'improvement_over_raw': float(np.mean(white_proc_rdm - raw_rdm)),
            'improvement_over_proc': float(np.mean(white_proc_rdm - proc_rdm)),
        },
        'raw_proc_white': {
            'rdm_reliability_mean': float(np.mean(proc_white_rdm)),
            'rdm_reliability_std': float(np.std(proc_white_rdm)),
            'nc_oddeven_mean': float(np.mean(proc_white_nc)),
            'positive_count': int(proc_white_pos),
            'improvement_over_raw': float(np.mean(proc_white_rdm - raw_rdm)),
        }
    }

    with open(output_dir / 'four_way_comparison_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"\n✅ Results saved:")
    print(f"   - four_way_comparison_detailed.json")
    print(f"   - four_way_comparison_summary.json")
    print()

if __name__ == '__main__':
    main()
