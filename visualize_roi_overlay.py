#!/usr/bin/env python3
"""
visualize_roi_overlay.py
------------------------
ROI mask를 BOLD 이미지 위에 overlay하여 시각화
기존 과정과 동일한 방법으로 정렬 확인
"""

import os
import sys
import nibabel as nib
import numpy as np
import matplotlib.pyplot as plt
from nilearn import plotting, image

def create_roi_overlay(roi_path, bold_path, roi_name, output_dir):
    """ROI overlay 시각화 생성"""

    print(f"Processing {roi_name}...")

    # ROI mask 로드
    roi_img = nib.load(roi_path)

    # BOLD mean 이미지 생성 (background로 사용)
    bold_img = nib.load(bold_path)
    mean_bold = image.mean_img(bold_img)

    # Output path
    output_path = os.path.join(output_dir, f'{roi_name}_overlay.png')

    # Overlay plot 생성
    display = plotting.plot_roi(
        roi_img,
        bg_img=mean_bold,
        title=f'{roi_name} ROI Overlay on BOLD',
        cut_coords=(-10, -80, 0),  # Occipital cortex 중심
        display_mode='ortho',
        cmap='Reds',
        alpha=0.7,
        output_file=output_path
    )

    print(f"  ✅ Saved: {output_path}")

    # Voxel count 정보 추가
    roi_data = roi_img.get_fdata()
    n_voxels = (roi_data > 0).sum()

    # BOLD와 overlap 확인
    bold_data = bold_img.get_fdata()
    bold_mean_data = bold_data.mean(axis=-1)
    epi_mask = bold_mean_data > 0
    roi_mask = roi_data > 0
    overlap = np.logical_and(roi_mask, epi_mask)
    overlap_ratio = overlap.sum() / n_voxels if n_voxels > 0 else 0

    print(f"  Voxel count: {n_voxels}")
    print(f"  EPI overlap: {overlap.sum()}/{n_voxels} ({overlap_ratio*100:.1f}%)")

    return output_path


def create_all_rois_combined(roi_paths, bold_path, output_dir):
    """모든 ROI를 하나의 이미지에 표시"""

    print(f"\nCreating combined ROI overlay...")

    # BOLD mean 이미지
    bold_img = nib.load(bold_path)
    mean_bold = image.mean_img(bold_img)

    # 큰 figure 생성
    fig, axes = plt.subplots(2, 2, figsize=(16, 14))
    fig.suptitle('All ROIs Overlay on BOLD (MNI152NLin2009cAsym:res-2)',
                 fontsize=16, fontweight='bold')

    rois = ['V1', 'V2', 'V3', 'hV4']

    for idx, roi_name in enumerate(rois):
        roi_path = roi_paths.get(roi_name)

        if roi_path is None or not os.path.exists(roi_path):
            print(f"  ⚠️ Skipping {roi_name} (not found)")
            continue

        roi_img = nib.load(roi_path)
        roi_data = roi_img.get_fdata()
        n_voxels = (roi_data > 0).sum()

        ax = axes[idx // 2, idx % 2]

        # Overlay plot
        plotting.plot_roi(
            roi_img,
            bg_img=mean_bold,
            title=f'{roi_name} (n={n_voxels} voxels)',
            cut_coords=(-10, -80, 0),
            display_mode='ortho',
            cmap='Reds',
            alpha=0.7,
            axes=ax
        )

    plt.tight_layout()

    output_path = os.path.join(output_dir, 'all_rois_overlay.png')
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"  ✅ Saved: {output_path}")

    return output_path


def create_glass_brain_view(roi_paths, output_dir):
    """Glass brain view - 전체 뇌에서 ROI 위치 파악"""

    print(f"\nCreating glass brain view...")

    fig = plt.figure(figsize=(16, 10))
    fig.suptitle('ROI Locations - Glass Brain View', fontsize=16, fontweight='bold')

    rois = ['V1', 'V2', 'V3', 'hV4']
    colors = ['blue', 'red', 'green', 'orange']

    for idx, (roi_name, color) in enumerate(zip(rois, colors)):
        roi_path = roi_paths.get(roi_name)

        if roi_path is None or not os.path.exists(roi_path):
            print(f"  ⚠️ Skipping {roi_name} (not found)")
            continue

        roi_img = nib.load(roi_path)

        ax = plt.subplot(2, 2, idx + 1)

        plotting.plot_glass_brain(
            roi_img,
            title=f'{roi_name}',
            colorbar=False,
            cmap=color,
            alpha=0.8,
            axes=ax
        )

    plt.tight_layout()

    output_path = os.path.join(output_dir, 'glass_brain_view.png')
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"  ✅ Saved: {output_path}")

    return output_path


