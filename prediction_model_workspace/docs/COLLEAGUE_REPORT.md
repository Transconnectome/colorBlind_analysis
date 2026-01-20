# 동료 보고: Future Phases 진행 상황 (2026-01-10)

## Executive Summary

**프로젝트**: Color-blind 피험자의 fMRI 패턴 분석 및 개인화 필터 학습

**현재 단계**: Phase 1, Step 1.3 (Trial-wise GLM) 실행 중

**예상 완료**: 6시간 이내

**다음 단계**: Hyperalignment (HC 공통 공간 생성)

---

## 1. 프로젝트 배경 및 목표

### 연구 질문

**Main Research Question (MRQ)**:
> CVD(색약/색맹) 피험자의 뇌 표상이 정상(HC) 피험자와 어떻게 다른가?

**Specific Research Questions**:
1. **SRQ2**: HC 피험자들을 공통 표상 공간으로 정렬할 수 있는가?
2. **SRQ3**: 8개 이산 색상 → 360° 연속 색상 예측이 가능한가?
3. **SRQ4**: CVD 피험자의 표상을 HC로 변환하는 개인화 필터를 학습할 수 있는가?

### 기존 연구 (Phase 0) 요약

**완료 사항**:
- Brouwer & Heeger (2009) 파이프라인 복제
- 8개 색상 분류 및 재구성 (V1 error: ~32°)
- HC 피험자 간 공통 구조 확인 (Procrustes stability: 0.91)

**한계점**:
- Run-averaged 접근 (48 패턴만 사용)
- T << p 문제 (48 observations vs 300-500 voxels)
- Run effects 무시 (run-to-run correlation ≈ 0.01)

**해결책**:
- **Trial-wise 접근** (384 trials 사용) → 현재 진행 중

---

## 2. 현재 진행 상황 (Phase 1)

### Pipeline 개요

```
[Phase 0] Baseline Decoding (완료)
    ↓
[Step 1.1] Data Structure Check (보류)
    ↓
[Step 1.2] Reliability Comparison (완료, 버그 발견)
    ↓
[Step 1.3] Trial-wise GLM (LS-S) ← 현재 실행 중 🚀
    ↓
[Step 1.4] Hyperalignment ← 다음 단계
    ↓
[Step 1.5] CVD Projection
```

### Step 1.3: Trial-wise GLM (현재)

**목적**:
- 각 색상 자극마다 독립적인 뇌 활성화 패턴 추출
- 384개 trial-wise beta estimates 생성 (8 colors × 9 repetitions × 6 runs)

**방법**: LS-S (Least-Squares Separate)
- 각 trial을 target으로, 나머지를 nuisance로 처리
- GLM으로 trial별 beta map 추정

**실행 정보**:
- **서버**: node4
- **리소스**: 32GB × 10 jobs (10 subjects)
- **재실행**: 2026-01-11 (버그 수정 후)
- **예상 완료**: 6시간 이내 (각 피험자 30-60분)

**예상 출력**:
- 40개 디렉토리 (10 subjects × 4 ROIs: V1, V2, V3, hV4)
- 각 디렉토리: trial_betas.npy (384 trials × n_voxels), quality_metrics.json

---

## 3. 이전 단계 결과 및 교훈

### Step 1.2: Reliability Comparison (완료, 실패)

**목적**: Color-averaged vs Trial-wise 방법 비교

**결과**: 치명적 버그 발견
- ❌ Color-averaged 방법: GLM contrast naming 이슈로 완전 실패
- ⚠️ Trial-wise (LS-S): 작동하지만 reliability 매우 낮음 (0.04-0.16)

**교훈**:
1. ✅ LS-S 기술적 검증 완료 (432 trials 추출 성공)
2. ✅ 버그 식별 완료 (contrast naming, masker/GLM 충돌)
3. ⚠️ 낮은 reliability → Step 1.3의 개선된 코드로 해결 시도 중

**Step 1.3 개선 사항**:
- Masker와 GLM 역할 명확히 분리
- 단일 'target' contrast 사용 (color name 직접 사용 안 함)
- Production-grade 코드 (Step 1.2는 진단용)

---

## 4. 예상 결과 및 의미

### 성공 기준

**Tier-1 메트릭**: Split-half Reliability (Procrustes-based)
- **목표**: ≥ 0.50 (색상별 평균)
- **의미**: Odd runs vs Even runs 패턴 일관성
- **중요성**: Hyperalignment의 전제 조건

**Tier-2 메트릭**: Temporal SNR
- **목표**: ≥ 20
- **의미**: Trial-to-trial 신호 안정성

### 시나리오별 판단

| Scenario | Mean Reliability | Decision |
|----------|------------------|----------|
| **Excellent** | ≥ 0.60 | ✅ 모든 ROI/피험자로 즉시 Step 1.4 진행 |
| **Good** | 0.50-0.59 | ✅ 선택적 ROI (V1>V2>V3>hV4)로 Step 1.4 진행 |
| **Acceptable** | 0.30-0.49 | ⚠️ V1, V2만 진행, V3/hV4 파라미터 재조정 |
| **Poor** | < 0.30 | ❌ 파라미터 grid search, 방법론 재검토 |

