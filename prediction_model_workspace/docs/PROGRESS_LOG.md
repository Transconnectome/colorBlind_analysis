# Prediction Model 프로젝트 진행 기록

**프로젝트 시작**: 2025-12-28
**마지막 업데이트**: 2025-12-28

---

## 📅 Timeline Overview

```
Week 1 (2025-12-28 ~ 2026-01-03)
├─ Day 1-2: 프로젝트 설정 및 데이터 준비성 확인
├─ Day 3-4: Trial-wise GLM 구현 (LS-S)
└─ Day 5-7: Pilot hyperalignment test

Week 2-3 (2026-01-04 ~ 2026-01-17)
├─ Full hyperalignment (HC 5명)
├─ Alignment quality 평가
└─ Common W 재학습

Week 3-4 (2026-01-11 ~ 2026-01-24)
├─ Channel encoder 개발
├─ LOCO CV 검증
└─ Common vs individual 비교

Week 5-6 (2026-01-25 ~ 2026-02-07)
├─ CVD 적용
├─ 데이터 증강
└─ 최종 평가
```

---

## 📝 Daily Progress

### 2025-12-28 (Day 1) - 프로젝트 시작

#### 완료된 작업
✅ **문서화 기반 구축**
- [x] `prediction_model/` 폴더 구조 생성
  - `docs/`, `scripts/`, `results/` 하위 폴더
- [x] `MASTER_PLAN.md` 작성 완료
  - 전체 프로젝트 개요, 3단계 계획, 성공 지표
- [x] `PHASE1_HYPERALIGNMENT.md` 작성 완료
  - Trial-wise GLM 설계 (LS-S 방식)
  - HC-only hyperalignment 구현 계획
  - 정렬 품질 평가 지표 정의
- [x] `PHASE2_PREDICTION_MODEL.md` 작성 완료
  - Channel response function 정의
  - Encoder 학습 방법
  - LOCO CV 프레임워크

#### 주요 결정 사항
🔹 **Trial-wise 접근 채택**
- 이유: 자극 순서 동일 → time-series hyperalignment 가능
- 방법: Least Squares Separate (LS-S) 선택
  - Beta 간 독립성 확보
  - Hyperalignment에 최적

🔹 **HC-only Hyperalignment**
- CVD는 학습에서 배제, 투사만 수행
- 목적: HC common space 오염 방지, CVD 왜곡 보존

🔹 **라이브러리 선택**
- Primary: BrainIAK SRM (검증된 구현체)
- Alternative: Custom GPA (비교 및 fine-tuning용)

#### 다음 단계 (Day 2-3)
🎯 **데이터 준비성 확인**
- [ ] Events/stimulus files 구조 분석
- [ ] 자극 순서 동일성 검증 스크립트
- [ ] TR, trial duration 확인
- [ ] 현재 derivatives 데이터와 비교

🎯 **환경 설정**
- [ ] BrainIAK 설치 (서버)
- [ ] LS-S GLM 구현 시작 (`trial_wise_glm.py`)

#### 메모 및 고려사항
💡 **데이터 규모 체크**
- HC 5명 × 6 runs × ~384 trials = ~11,520 total trials
- ROI voxels: V1(429), V2(279) → 차원 축소 필수
- Target: PCA k=20-80 (voxel 수의 10-20%)

💡 **성공 기준 재확인**
- Phase 1: Disparity < 0.10 (기존 Procrustes: ~0.09)
- Phase 2: LOCO error < 50° (chance: 90°)
- Phase 3: CVD 필터 성능 유지 또는 개선

---

### 2025-12-29 (Day 2) - 예정

#### 계획된 작업
📋 **데이터 분석**
- [ ] 자극 파일 구조 확인 (`/storage/.../colorBlind_data_deoblique/`)
- [ ] Run 간 자극 순서 동일성 검증
- [ ] Timing 정보 정리 (onset, duration, ISI)

📋 **문헌 조사**
- [ ] LS-S 구현 예시 찾기 (nilearn, SPM)
- [ ] BrainIAK SRM 튜토리얼 검토
- [ ] Trial-wise GLM SNR 이슈 및 해결책

#### 예상 이슈
⚠️ **Trial spacing 부족**
- 만약 ISI < 4s → HRF 겹침 심각
- 해결책: FIR deconvolution 고려

⚠️ **자극 순서 불일치**
- 만약 subject마다 순서 다름 → time-series 정렬 불가
- 대안: 조건 기반 hyperalignment (8색 점군)

---

### 주간 요약

#### Week 1 Summary (예정)

**목표**: 프로젝트 기반 구축 및 feasibility 점검

**완료 예정**:
- [ ] 프로젝트 문서화 (MASTER_PLAN, PHASE1-3)
- [ ] 데이터 구조 분석 및 준비성 확인
- [ ] Trial-wise GLM 구현 (pilot test)
- [ ] BrainIAK 환경 설정

**다음 주 목표**: HC 2명 pilot hyperalignment 테스트

---

## 🔬 실험 결과 (Experiment Log)

### Experiment 1: 데이터 구조 분석 (진행 예정)

**날짜**: 2025-12-29 예정
**목적**: Trial-wise hyperalignment 가능성 확인

