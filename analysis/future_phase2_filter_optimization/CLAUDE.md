# future_phase2_filter_optimization — CLAUDE.md : CURRENT FOCUS

**Stage B + C** · **Status**: ACTIVE.

## Objective

(B) CVD simulator를 피팅하고 (C) 역문제(pre-image)를 풀어 **stimulus-space 색 보정 필터**를 유도한다. 목표는 CVD가 HC-like primary percept를 얻도록 입력 자극을 이동시키는 개인별 δ(θ) 함수이다.

## Direction

- 세 모델을 서로 다른 mechanistic level(retinal cone / cortical opponent / stimulus-space dilation)로 병치하며, **각 CVD 개인에 대해 가장 잘 맞는 모델의 필터**를 채택한다. 임의로 모델을 추가/제거하지 않는다.
- 피팅 기준은 **LOCO vulnerability 일치**가 primary. ΔRDM은 부차 (공유 정보 weighting).
- Post-cortical mapping은 HC = CVD 동일 — simulator는 "HC primary percept → CVD primary percept" 만 모사한다.
- **HC specificity** (LOO-HC false positive, baseline_ρ 교란)는 현재 미해결 이슈이며, 해결 전에는 specificity claim을 하지 않는다.

## Results location

- 모델·피팅·pre-image 전체 서술: `notion.md`.
- 필터 디자인 계획/결과: `LOCO_FILTER_PLAN.md`, `LOCO_FILTER_RESULTS.md`.
- 3모델 비교: `COMPREHENSIVE_MODEL_RESULTS.md`.
- W-fixed 파이프라인: `PIPELINE_WFIXED.md`.
- 행동 연결: `behav_validation.md`.
- 스크립트/산출물: `scripts/`, `results/`.

## Rule of action

1. 작업 시작 전 `notion.md`와 `LOCO_FILTER_PLAN.md`를 먼저 확인하고, 이전 세션에서 확정된 결정을 재토론하지 않는다.
2. 세 모델(Machado 1-way / R+C / 2-Component)을 임의로 제거·추가하지 않는다. 수정은 **사용자 승인** 후.
3. SRM·ΔRDM을 피팅의 primary criterion으로 올리지 않는다 (metric ≠ functional).
4. C_baseline은 `machado_shifted_hue(0.0, family)` 기반으로만 계산 (CIELab nominal 각도 사용 금지).
5. Pre-image는 forward model의 수치적 역함수로 계산. 근사 실패 시 subject-model 조합을 **기각**하는 것이 옳다.
6. Specificity 관련 claim(CVD-only, HC에서 null)은 현재 파이프라인에서 보류. 결과·논문 인용 시 HC specificity 미해결을 함께 기술.
7. Sub-10은 현재 고려하지 않음 - CVD이나 HC와의 유의미한 차이를 포착하지 못함 & 이후 분석에서 제외함. 
8. SLURM: hV4 전체 fit은 CPU-heavy → node2 `%5~10`, `--mem=16G` 권장.
9. 결과 저장 규칙: flat `results/<analysis_name>/` (timestamp 서브디렉토리 금지), per-subject json, batch당 `config.json` 1개.
