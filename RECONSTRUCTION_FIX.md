# Reconstruction 실패 원인 및 해결 방법

## 🔴 문제 진단

### **Reconstruction 결과 (실패):**
```
평균 hit rate: 14.6% (chance: 12.5%)
평균 p-value: 0.523 (유의하지 않음)
```

### **Classification 결과 (성공):**
```
평균 accuracy: 70% (chance: 12.5%)
p-value: 0.001 (매우 유의)
```

→ **Classification은 좋은데 Reconstruction은 실패** = Ground truth hue 문제!

---

## 🔍 근본 원인

### **버그: 라인 1145**
```python
# 원래 Lab hue (지각적으로 균일)
LABEL2HUE_DEG = {
    'color_1': 178.57°,  # Lab 색공간
    'color_2': 310.77°,
    ...
}

# 버그: HSV hue로 덮어쓰기!
LABEL2HUE_DEG = build_label_to_hue_deg(COLOR_RGB)  # HSV 변환
```

### **Lab vs HSV 차이:**
| Color | Lab Hue | HSV Hue | 차이 |
|-------|---------|---------|------|
| color_1 | 178.6° | 173.1° | 5.5° |
| color_2 | 310.8° | 213.0° | **97.8°** ❌ |
| color_3 | 316.1° | 234.4° | **81.7°** ❌ |
| color_4 | 333.9° | 304.1° | 29.7° |
| color_5 | 54.5° | 3.1° | **51.4°** ❌ |
| color_6 | 68.4° | 38.0° | 30.4° |
| color_7 | 130.8° | 88.7° | **42.1°** ❌ |
| color_8 | 153.7° | 137.1° | 16.6° |

→ **최대 97.8° 차이!** 이것이 reconstruction을 망가뜨림

---

## ✅ Solution 1: Lab Hue 사용 (추천 - 가장 정확)

### **수정 완료:**
```python
# 라인 1144-1145 주석 처리
# DO NOT overwrite LABEL2HUE_DEG! Lab hue is the ground truth!
# LABEL2HUE_DEG = build_label_to_hue_deg(COLOR_RGB)  # <-- BUG!
```

### **재실행 방법:**
```bash
# 1. 서버에 업로드
scp naive_analysis.py node2:/scratch/connectome/haba6030/colorBlind/

# 2. SSH 접속
ssh node2
cd /scratch/connectome/haba6030/colorBlind

# 3. Reconstruction cache 삭제 (필수!)
rm hrf_test_outputs/cache_brain/reconstruction_results.joblib
rm hrf_test_outputs/cache_brain/reconstruction_results.csv

# 4. 재실행
sbatch sbatch_naive.sub
```

### **예상 결과:**
```
Hit rate: 40-60% (현재 14.6%에서 개선!)
p-value: <0.05 (유의함)
```

---

## 🔬 Solution 2: Brouwer & Heeger (2009) 방법 복제

원 논문을 참고하여 균등 8분할 사용:

```python
# 균등 8분할 (0°, 45°, 90°, ...)
LABEL2HUE_DEG_UNIFORM = {
    'color_1': 0,
    'color_2': 45,
    'color_3': 90,
    'color_4': 135,
    'color_5': 180,
    'color_6': 225,
    'color_7': 270,
    'color_8': 315,
}
```

**장점:**
- 단순하고 해석 가능
- Brouwer & Heeger와 직접 비교 가능

**단점:**
- 실제 자극 색상과 다름
- 지각적 균일성 보장 안 됨

---

## 📊 Solution 3: bh_anal.py 사용 (FIR model)

`naive_analysis.py` 대신 `bh_anal.py` 사용:

```bash
# bh_anal.py는 FIR (Finite Impulse Response) 사용
# Canonical HRF 대신 더 유연한 HRF 모델링

from bh_anal import BHAnalysisPipeline
pipeline = BHAnalysisPipeline()

# 전체 파이프라인 실행
pipeline.run("design")       # FIR design matrix
pipeline.run("deconv_glm")   # FIR GLM
pipeline.run("roi_build")    # ROI 생성
pipeline.run("extract_roi")  # ROI 데이터 추출
pipeline.run("forward_model")# Forward encoding model
pipeline.run("qc")           # Quality control
```

**장점:**
- Brouwer & Heeger (2009) 논문과 정확히 동일한 방법
- FIR model이 canonical HRF보다 유연
- 이미 테스트된 코드

**단점:**
- 처음부터 다시 실행 필요
- 시간이 오래 걸림 (3-4시간)

---

## 🎯 추천 순서

### **1단계: Solution 1 시도 (10분)**
```bash
# Lab hue 사용 (가장 간단)
scp naive_analysis.py node2:...
ssh node2
rm hrf_test_outputs/cache_brain/reconstruction_*.{joblib,csv}
sbatch sbatch_naive.sub
```

**기대:**
- Hit rate: 40-60%
- p-value: <0.05

### **2단계: 결과 확인**
```bash
# 로그 확인
tail -50 logs/naive_*.out

# Reconstruction 결과 다운로드
scp node2:...cache_brain/reconstruction_results.csv ./
```

### **3단계A: 성공하면**
```
→ V1, V2, V3, V4 ROI로 실행
→ 어느 ROI가 가장 좋은지 비교
```

### **3단계B: 여전히 안 되면**
```
→ Solution 2 시도 (균등 8분할)
→ Solution 3 시도 (bh_anal.py)
```

---

## 📝 기술적 세부사항

### **왜 Lab 색공간이 더 나은가?**

1. **지각적 균일성 (Perceptual Uniformity)**
   - Lab: 색상 간 거리 = 지각적 차이
   - HSV: 색상 간 거리 ≠ 지각적 차이

2. **색상 과학 표준**
   - CIE Lab는 국제 표준
   - 색상 실험의 gold standard

3. **fMRI 연구에 적합**
   - 뇌 반응은 지각적 차이에 반응
   - 물리적 RGB 값이 아님

### **Forward Model 수식:**

```
Training:
  C = f(H)  # Channel response as function of true Lab hue H
  W = argmin ||B - WC||²  # Learn voxel weights

Testing:
  C_hat = (W^T W + λI)^-1 W^T B  # Predict channel response
  H_hat = argmax corr(C_hat, C(h))  # Find closest hue

Hit rate = P(|H_hat - H_true| < 22.5°)
```

**버그의 영향:**
- Training: 잘못된 HSV hue 사용
- Testing: 올바른 Lab hue와 비교
- → Mismatch로 인한 실패!

---

## ✅ 체크리스트

- [x] 버그 확인 (라인 1145)
- [x] Lab hue 값 확인
- [x] HSV vs Lab 차이 측정
- [x] 코드 수정 (라인 1144-1145 주석)
- [ ] 서버에 업로드
- [ ] Cache 삭제
- [ ] 재실행
- [ ] 결과 확인
- [ ] V1-V4 ROI로 확장

---

## 참고 문헌

**Brouwer, G. J., & Heeger, D. J. (2009).** Decoding and reconstructing color from responses in human visual cortex. *Journal of Neuroscience*, 29(44), 13992-14003.

**CIE Lab Color Space:**
- International Commission on Illumination (CIE) 1976
- https://en.wikipedia.org/wiki/CIELAB_color_space