### 결과의 의미 (과학적)

**High Reliability (≥ 0.50)**:
- ✅ Trial-wise 패턴이 run 간 재현 가능
- ✅ Hyperalignment 가능 (384 correspondence points 사용)
- ✅ Phase 2-3로 진행 가능

**Low Reliability (< 0.50)**:
- ⚠️ 데이터 품질 문제 or 파라미터 부적절
- ⚠️ 추가 최적화 필요 (smoothing, confounds, HRF model)
- ⚠️ 또는 방법론 근본 재검토

---

## 5. 다음 단계 (Step 1.4: Hyperalignment)

### 조건

Step 1.3 reliability ≥ 0.50 달성 시

### 목적

**HC 5명을 공통 representational space로 정렬**
- 피험자 간 좌표계 차이 제거 (RDM correlation: 0.26 → 0.70+ 목표)
- Procrustes stability 유지 (0.91 수준)

### 방법론 선택지

**Option A: Hyperalignment (GPA)**
- 반복적 Procrustes alignment
- 384 correspondence points 사용
- 직교 변환만 (magnitude 보존)
- **장점**: 간단, 해석 용이
- **단점**: T ≈ p (384 vs 300-500 voxels), 정규화 없음

**Option B: SRM (Shared Response Model)**
- 확률적 잠재 공간 (k=30 차원)
- 차원 축소 내장
- 문헌 지지 (task-based fMRI)
- **장점**: Sample efficiency (T/k = 1280%), 정규화 내장
- **단점**: 하이퍼파라미터 선택 (k), 덜 해석적

**결정**: 둘 다 구현 후 비교 (1-2일)

### 평가 메트릭

1. **Inter-subject Correlation (ISC)**: > 0.30 목표
2. **Leave-One-Subject-Out (LOSO) decoding**: > 25% (chance: 12.5%)
3. **Procrustes disparity**: < 0.08 (aligned space 내)

---

## 6. 전체 타임라인

### 완료된 단계 ✅
- **Phase 0**: Baseline decoding (2025년)
- **Step 1.2**: Reliability check (2026-01-09, 버그 있지만 교훈 얻음)

### 진행 중 🚀
- **Step 1.3**: Trial-wise GLM (2026-01-10, 6시간 이내)

### 다음 단계 (예상)

**Step 1.4-1.5 (1-2주)**:
- Hyperalignment vs SRM 구현 및 비교 (1-2일)
- Best method 선택 (0.5일)
- CVD projection 및 차이 정량화 (1일)
- 결과 분석 및 논문 작성 (3-5일)

**Phase 2: Continuous Hue Encoder (2주)**:
- 360° forward model 설계
- SOTA model 조사 (Linear vs Non-linear)
- Trial-wise prediction 구현
- 평가 및 최적화

**Phase 3: CVD Filter Optimization (1주)**:
- 3D loss 함수 (magnitude, baseline, RDM)
- Gradient-based optimization
- 개인화 필터 학습
- CVD→HC 변환 평가

**Total**: 4-5주 예상

---

## 7. 주요 이슈 및 리스크

### 해결된 이슈 ✅

1. **T << p 문제**: Run-averaged (48) → Trial-wise (384)로 해결
2. **GLM preprocessing 충돌**: Masker와 FirstLevelModel 역할 분리
3. **서버 리소스**: 32GB × 10 = 320GB < 452GB (node4 가용)

### 미해결 이슈 ⚠️

1. **Step 1.2 낮은 reliability (0.04-0.16)**:
   - **원인 불명**: 버그? 데이터? 파라미터?
   - **대응**: Step 1.3 개선된 코드로 재시도 중
   - **리스크**: Step 1.3도 낮으면 파라미터 grid search 필요 (2-3일 지연)

2. **Tier 3 피험자 (sub-06, sub-07)**:
   - Preprocessing quality 낮음 (Dice 0.73-0.75)
   - **결정 보류**: Step 1.3 결과로 포함 vs 제외 판단

3. **Hyperalignment vs SRM**:
   - 문헌에서 명확한 Winner 없음
   - **대응**: 둘 다 구현 후 데이터 기반 선택

### 리스크 분석

**High Risk** 🔴:
- Step 1.3 reliability < 0.30
  - **영향**: 2-3주 지연 (파라미터 최적화)
  - **확률**: 중간 (Step 1.2 결과 기반)
  - **대응**: Grid search (smoothing, confounds, HRF)

**Medium Risk** 🟡:
- Hyperalignment 실패 (ISC < 0.30)
  - **영향**: 1주 지연 (SRM으로 전환)
  - **확률**: 낮음 (문헌 지지)
  - **대응**: SRM 대안 준비됨

**Low Risk** 🟢:
- 서버 리소스 부족
  - **영향**: 실행 시간 증가
  - **확률**: 매우 낮음 (리소스 계획 완료)
  - **대응**: Job throttling 가능

