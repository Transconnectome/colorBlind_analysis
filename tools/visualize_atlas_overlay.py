#!/usr/bin/env python3
"""Visualize an anatomical NIfTI overlaid with a Wang/ProbAtlas NIfTI.

This script will:
 - load an anatomical image (subject T1)
 - load an atlas image (ProbAtlas maxprob or percent maps)
 - resample the atlas to the anatomical image grid (nearest for labels)
 - save the resampled atlas and overlay PNGs (axial/coronal/sagittal)

Usage:
 python tools/visualize_atlas_overlay.py --anat pilot/sub-01/anat/sub-01_acq-mprage_T1w.nii.gz \
     --atlas ProbAtlas_v4/subj_vol_all/maxprob_vol_lh.nii.gz --out derivatives/sub-01/diagnostics/atlas_overlay

"""
import os
import argparse
from pathlib import Path

import nibabel as nib
import numpy as np
from nilearn import plotting, image
import matplotlib.pyplot as plt


def ensure_dir(p):
    Path(p).mkdir(parents=True, exist_ok=True)


def resample_atlas_to_anat(atlas_img, anat_img, is_label=True):
    """Resample atlas to anatomical image grid.

    Parameters
    - atlas_img: nibabel/Image or path
    - anat_img: nibabel/Image or path
    - is_label: if True use nearest interpolation
    Returns resampled nilearn image
    """
    # use nilearn.image.resample_to_img which preserves affine/shape
    interp = 'nearest' if is_label else 'continuous'
    res = image.resample_to_img(atlas_img, anat_img, interpolation=interp)
    return res


def plot_overlays(anat_img, atlas_img_resampled, outdir, prefix="atlas_overlay"):
    ensure_dir(outdir)
    # Save a nilearn style overlay (plot_anat + plot_roi)
    out_pngs = []

    # Create three views
    views = [dict(cut_coords=None, display_mode='ortho'),
             dict(display_mode='x', cut_coords=None),
             dict(display_mode='y', cut_coords=None)]

    for i, v in enumerate(views):
        fig = plt.figure(figsize=(8, 8))
        ax = fig.add_subplot(111)
        display = plotting.plot_anat(anat_img, axes=ax, title=f"{prefix} view {i}", annotate=False)
        # overlay with transparency
        display.add_overlay(atlas_img_resampled, cmap='tab20', alpha=0.6)
        out_png = os.path.join(outdir, f"{prefix}_view{i}.png")
        fig.savefig(out_png, dpi=150, bbox_inches='tight')
        plt.close(fig)
        out_pngs.append(out_png)

    # also save an outline view using plot_roi
    fig = plt.figure(figsize=(8, 8))
    ax = fig.add_subplot(111)
    plotting.plot_roi(atlas_img_resampled, bg_img=anat_img, title=f"{prefix}_roi_outline")
    out_png = os.path.join(outdir, f"{prefix}_roi_outline.png")
    fig.savefig(out_png, dpi=150, bbox_inches='tight')
    plt.close(fig)
    out_pngs.append(out_png)

    return out_pngs


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--anat', required=True, help='Path to anatomical NIfTI (T1w)')
    p.add_argument('--atlas', required=True, help='Path to atlas NIfTI (Wang / ProbAtlas)')
    p.add_argument('--out', required=True, help='Output directory to save overlays and resampled atlas')
    p.add_argument('--label', action='store_true', help='Treat atlas as label image (nearest interpolation)')
    args = p.parse_args()

    anat_path = Path(args.anat)
    atlas_path = Path(args.atlas)
    outdir = Path(args.out)
    ensure_dir(outdir)

    if not anat_path.exists():
        raise SystemExit(f"Anatomical file not found: {anat_path}")
    if not atlas_path.exists():
        raise SystemExit(f"Atlas file not found: {atlas_path}")

    print(f"Loading anat: {anat_path}")
    anat_img = nib.load(str(anat_path))

    print(f"Loading atlas: {atlas_path}")
    atlas_img = nib.load(str(atlas_path))

    # Resample atlas to anatomical grid
    print("Resampling atlas to anatomical grid (this may take a few seconds)...")
    atlas_res = resample_atlas_to_anat(atlas_img, anat_img, is_label=args.label)

    # Save resampled atlas
    resampled_path = outdir / (atlas_path.stem + '_resampled_to_anat.nii.gz')
    nib.save(atlas_res, str(resampled_path))
    print(f"Saved resampled atlas to: {resampled_path}")

    # Quick checks: print shapes/affines
    print(f"Anat shape: {anat_img.shape}, affine:\n{anat_img.affine}")
    print(f"Atlas original shape: {atlas_img.shape}, affine:\n{atlas_img.affine}")
    print(f"Atlas resampled shape: {atlas_res.shape}, affine:\n{atlas_res.affine}")

    # Plot overlays
    print("Generating overlay PNGs...")
    pngs = plot_overlays(str(anat_path), atlas_res, str(outdir), prefix=atlas_path.stem)

    # Write a small report
    report = outdir / 'report.txt'
    with open(report, 'w') as fh:
        fh.write(f"anat: {anat_path}\n")
        fh.write(f"atlas: {atlas_path}\n")
        fh.write(f"resampled_atlas: {resampled_path}\n")
        fh.write("pngs:\n")
        for pp in pngs:
            fh.write(f" - {pp}\n")
    print(f"Wrote report: {report}")
    print("Done.")


if __name__ == '__main__':
    main()
