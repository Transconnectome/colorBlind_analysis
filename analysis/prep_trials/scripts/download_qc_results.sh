#!/bin/bash
################################################################################
# Download aCompCor QC Results for Local Inspection
#
# Downloads:
# 1. Summary validation results (plots + report)
# 2. Sample QC visualizations from 3 subjects
#
# Usage:
#   bash download_qc_results.sh
################################################################################

set -e

# Local download directory
LOCAL_DIR="/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/prep_trials/qc_results/acompcor"

echo "================================================================================"
echo "Downloading aCompCor QC Results"
echo "================================================================================"
echo "Local directory: $LOCAL_DIR"
echo ""

mkdir -p "$LOCAL_DIR"

# 1. Download summary validation results
echo "[1/2] Downloading summary validation results..."
scp -r haba6030@node3:/scratch/connectome/haba6030/colorBlind/analysis/prep_trials/qc_summary \
    "$LOCAL_DIR/"

echo "  ✅ Summary downloaded"
echo ""

# 2. Download sample QC visualizations (sub-01, sub-05, sub-08)
echo "[2/2] Downloading sample subject QC visualizations..."

SAMPLE_SUBJECTS="01 05 08"
for sub in $SAMPLE_SUBJECTS; do
    echo "  Downloading sub-$sub..."
    scp -r haba6030@node3:/storage/connectome/haba6030/fmriprep_out_method3_header_mi/qc/sub-${sub} \
        "$LOCAL_DIR/sample_qc/"
done

echo "  ✅ Sample QC downloaded"
echo ""

echo "================================================================================"
echo "Download Complete"
echo "================================================================================"
echo ""
echo "Results saved to: $LOCAL_DIR/"
echo ""
echo "Inspect files:"
echo "  1. Summary report (text):"
echo "     open $LOCAL_DIR/qc_summary/acompcor_qc_report.txt"
echo ""
echo "  2. Summary plots:"
echo "     open $LOCAL_DIR/qc_summary/mask_coverage_summary.png"
echo "     open $LOCAL_DIR/qc_summary/variance_summary.png"
echo "     open $LOCAL_DIR/qc_summary/correlation_heatmap.png"
echo ""
echo "  3. Sample subject QC:"
echo "     open $LOCAL_DIR/sample_qc/sub-01/sub-01_run-1_tissue_masks.png"
echo "     open $LOCAL_DIR/sample_qc/sub-01/sub-01_run-1_acompcor_qc.png"
echo ""
