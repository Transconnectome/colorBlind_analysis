#!/usr/bin/env python3
"""
SRM Between-Subject Analysis for C010+Procrustes Data (HC vs CVD)

Novel approach: Compares two averaging methods for SRM:
1. Raw-averaged SRM: Raw amplitudes → average runs → SRM
2. Procrustes-averaged SRM: Procrustes-aligned amplitudes → average runs → SRM

Hypothesis: Procrustes-averaged data (higher RDM reliability 0.496 vs 0.042)
should yield better shared response models and stronger HC-CVD separation.

Usage:
    python evaluate_srm_c010_between_subject.py --roi V1

Expected Input:
    C010_RESULTS_DIR/
    ├── sub-01/{ROI}/amplitudes_raw.npy          # (6, 8, n_voxels)
    ├── sub-01/{ROI}/amplitudes_procrustes.npy   # (6, 8, n_voxels)
    ...

Output:
    results/c010/{TIMESTAMP}/
    ├── {ROI}_raw_srm_results.json
    ├── {ROI}_procrustes_srm_results.json
    ├── {ROI}_dual_comparison.json
    └── visualizations/
"""

import sys
import os
import argparse
import json
import time
import socket
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

import numpy as np
from scipy.stats import spearmanr, ttest_ind
from scipy.spatial.distance import squareform, pdist
from itertools import combinations

# Add utils to path
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR / 'utils'))
sys.path.insert(0, str(SCRIPT_DIR.parent / 'utils'))

try:
    from srm_alignment import apply_srm_alignment, BRAINIAK_AVAILABLE
except ImportError as e:
    print(f"Error importing utilities: {e}")
    sys.exit(1)

# ============================================================================
# CONFIGURATION
# ============================================================================

# Auto-detect local vs server paths
if socket.gethostname().startswith('node'):
    # Server path
    C010_RESULTS_DIR = Path("/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010")
    OUTPUT_BASE_DIR = Path("/scratch/connectome/haba6030/colorBlind/derivatives/srm_c010_between_subject")
else:
    # Local path
    C010_RESULTS_DIR = Path("/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/validation/preprocess_Check/full_dataset_C010")
    OUTPUT_BASE_DIR = Path("/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/validation/SRM/results/c010")

# Subject groups (updated: 10 subjects total)
HC_SUBJECTS = ['01', '02', '03', '04', '05', '06', '07']  # n=7
CVD_SUBJECTS = ['08', '09', '10']  # n=3

# ROI-specific k values (fixed based on color dimensionality)
DEFAULT_K_VALUES = {
    'V1': 4,
    'V2': 4,
    'V3': 3,
    'V4': 4
}

# ============================================================================
# DATA LOADING
# ============================================================================

