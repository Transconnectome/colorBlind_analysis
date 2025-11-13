#!/bin/bash
# submit_all_subjects_all_rois.sh
# Submit FIR reconstruction jobs for all subjects and all ROIs
# Usage: bash submit_all_subjects_all_rois.sh

# Configuration
SUBJECTS="P01 01 02 03 04"  # P01 = pilot, 01-04 = test subjects
ROIS="V1 V2 V3 hV4"
USE_PCA=1
N_COMPONENTS=20
SAVE_ZMAPS=0  # Set to 1 to save z-maps (takes more time/space)

echo "=================================================="
echo "Submitting FIR Reconstruction Jobs"
echo "=================================================="
echo "Subjects: $SUBJECTS (P01=pilot, 01-04=test)"
echo "ROIs: $ROIS"
echo "PCA: $USE_PCA (n_components=$N_COMPONENTS)"
echo "Save Z-maps: $SAVE_ZMAPS"
echo "=================================================="
echo ""
echo "NOTE: ROI masks will be built automatically if needed"
echo "      Missing ROI masks will be skipped gracefully"
echo "      P01 uses irregular pilot color spacing (already preprocessed)"
echo "      01-04 use regular 45° color spacing (need res-2 preprocessing)"
echo ""

# Create slurm_logs directory BEFORE submitting jobs
mkdir -p slurm_logs
echo "Created slurm_logs/ directory for log files"
echo ""

# Counter for submitted jobs
TOTAL_JOBS=0

# Loop through subjects and ROIs
for SUBJECT in $SUBJECTS; do
    echo "--- Subject: $SUBJECT ---"

    # Check if fMRIPrep data exists (handle pilot vs test)
    if [ "$SUBJECT" == "P01" ]; then
        FMRIPREP_DIR="/storage/connectome/haba6030/fmriprep_out/sub-P01"
    else
        FMRIPREP_DIR="/storage/connectome/haba6030/fmriprep_out/sub-${SUBJECT}"
    fi

    if [ ! -d "$FMRIPREP_DIR" ]; then
        echo "  WARNING: fMRIPrep data not found at $FMRIPREP_DIR"
        echo "  Skipping subject $SUBJECT"
        continue
    fi

    for ROI in $ROIS; do
        # Submit job
        JOB_ID=$(sbatch --export=SUBJECT=$SUBJECT,ROI=$ROI,USE_PCA=$USE_PCA,N_COMPONENTS=$N_COMPONENTS,SAVE_ZMAPS=$SAVE_ZMAPS \
                       --job-name="fir_sub${SUBJECT}_${ROI}" \
                       run_all_subjects.sbatch | awk '{print $4}')

        echo "  ✓ Submitted: sub-$SUBJECT $ROI (Job ID: $JOB_ID)"
        TOTAL_JOBS=$((TOTAL_JOBS + 1))
    done
    echo ""
done

echo "=================================================="
echo "Total jobs submitted: $TOTAL_JOBS"
echo "=================================================="
echo ""
echo "Monitor jobs with: squeue -u $USER"
echo "Check output logs: ls -lth slurm_logs/"
echo "View specific log: tail -f slurm_logs/sub-fir_subXX_ROI-JOBID.out"
echo ""
