#!/bin/bash
#SBATCH --job-name=check_pilot
#SBATCH --output=pilot_check_%j.txt
#SBATCH --error=pilot_check_err_%j.txt
#SBATCH --time=00:15:00
#SBATCH --mem=4G
#SBATCH --cpus-per-task=2
#SBATCH --nodelist=node2

# ==============================================================================
# Check Original Pilot Preprocessing
# ==============================================================================

echo "======================================================================"
echo "CHECKING ORIGINAL PILOT PREPROCESSING"
echo "======================================================================"
echo "Job ID: $SLURM_JOB_ID"
echo "Date: $(date)"
echo ""

source ~/.bashrc
conda activate nilearn 2>/dev/null

PILOT_DIR="/scratch/connectome/haba6030/colorBlind/pilot/sub-01"

echo "======================================================================"
echo "PART 1: Check Original Pilot Directory"
echo "======================================================================"
echo ""

if [ ! -d "$PILOT_DIR" ]; then
    echo "✗ Directory not found: $PILOT_DIR"
    exit 1
fi

echo "✓ Directory exists: $PILOT_DIR"
echo "  Created: $(stat -c %y $PILOT_DIR 2>/dev/null || stat -f %Sm $PILOT_DIR)"
echo "  Size: $(du -sh $PILOT_DIR 2>/dev/null | cut -f1)"
echo ""

echo "Directory structure:"
ls -la $PILOT_DIR/
echo ""

# Check for subdirectories
for subdir in func anat; do
    if [ -d "$PILOT_DIR/$subdir" ]; then
        echo "✓ $subdir/ exists"
        echo "  Files: $(ls $PILOT_DIR/$subdir/ 2>/dev/null | wc -l)"
    else
        echo "✗ $subdir/ not found"
    fi
done

echo ""
echo "======================================================================"
echo "PART 2: Check Functional Images"
echo "======================================================================"
echo ""

# Look for functional data
echo "Searching for functional images..."

# Try different patterns
FUNC_PATTERNS=(
    "$PILOT_DIR/func/*run-1*res-2*preproc*.nii.gz"
    "$PILOT_DIR/func/*run-1*preproc*.nii.gz"
    "$PILOT_DIR/*run-1*res-2*preproc*.nii.gz"
    "$PILOT_DIR/*run-1*preproc*.nii.gz"
)

FUNC_FILE=""
for pattern in "${FUNC_PATTERNS[@]}"; do
    files=$(ls $pattern 2>/dev/null | head -1)
    if [ -n "$files" ]; then
        FUNC_FILE=$files
        echo "✓ Found: $(basename $FUNC_FILE)"
        break
    fi
done

if [ -z "$FUNC_FILE" ]; then
    echo "✗ No functional file found with standard patterns"
    echo ""
    echo "Available files in pilot directory:"
    find $PILOT_DIR -name "*.nii.gz" 2>/dev/null | head -20
    exit 1
fi

echo "  Path: $FUNC_FILE"
echo "  Size: $(ls -lh $FUNC_FILE | awk '{print $5}')"
echo "  Modified: $(stat -c %y $FUNC_FILE 2>/dev/null || stat -f %Sm $FUNC_FILE)"
echo ""

# Check shape
python3 << EOF
import nibabel as nib
try:
    img = nib.load("$FUNC_FILE")
    print(f"  Shape: {img.shape}")
    print(f"  Voxel size: {img.header.get_zooms()[:3]}")
    print(f"  Data type: {img.get_data_dtype()}")
except Exception as e:
    print(f"  Error loading: {e}")
EOF

echo ""
echo "======================================================================"
echo "PART 3: Check Brain Mask"
echo "======================================================================"
echo ""

# Look for brain mask
MASK_PATTERNS=(
    "$PILOT_DIR/anat/*res-2*brain_mask*.nii.gz"
    "$PILOT_DIR/anat/*brain_mask*.nii.gz"
    "$PILOT_DIR/*res-2*brain_mask*.nii.gz"
    "$PILOT_DIR/*brain_mask*.nii.gz"
)

BRAIN_MASK=""
for pattern in "${MASK_PATTERNS[@]}"; do
    files=$(ls $pattern 2>/dev/null | head -1)
    if [ -n "$files" ]; then
        BRAIN_MASK=$files
        echo "✓ Found brain mask: $(basename $BRAIN_MASK)"
        break
    fi
done

if [ -z "$BRAIN_MASK" ]; then
    echo "✗ No brain mask found"
    echo "  This could explain the voxel count issue!"
else
    echo "  Path: $BRAIN_MASK"
    echo "  Size: $(ls -lh $BRAIN_MASK | awk '{print $5}')"

    # Check voxel count
    python3 << EOF
import nibabel as nib
import numpy as np
try:
    img = nib.load("$BRAIN_MASK")
    n_vox = int((img.get_fdata() > 0).sum())
    print(f"  Shape: {img.shape[:3]}")
    print(f"  Brain voxels: {n_vox}")
except Exception as e:
    print(f"  Error: {e}")
EOF
fi

echo ""
echo "======================================================================"
echo "PART 4: Test ROI Building from Pilot Directory"
echo "======================================================================"
echo ""

if [ -z "$FUNC_FILE" ]; then
    echo "Cannot test - no functional file found"
    exit 1
