"""
Compute normalized Procrustes disparities.

Normalized disparity = disparity / ||target||_F^2
where ||target||_F^2 is the Frobenius norm squared.

For centered, scaled data: ||target||_F^2 ≈ n_elements (since variance ≈ 1)

Usage:
    python scripts/compute_normalized_disparity.py \
        --input-file results/pairwise_procrustes/pairwise_summary.json \
        --output-file results/pairwise_procrustes/normalized_disparities.json
"""

import numpy as np
import json
import argparse
from pathlib import Path


def compute_normalization_factor(n_colors, n_voxels):
    """
    Compute normalization factor for Procrustes disparity.

    For centered and scaled data, the expected Frobenius norm squared is:
    E[||X||_F^2] = n_colors × n_voxels

    since each element has variance ≈ 1 after scaling.
    """
    return n_colors * n_voxels


def normalize_disparities(results, voxel_counts):
    """
    Normalize disparities by matrix size.

    Parameters
    ----------
    results : dict
        Raw pairwise results
    voxel_counts : dict
        Number of voxels per ROI

    Returns
    -------
    normalized_results : dict
        Results with normalized disparities added
    """
    normalized_results = {}

    n_colors = 8

    for roi, data in results.items():
        n_voxels = voxel_counts[roi]
        norm_factor = compute_normalization_factor(n_colors, n_voxels)

        # Normalize HC-to-HC disparities
        hc_disparities_raw = np.array(data['hc_to_hc']['disparities'])
        hc_disparities_norm = hc_disparities_raw / norm_factor

        # Normalize CVD-to-HC disparities
        cvd_disparities_raw = np.array(data['cvd_to_hc']['disparities'])
        cvd_disparities_norm = cvd_disparities_raw / norm_factor

        normalized_results[roi] = {
            'n_colors': n_colors,
            'n_voxels': n_voxels,
            'n_elements': n_colors * n_voxels,
            'normalization_factor': norm_factor,
            'hc_to_hc': {
                'raw': {
                    'mean': float(np.mean(hc_disparities_raw)),
                    'std': float(np.std(hc_disparities_raw)),
                    'median': float(np.median(hc_disparities_raw)),
                    'min': float(np.min(hc_disparities_raw)),
                    'max': float(np.max(hc_disparities_raw))
                },
                'normalized': {
                    'disparities': hc_disparities_norm.tolist(),
                    'mean': float(np.mean(hc_disparities_norm)),
                    'std': float(np.std(hc_disparities_norm)),
                    'median': float(np.median(hc_disparities_norm)),
                    'min': float(np.min(hc_disparities_norm)),
                    'max': float(np.max(hc_disparities_norm))
                }
            },
            'cvd_to_hc': {
                'raw': {
                    'mean': float(np.mean(cvd_disparities_raw)),
                    'std': float(np.std(cvd_disparities_raw)),
                    'median': float(np.median(cvd_disparities_raw)),
                    'min': float(np.min(cvd_disparities_raw)),
                    'max': float(np.max(cvd_disparities_raw))
                },
                'normalized': {
                    'disparities': cvd_disparities_norm.tolist(),
                    'mean': float(np.mean(cvd_disparities_norm)),
                    'std': float(np.std(cvd_disparities_norm)),
                    'median': float(np.median(cvd_disparities_norm)),
                    'min': float(np.min(cvd_disparities_norm)),
                    'max': float(np.max(cvd_disparities_norm))
                }
            },
            'interpretation': interpret_normalized_disparity(
                float(np.mean(hc_disparities_norm)),
                float(np.mean(cvd_disparities_norm))
            )
        }

    return normalized_results


def interpret_normalized_disparity(hc_mean, cvd_mean):
    """
    Interpret normalized disparity values.

    Typical ranges:
    - < 0.1: Excellent alignment
    - 0.1-0.3: Good alignment
    - 0.3-0.5: Moderate alignment
    - 0.5-0.7: Poor alignment
    - > 0.7: Very poor alignment
    """
    def classify(value):
        if value < 0.1:
            return "excellent"
        elif value < 0.3:
            return "good"
        elif value < 0.5:
            return "moderate"
        elif value < 0.7:
            return "poor"
        else:
            return "very_poor"

    return {
        'hc_to_hc': {
            'value': hc_mean,
            'category': classify(hc_mean)
        },
        'cvd_to_hc': {
            'value': cvd_mean,
            'category': classify(cvd_mean)
        }
    }


def print_comparison_table(normalized_results):
    """
    Print comparison table of normalized vs raw disparities.
    """
    print("\n" + "="*100)
    print("Procrustes Disparity: Raw vs Normalized")
    print("="*100)

    print(f"\n{'ROI':<8} {'Elements':<10} {'Raw HC→HC':<20} {'Norm HC→HC':<15} {'Raw CVD→HC':<20} {'Norm CVD→HC':<15}")
    print("-"*100)

    for roi in ['V1', 'V2', 'V3', 'hV4']:
        if roi not in normalized_results:
            continue

        data = normalized_results[roi]
        n_elem = data['n_elements']

        raw_hc = data['hc_to_hc']['raw']['mean']
        norm_hc = data['hc_to_hc']['normalized']['mean']

        raw_cvd = data['cvd_to_hc']['raw']['mean']
        norm_cvd = data['cvd_to_hc']['normalized']['mean']

        print(f"{roi:<8} {n_elem:<10} {raw_hc:<20.2f} {norm_hc:<15.4f} {raw_cvd:<20.2f} {norm_cvd:<15.4f}")

    print("\n" + "="*100)
    print("Interpretation Guide:")
    print("-"*100)
    print("Normalized Disparity Ranges:")
    print("  < 0.1:     Excellent alignment (< 10% residual variance)")
    print("  0.1-0.3:   Good alignment (10-30% residual)")
    print("  0.3-0.5:   Moderate alignment (30-50% residual)")
    print("  0.5-0.7:   Poor alignment (50-70% residual)")
    print("  > 0.7:     Very poor alignment (> 70% residual)")
    print("="*100)

    print("\nAlignment Quality by ROI:")
    print("-"*100)

    for roi in ['V1', 'V2', 'V3', 'hV4']:
        if roi not in normalized_results:
            continue

        interp = normalized_results[roi]['interpretation']
        hc_cat = interp['hc_to_hc']['category']
        cvd_cat = interp['cvd_to_hc']['category']

        print(f"{roi}:")
        print(f"  HC→HC:  {interp['hc_to_hc']['value']:.4f} ({hc_cat})")
        print(f"  CVD→HC: {interp['cvd_to_hc']['value']:.4f} ({cvd_cat})")

    print("="*100)


def main():
    parser = argparse.ArgumentParser(
        description='Compute normalized Procrustes disparities'
    )
    parser.add_argument('--input-file', type=str, required=True,
                        help='Input JSON with raw pairwise results')
    parser.add_argument('--output-file', type=str, required=True,
                        help='Output JSON for normalized results')

    args = parser.parse_args()

    # Load raw results
    with open(args.input_file) as f:
        results = json.load(f)

    # Voxel counts per ROI (from ANOVA selection)
    voxel_counts = {
        'V1': 129,
        'V2': 103,
        'V3': 50,
        'hV4': 57
    }

    # Normalize disparities
    normalized_results = normalize_disparities(results, voxel_counts)

    # Save results
    output_path = Path(args.output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(normalized_results, f, indent=2)

    # Print comparison table
    print_comparison_table(normalized_results)

    print(f"\n✅ Normalized results saved to: {output_path}")


if __name__ == '__main__':
    main()
