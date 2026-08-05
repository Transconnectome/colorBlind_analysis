#!/bin/bash
# Helper script to run task response quality validation

# Correct path to baseline results
BASELINE_DIR="/scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/method3_header_mi/results/baseline_decoding"

echo "Looking for baseline results in: ${BASELINE_DIR}"
echo ""

# Check if directory exists
if [ ! -d "$BASELINE_DIR" ]; then
    echo "Error: Baseline directory does not exist: ${BASELINE_DIR}"
    echo "Please check that phase1 baseline decoding has been completed."
    exit 1
fi

# List available timestamps
echo "Available timestamps:"
ls -1td ${BASELINE_DIR}/*/ 2>/dev/null | xargs -n 1 basename | head -5

# Find latest baseline timestamp
LATEST_TIMESTAMP=$(ls -1td ${BASELINE_DIR}/*/ 2>/dev/null | head -1 | xargs basename)

if [ -z "$LATEST_TIMESTAMP" ]; then
    echo ""
    echo "Error: No baseline results found in ${BASELINE_DIR}"
    echo "Please run phase0 baseline analysis first."
    exit 1
fi

echo ""
echo "Using baseline timestamp: $LATEST_TIMESTAMP"
echo "Submitting task response quality validation job..."
echo ""

# Submit job with timestamp
sbatch /scratch/connectome/haba6030/colorBlind/analysis/validation/scripts/01b_task_response.sbatch $LATEST_TIMESTAMP

echo "Job submitted. Monitor with: squeue -u \$USER"
echo "Check logs in: /scratch/connectome/haba6030/colorBlind/analysis/validation/logs/"
