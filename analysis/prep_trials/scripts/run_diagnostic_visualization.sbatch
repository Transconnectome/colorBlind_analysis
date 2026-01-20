#!/bin/bash
#SBATCH --job-name=diagnostic_viz
#SBATCH --qos=shared
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=02:00:00
#SBATCH --output=/scratch/connectome/haba6030/colorBlind/analysis/prep_trials/logs/diagnostic_%A_%a.out
#SBATCH --error=/scratch/connectome/haba6030/colorBlind/analysis/prep_trials/logs/diagnostic_%A_%a.err
#SBATCH --array=0-2

set -e

# Subject array
SUBJECTS=(01 03 06)
SUBJECT=${SUBJECTS[$SLURM_ARRAY_TASK_ID]}

# Activate conda environment
source /usr/anaconda3/etc/profile.d/conda.sh
conda activate nilearn

# Paths
SCRIPT_DIR="/scratch/connectome/haba6030/colorBlind/analysis/prep_trials/scripts"
LOG_DIR="/scratch/connectome/haba6030/colorBlind/analysis/prep_trials/logs"

mkdir -p ${LOG_DIR}

echo "=========================================="
echo "Registration Quality Diagnostic"
echo "Subject: ${SUBJECT}"
echo "Date: $(date)"
echo "=========================================="
echo ""

# Run diagnostic for all 6 runs
for RUN in {1..6}; do
    echo "Processing Run ${RUN}..."

    python ${SCRIPT_DIR}/diagnose_registration_quality.py \
        --subject ${SUBJECT} \
        --run ${RUN} \
        --rois V1 V2 V3 hV4 \
        --threshold 50

    echo ""
done

echo "=========================================="
echo "Subject ${SUBJECT} Complete!"
echo "Date: $(date)"
echo "=========================================="
