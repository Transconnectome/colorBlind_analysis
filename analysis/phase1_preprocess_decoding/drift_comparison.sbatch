#!/bin/bash
#SBATCH --job-name=drift_comp
#SBATCH --array=1-16
#SBATCH --output=/scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/logs/drift_%A_%a.out
#SBATCH --error=/scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/logs/drift_%A_%a.err
#SBATCH --time=00:30:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=10G
#SBATCH --qos=shared
#SBATCH --nodelist=node2,node4
#SBATCH --no-requeue

################################################################################
# Drift Processing Comparison Experiment
#
# Purpose: Test 4 drift processing strategies to identify why run-to-run
#          reliability is low (~0.02) compared to Baseline32 (~0.775)
#
# Hypothesis: Drift processing (highpass filter or cosine regressors)
#             removes signal along with noise
#
# Test Conditions:
#   D0+M0: No highpass, No drift regressors (Baseline32 재현) ← CRITICAL!
#   D1+M0: Highpass only (0.01 Hz)
#   D2+M0: Cosine regressors only
#   D2+M1: Full confounds (standard)
#
# Total jobs: 16 = 1 subject (sub-01) × 4 ROIs × 4 conditions
################################################################################

set -e

# Activate conda environment
source ~/.bashrc
conda activate nilearn

# Job mapping: 1 subject × 4 ROIs × 4 drift conditions
SUBJECTS=(01)
ROIS=(V1 V2 V3 hV4)

# Drift strategy arrays (4 conditions)
HIGHPASS_VALS=("None" "0.01" "None" "None")
MOTION_VALS=("none" "none" "cosine" "standard")
DRIFT_VALS=("none" "none" "none" "none")
CONDITION_NAMES=("D0+M0_NoDrift" "D1+M0_HPF" "D2+M0_Cosine" "D2+M1_Standard")

# Calculate indices from array task ID
TASK_ID=$((SLURM_ARRAY_TASK_ID - 1))

SUBJECT_IDX=$((TASK_ID / 16))  # 0 (only sub-01)
ROI_IDX=$(((TASK_ID % 16) / 4))  # 0-3
COND_IDX=$((TASK_ID % 4))  # 0-3

SUBJECT=${SUBJECTS[$SUBJECT_IDX]}
ROI=${ROIS[$ROI_IDX]}
HIGHPASS=${HIGHPASS_VALS[$COND_IDX]}
MOTION=${MOTION_VALS[$COND_IDX]}
DRIFT=${DRIFT_VALS[$COND_IDX]}
CONDITION=${CONDITION_NAMES[$COND_IDX]}

echo "================================================================================"
echo "Drift Comparison Experiment: Testing drift processing strategies"
echo "================================================================================"
echo "Job ID: ${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}"
echo "Node: ${SLURM_NODELIST}"
echo "Configuration:"
echo "  Subject:           sub-${SUBJECT}"
echo "  ROI:               ${ROI}"
echo "  Condition:         ${CONDITION}"
echo "  Highpass filter:   ${HIGHPASS} Hz"
echo "  Motion confounds:  ${MOTION}"
echo "  Drift model:       ${DRIFT}"
echo ""
echo "Expected outcome:"
if [ "$CONDITION" == "D0+M0_NoDrift" ]; then
    echo "  🎯 CRITICAL TEST: Should match Baseline32 (r~0.7)?"
    echo "  ✅ If r~0.7: Drift processing is the problem"
    echo "  ⚠️  If 0.3<r<0.5: Partial improvement, need more investigation"
    echo "  ❌ If r<0.3: Problem is not drift-related"
else
    echo "  Compare against D0+M0 baseline"
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

# Build command conditionally
if [ "$HIGHPASS" != "None" ]; then
    python ${SCRIPT_DIR}/fir_reconstruction_BH2009_system_clean.py \
        --subject ${SUBJECT} \
        --roi ${ROI} \
        --dataset method3_header_mi \
        --smooth 0 \
        --highpass ${HIGHPASS} \
        --motion ${MOTION} \
        --compcor 0 \
        --drift ${DRIFT} \
        --normalize-level none
else
    python ${SCRIPT_DIR}/fir_reconstruction_BH2009_system_clean.py \
        --subject ${SUBJECT} \
        --roi ${ROI} \
        --dataset method3_header_mi \
        --smooth 0 \
        --motion ${MOTION} \
        --compcor 0 \
        --drift ${DRIFT} \
        --normalize-level none
fi

EXIT_CODE=$?

echo ""
echo "================================================================================"
if [ ${EXIT_CODE} -eq 0 ]; then
    echo "✅ Pipeline completed successfully"
    echo ""
    echo "Next steps:"
    echo "  1. Check results in: analysis/phase1_preprocess_decoding/method3_header_mi/results/factorial_experiment/"
    echo "  2. Run analysis script to compare 4 conditions"
    if [ "$CONDITION" == "D0+M0_NoDrift" ]; then
        echo "  3. 🎯 MOST IMPORTANT: Check D0+M0 run_correlation_mean"
        echo "     If r~0.7: ✅ Drift processing is the problem!"
        echo "     If r~0.3: ⚠️  Drift + other factors involved"
        echo "     If r<0.3: ❌ Need deeper investigation"
    fi
else
    echo "❌ Pipeline failed with exit code: ${EXIT_CODE}"
fi
echo "================================================================================"
echo "End time: $(date)"
echo ""

exit ${EXIT_CODE}
