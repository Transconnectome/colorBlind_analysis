#!/usr/bin/env python3
"""
Run Hyperalignment Analysis
============================

1. Construct HC-only common space
2. Project CVD subjects
3. Analyze distortions in common space

Author: Automated
Date: 2025-12-18
"""

import numpy as np
import sys
from pathlib import Path
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))
from hyperalignment_core import (
    Hyperalignment, CommonSpaceAnalyzer, load_amplitudes
)


def main():
    """Main analysis pipeline."""

    # ========== Configuration ==========
    ROI = 'V1'
    HC_SUBJECTS = ['02', '03', '05', '06', '07']
    CVD_SUBJECTS = ['08', '09', '10']
    N_RUNS = 6
    N_COLORS = 8
    T = N_RUNS * N_COLORS  # 48

    OUTPUT_DIR = Path('analysis/hyperalignment/results')
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    FIGURES_DIR = Path('analysis/hyperalignment/figures')
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    print("\n" + "="*70)
    print(" Hyperalignment Analysis: HC Common Space + CVD Projection")
    print("="*70)
    print(f"\n📍 ROI: {ROI}")
    print(f"📍 HC subjects: {len(HC_SUBJECTS)}")
    print(f"📍 CVD subjects: {len(CVD_SUBJECTS)}")
    print(f"📍 T (observations): {T} = {N_RUNS} runs × {N_COLORS} colors")

    # ========== Step 1: Load HC Data ==========
    print("\n" + "="*70)
    print("Step 1: Loading HC Data")
    print("="*70)

    data_hc = {}
    for sub_id in HC_SUBJECTS:
        try:
            amplitudes = load_amplitudes(sub_id, ROI)  # (6, 8, p)
            n_runs, n_colors, n_voxels = amplitudes.shape

            # Reshape to (T, p)
            data_hc[f'sub-{sub_id}'] = amplitudes.reshape(T, n_voxels)

        except FileNotFoundError as e:
            print(f"  ⚠️ Skipping sub-{sub_id}: {e}")

    p = n_voxels
    print(f"\n✅ Loaded {len(data_hc)} HC subjects")
    print(f"   Data shape per subject: ({T}, {p})")
    print(f"   T/p ratio: {T/p:.2%}")

    # ========== Step 2: Load CVD Data ==========
    print("\n" + "="*70)
    print("Step 2: Loading CVD Data")
    print("="*70)

    data_cvd = {}
    for sub_id in CVD_SUBJECTS:
        try:
            amplitudes = load_amplitudes(sub_id, ROI)
            data_cvd[f'sub-{sub_id}'] = amplitudes.reshape(T, n_voxels)

        except FileNotFoundError as e:
            print(f"  ⚠️ Skipping sub-{sub_id}: {e}")

    print(f"\n✅ Loaded {len(data_cvd)} CVD subjects")

    # ========== Step 3: HC Hyperalignment ==========
    print("\n" + "="*70)
    print("Step 3: Constructing HC Common Space")
    print("="*70)

    ha = Hyperalignment(n_iter=15, regularization=0.01)
    ha.fit(data_hc, verbose=True)

    # Save common space
    np.save(OUTPUT_DIR / f'common_space_{ROI}.npy', ha.common_space)
    print(f"\n💾 Saved: {OUTPUT_DIR / f'common_space_{ROI}.npy'}")

    # Plot convergence
    ha.plot_convergence(save_path=FIGURES_DIR / f'convergence_{ROI}.png')

    # ========== Step 4: CVD Projection ==========
    print("\n" + "="*70)
    print("Step 4: Projecting CVD to Common Space")
    print("="*70)

    cvd_results = ha.transform_cvd(data_cvd, verbose=True)

    # Save CVD aligned data and rotations
    for cvd_id, result in cvd_results.items():
        np.save(OUTPUT_DIR / f'{cvd_id}_aligned_{ROI}.npy', result['aligned'])
        np.save(OUTPUT_DIR / f'{cvd_id}_rotation_{ROI}.npy', result['rotation'])

    print(f"\n💾 Saved CVD aligned data and rotations")

    # ========== Step 5: RDM Analysis ==========
    print("\n" + "="*70)
    print("Step 5: RDM Analysis in Common Space")
    print("="*70)

    analyzer = CommonSpaceAnalyzer(ha.common_space, T=T, n_colors=N_COLORS)

    # HC RDM (in common space)
    rdm_hc = analyzer.compute_rdm(ha.common_space, metric='correlation')
    np.save(OUTPUT_DIR / f'rdm_hc_{ROI}.npy', rdm_hc)
    print(f"\n✅ HC RDM computed")

    # CVD RDMs and comparisons
    rdm_cvd_dict = {}
    for cvd_id, result in cvd_results.items():
        rdm_cvd = analyzer.compute_rdm(result['aligned'], metric='correlation')
        rdm_cvd_dict[cvd_id] = rdm_cvd
        np.save(OUTPUT_DIR / f'rdm_{cvd_id}_{ROI}.npy', rdm_cvd)

        # Plot comparison
        analyzer.plot_rdm_comparison(
            rdm_hc, rdm_cvd, cvd_id,
            save_path=FIGURES_DIR / f'rdm_comparison_{cvd_id}_{ROI}.png'
        )

    print(f"\n✅ CVD RDMs computed and compared")

    # ========== Step 6: Color Distortion Analysis ==========
    print("\n" + "="*70)
    print("Step 6: Color-Specific Distortion Analysis")
    print("="*70)

    disparities_dict = {}
    for cvd_id, result in cvd_results.items():
        disparities = analyzer.compute_color_disparities(
            ha.common_space, result['aligned']
        )
        disparities_dict[cvd_id] = disparities

        print(f"\n{cvd_id} distortions:")
        colors = ['Red', 'Orange', 'Yellow', 'Chartreuse',
                  'Green', 'Cyan', 'Blue', 'Magenta']
        for color, dist in zip(colors, disparities):
            print(f"  {color:12s}: {dist:.4f}")

    # Plot all together
    analyzer.plot_color_distortions(
        disparities_dict,
        save_path=FIGURES_DIR / f'color_distortions_{ROI}.png'
    )

    # Save disparities
    for cvd_id, disparities in disparities_dict.items():
        np.save(OUTPUT_DIR / f'{cvd_id}_disparities_{ROI}.npy', disparities)

    print(f"\n💾 Saved color distortions")

    # ========== Step 7: Summary Report ==========
    print("\n" + "="*70)
    print("Step 7: Summary Report")
    print("="*70)

    summary = {
        'roi': ROI,
        'n_hc': len(data_hc),
        'n_cvd': len(data_cvd),
        'T': T,
        'p': p,
        'T_over_p': T/p,
        'regularization': ha.regularization,
        'n_iter': ha.n_iter,
        'converged_iter': len(ha.convergence_history),
        'final_change': ha.convergence_history[-1],
        'cvd_disparities': {
            cvd_id: float(result['disparity'])
            for cvd_id, result in cvd_results.items()
        }
    }

    with open(OUTPUT_DIR / f'summary_{ROI}.json', 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"\n📊 Summary:")
    print(f"   Converged in {summary['converged_iter']} iterations")
    print(f"   Final change: {summary['final_change']:.6f}")
    print(f"\n   CVD disparities (to HC common space):")
    for cvd_id, disp in summary['cvd_disparities'].items():
        print(f"     {cvd_id}: {disp:.4f}")

    print(f"\n💾 Saved: {OUTPUT_DIR / f'summary_{ROI}.json'}")

    # ========== Done ==========
    print("\n" + "="*70)
    print("✅ Hyperalignment Analysis Complete!")
    print("="*70)
    print(f"\n📂 Results: {OUTPUT_DIR}")
    print(f"📂 Figures: {FIGURES_DIR}")
    print("\nNext steps:")
    print("  1. Check convergence plot")
    print("  2. Review RDM comparisons")
    print("  3. Analyze color distortion patterns")
    print("  4. Use common space for deep learning filter!")


if __name__ == '__main__':
    main()
