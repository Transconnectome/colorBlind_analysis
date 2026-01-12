#!/bin/bash
#SBATCH --job-name=phase1to4_v3
#SBATCH --nodelist=node2
#SBATCH --qos=shared
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64GB
#SBATCH --time=24:00:00
#SBATCH --output=analysis/comprehensive/logs/phase1to4_v3_%j.out
#SBATCH --error=analysis/comprehensive/logs/phase1to4_v3_%j.err

# ============================================================================
# Phase 1-4: Group-level Analyses (Sequential)
# ============================================================================
#
# This script runs after Phase 0 array job completes
# Phases 1-4 require all subjects' baseline results
#
# ============================================================================

echo "================================================================"
echo "Phase 1-4: Group-level Analysis Pipeline"
echo "Job ID: ${SLURM_JOB_ID}"
echo "Start: $(date)"
echo "================================================================"

# Configuration
DATASET="original_v3"
TIMESTAMP="baseline32_original_v3"
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
mkdir -p derivatives/V3_Comprehensive/phase1_results
mkdir -p derivatives/V3_Comprehensive/phase2_procrustes
mkdir -p derivatives/V3_Comprehensive/feature_selection
mkdir -p analysis/comprehensive/results/phase2a_data/patterns
mkdir -p analysis/comprehensive/results/phase2a_data/models
mkdir -p analysis/phase1_preprocess_decoding
mkdir -p analysis/phase2_baseline_comparing
mkdir -p analysis/phase2_procrustes_cvd_hc
mkdir -p scripts/phase2a_filter_learning

# Activate conda environment
echo ""
echo "Activating conda environment..."
source ~/.bashrc
conda activate nilearn

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

    python phase1_rsa.py \
        --roi $ROI \
        --timestamp $TIMESTAMP \
        --dataset $DATASET \
        --subjects "${HC_SUBJECTS[@]}"

    if [ $? -eq 0 ]; then
        echo "✓ RDM analysis complete: ${ROI}"
    else
        echo "✗ RDM analysis failed: ${ROI}"
    fi
done

# ============================================================================
# Phase 2A: Procrustes-based Group Alignment
# ============================================================================
echo ""
echo "================================================================"
echo "PHASE 2A: Procrustes-based Group Alignment"
echo "================================================================"
echo ""

echo "HC subjects for alignment: ${HC_SUBJECTS[@]}"
echo "ROIs: ${ROIS[@]}"
echo ""

python option2b_procrustes_alignment.py \
    --timestamp $TIMESTAMP \
    --dataset $DATASET \
    --hc-subjects "${HC_SUBJECTS[@]}" \
    --rois "${ROIS[@]}"

if [ $? -eq 0 ]; then
    echo "✓ Procrustes alignment complete"
else
    echo "✗ Procrustes alignment failed"
    exit 1
fi

# ============================================================================
# Phase 2B: Procrustes-based Reconstruction (HC training)
# ============================================================================
echo ""
echo "================================================================"
echo "PHASE 2B: Procrustes Reconstruction - HC Training"
echo "================================================================"
echo ""

for ROI in "${ROIS[@]}"; do
    echo ""
    echo "--- Training HC model: ROI ${ROI} ---"

    python reconstruction_with_procrustes.py \
        --mode train \
        --roi $ROI \
        --timestamp $TIMESTAMP \
        --dataset $DATASET \
        --hc-subjects "${HC_SUBJECTS[@]}"

    if [ $? -eq 0 ]; then
        echo "✓ HC training complete: ${ROI}"
    else
        echo "✗ HC training failed: ${ROI}"
    fi
done

# ============================================================================
# Phase 2C: Procrustes-based Reconstruction (CVD testing)
# ============================================================================
echo ""
echo "================================================================"
echo "PHASE 2C: Procrustes Reconstruction - CVD Testing"
echo "================================================================"
echo ""

for ROI in "${ROIS[@]}"; do
    echo ""
    echo "--- Testing CVD subjects: ROI ${ROI} ---"
    echo "CVD subjects: ${CVD_SUBJECTS[@]}"

    python reconstruction_with_procrustes.py \
        --mode test \
        --roi $ROI \
        --timestamp $TIMESTAMP \
        --dataset $DATASET \
        --hc-subjects "${HC_SUBJECTS[@]}" \
        --cvd-subjects "${CVD_SUBJECTS[@]}"

    if [ $? -eq 0 ]; then
        echo "✓ CVD testing complete: ${ROI}"
    else
        echo "✗ CVD testing failed: ${ROI}"
    fi
done

# ============================================================================
# Phase 2D: CVD vs HC Systematic Comparison
# ============================================================================
echo ""
echo "================================================================"
echo "PHASE 2D: CVD vs HC Systematic Comparison"
echo "================================================================"
echo ""

echo "Comparing CVD vs HC patterns..."
echo "HC: ${HC_SUBJECTS[@]}"
echo "CVD: ${CVD_SUBJECTS[@]}"
echo ""

