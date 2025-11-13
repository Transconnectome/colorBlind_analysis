# Color Reconstruction Reproduction Pipeline

이 디렉토리는 문서화된 색상 재구성 결과를 재현하기 위한 독립적인 파이프라인을 포함합니다.

## 목표 (Target Results)

이 파이프라인은 다음의 검증된 결과를 재현하도록 설계되었습니다:

| ROI  | Voxels | Optimal Delay | Classification | Training Error | Novel Error |
|------|--------|---------------|----------------|----------------|-------------|
| **V2** | 310    | 5 TRs (7.5s)  | 100%           | 4.1°           | **52.4°**   |
| V1   | 344    | 4 TRs (6.0s)  | 100%           | 6.2°           | 64.1°       |
| hV4  | 55     | 6 TRs (9.0s)  | 100%           | 5.0°           | 75.0°       |

**V2가 최고의 결과를 보였습니다** (52.4° novel error, chance는 90°).

## 핵심 방법론 (Quick Fix Method)

성공적인 결과는 다음의 "Quick Fix" 방법을 통해 달성되었습니다:

1. **Universal HRF 추정**: 모든 voxel에서 FIR 응답을 평균화
2. **최적 딜레이 선택**: **절대값** 사용 (중요한 버그 픽스!)
3. **단일 딜레이에서 베타 추출**: 각 voxel의 고유한 진폭 유지
4. **Diagonal LDA 분류**: B&H 2009 방법
5. **B&H 순방향 모델 재구성**: 6개의 이상화된 색상 채널

## 중요한 버그 픽스 (CRITICAL BUG FIXES)

재현을 위해 **반드시** 보존해야 할 버그 픽스들:

### 1. 최적 딜레이 선택 (가장 중요!)

```python
# ❌ 잘못된 방법:
optimal_delay = np.argmax(universal_hrf)

# ✅ 올바른 방법:
optimal_delay = np.argmax(np.abs(universal_hrf))
```

**왜 중요한가?**
- HRF 값이 모두 음수일 수 있음
- 절대값을 사용하면 부호에 관계없이 최대 크기를 찾음
- 이 수정으로 V2 novel error가 77.8° → 52.4°로 개선됨 (35% 향상!)

### 2. 재구성 역행렬

```python
# ❌ 잘못된 방법:
C_test_est = np.linalg.inv(W.T @ W) @ W.T @ X_test_final.T

# ✅ 올바른 방법:
C_test_est = np.linalg.pinv(W.T @ W) @ W.T @ X_test_final.T
```

**왜 중요한가?**
- 7개 훈련 색상 + 6개 기저 함수 → W.T @ W가 full rank가 아닐 수 있음
- Pseudoinverse가 이를 처리함

## 파일 구조

```
reproduction_pipeline/
├── README.md                           # 이 파일
├── config_reproduction.py              # 정확한 설정 매개변수
├── build_rois_reproduction.py          # ROI 마스크 생성
├── validate_and_fix_rois.py            # ROI 검증 및 zero-voxel 제거 (중요!)
├── run_reconstruction_reproduction.py  # 메인 분석 파이프라인
├── run_reproduction.sbatch             # SLURM 배치 스크립트
└── verify_setup.py                     # 설정 검증
```

## 사용법 (Usage)

### 단계 1: ROI 마스크 생성 (정렬 및 EPI 마스크 교차 포함)

```bash
cd reproduction_pipeline
python build_rois_reproduction.py
```

**이 단계가 하는 일:**
1. Wang atlas에서 ROI 부분 결합 (V1v+V1d 등)
2. 50% 확률 임계값 적용
3. **기능 MNI 공간으로 리샘플** (res-2: 97×115×97)
4. **EPI 마스크와 교차** (`compute_epi_mask()` 사용) ⭐ **중요!**

