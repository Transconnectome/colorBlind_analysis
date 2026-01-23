#!/usr/bin/env python3
"""
Visualize T1w brain images: Sub-01 vs Sub-07
Compare brain extraction quality
"""

import nibabel as nib
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

def load_and_check_nifti(file_path):
    """Load NIfTI file and check validity"""
    try:
        img = nib.load(file_path)
        data = img.get_fdata()

        print(f"\n📊 {file_path.name}")
        print(f"   Shape: {data.shape}")
        print(f"   Data range: [{data.min():.2f}, {data.max():.2f}]")
        print(f"   Non-zero voxels: {np.count_nonzero(data):,}")
        print(f"   Affine:\n{img.affine}")

        return img, data
    except Exception as e:
        print(f"❌ Error loading {file_path}: {e}")
        return None, None

def create_brain_comparison_figure(sub01_data, sub07_data, output_path):
    """Create side-by-side comparison of brain images"""

    # Select middle slices
    if sub01_data is not None:
        mid_slice_01 = sub01_data.shape[2] // 2
        sagittal_01 = sub01_data[sub01_data.shape[0]//2, :, :]
        coronal_01 = sub01_data[:, sub01_data.shape[1]//2, :]
        axial_01 = sub01_data[:, :, mid_slice_01]

    if sub07_data is not None:
        mid_slice_07 = sub07_data.shape[2] // 2
        sagittal_07 = sub07_data[sub07_data.shape[0]//2, :, :]
        coronal_07 = sub07_data[:, sub07_data.shape[1]//2, :]
        axial_07 = sub07_data[:, :, mid_slice_07]

    # Create figure
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    fig.suptitle('Brain Extraction Comparison: Sub-01 vs Sub-07', fontsize=16, fontweight='bold')

    # Sub-01 (top row)
    if sub01_data is not None:
        axes[0, 0].imshow(sagittal_01.T, cmap='gray', origin='lower')
        axes[0, 0].set_title('Sub-01: Sagittal', fontweight='bold')
        axes[0, 0].axis('off')

        axes[0, 1].imshow(coronal_01.T, cmap='gray', origin='lower')
        axes[0, 1].set_title('Sub-01: Coronal', fontweight='bold')
        axes[0, 1].axis('off')

        axes[0, 2].imshow(axial_01.T, cmap='gray', origin='lower')
        axes[0, 2].set_title('Sub-01: Axial', fontweight='bold')
        axes[0, 2].axis('off')

        # Add voxel count
        voxel_count_01 = np.count_nonzero(sub01_data)
        fig.text(0.5, 0.48, f'Sub-01: {voxel_count_01:,} voxels',
                ha='center', fontsize=12, fontweight='bold', color='green')

    # Sub-07 (bottom row)
    if sub07_data is not None:
        axes[1, 0].imshow(sagittal_07.T, cmap='gray', origin='lower')
        axes[1, 0].set_title('Sub-07: Sagittal', fontweight='bold')
        axes[1, 0].axis('off')

        axes[1, 1].imshow(coronal_07.T, cmap='gray', origin='lower')
        axes[1, 1].set_title('Sub-07: Coronal', fontweight='bold')
        axes[1, 1].axis('off')

        axes[1, 2].imshow(axial_07.T, cmap='gray', origin='lower')
        axes[1, 2].set_title('Sub-07: Axial', fontweight='bold')
        axes[1, 2].axis('off')

        # Add voxel count
        voxel_count_07 = np.count_nonzero(sub07_data)
        fig.text(0.5, 0.02, f'Sub-07: {voxel_count_07:,} voxels',
                ha='center', fontsize=12, fontweight='bold', color='red')

        # Calculate difference
        if sub01_data is not None:
            diff_pct = ((voxel_count_01 - voxel_count_07) / voxel_count_01) * 100
            fig.text(0.5, 0.50, f'Difference: {diff_pct:.1f}% smaller',
                    ha='center', fontsize=14, fontweight='bold',
                    color='red' if diff_pct > 20 else 'orange')

    plt.tight_layout(rect=[0, 0.03, 1, 0.97])
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\n✅ Visualization saved: {output_path}")

    return fig

def create_intensity_histograms(sub01_data, sub07_data, output_path):
    """Compare intensity distributions"""

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle('Brain Signal Intensity Distributions', fontsize=14, fontweight='bold')

    if sub01_data is not None:
        # Only non-zero values
        nonzero_01 = sub01_data[sub01_data > 0]
        axes[0].hist(nonzero_01, bins=100, color='green', alpha=0.7)
        axes[0].set_title(f'Sub-01 (n={len(nonzero_01):,} voxels)', fontweight='bold')
        axes[0].set_xlabel('Signal Intensity')
        axes[0].set_ylabel('Frequency')
        axes[0].grid(True, alpha=0.3)

        # Add statistics
        axes[0].axvline(np.mean(nonzero_01), color='red', linestyle='--',
                       label=f'Mean: {np.mean(nonzero_01):.1f}')
        axes[0].axvline(np.median(nonzero_01), color='blue', linestyle='--',
                       label=f'Median: {np.median(nonzero_01):.1f}')
        axes[0].legend()

    if sub07_data is not None:
        nonzero_07 = sub07_data[sub07_data > 0]
        axes[1].hist(nonzero_07, bins=100, color='red', alpha=0.7)
        axes[1].set_title(f'Sub-07 (n={len(nonzero_07):,} voxels)', fontweight='bold')
        axes[1].set_xlabel('Signal Intensity')
        axes[1].set_ylabel('Frequency')
        axes[1].grid(True, alpha=0.3)

        # Add statistics
        axes[1].axvline(np.mean(nonzero_07), color='red', linestyle='--',
                       label=f'Mean: {np.mean(nonzero_07):.1f}')
        axes[1].axvline(np.median(nonzero_07), color='blue', linestyle='--',
                       label=f'Median: {np.median(nonzero_07):.1f}')
        axes[1].legend()

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"✅ Histogram saved: {output_path}")

    return fig

def main():
    logs_dir = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/prep_trials/logs')

    # Try to find the brain files
    sub07_file = logs_dir / 'sub-07_T1w_brain.nii'
    sub01_file = logs_dir / 'brain_file_2.nii'  # Might be sub-01

    print("="*80)
    print("T1w Brain Visualization: Sub-01 vs Sub-07")
    print("="*80)

    # Load files
    print("\n📁 Loading files...")
    sub07_img, sub07_data = load_and_check_nifti(sub07_file)

    # Try brain_file_2
    if sub01_file.exists():
        print("\nTrying brain_file_2 as Sub-01...")
        sub01_img, sub01_data = load_and_check_nifti(sub01_file)

        # If it's not valid NIfTI, set to None
        if sub01_data is not None and (sub01_data.shape[0] > 500 or sub01_data.max() < 10):
            print("⚠️  brain_file_2 doesn't look like a valid brain image")
            sub01_data = None
    else:
        sub01_data = None

    # Create visualizations
    if sub07_data is not None:
        print("\n🎨 Creating visualizations...")

        # Brain comparison
        output_path = logs_dir / 'brain_comparison.png'
        create_brain_comparison_figure(sub01_data, sub07_data, output_path)

        # Intensity histograms
        hist_path = logs_dir / 'intensity_comparison.png'
        create_intensity_histograms(sub01_data, sub07_data, hist_path)

        print("\n" + "="*80)
        print("Analysis Complete!")
        print("="*80)
        print(f"\nOutput files:")
        print(f"  - {output_path}")
        print(f"  - {hist_path}")

        # Summary
        print("\n📊 Summary:")
        if sub01_data is not None and sub07_data is not None:
            vox_01 = np.count_nonzero(sub01_data)
            vox_07 = np.count_nonzero(sub07_data)
            diff = ((vox_01 - vox_07) / vox_01) * 100

            print(f"  Sub-01: {vox_01:,} voxels")
            print(f"  Sub-07: {vox_07:,} voxels")
            print(f"  Difference: {diff:.1f}% smaller")

            if diff > 30:
                print("\n❌ VERDICT: Sub-07 brain mask is significantly smaller!")
                print("   This confirms brain extraction (bet2 -f 0.5) was too conservative.")
            elif diff > 15:
                print("\n⚠️  VERDICT: Sub-07 brain mask is moderately smaller")
                print("   This may contribute to lower ROI coverage.")
            else:
                print("\n✅ VERDICT: Brain mask sizes are similar")
                print("   Brain extraction is not the main issue.")
        else:
            print("  Only Sub-07 data available")
            print(f"  Sub-07: {np.count_nonzero(sub07_data):,} voxels")
    else:
        print("\n❌ ERROR: Could not load Sub-07 brain data")

if __name__ == '__main__':
    main()
