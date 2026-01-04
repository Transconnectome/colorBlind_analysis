# CVD vs non-CVD 분석 전체 워크플로우

## 빠른 시작 (Quick Start)

### 1단계: Non-CVD 그룹 분석 (이미 완료 예정)
```bash
scp group_level_analysis_comprehensive.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/
scp run_group_level_comprehensive.sbatch haba6030@node2:/scratch/connectome/haba6030/colorBlind/

ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind
sbatch run_group_level_comprehensive.sbatch
```

### 2단계: CVD 개별 분석
```bash
scp individual_comprehensive_analysis.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/
scp run_cvd_individual_analysis.sbatch haba6030@node2:/scratch/connectome/haba6030/colorBlind/

ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind
sbatch run_cvd_individual_analysis.sbatch
```

### 3단계: CVD vs non-CVD 비교
```bash
scp compare_cvd_vs_noncvd.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/
scp run_cvd_comparison.sbatch haba6030@node2:/scratch/connectome/haba6030/colorBlind/

ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind
sbatch run_cvd_comparison.sbatch
```

### 4단계: 결과 다운로드
```bash
# 로컬 머신에서
./download_all_cvd_results.sh
```

---

## 생성된 파일 목록

### Python Scripts
1. **`individual_comprehensive_analysis.py`** - CVD 피험자 개별 분석
   - Run-level statistical tests (N_runs=6)
   - LORO-CV (Leave-One-Run-Out)
   - 28 pairwise contrasts
   - PCA analysis

2. **`compare_cvd_vs_noncvd.py`** - CVD vs non-CVD 비교
   - Pairwise contrast comparison
   - Performance comparison
   - Union voxels comparison
   - Visualization

### SBATCH Scripts
1. **`run_cvd_individual_analysis.sbatch`** - CVD 개별 분석 실행
   - Array job: 3 subjects × 4 ROIs = 12 jobs
   - Parallel execution

2. **`run_cvd_comparison.sbatch`** - 비교 분석 실행
   - Array job: 4 ROIs
   - Depends on: group-level + individual results

### Documentation
1. **`RUN_CVD_COMPARISON_GUIDE.md`** - 상세 실행 가이드
2. **`CVD_ANALYSIS_WORKFLOW.md`** - 전체 워크플로우 (이 파일)

---

## 파일 업로드 체크리스트

```bash
# Python scripts
[ ] individual_comprehensive_analysis.py
[ ] compare_cvd_vs_noncvd.py
[ ] group_level_analysis_comprehensive.py (이미 완료?)

# SBATCH scripts
[ ] run_cvd_individual_analysis.sbatch
[ ] run_cvd_comparison.sbatch
[ ] run_group_level_comprehensive.sbatch (이미 완료?)

# 전체 업로드 커맨드
scp individual_comprehensive_analysis.py \
    compare_cvd_vs_noncvd.py \
    run_cvd_individual_analysis.sbatch \
    run_cvd_comparison.sbatch \
    haba6030@node2:/scratch/connectome/haba6030/colorBlind/
```

---

## 실행 순서

### Step 0: 준비 (사전 요구사항)
```bash
# Baseline 분석 완료 확인
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind

# CVD 피험자 baseline 결과 확인
for sub in 08 09 10; do
    for roi in V1 V2 V3 hV4; do
        ls derivatives/BH2009_deoblique_v2/baseline32_deob_determin/sm*_sub-${sub}_${roi}_*/amplitudes_z.npy
    done
done
```

### Step 1: Non-CVD 그룹 분석
```bash
# 이미 완료되었거나 실행 중이면 스킵
sbatch run_group_level_comprehensive.sbatch

# 상태 확인
squeue -u haba6030 | grep group_comprehensive

# 완료 후 결과 확인
ls derivatives/group_level/baseline32_deob_determin/*/comprehensive/performance/classification_results.csv
```

**예상 시간**: ~45분 (4 ROIs parallel)

**다음 단계 조건**:
```bash
# 4개 ROI 모두 완료
ls derivatives/group_level/baseline32_deob_determin/{V1,V2,V3,hV4}/comprehensive/statistics/union_voxels.npz
```

### Step 2: CVD 개별 분석
```bash
sbatch run_cvd_individual_analysis.sbatch

# 상태 확인
squeue -u haba6030 | grep cvd_individual

# 로그 실시간 확인
tail -f logs/cvd_individual/cvd_individual_*.out

# 완료 후 결과 확인
ls derivatives/individual_comprehensive/baseline32_deob_determin/sub-*/*/performance/classification_results.csv
```

