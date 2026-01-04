#!/bin/bash
#SBATCH --job-name=pca_16_01
#SBATCH --nodelist=node2
#SBATCH --array=0-8
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16GB
#SBATCH --time=08:00:00
#SBATCH --output=logs/feature_selection/pca_16_01_sub-%a_%j.out
#SBATCH --error=logs/feature_selection/pca_16_01_sub-%a_%j.err

# ============================================================================
# SLURM Array Job: PCA Feature Selection - Configs 1 & 16
# ============================================================================
#
# This script runs PCA feature selection on baseline 1 and 16 results.
#
# Purpose:
#   - Load baseline amplitudes (already preprocessed)
#   - Apply PCA dimensionality reduction
#   - Compare with baseline (no PCA)
#
# Baseline Configurations to Process (ALL):
#   - baseline01_deob_determin (Config 1, Deterministic ROI, High HRF repr)
#   - baseline01_deob_probability (Config 1, Probability ROI, High HRF repr)
#   - baseline16_deob_determin (Config 16, Deterministic ROI, High HRF repr + smoothing)
#   - baseline16_deob_probability (Config 16, Probability ROI, High HRF repr + smoothing)
#
# Job Array Processing:
#   - 9 parallel jobs (array 0-8), one per subject (excludes sub-04)
#   - Each job processes: 4 ROIs × 4 baselines = 16 analyses
#   - Total across all jobs: 9 × 16 = 144 analyses
#
# Usage:
#   sbatch run_pca_selection_16_01.sbatch
#
# Output:
#   - derivatives/feature_selection/pca_*/pca_results_*.csv
#   - PCA visualization plots
#
# ============================================================================

echo "================================================================"
echo "PCA Feature Selection - Configs 1 & 16"
echo "Job ID: ${SLURM_JOB_ID}"
echo "Array Task ID: ${SLURM_ARRAY_TASK_ID}"
echo "Start: $(date)"
echo "================================================================"

# Create log directory
mkdir -p logs/feature_selection

# Activate conda environment
echo ""
echo "Activating conda environment..."
source ~/.bashrc
conda activate nilearn

# ============================================================================
# Define Baseline Configurations
# ============================================================================

DATASET="deoblique_v2"

# Baseline timestamps to process (configs 1 and 16, both deterministic and probabilistic)
BASELINES=(baseline01_deob_determin baseline01_deob_probability baseline16_deob_determin baseline16_deob_probability)
BASELINE_NAMES=("Config01_Determin" "Config01_Probability" "Config16_Determin" "Config16_Probability")

echo ""
echo "Baseline Configurations to Process:"
for i in "${!BASELINES[@]}"; do
    echo "  $((i+1)). ${BASELINE_NAMES[$i]}: ${BASELINES[$i]}"
done
echo ""
echo "Dataset: ${DATASET}"
echo ""

# Map SLURM_ARRAY_TASK_ID to subject (excludes sub-04)
SUBJECTS=(01 02 03 05 06 07 08 09 10)
SUBJECT=${SUBJECTS[$SLURM_ARRAY_TASK_ID]}

echo "Processing Subject: ${SUBJECT}"
echo ""

# Define ROIs to process
ROIS=(V1 V2 V3 hV4)

# Initialize counters
TOTAL_RUNS=0
SUCCESS_COUNT=0
FAIL_COUNT=0

# Calculate total analyses
NUM_ROIS=${#ROIS[@]}
NUM_BASELINES=${#BASELINES[@]}
TOTAL_ANALYSES=$((NUM_BASELINES * NUM_ROIS))  # 4 baselines × 4 ROIs

# ============================================================================
# Main Loop: Process all ROIs with all baselines
# ============================================================================

echo "================================================================"
echo "Processing: ${NUM_BASELINES} baselines × ${NUM_ROIS} ROIs = ${TOTAL_ANALYSES} analyses for Subject ${SUBJECT}"
echo "================================================================"
echo ""

for i in "${!BASELINES[@]}"; do
    TIMESTAMP=${BASELINES[$i]}
    BASELINE_NAME=${BASELINE_NAMES[$i]}

    echo "==============================================================="
    echo "  PCA + ${BASELINE_NAME} (${TIMESTAMP})"
    echo "==============================================================="
    echo ""

    for ROI in "${ROIS[@]}"; do
        TOTAL_RUNS=$((TOTAL_RUNS + 1))

        echo "--- [${TOTAL_RUNS}/${TOTAL_ANALYSES}] PCA: Sub ${SUBJECT}, ROI ${ROI}, ${BASELINE_NAME} ---"
        echo "Start time: $(date '+%H:%M:%S')"
        echo ""

        # Run PCA feature selection on baseline amplitudes
        python feature_selection_pca.py \
            --subject $SUBJECT \
            --roi $ROI \
            --timestamp $TIMESTAMP \
            --dataset $DATASET

        # Check exit status
        EXIT_CODE=$?
        echo ""
        echo "End time: $(date '+%H:%M:%S')"

        if [ $EXIT_CODE -eq 0 ]; then
            echo "✓ Success: PCA Sub ${SUBJECT} ${ROI} ${BASELINE_NAME}"
            SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
        else
            echo "✗ Failed: PCA Sub ${SUBJECT} ${ROI} ${BASELINE_NAME} (exit code: ${EXIT_CODE})"
            FAIL_COUNT=$((FAIL_COUNT + 1))
        fi

        echo ""
    done

    echo ""
done

# ============================================================================
# Final Summary
# ============================================================================

echo ""
echo "================================================================"
echo "Subject ${SUBJECT} PCA analysis complete"
echo "================================================================"
echo ""
echo "Summary:"
echo "  Total runs: ${TOTAL_RUNS}"
echo "  Successful: ${SUCCESS_COUNT}/${TOTAL_ANALYSES}"
echo "  Failed: ${FAIL_COUNT}/${TOTAL_ANALYSES}"
if [ $TOTAL_ANALYSES -gt 0 ]; then
    echo "  Success rate: $(echo "scale=1; $SUCCESS_COUNT * 100 / $TOTAL_ANALYSES" | bc)%"
fi
echo ""
echo "Baselines tested:"
for i in "${!BASELINES[@]}"; do
    echo "  - ${BASELINE_NAMES[$i]}: ${BASELINES[$i]}"
done
echo "ROIs processed: V1, V2, V3, hV4"
echo ""
echo "Results saved to: derivatives/feature_selection/"
echo "  - pca_{timestamp}/pca_results_*.csv"
echo ""
echo "Completion time: $(date)"
echo "================================================================"

# Exit with error if any runs failed
if [ $FAIL_COUNT -gt 0 ]; then
    echo ""
    echo "⚠️  Warning: $FAIL_COUNT analyses failed"
    echo "Check logs for details: logs/feature_selection/pca_16_01_sub-${SLURM_ARRAY_TASK_ID}_${SLURM_JOB_ID}.{out,err}"
    exit 1
else
    echo ""
    echo "✓ All analyses completed successfully for Subject ${SUBJECT}!"
    exit 0
fi
