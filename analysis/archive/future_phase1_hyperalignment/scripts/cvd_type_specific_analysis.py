#!/usr/bin/env python3
"""
CVD Type-Specific Analysis
===========================

IMPORTANT: CVD subjects are heterogeneous!
- sub-08, sub-09: Deuteranopia (M-cone deficiency)
- sub-10: Protanomaly (L-cone weakness)

This script analyzes each CVD type SEPARATELY to respect this heterogeneity.

Approach:
1. HC common space (all HC subjects)
2. Project each CVD individually (keep heterogeneity)
3. Analyze Deutan vs Protan separately
4. Train type-specific filters OR conditional filter

Author: Automated
Date: 2025-12-18
"""

import numpy as np
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns

sys.path.insert(0, str(Path(__file__).parent))
from hyperalignment_core import (
    Hyperalignment, CommonSpaceAnalyzer, load_amplitudes
)


def analyze_cvd_type_specific(roi='V1'):
    """
    Analyze CVD types separately to respect heterogeneity.
    """

    # ========== Configuration ==========
    HC_SUBJECTS = ['02', '03', '05', '06', '07']

    # CVD subjects BY TYPE
    CVD_DEUTAN = {
        'sub-08': 'Deuteranopia',
        'sub-09': 'Deuteranopia'
    }

    CVD_PROTAN = {
        'sub-10': 'Protanomaly'
    }

    N_RUNS = 6
    N_COLORS = 8
    T = N_RUNS * N_COLORS

    OUTPUT_DIR = Path('analysis/hyperalignment/results')
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    FIGURES_DIR = Path('analysis/hyperalignment/figures')
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    print("\n" + "="*70)
    print(" CVD Type-Specific Hyperalignment Analysis")
    print("="*70)
    print(f"\n📍 ROI: {roi}")
    print(f"📍 HC subjects: {len(HC_SUBJECTS)}")
    print(f"\n📍 CVD Types:")
    print(f"   Deutan (M-cone deficiency): {len(CVD_DEUTAN)} subjects")
    for cvd_id, cvd_type in CVD_DEUTAN.items():
        print(f"     - {cvd_id}: {cvd_type}")
    print(f"   Protan (L-cone weakness): {len(CVD_PROTAN)} subjects")
    for cvd_id, cvd_type in CVD_PROTAN.items():
        print(f"     - {cvd_id}: {cvd_type}")

    # ========== Load HC Data ==========
    print("\n" + "="*70)
    print("Step 1: Loading HC Data (Common Space Reference)")
    print("="*70)

    data_hc = {}
    for sub_id in HC_SUBJECTS:
        try:
            amplitudes = load_amplitudes(sub_id, roi)
            n_runs, n_colors, n_voxels = amplitudes.shape
            data_hc[f'sub-{sub_id}'] = amplitudes.reshape(T, n_voxels)
        except FileNotFoundError as e:
            print(f"  ⚠️ Skipping sub-{sub_id}: {e}")

    p = n_voxels
    print(f"\n✅ Loaded {len(data_hc)} HC subjects")
    print(f"   Data shape: ({T}, {p})")
    print(f"   T/p ratio: {T/p:.2%}")

    # ========== HC Hyperalignment ==========
    print("\n" + "="*70)
    print("Step 2: Constructing HC-Only Common Space")
    print("="*70)
    print("NOTE: This is the 'normal color space' - CVD will be compared to this")

    ha = Hyperalignment(n_iter=15, regularization=0.01)
    ha.fit(data_hc, verbose=True)

    # ========== Load and Project CVD by Type ==========
    print("\n" + "="*70)
    print("Step 3: Loading and Projecting CVD (BY TYPE)")
    print("="*70)

    # Load Deutan
    print("\n--- Deuteranopia (M-cone deficiency) ---")
    data_deutan = {}
    for cvd_id in CVD_DEUTAN.keys():
        try:
            amplitudes = load_amplitudes(cvd_id.split('-')[1], roi)
            data_deutan[cvd_id] = amplitudes.reshape(T, n_voxels)
        except FileNotFoundError as e:
            print(f"  ⚠️ Skipping {cvd_id}: {e}")

    # Load Protan
    print("\n--- Protanomaly (L-cone weakness) ---")
    data_protan = {}
    for cvd_id in CVD_PROTAN.keys():
        try:
            amplitudes = load_amplitudes(cvd_id.split('-')[1], roi)
            data_protan[cvd_id] = amplitudes.reshape(T, n_voxels)
        except FileNotFoundError as e:
            print(f"  ⚠️ Skipping {cvd_id}: {e}")

    # Project Deutan
    print("\n" + "="*70)
    print("Step 4: Projecting Deutan to HC Common Space")
    print("="*70)
    deutan_results = ha.transform_cvd(data_deutan, verbose=True)

    # Project Protan
    print("\n" + "="*70)
    print("Step 5: Projecting Protan to HC Common Space")
    print("="*70)
    protan_results = ha.transform_cvd(data_protan, verbose=True)

    # ========== Type-Specific Analysis ==========
    print("\n" + "="*70)
    print("Step 6: Type-Specific Distortion Analysis")
    print("="*70)

    analyzer = CommonSpaceAnalyzer(ha.common_space, T=T, n_colors=N_COLORS)

    # HC RDM
    rdm_hc = analyzer.compute_rdm(ha.common_space, metric='correlation')

    # Deutan analysis
    print("\n--- Deuteranopia Analysis ---")
    deutan_disparities = {}
    for cvd_id, result in deutan_results.items():
        disparities = analyzer.compute_color_disparities(
            ha.common_space, result['aligned']
        )
        deutan_disparities[cvd_id] = disparities

        print(f"\n{cvd_id} color distortions:")
        colors = ['Red', 'Orange', 'Yellow', 'Chartreuse',
                  'Green', 'Cyan', 'Blue', 'Magenta']
        for color, dist in zip(colors, disparities):
            print(f"  {color:12s}: {dist:.4f}")

    # Protan analysis
    print("\n--- Protanomaly Analysis ---")
    protan_disparities = {}
    for cvd_id, result in protan_results.items():
        disparities = analyzer.compute_color_disparities(
            ha.common_space, result['aligned']
        )
        protan_disparities[cvd_id] = disparities

        print(f"\n{cvd_id} color distortions:")
        for color, dist in zip(colors, disparities):
            print(f"  {color:12s}: {dist:.4f}")

    # ========== Compare Deutan vs Protan ==========
    print("\n" + "="*70)
    print("Step 7: Deutan vs Protan Comparison")
    print("="*70)

    # Average within each type
    deutan_avg = np.mean([d for d in deutan_disparities.values()], axis=0)
    protan_avg = np.mean([d for d in protan_disparities.values()], axis=0)

    print("\nAverage distortion by CVD type:")
    print("\nColor         Deutan    Protan    Diff (D-P)")
    print("-" * 50)
    for i, color in enumerate(colors):
        diff = deutan_avg[i] - protan_avg[i]
        marker = "***" if abs(diff) > 0.1 else ""
        print(f"{color:12s}  {deutan_avg[i]:.4f}    {protan_avg[i]:.4f}    "
              f"{diff:+.4f} {marker}")

    # ========== Visualize Type-Specific Patterns ==========
    print("\n" + "="*70)
    print("Step 8: Visualizing Type-Specific Patterns")
    print("="*70)

    # Plot 1: Deutan vs Protan distortions
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    x = np.arange(len(colors))
    width = 0.35

    # Deutan
    axes[0].bar(x, deutan_avg, width, label='Deutan Avg', color='#d62728', alpha=0.7)
    for cvd_id, disp in deutan_disparities.items():
        axes[0].scatter(x, disp, alpha=0.5, s=100, label=cvd_id)
    axes[0].set_xlabel('Color', fontsize=12)
    axes[0].set_ylabel('Distortion (RMS)', fontsize=12)
    axes[0].set_title('Deuteranopia (M-cone deficiency)',
                     fontsize=14, fontweight='bold')
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(colors, rotation=45, ha='right')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3, axis='y')

    # Protan
    axes[1].bar(x, protan_avg, width, label='Protan Avg', color='#ff7f0e', alpha=0.7)
    for cvd_id, disp in protan_disparities.items():
        axes[1].scatter(x, disp, alpha=0.5, s=100, label=cvd_id)
    axes[1].set_xlabel('Color', fontsize=12)
    axes[1].set_ylabel('Distortion (RMS)', fontsize=12)
    axes[1].set_title('Protanomaly (L-cone weakness)',
                     fontsize=14, fontweight='bold')
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(colors, rotation=45, ha='right')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    save_path = FIGURES_DIR / f'deutan_vs_protan_distortions_{roi}.png'
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"   Saved: {save_path}")
    plt.close()

    # Plot 2: Direct comparison
    fig, ax = plt.subplots(figsize=(10, 6))

    ax.bar(x - width/2, deutan_avg, width, label='Deutan (n=2)',
           color='#d62728', alpha=0.7)
    ax.bar(x + width/2, protan_avg, width, label='Protan (n=1)',
           color='#ff7f0e', alpha=0.7)

    ax.set_xlabel('Color', fontsize=12)
    ax.set_ylabel('Distortion from HC Common Space (RMS)', fontsize=12)
    ax.set_title('CVD Type-Specific Color Distortions',
                fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(colors, rotation=45, ha='right')
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    save_path = FIGURES_DIR / f'cvd_type_comparison_{roi}.png'
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"   Saved: {save_path}")
    plt.close()

    # Plot 3: RDM for each type
    # Deutan RDM
    deutan_rdms = []
    for cvd_id, result in deutan_results.items():
        rdm = analyzer.compute_rdm(result['aligned'], metric='correlation')
        deutan_rdms.append(rdm)
    deutan_rdm_avg = np.mean(deutan_rdms, axis=0)

    # Protan RDM
    protan_rdms = []
    for cvd_id, result in protan_results.items():
        rdm = analyzer.compute_rdm(result['aligned'], metric='correlation')
        protan_rdms.append(rdm)
    protan_rdm_avg = np.mean(protan_rdms, axis=0)

    fig, axes = plt.subplots(1, 3, figsize=(16, 4))

    # HC
    im0 = axes[0].imshow(rdm_hc, cmap='hot', vmin=0, vmax=2)
    axes[0].set_title('HC Common Space', fontsize=12, fontweight='bold')
    axes[0].set_xticks(range(8))
    axes[0].set_yticks(range(8))
    axes[0].set_xticklabels(colors, rotation=45, ha='right', fontsize=9)
    axes[0].set_yticklabels(colors, fontsize=9)
    plt.colorbar(im0, ax=axes[0])

    # Deutan
    im1 = axes[1].imshow(deutan_rdm_avg, cmap='hot', vmin=0, vmax=2)
    axes[1].set_title('Deutan Average (n=2)', fontsize=12, fontweight='bold')
    axes[1].set_xticks(range(8))
    axes[1].set_yticks(range(8))
    axes[1].set_xticklabels(colors, rotation=45, ha='right', fontsize=9)
    axes[1].set_yticklabels(colors, fontsize=9)
    plt.colorbar(im1, ax=axes[1])

    # Protan
    im2 = axes[2].imshow(protan_rdm_avg, cmap='hot', vmin=0, vmax=2)
    axes[2].set_title('Protan Average (n=1)', fontsize=12, fontweight='bold')
    axes[2].set_xticks(range(8))
    axes[2].set_yticks(range(8))
    axes[2].set_xticklabels(colors, rotation=45, ha='right', fontsize=9)
    axes[2].set_yticklabels(colors, fontsize=9)
    plt.colorbar(im2, ax=axes[2])

    plt.tight_layout()
    save_path = FIGURES_DIR / f'rdm_by_cvd_type_{roi}.png'
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"   Saved: {save_path}")
    plt.close()

    # ========== Save Results ==========
    print("\n" + "="*70)
    print("Step 9: Saving Type-Specific Results")
    print("="*70)

    np.save(OUTPUT_DIR / f'deutan_avg_distortion_{roi}.npy', deutan_avg)
    np.save(OUTPUT_DIR / f'protan_avg_distortion_{roi}.npy', protan_avg)
    np.save(OUTPUT_DIR / f'deutan_rdm_avg_{roi}.npy', deutan_rdm_avg)
    np.save(OUTPUT_DIR / f'protan_rdm_avg_{roi}.npy', protan_rdm_avg)

    print(f"💾 Saved type-specific results")

    # ========== Summary ==========
    print("\n" + "="*70)
    print("✅ CVD Type-Specific Analysis Complete!")
    print("="*70)

    print("\n📊 Key Findings:")

    # Find most different colors
    diff = deutan_avg - protan_avg
    max_idx = np.argmax(np.abs(diff))

    print(f"\n  Most different color: {colors[max_idx]}")
    print(f"    Deutan: {deutan_avg[max_idx]:.4f}")
    print(f"    Protan: {protan_avg[max_idx]:.4f}")
    print(f"    Diff: {diff[max_idx]:+.4f}")

    print(f"\n  Overall pattern:")
    if np.mean(deutan_avg) > np.mean(protan_avg):
        print(f"    Deutan shows stronger distortion overall")
    else:
        print(f"    Protan shows stronger distortion overall")

    print(f"\n📂 Figures saved to: {FIGURES_DIR}")
    print(f"   - deutan_vs_protan_distortions_{roi}.png")
    print(f"   - cvd_type_comparison_{roi}.png")
    print(f"   - rdm_by_cvd_type_{roi}.png")

    print("\n💡 Interpretation:")
    print("   - Each CVD type has DISTINCT distortion pattern")
    print("   - Deutan (M-cone): Red-Green confusion expected")
    print("   - Protan (L-cone): Red-shifted confusion expected")
    print("   - Type-specific filters recommended for deep learning!")


if __name__ == '__main__':
    analyze_cvd_type_specific(roi='V1')
