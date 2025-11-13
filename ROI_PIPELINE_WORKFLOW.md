# ROI Pipeline - Complete Workflow Guide

## 개요

Wang atlas의 ROI를 MNI152NLin2009cAsym:res-2 공간으로 변환하고, 모든 가능한 파라미터 조합을 테스트하여 최적의 설정을 찾는 종합 파이프라인입니다.

### 주요 기능

1. **ROI 결합**: Wang atlas의 각 영역을 bilateral로 결합 (V1, V2, V3, hV4)
2. **파라미터 그리드 서치**: 모든 threshold, interpolation, binarization 조합 테스트
3. **자동 검증**: Voxel count, coverage, shape/affine 일치 확인
4. **포괄적 시각화**: Glass brain, overlay (func/anat), probability distribution 등
5. **비교 분석**: 모든 결과를 비교하여 최적 설정 추천

## 파일 설명

### 1. `roi_pipeline_comprehensive.py`
- **목적**: 메인 파이프라인 스크립트
- **기능**:
  - Wang atlas 로드 및 ROI 결합
  - 5가지 threshold × 2가지 interpolation × 2가지 binarize = 20가지 조합 테스트
  - 각 조합마다 마스크 생성, 검증, 시각화
  - 결과를 CSV/JSON으로 저장
  - 자동으로 비교 리포트 생성

**테스트 파라미터:**
```python
threshold: [0.05, 0.1, 0.2, 0.3, 0.5]
interpolation: ['nearest', 'linear']
binarize_after_resample: [True, False]
```

### 2. `run_roi_pipeline.sbatch`
- **목적**: SLURM 제출 스크립트
- **설정**:
  - node2 지정 (필수)
  - 8 CPUs, 32GB RAM
  - 4시간 타임아웃
  - nilearn 환경 자동 활성화

### 3. `analyze_roi_results.py`
- **목적**: 결과 심층 분석 및 비교
- **기능**:
  - 모든 파라미터 조합 효과 분석
  - Heatmap, 비교 그래프 생성
  - 최적 설정 추천
  - 상세 비교 테이블 생성

## 워크플로우

### Step 1: 서버에 파일 업로드

```bash
# 로컬 머신에서 실행
scp roi_pipeline_comprehensive.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/
scp run_roi_pipeline.sbatch haba6030@node2:/scratch/connectome/haba6030/colorBlind/
scp analyze_roi_results.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/
```

### Step 2: 서버 접속 및 파이프라인 실행

```bash
# 서버 접속
ssh haba6030@node2

# 작업 디렉토리로 이동
cd /scratch/connectome/haba6030/colorBlind

# 파일 권한 설정
chmod +x roi_pipeline_comprehensive.py
chmod +x analyze_roi_results.py

# SLURM으로 제출
sbatch run_roi_pipeline.sbatch P01 1
# 또는 다른 subject: sbatch run_roi_pipeline.sbatch 01 1

# Job ID 확인
squeue -u haba6030

# 실시간 로그 확인
tail -f logs/roi_pipeline_<JOB_ID>.out
```

### Step 3: 결과 확인

파이프라인이 완료되면 다음 디렉토리에 결과가 생성됩니다:

**Pilot (P01):**
```
derivatives/pilot/sub-01/roi_pipeline_<TIMESTAMP>/
```

**Test subjects:**
```
derivatives/sub-<SUBJECT_ID>/roi_pipeline_<TIMESTAMP>/
├── results_summary.csv          # 모든 결과 요약 (CSV)
├── results_full.json            # 전체 결과 (JSON)
├── COMPARISON_REPORT.md         # 비교 리포트
├── comparison_plots/            # 비교 그래프
│   └── voxel_count_comparison.png
├── figures/                     # 개별 ROI 시각화
│   ├── V1/
│   │   ├── V1_glass_thr0.1_intnearest_binTrue.png
│   │   ├── V1_overlay_func_thr0.1_intnearest_binTrue.png
│   │   ├── V1_overlay_anat_thr0.1_intnearest_binTrue.png
│   │   └── V1_prob_hist_thr0.1_intnearest_binTrue.png
│   ├── V2/
│   ├── V3/
│   └── hV4/
├── V1_mask_thr0.1_intnearest_binTrue.nii.gz
├── V2_mask_thr0.1_intnearest_binTrue.nii.gz
├── V3_mask_thr0.1_intnearest_binTrue.nii.gz
└── hV4_mask_thr0.1_intnearest_binTrue.nii.gz
```

### Step 4: 심층 분석 실행

```bash
# 결과 디렉토리 경로 설정
# Pilot의 경우:
RESULTS_DIR="derivatives/pilot/sub-01/roi_pipeline_20241110_143022"
# 또는 Test subject의 경우:
# RESULTS_DIR="derivatives/sub-01/roi_pipeline_20241110_143022"

# 심층 분석 실행
python analyze_roi_results.py $RESULTS_DIR
```

이 명령은 추가로 생성합니다:
```
$RESULTS_DIR/detailed_analysis/
├── voxel_count_heatmaps.png      # 파라미터별 voxel count 비교
├── parameter_effects.png          # 각 파라미터의 효과 분석
├── optimal_configurations.csv     # 최적 설정 추천
└── DETAILED_COMPARISON.md         # 상세 비교 테이블
```

### Step 5: 결과 다운로드

```bash
# 로컬 머신에서 실행

# Pilot (P01)의 경우:
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/derivatives/pilot/sub-01/roi_pipeline_<TIMESTAMP> ./

# Test subject의 경우:
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/derivatives/sub-01/roi_pipeline_<TIMESTAMP> ./

# 또는 특정 파일만 다운로드 (Pilot 예시):
scp haba6030@node2:/scratch/connectome/haba6030/colorBlind/derivatives/pilot/sub-01/roi_pipeline_<TIMESTAMP>/results_summary.csv ./
scp haba6030@node2:/scratch/connectome/haba6030/colorBlind/derivatives/pilot/sub-01/roi_pipeline_<TIMESTAMP>/COMPARISON_REPORT.md ./
```

