#!/usr/bin/env python3
"""
Parse LOCO ensemble results (2026-02-23)
Extract FE_Ensemble vs ForwardEncoding comparison across all alignments
"""

import json
import numpy as np
from pathlib import Path
from collections import defaultdict

# Paths
base_dir = Path(__file__).parent
alignments = ['raw', 'procrustes', 'srm']
subjects_hc = [f'{i:02d}' for i in range(1, 8)]  # Just '01', '02', etc.
subjects_cvd = [f'{i:02d}' for i in range(8, 11)]
all_subjects = subjects_hc + subjects_cvd
rois = ['V1', 'V2', 'V3', 'V4']  # Note: JSON uses 'V4' not 'hV4'

# Storage: results[alignment][decoder][subject][roi] = mae
results = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))

# Parse all files
for alignment in alignments:
    for subject_id in all_subjects:
        json_path = base_dir / alignment / f'sub-{subject_id}_loco.json'

        if not json_path.exists():
            print(f"WARNING: Missing {json_path}")
            continue

        with open(json_path, 'r') as f:
            data = json.load(f)

        # Structure: data['results'][ROI][Decoder]['overall_mae']
        if 'results' not in data:
            print(f"WARNING: No 'results' in {json_path}")
            continue

        for roi in rois:
            if roi not in data['results']:
                continue

            roi_results = data['results'][roi]

            # Iterate through decoders
            for decoder_name, decoder_data in roi_results.items():
                if 'overall_mae' in decoder_data:
                    mae = decoder_data['overall_mae']
                    results[alignment][decoder_name][subject_id][roi] = mae

# ============================================================================
# Generate Summary Report
# ============================================================================

print("\n" + "="*80)
print("LOCO ENSEMBLE RESULTS (2026-02-23)")
print("="*80)

# ============================================================================
# 1. FE_Ensemble vs ForwardEncoding Comparison (Procrustes)
# ============================================================================

print("\n### FE_Ensemble vs Baseline (Procrustes alignment)")
print("\n| ROI | FE Baseline HC | FE_Ensemble HC | Δ HC | FE Baseline CVD | FE_Ensemble CVD | Δ CVD |")
print("|-----|---------------|----------------|------|-----------------|-----------------|-------|")

# Display ROI name mapping
roi_display = {'V1': 'V1', 'V2': 'V2', 'V3': 'V3', 'V4': 'hV4'}

for roi in rois:
    # Baseline (ForwardEncoding)
    baseline_hc = []
    baseline_cvd = []

    if 'ForwardEncoding' in results['procrustes']:
        for subj in subjects_hc:
            if roi in results['procrustes']['ForwardEncoding'].get(subj, {}):
                baseline_hc.append(results['procrustes']['ForwardEncoding'][subj][roi])
        for subj in subjects_cvd:
            if roi in results['procrustes']['ForwardEncoding'].get(subj, {}):
                baseline_cvd.append(results['procrustes']['ForwardEncoding'][subj][roi])

    # Ensemble
    ensemble_hc = []
    ensemble_cvd = []

    if 'FE_Ensemble' in results['procrustes']:
        for subj in subjects_hc:
            if roi in results['procrustes']['FE_Ensemble'].get(subj, {}):
                ensemble_hc.append(results['procrustes']['FE_Ensemble'][subj][roi])
        for subj in subjects_cvd:
            if roi in results['procrustes']['FE_Ensemble'].get(subj, {}):
                ensemble_cvd.append(results['procrustes']['FE_Ensemble'][subj][roi])

    # Calculate means and improvements
    if baseline_hc and ensemble_hc:
        mean_baseline_hc = np.mean(baseline_hc)
        std_baseline_hc = np.std(baseline_hc, ddof=1)
        mean_ensemble_hc = np.mean(ensemble_hc)
        std_ensemble_hc = np.std(ensemble_hc, ddof=1)
        delta_hc = mean_ensemble_hc - mean_baseline_hc
    else:
        mean_baseline_hc = mean_ensemble_hc = delta_hc = std_baseline_hc = std_ensemble_hc = np.nan

    if baseline_cvd and ensemble_cvd:
        mean_baseline_cvd = np.mean(baseline_cvd)
        std_baseline_cvd = np.std(baseline_cvd, ddof=1)
        mean_ensemble_cvd = np.mean(ensemble_cvd)
        std_ensemble_cvd = np.std(ensemble_cvd, ddof=1)
        delta_cvd = mean_ensemble_cvd - mean_baseline_cvd
    else:
        mean_baseline_cvd = mean_ensemble_cvd = delta_cvd = std_baseline_cvd = std_ensemble_cvd = np.nan

    # Format with sign for delta
    delta_hc_str = f"{delta_hc:+.1f}" if not np.isnan(delta_hc) else "N/A"
    delta_cvd_str = f"{delta_cvd:+.1f}" if not np.isnan(delta_cvd) else "N/A"

    roi_name = roi_display[roi]
    print(f"| {roi_name:4s} | {mean_baseline_hc:.1f} ± {std_baseline_hc:.1f} | {mean_ensemble_hc:.1f} ± {std_ensemble_hc:.1f} | {delta_hc_str:>6s} | "
          f"{mean_baseline_cvd:.1f} ± {std_baseline_cvd:.1f} | {mean_ensemble_cvd:.1f} ± {std_ensemble_cvd:.1f} | {delta_cvd_str:>6s} |")