fi

echo "Simulating V2 ROI building from pilot directory..."
echo ""

python3 << 'EOFPYTHON'
import sys
import os
import nibabel as nib
import numpy as np

sys.path.insert(0, '/scratch/connectome/haba6030/colorBlind')

pilot_func = os.environ.get('FUNC_FILE', '')
pilot_mask = os.environ.get('BRAIN_MASK', '')

if not pilot_func or not os.path.exists(pilot_func):
    print("✗ Functional file not available")
    sys.exit(1)

print(f"Using reference: {os.path.basename(pilot_func)}")
ref_img = nib.load(pilot_func)
print(f"Reference shape: {ref_img.shape[:3]}")

# Check brain mask
has_brain_mask = pilot_mask and os.path.exists(pilot_mask)
if has_brain_mask:
    print(f"Using brain mask: {os.path.basename(pilot_mask)}")
    brain_img = nib.load(pilot_mask)
    print(f"Brain mask shape: {brain_img.shape[:3]}")
else:
    print("⚠ No brain mask - ROI will be inflated!")

# Load Wang atlas V2 parts
atlas_dir = '/scratch/connectome/haba6030/colorBlind/ProbAtlas_v4/subj_vol_all'
atlas_v2_parts = ['perc_VTPM_vol_roi3_', 'perc_VTPM_vol_roi4_']

if not os.path.exists(atlas_dir):
    print(f"✗ Atlas directory not found: {atlas_dir}")
    sys.exit(1)

print(f"\nLoading Wang atlas V2 from: {atlas_dir}")

try:
    from nilearn import image as nimg

    # Load atlas
    roi_mask = None
    atlas_img = None
    for hemi in ['lh', 'rh']:
        for part in atlas_v2_parts:
            atlas_file = f"{atlas_dir}/{part}{hemi}.nii.gz"
            if os.path.exists(atlas_file):
                atlas_img = nib.load(atlas_file)
                atlas_data = atlas_img.get_fdata()
                part_mask = atlas_data > 50

                if roi_mask is None:
                    roi_mask = part_mask
                else:
                    roi_mask = np.logical_or(roi_mask, part_mask)

    if roi_mask is None:
        print("✗ Could not load atlas")
        sys.exit(1)

    atlas_voxels = int(roi_mask.sum())
    print(f"Atlas voxels (original space): {atlas_voxels}")

    # Resample to pilot reference
    roi_nii = nib.Nifti1Image(roi_mask.astype(np.int16), atlas_img.affine)
    roi_resampled = nimg.resample_img(
        roi_nii,
        target_affine=ref_img.affine,
        target_shape=ref_img.shape[:3],
        interpolation='nearest'
    )

    resampled_voxels = int((roi_resampled.get_fdata() > 0).sum())
    print(f"After resampling to pilot reference: {resampled_voxels} voxels")

    # Apply brain mask if available
    if has_brain_mask:
        brain_resampled = nimg.resample_img(
            brain_img,
            target_affine=roi_resampled.affine,
            target_shape=roi_resampled.shape[:3],
            interpolation='nearest'
        )

        roi_bool = roi_resampled.get_fdata().astype(bool)
        brain_bool = brain_resampled.get_fdata().astype(bool)
        combined = np.logical_and(roi_bool, brain_bool)
        final_voxels = int(combined.sum())

        print(f"After brain mask intersection: {final_voxels} voxels")

        print("\n" + "="*60)
        if final_voxels == 310:
            print("✓✓✓ PERFECT! This gives the GOOD 310 voxels!")
        elif 300 <= final_voxels <= 320:
            print(f"✓✓ VERY CLOSE! {final_voxels} voxels (expected 310)")
        elif final_voxels in [536, 553]:
            print(f"✗✗✗ Still BAD - {final_voxels} voxels")
        else:
            print(f"? Different count: {final_voxels} voxels (expected 310)")
        print("="*60)
    else:
        print(f"\nWithout brain mask: {resampled_voxels} voxels")
        print("\n" + "="*60)
        if resampled_voxels in [536, 553]:
            print("✗ This explains the BAD result - missing brain mask!")
        print("="*60)

except Exception as e:
    print(f"Error during simulation: {e}")
    import traceback
    traceback.print_exc()
EOFPYTHON

echo ""
echo "======================================================================"
echo "SUMMARY"
echo "======================================================================"
echo ""

if [ -n "$FUNC_FILE" ]; then
    echo "✓ Original pilot preprocessing found"
    echo "  Location: $PILOT_DIR"
    echo "  Functional: $(basename $FUNC_FILE)"

    if [ -n "$BRAIN_MASK" ]; then
        echo "  Brain mask: $(basename $BRAIN_MASK)"
    else
        echo "  Brain mask: NOT FOUND (this is the problem!)"
    fi

    echo ""
    echo "RECOMMENDATION:"
    echo "  If simulation above shows 310 voxels:"
    echo "    → Use pilot directory for ROI building"
    echo "    → Update config.py to point here"
    echo "  If still shows 536 voxels:"
    echo "    → Original GOOD preprocessing may be elsewhere"
    echo "    → Or brain mask needs to be created"
else
    echo "✗ Could not find preprocessing in pilot directory"
fi

echo ""
echo "======================================================================"
echo "Date: $(date)"
echo "======================================================================"
