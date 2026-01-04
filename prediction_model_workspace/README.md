# Hyperalignment 기반 Prediction Model 프로젝트

**시작일**: 2025-12-28
**목표**: HC common space 기반 novel color prediction model 개발 및 CVD 개별 필터 최적화

---

## ⚠️ IMPORTANT: Workspace 역할 및 사용 규칙

### 이 디렉토리는 "작업 공간(Workspace)"입니다

**역할**:
- ✅ **실험 및 개발**: 새로운 분석 방법 시도, 코드 개발, 파라미터 튜닝
- ✅ **중간 결과 저장**: 검증 중인 결과 (`results/` - gitignored)
- ✅ **진행 기록**: 성공/실패한 시도 모두 `docs/PROGRESS_LOG.md`에 기록
- ❌ **최종 분석 아님**: 완성된 분석은 `../analysis/phase*_*/`로 이동

### 완성된 분석의 최종 위치

```
prediction_model_workspace/  →  ../analysis/
├── Phase 1 완료 시            →  phase1_hyperalignment/
├── Phase 2 완료 시            →  phase2_forward_model/
└── Phase 3 완료 시            →  phase3_filter_optimization/
```

**현재 상태**: analysis/에는 `future_phase*` 폴더가 계획 단계 README만 포함

### Migration 규칙 (Phase 완료 시)

**Step 1**: `final/` 폴더에 최종 코드 정리
```bash
prediction_model_workspace/final/phase1/
├── scripts/               # 검증 완료된 최종 스크립트
├── README.md             # 최종 결과 요약
└── figures/              # 주요 그림
```

**Step 2**: `../analysis/`로 복사 및 이름 변경
```bash
# Phase 1 예시
cp -r final/phase1/* ../analysis/future_phase1_hyperalignment/
mv ../analysis/future_phase1_hyperalignment ../analysis/phase1_hyperalignment
```

**Step 3**: workspace 버전 아카이브
```bash
# docs/PROGRESS_LOG.md에 완료 기록
# workspace/scripts/ 버전 히스토리는 유지 (참고용)
```

---

## 📂 프로젝트 구조

```
prediction_model_workspace/
├── README.md                    (본 문서 - workspace 사용 규칙)
├── MASTER_PLAN.md              (전체 3-phase 계획)
├── EXECUTION_GUIDE.md          (실행 가이드)
├── QUICK_START.md              (빠른 시작)
│
├── docs/                        (상세 문서 - 작업 중 버전)
│   ├── PHASE1_HYPERALIGNMENT.md
│   ├── PHASE2_PREDICTION_MODEL.md
│   ├── PHASE3_CVD_FILTER_OPTIMIZATION.md
│   ├── overall.png, phase1-3.png   (파이프라인 이미지)
│   └── PROGRESS_LOG.md          (진행 기록 - 시행착오 포함)
│
├── scripts/                     (실험 스크립트 - 개발 중)
│   ├── 00_check_data_structure.py
│   ├── 01_reliability_comparison.py
│   ├── 02_hyperalignment.py     (작성 예정)
│   ├── 03_evaluate_alignment.py (작성 예정)
│   ├── 04_channel_encoder.py    (작성 예정)
│   ├── 05_loco_cv.py            (작성 예정)
│   └── 06_cvd_filter_optimization.py (작성 예정)
│
├── final/                       ← 완성된 코드만 (analysis/로 이동 전 단계)
│   ├── phase1/                  (Phase 1 완료 시 생성)
│   ├── phase2/                  (Phase 2 완료 시 생성)
│   └── phase3/                  (Phase 3 완료 시 생성)
│
├── results/                     (중간 결과 - gitignored)
│   ├── alignment_quality/       (Phase 1 중간 결과)
│   ├── prediction_validation/   (Phase 2 중간 결과)
│   └── filter_optimization/     (Phase 3 중간 결과)
│
└── run_*.sbatch                 (SLURM 작업 스크립트)
```

### 디렉토리 역할 요약

| 디렉토리 | 역할 | Git 추적 | 최종 위치 |
|---------|------|---------|----------|
| `docs/` | 작업 중 문서 (자주 업데이트) | ✅ Yes | workspace 유지 |
| `scripts/` | 실험 스크립트 (버전 관리) | ✅ Yes | final/로 선별 복사 |
| `results/` | 중간 결과 | ❌ No (gitignored) | 최종 결과만 derivatives/ |
| `final/` | 검증 완료 코드 | ✅ Yes | analysis/로 이동 |

---

## 🔗 연관 디렉토리

**메인 분석 디렉토리** (최종 완성된 분석):
- `../analysis/future_phase1_hyperalignment/` - Phase 1 계획 (workspace 완료 시 phase1_hyperalignment로 변경)
- `../analysis/future_phase2_forward_model/` - Phase 2 계획
- `../analysis/future_phase3_filter_optimization/` - Phase 3 계획

**문서 참조**:
- 메인 README.md에서 이 workspace 설명: `../README.md` (Project Structure 섹션)
- 상세 계획: `./MASTER_PLAN.md`
- 진행 상황: `./docs/PROGRESS_LOG.md`

---