# ============================================================================
# 2. Individual Subject Improvements (Procrustes, FE_Ensemble)
# ============================================================================

print("\n### Individual Subject Improvements (Procrustes, FE_Ensemble vs Baseline)")
print("\n**HC Subjects:**\n")

for subj_id in subjects_hc:
    print(f"**sub-{subj_id}:**")
    for roi in rois:
        baseline = results['procrustes'].get('ForwardEncoding', {}).get(subj_id, {}).get(roi, np.nan)
        ensemble = results['procrustes'].get('FE_Ensemble', {}).get(subj_id, {}).get(roi, np.nan)

        if not np.isnan(baseline) and not np.isnan(ensemble):
            delta = ensemble - baseline
            roi_name = roi_display[roi]
            print(f"  - {roi_name}: {baseline:.1f}° → {ensemble:.1f}° ({delta:+.1f}°)")
    print()

print("**CVD Subjects:**\n")

for subj_id in subjects_cvd:
    print(f"**sub-{subj_id}:**")
    for roi in rois:
        baseline = results['procrustes'].get('ForwardEncoding', {}).get(subj_id, {}).get(roi, np.nan)
        ensemble = results['procrustes'].get('FE_Ensemble', {}).get(subj_id, {}).get(roi, np.nan)

        if not np.isnan(baseline) and not np.isnan(ensemble):
            delta = ensemble - baseline
            roi_name = roi_display[roi]
            print(f"  - {roi_name}: {baseline:.1f}° → {ensemble:.1f}° ({delta:+.1f}°)")
    print()

# ============================================================================
# 3. Non-linear Models Performance (Procrustes)
# ============================================================================

print("\n### Non-linear Models Performance (Procrustes)")
print("\n| ROI | FE_Ensemble HC | MLP HC | SVM HC | FE_Ensemble CVD | MLP CVD | SVM CVD |")
print("|-----|---------------|---------|---------|-----------------|---------|---------|")

for roi in rois:
    # Ensemble
    ensemble_hc = []
    ensemble_cvd = []
    if 'FE_Ensemble' in results['procrustes']:
        for subj_id in subjects_hc:
            if roi in results['procrustes']['FE_Ensemble'].get(subj_id, {}):
                ensemble_hc.append(results['procrustes']['FE_Ensemble'][subj_id][roi])
        for subj_id in subjects_cvd:
            if roi in results['procrustes']['FE_Ensemble'].get(subj_id, {}):
                ensemble_cvd.append(results['procrustes']['FE_Ensemble'][subj_id][roi])

    # MLP
    mlp_hc = []
    mlp_cvd = []
    if 'MLP' in results['procrustes']:
        for subj_id in subjects_hc:
            if roi in results['procrustes']['MLP'].get(subj_id, {}):
                mlp_hc.append(results['procrustes']['MLP'][subj_id][roi])
        for subj_id in subjects_cvd:
            if roi in results['procrustes']['MLP'].get(subj_id, {}):
                mlp_cvd.append(results['procrustes']['MLP'][subj_id][roi])

    # SVM
    svm_hc = []
    svm_cvd = []
    if 'SVM' in results['procrustes']:
        for subj_id in subjects_hc:
            if roi in results['procrustes']['SVM'].get(subj_id, {}):
                svm_hc.append(results['procrustes']['SVM'][subj_id][roi])
        for subj_id in subjects_cvd:
            if roi in results['procrustes']['SVM'].get(subj_id, {}):
                svm_cvd.append(results['procrustes']['SVM'][subj_id][roi])

    # Calculate means
    mean_ens_hc = np.mean(ensemble_hc) if ensemble_hc else np.nan
    std_ens_hc = np.std(ensemble_hc, ddof=1) if ensemble_hc else np.nan
    mean_mlp_hc = np.mean(mlp_hc) if mlp_hc else np.nan
    std_mlp_hc = np.std(mlp_hc, ddof=1) if mlp_hc else np.nan
    mean_svm_hc = np.mean(svm_hc) if svm_hc else np.nan
    std_svm_hc = np.std(svm_hc, ddof=1) if svm_hc else np.nan

    mean_ens_cvd = np.mean(ensemble_cvd) if ensemble_cvd else np.nan
    std_ens_cvd = np.std(ensemble_cvd, ddof=1) if ensemble_cvd else np.nan
    mean_mlp_cvd = np.mean(mlp_cvd) if mlp_cvd else np.nan
    std_mlp_cvd = np.std(mlp_cvd, ddof=1) if mlp_cvd else np.nan
    mean_svm_cvd = np.mean(svm_cvd) if svm_cvd else np.nan
    std_svm_cvd = np.std(svm_cvd, ddof=1) if svm_cvd else np.nan

    roi_name = roi_display[roi]
    print(f"| {roi_name:4s} | {mean_ens_hc:.1f} ± {std_ens_hc:.1f} | {mean_mlp_hc:.1f} ± {std_mlp_hc:.1f} | {mean_svm_hc:.1f} ± {std_svm_hc:.1f} | "
          f"{mean_ens_cvd:.1f} ± {std_ens_cvd:.1f} | {mean_mlp_cvd:.1f} ± {std_mlp_cvd:.1f} | {mean_svm_cvd:.1f} ± {std_svm_cvd:.1f} |")

