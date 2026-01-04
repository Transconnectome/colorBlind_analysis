#!/bin/bash
#SBATCH --job-name=option2_srm_cvd
#SBATCH --output=logs/group_level/option2_srm_cvd_%j.out
#SBATCH --error=logs/group_level/option2_srm_cvd_%j.err
#SBATCH --time=48:00:00
#SBATCH --mem=64G
#SBATCH --cpus-per-task=8
#SBATCH --nodelist=node2

# Option 2: SRM Analysis with CVD subjects
# CVD 피험자 포함 SRM 분석
#
# 목적: HC 공유 공간에 CVD를 투영하여 비교
# 실행 시간: ~2-3일
# 메모리: ~64GB

echo "================================================================"
echo "Option 2: SRM Analysis (HC + CVD)"
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

# BrainIAK 설치 확인
echo "Checking BrainIAK installation..."
python -c "import brainiak; print(f'BrainIAK version: {brainiak.__version__}')" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️ BrainIAK not found. Installing..."
    pip install brainiak
fi
echo ""

# Option 2 실행 (HC + CVD)
echo "Running Option 2: SRM Analysis (HC + CVD)..."
echo ""

python analysis/group_level/option2_srm_analysis.py \
    --timestamp baseline81_deob_determin \
    --dataset deoblique_v2 \
    --hc-subjects 02 03 05 06 07 \
    --cvd-subjects 08 09 10 \
    --rois V1 V2 V3 hV4 \
    --k-features 20 \
    --n-iter 10

EXIT_CODE=$?

echo ""
echo "================================================================"
echo "Job finished"
echo "Exit code: $EXIT_CODE"
echo "End time: $(date)"
echo "================================================================"

exit $EXIT_CODE
