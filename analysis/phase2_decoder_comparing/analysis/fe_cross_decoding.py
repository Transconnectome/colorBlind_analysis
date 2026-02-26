#!/usr/bin/env python3
"""
ForwardEncoding Cross-Decoding: HC → CVD in SRM Space

Trains FE W-matrix on HC SRM data (LOSO within HC), evaluates on CVD SRM data.
Tests whether HC-trained color representations generalize to CVD subjects.

Protocol:
- For each HC LOSO fold (leave-one-HC-out):
  - Train FE W-matrix on 6 HC subjects' SRM amplitudes
  - Evaluate on held-out HC subject (internal validation)
  - Evaluate on each CVD subject
- Report acc_45, MAE per CVD subject per ROI
- Permutation test (1000 iter)

Requires: amplitudes_srm.npy (from compute_srm_amplitudes.py)
Usage:    python fe_cross_decoding.py [--data_dir ...] [--output_dir ...]
"""

import numpy as np
import json
import argparse
import sys
from pathlib import Path
from datetime import datetime

# Add project utils to path
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root / "analysis" / "utils"))
from utils_color_decoding import create_basis_functions

# ============================================================================
# CONFIG
# ============================================================================

HC_SUBJECTS = [f"sub-{i:02d}" for i in range(1, 8)]
CVD_SUBJECTS = [f"sub-{i:02d}" for i in range(8, 11)]
ALL_SUBJECTS = HC_SUBJECTS + CVD_SUBJECTS

ROIS = ['V1', 'V2', 'V3', 'V4']
ROI_DISPLAY = {'V1': 'V1', 'V2': 'V2', 'V3': 'V3', 'V4': 'hV4'}
K_VALUES = {'V1': 4, 'V2': 4, 'V3': 3, 'V4': 3}

HUE_ANGLES = [i * 45 for i in range(8)]  # 0, 45, 90, ..., 315

N_PERM = 1000
SEED = 42

import socket
if socket.gethostname().startswith('node'):
    DEFAULT_DATA_DIR = "/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010"
else:
    DEFAULT_DATA_DIR = str(project_root / "analysis" / "phase1_preprocess_decoding" / "results" / "full_dataset_C010")


# ============================================================================
# FORWARD ENCODING
# ============================================================================

def circular_diff_deg(a, b):
    """Circular difference in degrees (absolute)."""
    diff = np.abs(np.asarray(a, dtype=float) - np.asarray(b, dtype=float))
    return np.where(diff > 180, 360 - diff, diff)


class CrossDecodingFE:
    """ForwardEncoding for cross-decoding: train on group, test on individual."""

    def __init__(self, n_channels=6, alpha=0):
        self.n_channels = n_channels
        self.alpha = alpha
        self.weights = None
        self.basis_full = create_basis_functions(n_channels=n_channels)  # (360, n_channels)

    def fit(self, amplitudes_list):
        """
        Train FE on multiple subjects' SRM-projected amplitudes.

        Args:
            amplitudes_list: list of (6, 8, k) arrays — one per training subject
        """
        # Average across subjects and runs → (8, k)
        all_mean = np.mean([a.mean(axis=0) for a in amplitudes_list], axis=0)  # (8, k)

        # Basis at 8 stimulus hues
        C = self.basis_full[HUE_ANGLES]  # (8, n_channels)
        B = all_mean  # (8, k)

        if self.alpha > 0:
            self.weights = np.linalg.solve(
                C.T @ C + self.alpha * np.eye(self.n_channels),
                C.T @ B
            )
        else:
            self.weights = np.linalg.pinv(C) @ B  # (n_channels, k)

    def predict(self, X):
        """
        Predict hue from brain patterns.

        Args:
            X: (n_samples, k) SRM-projected patterns

        Returns:
            pred_hues: (n_samples,) predicted hue angles (0-359°)
        """
        if self.weights is None:
            raise RuntimeError("Model not fitted yet")

        channel_responses = self.weights @ X.T  # (n_channels, n_samples)

        n_samples = X.shape[0]
        pred_hues = np.zeros(n_samples, dtype=float)

        for i in range(n_samples):
            resp = channel_responses[:, i]
            # Correlate with all 360 templates
            correlations = np.array([
                np.corrcoef(resp, self.basis_full[h])[0, 1]
                if np.std(resp) > 1e-10 else 0.0
                for h in range(360)
            ])
            pred_hues[i] = np.argmax(correlations)

        return pred_hues

    def evaluate(self, amplitudes):
        """
        Evaluate on a single subject's per-run data.

        Args:
            amplitudes: (6, 8, k) per-run SRM amplitudes

        Returns:
            dict with MAE, acc_45, per-color results
        """
        n_runs, n_colors, k = amplitudes.shape
        all_errors = []
        per_color_errors = {c: [] for c in range(n_colors)}

        for run in range(n_runs):
            X = amplitudes[run]  # (8, k)
            pred_hues = self.predict(X)

            for c in range(n_colors):
                true_hue = HUE_ANGLES[c]
                error = circular_diff_deg(pred_hues[c], true_hue)
                all_errors.append(error)
                per_color_errors[c].append(error)

        all_errors = np.array(all_errors)
        mae = float(np.mean(all_errors))
        acc_45 = float(np.mean(all_errors <= 45))

        per_color = {}
        for c in range(n_colors):
            errs = np.array(per_color_errors[c])
            per_color[f'color_{c+1}'] = {
                'mae': float(np.mean(errs)),
                'acc_45': float(np.mean(errs <= 45)),
            }

        return {'mae': mae, 'acc_45': acc_45, 'per_color': per_color}


