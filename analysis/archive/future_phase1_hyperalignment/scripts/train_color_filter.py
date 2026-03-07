#!/usr/bin/env python3
"""
Train Deep Learning Color Filter
=================================

Learn a neural network that transforms HC color patterns to CVD patterns
in the hyperalignment common space.

This is only possible with hyperalignment (not Procrustes) because:
- All data is in the SAME coordinate system
- Can pool all HC and CVD together
- Single unified model for all CVD subjects

Usage:
    python train_color_filter.py --roi V1 --model residual --epochs 200

Author: Automated
Date: 2025-12-18
"""

import numpy as np
import torch
from torch.utils.data import DataLoader, random_split
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from deep_color_filter import (
    CommonSpaceDataset,
    ColorFilterMLP,
    ColorFilterResidual,
    ColorFilterConditional,
    ColorFilterTrainer
)


def main():
    parser = argparse.ArgumentParser(description='Train color filter')
    parser.add_argument('--roi', type=str, default='V1', help='ROI name')
    parser.add_argument('--model', type=str, default='residual',
                       choices=['mlp', 'residual', 'conditional'],
                       help='Model architecture')
    parser.add_argument('--epochs', type=int, default=200, help='Training epochs')
    parser.add_argument('--lr', type=float, default=1e-3, help='Learning rate')
    parser.add_argument('--batch_size', type=int, default=32, help='Batch size')
    parser.add_argument('--lambda_structure', type=float, default=0.1,
                       help='Weight for structure preservation loss')
    parser.add_argument('--lambda_smooth', type=float, default=0.01,
                       help='Weight for smoothness loss')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    args = parser.parse_args()

    # Set seed
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)

    # Paths
    RESULTS_DIR = Path('analysis/hyperalignment/results')
    MODELS_DIR = Path('analysis/hyperalignment/models')
    FIGURES_DIR = Path('analysis/hyperalignment/figures')
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    print("\n" + "="*70)
    print(" Training Deep Learning Color Filter")
    print("="*70)
    print(f"\n📍 ROI: {args.roi}")
    print(f"📍 Model: {args.model}")
    print(f"📍 Epochs: {args.epochs}")
    print(f"📍 Batch size: {args.batch_size}")
    print(f"📍 Learning rate: {args.lr}")

    # ========== Load Data ==========
    print("\n" + "="*70)
    print("Loading Hyperalignment Results")
    print("="*70)

    # HC common space
    hc_common = np.load(RESULTS_DIR / f'common_space_{args.roi}.npy')
    print(f"  HC common space: {hc_common.shape}")

    # CVD aligned data
    cvd_data = {}
    cvd_types = {
        'sub-08': 'deutan',
        'sub-09': 'deutan',
        'sub-10': 'protan'
    }

    for cvd_id in ['sub-08', 'sub-09', 'sub-10']:
        aligned_path = RESULTS_DIR / f'{cvd_id}_aligned_{args.roi}.npy'
        if aligned_path.exists():
            cvd_data[cvd_id] = np.load(aligned_path)
            print(f"  {cvd_id} ({cvd_types[cvd_id]}): {cvd_data[cvd_id].shape}")

    if len(cvd_data) == 0:
        print("\n❌ No CVD data found! Run hyperalignment first.")
        return

    # ========== Create Dataset ==========
    print("\n" + "="*70)
    print("Creating Dataset")
    print("="*70)

    dataset = CommonSpaceDataset(
        hc_data=hc_common,
        cvd_data_dict=cvd_data,
        cvd_types=cvd_types,
        n_runs=6,
        n_colors=8
    )

    print(f"  Total samples: {len(dataset)}")
    print(f"  = {len(cvd_data)} CVD × 6 runs × 8 colors")

    # Train/val split (80/20)
    n_train = int(0.8 * len(dataset))
    n_val = len(dataset) - n_train
    train_dataset, val_dataset = random_split(dataset, [n_train, n_val])

    train_loader = DataLoader(train_dataset, batch_size=args.batch_size,
                              shuffle=True, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size,
                           shuffle=False, num_workers=0)

    print(f"  Train samples: {n_train}")
    print(f"  Val samples: {n_val}")

    # ========== Create Model ==========
    print("\n" + "="*70)
    print("Creating Model")
    print("="*70)

    p = hc_common.shape[1]  # Number of voxels

    if args.model == 'mlp':
        model = ColorFilterMLP(p, hidden_dims=[512, 256, 512])
        print(f"  Model: MLP (direct mapping)")
    elif args.model == 'residual':
        model = ColorFilterResidual(p, hidden_dims=[512, 256, 512])
        print(f"  Model: Residual (HC + distortion)")
    elif args.model == 'conditional':
        model = ColorFilterConditional(p, hidden_dims=[512, 256, 512])
        print(f"  Model: Conditional (includes CVD type)")

    n_params = sum(p.numel() for p in model.parameters())
    print(f"  Parameters: {n_params:,}")

    # ========== Train ==========
    trainer = ColorFilterTrainer(model)
    trainer.train(
        train_loader=train_loader,
        val_loader=val_loader,
        n_epochs=args.epochs,
        lr=args.lr,
        lambda_structure=args.lambda_structure,
        lambda_smooth=args.lambda_smooth
    )

    # ========== Save Results ==========
    print("\n" + "="*70)
    print("Saving Results")
    print("="*70)

    # Save model
    model_name = f'color_filter_{args.model}_{args.roi}.pt'
    trainer.save_model(MODELS_DIR / model_name)

    # Save training history plot
    history_name = f'training_history_{args.model}_{args.roi}.png'
    trainer.plot_history(save_path=FIGURES_DIR / history_name)

    # ========== Evaluate ==========
    print("\n" + "="*70)
    print("Evaluation on Validation Set")
    print("="*70)

    model.eval()
    predictions = []
    targets = []
    hc_inputs = []
    cvd_ids = []

    with torch.no_grad():
        for batch in val_loader:
            hc = batch['hc'].to(trainer.device)
            cvd = batch['cvd'].to(trainer.device)

            if args.model == 'conditional':
                cvd_type = batch['cvd_type'].to(trainer.device)
                pred = model(hc, cvd_type)
            else:
                pred = model(hc)

            predictions.append(pred.cpu().numpy())
            targets.append(cvd.cpu().numpy())
            hc_inputs.append(hc.cpu().numpy())
            cvd_ids.extend(batch['cvd_id'])

    predictions = np.vstack(predictions)
    targets = np.vstack(targets)
    hc_inputs = np.vstack(hc_inputs)

    # Compute metrics
    mse = np.mean((predictions - targets)**2)
    mae = np.mean(np.abs(predictions - targets))
    corr = np.corrcoef(predictions.flatten(), targets.flatten())[0, 1]

    print(f"\n  MSE: {mse:.6f}")
    print(f"  MAE: {mae:.6f}")
    print(f"  Correlation: {corr:.4f}")

    # Per-CVD metrics
    print("\n  Per-CVD performance:")
    unique_cvds = sorted(set(cvd_ids))
    for cvd_id in unique_cvds:
        mask = [i for i, cid in enumerate(cvd_ids) if cid == cvd_id]
        if len(mask) > 0:
            cvd_mse = np.mean((predictions[mask] - targets[mask])**2)
            cvd_corr = np.corrcoef(predictions[mask].flatten(),
                                  targets[mask].flatten())[0, 1]
            print(f"    {cvd_id}: MSE={cvd_mse:.6f}, Corr={cvd_corr:.4f}")

    # ========== Done ==========
    print("\n" + "="*70)
    print("✅ Training Complete!")
    print("="*70)
    print(f"\n📦 Model saved: {MODELS_DIR / model_name}")
    print(f"📊 History plot: {FIGURES_DIR / history_name}")
    print("\nNext steps:")
    print("  1. Evaluate on test CVD subjects")
    print("  2. Visualize learned filter structure")
    print("  3. Apply to new HC patterns for CVD simulation")
    print("  4. Compare with ground truth CVD data")


if __name__ == '__main__':
    main()
