#!/bin/bash
#SBATCH --job-name=group_comprehensive
#SBATCH --nodelist=node2
#SBATCH --output=logs/group_level/%x_%A_%a.out
#SBATCH --error=logs/group_level/%x_%A_%a.err
#SBATCH --time=04:00:00
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --array=0-3

# ============================================================================
# Comprehensive Group-level Analysis
# ============================================================================
#
# This script runs comprehensive group-level analysis with three statistical
# approaches for color vision fMRI data:
#
#   1. Common voxel identification (SNR-based top-K selection)
#   2. Comprehensive statistical analysis:
#      - Option A: One-sample t-test vs 0 (activation exists?)
#      - Option B-1: Each color vs others (color selectivity)
#      - Option B-2: Pairwise contrasts (28 pairs - critical for 적록색맹)
#   3. Union voxel approach + classification/reconstruction (LOSO-CV)
#
# Usage:
#   sbatch run_group_level_comprehensive.sbatch
#
# Array job indices:
#   0: V1
#   1: V2
#   2: V3
#   3: hV4
#
# Output:
#   derivatives/group_level/{timestamp}/{roi}/
#   ├── common_voxels/
#   │   ├── group_amplitudes_z.npy
#   │   └── preprocessing_info.json
#   └── comprehensive/
#       ├── statistics/
#       │   ├── option_a_vs_zero.npz
#       │   ├── option_b1_selectivity.npz
#       │   ├── option_b2_pairwise/  (28 color pairs)
#       │   └── union_voxels.npz
#       ├── figures/
#       │   ├── pairwise_contrasts_grid.png  ← Critical for color blindness
#       │   ├── union_voxels_breakdown.png
#       │   ├── circular_color_space_union.png
#       │   └── confusion_matrix_union.png
#       └── performance/
#           └── classification_results.csv
#
# ============================================================================

# Activate conda environment
source ~/.bashrc
conda activate nilearn

# Configuration
ROIS=("V1" "V2" "V3" "hV4")
ROI=${ROIS[$SLURM_ARRAY_TASK_ID]}

TIMESTAMP="baseline32_deob_determin"
DATASET="deoblique_v2"

# ============================================================================
# Subject Selection Strategy
# ============================================================================
# Based on validation results (2025-12-13):
#   Deterministic preprocessing now includes sub-01 and sub-02!
#   V1: Available subjects = 01, 02, 03, 05, 06, 07 (6 subjects)
#   V2: Available subjects = 01, 02, 03, 05, 06, 07 (6 subjects)
#   V3: Available subjects = 01, 02, 03, 05, 06, 07 (6 subjects)
#   hV4: Available subjects = 01, 02, 03, 05, 06, 07 (6 subjects)
#
# Using all 6 available subjects
# ============================================================================

SUBJECTS="01 02 03 05 06 07"  # 6 subjects available for ALL ROIs

echo "================================================================================"
echo "Comprehensive Group-level Analysis"
echo "================================================================================"
echo "ROI: $ROI"
echo "Timestamp: $TIMESTAMP"
echo "Dataset: $DATASET"
echo "Subjects: $SUBJECTS"
echo "Start time: $(date)"
echo "================================================================================"

# Create log directory
mkdir -p logs/group_level

# ============================================================================
# Step 1: Common Voxel Identification (SNR-based Top-K Selection)
# ============================================================================
echo ""
echo "Step 1: Identifying common voxels (SNR-based top-K selection)..."
echo "----------------------------------------------------------------------------"

python group_level_common_voxels.py \
    --roi $ROI \
    --timestamp $TIMESTAMP \
    --dataset $DATASET \
    --subjects $SUBJECTS \
    --fdr-alpha 0.05 \
    --min-colors 1

if [ $? -ne 0 ]; then
    echo "ERROR: Common voxel identification failed"
    exit 1
fi

echo "✓ Common voxel identification complete"

# ============================================================================
# Step 2: Comprehensive Statistical Analysis
# ============================================================================
echo ""
echo "Step 2: Running comprehensive statistical analysis..."
echo "----------------------------------------------------------------------------"
echo "  - Option A: One-sample t-test vs 0 (activation exists?)"
echo "  - Option B-1: Each color vs others (color selectivity)"
echo "  - Option B-2: Pairwise contrasts (28 pairs for 적록색맹 research)"
echo "  - Voxel selection: |t| > 5.0 (instead of FDR - more power with N=6)"
echo "  - Union voxel approach + classification/reconstruction (LOSO-CV)"
echo ""

python group_level_analysis_comprehensive.py \
    --roi $ROI \
    --timestamp $TIMESTAMP \
    --dataset $DATASET \
    --subjects $SUBJECTS \
    --use-t-threshold \
    --t-threshold 5.0

if [ $? -ne 0 ]; then
    echo "ERROR: Comprehensive analysis failed"
    exit 1
fi

echo "✓ Comprehensive analysis complete"

# ============================================================================
# Summary
# ============================================================================
echo ""
echo "================================================================================"
echo "Comprehensive Group-level Analysis Complete for ROI: $ROI"
echo "================================================================================"
echo "End time: $(date)"
echo ""
echo "Results saved to:"
echo "  derivatives/group_level/$TIMESTAMP/$ROI/common_voxels/"
echo "  derivatives/group_level/$TIMESTAMP/$ROI/comprehensive/"
echo ""
echo "Key outputs:"
echo "  - statistics/option_a_vs_zero.npz               (activation test)"
echo "  - statistics/option_b1_selectivity.npz          (color selectivity)"
echo "  - statistics/option_b2_pairwise/*.npz           (28 color pairs)"
echo "  - statistics/union_voxels.npz                   (union of all significant voxels)"
echo "  - pca/pca_results.npz                           (PCA loadings & variance)"
echo "  - figures/pairwise_contrasts_grid.png           (28 color pairs - critical!)"
echo "  - figures/union_voxels_breakdown.png            (union composition)"
echo "  - figures/circular_color_space_union.png        (reconstruction quality)"
echo "  - figures/confusion_matrix_union.png            (classification quality)"
echo "  - figures/pca_explained_variance.png            (PCA scree plot)"
echo "  - figures/pca_loadings_heatmap.png              (PCA loadings)"
echo "  - figures/pca_classification_performance.png    (PCA performance)"
echo "  - performance/classification_results.csv        (Union voxels LOSO-CV)"
echo "  - performance/pca_performance.csv               (PCA LOSO-CV)"
echo "================================================================================"