## 출력 설명

### 1. results_summary.csv
모든 파라미터 조합의 결과를 포함하는 CSV 파일:
- `roi_name`: ROI 이름 (V1, V2, V3, hV4)
- `threshold`: 사용된 확률 threshold
- `interpolation`: Resampling 방법
- `binarize_after_resample`: Resample 후 binarize 여부
- `n_voxels`: 최종 voxel 수
- `coverage_pct`: 전체 공간 대비 커버리지 비율
- `shape_match`: 예상 shape과 일치 여부
- `affine_match`: Functional reference affine과 일치 여부

### 2. COMPARISON_REPORT.md
자동 생성된 비교 리포트:
- ROI별 voxel count 비교표
- 최적 설정 추천
- 각 ROI별 최적 파라미터

### 3. 시각화 파일

각 파라미터 조합마다 4가지 시각화 생성:

1. **Glass brain**: 전체 뇌에서 ROI 위치 확인
2. **Functional overlay**: Functional reference 위에 ROI 오버레이
3. **Anatomical overlay**: T1w 위에 ROI 오버레이
4. **Probability histogram**: Atlas probability 분포 및 threshold 위치

### 4. detailed_analysis/

심층 분석 결과:

1. **voxel_count_heatmaps.png**: 각 ROI의 threshold별 voxel count 변화
2. **parameter_effects.png**:
   - Threshold 효과
   - Interpolation 효과
   - Binarization 효과
   - 파라미터 민감도 (CV)
3. **optimal_configurations.csv**: 추천 설정
4. **DETAILED_COMPARISON.md**: 모든 결과의 상세 테이블

## 결과 해석 가이드

### Voxel Count
- **너무 적음 (< 100)**: Threshold가 너무 높거나 ROI가 잘못 정의됨
- **적당함 (100-1000)**: 일반적인 visual cortex ROI 범위
- **많음 (> 1000)**: Threshold가 너무 낮거나 ROI가 과도하게 확장됨

### Coverage
- 일반적으로 0.1-2% 범위
- ROI마다 다르지만 일관성 있는 패턴 확인

### Shape/Affine Match
- **True여야 함**: Functional reference와 정확히 일치
- **False인 경우**: Resampling 오류, 즉시 조사 필요

### Threshold 선택
- **낮은 threshold (0.05-0.1)**: 더 많은 voxel, 경계가 넓음
- **중간 threshold (0.2-0.3)**: 균형잡힌 선택
- **높은 threshold (0.5)**: 더 적은 voxel, 확실한 영역만 포함

### Interpolation 선택
- **nearest**: 이진 마스크, sharp boundary
- **linear**: 부드러운 전환, 경계가 흐릿할 수 있음

### Binarization
- **True**: Resample 후 0.5 기준으로 binarize (권장)
- **False**: Resample 결과를 그대로 사용 (연속값)

## 최적 설정 선택 가이드

파이프라인이 자동으로 최적 설정을 추천하지만, 다음 기준으로 직접 선택할 수도 있습니다:

1. **Voxel count가 적당한 범위** (ROI마다 다름)
2. **시각화가 해부학적으로 타당함** (glass brain, overlay 확인)
3. **다른 subject들과 일관성** (여러 subject 비교 시)
4. **문헌에서 보고된 voxel count와 유사** (가능한 경우)

## 트러블슈팅

### 문제: Atlas 파일을 찾을 수 없음
```
Warning: Atlas file not found: ProbAtlas_v4/lh.roi1.nii.gz
```
**해결**: Wang atlas가 올바른 위치에 있는지 확인
```bash
ls -l /scratch/connectome/haba6030/colorBlind/ProbAtlas_v4/
```

### 문제: Functional reference를 찾을 수 없음
```
FileNotFoundError: Functional reference not found
```
**해결**: fMRIPrep 출력 확인
```bash
ls -l /storage/connectome/haba6030/fmriprep_out/sub-P01/func/*boldref*
```

### 문제: Shape mismatch
```
shape_match: False
```
**해결**:
1. Functional reference shape 확인
2. Resampling 파라미터 검토
3. 코드에서 EXPECTED_SHAPE 수정 필요할 수 있음

### 문제: 메모리 부족
```
SLURM: Out of memory
```
**해결**: SBATCH 파일에서 메모리 증가
```bash
#SBATCH --mem=64G  # 32G에서 64G로 증가
```

## 다음 단계

1. **최적 설정 선택**: `optimal_configurations.csv` 검토
2. **모든 subject에 적용**: 동일한 파라미터로 모든 subject 처리
3. **분석 파이프라인에 통합**: 선택된 마스크를 `bh_anal.py`에서 사용
4. **문서화**: 선택한 파라미터와 근거 기록

## 참고 사항

- **일관성 유지**: 모든 subject에 동일한 파라미터 사용
- **시각적 검증**: 숫자만 믿지 말고 overlay 이미지 확인
- **문헌 비교**: 가능하면 기존 연구의 ROI 크기와 비교
- **버전 관리**: 사용한 파라미터를 config.py에 기록

## 예상 실행 시간

- **파이프라인 실행**: ~30-60분 (subject당, 80개 조합)
- **심층 분석**: ~5-10분

## 연락처

문제가 발생하면:
1. 로그 파일 확인 (`logs/roi_pipeline_<JOB_ID>.err`)
2. Shape, affine 정보 확인
3. 필요시 코드 수정