**예상 시간**: ~15분 (12 jobs parallel)

**다음 단계 조건**:
```bash
# 3 subjects × 4 ROIs = 12개 모두 완료
ls derivatives/individual_comprehensive/baseline32_deob_determin/sub-{08,09,10}/{V1,V2,V3,hV4}/statistics/union_voxels.npz
```

### Step 3: CVD vs non-CVD 비교
```bash
sbatch run_cvd_comparison.sbatch

# 상태 확인
squeue -u haba6030 | grep cvd_comparison

# 완료 후 결과 확인
ls derivatives/cvd_comparison/baseline32_deob_determin/*/statistics/pairwise_comparison.csv
```

**예상 시간**: ~5분 (4 ROIs parallel)

**결과**:
```bash
# 4개 ROI 각각
derivatives/cvd_comparison/baseline32_deob_determin/{V1,V2,V3,hV4}/
├── statistics/pairwise_comparison.csv
├── performance/performance_summary.csv
└── figures/
    ├── pairwise_contrast_comparison.png
    ├── performance_comparison.png
    └── union_voxels_comparison.png
```

---

## 결과 다운로드

### 방법 1: 전체 다운로드
```bash
# 로컬 머신에서
TIMESTAMP="baseline32_deob_determin"

# CVD 개별 분석
mkdir -p results_cvd
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/derivatives/individual_comprehensive/$TIMESTAMP/ \
    ./results_cvd/

# CVD 비교
mkdir -p results_cvd_comparison
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/derivatives/cvd_comparison/$TIMESTAMP/ \
    ./results_cvd_comparison/
```

### 방법 2: 선택적 다운로드 (핵심 파일만)
```bash
# 비교 결과 CSV
for roi in V1 V2 V3 hV4; do
    scp haba6030@node2:/scratch/connectome/haba6030/colorBlind/derivatives/cvd_comparison/$TIMESTAMP/$roi/statistics/pairwise_comparison.csv \
        ./results/pairwise_${roi}.csv

    scp haba6030@node2:/scratch/connectome/haba6030/colorBlind/derivatives/cvd_comparison/$TIMESTAMP/$roi/performance/performance_summary.csv \
        ./results/performance_${roi}.csv
done

# 비교 Figures
for roi in V1 V2 V3 hV4; do
    scp haba6030@node2:/scratch/connectome/haba6030/colorBlind/derivatives/cvd_comparison/$TIMESTAMP/$roi/figures/pairwise_contrast_comparison.png \
        ./figures/pairwise_${roi}.png

    scp haba6030@node2:/scratch/connectome/haba6030/colorBlind/derivatives/cvd_comparison/$TIMESTAMP/$roi/figures/performance_comparison.png \
        ./figures/performance_${roi}.png
done
```

---

## 핵심 결과 파일

### 1. Pairwise Comparison (가장 중요!)
**파일**: `cvd_comparison/{ROI}/statistics/pairwise_comparison.csv`

**내용**: 28개 색상 쌍에 대한 non-CVD vs CVD 비교

**컬럼**:
- `pair_name`: C1_vs_C2, C1_vs_C3, ... (28 pairs)
- `noncvd_mean_abs_t`: Non-CVD 그룹 평균 |t|
- `noncvd_sig_pct`: Non-CVD 유의미한 voxel %
- `cvd08_mean_abs_t`: CVD sub-08 평균 |t|
- `cvd08_sig_pct`: CVD sub-08 유의미한 voxel %
- `cvd09_*`, `cvd10_*`: 다른 CVD 피험자들

**분석**:
```python
import pandas as pd

# V1 결과 로드
df = pd.read_csv('pairwise_V1.csv')

# Deficit 계산 (non-CVD - CVD)
df['cvd_mean_sig_pct'] = df[['cvd08_sig_pct', 'cvd09_sig_pct', 'cvd10_sig_pct']].mean(axis=1)
df['deficit'] = df['noncvd_sig_pct'] - df['cvd_mean_sig_pct']

# 가장 큰 deficit을 보이는 pairs
print(df.nlargest(5, 'deficit')[['pair_name', 'noncvd_sig_pct', 'cvd_mean_sig_pct', 'deficit']])
```

### 2. Performance Summary
**파일**: `cvd_comparison/{ROI}/performance/performance_summary.csv`

