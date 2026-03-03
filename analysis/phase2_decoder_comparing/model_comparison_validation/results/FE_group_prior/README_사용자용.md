# FE_GroupPrior 분석 결과 요약 (2026-02-25)

## 📌 핵심 요약

### 1. 마크다운 파일 통합 완료 ✅
**위치**: `FE_GroupPrior_Complete_Analysis.md`

기존 3개 파일(PAPER_SUMMARY.md, NEXT_STEPS.md, RESULTS_CAPTURED.md)을 **하나로 통합**했습니다.

### 2. 사용자 지적사항 반영 ✅

**원래 권장사항** (❌ 잘못됨):
- λ=0 (pure group prior)를 강제로 사용
- "개인 모델이 불안정하니 HC 평균만 사용하자"

**문제점**:
- λ=0은 **개인차를 완전히 무시**함
- CVD 피험자의 고유한 색 표상을 놓치게 됨
- 특히 V4에서 sub-08이 group prior로 인해 **오히려 악화**됨 (82.9° → 103.8°)

**수정된 권장사항** (✅ 올바름):
- **λ를 높여서** (0.5, 0.7, 0.9, 1.0) 개인차를 더 반영해야 함
- 특히 CVD 피험자는 **개인별 모델 (λ=1.0)**이 더 나을 수 있음
- Nested CV에서 λ=0이 선택된 것은 **validation artifact**일 가능성:
  - Inner validation fold가 1개 색만 사용 → 너무 작아서 불안정
  - 그래서 가장 안전한 λ=0이 선택된 것
  - 하지만 실제 test set(8개 색)에서는 λ가 높은 게 더 나을 수 있음

---

## 📊 현재 결과 요약

### V2: HC < CVD 유의미 (p=0.0086, d=-2.39)
- GP_ensemble: HC 32.8±5.4° vs CVD 45.3±4.7°
- **재해석**: CVD V2가 "나쁜" 게 아니라, **HC normative와 다른** 것
  - λ=0 (HC 평균 강제) → CVD에게 불리
  - λ 높이면 → CVD 고유 encoding 사용 → 차이 줄어들 가능성

### V4: Group prior가 CVD를 해침
- sub-08: baseline 82.9° → GP 103.8° (**+20.9° 악화**)
- **해석**: HC normative가 CVD V4와 **호환되지 않음**
  - 개인별 모델(λ=1)이 더 나음
  - CVD-specific group prior 필요할 수 있음

### V3: CVD < HC (예상 밖)
- CVD 88.3° vs HC 99.3° (+11.0°, CVD가 더 좋음)
- SRM K=3 artifact 가능성 → K=4로 재검증 필요

---

## 🚀 다음 단계 (우선순위)

### Priority 1: Fixed Lambda Grid 테스트 (가장 중요!)

**목적**: 최적 λ 값이 정말 0인지, 아니면 더 높은지 확인

**스크립트 생성 완료**:
```bash
# 로컬에서 생성된 파일들
analysis/phase2_decoder_comparing/model_comparison_validation/scripts/
├── validate_fixed_lambda_grid.py    # 메인 스크립트
└── validate_lambda_grid.sbatch      # SLURM batch 파일
```

**서버 업로드 및 실행**:
```bash
# 1. 서버에 업로드
scp validate_fixed_lambda_grid.py validate_lambda_grid.sbatch \
    haba6030@node3:/scratch/connectome/haba6030/colorBlind/analysis/phase2_decoder_comparing/model_comparison_validation/scripts/

# 2. 서버에서 실행
ssh node3
cd /scratch/connectome/haba6030/colorBlind/analysis/phase2_decoder_comparing/model_comparison_validation/scripts
sbatch validate_lambda_grid.sbatch

# 3. 결과 확인 (2시간 후)
cat /scratch/connectome/haba6030/colorBlind/analysis/phase2_decoder_comparing/model_comparison_validation/results/FE_lambda_grid/lambda_grid_*.out

# 4. 결과 다운로드
scp -r haba6030@node3:/scratch/connectome/haba6030/colorBlind/analysis/phase2_decoder_comparing/model_comparison_validation/results/FE_lambda_grid \
    analysis/phase2_decoder_comparing/model_comparison_validation/results/
```

**테스트 λ 값**: 0.0, 0.3, 0.5, 0.7, 0.9, 1.0

**예상 결과**:
- **V1/V2 HC**: λ=0~0.3 최적 (group prior 도움됨)
- **V4 CVD**: λ=0.7~1.0 최적 (개인 모델 필요)
- **HC-CVD 차이**: λ 높일수록 차이 감소 예상

