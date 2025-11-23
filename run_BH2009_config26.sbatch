#!/bin/bash
#SBATCH --job-name=BH2009_config26
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --output=logs/BH2009_config26_%j.out
#SBATCH --error=logs/BH2009_config26_%j.err

# Activate conda environment
source ~/.bashrc
conda activate nilearn

# Create logs directory if it doesn't exist
mkdir -p logs

# Subject and ROI to analyze
SUBJECT="P01"
ROI="V1"

echo "=========================================="
echo "BH2009 Pipeline with Config 26 Preprocessing"
echo "=========================================="
echo "Subject: ${SUBJECT}"
echo "ROI: ${ROI}"
echo "Start time: $(date)"
echo ""
echo "Config 26 Settings:"
echo "  - Spatial smoothing: 8mm FWHM"
echo "  - Motion confounds: 6 parameters"
echo "  - High-pass filter: NO (detrimental)"
echo "  - Drift model: polynomial (constant + linear)"
echo ""

# Run the analysis
python fir_reconstruction_BH2009_config26.py \
    --subject ${SUBJECT} \
    --roi ${ROI}

EXIT_CODE=$?

echo ""
echo "End time: $(date)"
echo "Exit code: ${EXIT_CODE}"

if [ ${EXIT_CODE} -eq 0 ]; then
    echo "✓ Analysis completed successfully!"
else
    echo "✗ Analysis failed with exit code ${EXIT_CODE}"
fi

exit ${EXIT_CODE}
