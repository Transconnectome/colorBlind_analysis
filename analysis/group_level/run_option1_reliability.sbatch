#!/bin/bash
#SBATCH --job-name=option1_reliability
#SBATCH --output=logs/group_level/option1_reliability_%j.out
#SBATCH --error=logs/group_level/option1_reliability_%j.err
#SBATCH --time=24:00:00
#SBATCH --mem=32G
#SBATCH --cpus-per-task=4
#SBATCH --nodelist=node2

# Option 1: Within-Subject Reliability Analysis
# 피험자 내 신뢰도 분석 (진단 - 최우선)
#
# 목적: 개별 피험자의 RDM이 얼마나 안정적인지 평가
# 실행 시간: ~2-3시간
# 메모리: ~32GB (안전 여유)

echo "================================================================"
echo "Option 1: Within-Subject Reliability Analysis"
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

# Option 1 실행
echo "Running Option 1: Within-Subject Reliability..."
echo ""

python analysis/group_level/option1_within_subject_reliability.py \
    --timestamp baseline81_deob_determin \
    --dataset deoblique_v2 \
    --subjects 01 02 03 05 06 07 \
    --rois V1 V2 V3 hV4 \
    --split-method first-second

EXIT_CODE=$?

echo ""
echo "================================================================"
echo "Job finished"
echo "Exit code: $EXIT_CODE"
echo "End time: $(date)"
echo "================================================================"

exit $EXIT_CODE