## 🎯 프로젝트 목표

### 1. Hyperalignment를 통한 HC Common Space 구축
- **현재 한계**: Procrustes 정렬만으로는 HC 간 variability 완전 해소 어려움
- **새로운 접근**: Trial-wise hyperalignment로 안정적인 공통 표현 공간 구축
- **기대 효과**: Common W의 일반화 성능 향상, between-subject consistency 증가

### 2. Novel Color Prediction Model 개발
- **현재 한계**: 8색 자극에만 국한된 분석
- **새로운 접근**: Channel-based encoder로 임의의 색 각도 예측
- **기대 효과**: 연속 색 공간 모델링, LOCO CV로 일반화 가능성 입증

### 3. CVD 개별 필터 학습을 위한 데이터 증강
- **현재 한계**: CVD 필터 학습에 충분한 샘플 부족 (8색)
- **새로운 접근**: Prediction model로 synthetic voxel patterns 생성
- **기대 효과**: 학습 샘플 확대, 필터 성능 개선

---

## 🔬 방법론 요약

### Phase 1: HC-only Hyperalignment
```
Trial-wise beta (LS-S) → PCA 차원축소 → Hyperalignment (SRM/GPA)
→ HC common space + transformations
```

**핵심 포인트**:
- CVD는 학습에서 배제 (공통 공간 오염 방지)
- Trial-wise 접근으로 대응점 증가 (~384 trials)
- 차원 축소 (k=20-80)로 안정성 확보

### Phase 2: Channel-based Prediction
```
색 각도 θ → Channel responses C(θ) → W_enc → Predicted voxel pattern ŷ(θ)
```

**핵심 포인트**:
- 6개 cosine^2 half-wave channels
- Common space에서 encoder 학습
- LOCO CV로 내삽 가능성 검증

### Phase 3: CVD Application & Augmentation
```
CVD → HC common space 투사 → Prediction model → HC-like targets
→ 개별 필터 A,b 학습 (augmented data)
```

**핵심 포인트**:
- CVD 왜곡 보존 (학습 배제)
- Synthetic data로 샘플 확대
- Common vs individual model 비교

---

## 📊 성공 지표 (Success Criteria)

### Phase 1 (Hyperalignment)
- ✅ **필수**: Procrustes disparity < 0.10, Split-half stability > 0.80
- ⭐ **우수**: Disparity < 0.05, LORO-CV error 감소 > 5°

### Phase 2 (Prediction)
- ✅ **필수**: LOCO error < 50° (chance: 90°), RDM correlation > 0.5
- ⭐ **우수**: LOCO error < 40°, Common ≈ Individual (Δ < 10°)

### Phase 3 (CVD)
- ✅ **필수**: CVD 필터 성능 유지, HC-like target 적용 가능 (error < 70°)
- ⭐ **우수**: 데이터 증강으로 CVD 필터 > 10° 개선

---

## 🚀 Quick Start

### 1. 환경 설정
```bash
# Conda environment
conda activate nilearn

# BrainIAK 설치 (서버)
pip install brainiak

# 필요한 패키지 확인
python -c "import nilearn, brainiak, scipy; print('OK')"
```

### 2. 데이터 구조 확인 (첫 단계)
```bash
cd prediction_model/scripts
python 00_check_data_structure.py
```

**확인 항목**:
- Events 파일 위치 및 형식
- 자극 순서 동일성 (subject 간, run 간)
- TR, trial duration, ISI
- BOLD preprocessing outputs

### 3. Pilot Test (HC 2명)
```bash
# Trial-wise GLM
python 01_trial_wise_glm.py --subjects 02 03 --roi V1 --runs 1 2

# Hyperalignment test
python 02_hyperalignment.py --subjects 02 03 --roi V1 --n_features 50

# 정렬 품질 평가
python 03_evaluate_alignment.py --roi V1
```

### 4. Full Pipeline (모든 HC)
```bash
# 전체 실행 (SLURM)
sbatch scripts/run_full_pipeline.sbatch
```

---

## 📈 현재 상태 (Progress)

### ✅ 완료
- [x] 프로젝트 구조 설정
- [x] 마스터 플랜 문서 작성
- [x] Phase 1-2 상세 계획 수립
- [x] Progress log 템플릿 생성

### 🔄 진행 중
- [ ] 데이터 구조 분석 스크립트 작성 (Day 2)
- [ ] 자극 순서 동일성 검증
- [ ] BrainIAK 설치 및 튜토리얼

### ⏳ 예정
- [ ] LS-S GLM 구현 (Week 1)
- [ ] Pilot hyperalignment (Week 2)
- [ ] Full pipeline (Week 2-3)

**상세 진행 상황**: [`docs/PROGRESS_LOG.md`](docs/PROGRESS_LOG.md) 참고

---

## 📚 주요 문서

### 필수 읽기
1. **[MASTER_PLAN.md](MASTER_PLAN.md)**: 전체 프로젝트 개요, 3단계 계획, 타임라인
2. **[PROGRESS_LOG.md](docs/PROGRESS_LOG.md)**: 일별 진행 기록, 실험 결과, 이슈 추적

