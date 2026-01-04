#!/bin/bash
#SBATCH --job-name=base_best_k
#SBATCH --output=logs/permutation_analysis/base_best_k_%A_%a.out
#SBATCH --error=logs/permutation_analysis/base_best_k_%A_%a.err
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=12:00:00
#SBATCH --array=0-8

# ============================================================================
# Re-run Baseline Analysis with Best K Values (ROI-Specific)
# ============================================================================
# FIXED: Each subject-ROI combination uses its own best k value
#
# Purpose: Baseline 결과를 best k로 재실행하여 permutation과 비교
# Total jobs: 9 (one per subject)
# Each job processes: 4 ROIs
# ============================================================================

# Activate conda environment
source ~/.bashrc
conda activate nilearn

# ============================================================================
# Helper Function: Get Best K for Subject-ROI pair from CSV
# ============================================================================
get_best_k() {
    local subject=$1
    local roi=$2
    local csv_file="results/anova_config32_determin_best_recon_summary.csv"

    # Read k value from CSV
    # Format: Subject,ROI,k,reconstruction_error,hit_rate_22_5,hit_rate_45
    local k_value=$(grep "^sub-${subject},${roi}," "$csv_file" | cut -d',' -f3)

    if [ -z "$k_value" ]; then
        echo "ERROR: Could not find k value for sub-${subject} ${roi}" >&2
        return 1
    fi

    echo "$k_value"
    return 0
}

# ============================================================================
# Configuration
# ============================================================================

# All subjects
SUBJECTS=(01 02 03 05 06 07 08 09 10)

# All ROIs
ROIS=(V1 V2 V3 hV4)

# Parse array task ID
TASK_ID=${SLURM_ARRAY_TASK_ID}
SUBJECT=${SUBJECTS[$TASK_ID]}

# Baseline timestamp (original data, not permuted)
TIMESTAMP="baseline32_deob_determin"

echo "============================================================================"
echo "Task ID: ${TASK_ID}"
echo "Subject: sub-${SUBJECT}"
echo "Processing all ROIs: ${ROIS[@]}"
echo "============================================================================"

# ============================================================================
# Main Loop: ROIs
# ============================================================================

# Loop through all ROIs
for ROI in "${ROIS[@]}"; do
    echo ""
    echo "------------------------------------------------------------------------"
    echo "Processing: sub-${SUBJECT} ${ROI}"
    echo "------------------------------------------------------------------------"

    # ====================================================================
    # FIXED: Get ROI-specific best k
    # ====================================================================
    K_FIXED=$(get_best_k ${SUBJECT} ${ROI})
    if [ $? -ne 0 ]; then
        echo "⚠️  Failed to get k value for sub-${SUBJECT} ${ROI}"
        echo "    Skipping this ROI"
        continue
    fi

    echo "Best k for sub-${SUBJECT} ${ROI}: ${K_FIXED}"
    # ====================================================================

    # Output directory
    OUTPUT_DIR="derivatives/feature_selection/permutation_analysis/anova_config32_determin"

    # Check if baseline amplitudes exist
    BASELINE_DIR="derivatives/BH2009_deoblique_v2/${TIMESTAMP}"
    AMP_DIR=$(find ${BASELINE_DIR} -name "*_sub-${SUBJECT}_${ROI}_*" -type d 2>/dev/null | head -1)

    if [ -z "$AMP_DIR" ]; then
        echo "⚠️  Baseline amplitudes NOT found for sub-${SUBJECT} ${ROI}"
        echo "    Skipping this ROI"
        continue
    fi

    echo "Found baseline amplitudes: ${AMP_DIR}"

    # Check if already processed with correct k
    RESULT_FILE="${OUTPUT_DIR}/anova_results_config32_determin_sub-${SUBJECT}_${ROI}.csv"
    if [ -f "$RESULT_FILE" ]; then
        # Extract k from existing result
        EXISTING_K=$(grep -v "^k," "$RESULT_FILE" | head -1 | cut -d',' -f1)
        if [ "$EXISTING_K" == "$K_FIXED" ]; then
            echo "✓ Already processed with correct k=${K_FIXED}"
            continue
        else
            echo "⚠️  Re-running with correct k=${K_FIXED} (previous k=${EXISTING_K})"
        fi
    fi

    # Run feature selection
    echo "Running feature selection with k_fixed=${K_FIXED}..."
    python feature_selection_anova.py \
        --subject ${SUBJECT} \
        --roi ${ROI} \
        --timestamp ${TIMESTAMP} \
        --dataset deoblique_v2 \
        --k_fixed ${K_FIXED}

    EXIT_CODE=$?

    if [ $EXIT_CODE -eq 0 ]; then
        echo "✓ Successfully completed: sub-${SUBJECT} ${ROI} (k=${K_FIXED})"
    else
        echo "✗ Failed: sub-${SUBJECT} ${ROI} (exit code: ${EXIT_CODE})"
    fi

done  # ROI loop

echo ""
echo "============================================================================"
echo "Subject ${SUBJECT} baseline analysis complete!"
echo "============================================================================"
