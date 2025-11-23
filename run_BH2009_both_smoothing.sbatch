#!/bin/bash
#SBATCH --job-name=BH2009_both_smooth
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=06:00:00
#SBATCH --output=logs/BH2009_both_smooth_%j.out
#SBATCH --error=logs/BH2009_both_smooth_%j.err

# Activate conda environment
source ~/.bashrc
conda activate nilearn

# Create logs directory if it doesn't exist
mkdir -p logs

# Subject and ROI to analyze
SUBJECT="01"  # Test subject (01, 02, 03, 04)
ROI="V1"

echo "=========================================="
echo "BH2009 Pipeline: Testing 6mm vs 8mm Smoothing"
echo "=========================================="
echo "Subject: ${SUBJECT}"
echo "ROI: ${ROI}"
echo "Start time: $(date)"
echo ""
echo "Purpose: Compare spatial specificity (6mm) vs SNR (8mm)"
echo ""

# ============================================
# Run 1: 6mm Smoothing (Better Spatial Resolution)
# ============================================
echo "================================================"
echo "ANALYSIS 1/2: 6mm Smoothing"
echo "================================================"
echo "Config 14/18 from grid search:"
echo "  - HRF correlation: 0.9971 (excellent)"
echo "  - Temporal SNR: 59.5"
echo "  - Advantages: Better spatial specificity"
echo "              Less signal leakage between ROIs"
echo "              Preserves fine-grained patterns"
echo ""

python fir_reconstruction_BH2009_smooth6mm.py \
    --subject ${SUBJECT} \
    --roi ${ROI}

EXIT_CODE_6MM=$?

if [ ${EXIT_CODE_6MM} -eq 0 ]; then
    echo ""
    echo "✓ 6mm smoothing analysis completed successfully!"
else
    echo ""
    echo "✗ 6mm smoothing analysis failed with exit code ${EXIT_CODE_6MM}"
fi

echo ""
echo "Waiting 5 seconds before next analysis..."
sleep 5

# ============================================
# Run 2: 8mm Smoothing (Better SNR)
# ============================================
echo ""
echo "================================================"
echo "ANALYSIS 2/2: 8mm Smoothing"
echo "================================================"
echo "Config 26 from grid search:"
echo "  - HRF correlation: 0.9998 (near-perfect)"
echo "  - Temporal SNR: 89.5"
echo "  - Advantages: Slightly better HRF homogeneity"
echo "              Higher temporal SNR"
echo "              Better noise reduction"
echo ""

python fir_reconstruction_BH2009_config26.py \
    --subject ${SUBJECT} \
    --roi ${ROI}

EXIT_CODE_8MM=$?

if [ ${EXIT_CODE_8MM} -eq 0 ]; then
    echo ""
    echo "✓ 8mm smoothing analysis completed successfully!"
else
    echo ""
    echo "✗ 8mm smoothing analysis failed with exit code ${EXIT_CODE_8MM}"
fi

# ============================================
# Summary
# ============================================
echo ""
echo "=========================================="
echo "ANALYSIS SUMMARY"
echo "=========================================="
echo "End time: $(date)"
echo ""

if [ ${EXIT_CODE_6MM} -eq 0 ] && [ ${EXIT_CODE_8MM} -eq 0 ]; then
    echo "✓ Both analyses completed successfully!"
    echo ""
    echo "Results saved to:"
    echo "  - derivatives/BH2009_smooth6mm/pilot/*_${SUBJECT}_${ROI}/"
    echo "  - derivatives/BH2009_config26/pilot/*_${SUBJECT}_${ROI}/"
    echo ""
    echo "Next steps:"
    echo "1. Download both results directories"
    echo "2. Compare analysis_summary.json files"
    echo "3. Look for trade-off:"
    echo "   - 6mm: Better spatial specificity → Better decoding?"
    echo "   - 8mm: Better SNR → Better decoding?"
    EXIT_CODE=0
elif [ ${EXIT_CODE_6MM} -eq 0 ]; then
    echo "⚠️  Only 6mm analysis succeeded"
    echo "   8mm analysis failed with exit code ${EXIT_CODE_8MM}"
    EXIT_CODE=1
elif [ ${EXIT_CODE_8MM} -eq 0 ]; then
    echo "⚠️  Only 8mm analysis succeeded"
    echo "   6mm analysis failed with exit code ${EXIT_CODE_6MM}"
    EXIT_CODE=1
else
    echo "✗ Both analyses failed"
    echo "   6mm exit code: ${EXIT_CODE_6MM}"
    echo "   8mm exit code: ${EXIT_CODE_8MM}"
    EXIT_CODE=1
fi

echo ""
exit ${EXIT_CODE}
