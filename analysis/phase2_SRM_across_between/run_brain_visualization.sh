#!/bin/bash
#
# Run SPM-Style Brain Visualization of Procrustes Improvement
#
# Purpose: Generate publication-quality brain surface figures showing
#          spatial distribution of Procrustes effects on brain anatomy
#
# Usage:
#   ./run_brain_visualization.sh
#
# Requirements:
#   - conda environment: srm (with nilearn, scipy, sklearn)
#   - Data: phase1 results (amplitudes_raw.npy, amplitudes_procrustes.npy)
#   - Atlas: Wang ROI masks (ProbAtlas_v4)
#
# Outputs:
#   - ./results/brain_surface_visualization/*.png (3-4 figures per ROI)
#   - ./results/brain_surface_visualization/*.json (metrics)
#
# Author: Claude Code
# Date: 2026-02-16

set -e  # Exit on error

# Activate conda environment
echo "Activating conda environment: srm"
source ~/.bashrc
conda activate srm

# Change to script directory
cd "$(dirname "$0")"

echo "========================================="
echo "SPM-Style Brain Visualization"
echo "========================================="
echo "Date: $(date)"
echo "User: $(whoami)"
echo "Working directory: $(pwd)"
echo "========================================="

# Configuration
SUBJECT="sub-08"       # CVD subject
HC_REF="sub-01"        # HC reference (single subject)
OUTPUT_DIR="./results/brain_surface_visualization"

# Create output directory
mkdir -p "$OUTPUT_DIR"

# =========================================
# Main Visualization (V2 - strongest effect)
# =========================================

echo ""
echo "========================================="
echo "Processing V2 (main analysis)"
echo "========================================="

python visualize_procrustes_brain_maps.py \
    --subject $SUBJECT \
    --roi V2 \
    --hc-reference $HC_REF \
    --output-dir "$OUTPUT_DIR" \
    --n-splits 50

echo ""
echo "✓ V2 complete"

# =========================================
# Optional: All ROIs
# =========================================

# Process all ROIs
echo ""
echo "========================================="
echo "Processing all ROIs"
echo "========================================="

for ROI in V1 V2 V3 V4; do
    echo ""
    echo "Processing $ROI..."
    echo "-----------------------------------------"

    python visualize_procrustes_brain_maps.py \
        --subject $SUBJECT \
        --roi $ROI \
        --hc-reference $HC_REF \
        --output-dir "$OUTPUT_DIR" \
        --n-splits 50

    echo "✓ $ROI complete"
done

# =========================================
# Optional: Surface Rendering (Enhancement)
# =========================================

# Uncomment to generate surface rendering (slower, optional)
# echo ""
# echo "========================================="
# echo "Generating surface rendering"
# echo "========================================="
#
# python visualize_procrustes_brain_maps.py \
#     --subject $SUBJECT \
#     --roi V2 \
#     --hc-reference $HC_REF \
#     --output-dir "$OUTPUT_DIR" \
#     --surface-rendering

# =========================================
# Summary
# =========================================

echo ""
echo "========================================="
echo "✅ COMPLETE!"
echo "========================================="
echo "Output directory: $OUTPUT_DIR"
echo ""
echo "Generated files:"
ls -lh "$OUTPUT_DIR" | tail -n +2

echo ""
echo "Key outputs:"
echo "  - ${SUBJECT}_V2_correspondence_brain_map.png (MAIN FIGURE)"
echo "  - ${SUBJECT}_V2_disparity_brain_map.png"
echo "  - ${SUBJECT}_V2_profile_reliability_brain_map.png"
echo "  - ${SUBJECT}_V2_brain_metrics.json"

echo ""
echo "View main figure:"
echo "  open $OUTPUT_DIR/${SUBJECT}_V2_correspondence_brain_map.png"

echo ""
echo "View metrics:"
echo "  cat $OUTPUT_DIR/${SUBJECT}_V2_brain_metrics.json | python -m json.tool"

echo ""
echo "========================================="
echo "Done! $(date)"
echo "========================================="
