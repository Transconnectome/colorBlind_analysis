#!/bin/bash
#SBATCH --job-name=diagnose_storage
#SBATCH --output=diagnostic_report_%j.txt
#SBATCH --error=diagnostic_error_%j.txt
#SBATCH --time=00:30:00
#SBATCH --mem=8G
#SBATCH --cpus-per-task=2
#SBATCH --nodelist=node2

# ==============================================================================
# Storage & Data Structure Diagnostic Script
# ==============================================================================
# Purpose: Diagnose why ROI voxel counts changed from 310 to 536
# Checks: Directory structure, brain masks, functional images, ROI masks
# ==============================================================================

echo "======================================================================"
echo "STORAGE & DATA STRUCTURE DIAGNOSTIC"
echo "======================================================================"
echo "Job ID: $SLURM_JOB_ID"
echo "Date: $(date)"
echo "Node: $(hostname)"
echo ""

# Activate conda environment for Python tools
source ~/.bashrc
conda activate nilearn 2>/dev/null || echo "Note: nilearn env not activated"

echo ""
echo "======================================================================"
echo "PART 1: DIRECTORY STRUCTURE CHECK"
echo "======================================================================"
echo ""

STORAGE_BASE="/storage/connectome/haba6030/fmriprep_out"
PROJECT_DIR="/scratch/connectome/haba6030/colorBlind"

echo "Checking fMRIPrep output directories..."
echo "----------------------------------------------------------------------"

# Check sub-01
if [ -d "$STORAGE_BASE/sub-01" ]; then
    echo "✓ FOUND: $STORAGE_BASE/sub-01/"
    echo "  Created: $(stat -c %y $STORAGE_BASE/sub-01 2>/dev/null || stat -f %Sm $STORAGE_BASE/sub-01)"
    echo "  Size: $(du -sh $STORAGE_BASE/sub-01 2>/dev/null | cut -f1)"
    SUB01_EXISTS=true
else
    echo "✗ NOT FOUND: $STORAGE_BASE/sub-01/"
    SUB01_EXISTS=false
fi

echo ""

# Check sub-P01
if [ -d "$STORAGE_BASE/sub-P01" ]; then
    echo "✓ FOUND: $STORAGE_BASE/sub-P01/"
    echo "  Created: $(stat -c %y $STORAGE_BASE/sub-P01 2>/dev/null || stat -f %Sm $STORAGE_BASE/sub-P01)"
    echo "  Size: $(du -sh $STORAGE_BASE/sub-P01 2>/dev/null | cut -f1)"
    SUBP01_EXISTS=true
else
    echo "✗ NOT FOUND: $STORAGE_BASE/sub-P01/"
    SUBP01_EXISTS=false
fi

echo ""
echo "======================================================================"
echo "PART 2: BRAIN MASK COMPARISON"
echo "======================================================================"
echo ""

echo "Searching for brain masks..."
echo "----------------------------------------------------------------------"

# Function to check brain masks
check_brain_masks() {
    local subdir=$1
    local label=$2

    echo ""
    echo "[$label] Brain masks in: $subdir"

    if [ ! -d "$subdir/anat" ]; then
        echo "  ✗ anat directory not found"
        return
    fi

    # Find all brain masks
    local masks=$(find "$subdir/anat" -name "*brain_mask*.nii.gz" 2>/dev/null)

    if [ -z "$masks" ]; then
        echo "  ✗ No brain masks found"
        return
    fi

    for mask in $masks; do
        echo "  ✓ $(basename $mask)"
        echo "    Path: $mask"
        echo "    Size: $(ls -lh $mask | awk '{print $5}')"
        echo "    Modified: $(stat -c %y $mask 2>/dev/null || stat -f %Sm $mask)"

        # Check shape with Python
        python3 << EOF
import nibabel as nib
try:
    img = nib.load("$mask")
    print(f"    Shape: {img.shape[:3]}")
    print(f"    Voxels: {int((img.get_fdata() > 0).sum())}")
except Exception as e:
    print(f"    Error loading: {e}")
EOF
    done
}