def main():
    """Main visualization function"""

    # Config
    try:
        from config import cfg
        sub_id = cfg.SUB_ID
        project_dir = cfg.PROJECT_DIR
    except ImportError:
        print("⚠️ Could not import config, using defaults")
        sub_id = 'P01'
        project_dir = os.path.dirname(os.path.abspath(__file__))

    # Paths
    roi_dir = os.path.join(project_dir, 'derivatives', f'sub-{sub_id}', 'roi')
    output_dir = os.path.join(roi_dir, 'qc_figures')
    os.makedirs(output_dir, exist_ok=True)

    # Reference BOLD image (run-1)
    bold_path = f'/storage/connectome/haba6030/fmriprep_out/sub-{sub_id}/func/sub-01_task-rsvp_run-1_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz'

    # Check if BOLD exists
    if not os.path.exists(bold_path):
        # Try alternative path
        bold_path = os.path.join(
            project_dir, 'output', 'pilot', f'sub-{sub_id}', 'func',
            f'sub-{sub_id}_task-rsvp_run-1_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz'
        )

    if not os.path.exists(bold_path):
        print(f"❌ ERROR: Could not find reference BOLD image")
        print(f"   Tried: {bold_path}")
        sys.exit(1)

    print("="*60)
    print("ROI OVERLAY VISUALIZATION")
    print("="*60)
    print(f"Subject: {sub_id}")
    print(f"ROI Directory: {roi_dir}")
    print(f"Output Directory: {output_dir}")
    print(f"Reference BOLD: {bold_path}")
    print("="*60)

    # ROI paths
    rois = ['V1', 'V2', 'V3', 'hV4']
    roi_paths = {}

    for roi_name in rois:
        roi_path = os.path.join(roi_dir, f'sub-{sub_id}_{roi_name}_mask.nii.gz')
        if os.path.exists(roi_path):
            roi_paths[roi_name] = roi_path
        else:
            print(f"⚠️ WARNING: {roi_name} mask not found at {roi_path}")

    if not roi_paths:
        print("❌ ERROR: No ROI masks found!")
        print(f"\nExpected location: {roi_dir}/sub-{sub_id}_<ROI>_mask.nii.gz")
        print(f"\n💡 Run roi_build.py first to create ROI masks")
        sys.exit(1)

    # 1. Individual ROI overlays
    print(f"\n1. Creating individual ROI overlays...")
    print("-" * 60)
    for roi_name, roi_path in roi_paths.items():
        create_roi_overlay(roi_path, bold_path, roi_name, output_dir)

    # 2. Combined view
    print(f"\n2. Creating combined ROI view...")
    print("-" * 60)
    create_all_rois_combined(roi_paths, bold_path, output_dir)

    # 3. Glass brain view
    print(f"\n3. Creating glass brain view...")
    print("-" * 60)
    create_glass_brain_view(roi_paths, output_dir)

    # Summary
    print("\n" + "="*60)
    print("✅ VISUALIZATION COMPLETE!")
    print("="*60)
    print(f"\nOutput files saved in: {output_dir}")
    print(f"\nGenerated files:")
    print(f"  - Individual overlays: V1_overlay.png, V2_overlay.png, etc.")
    print(f"  - Combined view: all_rois_overlay.png")
    print(f"  - Glass brain: glass_brain_view.png")
    print("\n📝 Check these images to verify:")
    print("  ✓ ROIs are in occipital cortex (visual areas)")
    print("  ✓ ROIs are symmetric (left/right)")
    print("  ✓ ROIs don't extend outside brain")
    print("  ✓ ROIs overlap with BOLD activation")
    print("="*60)

    return 0


if __name__ == '__main__':
    sys.exit(main())
