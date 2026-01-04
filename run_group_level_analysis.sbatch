#!/bin/bash
#SBATCH --job-name=group_level_analysis
#SBATCH --nodelist=node2
#SBATCH --output=logs/group_level/%x_%A_%a.out
#SBATCH --error=logs/group_level/%x_%A_%a.err
#SBATCH --time=04:00:00
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --array=0-3

# ============================================================================
# Group-level Analysis
# ============================================================================
#
# This script runs three group-level analyses sequentially:
#   1. Common voxel identification (group contrast + FDR correction)
#   2. PCA analysis with high-loading voxel visualization
#   3. ANOVA feature selection with reconstruction/classification
#
# Usage:
#   sbatch run_group_level_analysis.sbatch
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
#   ├── pca/
#   └── anova/
#
# ============================================================================

# Activate conda environment
source ~/.bashrc
conda activate nilearn

# Configuration
ROIS=("V1" "V2" "V3" "hV4")
ROI=${ROIS[$SLURM_ARRAY_TASK_ID]}

TIMESTAMP="baseline32_deob_determin"  # Modify as needed
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
# Using all 6 available subjects for better statistical power
# ============================================================================

SUBJECTS="01 02 03 05 06 07"  # 6 subjects available for ALL ROIs

echo "================================================================================"
echo "Group-level Analysis"
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
# Step 1: Common Voxel Identification
# ============================================================================
echo ""
echo "Step 1: Identifying common voxels (group-level contrast)..."
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
# Step 2: PCA Analysis
# ============================================================================
echo ""
echo "Step 2: Running PCA analysis with high-loading voxel visualization..."
echo "----------------------------------------------------------------------------"

python group_level_pca_analysis.py \
    --roi $ROI \
    --timestamp $TIMESTAMP \
    --dataset $DATASET \
    --n-components 50 \
    --use-common-voxels \
    --top-k-voxels 100 \
    --n-pcs-visualize 5 \
    --subjects $SUBJECTS

if [ $? -ne 0 ]; then
    echo "ERROR: PCA analysis failed"
    exit 1
fi

echo "✓ PCA analysis complete"

# ============================================================================
# Step 3: ANOVA Feature Selection
# ============================================================================
echo ""
echo "Step 3: Running ANOVA feature selection..."
echo "----------------------------------------------------------------------------"

python group_level_anova_selection.py \
    --roi $ROI \
    --timestamp $TIMESTAMP \
    --dataset $DATASET \
    --k-features 50 100 200 \
    --subjects $SUBJECTS

if [ $? -ne 0 ]; then
    echo "ERROR: ANOVA feature selection failed"
    exit 1
fi

echo "✓ ANOVA feature selection complete"

# ============================================================================
# Summary
# ============================================================================
echo ""
echo "================================================================================"
echo "Group-level Analysis Complete for ROI: $ROI"
echo "================================================================================"
echo "End time: $(date)"
echo ""
echo "Results saved to:"
echo "  derivatives/group_level/$TIMESTAMP/$ROI/common_voxels/"
echo "  derivatives/group_level/$TIMESTAMP/$ROI/pca/"
echo "  derivatives/group_level/$TIMESTAMP/$ROI/anova/"
echo "================================================================================"