# ============================================================================
# 4. Alignment Comparison (FE_Ensemble)
# ============================================================================

print("\n### Alignment Comparison (FE_Ensemble)")
print("\n**HC Group Mean:**\n")
print("| ROI | Raw | Procrustes | SRM |")
print("|-----|-----|------------|-----|")

for roi in rois:
    means = {}
    stds = {}

    for alignment in alignments:
        values = []
        if 'FE_Ensemble' in results[alignment]:
            for subj_id in subjects_hc:
                if roi in results[alignment]['FE_Ensemble'].get(subj_id, {}):
                    values.append(results[alignment]['FE_Ensemble'][subj_id][roi])

        means[alignment] = np.mean(values) if values else np.nan
        stds[alignment] = np.std(values, ddof=1) if values else np.nan

    roi_name = roi_display[roi]
    print(f"| {roi_name:4s} | {means['raw']:.1f} ± {stds['raw']:.1f} | {means['procrustes']:.1f} ± {stds['procrustes']:.1f} | {means['srm']:.1f} ± {stds['srm']:.1f} |")

print("\n**CVD Group Mean:**\n")
print("| ROI | Raw | Procrustes | SRM |")
print("|-----|-----|------------|-----|")

for roi in rois:
    means = {}
    stds = {}

    for alignment in alignments:
        values = []
        if 'FE_Ensemble' in results[alignment]:
            for subj_id in subjects_cvd:
                if roi in results[alignment]['FE_Ensemble'].get(subj_id, {}):
                    values.append(results[alignment]['FE_Ensemble'][subj_id][roi])

        means[alignment] = np.mean(values) if values else np.nan
        stds[alignment] = np.std(values, ddof=1) if values else np.nan

    roi_name = roi_display[roi]
    print(f"| {roi_name:4s} | {means['raw']:.1f} ± {stds['raw']:.1f} | {means['procrustes']:.1f} ± {stds['procrustes']:.1f} | {means['srm']:.1f} ± {stds['srm']:.1f} |")

# ============================================================================
# 5. All Available Decoders (Procrustes)
# ============================================================================

print("\n### All Decoder Methods (Procrustes, HC Mean)")
print("\nAvailable decoders:")
if 'procrustes' in results:
    for decoder in sorted(results['procrustes'].keys()):
        print(f"  - {decoder}")

    print("\n| ROI | " + " | ".join(sorted(results['procrustes'].keys())) + " |")
    print("|-----" + "|-------" * len(results['procrustes']) + "|")

    for roi in rois:
        roi_name = roi_display[roi]
        row = f"| {roi_name:4s} "
        for decoder in sorted(results['procrustes'].keys()):
            values = []
            for subj_id in subjects_hc:
                if roi in results['procrustes'][decoder].get(subj_id, {}):
                    values.append(results['procrustes'][decoder][subj_id][roi])

            mean_val = np.mean(values) if values else np.nan
            std_val = np.std(values, ddof=1) if values else np.nan
            row += f"| {mean_val:.1f} ± {std_val:.1f} "

        print(row + "|")

print("\n" + "="*80)
print("END OF REPORT")
print("="*80)
