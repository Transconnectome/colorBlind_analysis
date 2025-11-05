"""ROI mask construction utilities."""

import os
import time
from typing import Callable, Dict, Optional, Tuple

import nibabel as nib
import numpy as np
from nilearn import image


HEMISPHERES = ('lh', 'rh')

WANG_ROI_MAP = {
    'V1': ['perc_VTPM_vol_roi1_', 'perc_VTPM_vol_roi2_'],
    'V2': ['perc_VTPM_vol_roi3_', 'perc_VTPM_vol_roi4_'],
    'V3': ['perc_VTPM_vol_roi5_', 'perc_VTPM_vol_roi6_'],
    'hV4': ['perc_VTPM_vol_roi7_'],
}


def _emit(status: Optional[Callable[[str], None]], message: str) -> None:
    if status is None:
        print(message)
    else:
        status(message)


def _default_brain_mask_path(config) -> str:
    if hasattr(config, 'brain_mask_path') and config.brain_mask_path:
        return config.brain_mask_path
    return os.path.join(
        config.PROJECT_DIR,
        'output', 'pilot',
        f'sub-{config.SUB_ID}', 'anat',
        f'sub-{config.SUB_ID}_acq-mprage_space-MNI152NLin2009cAsym_res-2_desc-brain_mask.nii.gz'
    )


def _load_subject_mni_roi(config, roi_name: str, status=None) -> Tuple[Optional[nib.Nifti1Image], Optional[str]]:
    subj_anat_dir = os.path.join(
        config.PROJECT_DIR,
        'output', 'pilot',
        f'sub-{config.SUB_ID}', 'anat'
    )
    if not os.path.isdir(subj_anat_dir):
        _emit(status, f"[WARN] Subject anat directory not found for ROI {roi_name}: {subj_anat_dir}")
        return None, None

    roi_lower = roi_name.lower()
    candidates = []
    for fn in os.listdir(subj_anat_dir):
        low = fn.lower()
        if not low.endswith(('.nii', '.nii.gz')):
            continue
        if 'space-mni' not in low:
            continue
        if roi_lower not in low:
            continue
        candidates.append(os.path.join(subj_anat_dir, fn))

    if not candidates:
        return None, None

    candidates.sort()
    selected = candidates[0]
    try:
        return nib.load(selected), selected
    except Exception as exc:
        _emit(status, f"[WARN] Failed to load subject ROI {selected}: {exc}")
        return None, None


def build_wang_rois(config, *, status: Optional[Callable[[str], None]] = None,
                    skip_existing: bool = True) -> Dict[str, str]:
    """Build Wang atlas based ROI masks and optional subject intersections."""

    roi_dir = config.roi_dir
    os.makedirs(roi_dir, exist_ok=True)

    ref_img = nib.load(config.get_func_img_path(1))
    created: Dict[str, str] = {}

    brain_mask_path = _default_brain_mask_path(config)

    _emit(status, "[START] Building ROI masks (Wang atlas)")
    start = time.time()

    for roi_name, roi_parts in WANG_ROI_MAP.items():
        out_path = os.path.join(roi_dir, f'sub-{config.SUB_ID}_{roi_name}_mask.nii.gz')
        if skip_existing and os.path.exists(out_path):
            _emit(status, f"[SKIP] {roi_name} mask already present ({out_path})")
            continue

        roi_mask = None
        part_img = None
        for hemi in HEMISPHERES:
            for part in roi_parts:
                roi_file = os.path.join(
                    config.PROJECT_DIR,
                    'ProbAtlas_v4/subj_vol_all',
                    f'{part}{hemi}.nii.gz'
                )
                if not os.path.exists(roi_file):
                    _emit(status, f"[WARN] File not found: {roi_file}")
                    continue

                part_img = nib.load(roi_file)
                part_data = part_img.get_fdata()
                part_mask = part_data > 50

                roi_mask = part_mask if roi_mask is None else np.logical_or(roi_mask, part_mask)

        if roi_mask is None:
            _emit(status, f"[ERROR] Could not create mask for {roi_name}")
            continue

        roi_nii = nib.Nifti1Image(roi_mask.astype(np.int16), part_img.affine)
        roi_resampled = image.resample_img(
            roi_nii,
            target_affine=ref_img.affine,
            target_shape=ref_img.shape[:3],
            interpolation='nearest'
        )

        try:
            if os.path.exists(brain_mask_path):
                brain_img = nib.load(brain_mask_path)
                brain_resampled = image.resample_img(
                    brain_img,
                    target_affine=roi_resampled.affine,
                    target_shape=roi_resampled.shape[:3],
                    interpolation='nearest'
                )
                roi_bool = roi_resampled.get_fdata().astype(bool)
                brain_bool = brain_resampled.get_fdata().astype(bool)
                combined = np.logical_and(roi_bool, brain_bool).astype(np.int16)
                roi_resampled = nib.Nifti1Image(combined, roi_resampled.affine, roi_resampled.header)
                _emit(status, f"[OK] Applied brain_mask intersection for {roi_name}")
            else:
                _emit(status, f"[WARN] Brain mask not found at {brain_mask_path}; skipping intersection")
        except Exception as exc:
            _emit(status, f"[WARN] Could not apply brain mask intersection for {roi_name}: {exc}")

        subj_roi_img, subj_roi_path = _load_subject_mni_roi(config, roi_name, status)
        if subj_roi_img is not None:
            try:
                subj_resampled = image.resample_img(
                    subj_roi_img,
                    target_affine=roi_resampled.affine,
                    target_shape=roi_resampled.shape[:3],
                    interpolation='nearest'
                )
                atlas_bool = roi_resampled.get_fdata().astype(bool)
                subj_bool = subj_resampled.get_fdata().astype(bool)
                combined = np.logical_and(atlas_bool, subj_bool)
                if combined.any():
                    roi_resampled = nib.Nifti1Image(
                        combined.astype(np.int16),
                        roi_resampled.affine,
                        roi_resampled.header
                    )
                    _emit(status, f"[OK] Applied subject MNI ROI intersection for {roi_name} ({os.path.basename(subj_roi_path)})")
                else:
                    _emit(status, f"[WARN] Intersection empty for {roi_name}; retaining atlas-only mask")
            except Exception as exc:
                _emit(status, f"[WARN] Failed combining subject ROI for {roi_name}: {exc}")
        else:
            _emit(status, f"[INFO] No subject MNI ROI found for {roi_name}; using atlas mask only")

        roi_resampled.to_filename(out_path)
        created[roi_name] = out_path
        _emit(status, f"[OK] Created {roi_name} mask")

    _emit(status, f"[OK] ROI masks created in {time.time()-start:.1f}s")
    return created


