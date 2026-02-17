---
name: proofread
description: fMRI/CVD 색 표상 연구에 특화된 학술 검토를 수행합니다. "proofread", "논문 교정", "방법론 검토", "review methods", "통계 검토", "reviewer feedback" 요청 시 사용.
---

# 논문 교정 (proofread)

## 목적

색각 이상(CVD) 색 표상 fMRI 연구에 특화된 학술 리뷰를 수행합니다. Nature/NeuroImage 수준 리뷰어 관점에서 6가지 차원을 평가합니다.

---

## 주요 검토 대상

- **Primary**: `analysis/METHODS_RESULTS_SUMMARY_FOR_PAPER.md`
- **Cross-reference**: `analysis/phase2_SRM_across_between/results/` 내 실제 결과
- **Settings**: `analysis/phase1_preprocess_decoding/README.md`, `analysis/prep_trials/README.md`

---

## 6가지 검토 차원

### A. 전처리 투명성 (Preprocessing Transparency)

평가 항목:
- fMRIPrep 버전 및 파라미터 명시 여부
- C010 (confound) 선택 근거 설명
- Procrustes 정렬 방법 보고 완전성
- 공간 정규화: MNI152NLin2009cAsym, res-2 명시
- 스무딩 파라미터 및 high-pass 필터 명시

리뷰어 예상 질문:
```
"What confounds were regressed out and why were these specific regressors chosen?"
"Was spatial smoothing applied before or after feature extraction?"
```

### B. 통계적 엄밀성 (Statistical Rigor)

평가 항목:
- 4개 ROI (V1, V2, V3, hV4) 다중비교 보정 여부
- exact p-value 보고 (p < 0.05로 뭉뚱그리지 않음)
- 순열검정 (permutation test) 사용 여부 및 반복 횟수
- 효과 크기 (Cohen's d) 보고
- 신뢰구간 보고

리뷰어 예상 질문:
```
"How were multiple comparisons across ROIs corrected?"
"What was the number of permutations and how was the null distribution generated?"
```

### C. 소표본 문제 (CRITICAL — Small Sample Concerns)

**이 프로젝트의 가장 큰 약점: n=7 HC vs n=3 CVD**

필수 점검:
- [ ] n=3 CVD에 대한 group-level t-test 사용 회피
- [ ] 개별 CVD 프로필 (sub-08, 09, 10) 보고
- [ ] Bootstrap CI 사용 여부
- [ ] 효과 크기 해석에 소표본 한계 명시
- [ ] "group difference" 대신 "individual CVD patterns" 프레이밍
- [ ] 비모수 검정 (Mann-Whitney, permutation) 사용

경고 문구 (반드시 포함):
```
"Given the small CVD sample (n=3), group-level statistical comparisons should
be interpreted with caution. We report individual CVD profiles alongside
group-level descriptive statistics."
```

리뷰어 예상 질문:
```
"With only 3 CVD subjects, how can you justify any group-level inference?"
"Are the observed differences driven by a single outlier subject?"
```

### D. 뇌영상 방법론 (Neuroimaging Specifics)

평가 항목:
- MNI 공간 및 해상도 명시
- ROI 정의 방법: Wang Atlas (2015) 사용 명시
- SRM k-value 선택 근거
- Cross-validation 방법 (leave-one-run-out 등)
- BOLD 신호 추출 방법 (trial-wise beta 등)

리뷰어 예상 질문:
```
"How were ROI boundaries defined and what atlas was used?"
"What was the rationale for the chosen number of SRM components?"
```

### E. CVD 방법론 (CVD Methodology)

평가 항목:
- CVD 진단 방법 명시 (Ishihara, anomaloscope 등)
- CVD 하위 유형 구분 (protan, deutan, tritan)
- 자극 디자인의 CVD 가시성 고려
- 8색 자극의 색공간 좌표 보고
- CVD 피험자가 자극을 지각할 수 있었는지 확인 방법

리뷰어 예상 질문:
```
"How did you ensure CVD subjects could perceive the stimuli?"
"Were all CVD subjects of the same subtype, or mixed?"
```

### F. 과대해석 탐지 (Overclaim Detection)

주요 주의 표현:
- "preserved representation" → n=10에서 이런 결론 가능한가?
- "similar neural patterns" → 통계적으로 유의한 유사성인가?
- "color vision deficiency does not affect" → 강한 부정 주장의 근거?
- "compensatory mechanism" → 기제 추론의 근거?

과대해석 레벨:
```
SAFE:     "In our sample of 10 participants..."
CAUTION:  "These results suggest that..."
DANGER:   "CVD individuals show preserved..."
CRITICAL: "Color vision deficiency does not affect neural..."
```

---

## 심각도 레벨

| 레벨 | 설명 | 조치 |
|------|------|------|
| **CRITICAL** | 결론에 영향, 리뷰어 거절 사유 | 즉시 수정 필수 |
| **MAJOR** | 방법론적 약점, 신뢰성 저하 | 수정 권장 |
| **MINOR** | 명확성 부족, 관례 미준수 | 개선 권장 |
| **SUGGESTION** | 선택적 개선 | 참고 |

---

## 동작 순서

1. **대상 문서 읽기**: METHODS_RESULTS_SUMMARY_FOR_PAPER.md (또는 지정 문서)
2. **실제 결과 교차 확인**: `analysis/phase2_SRM_across_between/results/` 등
3. **6차원 평가 수행**: 각 차원별 문제점 식별
4. **심각도 분류**: CRITICAL / MAJOR / MINOR / SUGGESTION
5. **수정안 제시**: 각 문제에 대한 구체적 수정 문구
6. **종합 보고서 생성**: 우선순위 기반 정리

---

## 출력 형식

```markdown
# Proofreading Report — [날짜]

## CRITICAL Issues (즉시 수정)
1. [C-1] **소표본 그룹 비교**: ...
   - 현재: "..."
   - 수정안: "..."

## MAJOR Issues (수정 권장)
1. [M-1] **다중비교 미보정**: ...

## MINOR Issues (개선 권장)
1. [m-1] **fMRIPrep 버전 미명시**: ...

## SUGGESTIONS
1. [S-1] **개별 CVD 시각화 추가**: ...

## Summary
- CRITICAL: N개
- MAJOR: N개
- MINOR: N개
- SUGGESTION: N개
```

---

## 체크리스트

- [ ] 6개 차원 모두 평가됨
- [ ] 심각도 레벨 분류됨
- [ ] 실제 결과와 교차 확인됨
- [ ] n=3 CVD 소표본 이슈 다뤄짐
- [ ] 과대해석 표현 식별됨
- [ ] 각 문제에 구체적 수정안 포함
- [ ] 리뷰어 예상 질문 포함
