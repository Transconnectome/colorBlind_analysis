#!/bin/bash
# =============================================================================
# Memory Diagnostic Script for Phase 0 and Phase 1-4
# =============================================================================
#
# This script tests memory usage for a single subject to determine optimal
# SLURM settings before running full array jobs.
#
# Usage:
#   bash diagnose_memory.sh [test_subject_id]
#
# Example:
#   bash diagnose_memory.sh 01
#
# =============================================================================

set -e  # Exit on error

# Configuration
TEST_SUBJECT="${1:-01}"
DATASET="method3_header_mi"
TIMESTAMP="baseline32_${DATASET}"
TEST_ROI="V1"

BASE_DIR="/scratch/connectome/haba6030/colorBlind"
PROFILE_DIR="${BASE_DIR}/analysis/comprehensive/memory_profiles"
mkdir -p "${PROFILE_DIR}"

echo "================================================================================"
echo "Memory Diagnostic for colorBlind Analysis Pipeline"
echo "================================================================================"
echo "Test Subject: sub-${TEST_SUBJECT}"
echo "Dataset: ${DATASET}"
echo "Profile Directory: ${PROFILE_DIR}"
echo "================================================================================"
echo ""

# Activate conda environment
source ~/.bashrc
conda activate nilearn

cd ${BASE_DIR}

# =============================================================================
# Test 1: ROI Pipeline (Phase 0A)
# =============================================================================
echo ""
echo "--------------------------------------------------------------------------------"
echo "TEST 1: ROI Pipeline (Phase 0A)"
echo "--------------------------------------------------------------------------------"
echo "This builds ROI masks for one subject (4 ROIs)"
echo ""

/usr/bin/time -v python analysis/phase1_preprocess_decoding/roi_pipeline_selected_1202used.py ${TEST_SUBJECT} --dataset ${DATASET} 2>&1 | tee "${PROFILE_DIR}/roi_pipeline_sub${TEST_SUBJECT}.log"

# Extract memory from /usr/bin/time output
MAX_RSS=$(grep "Maximum resident set size" "${PROFILE_DIR}/roi_pipeline_sub${TEST_SUBJECT}.log" | awk '{print $6}')
MAX_RSS_GB=$(echo "scale=2; ${MAX_RSS} / 1024 / 1024" | bc)

echo ""
echo "ROI Pipeline Memory Usage:"
echo "  Peak RSS: ${MAX_RSS_GB}GB"
echo "  Recommendation: Use --mem=$(($(echo ${MAX_RSS_GB} | cut -d. -f1) + 5))G (adding 5GB buffer)"
echo ""

# =============================================================================
# Test 2: Baseline Decoding - Single ROI (Phase 0B)
# =============================================================================
echo ""
echo "--------------------------------------------------------------------------------"
echo "TEST 2: Baseline Decoding - Single ROI (Phase 0B)"
echo "--------------------------------------------------------------------------------"
echo "This runs baseline decoding for one subject-ROI pair"
echo ""

/usr/bin/time -v python analysis/phase1_preprocess_decoding/fir_reconstruction_BH2009_system_clean.py \
    --subject ${TEST_SUBJECT} \
    --roi ${TEST_ROI} \
    --dataset ${DATASET} \
    --timestamp ${TIMESTAMP} \
    --smooth 0 \
    --highpass 0.01 \
    --motion cosine \
    --use-pca \
    --n-components 30 \
    2>&1 | tee "${PROFILE_DIR}/baseline_sub${TEST_SUBJECT}_${TEST_ROI}.log"

MAX_RSS=$(grep "Maximum resident set size" "${PROFILE_DIR}/baseline_sub${TEST_SUBJECT}_${TEST_ROI}.log" | awk '{print $6}')
MAX_RSS_GB=$(echo "scale=2; ${MAX_RSS} / 1024 / 1024" | bc)

echo ""
echo "Baseline Decoding (Single ROI) Memory Usage:"
echo "  Peak RSS: ${MAX_RSS_GB}GB"
echo "  Recommendation: Use --mem=$(($(echo ${MAX_RSS_GB} | cut -d. -f1) + 5))G (adding 5GB buffer)"
echo ""

