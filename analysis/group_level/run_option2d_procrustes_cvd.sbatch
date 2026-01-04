#!/bin/bash
#SBATCH --job-name=option2d_cvd
#SBATCH --output=logs/group_level/option2d_cvd_%j.out
#SBATCH --error=logs/group_level/option2d_cvd_%j.err
#SBATCH --time=2:00:00
#SBATCH --mem=32G
#SBATCH --cpus-per-task=4
#SBATCH --nodelist=node2

# Option 2D: Procrustes + CVD Comparison
#
# 목적: HC와 CVD의 systematic difference 찾기
# - Option A: Reference-based (sub-02)
# - Option B: Iterative alignment
# - Option C: Voxel weighting
#
# 기대: CVD → HC transformation 찾기 → Color filter

echo "================================================================"
echo "Option 2D: Procrustes + CVD Comparison"
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

# Option 2D 실행
echo "Running Option 2D: Procrustes + CVD Comparison..."
echo ""

python analysis/group_level/option2d_procrustes_cvd_comparison.py \
    --timestamp baseline81_deob_determin \
    --dataset deoblique_v2 \
    --hc-subjects 02 03 05 06 07 \
    --cvd-subjects 08 09 10 \
    --rois V1 V2

EXIT_CODE=$?

echo ""
echo "================================================================"
echo "Job finished"
echo "Exit code: $EXIT_CODE"
echo "End time: $(date)"
echo "================================================================"
echo ""
echo "Results saved to:"
echo "  results/group_level/baseline81_deob_determin/procrustes_cvd_comparison_summary.json"
echo "  results/group_level/baseline81_deob_determin/V1/"
echo "  results/group_level/baseline81_deob_determin/V2/"

exit $EXIT_CODE
