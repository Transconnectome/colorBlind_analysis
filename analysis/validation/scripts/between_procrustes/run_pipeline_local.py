#!/usr/bin/env python3
"""
run_pipeline_local.py
---------------------
End-to-end pipeline for between-subject Procrustes with ANOVA voxel selection

Usage:
    python run_pipeline_local.py --roi V1 --k-values 20 50 100
    python run_pipeline_local.py --roi V1 --test-mode  # Quick test with k=50
"""

import argparse
import sys
from pathlib import Path
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.voxel_correspondence import load_all_subjects_common_amplitudes
from evaluate_procrustes_anova import evaluate_procrustes_anova


def main():
    parser = argparse.ArgumentParser(description='Between-subject Procrustes with ANOVA selection')
    parser.add_argument('--roi', type=str, default='V1',
                       help='ROI name (default: V1)')
    parser.add_argument('--k-values', type=int, nargs='+', default=[20, 50, 100],
                       help='k values for voxel selection (default: 20 50 100)')
    parser.add_argument('--baseline-dir', type=str,
                       default='analysis/phase1_preprocess_decoding/deoblique_v2/results/baseline_decoding/fixed_perRun_unfiltered',
                       help='Path to unfiltered baseline results')
    parser.add_argument('--output-dir', type=str,
                       default='analysis/validation/scripts/between_procrustes/results',
                       help='Output directory')
    parser.add_argument('--test-mode', action='store_true',
                       help='Quick test mode (single k=50)')

    args = parser.parse_args()

    # Configuration
    ROI = args.roi
    BASELINE_DIR = Path(args.baseline_dir)
    OUTPUT_DIR = Path(args.output_dir)
    K_VALUES = [50] if args.test_mode else args.k_values

    # Subject groups (excluding sub-07 - excluded from study)
    HC_SUBJECTS = ['sub-01', 'sub-02', 'sub-03', 'sub-04', 'sub-05', 'sub-06']
    CVD_SUBJECTS = ['sub-08', 'sub-09', 'sub-10']
    ALL_SUBJECTS = HC_SUBJECTS + CVD_SUBJECTS

    print("="*70)
    print("Between-Subject Procrustes with ANOVA Voxel Selection")
    print("="*70)
    print(f"ROI: {ROI}")
    print(f"K values: {K_VALUES}")
    print(f"HC subjects: {HC_SUBJECTS}")
    print(f"CVD subjects: {CVD_SUBJECTS}")
    print(f"Baseline directory: {BASELINE_DIR}")
    print(f"Output directory: {OUTPUT_DIR}")
    print()

    # Check if baseline directory exists
    if not BASELINE_DIR.exists():
        print(f"❌ ERROR: Baseline directory not found: {BASELINE_DIR}")
        print(f"\n📝 Note: You need to run the modified preprocessing first:")
        print(f"   1. Upload fir_reconstruction_no_voxel_filtering.py to server")
        print(f"   2. Run: sbatch run_preprocessing_unfiltered.sbatch")
        print(f"   3. Download results to: {BASELINE_DIR}")
        return 1

    # Step 1: Find common voxels and load amplitudes
    print("[1/3] Finding common voxels and loading amplitudes...")
    print("-"*70)

    try:
        amplitudes_dict, common_coords = load_all_subjects_common_amplitudes(
            ALL_SUBJECTS, ROI, BASELINE_DIR
        )
    except Exception as e:
        print(f"❌ ERROR: Failed to load amplitudes: {e}")
        return 1

    if len(amplitudes_dict) == 0:
        print(f"❌ ERROR: No subjects loaded successfully")
        return 1

    # Check which subjects were loaded
    loaded_hc = [s for s in HC_SUBJECTS if s in amplitudes_dict]
    loaded_cvd = [s for s in CVD_SUBJECTS if s in amplitudes_dict]

    print(f"\n✅ Successfully loaded {len(amplitudes_dict)} subjects")
    print(f"   HC: {len(loaded_hc)}/{len(HC_SUBJECTS)} - {loaded_hc}")
    print(f"   CVD: {len(loaded_cvd)}/{len(CVD_SUBJECTS)} - {loaded_cvd}")
    print(f"   Common voxels: {len(common_coords)}")

    # Check if we have enough common voxels
    max_k = max(K_VALUES)
    if len(common_coords) < max_k:
        print(f"\n⚠️  WARNING: Only {len(common_coords)} common voxels, but max k={max_k}")
        print(f"   Adjusting k values to fit available voxels...")
        K_VALUES = [k for k in K_VALUES if k <= len(common_coords)]
        if len(K_VALUES) == 0:
            K_VALUES = [min(20, len(common_coords))]
        print(f"   New k values: {K_VALUES}")

    # Step 2: Run evaluation
    print(f"\n[2/3] Running Procrustes evaluation...")
    print("-"*70)

    try:
        results = evaluate_procrustes_anova(
            amplitudes_dict=amplitudes_dict,
            subjects_hc=loaded_hc,
            subjects_cvd=loaded_cvd,
            k_values=K_VALUES,
            roi=ROI,
            output_dir=OUTPUT_DIR
        )
    except Exception as e:
        print(f"❌ ERROR: Evaluation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # Step 3: Print summary
    print(f"\n[3/3] Summary")
    print("="*70)

    for k in K_VALUES:
        res = results[k]
        print(f"\nk = {k} voxels:")
        print(f"  HC disparity: {res['disparity_stats']['hc_mean']:.4f} ± {res['disparity_stats']['hc_std']:.4f}")
        print(f"  CVD disparity: {res['disparity_stats']['cvd_mean']:.4f} ± {res['disparity_stats']['cvd_std']:.4f}")
        print(f"  t-test: t={res['ttest']['t']:.3f}, p={res['ttest']['p']:.4f}, d={res['ttest']['cohens_d']:.3f}")
        print(f"  RDM correlations:")
        print(f"    HC-HC: {res['rdm_correlations']['hc_hc_mean']:.3f}" if res['rdm_correlations']['hc_hc_mean'] else "    HC-HC: N/A")
        print(f"    CVD-CVD: {res['rdm_correlations']['cvd_cvd_mean']:.3f}" if res['rdm_correlations']['cvd_cvd_mean'] else "    CVD-CVD: N/A")
        print(f"    HC-CVD: {res['rdm_correlations']['hc_cvd_mean']:.3f}" if res['rdm_correlations']['hc_cvd_mean'] else "    HC-CVD: N/A")

    print("\n✅ Pipeline completed successfully!")
    print(f"📁 Results saved to: {OUTPUT_DIR}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
