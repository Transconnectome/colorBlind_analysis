# phase2_procrustes_cvd_hc — CLAUDE.md

**Stage A** · **Status**: Complete.

## Objective

Procrustes 기반으로 CVD-HC 차이의 **3차원 이질성** — Magnitude / Sign-Baseline / Structure(RDM) — 을 특성화. 개인화 필터의 필요성 근거를 제공한다 (RQ2, SRQ1).

## Direction

- 같은 CVD 유전자형이라도 신경 표현형이 다를 수 있다는 전제에서 기술적(descriptive) 특성화에 집중.
- 공통 HC decoder가 정렬 후 CVD에 적용 가능한지 검증 (필터 전제 조건).
- 모델링·필터 피팅 자체는 여기서 하지 않는다 (future_phase2 담당).

## Results location

- 수치·표·개별 프로파일: 이 폴더의 `README.md` 및 `results/`.
- 하위 phase가 인용할 핵심 서사는 "개인화 필수"와 "공통 decoder 공유 가능".

## Rule of action

1. 이 phase의 결론(RQ2/SRQ1)을 재검증하는 분석은 **사용자 승인 후에만** 시작.
2. 결과는 future_phase2의 "왜 개인화?" 근거로 **인용**만 하고 수치를 바꾸지 않는다.
3. Sub-10은 경도(normal control 가까움) — 필터 특이도 검증의 귀무기준으로 취급.
4. 결과 저장 규칙: flat `results/<name>/` + `config.json` 1개.
