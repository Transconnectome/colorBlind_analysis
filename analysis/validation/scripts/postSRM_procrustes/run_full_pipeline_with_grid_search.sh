#!/bin/bash
# Full Pipeline: Grid Search + Optimal Pipeline + SRM Comparison
#
# This script runs:
# 1. Grid search to find optimal dimensions (PCA and ANOVA)
# 2. Full pipeline (Steps 1-5) with optimal configurations
# 3. SRM metrics computation (if SRM results exist)
# 4. Method comparison (Procrustes-PCA vs Procrustes-ANOVA vs SRM)

set -e

echo "=========================================="
echo "Full Pipeline with Grid Search"
echo "=========================================="
echo ""

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

# Activate conda environment
echo "Activating nilearn environment..."
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate nilearn

# Check if conda activate was successful
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to activate nilearn environment"
    exit 1
fi

echo "✓ Environment activated"
echo ""

# ROIs to process
ROIS=(V1 V2 V3 hV4)

# ============================================================================
# PHASE 1: Grid Search for Optimal Dimensions
# ============================================================================

echo "=========================================="
echo "PHASE 1: Grid Search"
echo "=========================================="
echo ""

# Ask user if they want to run grid search or use existing results
read -p "Run grid search? This will take several hours. (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Running grid search for all ROIs..."
    echo ""

    for ROI in "${ROIS[@]}"; do
        echo "=========================================="
        echo "Grid Search: ${ROI}"
        echo "=========================================="

        # Run both PCA and ANOVA grid search
        python step0_determine_optimal_dimensions.py \
            --roi "${ROI}" \
            --method both \
            --baseline-dir "/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/phase1_preprocess_decoding/results/baseline" \
            --output-dir "./results/step0_grid_search"

        if [ $? -ne 0 ]; then
            echo "ERROR: Grid search failed for ${ROI}"
            exit 1
        fi

        echo ""
    done

    echo "✓ Grid search completed for all ROIs"
    echo ""
else
    echo "Skipping grid search. Using existing optimal_dimensions.json"
    echo ""

    # Check if optimal_dimensions.json exists
    if [ ! -f "results/step0_grid_search/optimal_dimensions.json" ]; then
        echo "ERROR: optimal_dimensions.json not found!"
        echo "Please run grid search first or create the file manually."
        exit 1
    fi
fi

# Load optimal dimensions
echo "Loading optimal dimensions..."
OPTIMAL_CONFIG="results/step0_grid_search/optimal_dimensions.json"

if [ ! -f "${OPTIMAL_CONFIG}" ]; then
    echo "ERROR: Optimal config not found: ${OPTIMAL_CONFIG}"
    exit 1
fi

echo "✓ Optimal dimensions loaded"
echo ""

# ============================================================================
# PHASE 2: Full Pipeline with Optimal Configurations
# ============================================================================

echo "=========================================="
echo "PHASE 2: Full Pipeline (Optimal Config)"
echo "=========================================="
echo ""

# Extract optimal parameters and run full pipeline
python << 'EOF'
import json
import subprocess
from pathlib import Path

config_file = Path("results/step0_grid_search/optimal_dimensions.json")
with open(config_file) as f:
    config = json.load(f)

print("Optimal configurations:")
print(json.dumps(config, indent=2))
print("")

rois = ['V1', 'V2', 'V3', 'hV4']
baseline_dir = "/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/phase1_preprocess_decoding/results/baseline"
subjects = ['01', '02', '03', '04', '05', '06', '08', '09', '10']

for method in ['pca', 'anova']:
    if method not in config:
        print(f"WARNING: No optimal config for {method}, skipping")
        continue

    print(f"\n{'='*80}")
    print(f"{method.upper()} Pipeline with Optimal Dimensions")
    print(f"{'='*80}\n")

    for roi in rois:
        if roi not in config[method]:
            print(f"WARNING: No optimal config for {roi} {method}, skipping")
            continue

        optimal_param = config[method][roi]['n_components'] if method == 'pca' else config[method][roi]['k_voxels']

        print(f"\n{roi} - {method.upper()} ({optimal_param}):")
        print("-" * 40)

        # Step 1: Dimension reduction for all subjects
        print(f"  Step 1: Dimension reduction ({len(subjects)} subjects)...")

        step1_dir = f"results/step1_{method}_optimal"

        for subj in subjects:
            if method == 'pca':
                cmd = [
                    'python', 'step1a_dimension_reduction_pca.py',
                    '--subject', subj,
                    '--roi', roi,
                    '--n-components', str(optimal_param),
                    '--baseline-dir', baseline_dir,
                    '--output-dir', step1_dir
                ]
            else:
                cmd = [
                    'python', 'step1b_voxel_selection_anova.py',
                    '--subject', subj,
                    '--roi', roi,
                    '--k', str(optimal_param),
                    '--baseline-dir', baseline_dir,
                    '--output-dir', step1_dir
                ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"    ERROR: sub-{subj} failed")
                print(result.stderr)
                exit(1)

        print(f"    ✓ Completed")

        # Step 2: Procrustes
        print(f"  Step 2: Procrustes alignment...")

        cmd = [
            'python', 'step2_iterative_procrustes.py',
            '--roi', roi,
            '--method', method,
            '--input-dir', step1_dir,
            '--output-dir', f'results/step2_procrustes_{method}_optimal'
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"    ERROR: Procrustes failed")
            print(result.stderr)
            exit(1)

        print(f"    ✓ Completed")

        # Step 3: RDMs
        print(f"  Step 3: Crossnobis RDMs ({len(subjects)} subjects)...")

        for subj in subjects:
            cmd = [
                'python', 'step3_compute_rdms_crossnobis.py',
                '--subject', subj,
                '--roi', roi,
                '--method', method,
                '--input-dir', f'results/step2_procrustes_{method}_optimal',
                '--output-dir', f'results/step3_rdms_{method}_optimal'
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"    ERROR: sub-{subj} RDM failed")
                exit(1)

        print(f"    ✓ Completed")

        # Step 4: Geometric metrics
        print(f"  Step 4: Geometric metrics...")

        cmd = [
            'python', 'step4_geometric_metrics.py',
            '--roi', roi,
            '--method', method,
            '--rdm-dir', f'results/step3_rdms_{method}_optimal',
            '--output-dir', f'results/step4_metrics_{method}_optimal'
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"    ERROR: Metrics computation failed")
            print(result.stderr)
            exit(1)

        print(f"    ✓ Completed")

        # Step 5: Visualization
        print(f"  Step 5: Visualization...")

        cmd = [
            'python', 'step5_visualize_report.py',
            '--roi', roi,
            '--method', method,
            '--metrics-dir', f'results/step4_metrics_{method}_optimal',
            '--rdm-dir', f'results/step3_rdms_{method}_optimal',
            '--procrustes-dir', f'results/step2_procrustes_{method}_optimal',
            '--output-dir', f'results/step5_visualizations_{method}_optimal'
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"    WARNING: Visualization failed (non-critical)")
        else:
            print(f"    ✓ Completed")

