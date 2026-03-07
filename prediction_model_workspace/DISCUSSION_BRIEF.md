# 연구 현황 및 논의 포인트

**작성일**: 2026-01-11
**목적**: 동료와의 연구 진행 상황 논의 및 향후 계획 수립

---

## 1. 프로젝트 개요

### 연구 목표
색맹(CVD) 피험자의 뇌 색상 표상을 정상(HC) 피험자와 비교하여, 신경 기반 개인화 필터를 학습하는 것

### 데이터셋
- **피험자**: HC 7명 (sub-01~07), CVD 3명 (sub-08~10)
- **분석 가능**: Tier 1+2 8명 (sub-01,02,03,04,05,08,09,10)
- **과제**: RSVP 색상 자극 (8 colors × 6 runs)
- **ROI**: V1, V2, V3, hV4 (Wang Atlas 2015)
- **데이터**: fMRIPrep original_v3 (Dice 0.889, 83.3% pass rate)

### 전체 파이프라인 구조
```
Phase 0: Baseline Decoding (완료)
  ↓
Step 1.1: Data Structure Check (미완료)
Step 1.2: Reliability Comparison (미완료)
Step 1.3: Trial-wise GLM (재실행 중) ← 현재 위치
Step 1.4: Hyperalignment (예정)
  ↓
Future Phase 2: Continuous Hue Encoder (360°)
Future Phase 3: CVD Filter Optimization
```

---

## 2. 현재 상황 (Step 1.3)

### 2.1 무엇을 하고 있는가?

**목표**: LS-S (Least-Squares Separate) GLM을 사용하여 **개별 trial의 beta 패턴** 추출

**방법**:
- 각 stimulus 제시를 독립적으로 모델링
- 6 runs × ~72 color trials/run = **~432 trials** (individual patterns)
- Phase 0와 달리 run-averaging 없음

**용도**:
- Step 1.4 Hyperalignment에서 trial-aligned GPA 수행
- HC 피험자 간 trial 단위 대응 필요
- 384 correspondence points로 정렬

### 2.2 진행 상황

**버그 발견 및 수정** (2026-01-11):
- **문제**: 스크립트가 `'red'`, `'orange'`, ... 기대 → 실제 파일은 `'color_1'`, ..., `'color_8'`
- **결과**: 모든 피험자에서 "Color trials: 0" 에러
- **수정**: `color_names = ['color_1', ..., 'color_8']` 변경
- **재실행**: 24시간 timeout으로 재실행 중

**예비 결과** (sub-10 V1, 버그 수정 후):
- ✅ Trial 추출 성공: 330 trials (0이 아님)
- ❌ Split-half reliability: **0.021** (목표: ≥0.50)
- ⚠️ 예상보다 낮은 trial 수: 330/432 (76%)

### 2.3 핵심 문제

**왜 Phase 0는 잘 작동했는데 trial-wise는 reliability가 낮을까?**

| 측면 | Phase 0 (Baseline) | Step 1.3 (Trial-wise) |
|------|--------------------|-----------------------|
| **Approach** | Run-averaged | Individual trials |
| **Pattern 수** | 48 (6 runs × 8 colors) | 330~432 trials |
| **Averaging** | 8 stimuli/color → 1 pattern | No averaging |
| **SNR** | High (averaging reduces noise) | Low (single trial noise) |
| **Reliability** | 0.85~0.91 ✅ | 0.021 ❌ |

**가설**: Averaging이 noise를 감소시켜 Phase 0에서 높은 reliability를 달성했으나, trial-wise에서는 개별 trial의 noise가 그대로 노출되어 reliability가 낮아짐.

---

## 3. 다음 단계 (착륙 후 우선순위)

### 3.1 즉시 확인 사항 (30분)

1. **작업 완료 확인**:
   ```bash
   ssh haba6030@node2
   squeue -u haba6030  # Empty?
   ls /scratch/connectome/haba6030/colorBlind/prediction_model_workspace/results/trial_wise_glm/original_v3/ | wc -l
   # 예상: 41 (40개 디렉토리 + 1 header)
   ```

2. **결과 집계**:
   ```bash
   cd /scratch/connectome/haba6030/colorBlind/prediction_model_workspace/scripts
   python aggregate_trial_glm_results.py \
       --input_dir ../results/trial_wise_glm/original_v3 \
       --output_dir ../results/trial_wise_glm/original_v3
   ```

3. **다운로드**:
   ```bash
   # 로컬 터미널
   cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/prediction_model_workspace/results/trial_wise_glm/
   scp haba6030@node2:/scratch/.../trial_glm_detailed.csv ./
   scp haba6030@node2:/scratch/.../trial_glm_summary.png ./
   scp haba6030@node2:/scratch/.../trial_glm_summary.txt ./
   ```

