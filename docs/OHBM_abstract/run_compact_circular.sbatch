#!/bin/bash
#SBATCH --job-name=compact_circular
#SBATCH --output=logs/compact_circular_%A_%a.out
#SBATCH --error=logs/compact_circular_%A_%a.err
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=02:00:00
#SBATCH --array=0-7

# ============================================================================
# Compact Circular Plot Generation for sub-06 and sub-08
# ============================================================================
#
# Purpose: Generate compact circular plots for publication
#
# Subjects: sub-06 (HC), sub-08 (CVD)
# ROIs: V1, V2, V3, hV4
# k value: Optimal k based on minimum reconstruction error
# ============================================================================

# Activate conda environment
source ~/.bashrc
conda activate nilearn

# Configuration
BASE_TIMESTAMP="baseline32_deob_determin"

# All subject-ROI combinations
SUBJECTS=(06 06 06 06 08 08 08 08)
ROIS=(V1 V2 V3 hV4 V1 V2 V3 hV4)

# Parse array task ID
TASK_ID=${SLURM_ARRAY_TASK_ID}
SUBJECT=${SUBJECTS[$TASK_ID]}
ROI=${ROIS[$TASK_ID]}

echo "============================================================================"
echo "Compact Circular Plot Generation"
echo "============================================================================"
echo "Task ID: ${TASK_ID}"
echo "Subject: sub-${SUBJECT}"
echo "ROI: ${ROI}"
echo "k value: Optimal (minimum reconstruction error)"
echo "Compact mode: ENABLED"
echo "============================================================================"

# Run feature selection with compact circular plots
python feature_selection_anova.py \
    --subject ${SUBJECT} \
    --roi ${ROI} \
    --timestamp ${BASE_TIMESTAMP} \
    --dataset deoblique_v2 \
    --output_subdir compact_optimal_k \
    --compact

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "✓ Completed: sub-${SUBJECT} ${ROI}"
else
    echo "✗ Failed: sub-${SUBJECT} ${ROI}"
fi

echo "============================================================================"
