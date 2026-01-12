# Trial 수 불균등 Error Control 요약

**날짜**: 2026-01-11
**문제**: 예비 결과에서 330/432 trials (76%) - trial 수 불균등
**해결**: Robust error control 추가

---

## 🔍 원본 문제

### 예비 결과 (sub-10 V1)
- **예상**: 432 trials (8 colors × 54 trials/color)
- **실제**: 330 trials (76% recovery)
- **문제**: Trial 수 불균등으로 인한 reliability 계산 오류 가능성

### 가능한 원인
1. Blank trials 제외 (정상)
2. 일부 runs의 trials 누락
3. Onset/duration filtering
4. Event file 불일치

---

## ✅ 추가된 Error Control

### 1. Trial Distribution Diagnostic

**추가 위치**: `extract_trial_betas_efficient()` 함수 끝

**출력 예시**:
```
📊 Trial Distribution Diagnostic:
  By color:
    color_1  :  41 trials
    color_2  :  38 trials
    color_3  :  42 trials
    ...
  By run:
    Run 1: 55 trials
    Run 2: 54 trials
    ...
  Split balance:
    Odd runs (1,3,5):  165 trials
    Even runs (2,4,6): 165 trials
    Balance ratio: 1.00
```

**목적**:
- 색상별 trial 분포 확인
- Run별 trial 분포 확인
- Odd/Even split 균형 확인 (split-half reliability 계산에 중요)

---

### 2. Procrustes Reliability - Trial 수 출력

**변경 전**:
```python
for color in colors:
    if len(odd_trials) > 0 and len(even_trials) > 0:
        # compute reliability
        print(f"  {color}: {stability:.3f}")
```

**변경 후**:
```python
for color in colors:
    if len(odd_trials) > 0 and len(even_trials) > 0:
        # compute reliability
        print(f"  {color}: {stability:.3f} (odd={len(odd_trials):2d}, even={len(even_trials):2d})")
    else:
        print(f"  {color}: SKIPPED (odd={len(odd_trials):2d}, even={len(even_trials):2d})")
```

**출력 예시**:
```
1. Split-half reliability (Procrustes):
  color_1  : 0.123 (odd=20, even=21)
  color_2  : 0.089 (odd=18, even=20)
  color_3  : SKIPPED (odd=2, even=0)  ← 경고!
  ...
  Mean     : 0.095 (7/8 colors)
```

**목적**:
- 각 색상별로 odd/even split에 충분한 trial이 있는지 확인
- SKIPPED 색상 식별

---

### 3. RDM Reliability - Minimum Trial Threshold

**핵심 개선**:
```python
MIN_TRIALS_PER_SPLIT = 3

for color in colors:
    if len(odd_trials) >= MIN_TRIALS_PER_SPLIT and len(even_trials) >= MIN_TRIALS_PER_SPLIT:
        # USE this color
        odd_patterns.append(odd_trials.mean(axis=0))
        even_patterns.append(even_trials.mean(axis=0))
        print(f"  {color}: USED (odd={len(odd_trials)}, even={len(even_trials)})")
    else:
        # SKIP this color
        print(f"  {color}: SKIPPED (odd={len(odd_trials)}, even={len(even_trials)}, min={MIN_TRIALS_PER_SPLIT})")
```

**출력 예시**:
```
2. RDM-based split-half reliability (PRIMARY):
  color_1  : USED (odd=20, even=21)
  color_2  : USED (odd=18, even=20)
  color_3  : SKIPPED (odd=2, even=0, min=3)  ← 제외!
  color_4  : USED (odd=22, even=19)
  ...

  Summary: 7/8 colors usable for RDM

  RDM Spearman r: 0.342 (p=1.2e-05)
  RDM pairs: 21 (from 7×7 matrix)
  ✅ PASS: RDM r ≥ 0.3
```

**목적**:
- Trial 수가 너무 적은 색상 제외 (unreliable averaging)
- RDM 계산에 사용된 색상 명시
- 최소 threshold 문서화 (재현성)

**Threshold 설정 근거**:
- `MIN_TRIALS_PER_SPLIT = 3`: 평균 계산의 최소 신뢰도
- 3 trials의 평균 SEM = σ/√3 ≈ 0.58σ
- 너무 높으면 → 많은 색상 제외
- 너무 낮으면 → Unreliable averaging

---

### 4. Data Quality Check (종합 진단)

**추가된 체크 항목**:

#### Check 1: Total Trial Recovery Rate
```python
recovery_rate = total_trials / EXPECTED_TOTAL_TRIALS  # 432
if recovery_rate < 0.7:
    warning: "❌ Low trial recovery"
elif recovery_rate < 0.85:
    warning: "⚠️ Moderate trial recovery"
else:
    pass: "✅ Good trial recovery"
```

#### Check 2: Color Imbalance
```python
imbalance = (max_count - min_count) / max_count
if imbalance > 0.3:
    warning: "⚠️ High color imbalance"
```

#### Check 3: Missing Runs
```python
missing_runs = [r for r in [1,2,3,4,5,6] if r not in runs_present]
if missing_runs:
    warning: "❌ Missing runs"
```

#### Check 4: Odd/Even Split Balance
```python
split_imbalance = abs(odd_count - even_count) / max(odd_count, even_count)
if split_imbalance > 0.2:
    warning: "⚠️ Odd/Even imbalance"
```

