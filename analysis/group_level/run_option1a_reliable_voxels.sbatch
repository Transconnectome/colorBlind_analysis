#!/bin/bash
#SBATCH --job-name=option1a_voxels
#SBATCH --output=logs/group_level/option1a_reliable_voxels_%j.out
#SBATCH --error=logs/group_level/option1a_reliable_voxels_%j.err
#SBATCH --time=4:00:00
#SBATCH --mem=16G
#SBATCH --cpus-per-task=2
#SBATCH --nodelist=node2

# Option 1A: Reliability-Guided Voxel Selection
# Voxel 수준 reliability 기반 선택
#
# 목적: Test-retest reliable voxels만 선택하여 group analysis 개선
# 실행 시간: ~2-4시간

echo "================================================================"
echo "Option 1A: Reliability-Guided Voxel Selection"
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

# Option 1A 실행
echo "Running Option 1A: Reliability-Guided Voxel Selection..."
echo ""

python analysis/group_level/option1a_reliable_voxel_selection.py \
    --timestamp baseline81_deob_determin \
    --dataset deoblique_v2 \
    --hc-subjects 02 03 05 06 07 \
    --rois V1 V2 V3 hV4 \
    --percentile 50

EXIT_CODE=$?

echo ""
echo "================================================================"
echo "Job finished"
echo "Exit code: $EXIT_CODE"
echo "End time: $(date)"
echo "================================================================"

exit $EXIT_CODE
