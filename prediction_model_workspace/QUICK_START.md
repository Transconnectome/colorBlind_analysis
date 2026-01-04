# Quick Start: Step 1.2 실행 가이드

**빠른 실행을 위한 커맨드 모음**

---

## 🚀 Step 1.2: Reliability Comparison

### **1. 파일 업로드 (Local → Server)**

```bash
# Terminal (Local)
cd ~/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis

# 스크립트 업로드
scp prediction_model/scripts/01_reliability_comparison.py \
    haba6030@node2:/scratch/connectome/haba6030/colorBlind/prediction_model/scripts/

# Sbatch 업로드
scp prediction_model/run_step1_reliability_check.sbatch \
    haba6030@node2:/scratch/connectome/haba6030/colorBlind/prediction_model/
```

---

### **2. 서버 실행**

```bash
# SSH 접속
ssh haba6030@node2

# 디렉토리 이동
cd /scratch/connectome/haba6030/colorBlind/prediction_model

# Logs 디렉토리 생성
mkdir -p logs

# Job 제출 (sub-02, V1)
sbatch run_step1_reliability_check.sbatch 02 V1

# Job 상태 확인
squeue -u haba6030

# 실시간 로그 (optional)
# tail -f logs/step1_reliability_sub-<JOB_ID>.out
```

---

### **3. 결과 확인 (Server)**

```bash
# 로그 확인
ls -lt logs/step1_reliability_sub-*.out | head -1  # 최신 파일
cat logs/step1_reliability_sub-<JOB_ID>.out

# 결과 JSON 확인
cat results/reliability_check/reliability_sub-02_V1.json
```

---

### **4. 결과 다운로드 (Server → Local)**

```bash
# Terminal (Local)
scp haba6030@node2:/scratch/connectome/haba6030/colorBlind/prediction_model/results/reliability_check/reliability_sub-02_V1.json \
    ~/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/prediction_model/results/reliability_check/

# 확인
cat ~/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/prediction_model/results/reliability_check/reliability_sub-02_V1.json
```

---

### **5. 의사결정**

**JSON 파일에서 `decision` 필드 확인**:

```bash
# Local에서
cd ~/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/prediction_model
cat results/reliability_check/reliability_sub-02_V1.json | grep -A 5 '"decision"'
```

**Decision 코드**:
- `"STOP"` → Data quality 문제, preprocessing 재검토
- `"IMPROVE_GLM"` → Smoothing 증가 또는 confounds 추가 후 재실행
- `"PROCEED_WITH_CAUTION"` → ✅ Step 1.3으로 진행
- `"PROCEED"` → ✅ Step 1.3으로 진행

---

## 🔄 재실행이 필요한 경우

### **Scenario: IMPROVE_GLM (Smoothing 증가)**

```bash
# Local에서 스크립트 수정
# prediction_model/run_step1_reliability_check.sbatch
# 수정: --smoothing_fwhm 6.0 → --smoothing_fwhm 8.0

# 재업로드
scp prediction_model/run_step1_reliability_check.sbatch \
    haba6030@node2:/scratch/connectome/haba6030/colorBlind/prediction_model/

# 서버에서 재실행
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind/prediction_model
sbatch run_step1_reliability_check.sbatch 02 V1
```

---

## 📊 모든 ROI 테스트 (Optional)

**한 번에 여러 ROI 실행**:

```bash
# 서버에서
cd /scratch/connectome/haba6030/colorBlind/prediction_model

# V1, V2, V3, hV4 순차 실행
for roi in V1 V2 V3 hV4; do
    sbatch run_step1_reliability_check.sbatch 02 $roi
    echo "Submitted: sub-02 $roi"
done

# Job 확인
squeue -u haba6030
```

---

## 🎯 Expected Timeline

| Step | Duration | Status |
|------|----------|--------|
| Upload files | 1 min | - |
| Job queue wait | 0-5 min | - |
| Execution | 30-60 min | - |
| Download results | 1 min | - |
| **Total** | **~40-70 min** | - |

---

## ✅ Success Criteria

**Step 1.2 성공**:
```json
{
  "decision": "PROCEED" or "PROCEED_WITH_CAUTION",
  "trial_wise": {
    "mean_reliability": >= 0.30
  }
}
```

→ **다음 단계**: Step 1.3 (Pilot Hyperalignment)

---

## 🆘 Quick Troubleshooting

### **Job 안 돌아갈 때**
```bash
# Job 상태 확인
squeue -u haba6030

# 에러 로그 확인
cat logs/step1_reliability_sub-<JOB_ID>.err
```

### **ROI mask 못 찾을 때**
```bash
# 서버에서 ROI mask 위치 확인
find /scratch/connectome/haba6030/colorBlind/derivatives -name "roi_mask.nii.gz" | grep V1 | head -1
```

### **메모리 부족**
```bash
# Sbatch 파일 수정
#SBATCH --mem=32G  # 16G → 32G

# 재업로드 후 재실행
```

---

**마지막 업데이트**: 2025-12-28
