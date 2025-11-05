#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
systematic_testing.py
---------------------
Systematic testing framework to find optimal analysis settings

Tests combinations of:
- HRF models
- ROI strategies
- Voxel selection methods
- Normalization approaches
- Confound strategies
"""

import os
import time
import json
import numpy as np
import pandas as pd
import nibabel as nib
from nilearn.glm.first_level import FirstLevelModel
from nilearn import image
from nilearn.maskers import NiftiMasker
from nilearn.interfaces.fmriprep import load_confounds_strategy
from sklearn.decomposition import PCA
from config import cfg


class SystematicTester:
    """Test different analysis parameter combinations"""

    def __init__(self, config=cfg):
        self.config = config
        self.test_results = []

    def run_test_battery(self, test_configs):
        """Run multiple test configurations"""
        print("\n=== Starting Systematic Test Battery ===")
        print(f"Number of configurations to test: {len(test_configs)}\n")

        for idx, test_config in enumerate(test_configs):
            print(f"\n{'='*60}")
            print(f"Test {idx+1}/{len(test_configs)}")
            print(f"Config: {test_config}")
            print(f"{'='*60}")

            try:
                result = self.run_single_test(**test_config)
                result['config'] = test_config
                self.test_results.append(result)

                print(f"\nResult: Classification={result.get('classification_acc', 'N/A'):.3f}, "
                      f"Reconstruction={result.get('reconstruction_hit', 'N/A'):.3f}")

            except Exception as e:
                print(f"ERROR in test {idx+1}: {e}")
                self.test_results.append({
                    'config': test_config,
                    'error': str(e)
                })

        self.save_results()
        self.print_summary()

    def run_single_test(self,
                        hrf_model='glover + derivative',
                        roi_name='BrainMask',
                        n_voxels=5000,
                        normalization='zscore',
                        confound_strategy='compcor',
                        use_pca=False,
                        pca_components=None):
        """Run single test with specified parameters"""

        start_time = time.time()

        # 1. Load and prepare data
        print("\n1. Loading data...")
        func_imgs = [nib.load(self.config.get_func_img_path(run))
                     for run in range(1, self.config.N_RUNS + 1)]

        events_list = [pd.read_csv(self.config.get_event_file_path(run), sep='\t')
                       for run in range(1, self.config.N_RUNS + 1)]

        # 2. Load ROI mask
        print(f"2. Loading ROI: {roi_name}")
        mask_img = self._load_roi_mask(roi_name)

        # 3. Fit GLM per run
        print(f"3. Fitting GLM with HRF model: {hrf_model}")
        betas_per_run = []

        for run_idx, (func_img, events) in enumerate(zip(func_imgs, events_list)):
            print(f"   Run {run_idx + 1}/{self.config.N_RUNS}...")

            # Filter events to color conditions only
            events = events[events['trial_type'].str.startswith('color_')].copy()

            # Load confounds
            confounds = self._load_confounds(run_idx + 1, confound_strategy)

            # Fit GLM
            try:
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

                glm.fit(func_img, events=events, confounds=confounds)

            except Exception as e:
                print(f"   Error fitting GLM: {e}")
                return {'error': f'GLM fitting failed: {e}'}

            # Extract betas for each color
            run_betas = []
            for color_idx in range(1, self.config.N_COLORS + 1):
                try:
                    # Get base regressor name
                    if hrf_model == 'fir':
                        # For FIR, use the first delay
                        contrast_name = f'color_{color_idx}_delay_0'
                    else:
                        contrast_name = f'color_{color_idx}'

                    beta_map = glm.compute_contrast(contrast_name, output_type='effect_size')

                    # Apply mask and extract
                    masker = NiftiMasker(mask_img=mask_img, standardize=False)
                    beta_vec = masker.fit_transform(beta_map).ravel()
                    run_betas.append(beta_vec)

                except Exception as e:
                    print(f"   Warning: Could not extract beta for color_{color_idx}: {e}")
                    # Use zeros if extraction fails
                    n_vox = np.sum(mask_img.get_fdata() > 0)
                    run_betas.append(np.zeros(n_vox))

            betas_per_run.append(np.array(run_betas))  # (n_colors, n_voxels)

        # Stack into (n_runs, n_colors, n_voxels)
        betas = np.stack(betas_per_run, axis=0)
        print(f"   Beta array shape: {betas.shape}")

        # 4. Voxel selection
        print(f"4. Selecting voxels (n={n_voxels})...")
        betas = self._select_voxels(betas, n_voxels)
        print(f"   Selected beta shape: {betas.shape}")

        # 5. Normalization
        if normalization:
            print(f"5. Applying normalization: {normalization}")
            betas = self._apply_normalization(betas, normalization)

        # 6. Optional PCA
        if use_pca and pca_components:
            print(f"6. Applying PCA (n_components={pca_components})...")
            betas = self._apply_pca(betas, pca_components)

        # 7. Classification
        print("7. Running classification...")
        class_acc = self._run_classification(betas)

        # 8. Reconstruction
        print("8. Running reconstruction...")
        recon_hit, recon_mae = self._run_reconstruction(betas)

        elapsed = time.time() - start_time
        print(f"\nTest completed in {elapsed:.1f}s")

        return {
            'classification_acc': class_acc,
            'reconstruction_hit': recon_hit,
            'reconstruction_mae': recon_mae,
            'n_voxels_final': betas.shape[2],
            'elapsed_time': elapsed
        }

    def _load_roi_mask(self, roi_name):
        """Load ROI mask"""
        mask_path = os.path.join(
            self.config.roi_dir,
            f'sub-{self.config.SUB_ID}_{roi_name}_mask.nii.gz'
        )

        if not os.path.exists(mask_path):
            raise FileNotFoundError(f"ROI mask not found: {mask_path}")

        return nib.load(mask_path)

    def _load_confounds(self, run, strategy):
        """Load confounds based on strategy"""
        func_path = self.config.get_func_img_path(run)

        if strategy == 'minimal':
            # Load confound file and extract motion only
            confound_path = self.config.get_confound_file_path(run)
            conf_df = pd.read_csv(confound_path, sep='\t')
            return conf_df[['trans_x', 'trans_y', 'trans_z', 'rot_x', 'rot_y', 'rot_z']]

        elif strategy in ['compcor', 'simple', 'ica_aroma']:
            conf_df, _ = load_confounds_strategy(func_path, strategy=[strategy])
            return conf_df

        else:
            return None

    def _select_voxels(self, betas, n_voxels):
        """Select top n voxels by activity"""
        # betas: (n_runs, n_colors, n_voxels)
        # Score each voxel by mean absolute response
        scores = np.abs(betas).mean(axis=(0, 1))  # (n_voxels,)

        if n_voxels >= len(scores):
            return betas

        top_idx = np.argsort(scores)[::-1][:n_voxels]
        return betas[:, :, top_idx]

    def _apply_normalization(self, betas, method):
        """Apply normalization"""
        # betas: (n_runs, n_colors, n_voxels)

        if method == 'zscore':
            # Z-score per voxel per run across colors
            normalized = np.zeros_like(betas)
            for run in range(betas.shape[0]):
                for vox in range(betas.shape[2]):
                    vals = betas[run, :, vox]
                    mu = vals.mean()
                    sd = vals.std(ddof=1)
                    if sd > 0:
                        normalized[run, :, vox] = (vals - mu) / sd
                    else:
                        normalized[run, :, vox] = vals - mu
            return normalized

        elif method == 'demean':
            # Remove mean per voxel per run
            return betas - betas.mean(axis=1, keepdims=True)

        elif method == 'none':
            return betas

        else:
            raise ValueError(f"Unknown normalization: {method}")

    def _apply_pca(self, betas, n_components):
        """Apply PCA dimensionality reduction"""
        # betas: (n_runs, n_colors, n_voxels)
        n_runs, n_colors, n_voxels = betas.shape

        if n_components >= n_voxels:
            return betas

        # Reshape to (n_runs * n_colors, n_voxels)
        data_2d = betas.reshape(-1, n_voxels)

        pca = PCA(n_components=n_components)
        data_pca = pca.fit_transform(data_2d)

        # Reshape back
        return data_pca.reshape(n_runs, n_colors, -1)

    def _run_classification(self, betas):
        """Run LOAO classification"""
        # betas: (n_runs, n_colors, n_features)
        n_runs, n_colors, n_features = betas.shape

        if n_runs < 2:
            return np.nan

        accuracies = []

        for test_run in range(n_runs):
            # Split data
            train_mask = np.ones(n_runs, dtype=bool)
            train_mask[test_run] = False

            train_X = betas[train_mask].reshape(-1, n_features)
            train_y = np.tile(np.arange(n_colors), train_mask.sum())

            test_X = betas[test_run]
            test_y = np.arange(n_colors)

            # Simple nearest-centroid classifier
            centroids = np.stack([train_X[train_y == c].mean(axis=0) for c in range(n_colors)])

            dists = np.stack([np.linalg.norm(test_X - centroids[c], axis=1) for c in range(n_colors)])
            preds = dists.argmin(axis=0)

            acc = (preds == test_y).mean()
            accuracies.append(acc)

        return np.mean(accuracies)

    def _run_reconstruction(self, betas):
        """Run forward model reconstruction"""
        # betas: (n_runs, n_colors, n_features)
        n_runs, n_colors, n_features = betas.shape

        if n_runs < 2:
            return np.nan, np.nan

        # Channel basis
        hue_table = self._channel_basis(num_channels=6, num_hues=360)

        # Color to hue mapping (uniform spacing)
        step = 360.0 / n_colors
        color_hues = np.arange(n_colors) * step

        hits = []
        maes = []

        for test_run in range(n_runs):
            # Split data
            train_mask = np.ones(n_runs, dtype=bool)
            train_mask[test_run] = False

            train_B = betas[train_mask].reshape(-1, n_features)  # (n_train, n_features)
            train_labels = np.tile(np.arange(n_colors), train_mask.sum())

            test_B = betas[test_run]  # (n_colors, n_features)

            # Forward model
            preds_hue = self._forward_model_predict(train_B, train_labels, test_B, hue_table)

            # Evaluate
            diffs = self._circular_diff(preds_hue, color_hues)
            hit = (diffs <= 22.5).mean()  # Within 22.5 degrees
            mae = diffs.mean()

            hits.append(hit)
            maes.append(mae)

        return np.mean(hits), np.mean(maes)

    @staticmethod
    def _channel_basis(num_channels=6, num_hues=360):
        """Six-channel encoding model basis"""
        hs = np.deg2rad(np.arange(num_hues))
        centers = np.deg2rad(np.linspace(0, 360, num_channels, endpoint=False))
        channels = []
        for c in centers:
            t = np.cos(hs - c)
            t = np.clip(t, 0, None)
            channels.append(t ** 2)
        return np.array(channels)  # (6, 360)

    def _forward_model_predict(self, train_B, train_labels, test_B, hue_table, lam=1e-2):
        """Forward encoding model prediction"""
        # Map labels to hue indices
        step = 360.0 / self.config.N_COLORS
        train_hue_idx = np.mod((train_labels * step).astype(int), 360)

        C1 = hue_table[:, train_hue_idx]  # (k, n_train)
        B1 = train_B.T  # (n_features, n_train)
        k = C1.shape[0]

        # Estimate weights
        W = (B1 @ C1.T) @ np.linalg.pinv(C1 @ C1.T + lam * np.eye(k))

        # Predict
        B2 = test_B.T  # (n_features, n_test)
        C_hat = np.linalg.pinv(W.T @ W + lam * np.eye(k)) @ (W.T @ B2)

        # Match to hues
        C_hat_norm = C_hat / (np.linalg.norm(C_hat, axis=0, keepdims=True) + 1e-8)
        hue_norm = hue_table / (np.linalg.norm(hue_table, axis=0, keepdims=True) + 1e-8)
        sims = C_hat_norm.T @ hue_norm
        hues_pred = sims.argmax(axis=1)

        return hues_pred.astype(float)

    @staticmethod
    def _circular_diff(a, b):
        """Circular difference in degrees"""
        d = np.abs(a - b) % 360.0
        return np.minimum(d, 360.0 - d)

    def save_results(self):
        """Save test results"""
        output_path = os.path.join(self.config.analysis_dir, 'systematic_test_results.json')

        # Convert numpy types to Python types for JSON serialization
        results_serializable = []
        for result in self.test_results:
            r = {}
            for key, val in result.items():
                if isinstance(val, (np.integer, np.floating)):
                    r[key] = float(val)
                elif isinstance(val, np.ndarray):
                    r[key] = val.tolist()
                else:
                    r[key] = val
            results_serializable.append(r)

        with open(output_path, 'w') as f:
            json.dump(results_serializable, f, indent=2)

        print(f"\nResults saved: {output_path}")

    def print_summary(self):
        """Print summary of all tests"""
        print("\n" + "="*60)
        print("SUMMARY OF ALL TESTS")
        print("="*60)

        if not self.test_results:
            print("No results to summarize")
            return

        # Sort by classification accuracy
        sorted_results = sorted(
            [r for r in self.test_results if 'error' not in r],
            key=lambda x: x.get('classification_acc', 0),
            reverse=True
        )

        print("\nTop 5 configurations by classification accuracy:")
        for i, result in enumerate(sorted_results[:5]):
            print(f"\n{i+1}. Classification: {result['classification_acc']:.3f}, "
                  f"Reconstruction: {result['reconstruction_hit']:.3f}")
            print(f"   Config: {result['config']}")

        # Sort by reconstruction hit rate
        sorted_results = sorted(
            [r for r in self.test_results if 'error' not in r],
            key=lambda x: x.get('reconstruction_hit', 0),
            reverse=True
        )

        print("\nTop 5 configurations by reconstruction hit rate:")
        for i, result in enumerate(sorted_results[:5]):
            print(f"\n{i+1}. Reconstruction: {result['reconstruction_hit']:.3f}, "
                  f"Classification: {result['classification_acc']:.3f}")
            print(f"   Config: {result['config']}")


def generate_test_configs():
    """Generate test configurations to try"""

    configs = []

    # Test 1: Baseline (like naive_analysis)
    configs.append({
        'hrf_model': 'glover + derivative',
        'roi_name': 'BrainMask',
        'n_voxels': 5000,
        'normalization': 'zscore',
        'confound_strategy': 'compcor'
    })

    # Test 2: Different HRF models
    for hrf in ['glover', 'spm', 'fir']:
        configs.append({
            'hrf_model': hrf,
            'roi_name': 'BrainMask',
            'n_voxels': 5000,
            'normalization': 'zscore',
            'confound_strategy': 'compcor'
        })

    # Test 3: Different ROIs
    for roi in ['V1', 'V2', 'V3', 'hV4']:
        configs.append({
            'hrf_model': 'glover + derivative',
            'roi_name': roi,
            'n_voxels': 5000,
            'normalization': 'zscore',
            'confound_strategy': 'compcor'
        })

    # Test 4: Different voxel counts
    for n_vox in [1000, 2000, 10000]:
        configs.append({
            'hrf_model': 'glover + derivative',
            'roi_name': 'BrainMask',
            'n_voxels': n_vox,
            'normalization': 'zscore',
            'confound_strategy': 'compcor'
        })

    # Test 5: Different normalizations
    for norm in ['demean', 'none']:
        configs.append({
            'hrf_model': 'glover + derivative',
            'roi_name': 'BrainMask',
            'n_voxels': 5000,
            'normalization': norm,
            'confound_strategy': 'compcor'
        })

    # Test 6: Different confound strategies
    for conf in ['simple', 'minimal']:
        configs.append({
            'hrf_model': 'glover + derivative',
            'roi_name': 'BrainMask',
            'n_voxels': 5000,
            'normalization': 'zscore',
            'confound_strategy': conf
        })

    return configs


def main():
    """Run systematic testing"""
    print("Generating test configurations...")
    test_configs = generate_test_configs()

    print(f"Total configurations to test: {len(test_configs)}")

    tester = SystematicTester()
    tester.run_test_battery(test_configs)


if __name__ == '__main__':
    main()
