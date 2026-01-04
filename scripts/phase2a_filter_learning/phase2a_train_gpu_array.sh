#!/bin/bash
#SBATCH --job-name=phase2a_gpu
#SBATCH --qos=shared_interactive
#SBATCH --nodelist=node3
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --time=1:00:00
#SBATCH --array=0-5
#SBATCH --output=/scratch/connectome/haba6030/colorBlind/logs/phase2a/gpu_train_%A_%a.out
#SBATCH --error=/scratch/connectome/haba6030/colorBlind/logs/phase2a/gpu_train_%A_%a.err

# Phase 2A: GPU Training (Option D)

echo "=================================="
echo "Phase 2A GPU Training"
echo "Job ID: $SLURM_JOB_ID"
echo "Array Task ID: $SLURM_ARRAY_TASK_ID"
echo "Node: $(hostname)"
echo "GPU: $CUDA_VISIBLE_DEVICES"
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

# GPU ID 자동 할당 (SLURM이 설정)
GPU_ID=$((SLURM_ARRAY_TASK_ID % 8))

echo ""
echo "Training: sub-$SUBJECT $ROI on GPU $GPU_ID"
echo "=================================="

# Python 스크립트 실행
python scripts/phase2a_train_gpu.py \
    --subject $SUBJECT \
    --roi $ROI \
    --option D \
    --gpu $GPU_ID

echo ""
echo "=================================="
echo "Task completed: sub-$SUBJECT $ROI"
echo "=================================="
