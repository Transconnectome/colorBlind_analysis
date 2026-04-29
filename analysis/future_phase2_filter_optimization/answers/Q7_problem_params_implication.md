# §6-5 문제적 파라미터와 모델 선택 논리의 균열 분석

**작성일**: 2026-04-29  
**분량**: 약 420단어  
**대상**: future_phase2_notion.md §6-5, §7, §9 및 CLAUDE.md rule 7 검토

---

## 1. 문서의 2-Component 채택 정당화 사슬

future_phase2_notion.md §7은 명시적으로 "2-Component는 두 CVD 피험자 모두에서 LOCO+ΔRDM dual-validated"라고 선언한다. 이 채택의 정당화 체인은:

1. **§5-2 hV4 LOCO**: sub-08은 p=0.004**(최강), sub-09는 p=0.035*(유의)
2. **§5-6 Pre-image bijectivity**: 2-component만이 양쪽 모두 8/8 exact pre-image 달성
3. **§6-3 S-cone축 생리학적 근거**: Emery et al. 2021의 21.4° B-Y rotation과 β_s=20-23°의 일치 (0.1-3°)
4. **§6-5 R+C g 비현실**: sub-08 V1 g=-2.25(125% 과보상)는 Tregillus 문헌(20-40%)을 초과
5. **§9 제한점**: HC specificity FPR=100% 인정하되, 행동 검증으로 해결 유보

**문제**: 이 사슬은 circular reasoning을 포함한다. §6-5의 첫 두 행(R+C g 비현실)은 "R+C를 버려야 한다"는 신호이지, "따라서 2-component를 채택하라"는 필연적 결론이 아니다.

---

## 2. §6-5 sub-10 V1 2-Comp FP의 위상

§6-5 세 번째 행은 치명적이다:
- **Sub-10 V1 2-Comp p=0.004**: 정상 대조군에서도 2-component가 유의하게 적합된다.

LOCO_FILTER_RESULTS.md §2.3에 따르면 sub-10 V1 LOCO는 **p=0.058**(경계선)이며, β_s=0°이되 β_c=36°(순수 confusion axis shift)로 ρ=0.619를 달성한다. 이는:

- 2-DOF 모델 × 8색 = 1,326개 그리드 점에서 rank order matching 과다유연성
- baseline ρ과의 비교 부재 → 우연일 가능성

**CLAUDE.md rule 7**("sub-10은 현재 고려하지 않음")이 면죄부 역할을 한다. 그러나 sub-10 FP는 2-component의 **specificity 신뢰도를 약화**시킨다.

---

## 3. HC specificity FPR=100% (2-Component)의 일관성

HC specificity 관련 분석에 따르면 2-component의 LOO-HC FPR은 100%(Machado 43%, R+C 71%와 대비). 이는 §6-5 sub-10 p=0.004와 일관된 신호다:

- **신호의 의미**: 2-component의 2 DOF는 HC 개인 간 변이(hV4 baseline ρ: [-0.36, +0.69])를 CVD 신호로 착각할 가능성이 높다.
- **§9 제한점에서 처리**: "HC specificity 미해결"로 기술되고, "필터는 행동 검증으로 판별"이라고 유보.

**충분성 평가**: 불충분하다. HC specificity 미해결은 단순 제한점이 아니라 **모델 선택 근거의 structural flaw**이다. LOCO+ΔRDM dual-validation이 CVD-specific이 아니면 그 claim이 무효화된다.

---

## 4. R+C g 비현실이 R+C 기각의 근거인가?

§6-5는 sub-08 V1 g=-2.25를 "비현실적"으로 낙인한다. 그러나:

- **hV4에서는** g=+2.25(amplification, 별 선례)이지만 LOCO ρ=0.857, p=0.005.
- LOCO_FILTER_RESULTS.md §3.3 "Severity-Dependent Filter Feasibility": 2-component는 sub-09에서 "stimulus-space sufficient"이지만, forward model accuracy(LOCO ρ=0.690)는 Machado(ρ=0.762)보다 낮다.

**해석**: g의 극단값은 fitting **자유도** 또는 **misspecification**의 신호일 수 있다. R+C의 단일축 rescaling(RG axis만)이 deutan의 150° confusion axis를 온전히 포착하지 못하고, 있는 자유도로 과적합할 수 있다. 이는 R+C 모델 구조의 한계이지, 2-component 채택의 근거가 아니라 **두 모델의 메커니즘 차이**만을 보여준다.

---

## 5. 사용자 질문에 대한 직설적 답변

**"§6-5의 첫 두 행(R+C g 비현실)은 2-Component를 사용하라는 신호인가?"**

**답변: 부분적이다. 그러나 확실한 신호가 아니다.**

**이유**:
1. **R+C 기각의 근거는 부분적**: Δλ(cone shift) 자체는 문헌 범위 내(sub-08 2nm, sub-09 13.5nm). 다만 g 파라미터의 극단값이 overfitting을 암시.
2. **2-Component 채택의 강점**: 유일하게 양쪽 CVD에서 8/8 exact pre-image 달성(§5-6). 이는 **필터 실현가능성**의 차원에서 결정적.
3. **그러나 structural flaw**: HC specificity FPR=100%(§6-5 sub-10)는 CVD-specific claim이 불안정함을 의미. 모델 선택이 "CVD 기전 이해"가 아니라 "우연한 과적합 회피"일 가능성.

**결론 섹션**:

2-Component 채택은 **제약적 타당성**(constrained validity)을 가진다. §6-5의 R+C 비현실성과 sub-10 FP 패턴이 2-component를 강력히 지지하지는 않지만, §5-6의 pre-image 존재성이 **실제 필터 디자인**의 차원에서는 2-component가 유일한 실행 가능한 선택임을 보여준다. 단, 이는 기계적 가능성이지 생리학적 정확성은 아니다. HC specificity 미해결 + sub-10 FP + CLAUDE.md rule 7의 결합은 **"현재로선 2-component가 낫다"는 pragmatic decision이지, 확정적 선택이 아님**을 의미한다. 행동 검증(Phase 3)이 최종 중재자.

