# Sequential development plan: notebook-driven (nilearn_test.ipynb)

작성일: 2025-10-27

목표
- `nilearn_test.ipynb`을 메인 분석 파이프라인으로 발전시켜, voxel-wise / whole-brain 기반의 재현 가능한 연구용 분석 흐름을 구축한다. B&H(2009) ROI 파이프라인은 보존하되, 노트북 중심의 실험 개발을 우선시한다.

핵심 원칙
- 노트북은 단일 버튼으로(혹은 한 셀로) 전체 파이프라인을 실행할 수 있어야 한다.
- 모든 실험 설정은 명시적 변수(변수 셀)에 배치하여 재현 가능하게 한다.
- 결과(혼동행렬, 요약 JSON, 플롯)는 `derivatives/sub-01/experiments/<run-id>/`에 저장한다.

단계(우선순위)

1) 백업 및 안전조치 (완료)
   - 원본 노트북을 `backup/nilearn_test.backup.<date>.ipynb`로 저장

2) 노트북 정리 — Baseline 파이프라인 구현 (필수)
   - 셀: 환경 확인, 데이터 로드, 전처리(상수 피처 제거), per-fold StandardScaler
   - 모델: multinomial LogisticRegression, leave-one-run-out CV
   - 저장: `derivatives/sub-01/experiments/nilearn_baseline_<timestamp>/`
   - 검증: 실행 종료 시 요약 JSON, 혼동행렬 PNG 생성

3) 전처리·특성 선택 모듈화
   - per-fold 옵션: top-k (500, 2000), PCA (50,100,300), z-scoring on/off
   - 자동화된 실험 루프(각 조합을 실행하고 결과를 요약)

4) 분류기 그리드
   - LogisticRegression (C grid), LinearSVC, LDA, 소형 RandomForest
   - 각 실험에 대해 train/test accuracy, confusion matrix, runtime 저장

5) 통계 검증
   - permutation test (초기: 200 perms; 후보에 대해 1000 perms)
   - p-value 및 신뢰구간 저장

6) 보고와 재현성
   - `generate_reports.py`를 사용해 QC 플롯과 bilingual report 생성
   - `requirements.txt` 또는 `environment.yml` 추가

7) 확장(선택)
   - 가벼운 딥러닝 프로토타입(notebook): MLP/autoencoder로 색상 복원 또는 분류

실험 폴더 구조 제안
- derivatives/sub-01/experiments/
  - nilearn_baseline_YYYYMMDD_HHMMSS/
    - results.json
    - confusion_matrices.png
    - config.json
    - runtime.log

짧은 체크리스트(첫 실행 전)
- Python env 확인(권장: `nilearn` conda env).
- `derivatives/sub-01/`에 이미 per-run betas 및 ROI 마스크가 있는지 확인.
- 충분한 디스크 여유 및 메모리 확보 (WholeBrain 실행 시 필요).

다음 단계로 제가 할 일 (원하시면 바로 진행합니다)
- A: `nilearn_test.ipynb`에 baseline 실행 셀을 추가하고 한 번 실행해 결과 저장 (권장).  
- B: 먼저 간단한 baseline 스크립트를 `tools/`로 만들어 노트북을 변경하지 않고 실행해 보기.  
- C: 위 작업 후 preproc/feature-selection sweep를 실행해 결과를 수집.
