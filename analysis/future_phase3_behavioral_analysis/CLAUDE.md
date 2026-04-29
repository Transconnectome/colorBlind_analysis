# future_phase3_behavioral_analysis — CLAUDE.md

**Stage D** · **Status**: Planning / preparation.

## Objective

future_phase2에서 유도한 개인별 필터를 CVD 피험자에게 적용하고, 착용 전/후의 **behavioral (JND)** 및 **fMRI (SRM, LOCO)** 지표가 HC 분포 방향으로 이동하는지 평가한다.

## Direction

- **Functional 지표(LOCO)가 behavior를 예측한다**는 기존 관찰을 프레임으로 유지한다. Metric 지표(SRM z)는 보조적 참고로만 쓴다.
- 필터 specificity(HC에서 null)가 future_phase2에서 보장된 뒤 본실험을 시작한다.
- 실험 프로토콜(자극 calibration, L\*=75 clamp 등)은 future_phase2의 filter_visualization과 수치적으로 정합되어야 한다.
- 대조: (a) 필터 미착용 baseline, (b) 개인별 필터, (c) 필요 시 대안 모델 필터.

## Results location

- 행동·fMRI 재측정 결과, 교차검증 로그: 이 폴더의 `results/`, `docs/`.
- 사전 분석 서술: `notion.md`.

## Rule of action

1. 필터가 specificity 요구를 충족하기 전에는 본실험 설계·집행을 진행하지 않는다 (future_phase2 진행 상태 먼저 확인).
2. "LOCO → JND" 연결은 기존 관찰을 근거로 유지. "SRM z → JND"를 예측적 주장으로 격상하지 않는다.
3. Plateau 가설(FE basis smoothness 관련)은 기각된 상태 — 되돌리지 않는다.
4. 결과 저장 규칙: flat `results/<name>/`, per-subject json, batch당 `config.json` 1개.
