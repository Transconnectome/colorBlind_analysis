# ColorBlind fMRI Analysis Pipeline

B&H (2009) 색상 디코딩 분석 파이프라인의 Python 구현입니다.

## 구조

```
colorBlind/
├── config.py              # 설정 및 경로
├── bh_anal.py            # 핵심 분석 파이프라인
├── utils/
│   ├── __init__.py
│   └── cache.py         # 캐싱 시스템
├── notebooks/
│   └── bh_viz.ipynb    # 시각화 노트북
└── tests/
    └── test_bh_anal.py # 단위 테스트
```

## 설치

필요한 패키지:
```bash
pip install -r requirements.txt
```

## 사용법

### 1. 설정

`config.py`에서 경로와 파라미터를 설정합니다:

```python
from config import cfg
cfg.SUB_ID = '01'  # 분석할 피험자 ID
```

### 2. 분석 실행

```python
from bh_anal import BHAnalysisPipeline

# 파이프라인 초기화
pipeline = BHAnalysisPipeline()

# 전체 파이프라인 실행
pipeline.run_pipeline()

# 또는 특정 단계부터 실행
pipeline.run_pipeline(start_from='fir_glm')
```

### 3. 결과 시각화

Jupyter 노트북 `notebooks/bh_viz.ipynb`을 실행하여 결과를 시각화합니다.

## 테스트

```bash
pytest tests/
```

## 참고문헌

Brouwer, G. J., & Heeger, D. J. (2009). Decoding and reconstructing color from responses in human visual cortex. Journal of Neuroscience, 29(44), 13992-14003.