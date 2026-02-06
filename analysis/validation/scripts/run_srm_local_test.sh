#!/bin/bash
# Test SRM evaluation locally with 1-2 subject-ROI pairs

set -e

echo "=========================================="
echo "SRM Evaluation - Local Test"
echo "=========================================="

# Configuration
SCRIPT_DIR="/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/validation/scripts"
OUTPUT_DIR="${SCRIPT_DIR}/results/srm_evaluation/test_local_$(date +%Y%m%d_%H%M%S)"

# Create output directory
mkdir -p "${OUTPUT_DIR}"

# Activate conda environment
echo "Activating srm environment..."
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate srm

# Test with 2 subject-ROI pairs
TEST_PAIRS=(
  "sub-01 V1"
  "sub-02 V2"
)

echo ""
echo "Testing with ${#TEST_PAIRS[@]} subject-ROI pairs..."
echo "Output directory: ${OUTPUT_DIR}"
echo ""

for PAIR in "${TEST_PAIRS[@]}"; do
  SUBJECT=$(echo ${PAIR} | awk '{print $1}')
  ROI=$(echo ${PAIR} | awk '{print $2}')

  echo "=========================================="
  echo "Testing: ${SUBJECT} ${ROI}"
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
    echo "✓ ${SUBJECT} ${ROI} completed successfully"
  else
    echo "✗ ${SUBJECT} ${ROI} failed (exit code: ${EXIT_CODE})"
    exit 1
  fi

  echo ""
done

echo "=========================================="
echo "Test completed successfully!"
echo "=========================================="
echo ""
echo "Results:"
ls -lh "${OUTPUT_DIR}"
echo ""
echo "Check results:"
echo "  JSON: cat ${OUTPUT_DIR}/*.json | python -m json.tool | head -50"
echo "  Plots: open ${OUTPUT_DIR}/*.png"
echo ""
echo "If test looks good, run full analysis:"
echo "  bash run_srm_local_all.sh"
