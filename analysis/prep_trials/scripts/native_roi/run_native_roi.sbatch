#!/bin/bash
#SBATCH --job-name=native_roi
#SBATCH --output=/scratch/connectome/haba6030/colorBlind/analysis/prep_trials/results/native_roi/logs/native_roi_%A_%a.out
#SBATCH --error=/scratch/connectome/haba6030/colorBlind/analysis/prep_trials/results/native_roi/logs/native_roi_%A_%a.err
#SBATCH --qos=shared
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=2
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --array=0-9

# ============================================================================
# T1w Space ROI Pipeline - SLURM Array Job
# ============================================================================
#
# Dataset: method3_header_mi (MI-based coregistration)
# Goal: Transform Wang atlas ROIs to T1w space for individual analysis
#
# Array jobs: 10 (one per subject, each processing 4 ROIs sequentially)
#
# Advantages over MNI-based analysis:
#   - Higher resolution (1mm T1w vs 2mm MNI)
#   - Independent of MNI normalization quality
#   - Preserves individual anatomical structure
#   - Better alignment with improved BOLD→T1w registration (MI method)
#
# ============================================================================

set -e

# ============================================================================
# Environment Setup
# ============================================================================

# Change to project directory
PROJECT_DIR="/scratch/connectome/haba6030/colorBlind"
cd "$PROJECT_DIR"

# Activate conda environment
source ~/.bashrc
conda activate nilearn

# Script directory
SCRIPT_DIR="${PROJECT_DIR}/analysis/prep_trials/scripts/native_roi"

# Output directory
OUTPUT_DIR="${PROJECT_DIR}/analysis/prep_trials/results/native_roi"
mkdir -p "${OUTPUT_DIR}/logs"

# ============================================================================
# Array Job Configuration
# ============================================================================

# Define subjects and ROIs (all 10 subjects with method3_header_mi)
SUBJECTS=(01 02 03 04 05 06 07 08 09 10)
ROIS=(V1 V2 V3 hV4)
RUN=1

# Get subject for this array task
SUBJECT=${SUBJECTS[$SLURM_ARRAY_TASK_ID]}

# ============================================================================
# Job Header
# ============================================================================

echo "================================================================================"
echo "SLURM Job: T1w Space ROI Pipeline"
echo "================================================================================"
echo "Job ID: ${SLURM_JOB_ID}"
echo "Array Task ID: ${SLURM_ARRAY_TASK_ID}"
echo "Node: $(hostname)"
echo ""
echo "Configuration:"
echo "  Subject: sub-${SUBJECT}"
echo "  ROIs: V1, V2, V3, hV4 (sequential)"
echo "  Run: ${RUN}"
echo "  Analysis space: T1w (1mm resolution)"
echo ""
echo "Start time: $(date)"
echo "================================================================================"
echo ""

# ============================================================================
# Process Each ROI Sequentially
# ============================================================================

for ROI in "${ROIS[@]}"; do
    echo ""
    echo "╔═══════════════════════════════════════════════════════════════════════════════╗"
    echo "║ Processing: sub-${SUBJECT} ${ROI}                                                       "
    echo "╚═══════════════════════════════════════════════════════════════════════════════╝"
    echo ""

    # ========================================================================
    # Step 1: Transform ROI to T1w space
    # ========================================================================

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Step 1: Transforming ${ROI} to T1w space"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    bash "${SCRIPT_DIR}/transform_roi_to_native.sh" ${SUBJECT} ${ROI} ${RUN}

    if [ $? -ne 0 ]; then
        echo ""
        echo "❌ ${ROI} transformation failed - continuing with next ROI"
        continue
    fi

    echo ""

    # ========================================================================
    # Step 2: Create detailed visualizations
    # ========================================================================

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Step 2: Creating ${ROI} visualizations"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    python "${SCRIPT_DIR}/visualize_native_roi.py" \
        --subject ${SUBJECT} \
        --roi ${ROI} \
        --run ${RUN}

    if [ $? -ne 0 ]; then
        echo ""
        echo "⚠ ${ROI} visualization failed (non-critical)"
    fi

    echo ""

    # ========================================================================
    # Step 3: Run functional sanity check
    # ========================================================================

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Step 3: Running ${ROI} functional sanity check"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    python "${SCRIPT_DIR}/sanity_check_native_roi.py" \
        --subject ${SUBJECT} \
        --roi ${ROI} \
        --run ${RUN}

    if [ $? -ne 0 ]; then
        echo ""
        echo "⚠ ${ROI} functional check failed (non-critical)"
    fi

    echo ""
    echo "✓ ${ROI} processing complete"
    echo ""

done

# ============================================================================
# Summary
# ============================================================================

echo "================================================================================"
echo "Subject Complete"
echo "================================================================================"
echo "Subject: sub-${SUBJECT}"
echo "ROIs processed: V1, V2, V3, hV4"
echo "Analysis space: T1w (1mm resolution)"
echo ""
echo "Output directory:"
echo "  ${OUTPUT_DIR}/sub-${SUBJECT}/"
echo ""
echo "End time: $(date)"
echo "================================================================================"
