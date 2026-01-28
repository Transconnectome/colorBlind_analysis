#!/bin/bash
#SBATCH --job-name=nodrift_full
#SBATCH --array=1-40%20
#SBATCH --output=/scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/logs/nodrift_%A_%a.out
#SBATCH --error=/scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/logs/nodrift_%A_%a.err
#SBATCH --time=00:30:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=10G
#SBATCH --qos=shared
#SBATCH --nodelist=node2,node4
#SBATCH --no-requeue

################################################################################
# No-Drift Strategy: Full Subject Analysis (sub-01 to sub-07)
#
# Based on drift experiment results:
#   D0+M0 (No Drift): mean r=0.5689, V1 r=0.8001 ✅
#
# Conclusion: Drift processing destroys run-to-run reliability
# Strategy: Use D0+M0 (no highpass, no drift regressors) for all subjects
#
# Total jobs: 40 = 10 subjects × 4 ROIs
################################################################################

set -e

# Activate conda environment
source ~/.bashrc
conda activate nilearn

# Job mapping: 10 subjects × 4 ROIs
SUBJECTS=(01 02 03 04 05 06 07 08 09 10)
ROIS=(V1 V2 V3 hV4)

# Calculate indices from array task ID
TASK_ID=$((SLURM_ARRAY_TASK_ID - 1))

SUBJECT_IDX=$((TASK_ID / 4))  # 0-9
ROI_IDX=$((TASK_ID % 4))      # 0-3

SUBJECT=${SUBJECTS[$SUBJECT_IDX]}
ROI=${ROIS[$ROI_IDX]}

echo "================================================================================"
echo "No-Drift Strategy: Full Subject Analysis"
echo "================================================================================"
echo "Job ID: ${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}"
echo "Node: ${SLURM_NODELIST}"
echo "Configuration:"
echo "  Subject:           sub-${SUBJECT}"
echo "  ROI:               ${ROI}"
echo "  Strategy:          D0+M0 (No Drift)"
echo "  Highpass filter:   None"
echo "  Motion confounds:  none"
echo "  Drift model:       none"
echo "  Normalization:     none"
echo ""
echo "Expected performance (based on sub-01 pilot):"
echo "  V1:  run_corr ~ 0.80"
echo "  V2:  run_corr ~ 0.50 (estimated)"
echo "  V3:  run_corr ~ 0.39"
echo "  hV4: run_corr ~ 0.52"
echo ""
echo "Start time: $(date)"
echo "================================================================================"
echo ""

# Directories
BASE_DIR="/scratch/connectome/haba6030/colorBlind"
SCRIPT_DIR="${BASE_DIR}/analysis/phase1_preprocess_decoding"

# Change to BASE directory (script uses relative paths)
cd ${BASE_DIR}

# Run decoding pipeline with D0+M0 strategy
echo "Running FIR reconstruction pipeline..."
echo ""

python ${SCRIPT_DIR}/fir_reconstruction_BH2009_system_clean.py \
    --subject ${SUBJECT} \
    --roi ${ROI} \
    --dataset method3_header_mi \
    --smooth 0 \
    --motion none \
    --compcor 0 \
    --drift none \
    --normalize-level none

EXIT_CODE=$?

echo ""
echo "================================================================================"
if [ ${EXIT_CODE} -eq 0 ]; then
    echo "✅ Pipeline completed successfully"
    echo ""
    echo "Output directory:"
    echo "  analysis/phase1_preprocess_decoding/method3_header_mi/results/factorial_experiment/nzNone_moNo/sub-${SUBJECT}/${ROI}/"
    echo ""
    echo "Next steps:"
    echo "  1. Download all results after completion"
    echo "  2. Run aggregate analysis to compare subjects"
    echo "  3. Check if reliability holds across all subjects"
    echo "  4. (Parallel) Run drift debugging analysis"
else
    echo "❌ Pipeline failed with exit code: ${EXIT_CODE}"
fi
echo "================================================================================"
echo "End time: $(date)"
echo ""

exit ${EXIT_CODE}
