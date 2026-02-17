#!/usr/bin/env python3
"""
Inflated Posterior View — Visual Cortex RMS Activation (V1 + V2)

Data source: C010 pipeline (method3_header_mi, Procrustes-aligned amplitudes)
Masks: Subject-specific ROI masks (maskfunc, gmTrue, subjFalse)

Usage:
    conda activate srm
    python analysis/phase2_procrustes_cvd_hc/plot_inflated_posterior.py
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import nibabel as nib
from nilearn import datasets, surface, plotting
from pathlib import Path
import warnings
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', category=RuntimeWarning)

# ============================================================================
# Configuration
# ============================================================================
BASE_DIR = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis')
C010_DIR = BASE_DIR / 'analysis' / 'phase1_preprocess_decoding' / 'results' / 'full_dataset_C010'
MASK_DIR = BASE_DIR / 'analysis' / 'roi_masks' / 'method3_header_mi' / 'method3_header_mi'
ATLAS_DIR = BASE_DIR / 'ProbAtlas_v4' / 'subj_vol_all'
OUTPUT_DIR = BASE_DIR / 'analysis' / 'phase2_procrustes_cvd_hc' / 'visualization'

HC_SUBJECTS = ['sub-01', 'sub-02', 'sub-03', 'sub-04', 'sub-05', 'sub-06', 'sub-07']
CVD_SUBJECTS = {
    'sub-08': 'Deuteranopia',
    'sub-09': 'Deuteranopia',
    'sub-10': 'Protanopia',
}

ROI_MASK_MAP = {'V1': 'V1', 'V2': 'V2'}
ROI_ATLAS_MAP = {'V1': 'roi1', 'V2': 'roi2'}
ROIS = ['V1', 'V2']
ROI_COLORS = {'V1': '#00FFFF', 'V2': '#FFD700'}


# ============================================================================
# Data loading
# ============================================================================
def get_mask_path(subject, roi):
    prefix = ROI_MASK_MAP[roi]
    return MASK_DIR / subject / 'roi_pipeline' / \
        f'{prefix}_mask_thr50_intnearest_binTrue_maskfunc_gmTrue_subjFalse.nii.gz'


def load_amplitudes(subject, roi):
    return np.load(C010_DIR / subject / roi / 'amplitudes_procrustes.npy')


def create_combined_volume(subject, rois, values_per_roi):
    ref_mask = nib.load(get_mask_path(subject, rois[0]))
    combined = np.full(ref_mask.shape[:3], np.nan, dtype=np.float32)

    for roi in rois:
        mask_img = nib.load(get_mask_path(subject, roi))
        mask_data = mask_img.get_fdata() > 0
        active_ijk = np.argwhere(mask_data)
        vals = values_per_roi[roi]
        n_fill = min(len(vals), len(active_ijk))
        for idx in range(n_fill):
            i, j, k = active_ijk[idx]
            combined[i, j, k] = vals[idx]

    return nib.Nifti1Image(combined, ref_mask.affine)


# ============================================================================
# Surface projection
# ============================================================================
def project_to_surface(brain_img, fsaverage, hemi):
    return surface.vol_to_surf(
        brain_img,
        fsaverage[f'pial_{hemi}'],
        inner_mesh=fsaverage[f'white_{hemi}'],
        interpolation='linear',
        radius=3.0,
    )


def get_roi_contour_labels(fsaverage):
    roi_labels = {}
    for roi in ROIS:
        roi_num = ROI_ATLAS_MAP[roi]
        lh_img = nib.load(ATLAS_DIR / f'perc_VTPM_vol_{roi_num}_lh.nii.gz')
        rh_img = nib.load(ATLAS_DIR / f'perc_VTPM_vol_{roi_num}_rh.nii.gz')
        combined = np.maximum(lh_img.get_fdata(), rh_img.get_fdata())
        atlas_img = nib.Nifti1Image(combined, lh_img.affine)

        for hemi in ['left', 'right']:
            tex = surface.vol_to_surf(
                atlas_img, fsaverage[f'pial_{hemi}'],
                inner_mesh=fsaverage[f'white_{hemi}'],
                interpolation='linear', radius=5.0,
            )
            labels = np.zeros_like(tex, dtype=np.int32)
            labels[tex > 10] = 1
            roi_labels[(roi, hemi)] = labels
    return roi_labels


# ============================================================================
# Main
# ============================================================================
def main():
    print("=" * 70)
    print("INFLATED POSTERIOR VIEW — RMS Activation (C010)")
    print("=" * 70)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fsaverage = datasets.fetch_surf_fsaverage('fsaverage5')
    roi_labels = get_roi_contour_labels(fsaverage)

    subjects_to_plot = [
        ('HC Mean (n=7)', None),
        ('Sub-08 (Deutan)', 'sub-08'),
        ('Sub-09 (Deutan)', 'sub-09'),
        ('Sub-10 (Protan)', 'sub-10'),
    ]

    surf_data = {}

    # HC group mean (project each subject, then average on surface)
    print("\nComputing HC group mean...")
    hc_textures = {'left': [], 'right': []}
    for hc_sub in HC_SUBJECTS:
        vals_per_roi = {}
        for roi in ROIS:
            amps = load_amplitudes(hc_sub, roi)  # (6, 8, n_voxels)
            rms = np.sqrt(np.mean(amps.mean(axis=0) ** 2, axis=0))
            vals_per_roi[roi] = rms
        brain_img = create_combined_volume(hc_sub, ROIS, vals_per_roi)
        for hemi in ['left', 'right']:
            hc_textures[hemi].append(project_to_surface(brain_img, fsaverage, hemi))
        print(f"  {hc_sub}: V1={len(vals_per_roi['V1'])} V2={len(vals_per_roi['V2'])}")

    for hemi in ['left', 'right']:
        surf_data[('HC Mean (n=7)', hemi)] = np.nanmean(hc_textures[hemi], axis=0)

    # CVD individuals
    for label, subject in subjects_to_plot[1:]:
        vals_per_roi = {}
        for roi in ROIS:
            amps = load_amplitudes(subject, roi)
            rms = np.sqrt(np.mean(amps.mean(axis=0) ** 2, axis=0))
            vals_per_roi[roi] = rms
        brain_img = create_combined_volume(subject, ROIS, vals_per_roi)
        for hemi in ['left', 'right']:
            surf_data[(label, hemi)] = project_to_surface(brain_img, fsaverage, hemi)
        print(f"  {subject}: V1={len(vals_per_roi['V1'])} V2={len(vals_per_roi['V2'])}")

    # Shared colorscale
    all_vals = np.concatenate([t[np.isfinite(t) & (t > 0)] for t in surf_data.values()])
    vmin = np.percentile(all_vals, 5)
    vmax = np.percentile(all_vals, 95)
    print(f"  Colorscale: [{vmin:.4f}, {vmax:.4f}]")

    # ---- Plot ----
    n_rows = len(subjects_to_plot)
    fig, axes = plt.subplots(n_rows, 2, figsize=(10, n_rows * 3.5),
                             subplot_kw={'projection': '3d'})

    for row, (label, _) in enumerate(subjects_to_plot):
        for col, hemi in enumerate(['left', 'right']):
            ax = axes[row, col]
            tex = surf_data[(label, hemi)]
            mesh = fsaverage[f'infl_{hemi}']
            bg = fsaverage[f'sulc_{hemi}']

            plotting.plot_surf_stat_map(
                mesh, tex, hemi=hemi, view='posterior',
                bg_map=bg, bg_on_data=True, darkness=0.5,
                cmap='hot', vmin=vmin, vmax=vmax,
                colorbar=False, threshold=vmin, axes=ax,
            )

            for roi in ROIS:
                labels = roi_labels[(roi, hemi)]
                if np.any(labels > 0):
                    try:
                        plotting.plot_surf_contours(
                            mesh, labels, hemi=hemi, view='posterior',
                            levels=[1], colors=[ROI_COLORS[roi]],
                            linewidths=2.5, figure=fig, axes=ax,
                        )
                    except Exception:
                        pass

            if row == 0:
                ax.set_title(f'{"Left" if hemi == "left" else "Right"} Hemisphere',
                             fontsize=13, fontweight='bold', pad=8)

        axes[row, 0].text2D(-0.05, 0.5, label,
                            transform=axes[row, 0].transAxes,
                            fontsize=10, fontweight='bold',
                            va='center', ha='right', rotation=90)

    fig.suptitle('Visual Cortex Color Activation (V1 + V2)\nC010 Procrustes — Posterior View',
                 fontsize=14, fontweight='bold', y=1.02)

    # Colorbar
    sm = plt.cm.ScalarMappable(cmap='hot', norm=plt.Normalize(vmin=vmin, vmax=vmax))
    sm.set_array([])
    cbar_ax = fig.add_axes([0.92, 0.25, 0.015, 0.5])
    cbar = fig.colorbar(sm, cax=cbar_ax)
    cbar.set_label('RMS Activation', fontsize=10)

    # Legend
    legend_elements = [
        Line2D([0], [0], color=ROI_COLORS['V1'], linewidth=2.5, label='V1'),
        Line2D([0], [0], color=ROI_COLORS['V2'], linewidth=2.5, label='V2'),
    ]
    fig.legend(handles=legend_elements, loc='lower center', ncol=2,
               fontsize=10, bbox_to_anchor=(0.45, -0.02),
               frameon=True, fancybox=True)

    plt.subplots_adjust(wspace=0.02, hspace=0.15)
    out_path = OUTPUT_DIR / 'FigA_rms_activation_posterior.png'
    fig.savefig(out_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f"\nSaved: {out_path} ({out_path.stat().st_size / 1024:.0f} KB)")


if __name__ == '__main__':
    main()
