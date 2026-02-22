---
name: making-notion
description: 실험 결과를 Notion에 붙여넣기 좋은 구조화된 마크다운으로 생성합니다. "notion", "notion 기록", "making notion", "실험 기록" 요청 시 사용.
recommended-model: sonnet
---

> **Model hint**: Use `model: "sonnet"` when spawning subagents for this skill (analytical task: multi-source data synthesis + structured scientific writing).

# Notion 회의 자료 생성 (making-notion)

## 목적

색각이상(CVD) fMRI 신경 색 표상 분석 결과를 **논문 수준의 구조화된 마크다운**으로 생성하여 Notion 페이지에 바로 붙여넣을 수 있도록 합니다.

---

## 데이터 소스 (우선순위순)

| Source | Path | 용도 |
|--------|------|------|
| **SRM 결과** | `analysis/phase2_SRM_across_between/results/loo_consistent/*/loo_consistent_results.json` | Phase 2 그룹 비교, 개인 검정 |
| **디코더 결과** | `analysis/phase2_decoder_comparing/results/loco/sub-*_loco.json` | LORO/LOCO 성능, 교차 디코딩 |
| **필터 검증** | `analysis/future_phase3_filter_optimization/pre_validation/results/fdr_corrected/*.json` | FDR 보정, 색 쌍 z-score |
| **방법론 요약** | `analysis/METHODS_RESULTS_SUMMARY_FOR_PAPER.md` | 전체 파이프라인, 검증 지표 |
| **프로젝트 현황** | `analysis/future_phase3_filter_optimization/pre_validation/PROJECT_STATUS_*.md` | 전략 변경, Go/No-Go 기준 |
| **README** | `analysis/phase*/README.md` | 각 phase 설명, 파일 구조 |

---

## 출력 구조 (논문 스타일 Notion Template)

아래 구조로 **각 Phase별** 마크다운을 생성:

### 0. Header

```markdown
# {Phase 이름} — {핵심 발견 한줄}

> **프로젝트**: Color Vision Deficiency Neural Representation Analysis
> **날짜**: YYYY-MM-DD
> **대상**: Phase 2/2b/3 분석 결과
> **피험자**: HC 7명, CVD 3명 (sub-08 deutan, sub-09 protan, sub-10 deutan)
> **ROI**: V1, V2, V3, hV4
```

---

### 1. 주요 결과

**필수 포함 요소**:

#### 1a. 결론 (1-2문장)
- "CVD 피험자는 HC 공통 색 표상 공간에서 체계적으로 이탈하며, 그 양상은 개인별·ROI별로 특이적이다."
- 핵심 메시지를 명확히

#### 1b. 근거 주요 지표 (테이블)

**Phase 2 예시**:
```markdown
| ROI | HC Mean (SD) | CVD Mean (SD) | Disparity [95% CI] | p (permutation test) | Hedges' g |
|-----|-------------|--------------|----------------|-------------|-----------|
| **V1** | 0.453 (0.083) | 0.590 (0.156) | 0.137 [−0.005, 0.301] | **0.062** | **1.16** |
| **V2** | 0.486 (0.103) | 0.606 (0.107) | 0.120 [0.001, 0.244] | **0.075** | **1.04** |
```

**중요**:
- 구체적 수치 (소수점 3자리)
- 95% CI 포함
- p-value, effect size 명시
- 유의미한 결과 **볼드** 처리

#### 1c. 시각화 위치

상대 경로 또는 절대 경로로 명시:
```markdown
**시각화**:
- 4-panel SRM 그룹 비교: `phase2_SRM_across_between/results/.../figures/srm_4panel_figure.png`
- LOCO 색 원 도표: `phase2_decoder_comparing/results/loco/color_wheel_plots/`
```

---

### 2. 분석 방법

#### 2a. 방법론 설명 (비유 포함)

**예시**:
```markdown
**SRM (Shared Response Model)**: 서로 다른 뇌를 하나의 "공용어"로 번역하는 방법이다.
7명의 HC 피험자 fMRI 데이터로 색 표상의 공통 좌표계를 학습한 후, CVD 피험자
데이터를 이 좌표계에 투영(SVD)한다. 마치 7명이 합의한 지도 위에 새로운 사람의
위치를 표시하는 것과 같다.
```

**필수**:
- 일반인도 이해 가능한 비유 1개 이상
- 핵심 파라미터 명시 (k값, CV 방법 등)
- 편향 보정 방법 설명

#### 2b. 통계 검정

사용한 검정 방법 명시:
```markdown
**Statistical tests**:
- Permutation test (10,000 iterations, label shuffling)
- Crawford & Howell (1998) single-case test (df=6, one-tailed)
- Bootstrap 95% CI (1,000 iterations)
- Hedges' g (small-sample bias correction)
```

---

### 3. 논의

#### 3a. 검증 지표 (Supplementary Material 스타일)

