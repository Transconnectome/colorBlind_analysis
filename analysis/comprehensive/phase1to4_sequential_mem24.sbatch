#!/bin/bash
#SBATCH --job-name=phase1to4_m3_24g
#SBATCH --nodelist=node2,node4
#SBATCH --qos=shared
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=3
#SBATCH --mem=24GB
#SBATCH --time=24:00:00
#SBATCH --no-requeue
#SBATCH --open-mode=append
#SBATCH --output=analysis/comprehensive/logs/phase1to4_m3_24g_%j.out
#SBATCH --error=analysis/comprehensive/logs/phase1to4_m3_24g_%j.err

# ============================================================================
# Phase 1-4: Group-level Analyses - 24GB Optimized
# ============================================================================
#
# This script runs after Phase 0 array job completes
# Phases 1-4 require all subjects' baseline results
#
# Memory: 24GB (sufficient for group-level analyses)
# Nodes: node2 or node4 (whichever is available)
#
# ============================================================================

echo "================================================================"
echo "Phase 1-4: Group-level Analysis Pipeline"
echo "Job ID: ${SLURM_JOB_ID}"
echo "Node: $(hostname)"
echo "Memory: 24GB"
echo "Start: $(date)"
echo "================================================================"

# Configuration
DATASET="method3_header_mi"
TIMESTAMP="baseline32_method3_header_mi"
SUBJECTS=(01 02 03 04 05 06 08 09 10)
ROIS=(V1 V2 V3 hV4)
HC_SUBJECTS=(01 02 03 04 05 06)  # Excluding sub-07: too few voxels (6-16 voxels)
CVD_SUBJECTS=(08 09 10)

# Paths
BASE_DIR=/scratch/connectome/haba6030/colorBlind
cd $BASE_DIR

# Create necessary directories
echo ""
echo "Creating required directories..."
mkdir -p analysis/comprehensive/logs
mkdir -p analysis/comprehensive/results
mkdir -p analysis/phase1_preprocess_decoding/${DATASET}/results
mkdir -p analysis/phase2_decoder_comparing/${DATASET}/results
mkdir -p analysis/phase2_procrustes_cvd_hc/${DATASET}/results
mkdir -p analysis/phase3_filter_learning/${DATASET}/results

# Activate conda environment
echo ""
echo "Activating conda environment..."
source ~/.bashrc
conda activate nilearn

if [ $? -ne 0 ]; then
    echo "✗ ERROR: Failed to activate conda environment 'nilearn'"
    exit 1
fi

echo "✓ Conda environment activated: $(which python)"
echo ""

# ============================================================================
# Phase 1: RDM/RSA Analysis
# ============================================================================
echo ""
echo "================================================================"
echo "PHASE 1: RDM/RSA Analysis (Representational Similarity)"
echo "================================================================"
echo ""

for ROI in "${ROIS[@]}"; do
    echo ""
    echo "--- RDM Analysis: ROI ${ROI} ---"
    echo "HC subjects: ${HC_SUBJECTS[@]}"

    python analysis/phase2_decoder_comparing/phase1_rsa.py \
        --roi $ROI \
        --timestamp $TIMESTAMP \
        --dataset $DATASET \
        --subjects ${HC_SUBJECTS[@]} \
        --output-dir analysis/phase2_decoder_comparing/${DATASET}/results/rdm_analysis

    if [ $? -eq 0 ]; then
        echo "✓ RDM analysis completed for ${ROI}"
    else
        echo "✗ RDM analysis failed for ${ROI}"
    fi
done

echo ""
echo "✓ Phase 1 complete"

# ============================================================================
# Phase 2: Procrustes Alignment (CVD-HC Comparison)
# ============================================================================
echo ""
echo "================================================================"
echo "PHASE 2: Procrustes Alignment Analysis (All ROIs)"
echo "================================================================"
echo ""
echo "HC subjects: ${HC_SUBJECTS[@]}"
echo "ROIs: ${ROIS[@]}"
echo ""
echo "Note: Procrustes script processes all ROIs together"
echo ""

