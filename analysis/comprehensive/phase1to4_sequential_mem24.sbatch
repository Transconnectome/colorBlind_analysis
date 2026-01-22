#!/bin/bash
#SBATCH --job-name=phase1to4_m3_24g
#SBATCH --nodelist=node2,node4
#SBATCH --qos=shared
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
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
SUBJECTS=(01 02 03 04 05 06 07 08 09 10)
ROIS=(V1 V2 V3 hV4)
HC_SUBJECTS=(01 02 03 04 05 06 07)
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
mkdir -p analysis/phase2_baseline_comparing/${DATASET}/results
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

    python analysis/phase2_baseline_comparing/phase1_rsa.py \
        --roi $ROI \
        --timestamp $TIMESTAMP \
        --dataset $DATASET \
        --hc-subjects ${HC_SUBJECTS[@]} \
        --output-dir analysis/phase2_baseline_comparing/${DATASET}/results/rdm_analysis

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
echo "PHASE 2: Procrustes Alignment Analysis"
echo "================================================================"
echo ""

for ROI in "${ROIS[@]}"; do
    echo ""
    echo "--- Procrustes: ROI ${ROI} ---"
    echo "HC subjects: ${HC_SUBJECTS[@]}"
    echo "CVD subjects: ${CVD_SUBJECTS[@]}"

    python analysis/phase2_procrustes_cvd_hc/option2b_procrustes_alignment.py \
        --roi $ROI \
        --timestamp $TIMESTAMP \
        --dataset $DATASET \
        --hc-subjects ${HC_SUBJECTS[@]} \
        --cvd-subjects ${CVD_SUBJECTS[@]} \
        --output-dir analysis/phase2_procrustes_cvd_hc/${DATASET}/results

    if [ $? -eq 0 ]; then
        echo "✓ Procrustes analysis completed for ${ROI}"
    else
        echo "✗ Procrustes analysis failed for ${ROI}"
    fi
done

echo ""
echo "✓ Phase 2 complete"

# ============================================================================
# Phase 3: Filter Learning (CVD Transformation)
# ============================================================================
echo ""
echo "================================================================"
echo "PHASE 3: Filter Learning (CVD → HC Transformation)"
echo "================================================================"
echo ""

# Note: Phase 3 implementation depends on your specific filter learning approach
# This is a placeholder - adjust according to your actual phase3 scripts

echo "Phase 3: Filter learning to be implemented based on Phase 2 results"
echo "  Input: Procrustes-aligned patterns from Phase 2"
echo "  Output: Learned transformation filters"
echo ""
echo "⚠️  Phase 3 script placeholder - update with actual implementation"

# Placeholder for phase 3
# python analysis/phase3_filter_learning/learn_cvd_filters.py \
#     --dataset $DATASET \
#     --timestamp $TIMESTAMP \
#     --input-dir analysis/phase2_procrustes_cvd_hc/${DATASET}/results \
#     --output-dir analysis/phase3_filter_learning/${DATASET}/results

echo ""
echo "✓ Phase 3 placeholder complete"

# ============================================================================
# Phase 4: Summary and Visualization
# ============================================================================
echo ""
echo "================================================================"
echo "PHASE 4: Summary Statistics and Visualization"
echo "================================================================"
echo ""

# Generate summary report
echo "Generating comprehensive summary..."

# Placeholder for summary generation
# python analysis/comprehensive/generate_summary.py \
#     --dataset $DATASET \
#     --timestamp $TIMESTAMP \
#     --output analysis/comprehensive/results/summary_${DATASET}.html

echo ""
echo "✓ Phase 4 placeholder complete"

# ============================================================================
# Final Summary
# ============================================================================
echo ""
echo "================================================================"
echo "Pipeline Complete!"
echo "================================================================"
echo ""
echo "Results saved to:"
echo "  Phase 1: analysis/phase2_baseline_comparing/${DATASET}/results/"
echo "  Phase 2: analysis/phase2_procrustes_cvd_hc/${DATASET}/results/"
echo "  Phase 3: analysis/phase3_filter_learning/${DATASET}/results/"
echo ""
echo "End time: $(date)"
echo "================================================================"
