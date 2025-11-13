#!/bin/bash
# submit_single_subject.sh
# Submit FIR reconstruction for a single subject and ROI
# Usage: bash submit_single_subject.sh P01 V2

if [ "$#" -ne 2 ]; then
    echo "Usage: bash submit_single_subject.sh SUBJECT ROI"
    echo "Example: bash submit_single_subject.sh P01 V2"
    echo "Subjects: P01 (pilot), 02, 03, 04 (test)"
    echo "ROIs: V1, V2, V3, hV4"
    exit 1
fi

SUBJECT=$1
ROI=$2
USE_PCA=1
N_COMPONENTS=20
SAVE_ZMAPS=0

echo "=================================================="
echo "Submitting FIR Reconstruction Job"
echo "=================================================="
echo "Subject: $SUBJECT"
echo "ROI: $ROI"
echo "PCA: $USE_PCA (n_components=$N_COMPONENTS)"
echo "=================================================="

# Create slurm_logs directory if it doesn't exist
mkdir -p slurm_logs

# Check if fMRIPrep data exists (handle pilot vs test)
if [ "$SUBJECT" == "P01" ]; then
    FMRIPREP_DIR="/storage/connectome/haba6030/fmriprep_out/sub-P01"
else
    FMRIPREP_DIR="/storage/connectome/haba6030/fmriprep_out/sub-${SUBJECT}"
fi

if [ ! -d "$FMRIPREP_DIR" ]; then
    echo "ERROR: fMRIPrep data not found at $FMRIPREP_DIR"
    exit 1
fi

# Submit job
JOB_ID=$(sbatch --export=SUBJECT=$SUBJECT,ROI=$ROI,USE_PCA=$USE_PCA,N_COMPONENTS=$N_COMPONENTS,SAVE_ZMAPS=$SAVE_ZMAPS \
               --job-name="fir_sub${SUBJECT}_${ROI}" \
               run_all_subjects.sbatch | awk '{print $4}')

echo "✓ Job submitted successfully!"
echo "  Job ID: $JOB_ID"
echo "  Monitor: squeue -u $USER"
echo "  Log: slurm_logs/sub-fir_sub${SUBJECT}_${ROI}-${JOB_ID}.out"
echo "  View: tail -f slurm_logs/sub-fir_sub${SUBJECT}_${ROI}-${JOB_ID}.out"
echo "=================================================="