---

## 8. 데이터 및 코드

### 데이터

**fMRIPrep 출력** (original_v3):
- 10 subjects (HC 7명 + CVD 3명)
- 4 ROIs (V1, V2, V3, hV4) per subject
- 6 runs × 72 trials = 432 total trials per subject-ROI

**현재 생성 중**:
- Trial-wise beta maps: 384 trials × n_voxels per subject-ROI
- Quality metrics: Reliability, tSNR

### 코드 저장소

**경로**: `/Users/jinilkim/.../prediction_model_workspace/`

**주요 스크립트**:
```
scripts/
├── 00_check_data_structure.py       # Step 1.1 (보류)
├── 01_reliability_comparison.py      # Step 1.2 (완료)
├── 02_trial_wise_glm.py             # Step 1.3 (실행 중) ★
├── aggregate_trial_glm_results.py   # 집계 스크립트
└── run_02_trial_wise_glm.sbatch     # SLURM 배치 파일 ★
```

**문서**:
```
docs/
├── CURRENT_PROGRESS_SUMMARY.md        # 진행 상황 요약 ★
├── RESULTS_INTERPRETATION_GUIDE.md    # 결과 해석 가이드 ★
├── LOCAL_EXECUTION_GUIDE.md           # 로컬 실행 가이드 ★
└── COLLEAGUE_REPORT.md                # 이 문서 ★
```

---

## 9. 결과 확인 방법 (비행 후)

### 빠른 확인 (30분)

1. **서버 작업 완료 확인**:
   ```bash
   ssh haba6030@node2
   squeue -u haba6030  # Empty면 완료
   ```

2. **서버에서 집계 실행**:
   ```bash
   cd /scratch/.../scripts
   python aggregate_trial_glm_results.py
   ```

3. **요약 파일 다운로드**:
   ```bash
   scp haba6030@node2:/scratch/.../trial_glm_summary.txt ./
   scp haba6030@node2:/scratch/.../trial_glm_summary.png ./
   ```

4. **결과 확인**:
   ```bash
   cat trial_glm_summary.txt  # 텍스트 확인
   open trial_glm_summary.png  # 시각화
   ```

5. **의사결정**:
   - Overall mean reliability 확인
   - RESULTS_INTERPRETATION_GUIDE.md 참조
   - 다음 단계 결정 (PROCEED vs ADJUST vs REDO)

### 상세 가이드

**LOCAL_EXECUTION_GUIDE.md** 참조
- 단계별 체크리스트
- 추가 시각화 스크립트
- 문제 해결 방법

---

## 10. Key Takeaways

### 과학적 기여

1. **방법론 개선**: Run-averaged → Trial-wise (T << p 문제 해결)
2. **Hyperalignment 검증**: 8 discrete colors로 384 correspondence points 생성
3. **CVD 표상 정량화**: 3D characterization (magnitude, baseline, structure)

### 기술적 성과

1. ✅ LS-S GLM 파이프라인 구축
2. ✅ 대규모 배치 처리 (10 subjects × 4 ROIs × 384 trials)
3. ✅ 자동화된 품질 평가 (reliability, tSNR)

### 다음 마일스톤

- **즉시**: Step 1.3 결과 확인 (6시간 이내)
- **1주**: Hyperalignment 완료, CVD projection
- **2-3주**: Phase 2 (360° encoder) 완료
- **4주**: Phase 3 (CVD filter) 완료
- **5주**: 논문 초안 작성

---

## 11. References

### 내부 문서
- `CURRENT_PROGRESS_SUMMARY.md`: 전체 진행 상황
- `RESULTS_INTERPRETATION_GUIDE.md`: 결과 해석 기준
- `LOCAL_EXECUTION_GUIDE.md`: 로컬 실행 방법
- `MASTER_PLAN.md`: 전체 TODO 체크리스트
- `PIPELINE_GUIDE.md`: Decision flow

### 방법론 비교
- `analysis/future_phase1_hyperalignment/COMPARISON.md`: Hyperalignment vs SRM

### 문헌
- Brouwer & Heeger (2009): "Decoding and reconstructing color from responses in human visual cortex"
- Haxby et al. (2011): "A common, high-dimensional model of the representational space in human ventral temporal cortex"
- Chen et al. (2015): "A reduced-dimension fMRI shared response model" (SRM)

---

## Contact

**프로젝트 리드**: [Your Name]

**서버**: node2, node4 (haba6030@node2)

**데이터 위치**:
- Server: `/scratch/connectome/haba6030/colorBlind/`
- Local: `/Users/jinilkim/.../colorBlind_analysis/`

**상태 업데이트**:
- CURRENT_PROGRESS_SUMMARY.md
- SLURM 로그: `/scratch/.../logs/`

---

**Report Date**: 2026-01-10
**Status**: Step 1.3 실행 중 (6시간 이내 완료 예상)
**Next Update**: Step 1.3 결과 확인 후 (비행 후)
