#!/bin/bash
#SBATCH --job-name=mni_diag_compare
#SBATCH --qos=shared
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=01:00:00
#SBATCH --output=logs/mni_diagnosis/mni_compare_sub-%a.out
#SBATCH --error=logs/mni_diagnosis/mni_compare_sub-%a.err
#SBATCH --array=1-10

# MNI Registration Chain Diagnosis - Comparison of Multiple fMRIPrep Versions
#
# Compares:
#   - fmriprep_out_deoblique_v2
#   - fmriprep_out_original_v3
#
# Usage:
#   sbatch run_mni_diagnosis_comparison.sbatch
#
# Or for specific subjects:
#   sbatch --array=1,2,3 run_mni_diagnosis_comparison.sbatch

set -e

# Create log directory
mkdir -p logs/mni_diagnosis

# Subject ID from array task ID
SUBJECT=$(printf "%02d" $SLURM_ARRAY_TASK_ID)

echo "========================================="
echo "MNI Chain Diagnosis - Version Comparison"
echo "========================================="
echo "Subject:  sub-${SUBJECT}"
echo "Node:     $(hostname)"
echo "Date:     $(date)"
echo "========================================="
echo ""

# Paths
SCRIPT_DIR="/scratch/connectome/haba6030/colorBlind"
OUTPUT_DIR="${SCRIPT_DIR}/logs/mni_diagnosis"
RUN=1

# fMRIPrep versions to compare
VERSIONS=(
    "deoblique_v2:/storage/connectome/haba6030/fmriprep_out_deoblique_v2"
    "original_v3:/storage/connectome/haba6030/fmriprep_out_original_v3"
)

# Navigate to project directory first (important for .bashrc)
cd ${SCRIPT_DIR}

# Activate conda environment
echo "🔧 Activating conda environment..."
source ~/.bashrc
conda activate nilearn

echo ""
echo "========================================="
echo "Testing ${#VERSIONS[@]} fMRIPrep versions"
echo "========================================="
echo ""

# Loop through versions
for version_info in "${VERSIONS[@]}"; do
    # Parse version name and path
    VERSION_NAME="${version_info%%:*}"
    FMRIPREP_DIR="${version_info##*:}"

    echo ""
    echo "========================================="
    echo "Version: ${VERSION_NAME}"
    echo "Path: ${FMRIPREP_DIR}"
    echo "========================================="
    echo ""

    # Check if fMRIPrep output exists
    if [ ! -d "${FMRIPREP_DIR}/sub-${SUBJECT}" ]; then
        echo "⚠️  WARNING: fMRIPrep output not found for sub-${SUBJECT}"
        echo "   Expected: ${FMRIPREP_DIR}/sub-${SUBJECT}"
        echo "   Skipping this version..."
        continue
    fi

    # Check if script exists
    if [ ! -f "${SCRIPT_DIR}/diagnose_mni_chain.py" ]; then
        echo "❌ ERROR: diagnose_mni_chain.py not found in ${SCRIPT_DIR}"
        echo "   Please upload the script first using:"
        echo "   scp diagnose_mni_chain.py haba6030@node2:${SCRIPT_DIR}/"
        exit 1
    fi

    # Run diagnosis
    echo "🔍 Running diagnosis for ${VERSION_NAME}..."
    echo ""

    python diagnose_mni_chain.py \
        --subject ${SUBJECT} \
        --fmriprep-dir ${FMRIPREP_DIR} \
        --run ${RUN} \
        --output ${OUTPUT_DIR}/mni_chain_diagnosis_${VERSION_NAME}_sub-${SUBJECT}.txt

    EXIT_CODE=$?

    if [ $EXIT_CODE -eq 0 ]; then
        echo ""
        echo "✅ ${VERSION_NAME} diagnosis completed"
    else
        echo ""
        echo "❌ ${VERSION_NAME} diagnosis failed with exit code: $EXIT_CODE"
    fi

    echo ""
done

# Generate comparison summary
echo ""
echo "========================================="
echo "Generating Comparison Summary"
echo "========================================="
echo ""

SUMMARY_FILE="${OUTPUT_DIR}/comparison_summary_sub-${SUBJECT}.txt"

cat > ${SUMMARY_FILE} <<EOF
========================================
MNI Chain Diagnosis - Version Comparison
========================================
Subject: sub-${SUBJECT}
Date: $(date)

EOF

for version_info in "${VERSIONS[@]}"; do
    VERSION_NAME="${version_info%%:*}"
    FMRIPREP_DIR="${version_info##*:}"

    echo "----------------------------------------" >> ${SUMMARY_FILE}
    echo "Version: ${VERSION_NAME}" >> ${SUMMARY_FILE}
    echo "----------------------------------------" >> ${SUMMARY_FILE}

    if [ ! -d "${FMRIPREP_DIR}/sub-${SUBJECT}" ]; then
        echo "Status: NOT FOUND" >> ${SUMMARY_FILE}
        echo "" >> ${SUMMARY_FILE}
        continue
    fi

    # Extract key info from output
    LOG_FILE="${OUTPUT_DIR}/mni_chain_diagnosis_${VERSION_NAME}_sub-${SUBJECT}.txt"

    if [ -f "${LOG_FILE}" ]; then
        echo "Shape (T1w/BOLD):" >> ${SUMMARY_FILE}
        grep "Shape:" ${LOG_FILE} | tail -2 >> ${SUMMARY_FILE}

        echo "" >> ${SUMMARY_FILE}
        echo "Results:" >> ${SUMMARY_FILE}
        grep -A 3 "T1w → MNI:" ${LOG_FILE} >> ${SUMMARY_FILE}
    else
        echo "Status: DIAGNOSIS FAILED" >> ${SUMMARY_FILE}
    fi

    echo "" >> ${SUMMARY_FILE}
done

cat ${SUMMARY_FILE}

echo ""
echo "========================================="
echo "Comparison Complete"
echo "========================================="
echo "Summary saved to: ${SUMMARY_FILE}"
echo ""
echo "Download results (from local machine):"
echo "  scp haba6030@node2:${SUMMARY_FILE} ./logs/mni_diagnosis/"
echo "========================================="

exit 0
