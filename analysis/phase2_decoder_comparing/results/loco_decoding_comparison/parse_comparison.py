#!/usr/bin/env python3
"""
Parse LOCO Decoding Comparison Results (2026-02-23)
FE_Ensemble vs Baseline and ensemble variants
"""

import json
import numpy as np
from pathlib import Path

# Paths
comparison_file = Path(__file__).parent / 'decoding_comparison.json'

with open(comparison_file, 'r') as f:
    data = json.load(f)

# Subject groups
subjects_hc = [f'{i:02d}' for i in range(1, 8)]
subjects_cvd = [f'{i:02d}' for i in range(8, 11)]
rois = data['rois']  # ['V1', 'V2', 'V3', 'V4']
models = data['models']  # ['ForwardEncoding', 'FE_Ensemble', ...]

# ROI display mapping
roi_display = {'V1': 'V1', 'V2': 'V2', 'V3': 'V3', 'V4': 'hV4'}

print("="*80)
print("LOCO ENSEMBLE RESULTS (2026-02-23)")
print("="*80)
print(f"\nData from: {data['description']}")
print(f"Models compared: {', '.join(models)}")
print(f"Alignment: {data['alignment']}")

# ============================================================================
# 1. FE_Ensemble vs ForwardEncoding (Primary Comparison)
# ============================================================================

print("\n### FE_Ensemble vs Baseline (Procrustes alignment)")
print("\n| ROI | FE Baseline HC | FE_Ensemble HC | Δ HC | FE Baseline CVD | FE_Ensemble CVD | Δ CVD |")
print("|-----|---------------|----------------|------|-----------------|-----------------|-------|")

for roi in rois:
    # Extract HC data
    baseline_hc = []
    ensemble_hc = []
    for subj_id in subjects_hc:
        if subj_id in data['per_subject'] and roi in data['per_subject'][subj_id]:
            subj_roi = data['per_subject'][subj_id][roi]
            if 'ForwardEncoding' in subj_roi:
                baseline_hc.append(subj_roi['ForwardEncoding']['mae'])
            if 'FE_Ensemble' in subj_roi:
                ensemble_hc.append(subj_roi['FE_Ensemble']['mae'])

    # Extract CVD data
    baseline_cvd = []
    ensemble_cvd = []
    for subj_id in subjects_cvd:
        if subj_id in data['per_subject'] and roi in data['per_subject'][subj_id]:
            subj_roi = data['per_subject'][subj_id][roi]
            if 'ForwardEncoding' in subj_roi:
                baseline_cvd.append(subj_roi['ForwardEncoding']['mae'])
            if 'FE_Ensemble' in subj_roi:
                ensemble_cvd.append(subj_roi['FE_Ensemble']['mae'])

    # Calculate stats
    if baseline_hc and ensemble_hc:
        mean_base_hc = np.mean(baseline_hc)
        std_base_hc = np.std(baseline_hc, ddof=1)
        mean_ens_hc = np.mean(ensemble_hc)
        std_ens_hc = np.std(ensemble_hc, ddof=1)
        delta_hc = mean_ens_hc - mean_base_hc
    else:
        mean_base_hc = std_base_hc = mean_ens_hc = std_ens_hc = delta_hc = np.nan

    if baseline_cvd and ensemble_cvd:
        mean_base_cvd = np.mean(baseline_cvd)
        std_base_cvd = np.std(baseline_cvd, ddof=1)
        mean_ens_cvd = np.mean(ensemble_cvd)
        std_ens_cvd = np.std(ensemble_cvd, ddof=1)
        delta_cvd = mean_ens_cvd - mean_base_cvd
    else:
        mean_base_cvd = std_base_cvd = mean_ens_cvd = std_ens_cvd = delta_cvd = np.nan

    # Format output
    delta_hc_str = f"{delta_hc:+.1f}" if not np.isnan(delta_hc) else "N/A"
    delta_cvd_str = f"{delta_cvd:+.1f}" if not np.isnan(delta_cvd) else "N/A"

    roi_name = roi_display[roi]
    print(f"| {roi_name:4s} | {mean_base_hc:.1f} ± {std_base_hc:.1f} | {mean_ens_hc:.1f} ± {std_ens_hc:.1f} | {delta_hc_str:>6s} | "
          f"{mean_base_cvd:.1f} ± {std_base_cvd:.1f} | {mean_ens_cvd:.1f} ± {std_ens_cvd:.1f} | {delta_cvd_str:>6s} |")

# ============================================================================
# 2. Individual Subject Improvements
# ============================================================================

print("\n### Individual Subject Improvements (FE_Ensemble vs Baseline)")
print("\n**HC Subjects:**\n")

for subj_id in subjects_hc:
    if subj_id not in data['per_subject']:
        continue

    print(f"**sub-{subj_id}:**")
    for roi in rois:
        if roi not in data['per_subject'][subj_id]:
            continue

        subj_roi = data['per_subject'][subj_id][roi]
        baseline = subj_roi['ForwardEncoding']['mae'] if 'ForwardEncoding' in subj_roi else np.nan
        ensemble = subj_roi['FE_Ensemble']['mae'] if 'FE_Ensemble' in subj_roi else np.nan

        if not np.isnan(baseline) and not np.isnan(ensemble):
            delta = ensemble - baseline
            roi_name = roi_display[roi]
            print(f"  - {roi_name}: {baseline:.1f}° → {ensemble:.1f}° ({delta:+.1f}°)")
    print()

print("**CVD Subjects:**\n")

