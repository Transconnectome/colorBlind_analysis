# Future Phase 2 — 답변 대기 질의 목록 (todo_list)

> 생성: 2026-04-29 · 출처: 사용자가 `future_phase2_notion.md` 검토 후 제기
>
> 각 항목은 코드/JSON 추적이 필요하므로 서브에이전트 분리 처리. 본 문서는 질의 내용 + 참조 파일 + 답변 연결만 기록한다.

---

## Q1. Detection 표(§5-1)는 HC 평균 결과인가?

- 위치: `future_phase2_notion.md` §5-1 (Machado/R+C/2-Component/Fourier × sub-08/09/10 p-value 표)
- 의문: "모든 모델이 수렴"으로 보이는 p-value들이 (a) HC 7명에 대한 평균 적합인지, (b) 단일 CVD 피험자별 적합인지, (c) HC 평균 RDM/vuln을 reference로 한 CVD 적합인지 명확화 필요.
- 답변: `answers/Q1_detection_design.md`

## Q2. Bootstrap 분포로 ρ(또는 핵심 파라미터)의 분포 제시 가능?

- 의문: 현재 표는 point estimate + permutation p만. ρ에 대한 bootstrap 95% CI를 추가할 수 있는가?
- 점검 대상: `comprehensive_2component_analysis.py`(이미 bootstrap 사용?), `loco_distortion_fit.py`, `step2c_retinal_cortical.py`
- 답변: `answers/Q2_bootstrap_rho.md`

## Q3. Permutation test는 어떻게 수행되었나?

- 의문: §4 표에 "Permutation: 8! exact (40,320)"이라 적혀 있으나, 어떤 라벨을 셔플하고 어떤 통계량을 비교하는지 코드 수준 정의 필요.
- 점검 대상: `loco_distortion_fit.py`, `comprehensive_2component_analysis.py`, `hc_specificity_test.py`
- 답변: `answers/Q3_permutation_design.md`

## Q4. §5-4 L_LOCO 구성 요소 분해 — L=loss? ΔL의 통계적 의미? simulation_recoverability_behavior.md와의 연결 발전 방향

- 의문 1: L_vuln/L_rank/L_rdm/L_smooth의 L이 loss인가, log-likelihood인가?
- 의문 2: 표에 적힌 ΔL_rank(−0.262 등)가 통계적으로 유의한지 (per-subject permutation, bootstrap이 가능한가).
- 의문 3: `simulation_recoverability_behavior.md`의 sub-08 행동 보고와 ΔL 분해를 어떻게 연결해 발전시킬 수 있나 (예: 색별 ΔL 기여도 ↔ 행동 collapse).
- 점검 대상: `loco_distortion_fit.py`(L_fit 정의), `results/loco_decomposition/`
- 답변: `answers/Q4_loss_decomposition.md`

## Q5. Pre-image의 "vector cosine = −0.18" 산출 방법

- 위치: §5-6 표 마지막 줄 ("벡터 cosine: −0.18 (반상관)")
- 의문: 8색 δθ 벡터 간 cosine similarity인지, 어떤 두 벡터인지, 산출 스크립트 위치.
- 점검 대상: `preimage_filter_search.py`, `evaluate_preimage_filter.py`, `results/loco_filter/preimage*/`
- 답변: `answers/Q5_preimage_cosine.md`

## Q6. β_s ↔ Emery 21.4° 수학적 비교 가능성

- 위치: §6-3, §9 (제한점)
- 현 입장: notion.md는 "수치 비교 무의미"로 결론. 그러나 `simulation_recoverability_behavior.md` Abstract는 "21.5° ≈ 21.4°"로 직접 비교를 시사 → 두 문서 간 모순.
- 의문: 두 양(β_s = angular dilation amplitude vs Emery B-Y phase shift)을 수학적으로 변환할 수 있는 조건/가정이 있는지, 또는 명시적으로 분리해야 하는지 정리.
- 답변: `answers/Q6_betas_emery_math.md`

## Q7. §6-5 "문제적 파라미터"는 2-Component 채택 권고를 시사하는가?

- 위치: §6-5 (sub-08 g=±2.25 문헌 초과, sub-10 V1 2-Comp p=0.004 FP)
- 의문: g 비현실성 → R+C 기각 → 2-Component 채택 논리가 닫혀 있는가? 그러나 §6-5에 sub-10 V1 2-Comp 자체도 FP로 적시됨 → 모델 선택 논리에 균열.
- 답변: `answers/Q7_problem_params_implication.md`

---

## 답변 인덱스

- [Q1: Detection 설계](answers/Q1_detection_design.md)
- [Q2: Bootstrap ρ 분포](answers/Q2_bootstrap_rho.md)
- [Q3: Permutation 설계](answers/Q3_permutation_design.md)
- [Q4: Loss decomposition](answers/Q4_loss_decomposition.md)
- [Q5: Pre-image vector cosine](answers/Q5_preimage_cosine.md)
- [Q6: β_s vs Emery 수학](answers/Q6_betas_emery_math.md)
- [Q7: 문제 파라미터의 함의](answers/Q7_problem_params_implication.md)
