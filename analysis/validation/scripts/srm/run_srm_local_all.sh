#!/bin/bash
# Run SRM evaluation locally for all subject-ROI pairs

set -e

echo "=========================================="
echo "SRM Evaluation - Local Execution"
echo "=========================================="

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="${SCRIPT_DIR}/results/srm_evaluation/local_$(date +%Y%m%d_%H%M%S)"

# Create output directory
mkdir -p "${OUTPUT_DIR}"

# Subject-ROI pairs
SUBJECTS=(sub-01 sub-02 sub-03 sub-04 sub-05 sub-06 sub-07 sub-08 sub-09 sub-10)
ROIS=(V1 V2 V3 hV4)

# Activate conda environment
echo "Activating srm environment..."
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate srm

# Total tasks
TOTAL=$((${#SUBJECTS[@]} * ${#ROIS[@]}))
CURRENT=0

echo ""
echo "Starting SRM evaluation for ${TOTAL} subject-ROI pairs..."
echo "Output directory: ${OUTPUT_DIR}"
echo ""

# Loop through all combinations
for SUBJECT in "${SUBJECTS[@]}"; do
  for ROI in "${ROIS[@]}"; do
    CURRENT=$((CURRENT + 1))

    echo "=========================================="
    echo "Progress: ${CURRENT}/${TOTAL}"
    echo "Subject: ${SUBJECT}, ROI: ${ROI}"
    echo "Time: $(date +%H:%M:%S)"
    echo "=========================================="

    # Run evaluation (unbuffered output for real-time progress)
    python -u "${SCRIPT_DIR}/evaluate_srm_vs_procrustes.py" \
      --subject "${SUBJECT}" \
      --roi "${ROI}" \
      --output-dir "${OUTPUT_DIR}" \
      2>&1 | tee "${OUTPUT_DIR}/${SUBJECT}_${ROI}_log.txt"

    EXIT_CODE=$?

    if [ ${EXIT_CODE} -eq 0 ]; then
      echo "✓ ${SUBJECT} ${ROI} completed"
    else
      echo "✗ ${SUBJECT} ${ROI} failed (exit code: ${EXIT_CODE})"
    fi

    echo ""
  done
done

echo "=========================================="
echo "All tasks completed!"
echo "=========================================="
echo ""
echo "Results saved to: ${OUTPUT_DIR}"
echo ""
echo "Summary:"
ls -lh "${OUTPUT_DIR}"/*.json | wc -l
echo "result files created"
echo ""
echo "Next steps:"
echo "1. Check results: ls ${OUTPUT_DIR}/*.json"
echo "2. Aggregate: python aggregate_srm_results.py --results-dir ${OUTPUT_DIR} --output-dir ${OUTPUT_DIR}/aggregated"
echo "3. Visualize: python visualize_srm_comparison.py --results-file ${OUTPUT_DIR}/aggregated/srm_summary.json --output-dir ${OUTPUT_DIR}/figures"
