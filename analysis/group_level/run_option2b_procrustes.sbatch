#!/bin/bash
#SBATCH --job-name=option2b_procrustes
#SBATCH --output=logs/group_level/option2b_procrustes_%j.out
#SBATCH --error=logs/group_level/option2b_procrustes_%j.err
#SBATCH --time=2:00:00
#SBATCH --mem=32G
#SBATCH --cpus-per-task=4
#SBATCH --nodelist=node2

# Option 2B: Procrustes-based Group Alignment
# SRM 대안: Procrustes로 피험자 간 정렬
#
# 목적: SRM이 실패했으므로 Procrustes 기반 정렬 시도
# 실행 시간: ~30분-1시간 (SRM보다 훨씬 빠름)
# 메모리: ~32GB (충분)

echo "================================================================"
echo "Option 2B: Procrustes-based Group Alignment"
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

# Option 2B 실행
echo "Running Option 2B: Procrustes Alignment..."
echo ""

python analysis/group_level/option2b_procrustes_alignment.py \
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