for subj_id in subjects_cvd:
    if subj_id not in data['per_subject']:
        continue

    print(f"**sub-{subj_id}:**")
    for roi in rois:
        if roi not in data['per_subject'][subj_id]:
            continue

        subj_roi = data['per_subject'][subj_id][roi]
        baseline = subj_roi['ForwardEncoding']['mae'] if 'ForwardEncoding' in subj_roi else np.nan
        ensemble = subj_roi['FE_Ensemble']['mae'] if 'FE_Ensemble' in subj_roi else np.nan

        if not np.isnan(baseline) and not np.isnan(ensemble):
            delta = ensemble - baseline
            roi_name = roi_display[roi]
            print(f"  - {roi_name}: {baseline:.1f}° → {ensemble:.1f}° ({delta:+.1f}°)")
    print()

# ============================================================================
# 3. All Ensemble Variants Comparison
# ============================================================================

print("\n### All Ensemble Variants (Procrustes)")
print("\n**HC Group:**\n")
print("| ROI | " + " | ".join(models) + " |")
print("|-----" + "|-------" * len(models) + "|")

for roi in rois:
    roi_name = roi_display[roi]
    row = f"| {roi_name:4s} "

    for model in models:
        values = []
        for subj_id in subjects_hc:
            if subj_id in data['per_subject'] and roi in data['per_subject'][subj_id]:
                if model in data['per_subject'][subj_id][roi]:
                    values.append(data['per_subject'][subj_id][roi][model]['mae'])

        mean_val = np.mean(values) if values else np.nan
        std_val = np.std(values, ddof=1) if values else np.nan
        row += f"| {mean_val:.1f} ± {std_val:.1f} "

    print(row + "|")

print("\n**CVD Group:**\n")
print("| ROI | " + " | ".join(models) + " |")
print("|-----" + "|-------" * len(models) + "|")

for roi in rois:
    roi_name = roi_display[roi]
    row = f"| {roi_name:4s} "

    for model in models:
        values = []
        for subj_id in subjects_cvd:
            if subj_id in data['per_subject'] and roi in data['per_subject'][subj_id]:
                if model in data['per_subject'][subj_id][roi]:
                    values.append(data['per_subject'][subj_id][roi][model]['mae'])

        mean_val = np.mean(values) if values else np.nan
        std_val = np.std(values, ddof=1) if values else np.nan
        row += f"| {mean_val:.1f} ± {std_val:.1f} "

    print(row + "|")

# ============================================================================
# 4. Relative Improvements for Each Variant
# ============================================================================

print("\n### Relative Improvements vs Baseline")
print("\n**HC Group (Δ from ForwardEncoding):**\n")
print("| ROI | FE_Ensemble | FE_EnsembleRidge | FE_EnsembleGaussML |")
print("|-----|-------------|------------------|---------------------|")

for roi in rois:
    roi_name = roi_display[roi]
    row = f"| {roi_name:4s} "

    # Get baseline mean
    baseline_vals = []
    for subj_id in subjects_hc:
        if subj_id in data['per_subject'] and roi in data['per_subject'][subj_id]:
            if 'ForwardEncoding' in data['per_subject'][subj_id][roi]:
                baseline_vals.append(data['per_subject'][subj_id][roi]['ForwardEncoding']['mae'])
    baseline_mean = np.mean(baseline_vals) if baseline_vals else np.nan

    # Calculate deltas for each ensemble variant
    for model in ['FE_Ensemble', 'FE_EnsembleRidge', 'FE_EnsembleGaussML']:
        values = []
        for subj_id in subjects_hc:
            if subj_id in data['per_subject'] and roi in data['per_subject'][subj_id]:
                if model in data['per_subject'][subj_id][roi]:
                    values.append(data['per_subject'][subj_id][roi][model]['mae'])

        model_mean = np.mean(values) if values else np.nan
        delta = model_mean - baseline_mean if not np.isnan(model_mean) and not np.isnan(baseline_mean) else np.nan

        delta_str = f"{delta:+.1f}" if not np.isnan(delta) else "N/A"
        row += f"| {delta_str:>12s} "

    print(row + "|")

print("\n**CVD Group (Δ from ForwardEncoding):**\n")
print("| ROI | FE_Ensemble | FE_EnsembleRidge | FE_EnsembleGaussML |")
print("|-----|-------------|------------------|---------------------|")

for roi in rois:
    roi_name = roi_display[roi]
    row = f"| {roi_name:4s} "

    # Get baseline mean
    baseline_vals = []
    for subj_id in subjects_cvd:
        if subj_id in data['per_subject'] and roi in data['per_subject'][subj_id]:
            if 'ForwardEncoding' in data['per_subject'][subj_id][roi]:
                baseline_vals.append(data['per_subject'][subj_id][roi]['ForwardEncoding']['mae'])
    baseline_mean = np.mean(baseline_vals) if baseline_vals else np.nan

    # Calculate deltas for each ensemble variant
    for model in ['FE_Ensemble', 'FE_EnsembleRidge', 'FE_EnsembleGaussML']:
        values = []
        for subj_id in subjects_cvd:
            if subj_id in data['per_subject'] and roi in data['per_subject'][subj_id]:
                if model in data['per_subject'][subj_id][roi]:
                    values.append(data['per_subject'][subj_id][roi][model]['mae'])

        model_mean = np.mean(values) if values else np.nan
        delta = model_mean - baseline_mean if not np.isnan(model_mean) and not np.isnan(baseline_mean) else np.nan

        delta_str = f"{delta:+.1f}" if not np.isnan(delta) else "N/A"
        row += f"| {delta_str:>12s} "

    print(row + "|")

print("\n" + "="*80)
print("END OF REPORT")
print("="*80)