4. **빠른 판단**:
   ```python
   import pandas as pd
   df = pd.read_csv('trial_glm_detailed.csv')
   overall_mean = df['reliability_mean'].mean()
   pass_rate = (df['reliability_mean'] >= 0.50).sum() / len(df)

   print(f"Overall mean: {overall_mean:.3f}")
   print(f"Pass rate: {pass_rate*100:.1f}%")
   ```

### 3.2 시나리오별 대응

| 시나리오 | Overall Mean | 다음 단계 | 예상 타임라인 |
|----------|--------------|-----------|---------------|
| **Excellent** | ≥0.60 | 즉시 Step 1.4 (Hyperalignment) | 1-2일 |
| **Good** | 0.50-0.59 | Step 1.4 (V1,V2 우선) | 2-3일 |
| **Acceptable** | 0.30-0.49 | V1,V2만 진행 + 파라미터 조정 | 3-4일 |
| **Poor** | <0.30 | **Baseline 비교 분석 필요** | 1-2주 |

**예비 결과 기반 예상**: Poor scenario 가능성 높음 (sub-10 = 0.021)

### 3.3 Poor Scenario 대응 (우선순위)

**1단계: Baseline vs Trial-wise 비교 분석** (최우선):
```bash
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/prediction_model_workspace/scripts

python compare_baseline_vs_trialwise.py \
    --subject 10 \
    --roi V1 \
    --baseline_dir /scratch/.../derivatives/BH2009_deoblique_v2/baseline81_deob_determin \
    --trialwise_dir /scratch/.../results/trial_wise_glm/original_v3
```

**분석 내용**:
- Baseline (run-averaged) vs Trial-wise (individual) SNR 비교
- Color-averaging trial-wise 데이터의 reliability 회복 가능성
- Averaging 효과 정량화 (4-panel figure)

**2단계: 의사결정**:
- **Option A**: Color-averaging trial-wise 데이터 사용 (48 patterns like Phase 0)
  - 장점: Reliability 회복 예상
  - 단점: Trial-level correspondence 상실 (Hyperalignment 불가)

- **Option B**: Trial-wise 유지 + 파라미터 최적화
  - Smoothing: 6mm → 8mm → 10mm
  - HRF: spm → spm+derivative
  - Confounds: motion → motion+acompcor
  - 장점: Trial-level alignment 가능
  - 단점: Reliability 개선 보장 없음

- **Option C**: 방법론 재검토
  - Step 1.4 Hyperalignment 대신 Phase 0 기반 Procrustes alignment 사용
  - Future Phase 2에서 continuous hue interpolation만 수행
  - 장점: Phase 0 결과 활용, 검증된 방법
  - 단점: Trial-level analysis 포기

---

## 4. 논의 포인트

### 4.1 핵심 질문

1. **Reliability 기준**: 0.50이 적절한가? Trial-wise에서는 더 낮은 기준을 수용해야 하는가?

2. **Averaging Trade-off**:
   - Trial-level alignment (Hyperalignment 가능) vs
   - High reliability (color-averaging 필요)
   - 둘 다 필요한가? 하나를 포기할 수 있는가?

3. **Downstream Impact**:
   - Future Phase 2 (continuous hue encoder)에 trial-level data가 필수인가?
   - Color-level data (48 patterns)로도 360° interpolation 가능한가?

4. **리소스 할당**:
   - 파라미터 최적화에 1-2주 투자할 가치가 있는가?
   - 아니면 방법론 pivot이 더 효율적인가?

### 4.2 문헌 참조 필요 사항

1. **Trial-wise GLM reliability benchmarks**:
   - LS-S 방법론에서 기대되는 reliability 범위는?
   - 다른 연구에서는 얼마나 달성했는가?

2. **Hyperalignment data requirements**:
   - Trial correspondence가 정말 필수인가?
   - Run-averaged data로 hyperalignment 성공 사례는?

3. **Forward encoding model with limited data**:
   - 48 patterns vs 384 trials에서 continuous hue prediction 차이는?
   - Small-sample encoder는 어떤 접근이 효과적인가?

### 4.3 의사결정 프레임워크

**단기 결정** (이번 주):
- [ ] 전체 결과 확인 (Overall mean reliability)
- [ ] Baseline 비교 분석 실행
- [ ] Option A, B, C 중 선택

**중기 계획** (2-3주):
- [ ] 선택한 option 구현 및 검증
- [ ] Step 1.4 또는 대안 방법 실행
- [ ] Future Phase 2 데이터 요구사항 재평가

