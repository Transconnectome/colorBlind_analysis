#!/bin/bash
#SBATCH --job-name=option2c_advanced
#SBATCH --output=logs/group_level/option2c_advanced_%j.out
#SBATCH --error=logs/group_level/option2c_advanced_%j.err
#SBATCH --time=3:00:00
#SBATCH --mem=32G
#SBATCH --cpus-per-task=4
#SBATCH --nodelist=node2

# Option 2C: Advanced Voxel Selection + Procrustes
#
# 목적: 여러 voxel selection 방법 시도
# - ANOVA color-significant
# - Group-consistent reliable
# - Combined
# - Cross-validated (optional)

echo "================================================================"
echo "Option 2C: Advanced Voxel Selection + Procrustes"
echo "================================================================"
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURM_NODELIST"
echo "Start time: $(date)"
echo ""

# Conda 환경 활성화
source ~/.bashrc
conda activate nilearn

# 작업 디렉토리로 이동
cd /scratch/connectome/haba6030/colorBlind

# Python 확인
echo "Python: $(which python)"
echo "Python version: $(python --version)"
echo ""

# Option 2C 실행
echo "Running Option 2C: Advanced Voxel Selection..."
echo ""

python analysis/group_level/option2c_advanced_voxel_selection.py \
    --timestamp baseline81_deob_determin \
    --dataset deoblique_v2 \
    --hc-subjects 02 03 05 06 07 \
    --rois V1 V2 \
    --anova-p 0.01 \
    --reliability-threshold 0.3 \
    --use-cv \
    --cv-top-k 100

EXIT_CODE=$?

echo ""
echo "================================================================"
echo "Job finished"
echo "Exit code: $EXIT_CODE"
echo "End time: $(date)"
echo "================================================================"

exit $EXIT_CODE
