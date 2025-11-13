# 🚀 Complete ROI → Analysis Workflow

**목적:** ROI 제작부터 분석까지 전체 프로세스 한눈에 보기
**타겟:** Pilot subject (sub-P01) → Test subjects (sub-01~04)

---

## 📝 Step-by-Step Workflow

### Step 0: 준비 및 확인 (5분)

```bash
# 1. 로컬에서 최신 코드 업로드
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis

scp roi_build.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/
scp visualize_roi_overlay.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/
scp fir_reconstruction.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/
scp config.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/

# 2. 서버 접속
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind
conda activate nilearn

# 3. 데이터 존재 확인
# Wang atlas
ls ProbAtlas_v4/subj_vol_all/perc_VTPM_vol_roi*.nii.gz | wc -l
# 예상: 28개 파일

# BOLD 이미지 (res-2)
ls /storage/connectome/haba6030/fmriprep_out/sub-P01/func/*res-2*preproc* | head -3

# Event 파일
ls /storage/connectome/haba6030/colorBlind_dataOct/sub-P01/func/*events.tsv
```

**✅ 체크포인트:**
- [ ] Wang atlas 파일 28개 존재
- [ ] BOLD 이미지 6개 run 존재 (res-2)
- [ ] Event 파일 6개 run 존재

---

### Step 1: ROI 생성 (5-10분)

```bash
# roi_build.py 실행
python roi_build.py
```

**생성되는 파일:**
```
derivatives/sub-P01/roi/
├── sub-P01_V1_mask.nii.gz
├── sub-P01_V2_mask.nii.gz
├── sub-P01_V3_mask.nii.gz
└── sub-P01_hV4_mask.nii.gz
```

**프로세스:**
1. Wang atlas에서 각 ROI 파일 로드 (ventral/dorsal, left/right)
2. Probability > 50% threshold 적용
3. Left + Right hemisphere 합치기
4. Ventral + Dorsal 합치기
5. **Resample to res-2 BOLD space** (nearest neighbor)
6. Brain mask intersection (optional)
7. Subject MNI ROI intersection (optional)

**확인:**
```bash
# 파일 생성 확인
ls -lh derivatives/sub-P01/roi/

# Voxel 수 확인
for roi in V1 V2 V3 hV4; do
    echo "=== ${roi} ==="
    fslstats derivatives/sub-P01/roi/sub-P01_${roi}_mask.nii.gz -V
done
```

**예상 Voxel 수:**
- V1: 190-250
- **V2: 280-350** (가장 중요!)
- V3: 180-230
- hV4: 100-150

---

### Step 2: Overlay 시각화 및 검증 ⭐ **가장 중요!**

```bash
# 시각화 실행
python visualize_roi_overlay.py
```

**생성되는 파일:**
```
derivatives/sub-P01/roi/qc_figures/
├── V1_overlay.png          # 개별 ROI overlay
├── V2_overlay.png
├── V3_overlay.png
├── hV4_overlay.png
├── all_rois_overlay.png    # 모든 ROI 한눈에
└── glass_brain_view.png    # Glass brain view
```

**시각적 검증 체크리스트:**
- [ ] ✅ ROI가 **후두엽(occipital cortex)**에 위치 (뒤통수 쪽)
- [ ] ✅ ROI가 **좌우 대칭**
- [ ] ✅ ROI가 **뇌 안에** 위치 (뇌 밖으로 안 튀어나감)
- [ ] ✅ ROI가 **BOLD 활성화 영역과 겹침**
- [ ] ✅ ROI 경계가 명확하고 깔끔함

**이미지 다운로드 (로컬에서):**
```bash
# Mac 터미널에서
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis

scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/derivatives/sub-P01/roi/qc_figures/ ./roi_qc_check/
```

**이미지 확인 후:**
- ✅ 모두 정상 → **Step 3으로 진행**
- ❌ 문제 발견 → **Step 2.1으로**

---

### Step 2.1: 문제 발견 시 조치 (Optional)

#### 문제 1: Voxel 수가 너무 적음 (<50)
```python
# roi_build.py 수정 (line 110)
# 변경 전:
part_mask = part_data > 50

# 변경 후:
part_mask = part_data > 25  # Threshold 낮춤
```

