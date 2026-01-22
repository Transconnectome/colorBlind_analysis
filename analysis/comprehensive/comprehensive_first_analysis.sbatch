#!/bin/bash
#SBATCH --job-name=pipeline_m3
#SBATCH --nodelist=node2,node4
#SBATCH --qos=shared
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64GB
#SBATCH --time=72:00:00
#SBATCH --no-requeue
#SBATCH --open-mode=append
#SBATCH --output=analysis/phase1_preprocess_decoding/method3_header_mi/logs/complete_pipeline_%j.out
#SBATCH --error=analysis/phase1_preprocess_decoding/method3_header_mi/logs/complete_pipeline_%j.err

# ============================================================================
# Complete Analysis Pipeline for fMRIPrep method3_header_mi Data
# ============================================================================
#
# This script runs the complete colorBlind analysis pipeline:
#   Phase 0: ROI building + Baseline reconstruction/classification
#   Phase 1: RDM/RSA analysis (inter-subject similarity)
#   Phase 2: Procrustes alignment + CVD-HC comparison (3D characterization)
#   Phase 3: ANOVA feature selection (optional voxel refinement)
#   Phase 4: 3D loss optimization (personalized filter learning)
#
# Data: /storage/connectome/haba6030/fmriprep_out_method3_header_mi
# Events: /storage/connectome/haba6030/bids_editted
# Preprocessing: Baseline32 (sm0, hp0.01, cosine motion, PCA30)
# Subjects: 01-10 (all subjects)
# ROIs: V1, V2, V3, hV4
#
# Research Questions:
#   RQ1: Neural color discrimination in CVD (Phase 0)
#   RQ2: Inter-individual heterogeneity (Phases 1-2)
#   RQ3: Neural-guided personalized filters (Phases 2-4)
#
# ============================================================================

echo "================================================================"
echo "Complete Analysis Pipeline - fMRIPrep method3_header_mi"
echo "Job ID: ${SLURM_JOB_ID}"
echo "Start: $(date)"
echo "================================================================"

# Configuration
DATASET="method3_header_mi"
TIMESTAMP="baseline32_method3_header_mi"
SUBJECTS=(01 02 03 04 05 06 07 08 09 10)
ROIS=(V1 V2 V3 hV4)
HC_SUBJECTS=(01 02 03 04 05 06 07)
CVD_SUBJECTS=(08 09 10)

# Baseline32 preprocessing parameters
SMOOTH=0
HIGHPASS="--highpass 0.01"
MOTION="cosine"
COMPCOR=""
DRIFT="none"
STANDARDIZE=""
USE_PCA="--use-pca"
N_COMPONENTS=30

# Paths
BASE_DIR=/scratch/connectome/haba6030/colorBlind
cd $BASE_DIR

# Create necessary directories
mkdir -p analysis/comprehensive/logs
mkdir -p analysis/comprehensive/results

# Activate conda environment
echo ""
echo "Activating conda environment..."
source ~/.bashrc
conda activate nilearn

# ============================================================================
# Phase 0A: ROI Building and Extraction
# ============================================================================
echo ""
echo "================================================================"
echo "PHASE 0A: ROI Building and Extraction"
echo "================================================================"
echo ""

# Note: roi_pipeline_selected_1202used.py processes all subjects/ROIs
# It should be updated to use fmriprep_out_method3_header_mi
echo "Running ROI pipeline..."
python roi_pipeline_selected_1202used.py --dataset $DATASET

if [ $? -eq 0 ]; then
    echo "✓ ROI building complete"
else
    echo "✗ ROI building failed"
    exit 1
fi

# ============================================================================
# Phase 0B: ROI Overlay Visualization (QC)
# ============================================================================
echo ""
echo "================================================================"
echo "PHASE 0B: ROI Overlay Visualization (QC)"
echo "================================================================"
echo ""

# Note: visualize_roi_overlay.py has hardcoded subjects/ROIs
echo "Creating ROI overlays..."
python visualize_roi_overlay.py --dataset $DATASET

if [ $? -eq 0 ]; then
    echo "✓ Overlay visualization complete"
else
    echo "✗ Overlay visualization failed (non-critical)"
fi