**기대 출력:**
```
Computing EPI mask from functional data...
  EPI mask: 235,847 voxels

Building ROI masks...
  Building V1...
    Before EPI mask: 366 voxels
    After EPI mask: 344 voxels
    Removed: 22 voxels outside brain (6.0%)
    ✓ Saved to: derivatives/sub-01/roi/sub-01_V1_mask.nii.gz

  Building V2...
    Before EPI mask: 322 voxels
    After EPI mask: 310 voxels
    Removed: 12 voxels outside brain (3.7%)
    ✓ Saved to: derivatives/sub-01/roi/sub-01_V2_mask.nii.gz
```

**왜 중요한가?**
- Wang atlas가 기능 커버리지를 벗어난 voxel을 포함할 수 있음
- EPI mask가 실제 BOLD 신호가 있는 뇌 영역을 정의
- 이 교차가 atlas를 anat 및 functional 데이터와 정렬!

**검증:**
- Voxel 수가 기대값과 ±5% 이내여야 함 (310, 344, 55)
- 큰 차이가 있으면 결과가 달라질 수 있음

### 단계 2: ROI 검증 (선택사항, 권장)

```bash
python validate_and_fix_rois.py
```

**이 단계가 하는 일:**
- ROI-functional 정렬 검증
- 공간 오버랩 확인
- 추가 zero-signal voxel 제거 (있다면)

**단계 1과의 차이:**
- **단계 1 (EPI 마스크)**: `compute_epi_mask()` - nilearn의 정교한 뇌 추출
- **단계 2 (검증)**: `mean_func > 0` - 추가 zero-signal 확인

**언제 사용:**
- 단계 1에서 생성된 ROI가 예상과 다를 때
- 추가 품질 검증이 필요할 때
- ROI voxel 수가 기대값과 크게 다를 때

**기대 출력:**
```
ROI         Original     Active       Removed      Overlap %
----------------------------------------------------------------------
V1          344          344          0            100.0
V2          310          310          0            100.0
hV4         55           55           0            100.0
```

**이상적 결과:**
- EPI 마스크 교차가 제대로 작동했다면 추가 제거 없음 (0개)
- 만약 추가 voxel이 제거된다면: `_fixed_mask.nii.gz` 사용

### 단계 3: 색상 재구성 실행

```bash
# V2 (최고 성능)
python run_reconstruction_reproduction.py --roi V2

# V1
python run_reconstruction_reproduction.py --roi V1

# hV4
python run_reconstruction_reproduction.py --roi hV4
```

### 단계 3: 결과 검증

스크립트는 자동으로 결과를 기대값과 비교합니다:

```
COMPARISON WITH DOCUMENTED RESULTS:
  Voxels: 310 vs 310 (expected)
  Delay: 5 vs 5 TRs (expected)
  Classification: 100.0% vs 100.0% (expected)
  Training: 4.1° vs 4.1° (expected)
  Novel: 52.4° vs 52.4° (expected)

✓✓✓ EXCELLENT MATCH - Results successfully reproduced!
```

**매치 기준:**
- ✓✓✓ EXCELLENT: Novel error 차이 < 2°
- ✓✓ GOOD: Novel error 차이 < 5°
- ⚠ PARTIAL: Novel error 차이 ≥ 5° → 조사 필요

## 출력 파일

각 ROI에 대해 다음이 생성됩니다:

```
derivatives/sub-01/fir_reconstruction_reproduction/{ROI}_universal_hrf/
├── log.txt                    # 전체 분석 로그
├── summary.csv                # 수치 결과
└── figures/                   # 시각화 (원래 코드에서 생성 가능)
```

## 서버에서 실행 (Running on Server)

### 업로드:

```bash
# 로컬 머신에서:
scp -r reproduction_pipeline/ haba6030@node2:/scratch/connectome/haba6030/colorBlind/
```

### 실행:

```bash
# 서버에서:
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind/reproduction_pipeline

# Conda 환경 활성화
conda activate nilearn

# ROI 생성
python build_rois_reproduction.py

# 분석 실행 (V2 예시)
python run_reconstruction_reproduction.py --roi V2
```

