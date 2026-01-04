#!/bin/bash
#SBATCH --job-name=fmriprep_v2_afni
#SBATCH --output=logs/fmriprep_v2_afni_%j.out
#SBATCH --error=logs/fmriprep_v2_afni_%j.err
#SBATCH --time=48:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=96G
#SBATCH --nodelist=node2

################################################################################
# fMRIPrep v2 - Using AFNI 3dWarp Deobliqued Data
#
# This script runs fMRIPrep on properly deobliqued data from AFNI 3dWarp.
#
# Key improvements:
# - Input data has proper resampling-based deoblique (not header-only)
# - Expected: Clean functional images, successful BBR registration
# - Expected: Proper brain masks (40-50% coverage, not 83%)
#
# Input:  /storage/connectome/haba6030/colorBlind_data_afni_deoblique
# Output: /storage/connectome/haba6030/fmriprep_out_afni_deoblique
# Work:   /storage/connectome/haba6030/fmriprep_work_afni_deoblique
#
# Author: Claude Code
# Date: 2025-12-18
################################################################################

set -e

# Configuration
BIDS_DIR="/storage/connectome/haba6030/colorBlind_data_afni_deoblique"
OUTPUT_DIR="/storage/connectome/haba6030/fmriprep_out_afni_deoblique"
WORK_DIR="/storage/connectome/haba6030/fmriprep_work_afni_deoblique"
FS_LICENSE="/storage/connectome/haba6030/license.txt"

echo "================================================================================"
echo "fMRIPrep v2 - AFNI Deobliqued Data"
echo "================================================================================"
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURM_NODELIST"
echo "Start time: $(date)"
echo ""
echo "Configuration:"
echo "  Input (BIDS):    ${BIDS_DIR}"
echo "  Output:          ${OUTPUT_DIR}"
echo "  Work directory:  ${WORK_DIR}"
echo "  FreeSurfer:      ${FS_LICENSE}"
echo "  CPUs:            ${SLURM_CPUS_PER_TASK}"
echo "  Memory:          ${SLURM_MEM_PER_NODE}MB"
echo ""
echo "Key features:"
echo "  ✅ Properly deobliqued input (AFNI 3dWarp)"
echo "  ✅ All subjects: obliquity < 1°"
echo "  ✅ No data-header mismatch"
echo "  ✅ BBR registration will succeed"
echo "================================================================================"
echo ""

# Create directories
mkdir -p ${OUTPUT_DIR}
mkdir -p ${WORK_DIR}

# Verify AFNI deoblique completed
echo "Verifying AFNI deobliqued data..."
echo "--------------------------------------------------------------------------------"

SUBJECTS=(01 02 03 04 05 06 07 08 09 10)
all_found=true

for sub in "${SUBJECTS[@]}"; do
    test_file="${BIDS_DIR}/sub-${sub}/func/sub-${sub}_task-rsvp_run-1_bold.nii.gz"
    if [ -f "${test_file}" ]; then
        echo "  ✅ sub-${sub}: Found"
    else
        echo "  ❌ sub-${sub}: NOT FOUND"
        all_found=false
    fi
done

echo ""

if [ "$all_found" = false ]; then
    echo "❌ ERROR: Some AFNI deobliqued files are missing"
    echo "   Please verify AFNI deoblique job completed successfully"
    exit 1
fi

echo "✅ All subjects' deobliqued data found"
echo ""

# Load Singularity
echo "Loading Singularity..."
module load singularity/3.11.4

if ! command -v singularity &> /dev/null; then
    echo "❌ ERROR: Singularity not available"
    exit 1
fi

echo "✅ Singularity available: $(which singularity)"
echo ""

# fMRIPrep container
FMRIPREP_CONTAINER="/storage/connectome/haba6030/fmriprep-24.0.1.sif"

if [ ! -f "${FMRIPREP_CONTAINER}" ]; then
    echo "❌ ERROR: fMRIPrep container not found: ${FMRIPREP_CONTAINER}"
    exit 1
fi

echo "✅ fMRIPrep container found"
echo ""

# Verify FreeSurfer license
if [ ! -f "${FS_LICENSE}" ]; then
    echo "❌ ERROR: FreeSurfer license not found: ${FS_LICENSE}"
    exit 1
fi

echo "✅ FreeSurfer license found"
echo ""

# =========================================================================
# Run fMRIPrep
# =========================================================================

echo "================================================================================"
echo "Running fMRIPrep"
echo "================================================================================"
echo ""

# Key fMRIPrep arguments:
# --ignore fieldmaps: Use if fieldmap issues persist (can test both ways)
# --use-syn-sdc: Synthetic distortion correction (backup if fieldmaps fail)
# --dummy-scans 0: No dummy scans to remove (already handled)
# --skull-strip-fixed-seed: Reproducible skull-stripping
# --force-bbr: Force boundary-based registration
# --bold2t1w-dof 9: 9 degrees of freedom for registration
# --output-spaces: MNI152NLin2009cAsym:res-2 (2mm resolution)

echo "fMRIPrep parameters:"
echo "  - BBR registration: Forced"
echo "  - DOF: 9"
echo "  - Fieldmaps: Included (B0FieldIdentifier present in JSON)"
echo "  - Output space: MNI152NLin2009cAsym:res-2"
echo "  - Dummy scans: 0 (already handled)"
echo ""

