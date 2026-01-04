#!/bin/bash
#SBATCH --job-name=phase2a_optionD
#SBATCH --qos=shared
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=2:00:00
#SBATCH --array=0-5
#SBATCH --output=/scratch/connectome/haba6030/colorBlind/logs/phase2a/optionD_train_%A_%a.out
#SBATCH --error=/scratch/connectome/haba6030/colorBlind/logs/phase2a/optionD_train_%A_%a.err

# Phase 2A: Option D (RDM-Based) - 기본 권장

echo "=================================="
echo "Phase 2A Filter Training - Option D"
echo "Job ID: $SLURM_JOB_ID"
echo "Array Task ID: $SLURM_ARRAY_TASK_ID"
echo "Node: $(hostname)"
echo "=================================="

cd /scratch/connectome/haba6030/colorBlind
mkdir -p logs/phase2a

source ~/.bashrc
conda activate nilearn

# 피험자-ROI 조합
SUBJECTS=(08 08 09 09 10 10)
ROIS=(V1 V2 V1 V2 V1 V2)

SUBJECT=${SUBJECTS[$SLURM_ARRAY_TASK_ID]}
ROI=${ROIS[$SLURM_ARRAY_TASK_ID]}

echo ""
echo "Training: sub-$SUBJECT $ROI (Option D: RDM-Based)"
echo "=================================="

# Python 스크립트 실행 (unbuffered for real-time logs)
python -u scripts/phase2a_train_single.py \
    --subject $SUBJECT \
    --roi $ROI \
    --option D

echo ""
echo "=================================="
echo "Task completed: sub-$SUBJECT $ROI"
echo "=================================="
