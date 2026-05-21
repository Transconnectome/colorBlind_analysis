# PI Feedback Gap Check (2026-05-19)

## 1. 4가지 작업으로 커버되는 항목 (체크)

- [x] **PI #1 Model & Loss Selection validation** — 사용자 작업 #3 (Model & Loss 정당화 markdown)
- [x] **PI #2 Loss Selection validation (end-to-end LOO)** — 사용자 작업 #3
- [x] **PI #3 Fitting 방법 구체화 (RDM 등 scalar 도출)** — 사용자 작업 #1 (파이프라인 정리 markdown)
- [x] **PI #4 Run 수 결정 (6 vs 4 run validation)** — 사용자 작업 #3 (Run 수 결정 markdown)
- [x] **문헌 비교 (기존 모델이 behav 어떻게 썼는지)** — 사용자 작업 #2 (NotebookLM)
- [x] **메타-분석 (기존 문헌과의 systematic 비교)** — 사용자 작업 #4

## 2. 4가지에 명시적으로 포함되지 않은 항목

- **Behavior-only simulation 자체 수행**: PI는 "행동 데이터만으로도 시뮬레이션 해보고 그 결과와 neural 모델 비교"를 요구. 메타-분석(문헌 수치)이 아니라 **우리 데이터로 behav-only ablation 실행**.
- **Neural ablation 비교 실험**: "행동 < 행동+신경" 입증을 위한 ablation 분석 (LOO generalize 비교 포함).
- **PI #5 Writing 과정의 반복 피드백 루프**: 단순 초안이 아니라 "계획-작성-피드백-정당성 검토 반복" + "간접·일부 관련 문헌까지 모델에 투입" 절차.
- **Biological structure (retina/cortical 분리) 정당화 축소 결정**: "굳이?" 발언 — 2-component 프레이밍 down-weight 여부를 명시적으로 결정 필요 (Model Comparison 프레이밍으로 전환).

## 3. 권장 처리

- **Behavior-only simulation**: 즉시 처리 — 새 sub-task (`behav_only_ablation/`) 신설, JND/Ishihara 데이터로 filter 학습 후 neural-augmented 결과와 직접 비교.
- **Neural ablation**: 즉시 처리 — 위 behav-only와 짝지어 동일 LOO 프레임으로 실행 (작업 #3 Model/Loss validation 안에 sub-section 추가도 가능).
- **Writing 반복 루프**: 별도 에이전트 — `/revise-draft` + `/apply-draft` 체인으로 운용, 작업 #1-3 산출물 완성 후 가동.
- **Biological structure 프레이밍**: PI와 추가 논의 — 2-component를 paper에서 "physiological grounding"으로 둘지 "model comparison candidate"로 강등할지 결정 필요 (수치 결과에 영향 없음, 서술 톤만 변경).
