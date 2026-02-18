#!/bin/bash
# Filter Pre-Validation: Per-pair z-score analysis (B1-B3)
# Runs locally or on server (auto-detects BrainIAK)
# Expected runtime: ~5-10 minutes

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Activate conda
source ~/.bashrc
conda activate nilearn

echo "=== Filter Pre-Validation ==="
echo "Working dir: $SCRIPT_DIR"
echo "Hostname: $(hostname)"
date

# Check if BrainIAK is available (needs mpirun)
if python -c "from brainiak.funcalign.srm import SRM" 2>/dev/null; then
    echo "BrainIAK detected, using mpirun"
    /usr/bin/time -v mpirun -np 1 python filter_pre_validation.py 2>&1 | tee run_pre_validation.log
else
    echo "No BrainIAK, using SimpleSRM fallback"
    /usr/bin/time -v python filter_pre_validation.py 2>&1 | tee run_pre_validation.log
fi

echo ""
echo "=== Done ==="
date
echo "Results: $SCRIPT_DIR/results/filter_pre_validation_results.json"
