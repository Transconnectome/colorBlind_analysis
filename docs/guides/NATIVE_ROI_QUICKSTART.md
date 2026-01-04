# Native Space ROI Pipeline - Quick Start Guide

**목적**: MNI 정규화와 무관하게 native BOLD 공간에서 ROI 피팅 및 분석 가능성 검증

---

## 🚀 빠른 시작 (서버)

### 1. 단일 피험자 테스트

```bash
# 서버 접속
ssh haba6030@node2

# 프로젝트 디렉토리로 이동
cd /scratch/connectome/haba6030/colorBlind

# 테스트 실행 (sub-02, V1 ROI)
bash run_native_roi_pipeline.sh 02 V1 1
```

### 2. 전체 피험자 배치 실행

```bash
# SLURM array job 제출 (7 subjects × 4 ROIs = 28 jobs)
sbatch run_native_roi_pipeline.sbatch

# 작업 상태 확인
squeue -u haba6030

# 로그 확인
tail -f logs/native_roi_*.out
```

### 3. 결과 확인

```bash
# 출력 디렉토리
cd derivatives/native_space_roi/sub-02

# 파일 목록
ls -lh

# QC 이미지 다운로드 (로컬에서 실행)
scp haba6030@node2:/scratch/connectome/haba6030/colorBlind/derivatives/native_space_roi/sub-02/QC*.png ./
```

---

## 📋 단계별 실행 (Manual)

필요한 경우 각 단계를 개별적으로 실행할 수 있습니다.

### Step 1: ROI 변환

```bash
# MNI → T1w → BOLD native
bash scripts/transform_roi_to_native.sh 02 V1 1
```

**출력**:
- `sub-02_V1_space-T1w.nii.gz` (T1w native ROI)
- `sub-02_V1_space-bold_run-1.nii.gz` (BOLD native ROI)
- `sub-02_V1_space-bold_run-1_mask.nii.gz` (Binary mask)

### Step 2: 시각화

```bash
# Conda 환경 활성화
conda activate nilearn

# 시각화 생성
python scripts/visualize_native_roi.py --subject 02 --roi V1 --run 1
```

**출력**:
- `QC_sub-02_V1_run-1_detailed.png` (Multi-view overlay)
- `QC_sub-02_V1_run-1_histogram.png` (Intensity distribution)

### Step 3: 기능적 검증

```bash
# Sanity check 실행
python scripts/sanity_check_native_roi.py --subject 02 --roi V1 --run 1
```

**출력**:
- `sanity_check_sub-02_V1_run-1.png` (Diagnostic plots)
- tSNR, decoding accuracy 등 통계

---

## 🔍 결과 해석

### 성공 예시

```
✅ SUCCESS: ROI successfully transformed to native BOLD space
   → Analysis can proceed in native space

Voxel counts:
  MNI space:   2847 voxels
  T1w native:  2756 voxels (95.3 max intensity)
  BOLD native: 2698 voxels (89.2 max intensity)
  Binary mask: 152 voxels (threshold > 20)

ROI Location Statistics:
  Center (mm):  (-15.2, -85.3, -5.1)
  Posterior location: ✓ YES

Signal Quality:
  Mean tSNR: 45.3
  Mean SNR ratio: 0.0342

Functional Response:
  Classification accuracy: 28.5%
  Chance level: 12.50%

✅ ROI passes functional sanity check
```

### 실패 예시

```
❌ FAILURE: No voxels in binary mask

Binary mask: 0 voxels

→ Check QC overlay and registration quality

Possible causes:
  1. EPI coverage insufficient
  2. T1w-to-MNI registration failed
  3. Transform chain error
```

---

## 📁 출력 파일 구조

```
derivatives/native_space_roi/
└── sub-02/
    ├── sub-02_V1_space-T1w.nii.gz                    # T1w native ROI
    ├── sub-02_V1_space-bold_run-1.nii.gz             # BOLD native (probabilistic)
    ├── sub-02_V1_space-bold_run-1_mask.nii.gz        # Binary mask
    ├── QC_sub-02_V1_run-1_overlay.png                # Quick QC
    ├── QC_sub-02_V1_run-1_detailed.png               # Detailed overlay
    ├── QC_sub-02_V1_run-1_histogram.png              # Intensity distribution
    └── sanity_check_sub-02_V1_run-1.png              # Functional diagnostics
```

---

## 🛠️ 트러블슈팅

### Q1: "Transform file not found" 에러

```bash
# Transform 파일 확인
ls /storage/connectome/haba6030/fmriprep_out_deoblique_v2/sub-02/anat/*xfm*

# 없으면 fMRIPrep 재실행 필요
```

### Q2: Binary mask가 비어있음 (0 voxels)

```bash
# Threshold 조정 시도
fslmaths sub-02_V1_space-bold_run-1.nii.gz -thr 10 -bin mask_thr10.nii.gz

# 변환 체인 검증
bash check_transform_chain.sh 02 1
```

### Q3: ROI 위치가 이상함

```bash
# fMRIPrep HTML report 확인
firefox /storage/connectome/haba6030/fmriprep_out_deoblique_v2/sub-02.html

# Registration quality 확인
# - T1w to MNI alignment
# - BOLD to T1w alignment
```

---

## 📊 다음 단계

### 성공 시 → Native Space 분석 진행

1. **Individual-level GLM**
   ```bash
   # 기존 스크립트 수정하여 native space 지원
   python fir_reconstruction_BH2009_system_clean.py \
       --subject 02 \
       --roi V1 \
       --space native
   ```

2. **Hyperalignment/Procrustes**
   ```bash
   # Native space beta patterns로 across-subject alignment
   python scripts/procrustes_alignment_native.py
   ```

3. **Group-level analysis**
   - Aligned native spaces에서 통계 분석
   - MNI 불필요!

### 실패 시 → 대안 탐색

1. **Brain mask 확장** (docs/FMRIPREP_BRAIN_MASK_SOLUTIONS.md 참고)
2. **다른 preprocessing 시도**
3. **해당 피험자 제외 고려**

---

## 📞 참고 문서

- **상세 문서**: `docs/NATIVE_SPACE_ROI_PIPELINE.md`
- **Brain mask 문제**: `docs/FMRIPREP_BRAIN_MASK_SOLUTIONS.md`
- **기존 분석 파이프라인**: `docs/GUIDE_to_classify_reconstruct.md`

---

## 💡 핵심 포인트

✅ **MNI 정규화는 필수가 아닙니다**
- Native space에서 분석 가능
- Hyperalignment로 group analysis 가능

✅ **ROI 위치가 가장 중요합니다**
- Posterior occipital cortex에 있어야 함
- Y < -50mm (MNI coordinates)

✅ **기능적 신호가 있어야 합니다**
- tSNR > 20
- Decoding > chance (12.5%)

---

**작성일**: 2025-01-04
**작성자**: Claude Code