if [ "$SUB01_EXISTS" = true ]; then
    check_brain_masks "$STORAGE_BASE/sub-01" "sub-01"
fi

if [ "$SUBP01_EXISTS" = true ]; then
    check_brain_masks "$STORAGE_BASE/sub-P01" "sub-P01"
fi

echo ""
echo "======================================================================"
echo "PART 3: FUNCTIONAL IMAGE COMPARISON"
echo "======================================================================"
echo ""

echo "Comparing functional reference images (run-1, res-2)..."
echo "----------------------------------------------------------------------"

# Function to check functional images
check_func_image() {
    local subdir=$1
    local label=$2
    local file_prefix=$3

    echo ""
    echo "[$label] Functional images in: $subdir/func/"

    if [ ! -d "$subdir/func" ]; then
        echo "  ✗ func directory not found"
        return
    fi

    # Find run-1 res-2 preprocessed bold
    local func_file="$subdir/func/${file_prefix}_task-rsvp_run-1_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz"

    if [ ! -f "$func_file" ]; then
        echo "  ✗ Reference file not found: $(basename $func_file)"
        # Try to find any run-1 file
        local any_run1=$(ls "$subdir/func/"*run-1*preproc_bold.nii.gz 2>/dev/null | head -1)
        if [ -n "$any_run1" ]; then
            echo "  ! Found alternative: $(basename $any_run1)"
            func_file=$any_run1
        else
            return
        fi
    fi

    echo "  ✓ $(basename $func_file)"
    echo "    Path: $func_file"
    echo "    Size: $(ls -lh $func_file | awk '{print $5}')"
    echo "    Modified: $(stat -c %y $func_file 2>/dev/null || stat -f %Sm $func_file)"

    # Check shape and affine with Python
    python3 << EOF
import nibabel as nib
import numpy as np
try:
    img = nib.load("$func_file")
    print(f"    Shape: {img.shape}")
    print(f"    Voxel size: {img.header.get_zooms()[:3]}")
    print(f"    Affine diagonal: {np.diag(img.affine)[:3]}")
except Exception as e:
    print(f"    Error loading: {e}")
EOF

    # Save path for comparison
    echo "$func_file" >> /tmp/func_paths_$$.txt
}

# Clear temp file
rm -f /tmp/func_paths_$$.txt

if [ "$SUB01_EXISTS" = true ]; then
    check_func_image "$STORAGE_BASE/sub-01" "sub-01" "sub-01"
fi

if [ "$SUBP01_EXISTS" = true ]; then
    check_func_image "$STORAGE_BASE/sub-P01" "sub-P01" "sub-01"
fi

# If both exist, compare files
if [ "$SUB01_EXISTS" = true ] && [ "$SUBP01_EXISTS" = true ]; then
    echo ""
    echo "Comparing files between sub-01 and sub-P01..."
    echo "----------------------------------------------------------------------"

    FILE1="$STORAGE_BASE/sub-01/func/sub-01_task-rsvp_run-1_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz"
    FILE2="$STORAGE_BASE/sub-P01/func/sub-01_task-rsvp_run-1_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz"

    if [ -f "$FILE1" ] && [ -f "$FILE2" ]; then
        echo "Computing MD5 checksums (this may take a minute)..."
        MD51=$(md5sum "$FILE1" | cut -d' ' -f1)
        MD52=$(md5sum "$FILE2" | cut -d' ' -f1)

        echo "  sub-01:  $MD51"
        echo "  sub-P01: $MD52"

        if [ "$MD51" = "$MD52" ]; then
            echo "  ✓✓✓ FILES ARE IDENTICAL! (Just directory rename)"
        else
            echo "  ✗✗✗ FILES ARE DIFFERENT! (Data was reprocessed)"
        fi
    else
        echo "  ! Cannot compare - one or both files missing"
    fi
fi

# Cleanup temp file
rm -f /tmp/func_paths_$$.txt

echo ""
echo "======================================================================"
echo "PART 4: EXISTING ROI MASKS CHECK"
echo "======================================================================"
echo ""

echo "Checking for existing ROI masks in derivatives..."
echo "----------------------------------------------------------------------"