#### 문제 2: ROI가 뇌 밖으로 튀어나감
```python
# roi_build.py에서 brain mask intersection이 활성화되어 있는지 확인
# Line 127-143: Brain mask intersection 코드가 실행되어야 함

# Brain mask 경로 확인
ls output/pilot/sub-P01/anat/*brain_mask.nii.gz
```

#### 문제 3: EPI overlap이 낮음 (<80%)
→ Brain mask intersection 필수
→ config.py에서 brain_mask_path 확인

**수정 후 다시 실행:**
```bash
# ROI 재생성
python roi_build.py

# 시각화 재확인
python visualize_roi_overlay.py
```

---

### Step 3: V2 ROI 테스트 실행 (10-15분) ⭐

```bash
# V2 ROI만 먼저 테스트 (가장 성공 확률 높음)
sbatch --export=ROI=V2,USE_PCA=1,N_COMPONENTS=20 run_fir_reconstruction_single.sbatch

# 또는 직접 실행 (디버깅용)
python fir_reconstruction.py --roi V2 --use-pca --n-components 20
```

**실시간 모니터링:**
```bash
# Job 상태
squeue -u haba6030

# 로그 확인
tail -f logs/fir_recon_*.out

# 또는 직접 실행한 경우 바로 출력 확인
```

**예상 출력:**
```
[INFO] Loading V2 ROI mask...
[INFO] ROI voxels: 310
[INFO] Running FIR GLM...
[INFO] Selecting best 200 voxels...
[INFO] Applying PCA (20 components)...
[INFO] Training classifier...
[INFO] Classification accuracy: 100.0%
[SUCCESS] Reconstruction error: 18.5°
[SUCCESS] p-value < 0.001
```

---

### Step 4: 결과 확인 및 검증

```bash
# 결과 파일 위치
cd derivatives/sub-P01/fir_reconstruction/V2/

# Summary 확인
cat summary.csv
```

**예상 summary.csv:**
```csv
ROI,N_voxels,Use_PCA,N_components,Classification_accuracy,Reconstruction_error_deg
V2,310,True,20,1.0,18.5
```

**성공 기준:**
- ✅ Classification_accuracy = 1.0 (100%)
- ✅ Reconstruction_error < 30°
- ✅ log.txt에 ERROR 없음

**결과 다운로드 (로컬에서):**
```bash
# Mac 터미널
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis

scp haba6030@node2:/scratch/connectome/haba6030/colorBlind/derivatives/sub-P01/fir_reconstruction/V2/summary.csv ./
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/derivatives/sub-P01/fir_reconstruction/V2/figures/ ./results_v2/
```

---

### Step 5: 전체 ROI 병렬 실행 (10-15분)

**V2가 성공했다면:**
```bash
# 모든 ROI 병렬 실행
sbatch run_fir_reconstruction_parallel.sbatch

# 모니터링
squeue -u haba6030
watch -n 5 squeue -u haba6030  # 5초마다 갱신
```

**완료 후 결과 합치기:**
```bash
# 모든 ROI summary 합치기
cat derivatives/sub-P01/fir_reconstruction/*/summary.csv > all_roi_results.csv

# 확인
cat all_roi_results.csv
```

**예상 결과:**
```csv
ROI,N_voxels,Use_PCA,N_components,Classification_accuracy,Reconstruction_error_deg
V1,220,True,20,1.0,15.2
V2,310,True,20,1.0,18.5
V3,200,True,20,1.0,22.3
hV4,120,True,20,1.0,28.7
```

---

### Step 6: 결과 분석 및 비교

```python
# Python에서 분석 (로컬 또는 서버)
import pandas as pd

# 결과 로드
results = pd.read_csv('all_roi_results.csv')

# 요약 통계
print(results)

# 최고 성능 ROI
best_roi = results.loc[results['Reconstruction_error_deg'].idxmin()]
print(f"\nBest ROI: {best_roi['ROI']}")
print(f"  Classification: {best_roi['Classification_accuracy']*100:.1f}%")
print(f"  Reconstruction: {best_roi['Reconstruction_error_deg']:.1f}°")

# 모든 ROI 평가
print("\n=== Performance Summary ===")
for idx, row in results.iterrows():
    roi = row['ROI']
    acc = row['Classification_accuracy']
    err = row['Reconstruction_error_deg']

    acc_status = "✅" if acc > 0.9 else "⚠️"
    err_status = "✅" if err < 30 else "⚠️"

    print(f"{roi:6s}: Classification {acc_status} {acc*100:5.1f}%  |  Reconstruction {err_status} {err:5.1f}°")
```

