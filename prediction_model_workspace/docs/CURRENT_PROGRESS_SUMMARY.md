# 현재 진행 상황 요약 (2026-01-10)

## 전체 워크플로우 개요

```
Phase 0 (완료) → Step 1.1 (보류) → Step 1.2 (진단) → Step 1.3 (실행 중) → Step 1.4 (대기)
```

---

## Phase 0: Baseline Decoding (완료 ✅)

**목적**: 기존 Brouwer & Heeger (2009) 파이프라인 복제

**방법**:
- Run-averaged 패턴 (8 colors × 6 runs = 48 patterns per subject)
- FIR-based HRF estimation → Forward encoding (6 channels)
- Leave-One-Run-Out cross-validation

**결과**:
- V1 reconstruction error: ~32° (기존 논문 수준)
- HC 피험자 간 공통 구조 확인 (Procrustes stability: 0.91)

**문제점**:
- T << p 문제 (48 observations vs 300-500 voxels)
- Run effects 무시 (run-to-run correlation ≈ 0.01)

**Status**: ✅ 완료, 하지만 Future Phases는 다른 접근 필요

---

## Step 1.1: Data Structure Check (보류 ⏸️)

**목적**:
- 6 runs × 10 subjects = 60 runs 모두 완전한가?
- 각 run당 72 color trials (8 colors × 9 repetitions) 확인
- Run-to-run 일관성 체크

**Status**: ⏸️ 스크립트 작성됨 (`00_check_data_structure.py`), 아직 미실행

**보류 이유**: Step 1.2-1.3 결과가 데이터 품질을 간접 확인

---

## Step 1.2: Reliability Comparison (완료, 실패 ❌)

**실행 일시**: 2026-01-09
**서버**: node4
**피험자**: 10명 (HC 7명 + CVD 3명)
**ROIs**: V1, V2, V3, hV4

### 목적
Color-averaged (baseline) vs Trial-wise (LS-S) reliability 비교

### 결과: 치명적 버그 발견

**Color-averaged 방법**: 완전 실패 ❌
```
Error: Failed to compute contrast for red/orange/yellow/...
Cause: GLM design matrix 컬럼명과 contrast 이름 불일치
Result: reliability_mean = nan (모든 피험자)
```

**Trial-wise (LS-S) 방법**: 작동은 하나 품질 매우 낮음 ⚠️
```
sub-07 V1: Procrustes stability = 0.041 (목표: 0.50+)
sub-08 V1: Procrustes stability = 0.161 (목표: 0.50+)
```

### 교훈
1. ✅ **LS-S 개념 검증**: 432 trials 추출 성공 (크래시 없음)
2. ✅ **버그 식별**:
   - Contrast naming 이슈
   - Masker/GLM preprocessing 충돌
3. ⚠️ **낮은 reliability**: 데이터 품질 or 파라미터 문제 의심

### 다음 단계 결정
Step 1.2 수정 대신 **Step 1.3로 진행** 결정:
- Step 1.3는 버그 수정된 깨끗한 구현
- Step 1.3 결과로 문제 원인 진단 (버그 vs 데이터 vs 파라미터)

---

## Step 1.3: Trial-wise GLM (LS-S) - **현재 실행 중** 🚀

**실행 일시**: 2026-01-10 오후
**예상 완료**: 6시간 이내 (각 피험자 30-60분)
**서버**: node4
**리소스**: 32GB × 10 jobs = 320GB (node4 총 452GB)

### 목적
**384개 trial-wise beta estimates 추출** (Hyperalignment용)
- 8 colors × 9 repetitions × 6 runs = 432 total trials
- "blank" trials 제외 → ~384 color trials

### 방법론: LS-S (Least-Squares Separate)

**핵심 원리**:
```python
# 각 trial을 독립적으로 추정
for trial_idx in range(n_trials):
    lss_events['trial_type'] = 'nuisance'  # 모든 trial
    lss_events.loc[trial_idx, 'trial_type'] = 'target'  # 현재 trial만

    glm.fit(bold_data, events=lss_events, confounds=confounds)
    beta = glm.compute_contrast('target')  # 단일 trial beta
```

**Step 1.2와의 차이**:

