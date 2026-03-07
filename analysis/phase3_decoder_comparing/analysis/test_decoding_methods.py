#!/usr/bin/env python3
"""
Test Decoding Methods — Local Comparison (Round 2: Ensemble)

Runs baseline FE + 3 ensemble FE variants on all 10 subjects × 4 ROIs (no permutation test).
Outputs a comparison table (MAE per method × ROI × group) + JSON results.

Usage:
    conda activate srm
    python analysis/phase2_decoder_comparing/analysis/test_decoding_methods.py
"""

import sys
import json
import time
import numpy as np
from pathlib import Path
from datetime import datetime

# Setup paths
PROJECT_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = PROJECT_ROOT / 'analysis' / 'phase2_decoder_comparing' / 'model_comparison_validation' / 'scripts'
sys.path.insert(0, str(SCRIPT_DIR))

from run_loco_comparison import (
    LOCOForwardEncodingDecoder,
    FE_EnsembleDecoder,
    FE_EnsembleRidgeDecoder,
    FE_EnsembleGaussMLDecoder,
    loco_cv, load_amplitudes
)
from utils import HUE_ANGLES, HC_SUBJECTS, CVD_SUBJECTS

# ============================================================================
# Configuration
# ============================================================================

C010_DIR = PROJECT_ROOT / 'analysis' / 'phase1_preprocess_decoding' / 'results' / 'full_dataset_C010'
OUTPUT_DIR = PROJECT_ROOT / 'analysis' / 'phase2_decoder_comparing' / 'results' / 'loco_decoding_comparison'

SUBJECTS = [f'{i:02d}' for i in range(1, 11)]
ROIS = ['V1', 'V2', 'V3', 'V4']

MODEL_MAP = {
    'ForwardEncoding': LOCOForwardEncodingDecoder,
    'FE_Ensemble': FE_EnsembleDecoder,
    'FE_EnsembleRidge': FE_EnsembleRidgeDecoder,
    'FE_EnsembleGaussML': FE_EnsembleGaussMLDecoder,
}
MODEL_NAMES = list(MODEL_MAP.keys())


