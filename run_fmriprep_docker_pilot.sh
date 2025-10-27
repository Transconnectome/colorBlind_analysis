#!/bin/bash
#SBATCH --job-name=colorBlind_pilot01
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/pilot
#SBATCH --output=/scratch/connectome/haba6030/colorBlind/logs/%x_%j.out
#SBATCH --error=/scratch/connectome/haba6030/colorBlind/logs/%x_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=20G
#SBATCH --nodelist=node2
#SBATCH --time=14:00:00

# 필요한 경우 Docker 사용을 허용하는 노드에서만 실행되도록 설정

set -euo pipefail                    # ★ 실패를 즉시 감지(권장)

# --- 사용자 설정 변수 ---
BIDS_DIR="/scratch/connectome/haba6030/colorBlind/pilot"
OUTPUT_DIR="/scratch/connectome/haba6030/colorBlind/output/pilot"
FS_LICENSE="/scratch/connectome/haba6030/license.txt"
WORKDIR_CUSTOM="/scratch/connectome/haba6030/colorBlind/work/pilot"
PARTICIPANT_LABEL="01"
FMRIprep_IMAGE_TAG="nipreps/fmriprep:25.0.0"
N_THREADS=16
MEM_MB=16000

# 폴더/바이너리 사전 점검 (로그가 아예 안 생기는 상황 방지)
command -v docker >/dev/null 2>&1 || { echo "[ERROR] docker not found"; exit 1; }
test -f "${BIDS_DIR}/dataset_description.json" || { echo "[ERROR] Not a BIDS root: ${BIDS_DIR}"; exit 2; }
test -f "${FS_LICENSE}" || { echo "[ERROR] FS license not found: ${FS_LICENSE}"; exit 2; }
mkdir -p "${OUTPUT_DIR}" "${WORKDIR_CUSTOM}"

echo "================================================"
echo "🧠 fMRIPrep Docker SLURM Job 시작"
echo "BIDS_DIR=${BIDS_DIR}"
echo "OUTPUT_DIR=${OUTPUT_DIR}"
echo "WORKDIR=${WORKDIR_CUSTOM}"
echo "THREADS=${N_THREADS}  MEM_MB=${MEM_MB}"
echo "IMAGE=${FMRIprep_IMAGE_TAG}"
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
    --fs-license-file /opt/freesurfer/license.txt \
    --output-spaces MNI152NLin2009cAsym:res-2 \
    --nthreads ${N_THREADS} \
    --mem-mb ${MEM_MB} \
    -w /work
    --skip-bids-validation # Validator를 따로 돌렸다면 선택적으로 사용


echo "================================================"
echo "🎉 fMRIPrep Docker 실행 완료"
echo "결과 위치: ${OUTPUT_DIR}/fmriprep/sub-${PARTICIPANT_LABEL}/"
echo "================================================"
