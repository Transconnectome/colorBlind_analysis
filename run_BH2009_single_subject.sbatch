#!/bin/bash
#SBATCH --job-name=BH2009_single
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=06:00:00
#SBATCH --output=logs/BH2009_single_%j.out
#SBATCH --error=logs/BH2009_single_%j.err

# Activate conda environment
source ~/.bashrc
conda activate nilearn

# Create logs directory if it doesn't exist
mkdir -p logs

# ============================================
# CONFIGURATION - CHANGE THESE AS NEEDED
# ============================================
SUBJECT="01"           # Subject ID: 01, 02, 03, 04 (NOT P01)
ROI="V1"              # ROI: V1, V2, V3, hV4
SMOOTHING="both"      # Options: 6mm, 8mm, both

echo "=========================================="
echo "BH2009 Pipeline: Single Subject Analysis"
echo "=========================================="
echo "Subject: ${SUBJECT}"
echo "ROI: ${ROI}"
echo "Smoothing: ${SMOOTHING}"
echo "Start time: $(date)"
echo ""

# ============================================
# Run Analysis
# ============================================

if [ "$SMOOTHING" == "6mm" ] || [ "$SMOOTHING" == "both" ]; then
    echo "================================================"
    echo "Running 6mm Smoothing Analysis"
    echo "================================================"
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
fi

if [ "$SMOOTHING" == "8mm" ] || [ "$SMOOTHING" == "both" ]; then
    if [ "$SMOOTHING" == "both" ]; then
        echo "Waiting 5 seconds before next analysis..."
        sleep 5
        echo ""
    fi

    echo "================================================"
    echo "Running 8mm Smoothing Analysis"
    echo "================================================"
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
    echo ""
fi

# ============================================
# Summary
# ============================================
echo "=========================================="
echo "ANALYSIS COMPLETE"
echo "=========================================="
echo "End time: $(date)"
echo ""

if [ "$SMOOTHING" == "both" ]; then
    echo "Results saved to:"
    echo "  - derivatives/BH2009_smooth6mm/*_sub-${SUBJECT}_${ROI}/"
    echo "  - derivatives/BH2009_config26/*_sub-${SUBJECT}_${ROI}/"
elif [ "$SMOOTHING" == "6mm" ]; then
    echo "Results saved to:"
    echo "  - derivatives/BH2009_smooth6mm/*_sub-${SUBJECT}_${ROI}/"
else
    echo "Results saved to:"
    echo "  - derivatives/BH2009_config26/*_sub-${SUBJECT}_${ROI}/"
fi

echo ""
exit 0
