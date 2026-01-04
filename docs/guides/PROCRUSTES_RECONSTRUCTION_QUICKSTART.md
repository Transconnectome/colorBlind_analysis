# Procrustes Reconstruction: Quick Start Guide

**날짜:** 2025-12-19
**목적:** HC common W를 CVD에 적용하여 **applicability 증명**

**HC subjects:** 03, 05, 06, 07 (4명)
**Excluded:** sub-01 (outlier), sub-02 (Procrustes issues), sub-04 (no V1 signal)

---

## ✅ Conda Activation (올바른 방법)

```bash
# ✅ CORRECT
source ~/.bashrc
conda activate nilearn

# ❌ WRONG - Do NOT use
source /opt/anaconda3/etc/profile.d/conda.sh
```

**참고:** 모든 SLURM batch 파일은 이미 `source ~/.bashrc` 사용 중

---

## 🎯 재조정된 목표 및 성공 기준

### 중요한 전제

**CVD의 input data는 HC와 근본적으로 다릅니다** (색각 이상으로 인한 distorted perception)

따라서:
- ❌ **비현실적:** CVD가 HC-like reconstruction 달성
- ✅ **현실적:** CVD가 **chance level보다 나으면** HC W applicability 증명!

### 성공 기준

```python
CHANCE_LEVEL = 90.0  # degrees (uniform circular distribution)

# Primary Success
if CVD_HC_W < 90.0:
    ✅ SUCCESS: HC W가 CVD에 적용 가능!
    → CVD neural pattern에 HC-like structure 존재
    → Applicability 증명 완료!

# Bonus Success
if CVD_HC_W < CVD_own_W:
    ✅✅ BONUS: Common W가 individual W보다 robust!
    → Overfitting 방지 효과
    → Group structure가 강함

# Best Case
if CVD_HC_W ≈ CVD_own_W:
    ✅✅✅ BEST: Individual 수준 달성!
    → Common W가 최적화된 수준
```

---

## 📊 예상 결과 시나리오

### Scenario A: 명확한 성공 ✅

```
CHANCE:         90.0°
HC (own W):     32° ± 3°
CVD (own W):    58° ± 5°
CVD (HC W):     55° ± 6° ✅

→ 55° < 90° ✅ Applicability 증명!
→ 55° ≈ 58° → Individual 수준과 비슷
```

**결론:** HC W 사용 가능! CVD에 HC-like structure 존재

### Scenario B: Bonus 성공 ✅✅

```
CHANCE:         90.0°
HC (own W):     32° ± 3°
CVD (own W):    58° ± 5°
CVD (HC W):     48° ± 4° ✅✅

→ 48° < 90° ✅ Applicability!
→ 48° < 58° ✅✅ Common W가 더 robust!
```

**결론:** Applicability + Robustness!

### Scenario C: 부분 성공 ⚠️

```
CHANCE:         90.0°
HC (own W):     32° ± 3°
CVD (own W):    58° ± 5°
CVD (HC W):     70° ± 8° ⚠️

→ 70° < 90° ✅ Applicability 달성
→ 70° > 58° ⚠️ Individual보다는 못함
```

**결론:** Applicability 증명됨, 하지만 최적은 아님

### Scenario D: 실패 ❌

```
CHANCE:         90.0°
CVD (HC W):     95° ± 10° ❌

→ 95° > 90° ❌ Chance보다 나쁨!
```

**결론:** HC W 적용 불가능, alignment 실패

---

## 🚀 실행 명령어 (Quick Reference)

### 1. Upload (Local)

```bash
scp analysis/group_level/reconstruction_with_procrustes.py \
    haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/group_level/

scp run_procrustes_reconstruction_*.sbatch \
    haba6030@node2:/scratch/connectome/haba6030/colorBlind/
```

### 2. Train HC Model (Server)

```bash
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind

sbatch run_procrustes_reconstruction_train.sbatch

# Monitor
tail -f logs/group_level/proc_recon_train_*.out
```

**예상 시간:** ~2-3시간

### 3. Test CVD (Server)

```bash
sbatch run_procrustes_reconstruction_test.sbatch

# Monitor
tail -f logs/group_level/proc_recon_test_*.out
```

**예상 시간:** ~1-2시간

### 4. Download Results (Local)

```bash
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/results/group_level/procrustes_reconstruction/ \
    results/group_level/
```

### 5. Check Results

```bash
# CVD errors
cat results/group_level/procrustes_reconstruction/V1/cvd_reconstruction_errors.csv

# Expected:
# subject_id,mean_error
# 08,55.3
# 09,58.1
# 10,52.7
```

---

## 📈 결과 해석 체크리스트

```bash
# 1. CVD (HC W) < 90° ?
if mean_error < 90.0:
    echo "✅ PRIMARY SUCCESS: Applicability 증명!"
else:
    echo "❌ FAILURE: Chance보다 나쁨"

# 2. CVD (HC W) < CVD (own W) ?
# CVD baseline 확인:
grep "Mean reconstruction error" \
    derivatives/BH2009_deoblique_v2/baseline81_deob_determin/sm*_sub-08_V1_*/classification_results.txt

if CVD_HC_W < CVD_own_W:
    echo "✅✅ BONUS: Common W가 더 robust!"

# 3. Statistical test
python -c "
import numpy as np
from scipy.stats import ttest_1samp

errors = [55.3, 58.1, 52.7]  # CVD (HC W)
chance = 90.0

t, p = ttest_1samp(errors, chance, alternative='less')
print(f't={t:.2f}, p={p:.4f}')

if p < 0.05:
    print('✅ Significantly better than chance!')
"
```

---

## 🎯 Key Takeaways

### ✅ 올바른 기준

1. **Primary goal:** CVD (HC W) < 90° → Applicability 증명
2. **Bonus:** CVD (HC W) < CVD (own W) → Robustness
3. **Best:** CVD (HC W) ≈ CVD (own W) → Optimal

### ❌ 피해야 할 오해

1. ~~CVD가 HC처럼 reconstruction 해야 함~~ → 비현실적
2. ~~CVD (HC W)가 HC (own W)와 비슷해야 함~~ → 불가능
3. ~~CVD 개선이 목표~~ → Applicability가 목표!

### 💡 핵심 인사이트

```
CVD input ≠ HC input (색각 이상)
    ↓
하지만 CVD neural pattern에 HC-like structure 존재?
    ↓
HC W를 CVD에 적용 → Chance보다 나음
    ↓
✅ YES! Applicability 증명!
    → Filter/intervention 가능성 제시
```

---

## 📚 추가 자료

- **전체 가이드:** `RUN_PROCRUSTES_RECONSTRUCTION.md`
- **이론적 배경:** `GUIDE_COMMON_W_RECONSTRUCTION.md`
- **Troubleshooting:** 위 파일들 참고

---

**다음 단계:** 실행 후 결과 분석 및 visualization 생성

**작성일:** 2025-12-19
**업데이트:** Conda activation 확인, 성공 기준 재조정
