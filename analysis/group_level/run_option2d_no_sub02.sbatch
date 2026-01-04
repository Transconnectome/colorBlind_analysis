#!/bin/bash
#SBATCH --job-name=option2d_no02
#SBATCH --output=logs/group_level/option2d_no_sub02_%j.out
#SBATCH --error=logs/group_level/option2d_no_sub02_%j.err
#SBATCH --time=2:00:00
#SBATCH --mem=32G
#SBATCH --cpus-per-task=4
#SBATCH --nodelist=node2

# Option 2D: WITHOUT sub-02 (Reference Bias Test)
#
# 목적: Sub-02 제외하고 재분석
# 기대:
#   - T magnitude 감소
#   - CV (coefficient of variation) 개선
#   - Disparity 개선 (현재 0.94-0.97 → 목표 < 0.5)
#
# Reference: Sub-03 (첫 번째 subject)

echo "================================================================"
echo "Option 2D: WITHOUT sub-02 (Reference Bias Test)"
echo "================================================================"
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURM_NODELIST"
echo "Start time: $(date)"
echo ""
echo "⚠️  EXCLUDING sub-02 due to reference bias (CV > 100%)"
echo "HC subjects: 03, 05, 06, 07 (4 subjects)"
echo "CVD subjects: 08, 09, 10 (3 subjects)"
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

# Option 2D 실행 (sub-02 제외)
echo "Running Option 2D without sub-02..."
echo ""

python analysis/group_level/option2d_procrustes_cvd_comparison.py \
    --timestamp baseline81_deob_determin \
    --dataset deoblique_v2 \
    --hc-subjects 03 05 06 07 \
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
echo "Results will be saved to the same directory as before:"
echo "  results/group_level/baseline81_deob_determin/"
echo ""
echo "⚠️  IMPORTANT: Results will OVERWRITE previous analysis!"
echo "   (Previous results with sub-02 are in downloaded local copy)"
echo ""
echo "Next steps:"
echo "  1. Download results"
echo "  2. Compare with previous (with sub-02)"
echo "  3. Check: T magnitude, CV, disparity, p-value"
echo "  4. If improved → proceed to transformation validation"
echo "  5. If still high CV → try generalized Procrustes"

exit $EXIT_CODE