**체크리스트**:
- [ ] Events 파일 형식 (TSV, JSON?)
- [ ] Columns: onset, duration, trial_type, ...
- [ ] 자극 순서 동일성 (subject 간, run 간)
- [ ] TR 및 trial 수

**결과**: (업데이트 예정)

---

### Experiment 2: LS-S Pilot Test (진행 예정)

**날짜**: 2026-01-02 예정
**목적**: Single-trial GLM SNR 평가

**설정**:
- Subject: 02 (pilot)
- ROI: V1
- Runs: 1-2 (테스트용)

**평가 지표**:
- Trial-wise beta SNR
- Split-half reliability
- 기존 run-averaged beta와 correlation

**결과**: (업데이트 예정)

---

## 📊 성능 추적 (Performance Tracking)

### Hyperalignment Quality Metrics

| Metric | Target | Baseline | Current | Status |
|--------|--------|----------|---------|--------|
| Procrustes Disparity | < 0.10 | 0.089 | - | 대기 |
| Split-half Stability | > 0.80 | 0.91 (V1) | - | 대기 |
| RDM Similarity | > 0.30 | 0.26 (V1) | - | 대기 |
| Common W Accuracy | ≥ baseline | 32° (V1) | - | 대기 |

### Prediction Model Metrics

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| LOCO CV Error | < 50° | - | 대기 |
| RDM Consistency | > 0.50 | - | 대기 |
| Common vs Ind | Δ < 10° | - | 대기 |

### CVD Application Metrics

| Metric | Target | Baseline | Current | Status |
|--------|--------|----------|---------|--------|
| CVD Disparity (HC space) | < 0.08 | 0.028-0.039 (V1) | - | 대기 |
| CVD Filter Performance | ≥ baseline | - | - | 대기 |
| Data Augmentation Effect | > 5° improve | - | - | 대기 |

---

## 🐛 Issues & Solutions

### Issue Tracker

#### Issue #1: [Open] 자극 순서 동일성 미확인
**날짜**: 2025-12-28
**우선순위**: 🔴 High
**설명**: Trial-wise hyperalignment의 전제 조건
**담당**: -
**상태**: 조사 필요

**해결 방안**:
1. Events 파일 비교 스크립트 작성
2. Subject 간, run 간 순서 검증
3. 만약 불일치 → 조건 기반 GPA로 전환

---

#### Issue #2: [Open] LS-S 계산 비용
**날짜**: 2025-12-28
**우선순위**: 🟡 Medium
**설명**: 384 trials × 6 runs × 5 subjects = ~11,520 GLMs
**담당**: -
**상태**: 최적화 필요

**해결 방안**:
1. 병렬 처리 (SLURM array jobs)
2. Pre-computed design matrices
3. Run 단위로 분할 실행

---

## 💡 Research Notes

### Note 1: Hyperalignment vs Procrustes
**날짜**: 2025-12-28

**핵심 차이**:
- Procrustes: 두 점군 (8 colors) 정렬
- Hyperalignment: 여러 피험자의 전체 trajectory 정렬

**우리 케이스**:
- Trial-wise면 ~384 대응점 → hyperalignment 유리
- 색별 평균이면 8 대응점 → GPA가 적절

**결론**: Trial-wise 성공 시 hyperalignment, 실패 시 GPA

---

### Note 2: Novel Color Validation 전략
**날짜**: 2025-12-28

**문제**: 8색 외 실제 데이터 없음

**검증 방법**:
1. LOCO CV (내삽 가능성)
2. RDM consistency (구조 보존)
3. Smoothness (연속성)

**논문 표현**:
- "Interpolation within trained color space" ✅
- "Generalization to unseen colors" ❌ (extrapolation 아님)

---

## 📚 References & Resources

### 구현 참고 자료
- [BrainIAK SRM Tutorial](https://brainiak.org/tutorials/10-srm/)
- [LS-S GLM (Mumford et al., 2012)](https://doi.org/10.1016/j.neuroimage.2012.04.051)
- Nilearn FirstLevelModel [문서](https://nilearn.github.io/stable/modules/generated/nilearn.glm.first_level.FirstLevelModel.html)

### 관련 논문
- Bannert & Bartels (2025): SRM for color decoding ⭐
- Chen et al. (2015): SRM 원본 논문
- Brouwer & Heeger (2009): Channel model

---

## 🎯 Next Actions

### Immediate (이번 주)
1. [x] 프로젝트 구조 및 문서화 완료
2. [ ] 데이터 구조 분석 스크립트 작성
3. [ ] 자극 순서 검증
4. [ ] BrainIAK 설치

### Short-term (다음 주)
1. [ ] LS-S GLM 구현 완료
2. [ ] Pilot hyperalignment (HC 2명)
3. [ ] 정렬 품질 평가 프레임워크

### Medium-term (2-3주 후)
1. [ ] Full hyperalignment (HC 5명)
2. [ ] Common encoder 학습
3. [ ] LOCO CV 검증

---

**마지막 업데이트**: 2025-12-28 23:45
**다음 업데이트 예정**: 2025-12-29 (데이터 분석 완료 후)