def build_structural_rois(config, *, status: Optional[Callable[[str], None]] = None,
                          skip_existing: bool = True) -> Dict[str, str]:
    """Build subject-specific structural ROI masks in functional space."""

    roi_dir = config.roi_dir
    os.makedirs(roi_dir, exist_ok=True)

    subj_anat_dir = os.path.join(
        config.PROJECT_DIR,
        'output', 'pilot',
        f'sub-{config.SUB_ID}', 'anat'
    )

    if not os.path.isdir(subj_anat_dir):
        _emit(status, f"[WARN] Subject anat directory not found: {subj_anat_dir}")
        return {}

    candidates = sorted([
        os.path.join(subj_anat_dir, fn)
        for fn in os.listdir(subj_anat_dir)
        if fn.lower().endswith(('.nii', '.nii.gz')) and 'brain_mask' not in fn and 'probseg' not in fn
    ])

    if not candidates:
        _emit(status, f"[WARN] No structural ROI nifti files found in {subj_anat_dir}")
        return {}

    ref_img = nib.load(config.get_func_img_path(1))
    brain_mask_path = _default_brain_mask_path(config)
    start = time.time()
    _emit(status, f"[START] Building structural ROI masks from {subj_anat_dir}")

    created: Dict[str, str] = {}

    for cand in candidates:
        try:
            fname = os.path.basename(cand)
            stem = fname.replace('.nii.gz', '').replace('.nii', '')
            prefix = f'sub-{config.SUB_ID}_'
            stem2 = stem[len(prefix):] if stem.startswith(prefix) else stem
            stem2 = stem2.replace('_mask', '')
            roi_name = f"{stem2}_anat"

            out_path = os.path.join(roi_dir, f'sub-{config.SUB_ID}_{roi_name}_mask.nii.gz')
            if skip_existing and os.path.exists(out_path):
                _emit(status, f"[SKIP] {roi_name} already present ({out_path})")
                continue

            mask_img = nib.load(cand)
            mask_resampled = image.resample_img(
                mask_img,
                target_affine=ref_img.affine,
                target_shape=ref_img.shape[:3],
                interpolation='nearest'
            )

            try:
                if os.path.exists(brain_mask_path):
                    brain_img = nib.load(brain_mask_path)
                    brain_resampled = image.resample_img(
                        brain_img,
                        target_affine=mask_resampled.affine,
                        target_shape=mask_resampled.shape[:3],
                        interpolation='nearest'
                    )
                    roi_bool = mask_resampled.get_fdata().astype(bool)
                    brain_bool = brain_resampled.get_fdata().astype(bool)
                    combined = np.logical_and(roi_bool, brain_bool).astype(np.int16)
                    mask_resampled = nib.Nifti1Image(combined, mask_resampled.affine, mask_resampled.header)
                    _emit(status, f"[OK] Applied brain_mask intersection for {roi_name}")
                else:
                    _emit(status, f"[WARN] Brain mask not found at {brain_mask_path}; skipping intersection")
            except Exception as exc:
                _emit(status, f"[WARN] Could not apply brain mask intersection for {roi_name}: {exc}")

            mask_resampled.to_filename(out_path)
            created[roi_name] = out_path
            _emit(status, f"[OK] Created structural ROI {roi_name}")

        except Exception as exc:
            _emit(status, f"[WARN] Failed to process {cand}: {exc}")

    _emit(status, f"[OK] Structural ROI masks created in {time.time()-start:.1f}s")
    return created


def build_all_rois(config, *, status: Optional[Callable[[str], None]] = None,
                   skip_existing: bool = True) -> Dict[str, str]:
    """Convenience wrapper to build Wang and structural ROIs together."""

    results = {}
    results.update(build_wang_rois(config, status=status, skip_existing=skip_existing))
    results.update(build_structural_rois(config, status=status, skip_existing=skip_existing))
    return results


__all__ = [
    'build_wang_rois',
    'build_structural_rois',
    'build_all_rois',
]


if __name__ == '__main__':  # pragma: no cover
    try:
        from config import cfg
    except ImportError as exc:
        raise SystemExit(f"Failed to import config: {exc}")

    build_all_rois(cfg)