**내용**:
```csv
group,classification_acc_mean,classification_acc_std,reconstruction_error_mean,reconstruction_error_std
non-CVD (N=6),0.69,0.03,27.7,2.8
CVD sub-08,0.48,0.08,42.3,5.1
CVD sub-09,0.51,0.07,39.8,4.6
CVD sub-10,0.45,0.09,45.2,6.2
```

### 3. Visualization
**파일**: `cvd_comparison/{ROI}/figures/pairwise_contrast_comparison.png`

**구조**: 28 panels (7 rows × 4 columns)
- 각 panel = 하나의 색상 쌍
- X축: non-CVD, CVD-08, CVD-09, CVD-10
- Y축: % Significant voxels
- 파란색: non-CVD, 빨강계열: CVD

**해석**:
- CVD 막대가 낮음 → 그 색상 쌍 구별 어려움
- 특히 Red-Green pairs 확인

---

## 예상 결과 및 해석

### V1 (Early Visual Cortex)
**예상**:
- 색상 정보: 약함
- CVD deficit: 작음 (20-30% reduction)
- Red-Green pairs: 약간의 차이

### V4/hV4 (Color-selective Areas)
**예상**:
- 색상 정보: 강함
- CVD deficit: 큼 (40-60% reduction)
- Red-Green pairs: **명확한 차이**

**예시 (V4, Red vs Green)**:
```
non-CVD: 45% significant voxels
CVD-08:  15% (66% reduction)
CVD-09:  18% (60% reduction)
CVD-10:  12% (73% reduction)
```

### Performance
**예상**:
```
             | Classification | Reconstruction
-------------|----------------|---------------
non-CVD (V4) | 68-72%        | 25-30°
CVD (V4)     | 45-55%        | 40-50°
Deficit      | ~20%          | ~20°
```

---

## Troubleshooting

### 문제 1: Array job 일부만 완료
```bash
# 실패한 job 확인
sacct -j JOBID --format=JobID,State,ExitCode

# 특정 array index 재실행
sbatch --array=3,7,11 run_cvd_individual_analysis.sbatch
```

### 문제 2: 결과 파일 없음
```bash
# CVD baseline 데이터 확인
ls derivatives/BH2009_deoblique_v2/baseline32_deob_determin/sm*_sub-08_*/amplitudes_z.npy

# 없으면 baseline 먼저 실행 필요
```

### 문제 3: Union voxels 너무 적음
```bash
# T-threshold 조정
# individual_comprehensive_analysis.py 실행 시:
--t-threshold 2.5  # 원래 3.0 → 2.5로 낮춤
```

---

## 다음 단계: 논문 Figure 준비

### Figure 1: 전체 비교 (Main Figure)
**Panel A**: V1 pairwise contrasts
**Panel B**: V4 pairwise contrasts (가장 중요)
**Panel C**: Performance comparison (4 ROIs)
**Panel D**: Red-Green pair across ROIs

### Figure 2: Individual CVD 상세
**Panel A-C**: CVD sub-08, 09, 10 각각의 pairwise patterns
**Panel D**: Confusion matrices

### Supplementary
- 모든 ROI의 full pairwise grids
- PCA analysis
- Per-run performance

---

## 체크리스트

### 분석 실행
- [ ] Non-CVD 그룹 분석 완료
- [ ] CVD 개별 분석 완료 (sub-08, 09, 10 × 4 ROIs)
- [ ] CVD vs non-CVD 비교 완료 (4 ROIs)

### 결과 확인
- [ ] Pairwise comparison CSV (4 ROIs)
- [ ] Performance summary CSV (4 ROIs)
- [ ] Visualization PNG (4 ROIs × 3 figures)

### 해석
- [ ] Red-Green pairs에서 CVD deficit 확인
- [ ] V4에서 가장 큰 차이 확인
- [ ] CVD 개인차 확인 (sub-08 vs 09 vs 10)

### 논문
- [ ] Main figure 준비
- [ ] Supplementary figure 준비
- [ ] Statistics table 준비
- [ ] Methods 작성

---

## 요약

1. **Non-CVD**: 6명 그룹 분석 (subject-level variance, |t|>5)
2. **CVD**: 3명 개별 분석 (run-level variance, |t|>3)
3. **비교**: 28 pairwise contrasts, performance, union voxels
4. **핵심**: Red-Green pairs에서 CVD deficit
5. **V4**: 가장 명확한 차이 예상

전체 소요 시간: ~1시간 (parallel 실행)
- Group-level: ~45분
- Individual: ~15분
- Comparison: ~5분
