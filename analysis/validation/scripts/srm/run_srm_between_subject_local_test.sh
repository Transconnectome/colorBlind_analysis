#!/bin/bash
# Test SRM Between-Subject evaluation locally (HC vs CVD)

set -e

echo "=========================================="
echo "SRM Between-Subject - Local Test"
echo "=========================================="

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="${SCRIPT_DIR}/results/srm_between_subject/test_local_$(date +%Y%m%d_%H%M%S)"

# Create output directory
mkdir -p "${OUTPUT_DIR}"

# Activate conda environment
echo "Activating srm environment..."
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate srm

echo ""
echo "Testing Between-Subject SRM (HC vs CVD)"
echo "This tests whether SRM can detect representational differences between groups"
echo ""
echo "Output directory: ${OUTPUT_DIR}"
echo ""

# Test ROIs (all 4 ROIs)
TEST_ROIS=(
  "V1"
  "V2"
  "V3"
  "hV4"
)

# Default k values per ROI (Beta-based SRM: k ≤ 8)
declare -A K_VALUES
K_VALUES["V1"]=4
K_VALUES["V2"]=4
K_VALUES["V3"]=3
K_VALUES["hV4"]=4

SUCCESS_COUNT=0
FAIL_COUNT=0

for ROI in "${TEST_ROIS[@]}"; do
  K=${K_VALUES[$ROI]}

  echo "=========================================="
  echo "Testing: ${ROI} (k=${K})"
  echo "Time: $(date +%H:%M:%S)"
  echo "=========================================="
  echo ""

  # Run between-subject SRM
  python -u "${SCRIPT_DIR}/evaluate_srm_between_subject.py" \
    --roi "${ROI}" \
    --n-features "${K}" \
    --output-dir "${OUTPUT_DIR}" \
    2>&1 | tee "${OUTPUT_DIR}/${ROI}_log.txt"

  EXIT_CODE=$?

  if [ ${EXIT_CODE} -eq 0 ]; then
    echo ""
    echo "✓ ${ROI} completed successfully"
    SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
  else
    echo ""
    echo "✗ ${ROI} failed (exit code: ${EXIT_CODE})"
    FAIL_COUNT=$((FAIL_COUNT + 1))
  fi

  echo ""
done

echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo "Successful: ${SUCCESS_COUNT}"
echo "Failed: ${FAIL_COUNT}"
echo ""
echo "Results:"
ls -lh "${OUTPUT_DIR}"
echo ""

if [ ${SUCCESS_COUNT} -gt 0 ]; then
  echo "Check results:"
  echo ""
  echo "1. View JSON results:"
  echo "   cat ${OUTPUT_DIR}/*_srm_between_subject_results.json | python -m json.tool"
  echo ""
  echo "2. View disparity plots:"
  echo "   open ${OUTPUT_DIR}/*_hc_cvd_disparity_comparison.png"
  echo ""
  echo "3. Visualize color representational space:"
  echo "   bash run_color_space_visualization.sh ${OUTPUT_DIR}"
  echo ""
  echo "4. Key findings to check:"
  echo "   - HC-to-HC disparity (should be lower)"
  echo "   - CVD-to-HC disparity (should be higher)"
  echo "   - CVD-to-CVD disparity (internal consistency)"
  echo "   - Statistical significance (p-value < 0.05?)"
  echo "   - Effect size (Cohen's d)"
  echo ""
fi

if [ ${FAIL_COUNT} -eq 0 ]; then
  echo "✅ All tests passed!"
  echo ""
  echo "Next steps:"
  echo "1. Review results above"
  echo "2. If results look good, run all 4 ROIs:"
  echo "   bash run_srm_between_subject_local_all.sh"
  echo ""
else
  echo "⚠️  Some tests failed. Check logs in ${OUTPUT_DIR}"
fi

echo "=========================================="
