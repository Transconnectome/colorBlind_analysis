#!/usr/bin/env python3
"""
Apply Phase 2A Filter + W Matrix Reconstruction Pipeline

Pipeline:
1. Load CVD raw voxel patterns (measured fMRI data)
2. Apply Phase 2A filter (A, b) → Filtered voxels
3. Apply W matrix → Channels (6D)
4. Channels → Hue reconstruction
5. Hue → RGB conversion

Usage:
    python scripts/apply_filter_with_reconstruction.py --subject 08 --roi V1
    python scripts/apply_filter_with_reconstruction.py --subject 09 --roi V2
"""

import numpy as np
import pickle
from pathlib import Path
import argparse
import matplotlib.pyplot as plt
from skimage import color as skcolor
import json
from scipy.spatial import procrustes

# ============================================================================
# Configuration
# ============================================================================

BASE_DIR = Path.cwd()
DERIVATIVES_DIR = BASE_DIR / "derivatives/BH2009_deoblique_v2/baseline32_deob_determin"
FILTER_DIR = BASE_DIR / "results/group_level/phase2a_data/models_optionA"
W_DIR = BASE_DIR / "results/group_level/procrustes_reconstruction_baseline32"
OUTPUT_DIR = BASE_DIR / "results/group_level/filter_reconstruction"

COLOR_NAMES = ['Red', 'Orange', 'Yellow', 'Chartreuse',
               'Green', 'Cyan', 'Blue', 'Magenta']

LABEL2HUE_DEG = {
    'color_1': 0.0, 'color_2': 45.0, 'color_3': 90.0, 'color_4': 135.0,
    'color_5': 180.0, 'color_6': 225.0, 'color_7': 270.0, 'color_8': 315.0,
}

# ============================================================================
# Helper Functions
# ============================================================================

def create_basis_functions(n_channels=6):
    """Create 6-channel color basis functions (Brouwer & Heeger 2009)"""
    hues = np.linspace(0, 360, n_channels, endpoint=False)
    basis = np.zeros((360, n_channels))

    for i, center_hue in enumerate(hues):
        for h in range(360):
            dist = np.abs(h - center_hue)
            if dist > 180:
                dist = 360 - dist
            response = np.cos(np.deg2rad(dist))
            if response > 0:
                basis[h, i] = response ** 2
            else:
                basis[h, i] = 0

    return basis


def circular_diff_deg(a, b):
    """Circular distance in degrees [0, 180]"""
    diff = np.abs(a - b)
    diff = np.where(diff > 180, 360 - diff, diff)
    return diff


def hue_to_rgb(hue_deg, L=70, chroma=50):
    """
    Convert hue (degrees) to RGB

    Parameters:
    - hue_deg: Hue in degrees [0, 360]
    - L: Lightness (fixed at 70, matching original stimulus)
    - chroma: Chroma radius (fixed at 50)

    Returns:
    - rgb: RGB values [0, 1]
    """
    # Hue → CIELAB a*b*
    hue_rad = np.deg2rad(hue_deg)
    a_star = chroma * np.cos(hue_rad)
    b_star = chroma * np.sin(hue_rad)

    # CIELAB → RGB
    lab = np.array([L, a_star, b_star])
    rgb = skcolor.lab2rgb(lab[np.newaxis, np.newaxis, :])

    return rgb[0, 0, :]


# ============================================================================
# Main Pipeline
# ============================================================================

def load_cvd_raw_pattern(subject_id, roi):
    """Load CVD raw voxel pattern from baseline analysis"""
    pattern_glob = list(DERIVATIVES_DIR.glob(f"*sub-{subject_id}_{roi}_*"))

    if not pattern_glob:
        raise FileNotFoundError(f"No baseline results for sub-{subject_id} {roi}")

    result_dir = pattern_glob[0]
    amp_file = result_dir / "amplitudes_z.npy"

    if not amp_file.exists():
        raise FileNotFoundError(f"amplitudes_z.npy not found in {result_dir}")

    # Load (n_runs, n_colors, n_voxels)
    amplitudes_z = np.load(amp_file)

    # Average across runs
    pattern = np.mean(amplitudes_z, axis=0)  # (8, n_voxels)

    print(f"Loaded CVD raw pattern: {pattern.shape}")
    return pattern