**분석할 지표**:
1. 각 λ에서 HC vs CVD MAE
2. HC-CVD difference가 최소화되는 λ 찾기
3. ROI별, 그룹별 최적 λ 다를 가능성

### Priority 2: CVD-Specific Group Prior 테스트

**가설**: CVD 피험자끼리는 일관된 encoding 공유

**테스트**:
- HC-prior (현재): W_group = mean(HC 피험자들)
- **CVD-prior (신규)**: W_group = mean(CVD 피험자들)
- CVD V4에서 CVD-prior가 HC-prior보다 나을 것

### Priority 3: V3 Anomaly 조사

- SRM K=4로 재실행 (현재 K=3)
- Voxel count, tSNR 체크
- Raw/Procrustes 데이터에서도 같은 패턴인지 확인

---

## 📁 생성된 파일 목록

### 통합 분석 문서
- **`FE_GroupPrior_Complete_Analysis.md`** ← **메인 문서 (여기 보세요!)**

### 결과 데이터
- `fe_group_prior_results.json` — 전체 결과
- `fe_group_prior_statistics.json` — 통계 분석 (t-test, Crawford-Howell)
- `subject_results/` — 피험자별 JSON (10개 + group summary)

### 분석 스크립트
- `parse_results.py` — SLURM .out → JSON 변환
- `FE_GroupPrior_Analysis.py` — 통계 분석
- `generate_subject_jsons.py` — 피험자 JSON 생성

### 신규 스크립트 (Lambda grid test용)
- `validate_fixed_lambda_grid.py` — Fixed λ 테스트 스크립트
- `validate_lambda_grid.sbatch` — SLURM batch 파일

**위치**: `analysis/phase2_decoder_comparing/model_comparison_validation/results/FE_group_prior/`

---

## 🔬 핵심 결론 (수정됨)

### 1. λ=0 선택은 validation artifact일 가능성 높음
- Inner validation이 1개 색만 사용 → 불안정
- Outer test set(8개 색)에서는 더 높은 λ가 좋을 수 있음

### 2. 개인차 보존이 중요 (특히 CVD)
- **사용자 지적 정확함**: λ=0은 개인차를 무시 → CVD 특성 못 잡음
- λ 높이면 → CVD 고유 encoding 반영 가능

### 3. ROI/그룹별로 최적 λ 다를 것
- V1/V2 HC: Group prior 도움 (λ 낮음)
- V4 CVD: Individual model 필수 (λ 높음)
- **Adaptive λ** 전략 필요

### 4. 다음 액션
1. ✅ **Fixed λ grid test 실행** (가장 중요!)
2. 결과 분석 후 최적 λ 결정
3. CVD-specific group prior 테스트
4. 논문용 figure 생성

---

## 📊 예상되는 결과 패턴

### 시나리오 A: λ 높일수록 CVD 성능 개선
```
V4 CVD MAE:
λ=0.0: 86.3° (현재, group prior)
λ=0.5: 80.0° (개선)
λ=0.7: 75.0° (더 개선)
λ=1.0: 72.0° (최적, individual)

→ 결론: CVD는 개인별 모델 필요, HC normative 부적합
```

### 시나리오 B: λ=0.5 정도가 최적
```
V2 HC-CVD difference:
λ=0.0: -12.5° (현재, 큰 차이)
λ=0.5: -6.0° (차이 감소)
λ=1.0: -8.0° (개인 모델, 여전히 차이)

→ 결론: 적당한 shrinkage가 최적, 완전 individual/group 둘 다 아님
```

### 시나리오 C: ROI별로 최적 λ 다름
```
V1: λ=0.0~0.3 최적 (group prior 효과적)
V2: λ=0.3~0.5 최적 (중간)
V4: λ=0.7~1.0 최적 (individual 필요)

→ 결론: 위계적 차이, early visual은 공유/higher는 개인화
```

---

## 💡 이론적 함의

### 원래 해석 (λ=0 기준)
"CVD V2는 HC보다 색 encoding이 나쁘다"

### 수정된 해석 (λ 고려)
"CVD V2는 HC와 **다른** 색 encoding을 사용한다"
- λ=0 (HC 강제) → CVD 불리
- λ 높이면 → CVD 고유 전략 사용 → 성능 회복 가능

### 예측
- **V1/V2**: Shared encoding (λ 낮음 OK)
- **V4**: Individual-specific (λ 높음 필수)
- **CVD**: HC normative 부적합 → 독립 모델 또는 CVD-specific prior

---

**작성**: 2026-02-25
**상태**: Lambda grid test 준비 완료, 서버 실행 대기 중
**다음**: Fixed λ grid 결과 분석 → 최적 λ 결정 → 논문 작성
