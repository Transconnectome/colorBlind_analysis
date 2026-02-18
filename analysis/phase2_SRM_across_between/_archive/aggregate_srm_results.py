#!/usr/bin/env python3
"""
Aggregate SRM Evaluation Results

Combines results from all subject-ROI pairs and generates summary statistics.

Usage:
    python aggregate_srm_results.py --results-dir results/srm_evaluation/TIMESTAMP/ --output summary.json

Input:
    results/srm_evaluation/TIMESTAMP/
    ├── sub-01_V1_srm_results.json
    ├── sub-01_V2_srm_results.json
    ...
    └── sub-10_hV4_srm_results.json

Output:
    - summary_all_subjects.json: Comprehensive statistics
    - summary_by_roi.json: ROI-specific aggregation
    - optimal_k_recommendations.json: Best k per ROI
"""

import sys
import argparse
import json
from pathlib import Path
from typing import Dict, List
from collections import defaultdict

import numpy as np
from scipy.stats import ttest_rel

# ============================================================================
# AGGREGATION FUNCTIONS
# ============================================================================

def load_all_results(results_dir: Path) -> List[Dict]:
    """Load all SRM evaluation results from directory."""
    result_files = list(results_dir.glob("*_srm_results.json"))

    if len(result_files) == 0:
        raise FileNotFoundError(f"No results found in {results_dir}")

    print(f"Found {len(result_files)} result files")

    results = []
    for file in sorted(result_files):
        with open(file, 'r') as f:
            data = json.load(f)
            results.append(data)

    return results


def aggregate_by_roi(results: List[Dict]) -> Dict:
    """Aggregate results by ROI."""
    by_roi = defaultdict(lambda: {
        'subjects': [],
        'procrustes_rdm': [],
        'procrustes_accuracy': [],
        'srm_best_k': [],
        'srm_rdm': [],
        'srm_accuracy': [],
        'rdm_improvement': [],
        'accuracy_improvement': [],
        'winner': []
    })

    for result in results:
        roi = result['roi']
        subject = result['subject']

        # Procrustes baseline
        by_roi[roi]['subjects'].append(subject)
        by_roi[roi]['procrustes_rdm'].append(result['procrustes_baseline']['rdm_correlation_mean'])
        by_roi[roi]['procrustes_accuracy'].append(result['procrustes_baseline']['decoding_accuracy'])

        # SRM best
        if result['srm_tuning']['best_k'] is not None:
            best_metrics = result['srm_tuning']['best_metrics']
            by_roi[roi]['srm_best_k'].append(result['srm_tuning']['best_k'])
            by_roi[roi]['srm_rdm'].append(best_metrics['rdm_correlation_mean'])
            by_roi[roi]['srm_accuracy'].append(best_metrics['decoding_accuracy'])

            # Improvements
            by_roi[roi]['rdm_improvement'].append(result['comparison']['rdm_improvement_absolute'])
            by_roi[roi]['accuracy_improvement'].append(result['comparison']['accuracy_improvement_absolute'])
            by_roi[roi]['winner'].append(result['comparison']['winner'])

    # Convert to numpy arrays and compute statistics
    summary = {}
    for roi, data in by_roi.items():
        procrustes_rdm = np.array(data['procrustes_rdm'])
        procrustes_acc = np.array(data['procrustes_accuracy'])
        srm_rdm = np.array(data['srm_rdm'])
        srm_acc = np.array(data['srm_accuracy'])
        rdm_improvement = np.array(data['rdm_improvement'])
        acc_improvement = np.array(data['accuracy_improvement'])
        best_k_values = np.array(data['srm_best_k'])

        # Paired t-tests
        if len(procrustes_rdm) > 1 and len(srm_rdm) > 1:
            t_rdm, p_rdm = ttest_rel(srm_rdm, procrustes_rdm)
            t_acc, p_acc = ttest_rel(srm_acc, procrustes_acc)
        else:
            t_rdm, p_rdm = np.nan, np.nan
            t_acc, p_acc = np.nan, np.nan

        summary[roi] = {
            'n_subjects': len(data['subjects']),
            'subjects': data['subjects'],
            'procrustes': {
                'rdm_correlation_mean': float(np.mean(procrustes_rdm)),
                'rdm_correlation_std': float(np.std(procrustes_rdm)),
                'decoding_accuracy_mean': float(np.mean(procrustes_acc)),
                'decoding_accuracy_std': float(np.std(procrustes_acc))
            },
            'srm': {
                'rdm_correlation_mean': float(np.mean(srm_rdm)),
                'rdm_correlation_std': float(np.std(srm_rdm)),
                'decoding_accuracy_mean': float(np.mean(srm_acc)),
                'decoding_accuracy_std': float(np.std(srm_acc)),
                'optimal_k_mean': float(np.mean(best_k_values)),
                'optimal_k_std': float(np.std(best_k_values)),
                'optimal_k_values': best_k_values.tolist()
            },
            'improvement': {
                'rdm_absolute_mean': float(np.mean(rdm_improvement)),
                'rdm_absolute_std': float(np.std(rdm_improvement)),
                'rdm_relative_pct': float(np.mean(rdm_improvement) / np.mean(procrustes_rdm) * 100) if np.mean(procrustes_rdm) > 0 else 0,
                'accuracy_absolute_mean': float(np.mean(acc_improvement)),
                'accuracy_absolute_std': float(np.std(acc_improvement)),
                'accuracy_relative_pct': float(np.mean(acc_improvement) / np.mean(procrustes_acc) * 100) if np.mean(procrustes_acc) > 0 else 0,
                'n_improved': int(np.sum(np.array(rdm_improvement) > 0)),
                'pct_improved': float(np.sum(np.array(rdm_improvement) > 0) / len(rdm_improvement) * 100)
            },
            'statistical_test': {
                'rdm_t_statistic': float(t_rdm),
                'rdm_p_value': float(p_rdm),
                'rdm_significant': bool(p_rdm < 0.05) if not np.isnan(p_rdm) else False,
                'accuracy_t_statistic': float(t_acc),
                'accuracy_p_value': float(p_acc),
                'accuracy_significant': bool(p_acc < 0.05) if not np.isnan(p_acc) else False
            },
            'winner_counts': {
                'SRM': data['winner'].count('SRM'),
                'Procrustes': data['winner'].count('Procrustes')
            }
        }

    return summary


