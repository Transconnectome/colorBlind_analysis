# Hyperalignment Project: 단계별 실행 가이드

**프로젝트**: CVD Individual Filter Optimization using Hyperalignment
**시작일**: 2025-12-28

---

## 🎯 전체 흐름 요약

```
Week 1: Data Validation & Feasibility Check
  └─ Step 1.1: Trial order consistency ✓
  └─ Step 1.2: Reliability comparison (baseline vs trial-wise)
  └─ Step 1.3: Pilot hyperalignment (HC 2명)

Week 2: Full Hyperalignment (HC 5명)
  └─ Step 2.1: Full hyperalignment
  └─ Step 2.2: Alignment quality evaluation

Week 3: Phase 2 Pilot (Encoder)
  └─ Step 3.1: Channel encoder learning
  └─ Step 3.2: LOCO CV validation

Week 4: Phase 3 Pilot (CVD Filter)
  └─ Step 4.1: CVD projection
  └─ Step 4.2: Filter optimization
  └─ Step 4.3: Tier 1 validation
```

---

## 📅 Week 1: Data Validation

### **Step 1.1: Trial Order Consistency Check** ✅

**목표**: 모든 subject/run에서 trial 순서가 동일한지 확인

**Local에서 실행**:
```bash
cd ~/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/prediction_model/scripts

# HC 5명 확인
python 00_check_data_structure.py --subjects 02 03 05 06 07

# 예상 출력:
# ✅ 결론: 모든 subject-run에서 자극 순서 IDENTICAL
# → Hyperalignment (trial-aligned GPA) 가능!
```

**결과 확인**:
```bash
cat ../results/data_structure_check/data_structure_summary.json
```

**의사결정**:
- ✅ `"stimulus_order_consistent": true` → **Proceed to Step 1.2**
- ❌ `"stimulus_order_consistent": false` → **Fallback: 조건 기반 GPA (8 colors)**

---

### **Step 1.2: Reliability Comparison** ⭐

**목표**: Color-averaged vs Trial-wise reliability 비교

#### **Phase A: 파일 업로드**

**Local에서**:
```bash
# 스크립트 업로드
scp prediction_model/scripts/01_reliability_comparison.py \
    haba6030@node2:/scratch/connectome/haba6030/colorBlind/prediction_model/scripts/

# Sbatch 파일 업로드
scp prediction_model/run_step1_reliability_check.sbatch \
    haba6030@node2:/scratch/connectome/haba6030/colorBlind/prediction_model/
```

#### **Phase B: 서버에서 실행**

**SSH 접속**:
```bash
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind/prediction_model
```

**Pilot test (1 subject, 1 ROI)**:
```bash
# HC 1명 (sub-02), V1
sbatch run_step1_reliability_check.sbatch 02 V1

# Job 제출 확인
squeue -u haba6030

# 실시간 로그 확인 (optional)
tail -f logs/step1_reliability_sub-<JOB_ID>.out
```

**예상 실행 시간**: ~30-60분

#### **Phase C: 결과 확인**

**서버에서**:
```bash
# 로그 확인
cat logs/step1_reliability_sub-<JOB_ID>.out

# 결과 파일 확인
cat results/reliability_check/reliability_sub-02_V1.json
```

**Local로 다운로드**:
```bash
# Local terminal에서
scp haba6030@node2:/scratch/connectome/haba6030/colorBlind/prediction_model/results/reliability_check/reliability_sub-02_V1.json \
    ~/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/prediction_model/results/reliability_check/
```

#### **Phase D: 결과 해석**

**결과 파일 확인**:
```bash
cd ~/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/prediction_model
cat results/reliability_check/reliability_sub-02_V1.json
```

**예상 출력 형식**:
```json
{
  "subject": "02",
  "roi": "V1",
  "color_averaged": {
    "mean_reliability": 0.75,
    "per_color": {
      "red": 0.78,
      "orange": 0.72,
      ...
    }
  },
  "trial_wise": {
    "mean_reliability": 0.45,
    "per_color": {
      "red": 0.48,
      "orange": 0.42,
      ...
    }
  },
  "decision": "PROCEED_WITH_CAUTION",
  "decision_message": "..."
}
```

**의사결정 매트릭스**:

| Color-averaged | Trial-wise | Decision | Action |
|---------------|-----------|----------|--------|
| < 0.3 | any | `STOP` | Data quality 문제, preprocessing 재검토 |
| ≥ 0.5 | < 0.3 | `IMPROVE_GLM` | Smoothing ↑ (8mm), confounds 추가 |
| ≥ 0.3 | ≥ 0.3 | `PROCEED_WITH_CAUTION` | Pilot GPA, regularization |
| any | ≥ 0.4 | `PROCEED` | Full hyperalignment 진행 |

---

### **Step 1.2 후속 조치**

