#!/bin/bash
# Test GLMsingle with single subject-ROI
# Run in interactive mode to see diagnostic output

set -e

echo "=========================================="
echo "GLMsingle Test - Single Subject-ROI"
echo "=========================================="
echo ""

# Activate environment
source ~/.bashrc
conda activate nilearn

# Test parameters
SUBJECT="01"
ROI="V1"

echo "Subject: ${SUBJECT}"
echo "ROI: ${ROI}"
echo ""

# Run GLMsingle Step 1
echo "Running Step 1: GLMsingle with residuals..."
python 01_glmsingle_with_residuals.py \
    --subject ${SUBJECT} \
    --roi ${ROI} \
    --n-pcs 10 \
    --config full

# Check outputs
echo ""
echo "=========================================="
echo "Checking outputs..."
echo "=========================================="

# Find the output directory
OUTPUT_BASE="./results/GLMsingle"
LATEST_DIR=$(ls -td ${OUTPUT_BASE}/*/sub-${SUBJECT}_${ROI} 2>/dev/null | head -1)

if [ -z "$LATEST_DIR" ]; then
    echo "ERROR: No output directory found"
    exit 1
fi

echo "Output directory: ${LATEST_DIR}"
echo ""

# Check files
echo "Files created:"
ls -lh ${LATEST_DIR}/*.npy ${LATEST_DIR}/*.npz ${LATEST_DIR}/*.json 2>/dev/null || echo "No output files found"
echo ""

# Verify betas
echo "Verifying betas..."
python << 'EOF'
import numpy as np
import sys
import glob
from pathlib import Path

# Find latest results
output_base = Path('./results/GLMsingle')
pattern = f"*/sub-01_V1"
dirs = sorted(output_base.glob(pattern), key=lambda x: x.stat().st_mtime, reverse=True)

if not dirs:
    print("ERROR: No results directory found")
    sys.exit(1)

result_dir = dirs[0]
print(f"Checking: {result_dir}")

# Load betas
betas_file = result_dir / 'betas_single_trial.npz'
if not betas_file.exists():
    print(f"ERROR: Betas file not found: {betas_file}")
    sys.exit(1)

betas_npz = np.load(betas_file)
print(f"\nBetas file structure:")
print(f"  Files in npz: {betas_npz.files}")
print(f"  Number of runs: {len(betas_npz.files)}")

# Check each run
for run_key in betas_npz.files:
    betas_run = betas_npz[run_key]
    print(f"  {run_key}: shape {betas_run.shape}")

# Expected: 8 conditions (colors) per run
expected_conditions = 8
for run_key in betas_npz.files:
    betas_run = betas_npz[run_key]
    n_conditions = betas_run.shape[0]
    if n_conditions != expected_conditions:
        print(f"\nWARNING: {run_key} has {n_conditions} conditions, expected {expected_conditions}")
    else:
        print(f"\n✓ {run_key} has correct number of conditions ({n_conditions})")

# Load metadata
meta_file = result_dir / 'glmsingle_metadata.json'
if meta_file.exists():
    import json
    with open(meta_file) as f:
        meta = json.load(f)

    print(f"\nGLMsingle metadata:")
    print(f"  Config used: {meta.get('config_type', 'unknown')}")
    if 'design_info' in meta:
        print(f"  Design info:")
        for key, val in meta['design_info'].items():
            print(f"    {key}: {val}")

print("\n✓ Test completed successfully")
EOF

echo ""
echo "=========================================="
echo "Test completed!"
echo "=========================================="
