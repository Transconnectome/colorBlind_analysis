#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
compare_forward_models.py
-------------------------
Compares B&H (2009) linear forward model with ML/DL alternatives

Usage:
    python compare_forward_models.py --roi V1 --models ridge mlp attention
"""

import os
import numpy as np
import argparse
import pickle
import matplotlib.pyplot as plt
from ml_forward_model import (
    RidgeForwardModel, RidgeCVForwardModel,
    MLPForwardModel, CNNForwardModel, AttentionForwardModel,
    compare_models, plot_model_comparison,
    TORCH_AVAILABLE
)
from config import cfg


def load_roi_data(roi_name='V1', config=cfg):
    """
    Load ROI voxel responses from B&H pipeline

    Returns
    -------
    voxels : ndarray (n_runs * n_colors, n_voxels)
        Voxel responses (beta estimates)
    """
    # Try per-run format first
    roi_file = os.path.join(
        config.analysis_dir,
        f'{roi_name}_responses_perrun.npy'
    )

    if os.path.exists(roi_file):
        data = np.load(roi_file)  # (n_runs * n_colors, n_voxels)
        print(f"Loaded ROI data: {roi_file}")
        print(f"  Shape: {data.shape}")
        return data
    else:
        print(f"ROI data not found: {roi_file}")
        return None


def generate_channel_responses(n_colors=8, n_channels=6):
    """
    Generate idealized channel responses for each color
    (Same as B&H 2009 - half-wave rectified & squared sinusoids)

    Returns
    -------
    channels : ndarray (n_colors, n_channels)
        Channel responses for each color
    """
    angles = np.linspace(0, 360, n_colors, endpoint=False)  # Color angles
    channel_centers = np.linspace(0, 360, n_channels, endpoint=False)

    channels = np.zeros((n_colors, n_channels))

    for i, angle in enumerate(angles):
        for j, center in enumerate(channel_centers):
            # Circular distance
            diff = np.abs(angle - center)
            if diff > 180:
                diff = 360 - diff

            # Half-wave rectified cosine, squared
            response = np.cos(np.deg2rad(diff))
            if response > 0:
                channels[i, j] = response ** 2

    # Normalize
    channels = channels / channels.sum(axis=1, keepdims=True)

    return channels


def prepare_data(roi_name='V1', n_runs=6, config=cfg):
    """
    Prepare voxel and channel data for model training

    Returns
    -------
    voxels : ndarray (n_total_samples, n_voxels)
    channels : ndarray (n_total_samples, n_channels)
    """
    # Load voxel data
    voxels = load_roi_data(roi_name, config)
    if voxels is None:
        return None, None

    # Generate channel responses
    channel_template = generate_channel_responses(
        n_colors=config.N_COLORS,
        n_channels=6
    )

    # Tile across runs
    channels = np.tile(channel_template, (n_runs, 1))

    print(f"\nData prepared:")
    print(f"  Voxels: {voxels.shape}")
    print(f"  Channels: {channels.shape}")

    return voxels, channels


def run_comparison(roi_name='V1', models_to_test=None, save_dir=None):
    """
    Run complete model comparison

    Parameters
    ----------
    roi_name : str
        ROI name (e.g., 'V1', 'V2', 'BrainMask')
    models_to_test : list of str
        Model names to test (e.g., ['ridge', 'mlp', 'attention'])
    save_dir : str, optional
        Directory to save results
    """

    if save_dir is None:
        save_dir = cfg.analysis_dir
    os.makedirs(save_dir, exist_ok=True)

    # Prepare data
    print(f"\n{'='*60}")
    print(f"Comparing Forward Models for ROI: {roi_name}")
    print(f"{'='*60}")

    voxels, channels = prepare_data(roi_name, n_runs=cfg.N_RUNS, config=cfg)

    if voxels is None or channels is None:
        print(f"ERROR: Could not load data for {roi_name}")
        return None

    # Auto-detect GPU
    device = 'cpu'
    if TORCH_AVAILABLE:
        import torch
        if torch.cuda.is_available():
            device = 'cuda'
            print(f"\n🚀 GPU detected: {torch.cuda.get_device_name(0)}")
            print(f"   Using device: {device}")
        else:
            print(f"\n⚠️  No GPU detected, using CPU")

    # Define models
    all_models = {
        'Ridge (alpha=1.0)': (RidgeForwardModel, {'alpha': 1.0}),
        'Ridge (CV)': (RidgeCVForwardModel, {
            'alphas': np.logspace(-3, 3, 20)
        }),
    }

    if TORCH_AVAILABLE:
        all_models.update({
            'MLP (Small)': (MLPForwardModel, {
                'hidden_dims': [256, 128],
                'epochs': 100,
                'lr': 1e-3,
                'batch_size': 16,
                'dropout': 0.3,
                'device': device
            }),
            'MLP (Large)': (MLPForwardModel, {
                'hidden_dims': [512, 256, 128],
                'epochs': 100,
                'lr': 1e-3,
                'batch_size': 16,
                'dropout': 0.3,
                'device': device
            }),
            'CNN': (CNNForwardModel, {
                'conv_channels': [64, 128],
                'kernel_size': 5,
                'epochs': 100,
                'lr': 1e-3,
                'batch_size': 16,
                'device': device
            }),
            'Attention': (AttentionForwardModel, {
                'hidden_dim': 256,
                'n_heads': 8,
                'epochs': 100,
                'lr': 1e-3,
                'batch_size': 16,
                'device': device
            }),
        })
    else:
        print("\nWarning: PyTorch not available. Only testing Ridge models.")

    # Filter models if specified
    if models_to_test is not None:
        filtered = {}
        for key in all_models:
            model_type = key.split()[0].lower()
            if model_type in models_to_test:
                filtered[key] = all_models[key]
        all_models = filtered

    # Run comparison
    results = compare_models(all_models, voxels, channels, n_runs=cfg.N_RUNS)

    # Save results
    results_file = os.path.join(save_dir, f'{roi_name}_model_comparison.pkl')
    with open(results_file, 'wb') as f:
        pickle.dump(results, f)
    print(f"\nResults saved: {results_file}")

    # Plot comparison
    fig = plot_model_comparison(
        results,
        save_path=os.path.join(save_dir, f'{roi_name}_model_comparison.png')
    )
    plt.show()

    return results


def decode_colors(predictions, channel_template):
    """
    Decode predicted colors from channel responses

    Parameters
    ----------
    predictions : ndarray (n_samples, n_channels)
        Predicted channel responses
    channel_template : ndarray (n_colors, n_channels)
        Template channel responses for each color

    Returns
    -------
    decoded_colors : ndarray (n_samples,)
        Decoded color indices
    """
    # Compute correlation with each template
    n_samples = predictions.shape[0]
    n_colors = channel_template.shape[0]

    decoded = np.zeros(n_samples, dtype=int)

    for i in range(n_samples):
        # Correlate with all templates
        corrs = np.array([
            np.corrcoef(predictions[i], channel_template[c])[0, 1]
            for c in range(n_colors)
        ])
        decoded[i] = np.argmax(corrs)

    return decoded


def evaluate_decoding_accuracy(results, n_runs=6, n_colors=8):
    """
    Evaluate color decoding accuracy from model predictions

    Parameters
    ----------
    results : dict
        Results from compare_models()
    n_runs : int
        Number of runs
    n_colors : int
        Number of colors

    Returns
    -------
    accuracies : dict
        Decoding accuracies for each model
    """
    channel_template = generate_channel_responses(n_colors=n_colors, n_channels=6)
    true_labels = np.tile(np.arange(n_colors), n_runs)

    accuracies = {}

    for name, result in results.items():
        predictions = result['predictions']
        decoded = decode_colors(predictions, channel_template)

        accuracy = (decoded == true_labels).mean()
        accuracies[name] = accuracy

        print(f"{name:<30} Accuracy: {accuracy:.3f} ({accuracy*100:.1f}%)")

    return accuracies


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Compare forward encoding models (Linear vs ML/DL)'
    )
    parser.add_argument('--roi', type=str, default='V1',
                       help='ROI name (default: V1)')
    parser.add_argument('--models', nargs='+',
                       choices=['ridge', 'mlp', 'cnn', 'attention'],
                       default=None,
                       help='Models to test (default: all)')
    parser.add_argument('--save-dir', type=str, default=None,
                       help='Directory to save results (default: derivatives/sub-XX)')

    args = parser.parse_args()

    # Run comparison
    results = run_comparison(
        roi_name=args.roi,
        models_to_test=args.models,
        save_dir=args.save_dir
    )

    if results is not None:
        # Evaluate decoding accuracy
        print(f"\n{'='*60}")
        print("COLOR DECODING ACCURACY")
        print(f"{'='*60}")
        accuracies = evaluate_decoding_accuracy(
            results,
            n_runs=cfg.N_RUNS,
            n_colors=cfg.N_COLORS
        )

        # Best model
        best_model = max(accuracies.keys(), key=lambda k: accuracies[k])
        print(f"\n{'='*60}")
        print(f"BEST MODEL: {best_model}")
        print(f"Accuracy: {accuracies[best_model]:.3f}")
        print(f"R²: {results[best_model]['mean_r2']:.4f}")
        print(f"{'='*60}")


if __name__ == '__main__':
    main()
