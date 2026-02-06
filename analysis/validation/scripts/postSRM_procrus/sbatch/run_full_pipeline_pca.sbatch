#!/bin/bash
#SBATCH --job-name=postSRM_full_pca
#SBATCH --qos=shared
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=02:00:00
#SBATCH --output=logs/full_pipeline_pca_%A.out
#SBATCH --error=logs/full_pipeline_pca_%A.err

# Procrustes Pipeline - Full Pipeline (All Steps)
# Runs sequentially: Step 1 → Step 2 → Step 3 → Step 4 → Step 5
# For all 4 ROIs

set -e

# Activate conda environment
source ~/.bashrc
conda activate nilearn

echo "=== Procrustes Pipeline: Full Execution (PCA Method) ==="
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $(hostname)"
echo "Start time: $(date)"

# Paths
SCRIPT_DIR=/scratch/connectome/haba6030/colorBlind/analysis/validation/scripts/postSRM_procrus
BASELINE_DIR=/scratch/connectome/haba6030/colorBlind/derivatives/baseline

cd $SCRIPT_DIR

# Create logs directory
mkdir -p logs

# ROIs to process
ROIS=(V1 V2 V3 hV4)

# Subjects
SUBJECTS=(01 02 03 04 05 06 08 09 10)

# Step 1: PCA Dimension Reduction (all subjects × all ROIs)
echo ""
echo "========================================="
echo "STEP 1: PCA Dimension Reduction"
echo "========================================="

for ROI in "${ROIS[@]}"; do
    echo ""
    echo "--- Processing ROI: $ROI ---"
    for SUBJECT in "${SUBJECTS[@]}"; do
        echo "  Subject: sub-$SUBJECT"
        python step1a_dimension_reduction_pca.py \
            --subject $SUBJECT \
            --roi $ROI \
            --n-components 50 \
            --baseline-dir $BASELINE_DIR \
            --output-dir results/step1_pca
    done
done

echo ""
echo "✓ Step 1 complete for all subjects and ROIs"

# Step 2: Iterative Procrustes (per ROI)
echo ""
echo "========================================="
echo "STEP 2: Iterative Procrustes"
echo "========================================="

for ROI in "${ROIS[@]}"; do
    echo ""
    echo "--- Processing ROI: $ROI ---"
    python step2_iterative_procrustes.py \
        --roi $ROI \
        --max-iter 10 \
        --tol 0.001 \
        --method pca \
        --input-dir results/step1_pca \
        --output-dir results/step2_procrustes
done

echo ""
echo "✓ Step 2 complete for all ROIs"

# Step 3: Compute Crossnobis RDMs (all subjects × all ROIs)
echo ""
echo "========================================="
echo "STEP 3: Compute Crossnobis RDMs"
echo "========================================="

for ROI in "${ROIS[@]}"; do
    echo ""
    echo "--- Processing ROI: $ROI ---"
    for SUBJECT in "${SUBJECTS[@]}"; do
        echo "  Subject: sub-$SUBJECT"
        python step3_compute_rdms_crossnobis.py \
            --subject $SUBJECT \
            --roi $ROI \
            --method pca \
            --input-dir results/step2_procrustes \
            --output-dir results/step3_rdms
    done
done

echo ""
echo "✓ Step 3 complete for all subjects and ROIs"

# Step 4: Geometric Metrics (per ROI)
echo ""
echo "========================================="
echo "STEP 4: Geometric Metrics"
echo "========================================="

for ROI in "${ROIS[@]}"; do
    echo ""
    echo "--- Processing ROI: $ROI ---"
    python step4_geometric_metrics.py \
        --roi $ROI \
        --method pca \
        --input-dir results/step3_rdms \
        --output-dir results/step4_metrics
done

echo ""
echo "✓ Step 4 complete for all ROIs"

# Step 5: Visualizations (per ROI)
echo ""
echo "========================================="
echo "STEP 5: Visualization & Reporting"
echo "========================================="

for ROI in "${ROIS[@]}"; do
    echo ""
    echo "--- Processing ROI: $ROI ---"
    python step5_visualize_report.py \
        --roi $ROI \
        --method pca \
        --results-root results
done

echo ""
echo "✓ Step 5 complete for all ROIs"

# Summary
echo ""
echo "========================================="
echo "PIPELINE COMPLETE"
echo "========================================="
echo "End time: $(date)"
echo ""
echo "Results saved to: $SCRIPT_DIR/results/"
echo ""
echo "Key files:"
echo "  - Step 1: results/step1_pca/{ROI}/sub-*_metadata.json"
echo "  - Step 2: results/step2_procrustes/{ROI}/convergence_history.json"
echo "  - Step 3: results/step3_rdms/{ROI}/sub-*_split_half_reliability.json"
echo "  - Step 4: results/step4_metrics/{ROI}/hc_vs_cvd_statistics.json"
echo "  - Step 5: results/step5_visualizations/{ROI}_*.png"
echo ""
echo "✓ Full pipeline executed successfully"