def generate_optimal_k_recommendations(roi_summary: Dict) -> Dict:
    """Generate recommendations for optimal k per ROI."""
    recommendations = {}

    for roi, stats in roi_summary.items():
        optimal_k_values = stats['srm']['optimal_k_values']
        mean_k = stats['srm']['optimal_k_mean']
        std_k = stats['srm']['optimal_k_std']

        # Recommend rounded mean
        recommended_k = int(np.round(mean_k / 10) * 10)  # Round to nearest 10

        # Check if improvement is substantial
        rdm_improvement_pct = stats['improvement']['rdm_relative_pct']
        is_worthwhile = rdm_improvement_pct > 5.0  # 5% threshold

        recommendations[roi] = {
            'recommended_k': recommended_k,
            'optimal_k_mean': mean_k,
            'optimal_k_std': std_k,
            'optimal_k_range': [int(min(optimal_k_values)), int(max(optimal_k_values))],
            'rdm_improvement_pct': rdm_improvement_pct,
            'is_worthwhile': is_worthwhile,
            'decision': 'Use SRM' if is_worthwhile else 'Use Procrustes (insufficient improvement)',
            'rationale': f"SRM improves RDM by {rdm_improvement_pct:.1f}% (threshold: 5%)"
        }

    return recommendations


def print_summary_report(roi_summary: Dict, recommendations: Dict):
    """Print formatted summary report."""
    print("\n" + "="*80)
    print("SRM EVALUATION SUMMARY")
    print("="*80)

    for roi in sorted(roi_summary.keys()):
        stats = roi_summary[roi]
        rec = recommendations[roi]

        print(f"\n{roi} (n={stats['n_subjects']} subjects)")
        print("-" * 40)

        print(f"Procrustes Baseline:")
        print(f"  RDM correlation: {stats['procrustes']['rdm_correlation_mean']:.3f} ± {stats['procrustes']['rdm_correlation_std']:.3f}")
        print(f"  Decoding accuracy: {stats['procrustes']['decoding_accuracy_mean']*100:.1f}% ± {stats['procrustes']['decoding_accuracy_std']*100:.1f}%")

        print(f"\nSRM (optimal k={rec['recommended_k']}):")
        print(f"  RDM correlation: {stats['srm']['rdm_correlation_mean']:.3f} ± {stats['srm']['rdm_correlation_std']:.3f}")
        print(f"  Decoding accuracy: {stats['srm']['decoding_accuracy_mean']*100:.1f}% ± {stats['srm']['decoding_accuracy_std']*100:.1f}%")

        print(f"\nImprovement:")
        print(f"  RDM: {stats['improvement']['rdm_absolute_mean']:+.3f} ({stats['improvement']['rdm_relative_pct']:+.1f}%)")
        print(f"  Accuracy: {stats['improvement']['accuracy_absolute_mean']:+.3f} ({stats['improvement']['accuracy_relative_pct']:+.1f}%)")
        print(f"  Improved subjects: {stats['improvement']['n_improved']}/{stats['n_subjects']} ({stats['improvement']['pct_improved']:.1f}%)")

        print(f"\nStatistical Test:")
        print(f"  RDM: t={stats['statistical_test']['rdm_t_statistic']:.3f}, p={stats['statistical_test']['rdm_p_value']:.4f} "
              f"{'*' if stats['statistical_test']['rdm_significant'] else '(ns)'}")

        print(f"\nRecommendation: {rec['decision']}")
        print(f"  {rec['rationale']}")

    print("\n" + "="*80)
    print("OVERALL DECISION")
    print("="*80)

    worthwhile_rois = [roi for roi, rec in recommendations.items() if rec['is_worthwhile']]

    if len(worthwhile_rois) > 0:
        print(f"✅ SRM recommended for: {', '.join(worthwhile_rois)}")
        print(f"⚠️  Use Procrustes for: {', '.join([roi for roi in recommendations.keys() if roi not in worthwhile_rois])}")
    else:
        print("⚠️  Procrustes sufficient for all ROIs (SRM improvement < 5%)")
        print("   Consider using Procrustes to save computational cost")

    print("="*80)


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='Aggregate SRM evaluation results')
    parser.add_argument('--results-dir', type=str, required=True,
                       help='Directory containing individual result files')
    parser.add_argument('--output-dir', type=str,
                       help='Output directory (default: same as results-dir)')

    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    output_dir = Path(args.output_dir) if args.output_dir else results_dir

    if not results_dir.exists():
        print(f"ERROR: Results directory not found: {results_dir}")
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*80}")
    print("Aggregating SRM Evaluation Results")
    print(f"{'='*80}")
    print(f"Results directory: {results_dir}")
    print(f"Output directory: {output_dir}")

    # ========================================================================
    # 1. LOAD RESULTS
    # ========================================================================

    print("\n[1/4] Loading results...")
    results = load_all_results(results_dir)
    print(f"  Loaded {len(results)} subject-ROI pairs")

    # ========================================================================
    # 2. AGGREGATE BY ROI
    # ========================================================================

    print("\n[2/4] Aggregating by ROI...")
    roi_summary = aggregate_by_roi(results)
    print(f"  Aggregated {len(roi_summary)} ROIs")

    # ========================================================================
    # 3. GENERATE RECOMMENDATIONS
    # ========================================================================

    print("\n[3/4] Generating optimal k recommendations...")
    recommendations = generate_optimal_k_recommendations(roi_summary)

    # ========================================================================
    # 4. SAVE OUTPUTS
    # ========================================================================

    print("\n[4/4] Saving outputs...")

    # Summary by ROI
    output_file = output_dir / "summary_by_roi.json"
    with open(output_file, 'w') as f:
        json.dump(roi_summary, f, indent=2)
    print(f"  Saved ROI summary to {output_file}")

    # Recommendations
    output_file = output_dir / "optimal_k_recommendations.json"
    with open(output_file, 'w') as f:
        json.dump(recommendations, f, indent=2)
    print(f"  Saved recommendations to {output_file}")

    # Overall summary
    overall_summary = {
        'n_total_pairs': len(results),
        'n_rois': len(roi_summary),
        'rois': list(roi_summary.keys()),
        'summary_by_roi': roi_summary,
        'recommendations': recommendations,
        'overall_decision': {
            'srm_recommended_for': [roi for roi, rec in recommendations.items() if rec['is_worthwhile']],
            'procrustes_sufficient_for': [roi for roi, rec in recommendations.items() if not rec['is_worthwhile']]
        }
    }

    output_file = output_dir / "summary_all_subjects.json"
    with open(output_file, 'w') as f:
        json.dump(overall_summary, f, indent=2)
    print(f"  Saved overall summary to {output_file}")

    # ========================================================================
    # PRINT REPORT
    # ========================================================================

    print_summary_report(roi_summary, recommendations)

    print(f"\nAggregation completed. Results saved to {output_dir}")


if __name__ == '__main__':
    main()