| 요소 | Step 1.2 | Step 1.3 |
|------|----------|----------|
| Masker 사용 | ❌ fit_transform() 반복 | ✅ fit() 한 번, transform() 반복 |
| GLM preprocessing | ⚠️ 충돌 가능 | ✅ 명확히 분리 |
| Contrast 계산 | ❌ Color name 직접 사용 | ✅ 'target' 단일 contrast |
| 코드 품질 | ⚠️ 진단용 | ✅ Production용 |

### GLM 설정

```python
FirstLevelModel(
    t_r=2.0,                    # TR (fMRIPrep 메타데이터에서)
    hrf_model='spm',            # SPM canonical HRF
    drift_model='cosine',       # Cosine basis for drift
    high_pass=1/128,            # 128s cutoff (SPM 기본값)
    smoothing_fwhm=6.0,         # 6mm FWHM
    mask_img=roi_mask,          # Subject-specific ROI mask
    standardize=True,           # Z-score voxels
    signal_scaling=False,       # Preserve beta units
    minimize_memory=True        # 메모리 효율성
)
```

**Confounds**: `motion` (6 motion parameters)

### 품질 메트릭

**Tier-1 (Trial-level)**:
1. **Split-half reliability (Procrustes)**:
   - Odd runs (1,3,5) vs Even runs (2,4,6)
   - Per-color reliability
   - **목표**: ≥ 0.50 (색상별 평균)

2. **Temporal SNR**:
   - Trial-to-trial 변동성
   - Voxel별 SNR 분포

3. **Trial counts**: 색상별 trial 수 (각 54개 예상)

**Decision Rule**:
```
if reliability_mean >= 0.50:
    → ✅ PROCEED TO STEP 1.4 (Hyperalignment)
elif reliability_mean >= 0.30:
    → ⚠️ PROCEED_WITH_CAUTION (일부 ROI만?)
else:
    → ❌ REVIEW PARAMETERS (smoothing, confounds, HRF model)
```

### 예상 출력 (40개 디렉토리)

**경로**: `/scratch/connectome/haba6030/colorBlind/prediction_model_workspace/results/trial_wise_glm/`

**각 sub-XX_ROI/ 디렉토리**:
```
trial_betas.npy              # (384, n_voxels) - 핵심 데이터
trial_metadata.json          # Trial 정보
quality_metrics.json         # Reliability, tSNR
diagnostic_figure.png        # 4패널 시각화
```

**집계 결과**:
```
trial_glm_detailed.csv       # 40 rows (전체 결과)
trial_glm_summary.png        # 6패널 시각화
trial_glm_summary.txt        # 텍스트 리포트
```

### 모니터링 방법

```bash
# 작업 상태
squeue -u haba6030

# 실시간 로그 (예: sub-01)
ssh haba6030@node2
tail -f /scratch/connectome/haba6030/colorBlind/prediction_model_workspace/logs/trial_glm_sub-0_*.out

# 완료된 결과 확인
ls -lh /scratch/connectome/haba6030/colorBlind/prediction_model_workspace/results/trial_wise_glm/
```

### ⚠️ 버그 발견 및 수정 (2026-01-11)

**첫 실행 실패**: 모든 피험자에서 "Color trials: 0" 에러

**원인**:
- 스크립트가 `'red'`, `'orange'`, ... 기대
- 실제 파일은 `'color_1'`, `'color_2'`, ..., `'color_8'`

**수정**:
```python
# 라인 217 수정
color_names = ['color_1', 'color_2', 'color_3', 'color_4',
               'color_5', 'color_6', 'color_7', 'color_8']
```

**추가 수정**:
- Empty DataFrame 체크 추가 (라인 355-358)
- None 처리 추가 (라인 477-479)

**재실행**: 2026-01-11, 예상 완료 6시간 이내

**상세**: `FIX_SUMMARY.md` 참조

---

## Step 1.4: Hyperalignment (대기 중 ⏳)

**조건**: Step 1.3 reliability ≥ 0.50 달성 시

### 목적
HC 5명을 공통 representational space로 정렬

### 방법론 선택지

**Option A: Hyperalignment (GPA)**
- Iterative Procrustes alignment
- 384 correspondence points 사용
- Orthogonal transformations (magnitude 보존)

**Option B: SRM (Shared Response Model)**
- Probabilistic latent space (k=30 dimensions)
- Better sample efficiency (T/k = 1280%)
- Literature-supported for task fMRI

