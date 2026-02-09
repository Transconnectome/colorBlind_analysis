#!/bin/bash
#SBATCH --job-name=confounds_test
#SBATCH --output=/scratch/connectome/haba6030/colorBlind/analysis/prep_trials/logs/confounds_test_%j.out
#SBATCH --error=/scratch/connectome/haba6030/colorBlind/analysis/prep_trials/logs/confounds_test_%j.err
#SBATCH --time=00:30:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --qos=shared
#SBATCH --nodelist=node2

################################################################################
# Test: Generate confounds with aCompCor (single subject/run)
#
# Purpose: Verify aCompCor implementation on server
#
# Expected outputs:
#   - Confounds TSV with a_comp_cor_00 ~ a_comp_cor_09
#   - QC visualizations in fmriprep_out_method3_header_mi/.../qc/
################################################################################

set -e

# Configuration
SUBJECT_ID="01"
RUN=1
METHOD="method3_header_mi"

echo "================================================================================"
echo "Server Test: Generate Confounds with aCompCor"
echo "================================================================================"
echo "Subject: sub-${SUBJECT_ID}, Run: ${RUN}"
echo "Node: ${SLURM_NODELIST}"
echo "Job ID: ${SLURM_JOB_ID}"
echo "Start time: $(date)"
echo "================================================================================"
echo ""

# Environment setup
source ~/.bashrc
conda activate nilearn

# Verify conda environment
echo "Python: $(which python)"
echo "Python version: $(python --version)"
echo ""

# Verify required packages
echo "Checking required packages..."
python -c "import nibabel; print(f'  ✓ nibabel {nibabel.__version__}')"
python -c "import nilearn; print(f'  ✓ nilearn {nilearn.__version__}')"
python -c "import sklearn; print(f'  ✓ sklearn {sklearn.__version__}')"
python -c "import matplotlib; print(f'  ✓ matplotlib {matplotlib.__version__}')"
echo ""

# Run confounds generation
cd /scratch/connectome/haba6030/colorBlind/analysis/prep_trials/scripts

python generate_confounds.py \
    --subject ${SUBJECT_ID} \
    --run ${RUN} \
    --method ${METHOD} \
    --tr 1.5

echo ""
echo "================================================================================"
echo "Test Complete"
echo "================================================================================"
echo "End time: $(date)"
echo ""
echo "Check outputs:"
echo "  1. Confounds TSV:"
echo "     /storage/connectome/haba6030/fmriprep_out_method3_header_mi/sub-${SUBJECT_ID}/func/"
echo "     sub-${SUBJECT_ID}_task-rsvp_run-${RUN}_desc-confounds_timeseries.tsv"
echo ""
echo "  2. QC visualizations:"
echo "     /storage/connectome/haba6030/fmriprep_out_method3_header_mi/qc/sub-${SUBJECT_ID}/"
echo "     - tissue_masks.png"
echo "     - acompcor_qc.png"
echo "     - mask_stats.json"
echo ""
echo "Verify TSV contains aCompCor columns: a_comp_cor_00 ~ a_comp_cor_09"
echo ""
