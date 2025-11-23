#!/bin/bash
#SBATCH --job-name=BH2009_all_subs
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=24:00:00
#SBATCH --output=logs/BH2009_all_subjects_%j.out
#SBATCH --error=logs/BH2009_all_subjects_%j.err

# Activate conda environment
source ~/.bashrc
conda activate nilearn

# Create logs directory if it doesn't exist
mkdir -p logs

# ROI to analyze
ROI="V1"

# Test subjects
SUBJECTS=("01" "02" "03" "04")

echo "=========================================="
echo "BH2009 Pipeline: All Test Subjects"
echo "=========================================="
echo "Subjects: ${SUBJECTS[@]}"
echo "ROI: ${ROI}"
echo "Start time: $(date)"
echo ""
echo "Running both 6mm and 8mm smoothing for each subject"
echo ""

TOTAL_ANALYSES=$((${#SUBJECTS[@]} * 2))
CURRENT=0

for SUBJECT in "${SUBJECTS[@]}"; do
    echo ""
    echo "######################################################"
    echo "# SUBJECT ${SUBJECT}"
    echo "######################################################"
    echo ""

    # ============================================
    # 6mm Smoothing
    # ============================================
    CURRENT=$((CURRENT + 1))
    echo "=========================================="
    echo "Analysis ${CURRENT}/${TOTAL_ANALYSES}: Subject ${SUBJECT} - 6mm Smoothing"
    echo "=========================================="
    echo "Start time: $(date)"
    echo ""

    python fir_reconstruction_BH2009_smooth6mm.py \
        --subject ${SUBJECT} \
        --roi ${ROI}

    EXIT_CODE_6MM=$?

    if [ ${EXIT_CODE_6MM} -eq 0 ]; then
        echo ""
        echo "✓ Subject ${SUBJECT} - 6mm smoothing completed successfully!"
    else
        echo ""
        echo "✗ Subject ${SUBJECT} - 6mm smoothing failed with exit code ${EXIT_CODE_6MM}"
    fi

    echo "End time: $(date)"
    echo ""
    sleep 3

    # ============================================
    # 8mm Smoothing
    # ============================================
    CURRENT=$((CURRENT + 1))
    echo "=========================================="
    echo "Analysis ${CURRENT}/${TOTAL_ANALYSES}: Subject ${SUBJECT} - 8mm Smoothing"
    echo "=========================================="
    echo "Start time: $(date)"
    echo ""

    python fir_reconstruction_BH2009_config26.py \
        --subject ${SUBJECT} \
        --roi ${ROI}

    EXIT_CODE_8MM=$?

    if [ ${EXIT_CODE_8MM} -eq 0 ]; then
        echo ""
        echo "✓ Subject ${SUBJECT} - 8mm smoothing completed successfully!"
    else
        echo ""
        echo "✗ Subject ${SUBJECT} - 8mm smoothing failed with exit code ${EXIT_CODE_8MM}"
    fi

    echo "End time: $(date)"
    echo ""
    sleep 3

done

# ============================================
# Summary
# ============================================
echo ""
echo "=========================================="
echo "ALL SUBJECTS COMPLETE"
echo "=========================================="
echo "End time: $(date)"
echo ""
echo "Results saved to:"
echo "  - derivatives/BH2009_smooth6mm/sub-*_${ROI}/"
echo "  - derivatives/BH2009_config26/sub-*_${ROI}/"
echo ""
echo "Next steps:"
echo "1. Download all results directories"
echo "2. Compare 6mm vs 8mm for each subject"
echo "3. Compare across subjects"
echo "4. Select optimal smoothing level"
echo ""

exit 0