---

## 🔧 Troubleshooting

### 문제: ROI 생성 실패
```
[ERROR] Could not create mask for V2
```
**해결:** Wang atlas 파일 경로 확인
```bash
ls ProbAtlas_v4/subj_vol_all/perc_VTPM_vol_roi3*.nii.gz
```

### 문제: Classification 성능 낮음 (< 70%)
```
Classification accuracy: 0.45
```
**가능한 원인:**
1. ROI가 잘못된 영역 (overlay 확인!)
2. PCA 미사용 (USE_PCA=1 확인)
3. Lab hue 값 오류 (config.py 확인)

**해결:**
```bash
# config.py 확인
python -c "from config import cfg; print(cfg.SUB_ID)"

# PCA 사용 확인
grep "USE_PCA" run_fir_reconstruction_single.sbatch
```

### 문제: Reconstruction error 높음 (> 50°)
```
Reconstruction error: 75.3°
```
**가능한 원인:**
1. Voxel 수가 너무 적거나 많음
2. ROI에 노이즈 많음 (zero-value voxel)
3. Forward model regularization 문제

**해결:**
1. Overlay 이미지 재확인
2. Voxel 수 확인 (280-350이 optimal for V2)
3. Brain mask intersection 적용

---

## 📊 Expected Performance (From Previous Success)

| ROI | Voxels | Classification | Reconstruction | Status |
|-----|--------|---------------|----------------|--------|
| **V2** | **310** | **100%** | **<20°** | 🏆 **Best** |
| V1 | 220 | 100% | <25° | ✅ Excellent |
| V3 | 200 | 100% | <30° | ✅ Good |
| hV4 | 120 | 100% | <35° | ✅ Good |

---

## ✅ Final Checklist

### ROI 제작
- [ ] Wang atlas 파일 확인
- [ ] roi_build.py 실행 성공
- [ ] 모든 ROI mask 파일 생성 (V1, V2, V3, hV4)
- [ ] Voxel 수가 예상 범위 내
- [ ] Overlay 시각화 생성
- [ ] Overlay 이미지 검증 완료 (후두엽, 대칭, 뇌 내부)

### 분석 실행
- [ ] V2 테스트 실행 성공
- [ ] V2 classification ~100%
- [ ] V2 reconstruction <30°
- [ ] 전체 ROI 병렬 실행
- [ ] 모든 ROI 결과 수집

### 결과 검증
- [ ] 모든 ROI classification > 90%
- [ ] 모든 ROI reconstruction < 40°
- [ ] 결과 다운로드 완료
- [ ] 시각화 자료 생성

---

## 🎯 Success Criteria

### Minimum (최소 목표)
- ✅ V2 ROI에서 100% classification
- ✅ V2 ROI에서 <30° reconstruction
- ✅ p < 0.05 statistical significance

### Optimal (최적 목표)
- ✅ 모든 ROI에서 >90% classification
- ✅ 모든 ROI에서 <35° reconstruction
- ✅ Overlay 이미지 완벽히 정렬

### Stretch (도전 목표)
- ✅ 모든 ROI에서 100% classification
- ✅ V1/V2에서 <20° reconstruction
- ✅ Leave-one-color-out 검증 통과

---

## 📞 When to Ask for Help

### 즉시 도움 요청:
- ❌ ROI가 뇌 밖에 위치
- ❌ Voxel 수 < 50
- ❌ Classification < 30%
- ❌ Reconstruction > 90° (chance level)

### 검토 필요:
- ⚠️ Voxel 수가 예상 범위 밖
- ⚠️ Classification 60-80%
- ⚠️ Reconstruction 30-50°

---

**작성일:** 2025-11-09
**상태:** Ready to execute
**예상 소요 시간:** 총 30-45분

**한 단계씩 차근차근 진행하세요! 각 단계마다 확인하면서 가면 됩니다! 💪**