def load_subject_roi_data_dual(subject_id: str, roi_name: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Load BOTH raw and procrustes amplitudes for a subject-ROI pair.

    Args:
        subject_id: Subject ID (e.g., '01', '08')
        roi_name: ROI name (e.g., 'V1')

    Returns:
        pattern_raw: (8, n_voxels) - Raw averaged across runs
        pattern_proc: (8, n_voxels) - Procrustes averaged across runs
    """
    data_path = C010_RESULTS_DIR / f"sub-{subject_id}" / roi_name

    # Check path exists
    if not data_path.exists():
        raise FileNotFoundError(f"Data path not found: {data_path}")

    # Load both versions
    amp_raw_path = data_path / "amplitudes_raw.npy"
    amp_proc_path = data_path / "amplitudes_procrustes.npy"

    if not amp_raw_path.exists():
        raise FileNotFoundError(f"Raw amplitudes not found: {amp_raw_path}")
    if not amp_proc_path.exists():
        raise FileNotFoundError(f"Procrustes amplitudes not found: {amp_proc_path}")

    amplitudes_raw = np.load(amp_raw_path)  # (6, 8, n_voxels)
    amplitudes_proc = np.load(amp_proc_path)  # (6, 8, n_voxels)

    # Average across runs (standard SRM input format)
    # This creates beta-like estimates for each color
    pattern_raw = amplitudes_raw.mean(axis=0)  # (8, n_voxels)
    pattern_proc = amplitudes_proc.mean(axis=0)  # (8, n_voxels)

    return pattern_raw, pattern_proc


# ============================================================================
# ANALYSIS FUNCTIONS
# ============================================================================

def compute_rdm_from_patterns(patterns: np.ndarray) -> np.ndarray:
    """
    Compute RDM from pattern matrix using Pearson dissimilarity.

    Args:
        patterns: (n_colors, n_features) pattern matrix

    Returns:
        rdm: (n_colors, n_colors) dissimilarity matrix
    """
    rdm = 1 - np.corrcoef(patterns)
    return rdm


def compute_procrustes_disparity(X: np.ndarray, Y: np.ndarray) -> float:
    """
    Compute Procrustes disparity between two pattern sets.

    Args:
        X, Y: (n_colors, n_features) pattern matrices

    Returns:
        disparity: Frobenius norm of residual after optimal alignment
    """
    from scipy.linalg import orthogonal_procrustes

    # Center and scale
    X_centered = X - X.mean(axis=0)
    Y_centered = Y - Y.mean(axis=0)

    X_scaled = X_centered / np.linalg.norm(X_centered, 'fro')
    Y_scaled = Y_centered / np.linalg.norm(Y_centered, 'fro')

    # Find optimal rotation
    R, scale = orthogonal_procrustes(X_scaled, Y_scaled)

    # Compute disparity
    Y_aligned = X_scaled @ R
    disparity = np.linalg.norm(Y_aligned - Y_scaled, 'fro')

    return disparity


def fit_srm_and_compute_disparities(hc_patterns: List[np.ndarray],
                                    cvd_patterns: List[np.ndarray],
                                    k_value: int) -> Dict:
    """
    Fit SRM on HC+CVD and compute HC-CVD disparities.

    Args:
        hc_patterns: List of (8, n_voxels) arrays for HC subjects
        cvd_patterns: List of (8, n_voxels) arrays for CVD subjects
        k_value: Number of SRM features

    Returns:
        results: Dict with disparities and statistics
    """
    print(f"    Fitting SRM with k={k_value}...")

    # Prepare data for SRM: add dummy run dimension
    # SRM expects (n_runs, n_colors, n_voxels), we have (n_colors, n_voxels)
    hc_amplitudes = {f'hc_{i}': p[np.newaxis, :, :] for i, p in enumerate(hc_patterns)}
    cvd_amplitudes = {f'cvd_{i}': p[np.newaxis, :, :] for i, p in enumerate(cvd_patterns)}

    all_amplitudes = {**hc_amplitudes, **cvd_amplitudes}

    # Apply SRM
    srm_result = apply_srm_alignment(
        all_amplitudes,
        n_features=k_value,
        n_iter=10
    )

    aligned_amplitudes = srm_result['aligned_amplitudes']

    # Extract aligned patterns (remove dummy run dimension)
    hc_aligned = [aligned_amplitudes[f'hc_{i}'][0] for i in range(len(hc_patterns))]  # List of (8, k)
    cvd_aligned = [aligned_amplitudes[f'cvd_{i}'][0] for i in range(len(cvd_patterns))]  # List of (8, k)

    # Compute HC reference (mean of HC subjects)
    hc_reference = np.mean(hc_aligned, axis=0)  # (8, k)

    print(f"    HC reference shape: {hc_reference.shape}")

    # Compute disparities
    hc_disparities = []
    for pattern in hc_aligned:
        disp = compute_procrustes_disparity(pattern, hc_reference)
        hc_disparities.append(disp)

    cvd_disparities = []
    for pattern in cvd_aligned:
        disp = compute_procrustes_disparity(pattern, hc_reference)
        cvd_disparities.append(disp)

    # CVD-to-CVD pairwise disparities
    cvd_cvd_disparities = []
    for i in range(len(cvd_aligned)):
        for j in range(i + 1, len(cvd_aligned)):
            disp = compute_procrustes_disparity(cvd_aligned[i], cvd_aligned[j])
            cvd_cvd_disparities.append(disp)

    hc_disparities = np.array(hc_disparities)
    cvd_disparities = np.array(cvd_disparities)
    cvd_cvd_disparities = np.array(cvd_cvd_disparities) if cvd_cvd_disparities else np.array([np.nan])

    # Statistical tests
    t_stat_hc_cvd, p_value_hc_cvd = ttest_ind(hc_disparities, cvd_disparities)

    cohens_d = (cvd_disparities.mean() - hc_disparities.mean()) / \
               np.sqrt((hc_disparities.std()**2 + cvd_disparities.std()**2) / 2)

    print(f"    HC-to-HC: {hc_disparities.mean():.3f} ± {hc_disparities.std():.3f}")
    print(f"    CVD-to-HC: {cvd_disparities.mean():.3f} ± {cvd_disparities.std():.3f}")
    print(f"    t-test: t={t_stat_hc_cvd:.3f}, p={p_value_hc_cvd:.4f}, d={cohens_d:.3f}")

    # Compute RDM similarities
    rdms = {f'hc_{i}': compute_rdm_from_patterns(p) for i, p in enumerate(hc_aligned)}
    rdms.update({f'cvd_{i}': compute_rdm_from_patterns(p) for i, p in enumerate(cvd_aligned)})

    hc_hc_correlations = []
    cvd_cvd_correlations = []
    hc_cvd_correlations = []

    all_subjects = list(rdms.keys())
    for subj_i, subj_j in combinations(all_subjects, 2):
        mask = np.triu(np.ones_like(rdms[subj_i], dtype=bool), k=1)
        vec_i = rdms[subj_i][mask]
        vec_j = rdms[subj_j][mask]

        r, _ = spearmanr(vec_i, vec_j)

        if subj_i.startswith('hc') and subj_j.startswith('hc'):
            hc_hc_correlations.append(r)
        elif subj_i.startswith('cvd') and subj_j.startswith('cvd'):
            cvd_cvd_correlations.append(r)
        else:
            hc_cvd_correlations.append(r)

    return {
        'disparities': {
            'hc_to_hc_reference': {
                'mean': float(hc_disparities.mean()),
                'std': float(hc_disparities.std()),
                'values': hc_disparities.tolist()
            },
            'cvd_to_hc_reference': {
                'mean': float(cvd_disparities.mean()),
                'std': float(cvd_disparities.std()),
                'values': cvd_disparities.tolist()
            },
            'cvd_to_cvd_pairwise': {
                'mean': float(cvd_cvd_disparities.mean()) if not np.isnan(cvd_cvd_disparities).all() else None,
                'std': float(cvd_cvd_disparities.std()) if not np.isnan(cvd_cvd_disparities).all() else None,
                'values': cvd_cvd_disparities.tolist() if not np.isnan(cvd_cvd_disparities).all() else []
            }
        },
        'statistical_tests': {
            'hc_vs_cvd': {
                't_statistic': float(t_stat_hc_cvd),
                'p_value': float(p_value_hc_cvd),
                'cohens_d': float(cohens_d),
                'significant': bool(p_value_hc_cvd < 0.05)
            }
        },
        'rdm_similarities': {
            'hc_hc': {
                'mean': float(np.mean(hc_hc_correlations)),
                'std': float(np.std(hc_hc_correlations)),
                'n_pairs': len(hc_hc_correlations)
            },
            'cvd_cvd': {
                'mean': float(np.mean(cvd_cvd_correlations)) if cvd_cvd_correlations else None,
                'std': float(np.std(cvd_cvd_correlations)) if cvd_cvd_correlations else None,
                'n_pairs': len(cvd_cvd_correlations)
            },
            'hc_cvd': {
                'mean': float(np.mean(hc_cvd_correlations)),
                'std': float(np.std(hc_cvd_correlations)),
                'n_pairs': len(hc_cvd_correlations)
            }
        },
        'aligned_patterns': {
            'hc': hc_aligned,
            'cvd': cvd_aligned
        }
    }


# ============================================================================
# MAIN EVALUATION (DUAL PIPELINE)
# ============================================================================

def evaluate_srm_c010_dual_pipeline(roi: str, output_dir: Path) -> Dict:
    """
    Run dual SRM pipeline: raw-averaged vs procrustes-averaged.

    Args:
        roi: ROI name
        output_dir: Output directory

    Returns:
        comparison: Dict with both results and comparison metrics
    """
    print(f"\n{'='*80}")
    print(f"C010 Between-Subject SRM Analysis (Dual Pipeline): {roi}")
    print(f"{'='*80}")

    if not BRAINIAK_AVAILABLE:
        raise ImportError("BrainIAK required for SRM")

    k_value = DEFAULT_K_VALUES.get(roi, 4)
    print(f"SRM features: k={k_value}")
    print(f"HC subjects: {HC_SUBJECTS} (n={len(HC_SUBJECTS)})")
    print(f"CVD subjects: {CVD_SUBJECTS} (n={len(CVD_SUBJECTS)})")

    output_dir.mkdir(parents=True, exist_ok=True)

    # ========================================================================
    # 1. LOAD DATA (DUAL)
    # ========================================================================

    print("\n[1/4] Loading data (dual: raw + procrustes)...")

    hc_patterns_raw = []
    hc_patterns_proc = []

    for subj in HC_SUBJECTS:
        try:
            p_raw, p_proc = load_subject_roi_data_dual(subj, roi)
            hc_patterns_raw.append(p_raw)
            hc_patterns_proc.append(p_proc)
            print(f"  Loaded sub-{subj}: raw={p_raw.shape}, proc={p_proc.shape}")
        except FileNotFoundError as e:
            print(f"  WARNING: {e}")

    cvd_patterns_raw = []
    cvd_patterns_proc = []

    for subj in CVD_SUBJECTS:
        try:
            p_raw, p_proc = load_subject_roi_data_dual(subj, roi)
            cvd_patterns_raw.append(p_raw)
            cvd_patterns_proc.append(p_proc)
            print(f"  Loaded sub-{subj}: raw={p_raw.shape}, proc={p_proc.shape}")
        except FileNotFoundError as e:
            print(f"  WARNING: {e}")

    if len(hc_patterns_raw) < 2:
        raise ValueError(f"Insufficient HC subjects: {len(hc_patterns_raw)} (need >=2)")

    if len(cvd_patterns_raw) == 0:
        raise ValueError("No CVD subjects found")

    print(f"\n  Total loaded: {len(hc_patterns_raw)} HC + {len(cvd_patterns_raw)} CVD")

    # ========================================================================
    # 2. RUN RAW-AVERAGED SRM
    # ========================================================================

    print("\n[2/4] Running Raw-Averaged SRM pipeline...")
    results_raw = fit_srm_and_compute_disparities(hc_patterns_raw, cvd_patterns_raw, k_value)

    # ========================================================================
    # 3. RUN PROCRUSTES-AVERAGED SRM
    # ========================================================================

    print("\n[3/4] Running Procrustes-Averaged SRM pipeline...")
    results_proc = fit_srm_and_compute_disparities(hc_patterns_proc, cvd_patterns_proc, k_value)

    # ========================================================================
    # 4. COMPARE METHODS
    # ========================================================================

    print("\n[4/4] Comparing Raw vs Procrustes SRM...")

    # Which method yields larger HC-CVD separation?
    hc_cvd_disp_raw = results_raw['disparities']['cvd_to_hc_reference']['mean'] - \
                       results_raw['disparities']['hc_to_hc_reference']['mean']

    hc_cvd_disp_proc = results_proc['disparities']['cvd_to_hc_reference']['mean'] - \
                        results_proc['disparities']['hc_to_hc_reference']['mean']

    winner = "Procrustes" if hc_cvd_disp_proc > hc_cvd_disp_raw else "Raw"

    improvement_abs = hc_cvd_disp_proc - hc_cvd_disp_raw
    improvement_pct = (improvement_abs / hc_cvd_disp_raw * 100) if hc_cvd_disp_raw > 0 else 0

    print(f"\n  === Dual Pipeline Comparison ===")
    print(f"  Raw SRM HC-CVD separation: {hc_cvd_disp_raw:.4f}")
    print(f"  Procrustes SRM HC-CVD separation: {hc_cvd_disp_proc:.4f}")
    print(f"  Improvement: {improvement_abs:+.4f} ({improvement_pct:+.2f}%)")
    print(f"  Winner: {winner}")

    # ========================================================================
    # 5. SAVE RESULTS
    # ========================================================================

    print("\n[5/4] Saving results...")

    # Save raw results
    raw_output = {
        'roi': roi,
        'method': 'raw_averaged_srm',
        'n_features': int(k_value),
        'timestamp': datetime.now().isoformat(),
        'subjects': {
            'hc': [f'sub-{s}' for s in HC_SUBJECTS],
            'cvd': [f'sub-{s}' for s in CVD_SUBJECTS]
        },
        'results': {k: v for k, v in results_raw.items() if k != 'aligned_patterns'}
    }

    raw_file = output_dir / f"{roi}_raw_srm_results.json"
    with open(raw_file, 'w') as f:
        json.dump(raw_output, f, indent=2)
    print(f"  Saved raw SRM results to {raw_file}")

    # Save procrustes results
    proc_output = {
        'roi': roi,
        'method': 'procrustes_averaged_srm',
        'n_features': int(k_value),
        'timestamp': datetime.now().isoformat(),
        'subjects': {
            'hc': [f'sub-{s}' for s in HC_SUBJECTS],
            'cvd': [f'sub-{s}' for s in CVD_SUBJECTS]
        },
        'results': {k: v for k, v in results_proc.items() if k != 'aligned_patterns'}
    }

    proc_file = output_dir / f"{roi}_procrustes_srm_results.json"
    with open(proc_file, 'w') as f:
        json.dump(proc_output, f, indent=2)
    print(f"  Saved procrustes SRM results to {proc_file}")

    # Save comparison
    comparison = {
        'roi': roi,
        'n_features': int(k_value),
        'timestamp': datetime.now().isoformat(),
        'raw_srm': {
            'hc_cvd_separation': float(hc_cvd_disp_raw),
            'p_value': float(results_raw['statistical_tests']['hc_vs_cvd']['p_value']),
            'cohens_d': float(results_raw['statistical_tests']['hc_vs_cvd']['cohens_d'])
        },
        'procrustes_srm': {
            'hc_cvd_separation': float(hc_cvd_disp_proc),
            'p_value': float(results_proc['statistical_tests']['hc_vs_cvd']['p_value']),
            'cohens_d': float(results_proc['statistical_tests']['hc_vs_cvd']['cohens_d'])
        },
        'comparison': {
            'improvement_absolute': float(improvement_abs),
            'improvement_percent': float(improvement_pct),
            'winner': winner
        }
    }

    comp_file = output_dir / f"{roi}_dual_comparison.json"
    with open(comp_file, 'w') as f:
        json.dump(comparison, f, indent=2)
    print(f"  Saved comparison to {comp_file}")

    # Save aligned amplitudes for visualization
    # Procrustes method (better performing)
    aligned_dict_proc = {}
    for i, subj_id in enumerate(HC_SUBJECTS):
        aligned_dict_proc[f'sub-{subj_id}'] = results_proc['aligned_patterns']['hc'][i]
    for i, subj_id in enumerate(CVD_SUBJECTS):
        aligned_dict_proc[f'sub-{subj_id}'] = results_proc['aligned_patterns']['cvd'][i]

    aligned_file_proc = output_dir / f"{roi}_procrustes_aligned_amplitudes.npy"
    np.save(aligned_file_proc, aligned_dict_proc, allow_pickle=True)
    print(f"  Saved Procrustes aligned amplitudes to {aligned_file_proc}")

    # Also save Raw for comparison
    aligned_dict_raw = {}
    for i, subj_id in enumerate(HC_SUBJECTS):
        aligned_dict_raw[f'sub-{subj_id}'] = results_raw['aligned_patterns']['hc'][i]
    for i, subj_id in enumerate(CVD_SUBJECTS):
        aligned_dict_raw[f'sub-{subj_id}'] = results_raw['aligned_patterns']['cvd'][i]

    aligned_file_raw = output_dir / f"{roi}_raw_aligned_amplitudes.npy"
    np.save(aligned_file_raw, aligned_dict_raw, allow_pickle=True)
    print(f"  Saved Raw aligned amplitudes to {aligned_file_raw}")

    return {
        'raw': results_raw,
        'procrustes': results_proc,
        'comparison': comparison
    }


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='C010 Between-Subject SRM Analysis (Dual Pipeline: Raw vs Procrustes)'
    )
    parser.add_argument('--roi', type=str, required=True,
                       help='ROI name (V1, V2, V3, V4)')

    args = parser.parse_args()

    # Create timestamped output directory
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = OUTPUT_BASE_DIR / timestamp

    print(f"\n{'='*80}")
    print("C010 Between-Subject SRM Analysis (Dual Pipeline)")
    print(f"{'='*80}")
    print(f"ROI: {args.roi}")
    print(f"Data: {C010_RESULTS_DIR}")
    print(f"Output: {output_dir}")

    # Check data exists
    if not C010_RESULTS_DIR.exists():
        print(f"\nERROR: C010 data not found: {C010_RESULTS_DIR}")
        sys.exit(1)

    start_time = time.time()

    try:
        results = evaluate_srm_c010_dual_pipeline(args.roi, output_dir)

        elapsed = time.time() - start_time
        print(f"\n{'='*80}")
        print(f"Analysis completed in {elapsed:.1f}s")
        print(f"{'='*80}")

        # Print summary
        comp = results['comparison']
        print("\n=== SUMMARY ===")
        print(f"ROI: {comp['roi']}, k={comp['n_features']}")
        print(f"Raw SRM: separation={comp['raw_srm']['hc_cvd_separation']:.4f}, "
              f"p={comp['raw_srm']['p_value']:.4f}, d={comp['raw_srm']['cohens_d']:.2f}")
        print(f"Procrustes SRM: separation={comp['procrustes_srm']['hc_cvd_separation']:.4f}, "
              f"p={comp['procrustes_srm']['p_value']:.4f}, d={comp['procrustes_srm']['cohens_d']:.2f}")
        print(f"Winner: {comp['comparison']['winner']} "
              f"({comp['comparison']['improvement_percent']:+.2f}% improvement)")

    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
