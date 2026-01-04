#!/bin/bash
#SBATCH --job-name=mni_diagnosis
#SBATCH --qos=shared
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=00:30:00
#SBATCH --output=logs/mni_diagnosis/mni_diag_sub-%a.out
#SBATCH --error=logs/mni_diagnosis/mni_diag_sub-%a.err
#SBATCH --array=1-10

# MNI Registration Chain Diagnosis - SLURM Batch Job
#
# Usage:
#   sbatch run_mni_diagnosis.sbatch
#
# Or for specific subjects:
#   sbatch --array=1,2,3 run_mni_diagnosis.sbatch

set -e

# Create log directory
mkdir -p logs/mni_diagnosis

# Subject ID from array task ID
SUBJECT=$(printf "%02d" $SLURM_ARRAY_TASK_ID)

echo "========================================="
echo "MNI Chain Diagnosis"
echo "========================================="
echo "Subject:  sub-${SUBJECT}"
echo "Node:     $(hostname)"
echo "Date:     $(date)"
echo "========================================="
echo ""

# Paths
FMRIPREP_DIR="/storage/connectome/haba6030/fmriprep_out_deoblique_v2"
SCRIPT_DIR="/scratch/connectome/haba6030/colorBlind"
OUTPUT_DIR="${SCRIPT_DIR}/logs/mni_diagnosis"
RUN=1

# Navigate to project directory first (important for .bashrc)
cd ${SCRIPT_DIR}

# Check if fMRIPrep output exists
if [ ! -d "${FMRIPREP_DIR}/sub-${SUBJECT}" ]; then
    echo "❌ ERROR: fMRIPrep output not found for sub-${SUBJECT}"
    echo "   Expected: ${FMRIPREP_DIR}/sub-${SUBJECT}"
    exit 1
fi

# Check if script exists
if [ ! -f "${SCRIPT_DIR}/diagnose_mni_chain.py" ]; then
    echo "❌ ERROR: diagnose_mni_chain.py not found in ${SCRIPT_DIR}"
    echo "   Please upload the script first using:"
    echo "   scp diagnose_mni_chain.py haba6030@node2:${SCRIPT_DIR}/"
    exit 1
fi

# Activate conda environment
echo "🔧 Activating conda environment..."
source ~/.bashrc
conda activate nilearn

# Run diagnosis
echo "🔍 Running MNI chain diagnosis..."
echo ""

python diagnose_mni_chain.py \
    --subject ${SUBJECT} \
    --fmriprep-dir ${FMRIPREP_DIR} \
    --run ${RUN} \
    --output ${OUTPUT_DIR}/mni_chain_diagnosis_sub-${SUBJECT}.txt

EXIT_CODE=$?

echo ""
echo "========================================="
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Diagnosis completed successfully"
    echo "📝 Results saved to:"
    echo "   ${OUTPUT_DIR}/mni_chain_diagnosis_sub-${SUBJECT}.txt"
else
    echo "❌ Diagnosis failed with exit code: $EXIT_CODE"
fi
echo "========================================="

exit $EXIT_CODE