**결정**: 둘 다 구현 후 비교 (COMPARISON.md 참조)

### 평가 메트릭
1. Inter-subject correlation (ISC) > 0.30
2. LOSO decoding accuracy > 25% (chance: 12.5%)
3. Procrustes disparity < 0.08 (aligned space)

---

## 데이터 파이프라인 요약

```
fMRIPrep outputs (original_v3)
│
├─ BOLD: sub-{ID}_task-rsvp_run-{X}_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz
├─ Confounds: sub-{ID}_task-rsvp_run-{X}_desc-confounds_timeseries.tsv
└─ Events: sub-{ID}_task-rsvp_run-{X}_events.tsv
    │
    ▼
Phase 0 (Baseline)               Step 1.3 (Trial-wise GLM) ← 현재
│                                │
├─ Run-averaged (48 patterns)    ├─ Stimulus-wise (384 trials)
├─ Forward encoding (6 ch)       ├─ LS-S beta extraction
└─ amplitudes_z.npy              └─ trial_betas.npy
    │                                │
    ▼                                ▼
Future Phase 1 (Hyperalignment)  Step 1.4 (Hyperalignment) ← 다음
│
├─ HC common space (5 subjects)
└─ CVD projection (3 subjects)
    │
    ▼
Phase 2 (Continuous Hue Encoder)
│
├─ 360° forward model
└─ Trial-wise predictions
    │
    ▼
Phase 3 (CVD Filter Optimization)
│
└─ Neural-guided personalized filters
```

---

## 현재 파일 구조

```
prediction_model_workspace/
│
├── scripts/
│   ├── 00_check_data_structure.py          # Step 1.1 (미실행)
│   ├── 01_reliability_comparison.py         # Step 1.2 (완료, 버그)
│   ├── 02_trial_wise_glm.py                # Step 1.3 (실행 중) ★
│   ├── aggregate_reliability_results.py     # Step 1.2 집계
│   ├── aggregate_trial_glm_results.py      # Step 1.3 집계 (대기)
│   ├── run_01_reliability_comparison.sbatch # Step 1.2 배치
│   └── run_02_trial_wise_glm.sbatch        # Step 1.3 배치 ★
│
├── results/
│   ├── reliability_check/                   # Step 1.2 결과 (버그 있음)
│   └── trial_wise_glm/                      # Step 1.3 결과 (생성 중) ★
│
├── logs/                                     # SLURM 로그 (실시간)
│
├── docs/
│   ├── PHASE1_HYPERALIGNMENT.md             # Phase 1 상세 계획
│   ├── PHASE2_CONTINUOUS_HUE.md             # Phase 2 계획
│   ├── PHASE3_CVD_FILTER.md                 # Phase 3 계획
│   └── CURRENT_PROGRESS_SUMMARY.md          # 이 문서 ★
│
├── MASTER_PLAN.md                           # 전체 TODO 체크리스트
├── QUICK_START.md                           # 단계별 실행 가이드
└── PIPELINE_GUIDE.md                        # Decision flow + 타임라인
```

---

## 주요 결정 포인트 (Decision Tree)

### Decision 1: Step 1.3 결과에 따라

```
Step 1.3 reliability_mean:
│
├─ ≥ 0.50: ✅ PROCEED → Step 1.4 (Hyperalignment)
│   └─ 모든 ROI, 모든 피험자 사용
│
├─ 0.30-0.49: ⚠️ SELECTIVE PROCEED
│   ├─ 높은 ROI만 사용 (V1 > V2 > V3 > hV4?)
│   └─ 또는 Tier 1 피험자만 (sub-01,03,04,08,09,10)
│
└─ < 0.30: ❌ PARAMETER OPTIMIZATION NEEDED
    ├─ Smoothing 증가 (6mm → 8mm)
    ├─ Confounds 변경 (motion → motion+compcor)
    └─ HRF model 변경 (spm → spm+derivative)
```

### Decision 2: Hyperalignment 방법 선택

```
Step 1.4 후 평가:
│
├─ Hyperalignment (GPA)
│   ├─ ISC, LOSO decoding
│   └─ Procrustes disparity
│
├─ SRM (k=30)
│   ├─ ISC, LOSO decoding
│   └─ Shared space variance
│
└─ Winner selection (or hybrid)
    └─ Phase 2로 진행
```

