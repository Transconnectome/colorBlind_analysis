#!/bin/bash
#SBATCH --job-name=baseline_all
#SBATCH --output=/scratch/connectome/haba6030/colorBlind/logs/baseline_%A_%a.out
#SBATCH --error=/scratch/connectome/haba6030/colorBlind/logs/baseline_%A_%a.err
#SBATCH --array=1-40%15
#SBATCH --time=00:40:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=16G
#SBATCH --qos=shared
#SBATCH --nodelist=node2
#SBATCH --no-requeue

set -e
source ~/.bashrc
conda activate nilearn

# ============================================================================
# Baseline Pipeline Deployment
# Configuration: c02 from Grid Factorial (optimal)
#   - highpass: 0 (preserve DC)
#   - motion: none (no regression)
#   - drift: per_run (run-specific only)
#   - smooth: 0
#   - normalize: none
# ============================================================================

SUBJECTS=(01 02 03 04 05 06 07 08 09 10)
ROIS=(V1 V2 V3 hV4)

# Map array task ID to subject and ROI
SUBJ_IDX=$(( ($SLURM_ARRAY_TASK_ID - 1) / 4 ))
ROI_IDX=$(( ($SLURM_ARRAY_TASK_ID - 1) % 4 ))

SUBJECT=${SUBJECTS[$SUBJ_IDX]}
ROI=${ROIS[$ROI_IDX]}
DATASET="method3_header_mi"

echo "========================================================================"
echo "Baseline Pipeline - All Subjects Deployment"
echo "========================================================================"
echo "Job ID: ${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}"
echo "Subject: ${SUBJECT}, ROI: ${ROI}"
echo ""
echo "Configuration (c02 - Optimal from Grid Factorial):"
echo "  Highpass: 0 Hz (preserve DC)"
echo "  Motion:   none (no regression)"
echo "  Drift:    per_run (run-specific only)"
echo "  Smooth:   0 mm"
echo "  Normalize: none"
echo ""

cd /scratch/connectome/haba6030/colorBlind

# Output directory
OUTPUT_DIR="analysis/phase1_preprocess_decoding/results/baseline/sub-${SUBJECT}/${ROI}"

# Check if already completed (resume capability)
if [ -f "${OUTPUT_DIR}/amplitudes_raw.npy" ]; then
    echo "⚠️  Output already exists: ${OUTPUT_DIR}/amplitudes_raw.npy"
    echo "    Skipping to avoid overwrite. Delete manually to re-run."
    exit 0
fi

# Create output directory
mkdir -p ${OUTPUT_DIR}

# Run FIR reconstruction
python analysis/phase1_preprocess_decoding/fir_reconstruction_BH2009_system_clean.py \
    --subject ${SUBJECT} \
    --roi ${ROI} \
    --dataset ${DATASET} \
    --highpass 0 \
    --motion none \
    --drift per_run \
    --smooth 0 \
    --normalize-level none \
    --output-dir ${OUTPUT_DIR}

EXIT_CODE=$?

echo ""
echo "========================================================================"
if [ ${EXIT_CODE} -eq 0 ]; then
    echo "✅ Baseline pipeline completed: sub-${SUBJECT} ${ROI}"
    echo ""
    echo "Outputs:"
    echo "  amplitudes_raw.npy"
    echo "  voxel_coords.npy"
    echo "  roi_hrf.npy"
    echo "  qc.json"
    echo ""
    echo "Next: Apply Procrustes alignment (run apply_procrustes_baseline.py)"
else
    echo "❌ Baseline pipeline failed: sub-${SUBJECT} ${ROI} (exit code: ${EXIT_CODE})"
fi
echo "========================================================================"

exit ${EXIT_CODE}
