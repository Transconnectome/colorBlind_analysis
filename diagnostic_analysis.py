#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
diagnostic_analysis.py
----------------------
Systematic comparison of analysis approaches to identify
what causes poor decoding performance in bh_anal.py

Test matrix:
1. HRF model: deconvolution vs standard (glover+deriv) vs FIR
2. ROI: whole brain vs V1-V4 segregated
3. Voxel selection: all vs top-k by |z|
4. Normalization: yes vs no
5. Confounds: minimal (motion) vs full (compcor)
"""

import os
import numpy as np
import pandas as pd
import nibabel as nib
from nilearn.glm.first_level import FirstLevelModel
from nilearn import image
from config import cfg

class DiagnosticPipeline:
    """Test different analysis settings systematically"""

    def __init__(self, config=cfg):
        self.config = config
        self.results = {}

    def compare_hrf_models(self, run=1):
        """Compare different HRF modeling approaches"""
        print("\n=== HRF Model Comparison ===")

        # Load data
        func_img = nib.load(self.config.get_func_img_path(run))
        events = pd.read_csv(self.config.get_event_file_path(run), sep='\t')

        hrf_models = ['glover', 'glover + derivative', 'spm', 'fir']
        results = {}

        for hrf_model in hrf_models:
            print(f"\nTesting HRF model: {hrf_model}")

            try:
                # Fit GLM
                if hrf_model == 'fir':
                    glm = FirstLevelModel(
                        t_r=self.config.TR,
                        hrf_model='fir',
                        fir_delays=range(10),
                        drift_model='cosine',
                        high_pass=1/128.0
                    )
                else:
                    glm = FirstLevelModel(
                        t_r=self.config.TR,
                        hrf_model=hrf_model,
                        drift_model='cosine',
                        high_pass=1/128.0
                    )

                glm.fit(func_img, events=events)

                # Get beta estimates for first color
                try:
                    beta = glm.compute_contrast('color_1', output_type='effect_size')
                    beta_data = beta.get_fdata()

                    # Compute signal quality metrics
                    mean_beta = np.nanmean(beta_data[beta_data != 0])
                    std_beta = np.nanstd(beta_data[beta_data != 0])
                    snr = abs(mean_beta) / (std_beta + 1e-8)

                    results[hrf_model] = {
                        'mean_beta': mean_beta,
                        'std_beta': std_beta,
                        'snr': snr,
                        'n_nonzero': np.sum(beta_data != 0)
                    }

                    print(f"  Mean beta: {mean_beta:.4f}")
                    print(f"  Std beta: {std_beta:.4f}")
                    print(f"  SNR: {snr:.4f}")

                except Exception as e:
                    print(f"  Error computing contrast: {e}")
                    results[hrf_model] = {'error': str(e)}

            except Exception as e:
                print(f"  Error fitting GLM: {e}")
                results[hrf_model] = {'error': str(e)}

        return results

    def check_roi_quality(self):
        """Check quality of ROI masks"""
        print("\n=== ROI Quality Check ===")

        roi_names = ['V1', 'V2', 'V3', 'hV4', 'BrainMask']
        results = {}

        # Load reference functional image
        ref_img = nib.load(self.config.get_func_img_path(1))
        ref_shape = ref_img.shape[:3]

        for roi_name in roi_names:
            mask_path = os.path.join(
                self.config.roi_dir,
                f'sub-{self.config.SUB_ID}_{roi_name}_mask.nii.gz'
            )

            if not os.path.exists(mask_path):
                print(f"\n{roi_name}: NOT FOUND")
                results[roi_name] = {'exists': False}
                continue

            # Load mask
            mask_img = nib.load(mask_path)
            mask_data = mask_img.get_fdata().astype(bool)

            # Check alignment
            if mask_img.shape != ref_shape:
                print(f"\n{roi_name}: SHAPE MISMATCH")
                print(f"  Mask shape: {mask_img.shape}")
                print(f"  Func shape: {ref_shape}")

                # Try resampling
                try:
                    resampled = image.resample_img(
                        mask_img,
                        target_affine=ref_img.affine,
                        target_shape=ref_shape,
                        interpolation='nearest'
                    )
                    mask_data = resampled.get_fdata().astype(bool)
                    print(f"  Resampled successfully")
                except Exception as e:
                    print(f"  Resampling failed: {e}")
                    results[roi_name] = {'error': str(e)}
                    continue

            n_voxels = np.sum(mask_data)
            print(f"\n{roi_name}:")
            print(f"  Shape: {mask_data.shape}")
            print(f"  N voxels: {n_voxels}")
            print(f"  Volume: {n_voxels * np.prod(ref_img.header.get_zooms()[:3]) / 1000:.2f} cm³")

            results[roi_name] = {
                'exists': True,
                'n_voxels': int(n_voxels),
                'shape': mask_data.shape,
                'aligned': mask_img.shape == ref_shape
            }

            # Check if mask overlaps with functional data
            func_data = ref_img.get_fdata()
            mean_signal = func_data.mean(axis=-1)
            overlap = np.sum(mask_data & (mean_signal > 0))
            print(f"  Overlap with non-zero voxels: {overlap} ({100*overlap/n_voxels:.1f}%)")
            results[roi_name]['overlap'] = int(overlap)

        return results

    def compare_beta_estimates(self):
        """Compare beta estimates from different methods"""
        print("\n=== Beta Estimate Comparison ===")

        # Method 1: Standard GLM (like naive_analysis)
        print("\nMethod 1: Standard GLM (glover + derivative)")
        betas_standard = self._get_betas_standard()

        # Method 2: Deconvolution (like bh_anal)
        print("\nMethod 2: Deconvolution approach")
        betas_deconv = self._get_betas_deconv()

        # Compare
        if betas_standard is not None and betas_deconv is not None:
            print("\nComparison:")
            print(f"  Standard - mean: {np.nanmean(betas_standard):.4f}, std: {np.nanstd(betas_standard):.4f}")
            print(f"  Deconv   - mean: {np.nanmean(betas_deconv):.4f}, std: {np.nanstd(betas_deconv):.4f}")

            # Correlation
            if betas_standard.shape == betas_deconv.shape:
                mask = ~(np.isnan(betas_standard) | np.isnan(betas_deconv))
                if np.sum(mask) > 0:
                    corr = np.corrcoef(betas_standard[mask].ravel(),
                                       betas_deconv[mask].ravel())[0, 1]
                    print(f"  Correlation: {corr:.4f}")

        return {'standard': betas_standard, 'deconv': betas_deconv}

    def _get_betas_standard(self):
        """Get betas using standard GLM"""
        try:
            func_img = nib.load(self.config.get_func_img_path(1))
            events = pd.read_csv(self.config.get_event_file_path(1), sep='\t')

            glm = FirstLevelModel(
                t_r=self.config.TR,
                hrf_model='glover + derivative',
                drift_model='cosine',
                high_pass=1/128.0
            ).fit(func_img, events=events)

            betas = []
            for i in range(1, 9):
                beta = glm.compute_contrast(f'color_{i}', output_type='effect_size')
                betas.append(beta.get_fdata())

            return np.stack(betas, axis=0)  # (8, x, y, z)

        except Exception as e:
            print(f"  Error: {e}")
            return None

    def _get_betas_deconv(self):
        """Get betas using deconvolution approach"""
        try:
            # Check if deconv results exist
            beta_path = os.path.join(
                self.config.analysis_dir,
                f'sub-{self.config.SUB_ID}_rsvp_deconv_betas_run-1.nii.gz'
            )

            if os.path.exists(beta_path):
                beta_img = nib.load(beta_path)
                return beta_img.get_fdata()  # (8, x, y, z)
            else:
                print(f"  Deconv betas not found: {beta_path}")
                return None

        except Exception as e:
            print(f"  Error: {e}")
            return None

    def test_voxel_selection_impact(self, k_values=[500, 1000, 2000, 5000, 10000]):
        """Test impact of voxel selection on decoding"""
        print("\n=== Voxel Selection Impact ===")

        # Load per-run betas
        roi_data = self._load_roi_responses('V1')  # or 'BrainMask'
        if roi_data is None:
            print("Could not load ROI data")
            return None

        results = {}
        n_voxels_total = roi_data.shape[1]
        print(f"\nTotal voxels available: {n_voxels_total}")

        for k in k_values:
            if k > n_voxels_total:
                print(f"\nSkipping k={k} (exceeds available voxels)")
                continue

            print(f"\nTesting with k={k} voxels")

            # Select top k voxels by variance or |mean|
            vox_scores = np.abs(roi_data).mean(axis=0)
            top_k_idx = np.argsort(vox_scores)[::-1][:k]
            roi_data_k = roi_data[:, top_k_idx]

            # Simple classification test (not full LOAO)
            acc = self._quick_classification_test(roi_data_k)
            results[k] = acc
            print(f"  Classification accuracy: {acc:.3f}")

        return results

    def _load_roi_responses(self, roi_name):
        """Load ROI response data"""
        # Try per-run first
        path = os.path.join(self.config.analysis_dir, f'{roi_name}_responses_perrun.npy')
        if os.path.exists(path):
            return np.load(path)

        # Try mean
        path = os.path.join(self.config.analysis_dir, f'{roi_name}_responses.npy')
        if os.path.exists(path):
            return np.load(path)

        return None

    def _quick_classification_test(self, data):
        """Quick classification test with simple train/test split"""
        n_samples, n_vox = data.shape
        n_colors = self.config.N_COLORS

        if n_samples % n_colors != 0:
            return np.nan

        n_runs = n_samples // n_colors
        if n_runs < 2:
            return np.nan

        # Reshape to (runs, colors, voxels)
        arr = data.reshape(n_runs, n_colors, n_vox)

        # Use first run as test, rest as train
        test_X = arr[0]
        train_X = arr[1:].reshape(-1, n_vox)

        test_y = np.arange(n_colors)
        train_y = np.tile(np.arange(n_colors), n_runs - 1)

        # Simple nearest-centroid classification
        centroids = np.stack([train_X[train_y == c].mean(axis=0) for c in range(n_colors)])

        # Predict
        dists = np.stack([np.linalg.norm(test_X - centroids[c], axis=1) for c in range(n_colors)])
        preds = dists.argmin(axis=0)

        return (preds == test_y).mean()

    def save_diagnostic_report(self, output_path=None):
        """Save comprehensive diagnostic report"""
        if output_path is None:
            output_path = os.path.join(self.config.analysis_dir, 'diagnostic_report.txt')

        with open(output_path, 'w') as f:
            f.write("=== ColorBlind Analysis Diagnostic Report ===\n\n")

            for key, val in self.results.items():
                f.write(f"\n{key}:\n")
                f.write(f"{val}\n")

        print(f"\nDiagnostic report saved: {output_path}")


def main():
    """Run all diagnostic tests"""
    pipeline = DiagnosticPipeline()

    # 1. HRF model comparison
    print("\n" + "="*60)
    hrf_results = pipeline.compare_hrf_models(run=1)
    pipeline.results['hrf_comparison'] = hrf_results

    # 2. ROI quality check
    print("\n" + "="*60)
    roi_results = pipeline.check_roi_quality()
    pipeline.results['roi_quality'] = roi_results

    # 3. Beta estimate comparison
    print("\n" + "="*60)
    beta_results = pipeline.compare_beta_estimates()
    # Don't save full arrays, just summary
    pipeline.results['beta_comparison'] = 'See console output'

    # 4. Voxel selection impact
    print("\n" + "="*60)
    voxel_results = pipeline.test_voxel_selection_impact()
    if voxel_results:
        pipeline.results['voxel_selection'] = voxel_results

    # Save report
    print("\n" + "="*60)
    pipeline.save_diagnostic_report()

    print("\n=== Diagnostic Analysis Complete ===")


if __name__ == '__main__':
    main()
