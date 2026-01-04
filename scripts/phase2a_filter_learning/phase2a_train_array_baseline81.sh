#!/bin/bash
#SBATCH --job-name=train_baseline81
#SBATCH --qos=shared
#SBATCH --nodelist=node2
#SBATCH --array=0-5
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=2:00:00
#SBATCH --output=logs/phase2a_train_baseline81_%A_%a.out
#SBATCH --error=logs/phase2a_train_baseline81_%A_%a.err

echo "=========================================="
echo "Phase 2A Filter Training (baseline81)"
echo "=========================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Array Task ID: $SLURM_ARRAY_TASK_ID"
echo "Node: $SLURM_NODELIST"
echo "Start time: $(date)"
echo ""

# Change to project directory
cd /scratch/connectome/haba6030/colorBlind

# Activate conda environment
source ~/.bashrc
conda activate nilearn

# Define combinations: 3 subjects × 2 ROIs = 6 tasks
SUBJECTS=("08" "08" "09" "09" "10" "10")
ROIS=("V1" "V2" "V1" "V2" "V1" "V2")

SUBJECT=${SUBJECTS[$SLURM_ARRAY_TASK_ID]}
ROI=${ROIS[$SLURM_ARRAY_TASK_ID]}

echo "Training: sub-${SUBJECT} ${ROI}"
echo ""

# Run training
python -u scripts/phase2a_train_single_baseline81.py \
    --subject ${SUBJECT} \
    --roi ${ROI}

echo ""
echo "Task completed at: $(date)"