**장기 전략** (1-2달):
- [ ] 전체 파이프라인 재검토
- [ ] 논문 방향성 조정 (필요시)
- [ ] CVD filter learning 목표 재정의

---

## 5. 참조 파일 (절대 경로)

### 5.1 프로젝트 문서

**전체 구조**:
- `/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/CLAUDE.md`
- `/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/README.md`
- `/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/README.md`

**현재 작업 (Workspace)**:
- `/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/prediction_model_workspace/MASTER_PLAN.md` - 전체 TODO 체크리스트
- `/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/prediction_model_workspace/QUICK_START.md` - 단계별 실행 가이드
- `/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/prediction_model_workspace/PIPELINE_GUIDE.md` - 결정 트리

**상세 계획**:
- `/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/prediction_model_workspace/docs/PHASE1_HYPERALIGNMENT.md`
- `/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/prediction_model_workspace/docs/PHASE2_FORWARD_MODEL.md`
- `/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/prediction_model_workspace/docs/PHASE3_FILTER_OPTIMIZATION.md`

### 5.2 현재 상태 문서

**진행 상황**:
- `/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/prediction_model_workspace/CURRENT_STATUS_EXPLAINED.md` - 종합 설명
- `/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/prediction_model_workspace/docs/CURRENT_PROGRESS_SUMMARY.md` - 진행 요약
- `/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/prediction_model_workspace/docs/COLLEAGUE_REPORT.md` - 동료 보고서

**버그 관련**:
- `/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/prediction_model_workspace/FIX_SUMMARY.md` - 버그 수정 상세

### 5.3 실행 스크립트

**Step 1.3 (현재)**:
- `/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/prediction_model_workspace/scripts/02_trial_wise_glm.py`
- `/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/prediction_model_workspace/scripts/run_02_trial_wise_glm.sbatch`

**결과 분석**:
- `/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/prediction_model_workspace/scripts/aggregate_trial_glm_results.py`
- `/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/prediction_model_workspace/scripts/compare_baseline_vs_trialwise.py`

**Step 1.4 (예정)**:
- `/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/archive/future_phase1_hyperalignment/scripts/hyperalignment_core.py`
- `/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/archive/future_phase1_hyperalignment/COMPARISON.md` - Hyperalignment vs SRM 비교

### 5.4 서버 경로

**결과 위치**:
- 서버: `/scratch/connectome/haba6030/colorBlind/prediction_model_workspace/results/trial_wise_glm/original_v3/`
- 로컬 (다운로드 후): `/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/prediction_model_workspace/results/trial_wise_glm/`

**로그 위치**:
- 서버: `/scratch/connectome/haba6030/colorBlind/prediction_model_workspace/logs/trial_glm_sub-*_*.out`
- 로컬: `/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/prediction_model_workspace/logs/`

**Baseline 데이터** (Phase 0):
- 서버: `/scratch/connectome/haba6030/colorBlind/derivatives/BH2009_deoblique_v2/baseline81_deob_determin/sm*_sub-{ID}_{ROI}_*/`
- 파일: `amplitudes_z.npy` (6 runs, 8 colors, n_voxels)

---

## 6. 예상 논의 흐름

### Meeting Agenda 제안

**Part 1: 현재 상황 공유** (10분)
1. Step 1.3 결과 확인
2. Reliability 수치 공유
3. 예비 분석 결과 (sub-10)

**Part 2: 문제 분석** (20분)
1. Phase 0 vs Trial-wise 비교
2. Averaging 효과 논의
3. Reliability 기준 재평가

**Part 3: 의사결정** (20분)
1. Option A, B, C 장단점 논의
2. 문헌 기반 근거 검토
3. 리소스 및 타임라인 고려

**Part 4: 다음 단계** (10분)
1. 즉시 실행할 분석 결정
2. 담당자 및 일정 할당
3. 다음 미팅 일정

---

## 7. 요약

### 현재 위치
- **Step 1.3 (Trial-wise GLM) 재실행 중** (24hr timeout)
- 버그 수정 완료, 예비 결과는 낮은 reliability (0.021)

### 핵심 이슈
Phase 0 (run-averaged)는 성공했으나 trial-wise는 reliability 매우 낮음. Averaging vs Trial-correspondence trade-off 결정 필요.

### 즉시 할 일
1. 전체 결과 확인 및 집계
2. Baseline 비교 분석 실행
3. Option A/B/C 중 선택

### 논의 필요 사항
1. Reliability 기준 재평가
2. Downstream impact 분석
3. 리소스 할당 결정

---

**작성자**: Claude Code
**최종 업데이트**: 2026-01-11
**용도**: 동료와의 연구 진행 논의 및 의사결정
