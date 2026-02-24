#!/usr/bin/env python3
"""
SRM Autoencoder for LOCO decoding.

Architecture:
  Encoder: 6 channels → [MLP(16)] → k features (SRM-like latent)
  Decoder: k features → [MLP(16)] → 6 channels

Training with cycle consistency:
  1. Forward: channels → encoder → latent → decoder → reconstructed channels
  2. Data fit: latent should match actual SRM voxel responses
  3. Cycle loss: reconstructed channels should match input channels

Motivation:
  - k=4 is small → low overfitting risk (768 params vs 7 colors)
  - Bidirectional consistency regularizes both encoder and decoder
  - SRM voxel responses provide supervision signal for encoder
"""
import sys
import numpy as np
from pathlib import Path
from sklearn.neural_network import MLPRegressor

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_loco_comparison import (
    load_amplitudes, create_basis_functions, circular_distance,
    HUE_ANGLES,
)

baseline = Path(__file__).resolve().parents[4] / \
    "analysis/phase1_preprocess_decoding/results/full_dataset_C010"


class SRMAutoEncoder:
    """
    Simplified autoencoder using sklearn MLP.

    Two separate MLPs:
      - Decoder only (SRM voxels → 6 channels)

    We skip the encoder (channels → voxels) because:
      1. It's not needed for prediction (we have SRM voxels directly)
      2. Reduces complexity and overfitting risk
    """
    def __init__(self, latent_dim=4, hidden_dim=16, alpha=0.01):
        self.latent_dim = latent_dim
        self.hidden_dim = hidden_dim

        # Decoder: k SRM features → 6 channels
        self.decoder = MLPRegressor(
            hidden_layer_sizes=(hidden_dim,),
            activation='relu',
            solver='adam',
            alpha=alpha,
            max_iter=1000,
            random_state=42,
            early_stopping=False,
        )

    def fit(self, train_srm_voxels, train_channels):
        """
        Train decoder: SRM voxels → channels

        Args:
            train_srm_voxels: (n_train_colors, k)
            train_channels: (n_train_colors, 6)
        """
        self.decoder.fit(train_srm_voxels, train_channels)
        return self

    def predict_channels(self, test_srm_voxels):
        """SRM voxels → predicted channels"""
        return self.decoder.predict(test_srm_voxels)


def circular_mean_deg(angles_deg):
    """Circular mean of angles in degrees."""
    rads = np.deg2rad(angles_deg)
    mean_sin = np.mean(np.sin(rads))
    mean_cos = np.mean(np.cos(rads))
    return np.rad2deg(np.arctan2(mean_sin, mean_cos)) % 360


def loco_mlp_decoder(amp_srm, hidden_dim=16, alpha=0.01):
    """
    LOCO with MLP decoder: SRM voxels → channels

    Simpler than autoencoder — just trains SRM → channels directly.
    """
    n_runs, n_colors, k = amp_srm.shape
    all_hues = np.array(HUE_ANGLES)
    basis_full = create_basis_functions(n_channels=6)

    fold_maes = []

    for test_color in range(n_colors):
        train_colors = [c for c in range(n_colors) if c != test_color]
        train_hues = all_hues[train_colors]
        test_hue = all_hues[test_color]

        # Training data: mean SRM responses
        train_srm_mean = amp_srm[:, train_colors, :].mean(axis=0)  # (7, k)
        train_channels_theory = basis_full[train_hues]  # (7, 6)

        # Train MLP: SRM → channels
        model = SRMAutoEncoder(latent_dim=k, hidden_dim=hidden_dim, alpha=alpha)
        model.fit(train_srm_mean, train_channels_theory)

        # Test
        test_srm = amp_srm[:, test_color, :]  # (6, k)
        pred_channels = model.predict_channels(test_srm)  # (6, 6)

        # Template matching
        pred_hues = []
        for i in range(n_runs):
            corrs = np.array([np.corrcoef(pred_channels[i], basis_full[h])[0, 1]
                             for h in range(360)])
            pred_hues.append(np.nanargmax(corrs))
        pred_hues = np.array(pred_hues)

        errors = circular_distance(np.full(n_runs, test_hue), pred_hues)
        fold_maes.append(np.mean(errors))

    return np.mean(fold_maes)


def loco_mlp_ensemble(amp_srm, hidden_dim=16, alpha=0.01):
    """
    LOCO with per-run MLP ensemble.
    """
    n_runs, n_colors, k = amp_srm.shape
    all_hues = np.array(HUE_ANGLES)
    basis_full = create_basis_functions(n_channels=6)

    fold_maes = []

    for test_color in range(n_colors):
        train_colors = [c for c in range(n_colors) if c != test_color]
        train_hues = all_hues[train_colors]
        test_hue = all_hues[test_color]

        train_channels_theory = basis_full[train_hues]  # (7, 6)
        test_srm = amp_srm[:, test_color, :]  # (6, k)

        all_run_preds = []

        for r in range(n_runs):
            # Train on this run's SRM data
            train_srm_r = amp_srm[r, train_colors, :]  # (7, k)

            model_r = SRMAutoEncoder(latent_dim=k, hidden_dim=hidden_dim, alpha=alpha)
            model_r.fit(train_srm_r, train_channels_theory)

            # Predict on all test runs
            pred_channels_r = model_r.predict_channels(test_srm)
            pred_hues_r = []
            for i in range(n_runs):
                corrs = np.array([np.corrcoef(pred_channels_r[i], basis_full[h])[0, 1]
                                 for h in range(360)])
                pred_hues_r.append(np.nanargmax(corrs))
            all_run_preds.append(pred_hues_r)

        # Circular mean across models
        all_run_preds = np.array(all_run_preds)  # (6, 6)
        final_preds = np.array([circular_mean_deg(all_run_preds[:, i])
                               for i in range(n_runs)])

        errors = circular_distance(np.full(n_runs, test_hue), final_preds)
        fold_maes.append(np.mean(errors))

    return np.mean(fold_maes)