python option2d_procrustes_cvd_comparison.py \
    --timestamp $TIMESTAMP \
    --dataset $DATASET \
    --hc-subjects "${HC_SUBJECTS[@]}" \
    --cvd-subjects "${CVD_SUBJECTS[@]}" \
    --rois "${ROIS[@]}"

if [ $? -eq 0 ]; then
    echo "✓ CVD-HC comparison complete"
else
    echo "✗ CVD-HC comparison failed"
fi

# ============================================================================
# Phase 3: Feature Selection (ANOVA F-test)
# ============================================================================
echo ""
echo "================================================================"
echo "PHASE 3: ANOVA-based Feature Selection"
echo "================================================================"
echo ""
echo "NOTE: Core quality improvement step for voxel refinement"
echo "Running on all subjects to maximize information quality"
echo ""

for SUBJECT in "${SUBJECTS[@]}"; do
    for ROI in "${ROIS[@]}"; do
        echo ""
        echo "--- Feature Selection: sub-${SUBJECT}, ROI ${ROI} ---"

        # Check if baseline results exist (new structure: sub-XX/ROI/)
        BASELINE_DIR="derivatives/V3_Comprehensive/BH2009_${DATASET}/${TIMESTAMP}/sub-${SUBJECT}/${ROI}"
        if [ -d "$BASELINE_DIR" ]; then
            python feature_selection_anova.py \
                --subject $SUBJECT \
                --roi $ROI \
                --timestamp $TIMESTAMP \
                --dataset $DATASET

            if [ $? -eq 0 ]; then
                echo "✓ Feature selection complete: sub-${SUBJECT}, ${ROI}"
            else
                echo "✗ Feature selection failed: sub-${SUBJECT}, ${ROI}"
            fi
        else
            echo "⚠️  Baseline results not found, skipping feature selection"
        fi
    done
done

# ============================================================================
# Phase 4: 3D Loss Function Optimization (Filter Learning)
# ============================================================================
echo ""
echo "================================================================"
echo "PHASE 4: 3D Loss Function Optimization (CVD Filter Learning)"
echo "================================================================"
echo ""
echo "Learning personalized filters: F = Y @ A + b"
echo "3D Loss: λ_mag × L_magnitude + λ_base × L_baseline + λ_rdm × L_RDM"
echo ""

# Extract patterns first (from Procrustes-aligned data)
echo "--- Extracting patterns for filter learning ---"

for SUBJECT in "${CVD_SUBJECTS[@]}"; do
    for ROI in "${ROIS[@]}"; do
        echo "Extracting patterns: sub-${SUBJECT}, ${ROI}"

        python phase2a_extract_patterns.py \
            --cvd-subject $SUBJECT \
            --roi $ROI \
            --timestamp $TIMESTAMP \
            --dataset $DATASET

        if [ $? -eq 0 ]; then
            echo "✓ Pattern extraction complete: sub-${SUBJECT}, ${ROI}"
        else
            echo "✗ Pattern extraction failed: sub-${SUBJECT}, ${ROI}"
        fi
    done
done

# Train filters with 3D loss optimization
echo ""
echo "--- Training personalized filters ---"

for SUBJECT in "${CVD_SUBJECTS[@]}"; do
    for ROI in "${ROIS[@]}"; do
        echo ""
        echo "Training filter: sub-${SUBJECT}, ${ROI}"

        python phase2a_train_filter.py \
            --cvd-subject $SUBJECT \
            --roi $ROI \
            --timestamp $TIMESTAMP \
            --dataset $DATASET \
            --max-epochs 1000 \
            --learning-rate 1e-3

        if [ $? -eq 0 ]; then
            echo "✓ Filter training complete: sub-${SUBJECT}, ${ROI}"
        else
            echo "✗ Filter training failed: sub-${SUBJECT}, ${ROI}"
        fi
    done
done

# Analyze filter learning results
echo ""
echo "--- Analyzing filter learning results ---"

python phase2a_analyze_results.py \
    --timestamp $TIMESTAMP \
    --dataset $DATASET

if [ $? -eq 0 ]; then
    echo "✓ Filter analysis complete"
else
    echo "✗ Filter analysis failed"
fi

# ============================================================================
# Pipeline Complete
# ============================================================================
echo ""
echo "================================================================"
echo "Phase 1-4 Analysis Pipeline: FINISHED"
echo "================================================================"
echo ""
echo "Results saved to:"
echo "  - Phase 1 (RDM/RSA): derivatives/V3_Comprehensive/phase1_results/"
echo "  - Phase 2 (Procrustes): derivatives/V3_Comprehensive/phase2_procrustes/"
echo "  - Phase 3 (Feature Selection): derivatives/V3_Comprehensive/feature_selection/"
echo "  - Phase 4 (Filters): results/group_level/phase2a_data/models/"
echo ""
echo "Completion time: $(date)"
echo "================================================================"

exit 0
