# ROI Pipeline Quick Start

## 빠른 실행 가이드

### 1. 업로드
```bash
scp roi_pipeline_comprehensive.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/
scp run_roi_pipeline.sbatch haba6030@node2:/scratch/connectome/haba6030/colorBlind/
scp analyze_roi_results.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/
```

### 2. 실행
```bash
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind
chmod +x roi_pipeline_comprehensive.py analyze_roi_results.py
sbatch run_roi_pipeline.sbatch P01 1
```

### 3. 모니터링
```bash
# Job 상태 확인
squeue -u haba6030

# 로그 실시간 확인
tail -f logs/roi_pipeline_*.out
```

### 4. 심층 분석
```bash
# 결과 디렉토리 찾기 (Pilot)
ls -ltr derivatives/pilot/sub-01/
# 또는 Test subject
ls -ltr derivatives/sub-01/

# 가장 최근 결과 분석 (Pilot 예시)
python analyze_roi_results.py derivatives/pilot/sub-01/roi_pipeline_YYYYMMDD_HHMMSS
```

### 5. 다운로드
```bash
# 로컬 머신에서

# Pilot (P01)
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/derivatives/pilot/sub-01/roi_pipeline_* ./

# Test subject
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/derivatives/sub-01/roi_pipeline_* ./
```

## 주요 출력 파일

**Pilot (P01):**
```
derivatives/pilot/sub-01/roi_pipeline_<TIMESTAMP>/
├── results_summary.csv              ← 모든 결과 요약
├── COMPARISON_REPORT.md             ← 비교 리포트
├── figures/                         ← ROI별 시각화
│   ├── V1/
│   ├── V2/
│   ├── V3/
│   └── hV4/
└── detailed_analysis/               ← 심층 분석 (analyze 스크립트 실행 후)
    ├── optimal_configurations.csv   ← **최적 설정 추천**
    ├── parameter_effects.png        ← 파라미터 효과 분석
    └── DETAILED_COMPARISON.md       ← 상세 비교 테이블
```

**Test subjects:**
```
derivatives/sub-<ID>/roi_pipeline_<TIMESTAMP>/
├── results_summary.csv              ← 모든 결과 요약
├── COMPARISON_REPORT.md             ← 비교 리포트
├── figures/                         ← ROI별 시각화
│   ├── V1/
│   ├── V2/
│   ├── V3/
│   └── hV4/
└── detailed_analysis/               ← 심층 분석 (analyze 스크립트 실행 후)
    ├── optimal_configurations.csv   ← **최적 설정 추천**
    ├── parameter_effects.png        ← 파라미터 효과 분석
    └── DETAILED_COMPARISON.md       ← 상세 비교 테이블
```

## 결과 확인 체크리스트

- [ ] `results_summary.csv` 열어서 voxel count 확인
- [ ] `COMPARISON_REPORT.md` 읽고 추천 설정 확인
- [ ] `figures/` 폴더에서 각 ROI의 overlay 이미지 확인
- [ ] `optimal_configurations.csv`에서 최종 파라미터 선택
- [ ] 선택한 마스크 파일 확인 (예: `V1_mask_thr0.2_intnearest_binTrue.nii.gz`)

## 파라미터 해석

### Threshold
- `0.05-0.1`: 넓은 ROI (많은 voxel)
- `0.2-0.3`: 균형잡힌 ROI (권장)
- `0.5`: 좁은 ROI (확실한 영역만)

### Interpolation
- `nearest`: Sharp boundary (권장)
- `linear`: Smooth boundary

### Binarize
- `True`: 0.5 기준으로 이진화 (권장)
- `False`: 연속값 유지

## 일반적인 최적 설정

대부분의 경우 다음 설정이 좋은 출발점:
- **Threshold**: 0.2
- **Interpolation**: nearest
- **Binarize**: True

→ 파일명: `<ROI>_mask_thr0.2_intnearest_binTrue.nii.gz`

## 트러블슈팅

### 에러: Atlas 파일 없음
```bash
ls /scratch/connectome/haba6030/colorBlind/ProbAtlas_v4/
```

### 에러: Functional reference 없음
```bash
ls /storage/connectome/haba6030/fmriprep_out/sub-P01/func/*boldref*
```

### 에러: 메모리 부족
SBATCH 파일에서 `#SBATCH --mem=64G` 로 증가

### Job이 시작 안됨
```bash
# Job 상태 확인
squeue -u haba6030

# 취소하고 재시작
scancel <JOB_ID>
sbatch run_roi_pipeline.sbatch P01 1
```

## 모든 Subject 처리

```bash
# P01 (pilot)
sbatch run_roi_pipeline.sbatch P01 1

# Test subjects
for subj in 01 02 03 04; do
    sbatch run_roi_pipeline.sbatch $subj 1
done
```

## 다음 단계

1. 최적 설정을 `config.py`에 추가
2. 선택한 마스크를 분석 파이프라인에서 사용
3. 모든 subject에 동일한 파라미터 적용