# ============================================================================
# CROSS-DECODING ANALYSIS
# ============================================================================

def run_cross_decoding(data_dir, roi):
    """
    LOSO cross-decoding: train FE on N-1 HC, test on held-out HC + all CVD.
    """
    roi_display = ROI_DISPLAY.get(roi, roi)
    k = K_VALUES[roi]

    print(f"\n{'='*60}")
    print(f"FE Cross-Decoding: {roi_display} (k={k})")
    print(f"{'='*60}")

    # Load SRM amplitudes
    hc_data = {}
    for s in HC_SUBJECTS:
        path = Path(data_dir) / s / roi / "amplitudes_srm.npy"
        if not path.exists():
            print(f"  WARNING: {path} not found, skipping")
            return None
        hc_data[s] = np.load(path)
        print(f"  Loaded {s}: {hc_data[s].shape}")

    cvd_data = {}
    for s in CVD_SUBJECTS:
        path = Path(data_dir) / s / roi / "amplitudes_srm.npy"
        if not path.exists():
            print(f"  WARNING: {path} not found, skipping")
            return None
        cvd_data[s] = np.load(path)
        print(f"  Loaded {s}: {cvd_data[s].shape}")

    n_hc = len(HC_SUBJECTS)

    # LOSO cross-decoding
    hc_held_out_results = {}
    cvd_fold_results = {s: [] for s in CVD_SUBJECTS}

    for i, held_out in enumerate(HC_SUBJECTS):
        train_subjects = [s for s in HC_SUBJECTS if s != held_out]
        train_data = [hc_data[s] for s in train_subjects]

        # Train FE on 6 HC
        fe = CrossDecodingFE(n_channels=6, alpha=0)
        fe.fit(train_data)

        # Evaluate held-out HC
        result = fe.evaluate(hc_data[held_out])
        hc_held_out_results[held_out] = result
        print(f"  Fold {i+1}: held-out {held_out} MAE={result['mae']:.1f}° acc_45={result['acc_45']:.3f}")

        # Evaluate each CVD
        for s in CVD_SUBJECTS:
            cvd_result = fe.evaluate(cvd_data[s])
            cvd_fold_results[s].append(cvd_result)

    # Aggregate CVD results across folds
    cvd_aggregate = {}
    for s in CVD_SUBJECTS:
        fold_maes = [r['mae'] for r in cvd_fold_results[s]]
        fold_acc45 = [r['acc_45'] for r in cvd_fold_results[s]]
        cvd_aggregate[s] = {
            'mae_mean': float(np.mean(fold_maes)),
            'mae_std': float(np.std(fold_maes)),
            'acc_45_mean': float(np.mean(fold_acc45)),
            'acc_45_std': float(np.std(fold_acc45)),
            'fold_maes': fold_maes,
            'fold_acc45': fold_acc45,
        }
        print(f"  {s} CVD: MAE={cvd_aggregate[s]['mae_mean']:.1f}° ± {cvd_aggregate[s]['mae_std']:.1f}°, "
              f"acc_45={cvd_aggregate[s]['acc_45_mean']:.3f}")

    # HC aggregate
    hc_maes = [hc_held_out_results[s]['mae'] for s in HC_SUBJECTS]
    hc_acc45 = [hc_held_out_results[s]['acc_45'] for s in HC_SUBJECTS]

    print(f"\n  HC held-out: MAE={np.mean(hc_maes):.1f}° ± {np.std(hc_maes, ddof=1):.1f}°, "
          f"acc_45={np.mean(hc_acc45):.3f}")

    # --- Permutation test ---
    # Under null: shuffle color labels → FE should be at chance
    print(f"\n  Permutation test ({N_PERM} iter)...")
    rng = np.random.RandomState(SEED)

    null_hc_maes = []
    null_cvd_maes = {s: [] for s in CVD_SUBJECTS}

    for perm_i in range(N_PERM):
        if (perm_i + 1) % 200 == 0:
            print(f"    Perm {perm_i + 1}/{N_PERM}")

        # Pick a random LOSO fold for efficiency
        fold_idx = rng.randint(0, n_hc)
        held_out = HC_SUBJECTS[fold_idx]
        train_subjects = [s for s in HC_SUBJECTS if s != held_out]

        # Shuffle color labels per subject
        shuffled_train = []
        for s in train_subjects:
            data = hc_data[s].copy()
            for run in range(6):
                perm = rng.permutation(8)
                data[run] = data[run, perm]
            shuffled_train.append(data)

        fe = CrossDecodingFE(n_channels=6, alpha=0)
        fe.fit(shuffled_train)

        # Evaluate held-out HC with shuffled model
        result = fe.evaluate(hc_data[held_out])
        null_hc_maes.append(result['mae'])

        # Evaluate CVD
        for s in CVD_SUBJECTS:
            cvd_result = fe.evaluate(cvd_data[s])
            null_cvd_maes[s].append(cvd_result['mae'])

    # p-values: observed MAE < null MAE (lower is better)
    null_hc_maes = np.array(null_hc_maes)
    observed_hc_mae = np.mean(hc_maes)
    p_hc = float(np.mean(null_hc_maes <= observed_hc_mae))
    print(f"  HC: observed={observed_hc_mae:.1f}°, null={null_hc_maes.mean():.1f}°, p={p_hc:.4f}")

    cvd_perm_results = {}
    for s in CVD_SUBJECTS:
        null_arr = np.array(null_cvd_maes[s])
        obs = cvd_aggregate[s]['mae_mean']
        p = float(np.mean(null_arr <= obs))
        print(f"  {s}: observed={obs:.1f}°, null={null_arr.mean():.1f}°, p={p:.4f}")
        cvd_perm_results[s] = {
            'observed_mae': obs,
            'null_mean': float(null_arr.mean()),
            'null_std': float(null_arr.std()),
            'p_value': p,
        }

    return {
        'roi': roi_display,
        'k': k,
        'hc_held_out': {
            s: hc_held_out_results[s] for s in HC_SUBJECTS
        },
        'hc_summary': {
            'mae_mean': float(np.mean(hc_maes)),
            'mae_std': float(np.std(hc_maes, ddof=1)),
            'acc_45_mean': float(np.mean(hc_acc45)),
            'acc_45_std': float(np.std(hc_acc45, ddof=1)),
        },
        'cvd': cvd_aggregate,
        'permutation': {
            'n_perm': N_PERM,
            'hc': {
                'observed_mae': observed_hc_mae,
                'null_mean': float(null_hc_maes.mean()),
                'p_value': p_hc,
            },
            'cvd': cvd_perm_results,
        },
    }