### Phase별 상세 계획
1. **[PHASE1_HYPERALIGNMENT.md](docs/PHASE1_HYPERALIGNMENT.md)**
   - Trial-wise GLM (LS-S) 구현 방법
   - HC-only hyperalignment 절차
   - 정렬 품질 평가 지표

2. **[PHASE2_PREDICTION_MODEL.md](docs/PHASE2_PREDICTION_MODEL.md)**
   - Channel response function 정의
   - Common/Individual encoder 학습
   - LOCO cross-validation 프레임워크

3. **[PHASE3_CVD_APPLICATION.md](docs/PHASE3_CVD_APPLICATION.md)** (작성 예정)
   - CVD 투사 및 왜곡 평가
   - 데이터 증강 파이프라인
   - 개별 필터 재학습 및 검증

---

## 🔗 관련 자료

### 기존 분석 결과
- **Procrustes 분석**: [`../docs/PROCRUSTES_ANALYSIS_GUIDE.md`](../docs/PROCRUSTES_ANALYSIS_GUIDE.md)
- **Baseline 결과**: `../results/group_level/baseline81_deob_determin/`
- **Phase 1 결과**: `../docs/PHASE1_RESULTS_ANALYSIS.md`

### 참고 논문
- Bannert & Bartels (2025). SRM for cross-subject color decoding. *J. Neurosci*. ⭐
- Chen et al. (2015). Shared Response Model. *NIPS*.
- Brouwer & Heeger (2009). Color decoding and reconstruction. *J. Neurosci*.
- Mumford et al. (2012). LS-S for single-trial estimates. *NeuroImage*.

### 구현 참고
- [BrainIAK SRM Tutorial](https://brainiak.org/tutorials/10-srm/)
- [Nilearn FirstLevelModel](https://nilearn.github.io/stable/modules/generated/nilearn.glm.first_level.FirstLevelModel.html)
- [LSS Implementation (Dartmouth)](https://dartbrains.org/content/RSA.html#lss-single-trial-models)

---

## 💡 핵심 개념 정리

### Hyperalignment vs Procrustes
| 특성 | Procrustes | Hyperalignment |
|------|-----------|----------------|
| 정렬 단위 | 점군 (8 colors) | Trajectory (trials) |
| 대응점 수 | 8 | ~384 (trial-wise) |
| 변환 | 회전, 이동 | 고차원 직교변환 |
| 목적 | 비교 가능화 | 공통 공간 학습 |

### Trial-wise vs Color-averaged
| 특성 | Color-averaged (기존) | Trial-wise (새) |
|------|---------------------|---------------|
| 데이터 형태 | (8, voxels) | (~384, voxels) |
| 정보량 | 색별 평균 (trial variance 손실) | 모든 trial 보존 |
| Hyperalignment | GPA (8 대응점) | SRM (384 대응점) |
| SNR | 높음 | 낮음 (regularization 필요) |

### Common vs Individual Model
| 특성 | Common | Individual |
|------|--------|-----------|
| 학습 데이터 | 모든 HC pooled | 각 subject 별도 |
| 일반화 | 우수 (robust) | 제한적 (overfitting 위험) |
| 개인차 | 무시 | 반영 |
| CVD 적용 | 표준 target | - |

---

## ⚠️ 주의사항 및 Troubleshooting

### 예상 문제 1: Trial-wise SNR 너무 낮음
**증상**: Beta estimates 매우 noisy, split-half < 0.5
**해결**: Spatial smoothing ↑, AR1 regularization, searchlight 단위

### 예상 문제 2: Hyperalignment 수렴 안 됨
**증상**: Reference 계속 변화, disparity 감소 없음
**해결**: 차원 축소 강화 (k ↓), 초기값 변경, regularization

### 예상 문제 3: LOCO 성능 chance level
**증상**: Reconstruction error > 80°
**해결**: Ridge regularization, bandwidth 조정, 차원 재검토

---

## 📞 Contact & Collaboration

**연구자**: Neuroimaging Team
**프로젝트 저장소**: `colorBlind_analysis/prediction_model/`
**이슈 보고**: `docs/PROGRESS_LOG.md`의 Issue Tracker 활용

---

**최종 업데이트**: 2025-12-28
**다음 마일스톤**: 데이터 준비성 확인 (2025-12-29)

---

## 🎓 How to Contribute

### 실험 결과 업데이트
1. 실험 수행 후 `docs/PROGRESS_LOG.md` 업데이트
2. 결과 파일을 `results/` 적절한 하위 폴더에 저장
3. 주요 발견 사항을 PROGRESS_LOG의 Research Notes에 기록

### 코드 작성 가이드
- 모든 스크립트는 `scripts/` 폴더에 저장
- 명명 규칙: `##_descriptive_name.py` (숫자 순서 prefix)
- Docstring 필수 (Google style)
- 주요 파라미터는 argparse로 받기

### 문서 업데이트
- 주요 결정 사항은 PROGRESS_LOG에 기록
- Phase별 문서는 구현 중 발견한 내용으로 업데이트
- README는 프로젝트 구조 변경 시 수정

---

**Let's build a robust prediction model! 🚀**
