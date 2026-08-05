#!/bin/bash
# Local testing script for Procrustes pipeline
# Tests single ROI (V1) with all subjects

set -e

echo "=== Procrustes Pipeline: Local Test (V1) ==="
echo "Start time: $(date)"

ROI="V1"
SUBJECTS=(01 02 03 04 05 06 08 09 10)

# Step 1: PCA for all subjects
echo ""
echo "========================================="
echo "STEP 1: PCA Dimension Reduction"
echo "========================================="

for SUBJECT in "${SUBJECTS[@]}"; do
    echo "  Processing sub-$SUBJECT..."
    python step1a_dimension_reduction_pca.py \
        --subject $SUBJECT \
        --roi $ROI \
        --n-components 50
done

echo "✓ Step 1 complete"

# Step 2: Iterative Procrustes
echo ""
echo "========================================="
echo "STEP 2: Iterative Procrustes"
echo "========================================="

python step2_iterative_procrustes.py \
    --roi $ROI \
    --max-iter 10 \
    --method pca

echo "✓ Step 2 complete"

# Step 3: Crossnobis RDMs
echo ""
echo "========================================="
echo "STEP 3: Compute Crossnobis RDMs"
echo "========================================="

for SUBJECT in "${SUBJECTS[@]}"; do
    echo "  Processing sub-$SUBJECT..."
    python step3_compute_rdms_crossnobis.py \
        --subject $SUBJECT \
        --roi $ROI \
        --method pca
done

echo "✓ Step 3 complete"

# Step 4: Geometric Metrics
echo ""
echo "========================================="
echo "STEP 4: Geometric Metrics"
echo "========================================="

python step4_geometric_metrics.py \
    --roi $ROI \
    --method pca

echo "✓ Step 4 complete"

# Step 5: Visualizations
echo ""
echo "========================================="
echo "STEP 5: Visualization & Reporting"
echo "========================================="

python step5_visualize_report.py \
    --roi $ROI \
    --method pca

echo "✓ Step 5 complete"

echo ""
echo "========================================="
echo "TEST COMPLETE"
echo "========================================="
echo "End time: $(date)"
echo ""
echo "Check results:"
echo "  - PCA diagnostics: results/step5_visualizations/V1_pca_diagnostics.png"
echo "  - Statistics: results/step4_metrics/V1/hc_vs_cvd_statistics.json"
echo "  - Convergence: results/step2_procrustes/V1/convergence_history.json"