# ============================================================================
# Phase 0C: Baseline Reconstruction & Classification
# ============================================================================
echo ""
echo "================================================================"
echo "PHASE 0C: Baseline Reconstruction & Classification"
echo "================================================================"
echo ""

SUCCESS_COUNT=0
FAIL_COUNT=0
TOTAL_ANALYSES=$((${#SUBJECTS[@]} * ${#ROIS[@]}))

for SUBJECT in "${SUBJECTS[@]}"; do
    for ROI in "${ROIS[@]}"; do
        echo ""
        echo "--- Processing: sub-${SUBJECT}, ROI ${ROI} ---"
        echo "Start: $(date '+%H:%M:%S')"

        python fir_reconstruction_BH2009_system_clean.py \
            --subject $SUBJECT \
            --roi $ROI \
            --dataset $DATASET \
            --timestamp $TIMESTAMP \
            --smooth $SMOOTH \
            $HIGHPASS \
            --motion $MOTION \
            $COMPCOR \
            --drift $DRIFT \
            $STANDARDIZE \
            $USE_PCA \
            --n-components $N_COMPONENTS

        EXIT_CODE=$?
        echo "End: $(date '+%H:%M:%S')"

        if [ $EXIT_CODE -eq 0 ]; then
            echo "✓ Success: sub-${SUBJECT}, ROI ${ROI}"
            SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
        else
            echo "✗ Failed: sub-${SUBJECT}, ROI ${ROI} (exit code: ${EXIT_CODE})"
            FAIL_COUNT=$((FAIL_COUNT + 1))
        fi
    done
done

echo ""
echo "Phase 0C Summary:"
echo "  Successful: ${SUCCESS_COUNT}/${TOTAL_ANALYSES}"
echo "  Failed: ${FAIL_COUNT}/${TOTAL_ANALYSES}"
echo "  Success rate: $(echo "scale=1; $SUCCESS_COUNT * 100 / $TOTAL_ANALYSES" | bc)%"

if [ $FAIL_COUNT -gt 0 ]; then
    echo ""
    echo "⚠️  Warning: $FAIL_COUNT analyses failed in Phase 0C"
    echo "Continuing to Phase 1, but some subjects/ROIs may be incomplete..."
fi

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
echo "Complements baseline Top 50% voxels by FIR R² selection"
echo "Running on all subjects to maximize information quality"
echo ""

# Feature selection is a core step to improve information quality
# Running on all subjects
FEATURE_SUBJECTS=("${SUBJECTS[@]}")  # All 10 subjects

for SUBJECT in "${FEATURE_SUBJECTS[@]}"; do
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
echo "Complete Analysis Pipeline: FINISHED"
echo "================================================================"
echo ""
echo "Results saved to:"
echo "  - Phase 0 (Baseline): derivatives/V3_Comprehensive/BH2009_${DATASET}/${TIMESTAMP}/"
echo "  - Phase 1 (RDM/RSA): derivatives/V3_Comprehensive/phase1_results/"
echo "  - Phase 2 (Procrustes): derivatives/V3_Comprehensive/phase2_procrustes/"
echo "  - Phase 3 (Feature Selection): derivatives/V3_Comprehensive/feature_selection/"
echo "  - Phase 4 (Filters): results/group_level/phase2a_data/models/"
echo ""
echo "Pipeline Summary:"
echo "  ✓ Phase 0A: ROI building (all subjects, 4 ROIs)"
echo "  ✓ Phase 0B: Overlay visualization (QC)"
echo "  ✓ Phase 0C: Baseline reconstruction & classification (40 analyses)"
echo "  ✓ Phase 1:  RDM/RSA analysis (4 ROIs)"
echo "  ✓ Phase 2A: Procrustes alignment (HC group)"
echo "  ✓ Phase 2B: HC common decoder training (4 ROIs)"
echo "  ✓ Phase 2C: CVD testing with Procrustes (3 CVD × 4 ROIs)"
echo "  ✓ Phase 2D: CVD-HC systematic comparison"
echo "  ✓ Phase 3:  ANOVA feature selection (10 subjects × 4 ROIs)"
echo "  ✓ Phase 4:  3D loss filter optimization (3 CVD × 4 ROIs)"
echo ""
echo "Completion time: $(date)"
echo "================================================================"

exit 0