python analysis/phase2_procrustes_cvd_hc/option2b_procrustes_alignment.py \
    --timestamp $TIMESTAMP \
    --dataset $DATASET \
    --hc-subjects ${HC_SUBJECTS[@]} \
    --cvd-subjects ${CVD_SUBJECTS[@]} \
    --rois ${ROIS[@]}

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Phase 2 (Procrustes) completed for all ROIs"
else
    echo ""
    echo "✗ Phase 2 (Procrustes) failed"
fi

echo ""
echo "✓ Phase 2 complete"

# ============================================================================
# Phase 3: Filter Learning (CVD → HC Transformation)
# ============================================================================
echo ""
echo "================================================================"
echo "PHASE 3: Filter Learning (CVD → HC Transformation)"
echo "================================================================"
echo ""
echo "Learning linear filters for CVD subjects..."
echo "  Target: HC group template from Phase 2 Procrustes alignment"
echo "  Method: Least-squares linear transformation (Y = A @ X + b)"
echo ""

PHASE3_SUCCESS=0
PHASE3_TOTAL=0

for ROI in "${ROIS[@]}"; do
    echo ""
    echo "--- Training filters for ROI ${ROI} ---"

    python analysis/comprehensive/run_phase3_filter_learning.py \
        --timestamp $TIMESTAMP \
        --roi $ROI \
        --cvd-subjects ${CVD_SUBJECTS[@]} \
        --hc-subjects ${HC_SUBJECTS[@]} \
        --dataset $DATASET

    if [ $? -eq 0 ]; then
        echo "✓ Filter learning completed for ${ROI}"
        PHASE3_SUCCESS=$((PHASE3_SUCCESS + 1))
    else
        echo "✗ Filter learning failed for ${ROI}"
    fi

    PHASE3_TOTAL=$((PHASE3_TOTAL + 1))
done

echo ""
echo "Phase 3 Summary: ${PHASE3_SUCCESS}/${PHASE3_TOTAL} ROIs completed"
echo ""
echo "✓ Phase 3 complete"

# ============================================================================
# Phase 4: Summary and Visualization
# ============================================================================
echo ""
echo "================================================================"
echo "PHASE 4: Summary Statistics and Visualization"
echo "================================================================"
echo ""

echo "Generating comprehensive summary report..."
echo ""

python analysis/comprehensive/generate_phase_summary.py \
    --dataset $DATASET \
    --timestamp $TIMESTAMP

PHASE4_EXIT=$?

if [ $PHASE4_EXIT -eq 0 ]; then
    echo ""
    echo "✓ Phase 4 (Summary) completed successfully"
else
    echo ""
    echo "✗ Phase 4 (Summary) failed (exit code: ${PHASE4_EXIT})"
fi

echo ""
echo "✓ Phase 4 complete"

# ============================================================================
# Final Summary
# ============================================================================
echo ""
echo "================================================================"
echo "Pipeline Complete!"
echo "================================================================"
echo ""
echo "Subjects analyzed:"
echo "  HC: ${HC_SUBJECTS[@]} (6 subjects, sub-07 excluded)"
echo "  CVD: ${CVD_SUBJECTS[@]} (3 subjects)"
echo ""
echo "Results saved to:"
echo "  Phase 0: analysis/phase1_preprocess_decoding/${DATASET}/results/"
echo "  Phase 1: analysis/phase2_decoder_comparing/${DATASET}/results/"
echo "  Phase 2: analysis/comprehensive/results/${TIMESTAMP}/"
echo "  Phase 3: analysis/comprehensive/results/${TIMESTAMP}/[ROI]/filter_learning/"
echo "  Phase 4 Summary: analysis/comprehensive/results/COMPREHENSIVE_SUMMARY_${TIMESTAMP}.txt"
echo ""
echo "Key outputs:"
echo "  - Procrustes alignment: analysis/comprehensive/results/${TIMESTAMP}/"
echo "  - Learned filters: analysis/comprehensive/results/${TIMESTAMP}/[ROI]/filter_learning/"
echo "  - Summary report: analysis/comprehensive/results/COMPREHENSIVE_SUMMARY_${TIMESTAMP}.txt"
echo "  - Visualizations: analysis/comprehensive/results/${TIMESTAMP}/*/figures/"
echo ""
echo "End time: $(date)"
echo "================================================================"
