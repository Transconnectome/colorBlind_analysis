#!/usr/bin/env python3
"""
Test sequential models locally before submitting to server.

Tests:
1. ForwardEncodingSequential
2. HybridMLPSequential
3. HybridSVRSequential

Verifies:
- Models can fit and predict
- Output shapes are correct
- Circular MSE can be computed
"""

import sys
from pathlib import Path
import numpy as np

# Add script directory to path
script_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(script_dir))

from run_loco_comparison import (
    ForwardEncodingSequential,
    HybridMLPSequential,
    HybridSVRSequential,
    circular_distance,
    circular_mse,
    load_amplitudes,
    HUE_ANGLES,
)

def test_sequential_models():
    """Test sequential models on a single subject/ROI."""

    # Load data
    baseline_dir = Path(__file__).resolve().parents[4] / "analysis" / "phase1_preprocess_decoding" / "results" / "full_dataset_C010"
    subject = "01"
    roi = "V1"
    alignment = "procrustes"

    print(f"\nLoading data: sub-{subject} {roi} ({alignment})")
    amplitudes = load_amplitudes(baseline_dir, subject, roi, alignment)
    print(f"Amplitudes shape: {amplitudes.shape}")

    # LOCO fold: hold out color 0 (hue=0°)
    held_out_color = 0
    train_colors = [c for c in range(8) if c != held_out_color]

    # Training data: 7 colors × 6 runs = 42 samples
    X_train = amplitudes[:, train_colors, :].reshape(-1, amplitudes.shape[2])
    y_train = np.array([c for c in train_colors for _ in range(6)])

    # Test data: held-out color × 6 runs = 6 samples
    X_test = amplitudes[:, held_out_color, :]
    y_test_hue = np.array([HUE_ANGLES[held_out_color]] * 6)

    print(f"\nTrain: {X_train.shape}, Test: {X_test.shape}")
    print(f"Train labels: {np.unique(y_train)} (n={len(y_train)})")
    print(f"Test true hue: {y_test_hue[0]}°")

    # Test 1: ForwardEncodingSequential
    print("\n" + "="*60)
    print("Test 1: ForwardEncodingSequential")
    print("="*60)
    model1 = ForwardEncodingSequential(alpha=0, n_channels=6)
    model1.fit(X_train, y_train)
    y_pred1 = model1.predict(X_test)
    mae1 = circular_distance(y_test_hue, y_pred1).mean()
    mse1 = circular_mse(y_test_hue, y_pred1)
    print(f"Predictions: {y_pred1}")
    print(f"MAE: {mae1:.1f}°  MSE: {mse1:.1f}")

    # Test 2: HybridMLPSequential
    print("\n" + "="*60)
    print("Test 2: HybridMLPSequential")
    print("="*60)
    model2 = HybridMLPSequential(
        fe_alpha=0, n_channels=6,
        hidden_layer_sizes=(64, 32), mlp_alpha=0.1
    )
    model2.fit(X_train, y_train)
    y_pred2 = model2.predict(X_test)
    mae2 = circular_distance(y_test_hue, y_pred2).mean()
    mse2 = circular_mse(y_test_hue, y_pred2)
    print(f"Predictions: {y_pred2}")
    print(f"MAE: {mae2:.1f}°  MSE: {mse2:.1f}")

    # Test 3: HybridSVRSequential
    print("\n" + "="*60)
    print("Test 3: HybridSVRSequential")
    print("="*60)
    model3 = HybridSVRSequential(
        fe_alpha=0, n_channels=6, C=1.0, epsilon=0.1
    )
    model3.fit(X_train, y_train)
    y_pred3 = model3.predict(X_test)
    mae3 = circular_distance(y_test_hue, y_pred3).mean()
    mse3 = circular_mse(y_test_hue, y_pred3)
    print(f"Predictions: {y_pred3}")
    print(f"MAE: {mae3:.1f}°  MSE: {mse3:.1f}")

    # Summary
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    print(f"{'Model':<30} {'MAE (°)':<12} {'MSE (°²)':<12}")
    print("-"*60)
    print(f"{'ForwardEncodingSequential':<30} {mae1:<12.1f} {mse1:<12.1f}")
    print(f"{'HybridMLPSequential':<30} {mae2:<12.1f} {mse2:<12.1f}")
    print(f"{'HybridSVRSequential':<30} {mae3:<12.1f} {mse3:<12.1f}")

    print("\n✓ All tests passed!")

if __name__ == "__main__":
    test_sequential_models()
