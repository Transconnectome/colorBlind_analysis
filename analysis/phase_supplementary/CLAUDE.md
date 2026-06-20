# phase_supplementary — CLAUDE.md

**Stage**: Supplementary (paper backing) · **Status**: S1 complete.

## Objective

논문이 인용하지만 다른 phase 폴더에 흩어져 찾기 어려운 **supporting 분석**을 한 곳에
정리한다. 신규 데이터 처리 없음 — frozen result JSON을 읽어 paper-ready 표/그림만 생성.

## Contents

- **S1 — Overall signal preserved**: abstract의 *"not reduced in overall signal"*
  주장의 univariate 근거. 출처는 `phase2_SRM_across_between/activation_prior_analysis.py`
  (2026-03-27). 이 폴더는 결과를 **재계산하지 않고** consolidate + 시각화만 한다.
  수치는 source JSON과 byte-identical. README.md 참조.

## Rule of action

1. **재계산 금지**: source 분석의 frozen JSON을 읽기만 한다. 숫자를 바꾸지 않는다.
   원 분석을 수정해야 하면 `phase2_SRM_across_between/`에서 하고 JSON을 다시 복사한다.
2. 새 supplementary 분석 추가 시 `S{n}_*` 네이밍 + README.md에 섹션 추가.
3. 결과 저장: flat `results/`, 그림은 `figures/`, png+pdf 동시 출력.
4. seaborn 금지 (matplotlib only).
5. 이 폴더는 LOCO accuracy(exp2) 작업과 무관 — 그건
   `future_phase3_behavioral_analysis/exp2_neural/`.
