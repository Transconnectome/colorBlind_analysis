#!/bin/bash
#SBATCH --job-name=feat_sel
#SBATCH --nodelist=node2
#SBATCH --array=0-8
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16GB
#SBATCH --time=6:00:00
#SBATCH --output=logs/feature_selection/anova_rfe_sub-%a_%j.out
#SBATCH --error=logs/feature_selection/anova_rfe_sub-%a_%j.err

# ============================================================================
# SLURM Batch Script: Feature Selection (ANOVA + RFE)
# ============================================================================
#
# This script runs ANOVA and RFE feature selection on baseline results.
#
# Purpose:
#   - Load baseline amplitudes (already preprocessed)
#   - Apply ANOVA and RFE feature selection
#   - Compare with baseline (no feature selection)
#
# Baseline Configurations to Process (ALL):
#   - baseline32_deob (Config 32, Deterministic ROI)
#   - baseline32_deob_probability (Config 32, Probability ROI)
#   - baseline81_deob (Config 81, Deterministic ROI)
#   - baseline81_deob_probability (Config 81, Probability ROI)
#
# Job Array Processing:
#   - 9 parallel jobs (array 0-8), one per subject (excludes sub-04)
#   - Each job processes: 4 ROIs × 2 methods × 4 baselines = 32 analyses
#   - Total across all jobs: 9 × 32 = 288 analyses
#
# Usage:
#   sbatch run_feature_selection_dual_config.sbatch
#
# Output (per subject):
#   - logs/feature_selection/anova_rfe_sub-{ARRAY_ID}_{JOB_ID}.out
#   - derivatives/feature_selection/anova_*/anova_results_*.csv
#   - derivatives/feature_selection/rfe_*/rfe_results_*.csv
#   - Visualizations for each method/baseline/ROI
#
# ============================================================================

echo "================================================================"
echo "Feature Selection: ANOVA + RFE"
echo "Job Array Task ID: ${SLURM_ARRAY_TASK_ID}"
echo "Job ID: ${SLURM_JOB_ID}"
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

# Baseline timestamps to process (all baselines including probability)
BASELINES=(baseline32_deob_determin baseline32_deob_probability baseline81_deob_determin baseline81_deob_probability)
BASELINE_NAMES=("Config32_Determin" "Config32_Probability" "Config81_Determin" "Config81_Probability")

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
ROIS=(V1 V2 V3 hV4)

# Get subject for this array task
SUBJECT=${SUBJECTS[$SLURM_ARRAY_TASK_ID]}

# Initialize counters
TOTAL_RUNS=0
SUCCESS_COUNT=0
FAIL_COUNT=0

# Calculate total analyses for THIS subject
NUM_ROIS=${#ROIS[@]}
NUM_BASELINES=${#BASELINES[@]}
TOTAL_ANALYSES=$((2 * NUM_BASELINES * NUM_ROIS))  # 2 methods × 4 baselines × 4 ROIs

# ============================================================================
# Main Loop: Iterate through Methods, Baselines, and ROIs for ONE subject
# ============================================================================

echo "================================================================"
echo "Processing Subject ${SUBJECT}: 2 methods × ${NUM_BASELINES} baselines × ${NUM_ROIS} ROIs = ${TOTAL_ANALYSES} analyses"
echo "================================================================"
echo ""

for METHOD in anova rfe; do
    echo "###############################################################"
    echo "# METHOD: ${METHOD^^}"
    echo "###############################################################"
    echo ""

    for i in "${!BASELINES[@]}"; do
        TIMESTAMP=${BASELINES[$i]}
        BASELINE_NAME=${BASELINE_NAMES[$i]}

        echo "==============================================================="
        echo "  ${METHOD^^} + ${BASELINE_NAME} (${TIMESTAMP})"
        echo "==============================================================="
        echo ""

        for ROI in "${ROIS[@]}"; do

            TOTAL_RUNS=$((TOTAL_RUNS + 1))

            echo "--- [$TOTAL_RUNS/$TOTAL_ANALYSES] ${METHOD^^}: Sub ${SUBJECT}, ROI ${ROI}, ${BASELINE_NAME} ---"
            echo "Start time: $(date '+%H:%M:%S')"
            echo ""

            # Run feature selection on baseline amplitudes
            python feature_selection_${METHOD}.py \
                --subject $SUBJECT \
                --roi $ROI \
                --timestamp $TIMESTAMP \
                --dataset $DATASET

            # Check exit status
            EXIT_CODE=$?
            echo ""
            echo "End time: $(date '+%H:%M:%S')"

            if [ $EXIT_CODE -eq 0 ]; then
                echo "✓ Success: ${METHOD^^} Sub ${SUBJECT} ${ROI} ${BASELINE_NAME}"
                SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
            else
                echo "✗ Failed: ${METHOD^^} Sub ${SUBJECT} ${ROI} ${BASELINE_NAME} (exit code: ${EXIT_CODE})"
                FAIL_COUNT=$((FAIL_COUNT + 1))
            fi

            echo ""
        done  # ROI loop

        echo ""
    done  # BASELINE loop

    echo ""
done  # METHOD loop

# ============================================================================
# Final Summary (for this subject)
# ============================================================================

echo ""
echo "================================================================"
echo "Subject ${SUBJECT}: All ${TOTAL_ANALYSES} analyses complete"
echo "================================================================"
echo ""
echo "Summary for Subject ${SUBJECT}:"
echo "  Total runs: ${TOTAL_RUNS}"
echo "  Successful: ${SUCCESS_COUNT}/${TOTAL_ANALYSES}"
echo "  Failed: ${FAIL_COUNT}/${TOTAL_ANALYSES}"
if [ $TOTAL_ANALYSES -gt 0 ]; then
    echo "  Success rate: $(echo "scale=1; $SUCCESS_COUNT * 100 / $TOTAL_ANALYSES" | bc)%"
fi
echo ""
echo "Methods tested: ANOVA, RFE"
echo "Baselines tested:"
for i in "${!BASELINES[@]}"; do
    echo "  - ${BASELINE_NAMES[$i]}: ${BASELINES[$i]}"
done
echo "ROIs tested: ${NUM_ROIS} (${ROIS[*]})"
echo ""
echo "Results saved to: derivatives/feature_selection/"
echo "  - anova_{timestamp}/anova_results_*.csv"
echo "  - rfe_{timestamp}/rfe_results_*.csv"
echo ""
echo "Completion time: $(date)"
echo "================================================================"

# Exit with error if any runs failed
if [ $FAIL_COUNT -gt 0 ]; then
    echo ""
    echo "⚠️  Warning: $FAIL_COUNT analyses failed for subject ${SUBJECT}"
    echo "Check log: logs/feature_selection/anova_rfe_sub-${SLURM_ARRAY_TASK_ID}_${SLURM_JOB_ID}.{out,err}"
    exit 1
else
    echo ""
    echo "✓ Subject ${SUBJECT}: All analyses completed successfully!"
    exit 0
fi
