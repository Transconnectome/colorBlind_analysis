---
name: capture-results
description: fMRI 분석 결과를 파싱하여 논문용 요약을 생성합니다. "capture results", "결과 정리", "결과 요약", "update paper summary", "논문 결과 업데이트" 요청 시 사용.
recommended-model: sonnet
---

> **Model hint**: Use `model: "sonnet"` when spawning subagents for this skill (analytical task: metric parsing + ROI comparison + paper summary).

# 결과 캡처 (capture-results)

## 목적

각 분석 phase의 결과 파일(JSON, .npy 통계, SLURM 로그)을 파싱하여 논문용 구조화된 요약을 생성합니다.

---

## 결과 소스

| Phase | 결과 위치 | 주요 파일 |
|-------|----------|----------|
| phase1 | `analysis/phase1_preprocess_decoding/results/` | results.json, accuracy*.json |
| phase2_SRM | `analysis/phase2_SRM_across_between/results/` | results.json, *_summary.json |
| phase2_procrustes | `derivatives/phase2_procrustes/` | results.json, disparity*.npy |
| phase3 | `derivatives/phase3_filters/` | results.json, loss*.json |
| future_phases | `analysis/future_phase{1,2,3}_*/results/` | results.json |

---

## 동작 순서

1. **대상 phase 확인**: 사용자가 지정하거나, 최신 결과가 있는 phase 자동 감지
2. **결과 파일 읽기**:
   - `results.json` → 주요 메트릭 추출
   - `settings.json` → 사용된 파라미터 확인
   - `.npy` 파일 → shape + 기본 통계 (mean, std, min, max) 보고
3. **ROI별 정리**: V1, V2, V3, hV4 각각에 대한 결과 분리
4. **그룹 비교**: HC (sub-01~07) vs CVD (sub-08~10) 메트릭 분리
5. **요약 생성**: `analysis/METHODS_RESULTS_SUMMARY_FOR_PAPER.md`에 추가

---

## 피험자 그룹

```
HC (n=7):  sub-01, sub-02, sub-03, sub-04, sub-05, sub-06, sub-07
CVD (n=3): sub-08, sub-09, sub-10
```

---

## 출력 형식

### 마크다운 요약 (METHODS_RESULTS_SUMMARY_FOR_PAPER.md에 추가)

```markdown
## [Phase Name] Results — [날짜]

### Settings
- Parameter1: value1
- Parameter2: value2

### Results by ROI

| ROI | Metric | HC Mean (SD) | CVD Mean (SD) | Difference | p-value | Cohen's d | 95% CI |
|-----|--------|-------------|---------------|------------|---------|-----------|--------|
| V1  | ...    | ...         | ...           | ...        | ...     | ...       | ...    |
| V2  | ...    | ...         | ...           | ...        | ...     | ...       | ...    |
| V3  | ...    | ...         | ...           | ...        | ...     | ...       | ...    |
| hV4 | ...    | ...         | ...           | ...        | ...     | ...       | ...    |

### Individual CVD Profiles
- sub-08: [개별 결과]
- sub-09: [개별 결과]
- sub-10: [개별 결과]

### Key Findings
1. ...
2. ...
```

---

## 필수 포함 항목

모든 결과 요약에 반드시 포함:
- **Exact p-values**: p = 0.023 (p < 0.05로 뭉뚱그리지 않음)
- **Cohen's d**: 효과 크기
- **HC-CVD 그룹 평균 + SD**: M = 0.85, SD = 0.12
- **95% CI**: [0.71, 0.99]
- **개별 CVD 프로필**: n=3이므로 개별 결과 항상 보고

---

## .npy 파일 처리

.npy 파일은 직접 읽지 않고, 관련 JSON에서 참조하거나 shape/stats만 보고:

```python
# 서버에서 실행할 보조 스크립트 (필요 시)
import numpy as np
data = np.load('file.npy')
print(f"Shape: {data.shape}")
print(f"Mean: {data.mean():.4f}, SD: {data.std():.4f}")
print(f"Min: {data.min():.4f}, Max: {data.max():.4f}")
```

---

## 체크리스트

- [ ] 정확한 p-value 포함 (근사값 아님)
- [ ] Cohen's d 효과 크기 포함
- [ ] HC/CVD 그룹 평균 + SD 포함
- [ ] 95% CI 포함
- [ ] 개별 CVD 프로필 (sub-08, 09, 10) 포함
- [ ] ROI별 (V1, V2, V3, hV4) 결과 분리
- [ ] 타임스탬프가 있는 섹션 헤더
- [ ] METHODS_RESULTS_SUMMARY_FOR_PAPER.md에 추가됨
