# phase3_decoder_comparing — CLAUDE.md

**Stage A** · **Status**: Complete.

## Objective

디코더 모델(LDA/SVM/Ridge/KernelRidge/ForwardEncoding/MLP + hybrids)을 LORO(분류)·LOCO(보간) 두 과제에서 비교하여, 하위 phase가 쓸 **task-dependent optimal pipeline**을 선정한다.

## Direction

- LORO(분류) vs LOCO(보간)은 요구 특성이 다르다 — 정렬(SRM vs Procrustes)·모델 조합이 과제별로 달라진다는 전제에서 비교.
- 하위 phase(future_phase1/2)가 **신규 디코더를 제안하지 않고** 이 폴더의 선정 결과를 재사용하도록 한다.
- LOCO 디코더는 correlation-based template matching을 기본으로 한다 (대안들은 df 부족으로 열세 확인됨).

## Results location

- Task별 optimal 선정, bootstrap CI, cross-decoding 결과: 이 폴더의 `README.md` 및 `results/`.
- FE 6-channel W 결과는 `future_phase1_forward_model`, `future_phase2_filter_optimization`의 입력.

## Rule of action

1. 새 디코더 제안 금지 — 기존 탐색에서 이미 결론 도출됨. 추가가 필요하면 **사용자 승인 필수**.
2. LOCO에서 correlation template matching 대신 다른 방법을 쓰지 않는다.
3. Pooled W(6 runs × 7 colors)를 LOCO·LORO 모두의 base로 유지.
4. Nested CV(inner LORO 5-fold)와 lambda 그리드(16 values, 0.0~1.0)를 유지.
5. 결과 저장 규칙: flat `results/<name>/` + `config.json` 1개.
