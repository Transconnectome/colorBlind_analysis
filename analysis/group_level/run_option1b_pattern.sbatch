#!/bin/bash
#SBATCH --job-name=option1b_pattern
#SBATCH --output=logs/group_level/option1b_pattern_%j.out
#SBATCH --error=logs/group_level/option1b_pattern_%j.err
#SBATCH --time=4:00:00
#SBATCH --mem=16G
#SBATCH --cpus-per-task=2
#SBATCH --nodelist=node2

# Option 1B: Pattern-Based Consistency
# Pattern geometry 기반 consistency 측정
#
# 목적: Voxel 간 관계(pattern)의 stability 평가
# 실행 시간: ~2-4시간

echo "================================================================"
echo "Option 1B: Pattern-Based Consistency"
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

# Python 경로 확인
echo "Python path: $(which python)"
echo "Python version: $(python --version)"
echo ""

# Option 1B 실행
echo "Running Option 1B: Pattern Consistency Analysis..."
echo ""

python analysis/group_level/option1b_pattern_consistency.py \
    --timestamp baseline81_deob_determin \
    --dataset deoblique_v2 \
    --hc-subjects 02 03 05 06 07 \
    --rois V1 V2 V3 hV4

EXIT_CODE=$?

echo ""
echo "================================================================"
echo "Job finished"
echo "Exit code: $EXIT_CODE"
echo "End time: $(date)"
echo "================================================================"

exit $EXIT_CODE