# Function to check ROI masks
check_roi_masks() {
    local deriv_dir="$PROJECT_DIR/derivatives/$1"
    local label=$1

    echo ""
    echo "[$label] Derivatives: $deriv_dir"

    if [ ! -d "$deriv_dir/roi" ]; then
        echo "  ✗ roi directory not found"
        return
    fi

    local masks=$(ls "$deriv_dir/roi/"*.nii.gz 2>/dev/null)

    if [ -z "$masks" ]; then
        echo "  ✗ No ROI masks found"
        return
    fi

    for mask in $masks; do
        echo "  ✓ $(basename $mask)"
        echo "    Created: $(stat -c %y $mask 2>/dev/null || stat -f %Sm $mask)"

        # Get voxel count
        python3 << EOF
import nibabel as nib
try:
    img = nib.load("$mask")
    n_vox = int((img.get_fdata() > 0).sum())
    shape = img.shape[:3]
    print(f"    Voxels: {n_vox}")
    print(f"    Shape: {shape}")

    # Flag if unusual
    roi_name = "$(basename $mask)"
    if "V2" in roi_name:
        if n_vox == 310:
            print(f"    ✓✓✓ GOOD VOXEL COUNT (matches original)")
        elif n_vox in [536, 553]:
            print(f"    ✗✗✗ BAD VOXEL COUNT (inflated)")
        else:
            print(f"    ? UNKNOWN VOXEL COUNT")
except Exception as e:
    print(f"    Error: {e}")
EOF
    done
}

check_roi_masks "sub-01"
check_roi_masks "sub-P01"

echo ""
echo "======================================================================"
echo "PART 5: TEST ROI BUILDING FROM BOTH LOCATIONS"
echo "======================================================================"
echo ""

echo "Testing ROI mask building with both configurations..."
echo "----------------------------------------------------------------------"

# Create test script
cat > /tmp/test_roi_build_$$.py << 'EOFPYTHON'
import sys
import os
import nibabel as nib
import numpy as np
from pathlib import Path

# Add project to path
sys.path.insert(0, '/scratch/connectome/haba6030/colorBlind')

def test_roi_build(storage_path, sub_id, file_prefix, label):
    """Test ROI building with given configuration"""
    print(f"\n[{label}] Testing ROI build")
    print(f"  Storage path: {storage_path}")
    print(f"  Subject ID: {sub_id}")
    print(f"  File prefix: {file_prefix}")

    # Check reference image
    func_path = f"{storage_path}/func/{file_prefix}_task-rsvp_run-1_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz"

    if not os.path.exists(func_path):
        print(f"  ✗ Reference functional not found")
        return

    print(f"  ✓ Reference functional found")
    ref_img = nib.load(func_path)
    print(f"    Shape: {ref_img.shape[:3]}")

    # Check brain mask
    brain_mask_paths = [
        f"{storage_path}/anat/{file_prefix}_space-MNI152NLin2009cAsym_res-2_desc-brain_mask.nii.gz",
        f"{storage_path}/anat/{file_prefix}_acq-mprage_space-MNI152NLin2009cAsym_res-2_desc-brain_mask.nii.gz",
    ]

    brain_mask_found = False
    for bm_path in brain_mask_paths:
        if os.path.exists(bm_path):
            print(f"  ✓ Brain mask found: {os.path.basename(bm_path)}")
            brain_img = nib.load(bm_path)
            print(f"    Brain voxels: {int((brain_img.get_fdata() > 0).sum())}")
            brain_mask_found = True
            break

    if not brain_mask_found:
        print(f"  ✗ Brain mask NOT found - ROI will be inflated!")

    # Simulate V2 ROI voxel count (without actually building)
    atlas_v2_parts = ['perc_VTPM_vol_roi3_', 'perc_VTPM_vol_roi4_']
    atlas_dir = '/scratch/connectome/haba6030/colorBlind/ProbAtlas_v4/subj_vol_all'

    if not os.path.exists(atlas_dir):
        print(f"  ✗ Atlas directory not found")
        return

    print(f"  Computing expected V2 voxel count...")

    try:
        from nilearn import image as nimg

        # Load atlas parts
        roi_mask = None
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
            print(f"  ✗ Could not load atlas")
            return

        # Count before resampling
        atlas_voxels = int(roi_mask.sum())
        print(f"    Atlas voxels (original): {atlas_voxels}")

        # Resample to reference
        roi_nii = nib.Nifti1Image(roi_mask.astype(np.int16), atlas_img.affine)
        roi_resampled = nimg.resample_img(
            roi_nii,
            target_affine=ref_img.affine,
            target_shape=ref_img.shape[:3],
            interpolation='nearest'
        )

        resampled_voxels = int((roi_resampled.get_fdata() > 0).sum())
        print(f"    After resampling: {resampled_voxels}")

        # If brain mask exists, apply intersection
        if brain_mask_found:
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
            print(f"    After brain mask: {final_voxels}")

            if final_voxels == 310:
                print(f"    ✓✓✓ MATCHES GOOD RESULT (310 voxels)")
            elif final_voxels in [536, 553]:
                print(f"    ✗✗✗ MATCHES BAD RESULT ({final_voxels} voxels)")
            else:
                print(f"    ? Different from both ({final_voxels} voxels)")
        else:
            print(f"    ! Without brain mask: {resampled_voxels} voxels")
            if resampled_voxels in [536, 553]:
                print(f"    ✗✗✗ This explains the BAD result!")

    except Exception as e:
        print(f"  Error during simulation: {e}")
        import traceback
        traceback.print_exc()

