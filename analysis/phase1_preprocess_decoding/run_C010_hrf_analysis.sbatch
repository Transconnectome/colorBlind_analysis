#!/bin/bash
#SBATCH --job-name=C010_hrf_analysis
#SBATCH --output=logs/C010_hrf_%A_%a.out
#SBATCH --error=logs/C010_hrf_%A_%a.err
#SBATCH --qos=shared
#SBATCH --nodelist=node2,node4
#SBATCH --cpus-per-task=2
#SBATCH --mem=24G
#SBATCH --time=4:00:00
#SBATCH --array=1-40
#SBATCH --no-requeue

# C010 Pipeline with HRF Variability Analysis
# Generates HRF visualizations matching the reference figure

source ~/.bashrc
conda activate nilearn

# Subject-ROI combinations (10 subjects × 4 ROIs = 40 jobs)
SUBJECTS=(02 03 04 05 06 07 08 09 10 11)
ROIS=(V1 V2 V3 V4)

# Calculate subject and ROI from array task ID
SUBJ_IDX=$(( (SLURM_ARRAY_TASK_ID - 1) / 4 ))
ROI_IDX=$(( (SLURM_ARRAY_TASK_ID - 1) % 4 ))

SUBJECT=${SUBJECTS[$SUBJ_IDX]}
ROI=${ROIS[$ROI_IDX]}

echo "=================================================="
echo "SLURM Job ID: $SLURM_JOB_ID"
echo "Array Task ID: $SLURM_ARRAY_TASK_ID"
echo "Subject: $SUBJECT"
echo "ROI: $ROI"
echo "Node: $(hostname)"
echo "=================================================="

# Create logs directory
mkdir -p logs

# Run pipeline
cd /scratch/connectome/haba6030/colorBlind/analysis/validation/preprocess_Check

python run_C010_with_hrf_analysis.py \
    --subject $SUBJECT \
    --roi $ROI

echo "=================================================="
echo "COMPLETED: sub-${SUBJECT} ${ROI}"
echo "=================================================="
