#!/bin/bash
# Quick check of pilot directory
# Run this directly on the server (no sbatch needed)

echo "Checking pilot directory..."
echo ""

PILOT_DIR="/scratch/connectome/haba6030/colorBlind/pilot/sub-01"

if [ ! -d "$PILOT_DIR" ]; then
    echo "Directory not found: $PILOT_DIR"
    exit 1
fi

echo "Directory exists: $PILOT_DIR"
echo ""
echo "Contents:"
ls -lah $PILOT_DIR/
echo ""

echo "Searching for functional and brain mask files..."
echo ""

# Find functional
find $PILOT_DIR -name "*bold*.nii.gz" | head -5

echo ""

# Find brain mask
find $PILOT_DIR -name "*brain_mask*.nii.gz" | head -5

echo ""
echo "To test if this gives 310 voxels, run:"
echo "  sbatch check_pilot_original.sbatch"