# =============================================================================
# Test 3: Baseline Decoding - All 4 ROIs (Phase 0C)
# =============================================================================
echo ""
echo "--------------------------------------------------------------------------------"
echo "TEST 3: Baseline Decoding - All 4 ROIs (Sequential)"
echo "--------------------------------------------------------------------------------"
echo "This simulates a full Phase 0 array task (1 subject × 4 ROIs)"
echo ""

ROIS=(V1 V2 V3 hV4)
START_TIME=$(date +%s)

for ROI in "${ROIS[@]}"; do
    echo "Processing ${ROI}..."
    /usr/bin/time -v python analysis/phase1_preprocess_decoding/fir_reconstruction_BH2009_system_clean.py \
        --subject ${TEST_SUBJECT} \
        --roi ${ROI} \
        --dataset ${DATASET} \
        --timestamp ${TIMESTAMP} \
        --smooth 0 \
        --highpass 0.01 \
        --motion cosine \
        --use-pca \
        --n-components 30 \
        2>&1 | tee "${PROFILE_DIR}/baseline_sub${TEST_SUBJECT}_${ROI}_full.log"
done

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo ""
echo "All 4 ROIs completed in ${DURATION} seconds ($((DURATION / 60)) minutes)"
echo ""

# Analyze all ROIs
echo "Memory Usage Summary (All 4 ROIs):"
echo "-----------------------------------"

MAX_RSS_TOTAL=0
for ROI in "${ROIS[@]}"; do
    MAX_RSS=$(grep "Maximum resident set size" "${PROFILE_DIR}/baseline_sub${TEST_SUBJECT}_${ROI}_full.log" | awk '{print $6}')
    MAX_RSS_GB=$(echo "scale=2; ${MAX_RSS} / 1024 / 1024" | bc)
    echo "  ${ROI}: ${MAX_RSS_GB}GB"

    # Track maximum (handle empty variables)
    MAX_RSS_INT=$(echo ${MAX_RSS_GB} | cut -d. -f1)
    if [ -n "${MAX_RSS_INT}" ] && [ ${MAX_RSS_INT} -gt ${MAX_RSS_TOTAL} ]; then
        MAX_RSS_TOTAL=${MAX_RSS_INT}
    fi
done

echo ""
echo "Peak Memory Across All ROIs: ${MAX_RSS_TOTAL}GB"
echo "Recommended SLURM Setting: --mem=$((MAX_RSS_TOTAL + 10))G (adding 10GB buffer)"
echo ""

# =============================================================================
# Summary and Recommendations
# =============================================================================
echo ""
echo "================================================================================"
echo "SUMMARY AND RECOMMENDATIONS"
echo "================================================================================"
echo ""
echo "Phase 0 (per subject, 4 ROIs sequential):"
echo "  Measured Peak: ~${MAX_RSS_TOTAL}GB"
echo "  Recommended: --mem=$((MAX_RSS_TOTAL + 10))G"
echo "  Safe Conservative: --mem=64G"
echo "  Memory Optimized: --mem=45G (if peak < 35GB)"
echo ""
echo "Array Job Limits (node2: 450GB usable):"
echo "  64GB per task: max 7 concurrent (--array=1-10%7)"
echo "  45GB per task: max 10 concurrent (--array=1-10)"
echo ""
echo "Time per subject (4 ROIs): ~$((DURATION / 60)) minutes"
echo "Estimated total time (10 subjects parallel):"
echo "  With 7 concurrent: ~$(((DURATION * 10 / 7) / 60)) minutes"
echo "  With 10 concurrent: ~$((DURATION / 60)) minutes"
echo ""
echo "================================================================================"
echo ""
echo "Profile logs saved to: ${PROFILE_DIR}/"
echo ""
echo "Next steps:"
echo "1. Review memory usage above"
echo "2. Choose appropriate sbatch file:"
echo "   - phase0_parallel.sbatch (64GB × 10 tasks)"
echo "   - phase0_parallel_throttle.sbatch (64GB × 7 tasks)"
echo "   - phase0_parallel_mem45.sbatch (45GB × 10 tasks)"
echo "3. Monitor actual job: sstat -j JOB_ID --format=JobID,MaxRSS,MaxVMSize"
echo ""
echo "================================================================================"