### SLURM 배치 작업 (선택사항):

```bash
#!/bin/bash
#SBATCH -J reproduce_V2
#SBATCH -c 8
#SBATCH --mem=64G
#SBATCH -t 2:00:00
#SBATCH --nodelist=node2
#SBATCH -o logs/reproduce_V2_%j.out
#SBATCH -e logs/reproduce_V2_%j.err

source $(conda info --base)/etc/profile.d/conda.sh
conda activate nilearn

cd /scratch/connectome/haba6030/colorBlind/reproduction_pipeline

python run_reconstruction_reproduction.py --roi V2
```

## 트러블슈팅

### 문제: "ROI mask not found"

**해결:**
```bash
python build_rois_reproduction.py
```

### 문제: "fMRIPrep directory not found"

**확인:**
```bash
ls /storage/connectome/haba6030/fmriprep_out/sub-01/
```

fMRIPrep 데이터가 올바른 위치에 있는지 확인.

### 문제: "Event file not found"

**확인:**
```bash
ls /scratch/connectome/haba6030/colorBlind/pilot/sub-01/func/
```

이벤트 파일이 BIDS 구조에 있는지 확인.

### 문제: Voxel 수가 크게 다름

**가능한 원인:**
- Atlas 파일 버전 차이
- 리샘플링 방법 차이
- Brain mask 적용 차이

**영향:**
- ±5% 이내: 무시 가능
- ±5-10%: 결과가 약간 다를 수 있음
- >10%: 심각한 문제, 조사 필요

### 문제: Novel error가 크게 다름

**체크리스트:**
1. Optimal delay가 일치하는가?
2. Voxel 수가 비슷한가?
3. Classification accuracy가 100%인가?
4. 올바른 색상 hue 값을 사용하는가? (LABEL2HUE_DEG_PILOT)
5. PCA 컴포넌트가 20개인가?

## 다른 피험자에게 적용

```bash
# Sub-02 예시
python build_rois_reproduction.py --subject 02
python run_reconstruction_reproduction.py --roi V2 --subject 02
```

**주의:**
- Sub-01의 기대값은 정의되어 있음
- 다른 피험자는 결과가 다를 것으로 예상됨
- 이것이 정상입니다!

## 방법론적 차이

### 원래 B&H 2009 논문 vs 우리의 Quick Fix

| 측면 | B&H 2009 | Quick Fix |
|------|----------|-----------|
| HRF 추정 | Voxel별 전체 HRF 곡선 | 평균 HRF에서 최적 딜레이 |
| ROI 정의 | 기능적 retinotopy | Wang atlas |
| V4/VO1 | 최고 성능 | 테스트 불가 (atlas 없음) |
| 매개변수 수 | ~3,100 | ~310 (90% 감소) |
| 과적합 위험 | 높음 | 낮음 |

### 왜 Quick Fix가 작동하는가?

1. **매개변수 감소**: 3,100 → 310 (90% 감소)
2. **Voxel 이질성 보존**: 각 voxel의 고유한 진폭 유지
3. **데이터 기반 타이밍**: 최적 딜레이를 직접 추정
4. **PCA 정규화**: 20 컴포넌트로 추가 감소

## 참고 문헌

- Brouwer, G. J., & Heeger, D. J. (2009). Decoding and reconstructing color from responses in human visual cortex. Journal of Neuroscience, 29(44), 13992-14003.
- Wang, L., Mruczek, R. E., Arcaro, M. J., & Kastner, S. (2015). Probabilistic maps of visual topography in human cortex. Cerebral Cortex, 25(10), 3911-3931.

## 연락처

문제가 있거나 질문이 있으면 원래 대화 기록을 참조하거나 이슈를 열어주세요.

---

**생성일**: 2025-11-08
**버전**: 1.0 (재현 파이프라인)
**상태**: 검증됨 (V2: 52.4° novel error)
