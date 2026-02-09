#!/bin/bash
################################################################################
# Run aCompCor Quality Control Validation
#
# Analyzes all generated confounds and creates summary report:
# - Mask coverage statistics
# - Component variance distribution
# - Inter-component correlations
# - Quality assessment and recommendations
#
# Usage:
#   bash run_acompcor_validation.sh
################################################################################

set -e

echo "================================================================================"
echo "aCompCor Quality Control Validation"
echo "================================================================================"
echo ""

# Activate conda environment
source ~/.bashrc
conda activate nilearn

# Run validation
cd /scratch/connectome/haba6030/colorBlind/analysis/prep_trials/scripts

python validate_acompcor_quality.py \
    --method method3_header_mi \
    --subjects 01,02,03,04,05,06,07,08,09,10 \
    --runs 1,2,3,4,5,6 \
    --output-dir /scratch/connectome/haba6030/colorBlind/analysis/prep_trials/qc_summary

echo ""
echo "================================================================================"
echo "Validation Complete"
echo "================================================================================"
echo ""
echo "Check outputs:"
echo "  /scratch/connectome/haba6030/colorBlind/analysis/prep_trials/qc_summary/"
echo "    - mask_coverage_summary.png"
echo "    - variance_summary.png"
echo "    - correlation_heatmap.png"
echo "    - acompcor_qc_report.txt"
echo ""
echo "Download results:"
echo "  scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/prep_trials/qc_summary \\"
echo "    ~/Downloads/acompcor_validation/"
echo ""
