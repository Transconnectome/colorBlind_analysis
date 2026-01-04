#!/bin/bash
#SBATCH --job-name=option2c_v2_relaxed
#SBATCH --output=logs/group_level/option2c_v2_relaxed_%j.out
#SBATCH --error=logs/group_level/option2c_v2_relaxed_%j.err
#SBATCH --time=3:00:00
#SBATCH --mem=32G
#SBATCH --cpus-per-task=4
#SBATCH --nodelist=node2

# Option 2C-v2: Advanced Voxel Selection + Procrustes (Relaxed Thresholds)
#
# 목적: 완화된 threshold로 여러 consensus level 시도
# - ANOVA p-value: 0.01 → 0.05 (원논문)
# - Consensus: 여러 레벨 테스트 (≥2/5, ≥3/5)
# - Reliability: 0.2로 낮춤

echo "================================================================"
echo "Option 2C-v2: Advanced Voxel Selection + Procrustes (Relaxed)"
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

# Option 2C-v2 실행
echo "Running Option 2C-v2: Relaxed Thresholds..."
echo ""

# Test 1: Moderate relaxation (≥2/5 subjects, p=0.05)
echo "----------------------------------------"
echo "Test 1: Moderate (≥2/5, p=0.05, r>0.2)"
echo "----------------------------------------"
python analysis/group_level/option2c_advanced_voxel_selection.py \
    --timestamp baseline81_deob_determin \
    --dataset deoblique_v2 \
    --hc-subjects 02 03 05 06 07 \
    --rois V1 V2 \
    --anova-p 0.05 \
    --anova-consensus 2 \
    --reliability-threshold 0.2 \
    --reliability-consensus 2 \
    --use-cv \
    --cv-top-k 100

TEST1_EXIT=$?

echo ""
echo "Test 1 finished with exit code: $TEST1_EXIT"
echo ""

# 결과 디렉토리 이름 변경
if [ $TEST1_EXIT -eq 0 ]; then
    cd results/group_level/baseline81_deob_determin
    if [ -f "advanced_voxel_selection_summary.txt" ]; then
        mv advanced_voxel_selection_summary.txt advanced_voxel_selection_v2_moderate.txt
        echo "✓ Saved results as: advanced_voxel_selection_v2_moderate.txt"
    fi
    cd /scratch/connectome/haba6030/colorBlind
fi

# Test 2: Majority consensus (≥3/5 subjects)
echo ""
echo "----------------------------------------"
echo "Test 2: Majority (≥3/5, p=0.05, r>0.2)"
echo "----------------------------------------"
python analysis/group_level/option2c_advanced_voxel_selection.py \
    --timestamp baseline81_deob_determin \
    --dataset deoblique_v2 \
    --hc-subjects 02 03 05 06 07 \
    --rois V1 V2 \
    --anova-p 0.05 \
    --anova-consensus 3 \
    --reliability-threshold 0.2 \
    --reliability-consensus 3 \
    --use-cv \
    --cv-top-k 100

TEST2_EXIT=$?

echo ""
echo "Test 2 finished with exit code: $TEST2_EXIT"
echo ""

# 결과 디렉토리 이름 변경
if [ $TEST2_EXIT -eq 0 ]; then
    cd results/group_level/baseline81_deob_determin
    if [ -f "advanced_voxel_selection_summary.txt" ]; then
        mv advanced_voxel_selection_summary.txt advanced_voxel_selection_v2_majority.txt
        echo "✓ Saved results as: advanced_voxel_selection_v2_majority.txt"
    fi
    cd /scratch/connectome/haba6030/colorBlind
fi

echo ""
echo "================================================================"
echo "All tests finished"
echo "Test 1 (Moderate ≥2/5): Exit code $TEST1_EXIT"
echo "Test 2 (Majority ≥3/5): Exit code $TEST2_EXIT"
echo "End time: $(date)"
echo "================================================================"
echo ""
echo "Results saved to:"
echo "  - results/group_level/baseline81_deob_determin/advanced_voxel_selection_v2_moderate.txt"
echo "  - results/group_level/baseline81_deob_determin/advanced_voxel_selection_v2_majority.txt"

exit 0
