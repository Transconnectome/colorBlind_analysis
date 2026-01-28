#!/bin/bash
#SBATCH --job-name=factorial_2x2
#SBATCH --array=1-16
#SBATCH --output=/scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/logs/factorial_%A_%a.out
#SBATCH --error=/scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/logs/factorial_%A_%a.err
#SBATCH --time=00:30:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=10G
#SBATCH --qos=shared
#SBATCH --nodelist=node2,node4
#SBATCH --no-requeue

################################################################################
# 2×2 Factorial Experiment: Normalization × Confounds
#
# Axis 1: Normalization level
#   E1 (both): Consistent normalization (1st + 2nd level)
#   E2 (none): All original (no normalization)
#
# Axis 2: Confounds regression
#   C0 (none): No confounds (minimal drift)
#   C1 (cosine): Cosine confounds (Baseline32)
#
# Total: 1 subject × 4 ROIs × 4 conditions = 16 jobs
#
# Conditions:
#   1. E1+C0 (nzBoth_moNo):  both + none
#   2. E1+C1 (nzBoth_moCo):  both + cosine
#   3. E2+C0 (nzNone_moNo):  none + none
#   4. E2+C1 (nzNone_moCo):  none + cosine
#
# Expected diagnosis:
#   - SUCCESS: HRF L2 norm ~ 700 (original scale)
#             amplitude std ~ 0.3 (stable)
#             run_correlation > 0.5 (reliable)
#   - FAILURE: HRF L2 norm ~ 0.02 (normalized scale)
#             amplitude std ~ 500 (explosion)
#             run_correlation ~ 0 (unreliable)
################################################################################

set -e

# Activate conda environment
source ~/.bashrc
conda activate nilearn

# Job mapping: 1 subject × 4 ROIs × 4 conditions
SUBJECTS=(01)
ROIS=(V1 V2 V3 hV4)

# Factorial design: 2×2
NORMALIZE_LEVELS=(both both none none)  # E1, E1, E2, E2
MOTION_TYPES=(none cosine none cosine)  # C0, C1, C0, C1
CONDITION_NAMES=("E1+C0" "E1+C1" "E2+C0" "E2+C1")

# Calculate indices from array task ID
TASK_ID=$((SLURM_ARRAY_TASK_ID - 1))

SUBJECT_IDX=$((TASK_ID / 16))  # 0 (only sub-01)
ROI_IDX=$(((TASK_ID % 16) / 4))  # 0-3
CONDITION_IDX=$((TASK_ID % 4))  # 0-3

SUBJECT=${SUBJECTS[$SUBJECT_IDX]}
ROI=${ROIS[$ROI_IDX]}
NORMALIZE_LEVEL=${NORMALIZE_LEVELS[$CONDITION_IDX]}
MOTION_TYPE=${MOTION_TYPES[$CONDITION_IDX]}
CONDITION_NAME=${CONDITION_NAMES[$CONDITION_IDX]}

echo "================================================================================"
echo "2×2 Factorial Experiment: Normalization × Confounds"
echo "================================================================================"
echo "Job ID: ${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}"
echo "Node: ${SLURM_NODELIST}"
echo "Configuration:"
echo "  Subject:           sub-${SUBJECT}"
echo "  ROI:               ${ROI}"
echo "  Condition:         ${CONDITION_NAME}"
echo "  Normalize level:   ${NORMALIZE_LEVEL} (E1=both, E2=none)"
echo "  Motion confounds:  ${MOTION_TYPE} (C0=none, C1=cosine)"
echo ""
echo "Expected outcome:"
if [ "$NORMALIZE_LEVEL" == "both" ]; then
    echo "  ✅ HRF L2 norm should be stable (~700)"
    echo "  ✅ Amplitude std should be normal (~0.3)"
    echo "  ✅ Run correlation should be high (>0.5)"
else
    echo "  ⚠️  Testing all-original strategy"
    echo "  📊 Will compare HRF/amplitude scales"
fi
echo ""
echo "Start time: $(date)"
echo "================================================================================"
echo ""

# Directories
BASE_DIR="/scratch/connectome/haba6030/colorBlind"
SCRIPT_DIR="${BASE_DIR}/analysis/phase1_preprocess_decoding"

# Change to BASE directory (script uses relative paths)
cd ${BASE_DIR}

# Run decoding pipeline
echo "Running FIR reconstruction pipeline..."
echo ""

python ${SCRIPT_DIR}/fir_reconstruction_BH2009_system_clean.py \
    --subject ${SUBJECT} \
    --roi ${ROI} \
    --dataset method3_header_mi \
    --smooth 0 \
    --highpass 0.01 \
    --motion ${MOTION_TYPE} \
    --compcor 0 \
    --drift none \
    --normalize-level ${NORMALIZE_LEVEL}

EXIT_CODE=$?

echo ""
echo "================================================================================"
if [ ${EXIT_CODE} -eq 0 ]; then
    echo "✅ Pipeline completed successfully"
    echo ""
    echo "Next steps:"
    echo "  1. Check results in: analysis/phase1_preprocess_decoding/method3_header_mi/results/factorial_experiment/"
    echo "  2. Run analysis script to compare 4 conditions"
    echo "  3. Look for:"
    echo "     - HRF L2 norm (should be ~700 for success, ~0.02 for failure)"
    echo "     - amplitude_std_raw (should be ~0.3 for success, ~500 for failure)"
    echo "     - run_correlation_mean (should be >0.5 for success, ~0 for failure)"
else
    echo "❌ Pipeline failed with exit code: ${EXIT_CODE}"
fi
echo "================================================================================"
echo "End time: $(date)"
echo ""

exit ${EXIT_CODE}
