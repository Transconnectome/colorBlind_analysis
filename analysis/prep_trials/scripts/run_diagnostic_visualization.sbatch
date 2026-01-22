#!/bin/bash
#SBATCH --job-name=diagnostic_viz
#SBATCH --qos=shared
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:15:00
#SBATCH --output=/scratch/connectome/haba6030/colorBlind/analysis/prep_trials/logs/diagnostic_%A_%a.out
#SBATCH --error=/scratch/connectome/haba6030/colorBlind/analysis/prep_trials/logs/diagnostic_%A_%a.err
#SBATCH --array=0-9

set -e

# Method name (passed as environment variable or default)
METHOD=${METHOD:-method3_header_mi}

# Subject array (all 10 subjects)
SUBJECTS=(01 02 03 04 05 06 07 08 09 10)
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
echo "Method: ${METHOD}"
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
        --method ${METHOD} \
        --rois V1 V2 V3 hV4 \
        --threshold 50

    echo ""
done

echo "=========================================="
echo "Subject ${SUBJECT} Complete!"
echo "Date: $(date)"
echo "=========================================="
