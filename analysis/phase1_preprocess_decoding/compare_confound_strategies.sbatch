#!/bin/bash
#SBATCH --job-name=confound_cmp
#SBATCH --array=1-24%12
#SBATCH --output=/scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/logs/confound_compare_%A_%a.out
#SBATCH --error=/scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/logs/confound_compare_%A_%a.err
#SBATCH --time=00:30:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=10G
#SBATCH --qos=shared
#SBATCH --nodelist=node2,node4
#SBATCH --no-requeue

################################################################################
# Confound Strategy Comparison Test
#
# Compare Baseline32 (cosine only) vs Method3+confounds (standard)
#
# Test subjects: sub-01, sub-06 (non-CVD), sub-09 (CVD)
# ROIs: V1, V2, V3, hV4
# Motion types: cosine, standard
#
# Total: 3 subjects × 4 ROIs × 2 motion types = 24 jobs
################################################################################

set -e

# Activate conda environment
source ~/.bashrc
conda activate nilearn

# Job mapping
SUBJECTS=(01 06 09)
ROIS=(V1 V2 V3 hV4)
MOTION_TYPES=(cosine standard)

# Calculate indices from array task ID
# Total combinations: 3 subjects × 4 ROIs × 2 motion types = 24
TASK_ID=$((SLURM_ARRAY_TASK_ID - 1))

SUBJECT_IDX=$((TASK_ID / 8))  # 0-2
ROI_IDX=$(((TASK_ID % 8) / 2))  # 0-3
MOTION_IDX=$((TASK_ID % 2))  # 0-1

SUBJECT=${SUBJECTS[$SUBJECT_IDX]}
ROI=${ROIS[$ROI_IDX]}
MOTION_TYPE=${MOTION_TYPES[$MOTION_IDX]}

echo "================================================================================"
echo "Confound Strategy Comparison"
echo "================================================================================"
echo "Job ID: ${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}"
echo "Node: ${SLURM_NODELIST}"
echo "Configuration:"
echo "  Subject:     sub-${SUBJECT}"
echo "  ROI:         ${ROI}"
echo "  Motion type: ${MOTION_TYPE}"
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
    --drift none

EXIT_CODE=$?

echo ""
echo "================================================================================"
if [ ${EXIT_CODE} -eq 0 ]; then
    echo "✅ Pipeline completed successfully"
else
    echo "❌ Pipeline failed with exit code: ${EXIT_CODE}"
fi
echo "================================================================================"
echo "End time: $(date)"
echo ""

exit ${EXIT_CODE}