def load_filter(subject_id, roi):
    """Load Phase 2A filter (A, b)"""
    filter_path = FILTER_DIR / f"sub-{subject_id}" / roi

    A = np.load(filter_path / "A_matrix.npy")
    b = np.load(filter_path / "b_vector.npy")

    print(f"Loaded filter: A {A.shape}, b {b.shape}")
    return A, b


def load_w_matrix(roi):
    """Load Procrustes W matrix and HC reference"""
    model_path = W_DIR / roi / "procrustes_model.pkl"

    with open(model_path, 'rb') as f:
        model_data = pickle.load(f)

    W = model_data['W_common']
    basis = model_data['basis_functions']
    hc_reference = model_data['hc_reference']

    print(f"Loaded W matrix: {W.shape}")
    print(f"Loaded HC reference: {hc_reference.shape}")
    return W, basis, hc_reference


def apply_pipeline(subject_id, roi, save_results=True):
    """
    Full pipeline: CVD raw → Filter → Procrustes → W → Channels → Hue → RGB

    Returns:
        results: dict with all intermediate steps and final RGB
    """
    print(f"\n{'='*70}")
    print(f"Filter + Reconstruction Pipeline")
    print(f"Subject: {subject_id}, ROI: {roi}")
    print(f"{'='*70}\n")

    # ========================================================================
    # Step 1: Load CVD raw voxel pattern
    # ========================================================================
    print("[1/6] Loading CVD raw voxel pattern...")
    CVD_raw = load_cvd_raw_pattern(subject_id, roi)  # (8, n_voxels_cvd)
    n_voxels_cvd = CVD_raw.shape[1]

    # ========================================================================
    # Step 2: Apply Phase 2A filter
    # ========================================================================
    print("\n[2/6] Applying Phase 2A filter (A, b)...")
    A, b = load_filter(subject_id, roi)

    # Check dimension match
    n_voxels_filter = A.shape[0]
    if n_voxels_cvd != n_voxels_filter:
        raise ValueError(f"Voxel mismatch: CVD={n_voxels_cvd}, Filter={n_voxels_filter}")

    # Apply filter: X_filtered = X_raw @ A + b
    X_filtered = CVD_raw @ A + b  # (8, n_voxels)
    print(f"Filtered voxels: {X_filtered.shape}")

    # ========================================================================
    # Step 3: Load W matrix and HC reference
    # ========================================================================
    print("\n[3/7] Loading W matrix and HC reference...")
    W_full, basis, hc_reference = load_w_matrix(roi)
    n_voxels_w = W_full.shape[0]

    # Truncate to minimum voxels
    min_voxels = min(n_voxels_cvd, n_voxels_w)
    print(f"Voxel counts: Filter={n_voxels_cvd}, W={n_voxels_w}")
    print(f"Using minimum: {min_voxels}")

    X_filtered_trunc = X_filtered[:, :min_voxels]
    hc_ref_trunc = hc_reference[:, :min_voxels]
    W_truncated = W_full[:min_voxels, :]
    print(f"Truncated: X_filtered={X_filtered_trunc.shape}, HC_ref={hc_ref_trunc.shape}, W={W_truncated.shape}")

    # ========================================================================
    # Step 4: Procrustes Alignment (CRITICAL!)
    # ========================================================================
    print("\n[4/7] Applying Procrustes alignment to filtered voxels...")
    print("  Aligning filter output to HC reference space...")

    _, X_aligned, disparity = procrustes(hc_ref_trunc, X_filtered_trunc)

    print(f"  Procrustes disparity: {disparity:.4f}")
    print(f"  Aligned voxels: {X_aligned.shape}")

    if disparity > 0.1:
        print(f"  ⚠️  Warning: High disparity ({disparity:.4f}) - alignment may be poor")
    else:
        print(f"  ✅ Good alignment (disparity < 0.1)")

    # ========================================================================
    # Step 5: Apply W matrix (Aligned Voxels → Channels)
    # ========================================================================
    print("\n[5/7] Estimating channels from aligned voxels...")

    # C = (W^T W)^-1 W^T X^T
    C_estimated = np.linalg.pinv(W_truncated.T @ W_truncated) @ W_truncated.T @ X_aligned.T
    C_estimated = C_estimated.T  # (8, 6)
    print(f"Estimated channels: {C_estimated.shape}")

    # ========================================================================
    # Step 6: Channels → Hue reconstruction
    # ========================================================================
    print("\n[6/7] Reconstructing hues from channels...")

    reconstructed_hues = []
    reconstruction_errors = []

    for color_idx in range(8):
        channels = C_estimated[color_idx, :]  # (6,)

        # Find best matching hue via correlation
        correlations = []
        for h in range(360):
            template = basis[h, :]  # (6,)
            corr = np.corrcoef(channels, template)[0, 1]
            correlations.append(corr)

        best_hue = np.argmax(correlations)
        reconstructed_hues.append(best_hue)

        # Compute error
        true_hue = LABEL2HUE_DEG[f'color_{color_idx + 1}']
        error = circular_diff_deg(best_hue, true_hue)
        reconstruction_errors.append(error)

        print(f"  {COLOR_NAMES[color_idx]:12s}: True={true_hue:6.1f}°, "
              f"Recon={best_hue:6.1f}°, Error={error:5.1f}°")

    reconstructed_hues = np.array(reconstructed_hues)
    reconstruction_errors = np.array(reconstruction_errors)

    mean_error = np.mean(reconstruction_errors)
    print(f"\n  Mean reconstruction error: {mean_error:.1f}°")
    print(f"  Chance level: 90.0°")

    if mean_error < 90.0:
        print(f"  ✅ Better than chance!")
    else:
        print(f"  ⚠️  At or worse than chance level")

    # ========================================================================
    # Step 7: Hue → RGB conversion
    # ========================================================================
    print("\n[7/7] Converting hues to RGB...")

    true_hues = [LABEL2HUE_DEG[f'color_{i+1}'] for i in range(8)]

    original_rgbs = []
    modified_rgbs = []

    for true_hue, recon_hue in zip(true_hues, reconstructed_hues):
        original_rgb = hue_to_rgb(true_hue, L=70, chroma=50)
        modified_rgb = hue_to_rgb(recon_hue, L=70, chroma=50)

        original_rgbs.append(original_rgb)
        modified_rgbs.append(modified_rgb)

    original_rgbs = np.array(original_rgbs)
    modified_rgbs = np.array(modified_rgbs)

    print(f"  Original RGBs: {original_rgbs.shape}")
    print(f"  Modified RGBs: {modified_rgbs.shape}")

    # ========================================================================
    # Save results
    # ========================================================================
    if save_results:
        output_dir = OUTPUT_DIR / f"sub-{subject_id}" / roi
        output_dir.mkdir(parents=True, exist_ok=True)

        results = {
            'subject_id': subject_id,
            'roi': roi,
            'n_voxels_raw': n_voxels_cvd,
            'n_voxels_used': min_voxels,
            'cvd_raw': CVD_raw,
            'filtered_voxels': X_filtered_trunc,
            'channels': C_estimated,
            'reconstructed_hues': reconstructed_hues,
            'true_hues': true_hues,
            'reconstruction_errors': reconstruction_errors,
            'mean_error': mean_error,
            'original_rgbs': original_rgbs,
            'modified_rgbs': modified_rgbs,
        }

        # Save as pickle
        with open(output_dir / 'reconstruction_results.pkl', 'wb') as f:
            pickle.dump(results, f)

        # Save summary as JSON
        summary = {
            'subject_id': subject_id,
            'roi': roi,
            'mean_reconstruction_error': float(mean_error),
            'reconstruction_errors': reconstruction_errors.tolist(),
            'reconstructed_hues': reconstructed_hues.tolist(),
            'true_hues': true_hues,
            'better_than_chance': bool(mean_error < 90.0),
        }

        with open(output_dir / 'summary.json', 'w') as f:
            json.dump(summary, f, indent=2)

        # Save RGBs
        np.save(output_dir / 'original_rgbs.npy', original_rgbs)
        np.save(output_dir / 'modified_rgbs.npy', modified_rgbs)

        print(f"\n  Results saved to: {output_dir}")

    return results