---

## 타임라인 (예상)

### 완료된 단계
- ✅ Phase 0: Baseline decoding (2025년)
- ✅ Step 1.2: Reliability check (2026-01-09, 버그 있음)

### 현재 진행 중
- 🚀 **Step 1.3**: Trial-wise GLM (2026-01-10, 6시간 소요)

### 다음 단계 (예상)
- **Step 1.4**: Hyperalignment (1-2일)
  - 두 방법 구현 및 비교
  - Best method 선택
- **Step 1.5**: CVD projection (1일)
  - CVD 3명을 HC common space로 투영
  - 표현 차이 정량화

### Phase 2 (예상: 2주)
- 360° continuous hue encoder
- Trial-wise prediction
- SOTA model 조사 (TODO에 추가됨)

### Phase 3 (예상: 1주)
- CVD filter learning
- 3D loss optimization (magnitude, baseline, RDM)

---

## 참고 문서

### 기술 문서
- `MASTER_PLAN.md`: 전체 TODO 체크리스트 (Phase 1-3)
- `QUICK_START.md`: 단계별 실행 커맨드
- `PIPELINE_GUIDE.md`: Decision flow 및 상세 가이드

### 방법론 비교
- `analysis/future_phase1_hyperalignment/COMPARISON.md`: Hyperalignment vs SRM 상세 비교

### Phase별 상세 계획
- `docs/PHASE1_HYPERALIGNMENT.md`: Step 1.1-1.5 상세
- `docs/PHASE2_CONTINUOUS_HUE.md`: 360° encoder 설계
- `docs/PHASE3_CVD_FILTER.md`: Filter optimization 설계

### 프로젝트 배경
- `CLAUDE.md`: 서버 설정, 데이터 경로, 전체 개요
- `docs/0104_Preprocessing_Report.md`: fMRIPrep 품질 평가 (original_v3)

---

## 핵심 이슈 및 질문

### 해결된 이슈 ✅
1. **T << p 문제**: Run-averaged (48) → Trial-wise (384)로 해결
2. **GLM preprocessing 충돌**: Masker vs FirstLevelModel 역할 분리
3. **서버 리소스**: 32GB × 10 = 320GB < 452GB (node4 가용)

### 미해결 이슈 ⚠️
1. **Step 1.2 낮은 reliability** (0.04-0.16):
   - 버그 때문? Step 1.3 결과로 확인 필요
   - 데이터 품질? (sub-07은 Tier 3, Dice 0.73)
   - 파라미터? (smoothing, confounds, HRF)

2. **Tier 3 피험자 (sub-06, sub-07)**:
   - 포함 vs 제외 결정 필요
   - Step 1.3 결과로 판단

3. **Hyperalignment vs SRM**:
   - 둘 다 구현 후 비교 필요
   - 평가 메트릭: ISC, LOSO, Procrustes disparity

### 대기 중인 질문 🤔
1. **Step 1.3 reliability가 여전히 낮으면?**
   - 파라미터 최적화 (smoothing, confounds, HRF)
   - 또는 데이터 자체 문제 인정?

2. **어떤 ROI가 가장 신뢰할 만한가?**
   - V1 > V2 > V3 > hV4 예상
   - Step 1.3 결과로 확인

3. **Phase 2 encoder architecture?**
   - Linear (Ridge/Lasso)?
   - Non-linear (MLP)?
   - SOTA survey 필요 (TODO 추가됨)

---

## 다음 액션 아이템

### 즉시 (비행 전)
1. ✅ Step 1.3 작업 제출 완료
2. ⏳ 작업 모니터링 설정
3. 📄 결과 해석 가이드 작성
4. 📄 동료 보고 자료 준비

### 비행 후 (6-8시간 후)
1. 📥 Step 1.3 결과 다운로드
2. 🔍 집계 스크립트 실행 (`aggregate_trial_glm_results.py`)
3. 📊 Reliability 분석 및 결정
4. 🚀 Step 1.4 준비 (통과 시) or 파라미터 조정 (실패 시)

---

**Last updated**: 2026-01-10 (Step 1.3 실행 시작)
**Next milestone**: Step 1.3 결과 확인 (6시간 이내)
**Critical decision**: Reliability ≥ 0.50 달성 여부