**출력 예시**:
```
4. Trial counts and data quality:
  Total trials: 330/432 (76.4%)

  color_1  : 41/54 trials ( 75.9%) ✅
  color_2  : 38/54 trials ( 70.4%) ⚠️
  color_3  : 42/54 trials ( 77.8%) ✅
  ...

  Data Quality Warnings:
    ✅ Good trial recovery: 76.4%
    ✅ Balanced colors: imbalance=12.2%
    ✅ All 6 runs present
    ✅ Balanced odd/even split: 3.0%
```

---

## 🎯 Error Control 시나리오

### 시나리오 1: 이상적 (432/432 trials)
```
Total trials: 432/432 (100.0%)
RDM: 8/8 colors usable
✅ All checks pass
```
→ 문제 없음

### 시나리오 2: 양호 (330/432 trials, 균등 분포)
```
Total trials: 330/432 (76.4%)
각 색상: 40-42 trials (균등)
Odd/Even: 165/165 (균형)
RDM: 8/8 colors usable (≥3 trials per split)
✅ Good recovery, balanced distribution
```
→ 허용 가능, 분석 진행

### 시나리오 3: 경고 (280/432 trials, 약간 불균등)
```
Total trials: 280/432 (64.8%)
일부 색상: 25-30 trials
Odd/Even: 150/130 (불균형)
RDM: 6/8 colors usable
⚠️ Moderate recovery, some imbalance
```
→ 주의해서 진행, 결과 해석 시 고려

### 시나리오 4: 문제 (200/432 trials, 매우 불균등)
```
Total trials: 200/432 (46.3%)
일부 색상: <10 trials
Odd/Even: 120/80 (심각한 불균형)
RDM: 4/8 colors usable
❌ Low recovery, high imbalance, missing runs
```
→ 데이터 검토 필요, 분석 보류

---

## 📊 저장되는 Metadata

### quality_metrics.json 구조

```json
{
  "split_half_reliability": {
    "by_color": {"color_1": 0.123, ...},
    "mean": 0.095,
    "n_colors_valid": 7,
    "n_colors_total": 8
  },
  "rdm_reliability": {
    "spearman_r": 0.342,
    "p_value": 1.2e-05,
    "n_colors_used": 7,
    "n_colors_skipped": 1,
    "colors_used": ["color_1", "color_2", ...],
    "colors_skipped": ["color_3"],
    "min_trials_threshold": 3
  },
  "trial_counts": {
    "color_1": 41,
    "color_2": 38,
    ...
  },
  "data_quality": {
    "total_trials": 330,
    "expected_trials": 432,
    "recovery_rate": 0.764,
    "color_imbalance": 0.122,
    "runs_present": [1,2,3,4,5,6],
    "missing_runs": [],
    "odd_even_imbalance": 0.030,
    "warnings": []
  }
}
```

**용도**:
- 사후 분석 시 데이터 품질 확인
- Subject/ROI 간 비교
- Exclusion criteria 적용

---

## 🚀 사용 방법

### 업로드 및 실행

```bash
# 로컬에서 서버로 업로드
scp 02_trial_wise_glm_optimized.py haba6030@node2:/scratch/.../scripts/
scp test_02_sub01_V1_optimized.sbatch haba6030@node2:/scratch/.../scripts/

# 서버에서 실행
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind/prediction_model_workspace/scripts
sbatch test_02_sub01_V1_optimized.sbatch
```

### 로그 확인

```bash
# 실시간 로그
tail -f logs/test_trial_glm_opt_sub01_V1_*.out

# Trial distribution 확인
grep -A 20 "Trial Distribution Diagnostic" logs/*.out

# Data quality warnings 확인
grep -A 10 "Data Quality Warnings" logs/*.out

# RDM reliability 확인
grep -A 5 "RDM-based split-half" logs/*.out
```

---

## 🎯 해석 가이드

### RDM Reliability 해석

| RDM r | 색상 수 | Trial 회복률 | 판단 |
|-------|---------|--------------|------|
| ≥0.3 | 8/8 | >85% | ✅ Excellent |
| ≥0.3 | 7/8 | 75-85% | ✅ Good |
| 0.1-0.3 | 6-7/8 | 70-85% | ⚠️ Acceptable |
| <0.1 | <6/8 | <70% | ❌ Poor |

### 경고 대응

**⚠️ Moderate trial recovery (70-85%)**:
- 진행 가능하지만 결과 해석 시 주의
- Trial 수가 적은 색상의 reliability는 낮을 수 있음

**⚠️ Color imbalance >30%**:
- RDM에 일부 색상 제외될 수 있음
- Split-half reliability에 영향 가능

**⚠️ Odd/Even imbalance >20%**:
- Split-half reliability 계산에 영향
- 한 쪽 split이 더 noisy할 수 있음

**❌ Missing runs**:
- 심각한 문제, 데이터 검토 필요
- 특정 run의 파일 누락 또는 처리 실패

---

## 📝 개선 사항 요약

1. **Trial Distribution Diagnostic**: 색상/run/split별 분포 출력
2. **Procrustes with Trial Counts**: 각 색상별 odd/even trial 수 표시
3. **RDM Minimum Threshold**: 3 trials 미만 색상 자동 제외
4. **Comprehensive Quality Check**: 4가지 자동 검사 (recovery, balance, runs, splits)
5. **Detailed Metadata**: 모든 진단 정보 JSON 저장

**결과**: Trial 수 불균등에도 robust하게 대응 가능! ✅

---

**작성**: 2026-01-11
**용도**: Trial 수 불균등 상황에서도 안정적인 분석