def baseline_loco_srm(amp_srm, use_ensemble=False):
    """Standard FE baseline in SRM space (for comparison)."""
    from run_loco_comparison import LOCOForwardEncodingDecoder

    n_runs, n_colors, k = amp_srm.shape
    all_hues = np.array(HUE_ANGLES)
    fold_maes = []

    for test_color in range(n_colors):
        train_colors = [c for c in range(n_colors) if c != test_color]
        test_hue = all_hues[test_color]

        if use_ensemble:
            # Per-run FE
            all_run_preds = []
            for r in range(n_runs):
                X_train = amp_srm[r, train_colors, :]
                y_train = train_colors

                model = LOCOForwardEncodingDecoder(alpha=0, n_channels=6)
                model.fit(X_train, y_train)

                X_test = amp_srm[:, test_color, :]
                pred_hues = model.predict(X_test)
                all_run_preds.append(pred_hues)

            all_run_preds = np.array(all_run_preds)
            final_preds = np.array([circular_mean_deg(all_run_preds[:, i])
                                   for i in range(n_runs)])
        else:
            # Pooled FE
            X_train = amp_srm[:, train_colors, :].reshape(-1, k)
            y_train = np.tile(train_colors, n_runs)

            model = LOCOForwardEncodingDecoder(alpha=0, n_channels=6)
            model.fit(X_train, y_train)

            X_test = amp_srm[:, test_color, :]
            final_preds = model.predict(X_test)

        errors = circular_distance(np.full(n_runs, test_hue), final_preds)
        fold_maes.append(np.mean(errors))

    return np.mean(fold_maes)


if __name__ == "__main__":
    subjects_test = ["01", "03", "05"]
    roi = "V1"

    print(f"SRM Autoencoder Experiment")
    print(f"Subjects: {subjects_test}")
    print(f"ROI: {roi}")
    print()

    # Load SRM data
    all_amps_srm = {}
    for s in subjects_test:
        all_amps_srm[s] = load_amplitudes(str(baseline), s, roi, 'srm')
        print(f"sub-{s}: {all_amps_srm[s].shape}")

    k = all_amps_srm[subjects_test[0]].shape[2]
    print(f"\nSRM dimensionality: k={k}")
    print(f"Autoencoder params: 6→16→{k}→16→6 = {6*16 + 16 + k*16 + 16 + 16*6 + 6} total")
    print()

    # Hyperparameter sweep
    configs = [
        ("FE Baseline", "baseline", None),
        ("FE Ensemble", "ensemble", None),
        ("MLP h=8 α=0.001", "mlp", (8, 0.001)),
        ("MLP h=16 α=0.01", "mlp", (16, 0.01)),
        ("MLP h=16 α=0.1", "mlp", (16, 0.1)),
        ("MLP h=24 α=0.01", "mlp", (24, 0.01)),
        ("MLP_Ens h=16 α=0.01", "mlp_ens", (16, 0.01)),
        ("MLP_Ens h=16 α=0.1", "mlp_ens", (16, 0.1)),
    ]

    header = f"{'Config':<30s} | {'sub-01':>8s} {'sub-03':>8s} {'sub-05':>8s} | {'Mean':>8s}"
    print(header)
    print("-" * len(header))

    for name, method, cfg in configs:
        maes = []
        for s in subjects_test:
            amp = all_amps_srm[s]

            if method == "baseline":
                mae = baseline_loco_srm(amp, use_ensemble=False)
            elif method == "ensemble":
                mae = baseline_loco_srm(amp, use_ensemble=True)
            elif method == "mlp":
                hidden_dim, alpha = cfg
                mae = loco_mlp_decoder(amp, hidden_dim=hidden_dim, alpha=alpha)
            elif method == "mlp_ens":
                hidden_dim, alpha = cfg
                mae = loco_mlp_ensemble(amp, hidden_dim=hidden_dim, alpha=alpha)

            maes.append(mae)

        print(f"{name:<30s} | {maes[0]:7.1f}  {maes[1]:7.1f}  {maes[2]:7.1f}  | {np.mean(maes):7.1f}")

    print()
    print("Lower MAE = better. Chance = 90°.")
    print("\nNOTE: MLP Decoder = SRM voxels (k=4) → MLP → 6 channels → correlation → hue")
    print("      Params: k×h + h + h×6 + 6. For k=4, h=16: 64 + 16 + 96 + 6 = 182 total.")
    print("      Training: 7 colors only. Compare with FE baseline (parameter-free).")