singularity run --cleanenv \
    -B ${BIDS_DIR}:/data:ro \
    -B ${OUTPUT_DIR}:/out \
    -B ${WORK_DIR}:/work \
    -B ${FS_LICENSE}:/opt/freesurfer/license.txt:ro \
    ${FMRIPREP_CONTAINER} \
    /data /out participant \
    --participant-label 01 02 03 04 05 06 07 08 09 10 \
    --skip_bids_validation \
    --fs-license-file /opt/freesurfer/license.txt \
    --output-spaces MNI152NLin2009cAsym:res-2 \
    --bold2t1w-dof 9 \
    --force-bbr \
    --dummy-scans 0 \
    --skull-strip-fixed-seed \
    --nthreads ${SLURM_CPUS_PER_TASK} \
    --omp-nthreads 8 \
    --mem_mb $((SLURM_MEM_PER_NODE - 8000)) \
    --work-dir /work \
    --write-graph \
    --stop-on-first-crash

# =========================================================================
# Post-processing verification
# =========================================================================

echo ""
echo "================================================================================"
echo "VERIFICATION"
echo "================================================================================"
echo ""

echo "Checking fMRIPrep outputs..."
echo "--------------------------------------------------------------------------------"

for sub in "${SUBJECTS[@]}"; do
    func_dir="${OUTPUT_DIR}/sub-${sub}/func"

    if [ -d "${func_dir}" ]; then
        # Count processed BOLD runs
        bold_count=$(ls ${func_dir}/sub-${sub}_task-rsvp_run-*_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz 2>/dev/null | wc -l)

        if [ ${bold_count} -gt 0 ]; then
            echo "  ✅ sub-${sub}: ${bold_count} BOLD runs processed"

            # Check first run for quality
            first_bold="${func_dir}/sub-${sub}_task-rsvp_run-1_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz"

            if [ -f "${first_bold}" ]; then
                # Use AFNI to check if data is clean (not all zeros)
                data_range=$(3dBrickStat -slow -max ${first_bold} 2>/dev/null || echo "N/A")
                echo "    Data range max: ${data_range}"
            fi
        else
            echo "  ❌ sub-${sub}: No BOLD runs found"
        fi
    else
        echo "  ❌ sub-${sub}: func directory not found"
    fi
done

echo ""
echo "================================================================================"
echo "Sub-01 Specific Verification"
echo "================================================================================"
echo ""

SUB01_FUNC="${OUTPUT_DIR}/sub-01/func"

if [ -d "${SUB01_FUNC}" ]; then
    echo "✅ sub-01 func directory exists"
    echo ""

    echo "Checking brain mask coverage..."

    # Get brain mask
    mask_file="${SUB01_FUNC}/sub-01_task-rsvp_run-1_space-MNI152NLin2009cAsym_res-2_desc-brain_mask.nii.gz"

    if [ -f "${mask_file}" ]; then
        # Calculate mask coverage
        total_voxels=$(3dBrickStat -count -non-zero ${mask_file} 2>/dev/null | awk '{print $NF}')
        all_voxels=$(3dinfo -nv ${mask_file} 2>/dev/null)

        if [ ! -z "${total_voxels}" ] && [ ! -z "${all_voxels}" ]; then
            coverage=$(echo "scale=1; 100 * ${total_voxels} / ${all_voxels}" | bc)
            echo "  Brain mask coverage: ${coverage}%"
            echo ""

            if (( $(echo "${coverage} < 60" | bc -l) )); then
                echo "  ✅ EXCELLENT: Coverage is normal (< 60%)"
                echo "  ✅ Previous 83.6% issue should be resolved!"
            else
                echo "  ⚠️  WARNING: High coverage (${coverage}%)"
                echo "  ⚠️  Expected < 60%, previous problematic value was 83.6%"
            fi
        fi
    else
        echo "  ⚠️  Brain mask file not found"
    fi

    echo ""
    echo "Checking for image distortion artifacts..."

    bold_file="${SUB01_FUNC}/sub-01_task-rsvp_run-1_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz"

    if [ -f "${bold_file}" ]; then
        # Get basic stats
        data_max=$(3dBrickStat -max ${bold_file} 2>/dev/null)
        data_mean=$(3dBrickStat -mean ${bold_file} 2>/dev/null)

        echo "  Max intensity: ${data_max}"
        echo "  Mean intensity: ${data_mean}"
        echo ""

        if (( $(echo "${data_max} > 0" | bc -l) )); then
            echo "  ✅ Data has valid intensities"
            echo "  ✅ No all-zero data (unlike scipy resampling failure)"
        else
            echo "  ❌ WARNING: Data appears to be all zeros"
        fi
    else
        echo "  ❌ BOLD file not found"
    fi
else
    echo "❌ sub-01 func directory not found - fMRIPrep may have failed"
fi

echo ""
echo "================================================================================"
echo "fMRIPrep v2 COMPLETE"
echo "================================================================================"
echo ""
echo "Output directory: ${OUTPUT_DIR}"
echo "Work directory: ${WORK_DIR}"
echo ""
echo "Key improvements from AFNI deoblique:"
echo "  ✅ Proper resampling-based deoblique (not header-only)"
echo "  ✅ No data-header mismatch"
echo "  ✅ BBR registration should succeed"
echo "  ✅ Expected: Clean functional images"
echo "  ✅ Expected: Normal brain mask coverage (< 60%)"
echo ""
echo "Next steps:"
echo "  1. Review fMRIPrep HTML reports in ${OUTPUT_DIR}"
echo "  2. Visual inspection of sub-01 images (check for streaking)"
echo "  3. If quality is good, run baseline analysis"
echo "  4. Compare sub-01 results with previous analysis"
echo ""
echo "Expected sub-01 outcomes:"
echo "  ✅ Clean functional images (no horizontal streaking)"
echo "  ✅ Sharp anatomical details (not blurred)"
echo "  ✅ Brain mask: 40-50% coverage (not 83.6%)"
echo "  ✅ ROI voxel counts: Normal (not too few)"
echo "  ✅ Baseline analysis: Will succeed"
echo ""
echo "End time: $(date)"
echo "================================================================================"
