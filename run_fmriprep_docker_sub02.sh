#!/bin/bash
#SBATCH --job-name=fmriprep_sub02
#SBATCH --chdir=/scratch/connectome/haba6030/fMRItest_preprocess_sub02
#SBATCH --output=logs/fmriprep_sub02_%j.out
#SBATCH --error=logs/fmriprep_sub02_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=20G
#SBATCH --nodelist=node2
#SBATCH --time=14:00:00

# 필요한 경우 Docker 사용을 허용하는 노드에서만 실행되도록 설정
##SBATCH --constraint=docker

cd /scratch/connectome/haba6030/fMRItest_preprocess_sub02

# --- 사용자 설정 변수 ---
BIDS_DIR="/scratch/connectome/haba6030/datasets/ds003834/sub-sid000005"
OUTPUT_DIR="/scratch/connectome/haba6030/fMRItest_preprocess_sub02/output"
FS_LICENSE="/scratch/connectome/haba6030/license.txt"
WORKDIR_CUSTOM="/scratch/connectome/haba6030/fMRItest_preprocess_sub02/work"
PARTICIPANT_LABEL="sub-02"
FMRIprep_IMAGE_TAG="nipreps/fmriprep:25.0.0"
N_THREADS=16
MEM_MB=16000


echo "================================================"
echo "🧠 fMRIPrep Docker SLURM Job 시작"
echo "================================================"

# Docker run
docker run --rm \
    -v ${BIDS_DIR}:${BIDS_DIR}:ro \
    -v ${OUTPUT_DIR}:/out \
    -v ${WORKDIR_CUSTOM}:/work \
    -v ${FS_LICENSE}:/opt/freesurfer/license.txt \
    ${FMRIprep_IMAGE_TAG} \
    ${BIDS_DIR} /out participant \
    --participant-label ${PARTICIPANT_LABEL} \
    --skip-bids-validation \
    --fs-license-file /opt/freesurfer/license.txt \
    --output-spaces MNI152NLin2009cAsym:res-2 \
    --nthreads ${N_THREADS} \
    --mem_mb ${MEM_MB} \
    -w /work

echo "================================================"
echo "🎉 fMRIPrep Docker 실행 완료"
echo "결과 위치: ${OUTPUT_DIR}/fmriprep/sub-${PARTICIPANT_LABEL}/"
echo "================================================"
