#!/usr/bin/env python3
"""
Step 2: Iterative Procrustes (HC Template Generation)

Generates HC common template using iterative Procrustes (Haxby et al. 2011)
and projects all subjects (HC + CVD) to HC normative space.

Usage:
    python step2_iterative_procrustes.py --roi V1 --max-iter 10 --method pca
"""

import argparse
import json
import numpy as np
from pathlib import Path
import sys

# Add parent and utils to path
sys.path.append(str(Path(__file__).parent))
from utils.iterative_procrustes import (
    iterative_procrustes_hc_template,
    apply_template_to_subjects
)


def main():
    parser = argparse.ArgumentParser(description='Step 2: Iterative Procrustes HC Template')
    parser.add_argument('--roi', type=str, required=True, help='ROI name (V1, V2, V3, hV4)')
    parser.add_argument('--max-iter', type=int, default=10, help='Max iterations (default: 10)')
    parser.add_argument('--tol', type=float, default=0.001, help='Convergence tolerance (default: 0.001)')
    parser.add_argument('--method', type=str, default='pca', choices=['pca', 'anova'],
                        help='Dimension reduction method (default: pca)')
    parser.add_argument('--input-dir', type=str,
                        default='/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/validation/scripts/postSRM_procrus/results/step1_pca',
                        help='Input directory from Step 1')
    parser.add_argument('--output-dir', type=str,
                        default='/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/validation/scripts/postSRM_procrus/results/step2_procrustes',
                        help='Output directory')

    args = parser.parse_args()

    # Adjust input directory based on method
    if args.method == 'anova':
        input_dir = Path(args.input_dir.replace('step1_pca', 'step1_anova'))
    else:
        input_dir = Path(args.input_dir)

    output_dir = Path(args.output_dir)
    roi = args.roi

    print(f"\n=== Step 2: Iterative Procrustes ===")
    print(f"ROI: {roi}")
    print(f"Method: {args.method}")
    print(f"Max iterations: {args.max_iter}, Tolerance: {args.tol}")

    # Subject groups
    hc_subjects = ['sub-01', 'sub-02', 'sub-03', 'sub-04', 'sub-05', 'sub-06']  # Exclude sub-07 (outlier)
    cvd_subjects = ['sub-08', 'sub-09', 'sub-10']
    all_subjects = hc_subjects + cvd_subjects

    print(f"\nHC subjects: {hc_subjects}")
    print(f"CVD subjects: {cvd_subjects}")

    # Load HC odd patterns
    print(f"\nLoading HC odd patterns from {input_dir / roi}...")
    hc_odd_patterns = []
    hc_even_patterns = []

    for subj_id in hc_subjects:
        if args.method == 'pca':
            odd_path = input_dir / roi / f"{subj_id}_odd_pc.npy"
            even_path = input_dir / roi / f"{subj_id}_even_pc.npy"
        else:  # anova
            odd_path = input_dir / roi / f"{subj_id}_odd_patterns.npy"
            even_path = input_dir / roi / f"{subj_id}_even_patterns.npy"

        if not odd_path.exists():
            print(f"  ERROR: Missing {odd_path}")
            sys.exit(1)

        odd_pattern = np.load(odd_path)
        even_pattern = np.load(even_path)

        hc_odd_patterns.append(odd_pattern)
        hc_even_patterns.append(even_pattern)

        print(f"  {subj_id}: shape={odd_pattern.shape}")

    # Generate HC template via iterative Procrustes
    print(f"\n=== Iterative Procrustes on HC Odd Patterns ===")
    template_hc, aligned_hc_odd, history = iterative_procrustes_hc_template(
        hc_odd_patterns,
        max_iter=args.max_iter,
        tol=args.tol,
        verbose=True
    )

    print(f"\n✓ Template shape: {template_hc.shape}")

    # Apply template to all subjects (odd + even)
    print(f"\n=== Applying Template to All Subjects ===")

    # Load all patterns
    all_odd_patterns = []
    all_even_patterns = []

    for subj_id in all_subjects:
        if args.method == 'pca':
            odd_path = input_dir / roi / f"{subj_id}_odd_pc.npy"
            even_path = input_dir / roi / f"{subj_id}_even_pc.npy"
        else:
            odd_path = input_dir / roi / f"{subj_id}_odd_patterns.npy"
            even_path = input_dir / roi / f"{subj_id}_even_patterns.npy"

        if not odd_path.exists():
            print(f"  WARNING: Missing {subj_id}, skipping")
            continue

        all_odd_patterns.append(np.load(odd_path))
        all_even_patterns.append(np.load(even_path))

    # Align to template
    aligned_odd, rotations_odd, disparities_odd = apply_template_to_subjects(
        all_odd_patterns, template_hc, all_subjects, verbose=True
    )

    print(f"\n=== Applying Template to Even Patterns ===")
    aligned_even, rotations_even, disparities_even = apply_template_to_subjects(
        all_even_patterns, template_hc, all_subjects, verbose=True
    )

    # Save outputs
    output_roi_dir = output_dir / roi
    output_roi_dir.mkdir(parents=True, exist_ok=True)

    # Save template
    template_path = output_roi_dir / "template_hc.npy"
    np.save(template_path, template_hc)
    print(f"\n✓ Saved HC template: {template_path}")

    # Save convergence history
    history_path = output_roi_dir / "convergence_history.json"
    with open(history_path, 'w') as f:
        json.dump(history, f, indent=2)
    print(f"✓ Saved convergence history: {history_path}")

    # Save aligned patterns and transformations
    print(f"\n=== Saving Subject Alignments ===")
    for idx, subj_id in enumerate(all_subjects):
        if idx >= len(aligned_odd):
            continue

        # Aligned patterns
        aligned_odd_path = output_roi_dir / f"{subj_id}_aligned_odd.npy"
        aligned_even_path = output_roi_dir / f"{subj_id}_aligned_even.npy"

        np.save(aligned_odd_path, aligned_odd[idx])
        np.save(aligned_even_path, aligned_even[idx])

        # Transformation matrix (use odd rotation)
        if rotations_odd[idx] is not None:
            rotation_path = output_roi_dir / f"{subj_id}_transformation_R.npy"
            np.save(rotation_path, rotations_odd[idx])

        # Disparity metadata
        disparity_path = output_roi_dir / f"{subj_id}_disparity.json"
        disparity_data = {
            'subject': subj_id,
            'roi': roi,
            'disparity_odd': float(disparities_odd[idx]) if not np.isnan(disparities_odd[idx]) else None,
            'disparity_even': float(disparities_even[idx]) if not np.isnan(disparities_even[idx]) else None,
            'group': 'HC' if subj_id in hc_subjects else 'CVD',
        }

        with open(disparity_path, 'w') as f:
            json.dump(disparity_data, f, indent=2)

        print(f"  {subj_id}: disparity_odd={disparities_odd[idx]:.6f}, "
              f"disparity_even={disparities_even[idx]:.6f}")

    # Summary statistics
    hc_disparities = [d for subj_id, d in zip(all_subjects, disparities_odd) if subj_id in hc_subjects]
    cvd_disparities = [d for subj_id, d in zip(all_subjects, disparities_odd) if subj_id in cvd_subjects]

    summary = {
        'roi': roi,
        'method': args.method,
        'n_hc': len(hc_subjects),
        'n_cvd': len(cvd_subjects),
        'convergence': {
            'iterations': len(history),
            'converged': history[-1]['template_change'] < args.tol if history else False,
            'final_mean_disparity': history[-1]['mean_disparity'] if history else None,
            'final_template_change': history[-1]['template_change'] if history else None,
        },
        'disparities': {
            'hc_mean': float(np.mean(hc_disparities)),
            'hc_std': float(np.std(hc_disparities)),
            'cvd_mean': float(np.mean(cvd_disparities)),
            'cvd_std': float(np.std(cvd_disparities)),
        },
    }

    summary_path = output_roi_dir / "summary.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"\n=== Summary ===")
    print(f"  HC disparities: {summary['disparities']['hc_mean']:.6f} ± {summary['disparities']['hc_std']:.6f}")
    print(f"  CVD disparities: {summary['disparities']['cvd_mean']:.6f} ± {summary['disparities']['cvd_std']:.6f}")
    print(f"  Saved: {summary_path}")

    print(f"\n✓ Step 2 complete for {roi}")


if __name__ == '__main__':
    main()
