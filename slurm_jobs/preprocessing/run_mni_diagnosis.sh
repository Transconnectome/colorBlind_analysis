#!/bin/bash
# Quick launcher for MNI chain diagnosis
#
# Usage:
#   ./run_mni_diagnosis.sh <subject_id>
#
# Example:
#   ./run_mni_diagnosis.sh 01

set -e

SUBJECT=${1:-01}
FMRIPREP_DIR="/storage/connectome/haba6030/fmriprep_out_deoblique_v2"
RUN=1

# Check if fMRIPrep dir exists (if running locally, download files first)
if [ ! -d "$FMRIPREP_DIR" ]; then
    echo "⚠️  fMRIPrep directory not found: $FMRIPREP_DIR"
    echo ""
    echo "To download required files from server:"
    echo ""
    echo "# Download T1w MNI"
    echo "scp haba6030@node2:$FMRIPREP_DIR/sub-${SUBJECT}/anat/*_space-MNI*_desc-preproc_T1w.nii.gz ./temp_diagnosis/"
    echo ""
    echo "# Download BOLD MNI (boldref)"
    echo "scp haba6030@node2:$FMRIPREP_DIR/sub-${SUBJECT}/func/*_run-${RUN}_*space-MNI*boldref.nii.gz ./temp_diagnosis/"
    echo ""
    echo "Then run with local directory:"
    echo "  python diagnose_mni_chain.py --subject ${SUBJECT} --fmriprep-dir ./temp_diagnosis --run ${RUN}"
    exit 1
fi

echo "🔍 Running MNI chain diagnosis for sub-${SUBJECT}"

python diagnose_mni_chain.py \
    --subject ${SUBJECT} \
    --fmriprep-dir ${FMRIPREP_DIR} \
    --run ${RUN} \
    --output mni_chain_diagnosis_sub-${SUBJECT}.txt

echo ""
echo "✅ Diagnosis complete!"
echo "📝 Visual inspection commands saved to: mni_chain_diagnosis_sub-${SUBJECT}.txt"
