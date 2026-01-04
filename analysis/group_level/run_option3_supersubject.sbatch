#!/bin/bash
#SBATCH --job-name=option3_supersubject
#SBATCH --output=logs/group_level/option3_supersubject_%j.out
#SBATCH --error=logs/group_level/option3_supersubject_%j.err
#SBATCH --time=24:00:00
#SBATCH --mem=32G
#SBATCH --cpus-per-task=4
#SBATCH --nodelist=node2

# Option 3: Supersubject Analysis (Brouwer & Heeger method)
# Supersubject 분석 (고전적 기준선)
#
# 목적: 모든 HC 데이터를 하나로 합쳐서 그룹 수준 모델 구성
# 실행 시간: ~1일
# 메모리: ~32GB

echo "================================================================"
echo "Option 3: Supersubject Analysis"
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

# Option 3 실행 (HC만)
echo "Running Option 3: Supersubject Analysis (HC only)..."
echo ""

python analysis/group_level/option3_supersubject.py \
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
