#!/bin/bash
#SBATCH --job-name=phase2a_hypernet
#SBATCH --qos=shared_interactive
#SBATCH --nodelist=node3
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --time=2:00:00
#SBATCH --output=/scratch/connectome/haba6030/colorBlind/logs/phase2a/hypernet_train_%j.out
#SBATCH --error=/scratch/connectome/haba6030/colorBlind/logs/phase2a/hypernet_train_%j.err

# Phase 2A: HyperNetwork Training (모든 피험자 동시)

echo "=================================="
echo "Phase 2A HyperNetwork Training"
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $(hostname)"
echo "GPU: $CUDA_VISIBLE_DEVICES"
echo "=================================="

cd /scratch/connectome/haba6030/colorBlind
mkdir -p logs/phase2a

source ~/.bashrc
conda activate nilearn

echo ""
echo "Training HyperNetwork for all subjects..."
echo "=================================="

# Python 스크립트 실행
python scripts/phase2a_hypernet.py --gpu 0

echo ""
echo "=================================="
echo "HyperNetwork training completed!"
echo "=================================="
