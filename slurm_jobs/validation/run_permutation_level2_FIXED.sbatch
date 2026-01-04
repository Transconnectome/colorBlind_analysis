#!/bin/bash
#SBATCH --job-name=perm_lv2
#SBATCH --output=logs/permutation_analysis/level2/perm_level2_%A_%a.out
#SBATCH --error=logs/permutation_analysis/level2/perm_level2_%A_%a.err
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=24:00:00
#SBATCH --array=0-8

# ============================================================================
# Level 2 Permutation Test with ROI-Specific Best K Values
# ============================================================================
# FIXED: Each subject-ROI combination uses its own best k value
#
# Level 2 scenarios: warm_cool, opposite_quadrants, adjacent_quadrants
# Total jobs: 9 (one per subject)
# Each job processes: 3 scenarios × 4 ROIs = 12 combinations
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

# Level 2 scenarios (half-space permutation)
SCENARIOS=(warm_cool opposite_quadrants adjacent_quadrants)

# Parse array task ID
TASK_ID=${SLURM_ARRAY_TASK_ID}
SUBJECT=${SUBJECTS[$TASK_ID]}

echo "============================================================================"
echo "Task ID: ${TASK_ID}"
echo "Subject: sub-${SUBJECT}"
echo "Level 2 Permutation Test (Half-Space)"
echo "Processing scenarios: ${SCENARIOS[@]}"
echo "Processing ROIs: ${ROIS[@]}"
echo "============================================================================"

# ============================================================================
# Main Loop: Scenarios → ROIs
# ============================================================================

# Loop through all Level 2 scenarios
for SCENARIO in "${SCENARIOS[@]}"; do
    echo ""
    echo "========================================================================"
    echo "Scenario: ${SCENARIO}"
    echo "========================================================================"

    # Timestamp for permuted dataset
    TIMESTAMP="baseline32_deob_determin_permuted_${SCENARIO}"

    # Loop through all ROIs
    for ROI in "${ROIS[@]}"; do
        echo ""
        echo "--------------------------------------------------------------------"
        echo "Processing: sub-${SUBJECT} ${ROI} ${SCENARIO}"
        echo "--------------------------------------------------------------------"

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

        # Step 1: Create permuted amplitudes if not exists
        echo ""
        echo "Step 1: Checking permuted amplitudes..."

        BASELINE_DIR="derivatives/BH2009_deoblique_v2/${TIMESTAMP}"
        AMP_DIR=$(find ${BASELINE_DIR} -name "*_sub-${SUBJECT}_${ROI}_*" -type d 2>/dev/null | head -1)

        if [ -z "$AMP_DIR" ]; then
            echo "⚠️  Permuted amplitudes NOT found. Creating..."

            # Create permuted amplitudes
            python create_permuted_amplitudes.py \
                --subject ${SUBJECT} \
                --roi ${ROI} \
                --scenario ${SCENARIO} \
                --timestamp baseline32_deob_determin \
                --dataset deoblique_v2

            if [ $? -ne 0 ]; then
                echo "✗ Failed to create permuted amplitudes"
                continue
            fi

            # Re-check
            AMP_DIR=$(find ${BASELINE_DIR} -name "*_sub-${SUBJECT}_${ROI}_*" -type d 2>/dev/null | head -1)
            if [ -z "$AMP_DIR" ]; then
                echo "✗ Still cannot find permuted amplitudes after creation"
                continue
            fi
        fi

        echo "Found permuted amplitudes: ${AMP_DIR}"

        # Step 2: Run feature selection with ROI-specific best k
        echo ""
        echo "Step 2: Running feature selection with k=${K_FIXED}..."

        python feature_selection_anova.py \
            --subject ${SUBJECT} \
            --roi ${ROI} \
            --timestamp ${TIMESTAMP} \
            --dataset deoblique_v2 \
            --k_fixed ${K_FIXED} \
            --output_subdir "../../permutation_analysis/fixed_bestK"

        EXIT_CODE=$?

        if [ $EXIT_CODE -eq 0 ]; then
            echo "✓ Successfully completed: sub-${SUBJECT} ${ROI} ${SCENARIO} (k=${K_FIXED})"
        else
            echo "✗ Failed: sub-${SUBJECT} ${ROI} ${SCENARIO} (exit code: ${EXIT_CODE})"
        fi

    done  # ROI loop
done  # Scenario loop

echo ""
echo "============================================================================"
echo "Subject ${SUBJECT} Level 2 permutation analysis complete!"
echo "============================================================================"