# Test both configurations
if os.path.exists('/storage/connectome/haba6030/fmriprep_out/sub-01'):
    test_roi_build(
        '/storage/connectome/haba6030/fmriprep_out/sub-01',
        '01',
        'sub-01',
        'sub-01 (ORIGINAL)'
    )

if os.path.exists('/storage/connectome/haba6030/fmriprep_out/sub-P01'):
    test_roi_build(
        '/storage/connectome/haba6030/fmriprep_out/sub-P01',
        'P01',
        'sub-01',
        'sub-P01 (RENAMED)'
    )
EOFPYTHON

# Run test
python3 /tmp/test_roi_build_$$.py

# Cleanup
rm -f /tmp/test_roi_build_$$.py

echo ""
echo "======================================================================"
echo "PART 6: SUMMARY & RECOMMENDATIONS"
echo "======================================================================"
echo ""

echo "FINDINGS:"
echo "----------------------------------------------------------------------"

if [ "$SUB01_EXISTS" = true ] && [ "$SUBP01_EXISTS" = true ]; then
    echo "• Both sub-01/ and sub-P01/ directories exist"
    echo "  → Check MD5 comparison above to see if data is identical"
    echo ""
elif [ "$SUB01_EXISTS" = true ]; then
    echo "• Only sub-01/ exists (original location)"
    echo "  → sub-P01/ was never created or was deleted"
    echo ""
elif [ "$SUBP01_EXISTS" = true ]; then
    echo "• Only sub-P01/ exists (renamed location)"
    echo "  → sub-01/ no longer exists (was renamed/moved)"
    echo ""
else
    echo "• Neither directory found - DATA MISSING!"
    echo ""
fi

echo ""
echo "NEXT STEPS:"
echo "----------------------------------------------------------------------"
echo "1. Review the voxel counts from Part 5 above"
echo "2. Identify which configuration gives 310 voxels (GOOD)"
echo "3. Update config.py to use the GOOD configuration"
echo "4. Rebuild ROI masks if necessary"
echo "5. Re-run analysis with correct masks"
echo ""
echo "KEY METRICS TO MATCH:"
echo "  • V2 voxels: 310 (not 536 or 553)"
echo "  • V1 voxels: 511"
echo "  • V3 voxels: 89"
echo "  • hV4 voxels: 55"
echo ""

echo "======================================================================"
echo "DIAGNOSTIC COMPLETE"
echo "======================================================================"
echo "Report saved to: diagnostic_report_$SLURM_JOB_ID.txt"
echo "Date: $(date)"
echo "======================================================================"