def run_comparison():
    """Run all models on all subjects × ROIs, collect MAE results."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # results[subject][roi][model] = mae
    all_results = {}
    total_combos = len(SUBJECTS) * len(ROIS) * len(MODEL_NAMES)
    done = 0
    t_start = time.time()

    for subject in SUBJECTS:
        all_results[subject] = {}
        for roi in ROIS:
            all_results[subject][roi] = {}

            try:
                amplitudes = load_amplitudes(str(C010_DIR), subject, roi, 'procrustes')
            except FileNotFoundError as e:
                print(f"  SKIP sub-{subject} {roi}: {e}")
                for model_name in MODEL_NAMES:
                    all_results[subject][roi][model_name] = {
                        'mae': float('nan'), 'fold_results': None
                    }
                    done += 1
                continue

            for model_name in MODEL_NAMES:
                done += 1
                model_class = MODEL_MAP[model_name]

                try:
                    fold_results = loco_cv(amplitudes, model_class, model_name)
                    mae = np.mean([f['mae'] for f in fold_results])
                    adj_acc = np.mean([f['adjacent_acc'] for f in fold_results])

                    all_results[subject][roi][model_name] = {
                        'mae': float(mae),
                        'adjacent_acc': float(adj_acc),
                        'fold_results': fold_results
                    }

                    elapsed = time.time() - t_start
                    eta = elapsed / done * (total_combos - done) if done > 0 else 0
                    print(f"  [{done}/{total_combos}] sub-{subject} {roi} {model_name}: "
                          f"MAE={mae:.1f}°  (ETA {eta:.0f}s)")

                except Exception as e:
                    print(f"  ERROR sub-{subject} {roi} {model_name}: {e}")
                    all_results[subject][roi][model_name] = {
                        'mae': float('nan'), 'fold_results': None
                    }

    return all_results


def print_comparison_table(all_results):
    """Print formatted comparison table: MAE per method × ROI × group."""
    print(f"\n{'='*100}")
    print("DECODING METHOD COMPARISON — MAE (degrees)")
    print(f"{'='*100}")

    # Header
    header = f"{'Method':<16}"
    for roi in ROIS:
        header += f" | {roi} HC    {roi} CVD  "
    print(header)
    print("-" * len(header))

    for model_name in MODEL_NAMES:
        row = f"{model_name:<16}"
        for roi in ROIS:
            # HC mean
            hc_maes = []
            for s in HC_SUBJECTS:
                m = all_results.get(s, {}).get(roi, {}).get(model_name, {}).get('mae', float('nan'))
                if not np.isnan(m):
                    hc_maes.append(m)
            hc_mean = np.mean(hc_maes) if hc_maes else float('nan')

            # CVD mean
            cvd_maes = []
            for s in CVD_SUBJECTS:
                m = all_results.get(s, {}).get(roi, {}).get(model_name, {}).get('mae', float('nan'))
                if not np.isnan(m):
                    cvd_maes.append(m)
            cvd_mean = np.mean(cvd_maes) if cvd_maes else float('nan')

            row += f" | {hc_mean:6.1f}° {cvd_mean:6.1f}°"
        print(row)

    # Print per-subject detail
    print(f"\n{'='*100}")
    print("PER-SUBJECT MAE")
    print(f"{'='*100}")

    for roi in ROIS:
        print(f"\n--- {roi} ---")
        header = f"{'Subject':<10}"
        for model_name in MODEL_NAMES:
            header += f" {model_name:>16}"
        print(header)

        for subject in SUBJECTS:
            group = 'HC' if subject in HC_SUBJECTS else 'CVD'
            row = f"sub-{subject} ({group})"
            for model_name in MODEL_NAMES:
                mae = all_results.get(subject, {}).get(roi, {}).get(model_name, {}).get('mae', float('nan'))
                row += f" {mae:16.1f}"
            print(row)


def save_results(all_results):
    """Save JSON results."""
    # Build summary (without fold_results for compact output)
    summary = {}
    for subject in SUBJECTS:
        summary[subject] = {}
        for roi in ROIS:
            summary[subject][roi] = {}
            for model_name in MODEL_NAMES:
                entry = all_results.get(subject, {}).get(roi, {}).get(model_name, {})
                summary[subject][roi][model_name] = {
                    'mae': entry.get('mae', float('nan')),
                    'adjacent_acc': entry.get('adjacent_acc', float('nan')),
                }

    # Group means
    group_summary = {}
    for model_name in MODEL_NAMES:
        group_summary[model_name] = {}
        for roi in ROIS:
            hc_maes = [all_results[s][roi][model_name]['mae']
                       for s in HC_SUBJECTS
                       if not np.isnan(all_results.get(s, {}).get(roi, {}).get(model_name, {}).get('mae', float('nan')))]
            cvd_maes = [all_results[s][roi][model_name]['mae']
                        for s in CVD_SUBJECTS
                        if not np.isnan(all_results.get(s, {}).get(roi, {}).get(model_name, {}).get('mae', float('nan')))]
            group_summary[model_name][roi] = {
                'HC_mean': float(np.mean(hc_maes)) if hc_maes else None,
                'HC_std': float(np.std(hc_maes)) if hc_maes else None,
                'CVD_mean': float(np.mean(cvd_maes)) if cvd_maes else None,
                'CVD_std': float(np.std(cvd_maes)) if cvd_maes else None,
            }

    output = {
        'description': 'LOCO decoding method comparison — Round 2: Ensemble (baseline + 3 ensemble variants)',
        'models': MODEL_NAMES,
        'subjects': SUBJECTS,
        'rois': ROIS,
        'alignment': 'procrustes',
        'n_permutations': 0,
        'per_subject': summary,
        'group_summary': group_summary,
        'timestamp': datetime.now().isoformat(),
    }

    output_file = OUTPUT_DIR / 'decoding_comparison.json'
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    print(f"\nSaved: {output_file}")

    # Save full results with fold details
    full_output_file = OUTPUT_DIR / 'decoding_comparison_full.json'
    # Convert fold_results for serialization
    full_data = {}
    for subject in SUBJECTS:
        full_data[subject] = {}
        for roi in ROIS:
            full_data[subject][roi] = {}
            for model_name in MODEL_NAMES:
                entry = all_results.get(subject, {}).get(roi, {}).get(model_name, {})
                full_data[subject][roi][model_name] = {
                    'mae': entry.get('mae', float('nan')),
                    'adjacent_acc': entry.get('adjacent_acc', float('nan')),
                    'fold_results': entry.get('fold_results'),
                }

    with open(full_output_file, 'w') as f:
        json.dump(full_data, f, indent=2)
    print(f"Saved: {full_output_file}")


if __name__ == '__main__':
    print(f"{'='*80}")
    print("LOCO Decoding Method Comparison")
    print(f"{'='*80}")
    print(f"Data: {C010_DIR}")
    print(f"Subjects: {SUBJECTS}")
    print(f"ROIs: {ROIS}")
    print(f"Models: {MODEL_NAMES}")
    print(f"Output: {OUTPUT_DIR}")
    print(f"{'='*80}\n")

    all_results = run_comparison()
    print_comparison_table(all_results)
    save_results(all_results)