def main():
    parser = argparse.ArgumentParser(description="FE cross-decoding HC→CVD in SRM space")
    parser.add_argument('--data_dir', type=str, default=DEFAULT_DATA_DIR)
    parser.add_argument('--output_dir', type=str,
                        default=str(Path(__file__).resolve().parent.parent / "results"))
    parser.add_argument('--rois', nargs='+', default=['V1', 'V2', 'V3', 'V4'])
    args = parser.parse_args()

    print("="*60)
    print("ForwardEncoding Cross-Decoding: HC → CVD (SRM Space)")
    print(f"Data: {args.data_dir}")
    print("="*60)

    all_results = {}
    for roi in args.rois:
        result = run_cross_decoding(args.data_dir, roi)
        if result is not None:
            all_results[ROI_DISPLAY.get(roi, roi)] = result

    # Save
    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    output_file = output_path / "fe_cross_decoding.json"

    save_data = {
        'description': 'ForwardEncoding cross-decoding: HC-trained FE evaluated on CVD in SRM space',
        'method': 'LOSO within HC, evaluate held-out HC + CVD',
        'alignment': 'srm',
        'n_perm': N_PERM,
        'seed': SEED,
        'results': all_results,
        'created': datetime.now().isoformat(),
    }

    with open(output_file, 'w') as f:
        json.dump(save_data, f, indent=2)

    # Summary table
    print(f"\n\n{'='*80}")
    print("SUMMARY: FE Cross-Decoding")
    print(f"{'='*80}")
    print(f"{'ROI':<5} | {'HC MAE':<10} | {'HC acc_45':<10} | {'sub-08 MAE':<12} | {'sub-09 MAE':<12} | {'sub-10 MAE':<12}")
    print("-"*70)
    for roi_d in ['V1', 'V2', 'V3', 'hV4']:
        if roi_d not in all_results:
            continue
        r = all_results[roi_d]
        hc = r['hc_summary']
        parts = [f"{roi_d:<5}", f"{hc['mae_mean']:5.1f}±{hc['mae_std']:.1f}", f"{hc['acc_45_mean']:.3f}"]
        for s in CVD_SUBJECTS:
            if s in r['cvd']:
                parts.append(f"{r['cvd'][s]['mae_mean']:5.1f}±{r['cvd'][s]['mae_std']:.1f}")
            else:
                parts.append("N/A")
        print(" | ".join(parts))

    print(f"\nSaved: {output_file}")


if __name__ == '__main__':
    main()