**Phase 2 예시**:
```markdown
| Validation | V1 | V2 | V3 | hV4 | Interpretation |
|------|----|----|----|----|------|
| LOSO stability | 6/7 significant | **7/7 significant** | 0/7 | 0/7 | V2 perfect |
| Split-half reliability | One-sided significant | **Both significant** | n.s. | n.s. | V2 robust |
| CVD color dependency | n.s. | **p=0.010** | **p=0.000** | **p=0.016** | CVD만 color-specific |
| Crossnobis convergence | r=0.721* | r=0.806** | r=0.200 | r=0.248 | V1/V2 converge |
```

**중요**:
- 모든 검증 지표를 ROI별로 정리
- 일관성 패턴 강조 (V2가 모든 지표에서 강건 등)

#### 3b. 해석 및 함의

**논문 Discussion 스타일**:
```markdown
#### "Scattered but Parallel" 패턴

CVD 피험자는 HC보다 SRM 공간에서 1.4~1.6배 더 분산되어 있으나, V2에서
HC-CVD RDM 상관 [0.414, 0.587]이 HC-HC [0.442, 0.592]와 대폭 중첩된다.
즉, CVD는 **동일한 색 지도**를 갖되 **위치가 어긋난** 것이지, 지도 자체가
깨진 것이 아니다.

**함의**: 이는 CVD를 "신호 손실"이 아닌 "색 공간 왜곡"으로 규정하며,
개인 맞춤형 색 필터 설계의 신경학적 근거를 제공한다.
```

**필수**:
- 데이터가 지지하는 해석만 기술
- 이론적/실무적 함의 명시
- 선행 연구와의 관계 (있는 경우)

#### 3c. 우려 지점 및 보완 계획

**솔직하고 구체적으로**:
```markdown
#### 우려 지점

1. **n=3 검정력 한계**: CVD 3명으로는 그룹 수준 p<0.05 도달이 구조적으로 어려움.
   대효과(g>1.0)에도 불구하고 trending에 그침.

   **보완**: 개인 단일사례 분석(Crawford & Howell)으로 전환 → "2/3이 유의"
   사례 기반 보고

2. **SRM 정렬 아티팩트 가능성**: SRM 공간에서만 효과가 검출될 수 있음.

   **보완**: Crossnobis (네이티브 복셀), PCA-CCA (다른 정렬) 삼각검증 완료
   (V1/V2에서 r=0.72~0.89 수렴 확인)
```

**필수**:
- 각 우려에 대한 구체적 보완 계획
- 완료된 보완은 결과와 함께 명시
- Go/No-Go 기준 (있는 경우)

---

## 출력 파일

**경로**: `analysis/meeting_materials/YYYY-MM-DD_{phase_name}_meeting_notes.md`

**예시**:
- `2026-02-19_phase2_srm_meeting_notes.md`
- `2026-02-19_phase3_filter_meeting_notes.md`

**특징**:
- git 추적됨 (문서 목적)
- Notion 복사-붙여넣기 가능한 clean markdown
- 이모지 사용 금지 (Notion 자체 아이콘 사용)
- 상대 경로 링크 사용 (Notion에서 자동 변환)
- **한영 혼용 규칙**: 통계 용어, 방법론 용어, 기술 표현은 반드시 **영어**로 작성. 일반 설명/서술은 한국어 유지. 예시:
  - ✅ "V1/V2에서 large effect size (g>1.0)" / "split-half reliability" / "permutation test"
  - ❌ "대효과" / "반분 신뢰도" / "순열검정"
  - ✅ "SRM alignment artifact" / "convergent validity" / "statistical power"
  - ❌ "정렬 아티팩트" / "수렴 타당도" / "검정력"
  - 테이블 헤더도 영어: Disparity, Hedges' g, Interpretation, Direction 등

---

## 동작 순서

1. **Phase 확인**: 사용자 지정 또는 최신 분석 자동 감지 (phase2/2b/3)
2. **결과 파일 수집**:
   - SRM: `loo_consistent_results.json` 읽기
   - 디코더: `sub-*_loco.json` 읽기 (10명 × 4 ROI)
   - 필터: FDR 보정 결과 읽기
3. **방법론 참조**: `METHODS_RESULTS_SUMMARY_FOR_PAPER.md`에서 검증 지표 추출
4. **섹션별 생성**:
   - 주요 결과: JSON에서 수치 추출 → 테이블 생성
   - 분석 방법: README 기반 + 비유 추가
   - 논의: 검증 지표 정리 + 해석 + 우려 지점
5. **파일 저장**: `analysis/meeting_materials/YYYY-MM-DD_{phase}_meeting_notes.md`

---

## 체크리스트

- [ ] **주요 결과**: 결론 1-2문장 + 근거 테이블 (구체적 수치) + 시각화 위치
- [ ] **분석 방법**: 비유 포함 설명 + 통계 검정 명시
- [ ] **논의**: 검증 지표 테이블 + 해석 + 우려 지점 및 보완 계획
- [ ] **논문 수준**: 분석 목적, 가설, 결과, 결론, 함의 명확히 서술
- [ ] **Supplementary 스타일**: 모든 validation metrics를 ROI별 테이블로 정리
- [ ] **수치 정확성**: JSON 파일에서 직접 추출한 정확한 수치 사용
- [ ] **Notion 호환**: clean markdown, 이모지 없음, 상대 경로 링크