print(f"\n{'='*80}")
print("Full pipeline completed successfully!")
print(f"{'='*80}\n")
EOF

if [ $? -ne 0 ]; then
    echo "ERROR: Full pipeline failed"
    exit 1
fi

# ============================================================================
# PHASE 3: SRM Metrics Computation (if SRM results exist)
# ============================================================================

echo "=========================================="
echo "PHASE 3: SRM Metrics"
echo "=========================================="
echo ""

SRM_RESULTS_DIR="../srm/results/srm_between_subject"

if [ -d "${SRM_RESULTS_DIR}" ]; then
    echo "SRM results found. Computing geometric metrics..."
    echo ""

    for ROI in "${ROIS[@]}"; do
        echo "Computing SRM metrics for ${ROI}..."

        python compute_srm_metrics.py \
            --roi "${ROI}" \
            --srm-dir "${SRM_RESULTS_DIR}" \
            --output-dir "./results/srm_metrics"

        if [ $? -eq 0 ]; then
            echo "  ✓ ${ROI} metrics computed"
        else
            echo "  ⚠ ${ROI} metrics computation failed (may not have SRM results)"
        fi

        echo ""
    done
else
    echo "SRM results not found at: ${SRM_RESULTS_DIR}"
    echo "Skipping SRM metrics computation."
    echo ""
fi

# ============================================================================
# PHASE 4: Method Comparison
# ============================================================================

echo "=========================================="
echo "PHASE 4: Method Comparison"
echo "=========================================="
echo ""

for ROI in "${ROIS[@]}"; do
    echo "Comparing methods for ${ROI}..."

    # Compare Procrustes-PCA vs Procrustes-ANOVA
    python compare_procrustes_methods.py \
        --roi "${ROI}" \
        --pca-dir "results/step4_metrics_pca_optimal" \
        --anova-dir "results/step4_metrics_anova_optimal" \
        --output-dir "results/method_comparison"

    # Compare with SRM (if available)
    if [ -d "results/srm_metrics/${ROI}" ]; then
        python compare_procrustes_vs_srm.py \
            --roi "${ROI}" \
            --procrustes-dir "results/step4_metrics_pca_optimal" \
            --srm-dir "results/srm_metrics" \
            --output-dir "results/srm_comparison"

        if [ $? -eq 0 ]; then
            echo "  ✓ ${ROI} SRM comparison completed"
        fi
    fi

    echo ""
done

echo "✓ Method comparison completed"
echo ""

# ============================================================================
# Summary
# ============================================================================

echo "=========================================="
echo "Pipeline Summary"
echo "=========================================="
echo ""
echo "Results directories:"
echo "  - Grid search: results/step0_grid_search/"
echo "  - PCA pipeline: results/step*_pca_optimal/"
echo "  - ANOVA pipeline: results/step*_anova_optimal/"
echo "  - Method comparison: results/method_comparison/"
echo "  - SRM comparison: results/srm_comparison/"
echo ""
echo "Key files:"
echo "  - Optimal dimensions: results/step0_grid_search/optimal_dimensions.json"
echo "  - HC vs CVD statistics: results/step4_metrics_*/*/hc_vs_cvd_statistics.json"
echo "  - Visualizations: results/step5_visualizations_*/"
echo ""
echo "Next steps:"
echo "  1. Review optimal dimensions: cat results/step0_grid_search/optimal_dimensions.json"
echo "  2. Check HC-CVD differences: cat results/step4_metrics_pca_optimal/*/hc_vs_cvd_statistics.json"
echo "  3. View visualizations: open results/step5_visualizations_pca_optimal/*_pca_diagnostics.png"
echo "  4. Compare methods: open results/method_comparison/*_comparison.png"
echo ""
echo "✅ All done!"
echo ""