#### **Scenario 1: STOP (Data quality 문제)**
```bash
# 원인 진단
# 1. Alignment 확인
# 2. fMRIPrep quality check
# 3. Subject exclusion 고려

# DO NOT proceed
```

#### **Scenario 2: IMPROVE_GLM (SNR 문제)**
```bash
# Smoothing 증가로 재실행
sbatch run_step1_reliability_check.sbatch 02 V1 --smoothing_fwhm 8.0

# 또는 confounds 추가
# 스크립트 수정: --confounds_strategy motion_compcor
```

**수정 후 재실행**:
```bash
# 파일 수정 (local)
# scripts/01_reliability_comparison.py
# default smoothing_fwhm = 8.0

# 재업로드
scp prediction_model/scripts/01_reliability_comparison.py \
    haba6030@node2:/scratch/connectome/haba6030/colorBlind/prediction_model/scripts/

# 재실행
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind/prediction_model
sbatch run_step1_reliability_check.sbatch 02 V1
```

#### **Scenario 3: PROCEED_WITH_CAUTION (정상 범위)**
```bash
# ✅ Trial-wise ≥ 0.3 달성
# → Step 1.3 (Pilot GPA) 진행
```

---

### **Step 1.3: Pilot Hyperalignment** (다음 단계)

**목표**: HC 2명으로 full voxel space GPA 수렴 확인

**예정 스크립트**: `02_pilot_hyperalignment.py`
**예정 시간**: ~1-2시간

**Prerequisites**:
- ✅ Step 1.2 완료
- ✅ Decision: `PROCEED` or `PROCEED_WITH_CAUTION`

---

## 📊 진행 상황 체크리스트

### **Week 1 Progress**

- [x] Step 1.1: Trial order consistency
  - [x] 스크립트 실행
  - [x] 결과 확인: stimulus_order_consistent = true

- [ ] Step 1.2: Reliability comparison
  - [ ] 스크립트 작성 ✅
  - [ ] 서버 업로드
  - [ ] Pilot test (sub-02, V1)
  - [ ] 결과 해석
  - [ ] 의사결정

- [ ] Step 1.3: Pilot hyperalignment
  - [ ] 스크립트 작성 (대기)
  - [ ] HC 2명 테스트
  - [ ] 수렴 확인

---

## 🔧 Troubleshooting

### **Problem 1: ROI mask not found**

**Error message**:
```
FileNotFoundError: ROI mask for V1 not found
```

**Solution**:
```bash
# 기존 baseline 분석에서 ROI mask 복사
# 서버에서:
cd /scratch/connectome/haba6030/colorBlind/derivatives/BH2009_deoblique_v2/baseline81_deob_determin

# V1 mask 찾기
find . -name "roi_mask.nii.gz" | grep V1 | head -1

# 복사 (if needed)
mkdir -p /scratch/connectome/haba6030/colorBlind/prediction_model/roi_masks
cp <path_to_v1_mask> /scratch/connectome/haba6030/colorBlind/prediction_model/roi_masks/V1_mask.nii.gz
```

**스크립트 수정**:
```python
# 01_reliability_comparison.py
# load_roi_mask() 함수에서 직접 경로 지정
def load_roi_mask(roi_name):
    roi_mask_file = f'/scratch/.../roi_masks/{roi_name}_mask.nii.gz'
    return image.load_img(roi_mask_file)
```

### **Problem 2: Memory error**

**Error message**:
```
MemoryError: Unable to allocate array
```

**Solution**:
```bash
# Sbatch 파일 수정: 메모리 증가
#SBATCH --mem=32G  # 16G → 32G
```

### **Problem 3: LS-S too slow**

**Issue**: Trial-wise GLM 너무 느림 (384 trials × 6 runs)

**Solution**:
```python
# 스크립트 최적화 옵션:
# 1. minimize_memory=True
# 2. Run 병렬처리 고려
# 3. Pilot은 1-2 runs만 테스트
```

---

## 📝 다음 단계 준비

### **Step 1.3 스크립트 (예정)**

필요 사항:
- [ ] LS-S GLM 함수 (Step 1.2에서 재사용)
- [ ] Regularized GPA 구현
- [ ] HC 2명 데이터 로드
- [ ] 수렴 확인 메트릭

예정 실행:
```bash
# Pilot: sub-02, 03 / V1
python 02_pilot_hyperalignment.py --subjects 02 03 --roi V1
```

---

## 🎯 Week 1 성공 기준

- ✅ Step 1.1: Trial order consistent
- ✅ Step 1.2: Trial-wise reliability ≥ 0.3
- ✅ Step 1.3: Pilot GPA converges (disparity 감소)

**Week 1 완료 시**: Week 2 (Full Hyperalignment) 진행 가능

---

**마지막 업데이트**: 2025-12-28
**다음 업데이트 예정**: Step 1.2 결과 확인 후
