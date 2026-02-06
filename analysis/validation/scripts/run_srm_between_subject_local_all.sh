#!/bin/bash
# Run SRM Between-Subject evaluation locally for all ROIs (HC vs CVD)

set -e

echo "=========================================="
echo "SRM Between-Subject - All ROIs"
echo "=========================================="

# Configuration
SCRIPT_DIR="/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/validation/scripts"
OUTPUT_DIR="${SCRIPT_DIR}/results/srm_between_subject/local_$(date +%Y%m%d_%H%M%S)"

# Create output directory
mkdir -p "${OUTPUT_DIR}"

# Activate conda environment
echo "Activating srm environment..."
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate srm

echo ""
echo "Running Between-Subject SRM for all ROIs"
echo "HC subjects: sub-01 to sub-06 (excluding sub-07)"
echo "CVD subjects: sub-08 to sub-10"
echo ""
echo "Output directory: ${OUTPUT_DIR}"
echo ""

# All ROIs
ROIS=(V1 V2 V3 hV4)

# Default k values per ROI (Beta-based SRM: k ≤ 8)
declare -A K_VALUES
K_VALUES["V1"]=4
K_VALUES["V2"]=4
K_VALUES["V3"]=3
K_VALUES["hV4"]=4

SUCCESS_COUNT=0
FAIL_COUNT=0

for ROI in "${ROIS[@]}"; do
  K=${K_VALUES[$ROI]}

  echo "=========================================="
  echo "Processing: ${ROI} (k=${K})"
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
echo "All ROIs Completed"
echo "=========================================="
echo ""
echo "Summary:"
echo "  Successful: ${SUCCESS_COUNT}/4"
echo "  Failed: ${FAIL_COUNT}/4"
echo ""
echo "Results directory: ${OUTPUT_DIR}"
echo ""

# List results
echo "Output files:"
ls -lh "${OUTPUT_DIR}"
echo ""

if [ ${SUCCESS_COUNT} -gt 0 ]; then
  echo "=========================================="
  echo "Next Steps: Analyze Results"
  echo "=========================================="
  echo ""
  echo "1. View individual ROI results:"
  for ROI in "${ROIS[@]}"; do
    RESULT_FILE="${OUTPUT_DIR}/${ROI}_srm_between_subject_results.json"
    if [ -f "${RESULT_FILE}" ]; then
      echo "   ${ROI}: cat ${RESULT_FILE} | python -m json.tool | head -80"
    fi
  done
  echo ""
  echo "2. View disparity plots:"
  echo "   open ${OUTPUT_DIR}/*_hc_cvd_disparity_comparison.png"
  echo ""
  echo "3. Visualize color representational space:"
  echo "   bash run_color_space_visualization.sh ${OUTPUT_DIR}"
  echo "   This creates MDS 2D projections showing 8-color space per subject"
  echo ""
  echo "4. Compare across ROIs:"
  echo "   - Which ROIs show significant HC-CVD differences?"
  echo "   - What are the effect sizes (Cohen's d)?"
  echo "   - How do disparities vary across visual hierarchy?"
  echo "   - CVD-to-CVD internal consistency vs CVD-to-HC disparity"
  echo ""
  echo "5. Statistical summary:"
  echo "   grep -A 5 'statistical_test' ${OUTPUT_DIR}/*.json"
  echo ""
fi

if [ ${FAIL_COUNT} -eq 0 ]; then
  echo "✅ All ROIs processed successfully!"
else
  echo "⚠️  ${FAIL_COUNT} ROI(s) failed. Check logs:"
  echo "   tail ${OUTPUT_DIR}/*_log.txt"
fi

echo "=========================================="