# ============================================================================
# Visualization
# ============================================================================

def visualize_results(results, save_path=None):
    """Create visualization of reconstruction results"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # 1. Reconstruction error per color
    ax = axes[0, 0]
    x = np.arange(8)
    bars = ax.bar(x, results['reconstruction_errors'], color='steelblue',
                   edgecolor='black', alpha=0.7)
    ax.axhline(90.0, color='red', linestyle='--', linewidth=2, label='Chance (90°)')
    ax.set_xticks(x)
    ax.set_xticklabels(COLOR_NAMES, rotation=45, ha='right')
    ax.set_ylabel('Reconstruction Error (°)', fontsize=12)
    ax.set_title(f'Reconstruction Error (Mean: {results["mean_error"]:.1f}°)',
                 fontsize=13, fontweight='bold')
    ax.legend()
    ax.grid(axis='y', alpha=0.3)

    # 2. True vs Reconstructed hues
    ax = axes[0, 1]
    ax.scatter(results['true_hues'], results['reconstructed_hues'],
               s=100, alpha=0.7, edgecolors='black')
    ax.plot([0, 360], [0, 360], 'r--', linewidth=2, label='Perfect reconstruction')
    ax.set_xlabel('True Hue (°)', fontsize=12)
    ax.set_ylabel('Reconstructed Hue (°)', fontsize=12)
    ax.set_title('True vs Reconstructed Hues', fontsize=13, fontweight='bold')
    ax.legend()
    ax.grid(alpha=0.3)
    ax.set_xlim(-10, 370)
    ax.set_ylim(-10, 370)

    # 3. Original RGB colors
    ax = axes[1, 0]
    ax.imshow(results['original_rgbs'][np.newaxis, :, :], aspect='auto')
    ax.set_yticks([])
    ax.set_xticks(x)
    ax.set_xticklabels(COLOR_NAMES, rotation=45, ha='right')
    ax.set_title('Original RGB Colors', fontsize=13, fontweight='bold')

    # 4. Modified RGB colors
    ax = axes[1, 1]
    ax.imshow(results['modified_rgbs'][np.newaxis, :, :], aspect='auto')
    ax.set_yticks([])
    ax.set_xticks(x)
    ax.set_xticklabels(COLOR_NAMES, rotation=45, ha='right')
    ax.set_title('Modified RGB Colors (Filtered)', fontsize=13, fontweight='bold')

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Visualization saved: {save_path}")

    return fig


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='Apply filter + reconstruction pipeline')
    parser.add_argument('--subject', type=str, required=True, help='CVD subject ID (08, 09, 10)')
    parser.add_argument('--roi', type=str, required=True, help='ROI (V1, V2, V3, hV4)')
    parser.add_argument('--no-save', action='store_true', help='Do not save results')
    args = parser.parse_args()

    # Run pipeline
    results = apply_pipeline(args.subject, args.roi, save_results=not args.no_save)

    # Visualize
    if not args.no_save:
        output_dir = OUTPUT_DIR / f"sub-{args.subject}" / args.roi
        fig = visualize_results(results, save_path=output_dir / 'reconstruction_plot.png')
    else:
        fig = visualize_results(results)
        plt.show()


if __name__ == '__main__':
    main()
