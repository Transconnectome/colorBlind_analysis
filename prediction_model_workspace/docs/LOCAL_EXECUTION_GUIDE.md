# 로컬 실행 가이드 (비행 후)

## 현재 상황

- ✅ Step 1.3 서버 작업 실행 중 (6시간 소요)
- ⏳ 비행 중 작업 완료 예상
- 📥 착륙 후: 결과 다운로드 → 로컬 분석

---

## 1단계: 서버 작업 완료 확인

### SSH 접속하여 상태 확인

```bash
# 서버 접속
ssh haba6030@node2

# 작업 상태 확인
squeue -u haba6030
```

**예상 출력**:
```
# 작업 완료 시 (empty)
JOBID  PARTITION  NAME  USER  ST  TIME  NODES  NODELIST(REASON)
(아무것도 없음)

# 또는 작업 진행 중
JOBID  PARTITION  NAME           USER      ST  TIME     NODES  NODELIST(REASON)
71234  shared     trial_glm      haba6030  R   3:24:15  1      node4
```

### 결과 파일 생성 확인

```bash
# 생성된 디렉토리 확인
ls -lh /scratch/connectome/haba6030/colorBlind/prediction_model_workspace/results/trial_wise_glm/

# 예상: 40개 디렉토리 (10 subjects × 4 ROIs)
# sub-01_V1/  sub-01_V2/  sub-01_V3/  sub-01_hV4/
# sub-02_V1/  ...
# sub-10_hV4/
```

**완료 기준**: 40개 디렉토리 모두 존재

### 로그 확인 (에러 체크)

```bash
# 각 피험자 완료 상태
grep "completed successfully" /scratch/connectome/haba6030/colorBlind/prediction_model_workspace/logs/trial_glm_sub-*_*.out

# 실패한 작업 확인
grep "failed with exit code" /scratch/connectome/haba6030/colorBlind/prediction_model_workspace/logs/trial_glm_sub-*_*.out
```

**정상 출력**:
```
✅ Subject 01, ROI V1 completed successfully
✅ Subject 01, ROI V2 completed successfully
...
(40개 success 메시지)
```

---

## 2단계: 서버에서 집계 실행 (권장)

**이유**: 서버에 데이터가 이미 있으므로 더 빠름

```bash
# 서버에서 (SSH 접속 상태)
cd /scratch/connectome/haba6030/colorBlind/prediction_model_workspace/scripts

# 집계 스크립트 실행
python aggregate_trial_glm_results.py \
    --input_dir ../results/trial_wise_glm \
    --output_dir ../results/trial_wise_glm

# 예상 소요 시간: 1-2분
```

**생성 파일**:
```
results/trial_wise_glm/
├── trial_glm_detailed.csv    # 전체 결과 테이블
├── trial_glm_summary.png     # 6패널 시각화
└── trial_glm_summary.txt     # 텍스트 리포트
```

---

## 3단계: 결과 다운로드 (로컬로)

### 요약 파일만 다운로드 (빠름, 권장)

```bash
# 로컬 터미널에서 실행
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/prediction_model_workspace/results/

# CSV 다운로드 (핵심 데이터)
scp haba6030@node2:/scratch/connectome/haba6030/colorBlind/prediction_model_workspace/results/trial_wise_glm/trial_glm_detailed.csv ./trial_wise_glm/

# 시각화 다운로드
scp haba6030@node2:/scratch/connectome/haba6030/colorBlind/prediction_model_workspace/results/trial_wise_glm/trial_glm_summary.png ./trial_wise_glm/

# 텍스트 리포트 다운로드
scp haba6030@node2:/scratch/connectome/haba6030/colorBlind/prediction_model_workspace/results/trial_wise_glm/trial_glm_summary.txt ./trial_wise_glm/
```

**예상 파일 크기**:
- CSV: ~50 KB
- PNG: ~500 KB
- TXT: ~5 KB

### 전체 결과 다운로드 (느림, 선택)

```bash
# 40개 디렉토리 전체 (trial_betas.npy 포함)
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/prediction_model_workspace/results/trial_wise_glm ./

# 예상 크기: ~5-10 GB (trial_betas.npy가 큼)
# 예상 시간: 10-30분 (네트워크 속도 의존)
```

**주의**: trial_betas.npy는 나중에 Step 1.4에서 사용하므로 서버에 보관 권장

---

## 4단계: 로컬에서 집계 실행 (선택)

**필요 조건**: 전체 결과 다운로드 완료 (3단계 전체 버전)

### 환경 확인

```bash
# Conda 환경 활성화
conda activate nilearn

# Python 패키지 확인
python -c "import pandas, numpy, matplotlib, seaborn; print('✅ All packages available')"
```

### 집계 스크립트 실행

```bash
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/prediction_model_workspace/scripts

python aggregate_trial_glm_results.py \
    --input_dir ../results/trial_wise_glm \
    --output_dir ../results/trial_wise_glm
```

**출력 예시**:
```
Aggregating trial-wise GLM results...

Found 40 result files

✅ Saved: results/trial_wise_glm/trial_glm_detailed.csv
✅ Saved: results/trial_wise_glm/trial_glm_summary.png

================================================================================
TRIAL-WISE GLM (LS-S) SUMMARY
================================================================================

## Overall Statistics
Total subject-ROI combinations: 40
Subjects: 10
ROIs: 4

## Split-half Reliability (Procrustes)
Overall mean: 0.623 ± 0.145
...
```

---

## 5단계: 결과 해석

### 빠른 확인 (텍스트 리포트)

```bash
# 로컬에서
cat /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/prediction_model_workspace/results/trial_wise_glm/trial_glm_summary.txt

# 핵심 확인 사항:
# 1. Overall mean reliability
# 2. Pass rate (≥0.50)
# 3. Next Steps 섹션 메시지
```

### 시각화 확인

```bash
# PNG 파일 열기
open /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/prediction_model_workspace/results/trial_wise_glm/trial_glm_summary.png
```

**체크 포인트**:
- Panel A: 대부분 막대가 0.50 초록선 위에?
- Panel D: 박스플롯 median이 0.50 위에?
- Panel F: tSNR vs Reliability 양의 상관관계?

### CSV 분석 (상세)

```bash
# Excel이나 Numbers로 열기
open /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/prediction_model_workspace/results/trial_wise_glm/trial_glm_detailed.csv

# 또는 Python으로
python
```

```python
import pandas as pd

df = pd.read_csv('../results/trial_wise_glm/trial_glm_detailed.csv')

# 기본 통계
print(df['reliability_mean'].describe())
print(df.groupby('roi')['reliability_mean'].mean().sort_values(ascending=False))

# 낮은 reliability 케이스
low_rel = df[df['reliability_mean'] < 0.50]
print(f"\n⚠️ Low reliability cases: {len(low_rel)}/{len(df)}")
print(low_rel[['subject', 'roi', 'reliability_mean', 'tsnr_mean']])

# Tier별 비교
tier1 = ['01', '03', '04', '08', '09', '10']
tier2 = ['02', '05']
tier3 = ['06', '07']

df['tier'] = df['subject'].apply(lambda x:
    'Tier1' if x in tier1 else
    'Tier2' if x in tier2 else 'Tier3')

print("\n📊 Reliability by Tier:")
print(df.groupby('tier')['reliability_mean'].agg(['mean', 'std', 'count']))
```

---

## 6단계: 추가 시각화 (선택)

### Per-color Reliability 히트맵

```python
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

df = pd.read_csv('../results/trial_wise_glm/trial_glm_detailed.csv')

# Per-color reliability columns
colors = ['red', 'orange', 'yellow', 'green', 'cyan', 'blue', 'purple', 'magenta']
reliability_cols = [f'reliability_{c}' for c in colors]

# Heatmap
plt.figure(figsize=(10, 12))
sns.heatmap(df[reliability_cols].values,
            xticklabels=colors,
            yticklabels=[f"{row['subject']}-{row['roi']}" for _, row in df.iterrows()],
            cmap='RdYlGn', vmin=0, vmax=1, center=0.5,
            annot=False, cbar_kws={'label': 'Reliability'})
plt.title('Per-color Reliability Heatmap')
plt.xlabel('Color')
plt.ylabel('Subject-ROI')
plt.tight_layout()
plt.savefig('../results/trial_wise_glm/reliability_heatmap.png', dpi=300)
print("✅ Saved: reliability_heatmap.png")
plt.show()
```

### Tier별 비교 박스플롯

```python
tier1 = ['01', '03', '04', '08', '09', '10']
tier2 = ['02', '05']
tier3 = ['06', '07']

df['tier'] = df['subject'].apply(lambda x:
    'Tier1' if x in tier1 else
    'Tier2' if x in tier2 else 'Tier3')

plt.figure(figsize=(12, 5))

# Subplot 1: Reliability by tier
plt.subplot(1, 2, 1)
sns.boxplot(data=df, x='tier', y='reliability_mean', hue='roi', order=['Tier1', 'Tier2', 'Tier3'])
plt.axhline(0.50, color='green', linestyle='--', label='Target')
plt.title('Reliability by Preprocessing Tier')
plt.xlabel('Tier (Preprocessing Quality)')
plt.ylabel('Reliability')
plt.legend()

# Subplot 2: tSNR by tier
plt.subplot(1, 2, 2)
sns.boxplot(data=df, x='tier', y='tsnr_mean', hue='roi', order=['Tier1', 'Tier2', 'Tier3'])
plt.title('tSNR by Preprocessing Tier')
plt.xlabel('Tier (Preprocessing Quality)')
plt.ylabel('Temporal SNR')
plt.legend()

plt.tight_layout()
plt.savefig('../results/trial_wise_glm/tier_comparison.png', dpi=300)
print("✅ Saved: tier_comparison.png")
plt.show()
```

### tSNR vs Reliability 상관관계

```python
import scipy.stats as stats

corr, pval = stats.pearsonr(df['tsnr_mean'], df['reliability_mean'])

plt.figure(figsize=(8, 6))
for roi in df['roi'].unique():
    df_roi = df[df['roi'] == roi]
    plt.scatter(df_roi['tsnr_mean'], df_roi['reliability_mean'],
                label=roi, s=100, alpha=0.7)

plt.xlabel('Temporal SNR', fontsize=12)
plt.ylabel('Reliability (Procrustes)', fontsize=12)
plt.title(f'tSNR vs Reliability\n(r = {corr:.3f}, p = {pval:.4f})', fontsize=14)
plt.axhline(0.50, color='green', linestyle='--', alpha=0.5, label='Target reliability')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('../results/trial_wise_glm/tsnr_reliability_correlation.png', dpi=300)
print("✅ Saved: tsnr_reliability_correlation.png")
plt.show()
```

---

## 7단계: 결과 기반 의사결정

### 자동 판단 스크립트

```python
import pandas as pd

df = pd.read_csv('../results/trial_wise_glm/trial_glm_detailed.csv')

overall_mean = df['reliability_mean'].mean()
pass_rate = (df['reliability_mean'] >= 0.50).sum() / len(df)
v1_mean = df[df['roi'] == 'V1']['reliability_mean'].mean()

print("=" * 60)
print("DECISION SUMMARY")
print("=" * 60)
print(f"Overall mean reliability: {overall_mean:.3f}")
print(f"Pass rate (≥0.50): {pass_rate*100:.1f}% ({(df['reliability_mean'] >= 0.50).sum()}/{len(df)})")
print(f"V1 mean reliability: {v1_mean:.3f}")
print()

# Decision logic
if overall_mean >= 0.60:
    decision = "✅ EXCELLENT"
    action = "즉시 Step 1.4로 진행, 모든 ROI/피험자 사용"
    priority = "HIGH"
elif overall_mean >= 0.50:
    decision = "✅ GOOD"
    action = "Step 1.4로 진행, 선택적 ROI 사용 (V1>V2>V3>hV4)"
    priority = "MEDIUM"
elif overall_mean >= 0.30:
    decision = "⚠️ ACCEPTABLE"
    action = "V1, V2만 Step 1.4, V3/hV4 파라미터 재조정"
    priority = "LOW"
else:
    decision = "❌ POOR"
    action = "파라미터 grid search 필요, 방법론 재검토"
    priority = "CRITICAL"

print(f"Decision: {decision}")
print(f"Priority: {priority}")
print()
print("Recommended Action:")
print(f"  {action}")
print()

# ROI recommendations
print("ROI-specific recommendations:")
for roi in ['V1', 'V2', 'V3', 'hV4']:
    roi_mean = df[df['roi'] == roi]['reliability_mean'].mean()
    if roi_mean >= 0.50:
        status = "✅ Use"
    elif roi_mean >= 0.30:
        status = "⚠️ Caution"
    else:
        status = "❌ Exclude"
    print(f"  {roi}: {roi_mean:.3f} → {status}")

print("=" * 60)

# Save decision
with open('../results/trial_wise_glm/DECISION.txt', 'w') as f:
    f.write(f"Decision: {decision}\n")
    f.write(f"Action: {action}\n")
    f.write(f"Overall mean: {overall_mean:.3f}\n")
    f.write(f"Pass rate: {pass_rate*100:.1f}%\n")

print("\n✅ Decision saved to: DECISION.txt")
```

---

## 실행 타임라인 요약

### 착륙 후 (30분 이내)

1. **서버 접속** (5분)
   ```bash
   ssh haba6030@node2
   squeue -u haba6030  # 완료 확인
   ls -lh /scratch/.../trial_wise_glm/  # 40개 디렉토리 확인
   ```

2. **서버에서 집계** (2분)
   ```bash
   cd /scratch/.../scripts
   python aggregate_trial_glm_results.py
   ```

3. **요약 파일 다운로드** (1분)
   ```bash
   # 로컬에서
   scp haba6030@node2:/scratch/.../trial_glm_summary.* ./
   scp haba6030@node2:/scratch/.../trial_glm_detailed.csv ./
   ```

4. **빠른 확인** (5분)
   ```bash
   cat trial_glm_summary.txt  # 텍스트 확인
   open trial_glm_summary.png  # 시각화 확인
   ```

5. **의사결정** (10분)
   - Python 스크립트로 자동 판단
   - 또는 RESULTS_INTERPRETATION_GUIDE.md 참조

### 선택 사항 (추가 1시간)

6. **전체 결과 다운로드** (20분)
   - trial_betas.npy 포함 (5-10 GB)

7. **추가 시각화** (20분)
   - 히트맵, Tier 비교, 상관관계 등

8. **상세 분석** (20분)
   - 색상별 패턴, 피험자별 비교 등

---

## 문제 해결

### 문제 1: 일부 결과 누락

```bash
# 서버에서 확인
ls /scratch/.../trial_wise_glm/ | wc -l
# 예상: 40 (+ 3개 summary 파일)

# 누락된 subject-ROI 찾기
for sub in 01 02 03 04 05 06 07 08 09 10; do
  for roi in V1 V2 V3 hV4; do
    if [ ! -d "/scratch/.../trial_wise_glm/sub-${sub}_${roi}" ]; then
      echo "Missing: sub-${sub}_${roi}"
    fi
  done
done
```

**조치**:
- 로그 확인하여 실패 원인 파악
- 해당 subject-ROI만 재실행

### 문제 2: 집계 스크립트 에러

```bash
# 에러 예시: "No result files found"
python aggregate_trial_glm_results.py --input_dir ../results/trial_wise_glm

# 원인: quality_metrics.json 파일 찾지 못함
# 확인:
ls ../results/trial_wise_glm/sub-01_V1/quality_metrics.json
```

**조치**:
- 파일 존재 확인
- 경로 수정 (--input_dir)

### 문제 3: 로컬 Python 환경 문제

```bash
# 패키지 누락
conda activate nilearn
pip install seaborn  # 시각화용
pip install scipy    # 통계용
```

---

## 체크리스트

### 비행 후 필수 (30분)

- [ ] 서버 작업 완료 확인 (`squeue`)
- [ ] 40개 디렉토리 생성 확인 (`ls -lh`)
- [ ] 서버에서 집계 실행
- [ ] 요약 파일 다운로드 (CSV, PNG, TXT)
- [ ] trial_glm_summary.txt 읽고 전체 파악
- [ ] trial_glm_summary.png 보고 시각적 확인
- [ ] 의사결정 (PROCEED vs ADJUST vs REDO)

### 선택 사항 (1시간)

- [ ] 전체 결과 다운로드 (trial_betas.npy)
- [ ] 로컬에서 집계 재실행 (검증)
- [ ] 추가 시각화 (히트맵, Tier 비교)
- [ ] 상세 분석 (색상별, 피험자별)
- [ ] DECISION.txt 생성 (자동 판단)

---

## 다음 단계 준비

### 결과가 Good 이상 (≥0.50)

**즉시 준비**:
```bash
# Step 1.4 스크립트 확인
ls prediction_model_workspace/scripts/
# 예상: 03_hyperalignment.py (아직 없음, 작성 필요)

# 문헌 확인
# - analysis/future_phase1_hyperalignment/COMPARISON.md
# - prediction_model_workspace/docs/PHASE1_HYPERALIGNMENT.md
```

**작업 예상**:
- Hyperalignment vs SRM 둘 다 구현 (1일)
- V1부터 테스트 (4시간)
- 평가 및 Winner 선택 (4시간)

### 결과가 Acceptable (0.30-0.49)

**선택적 진행**:
- V1, V2만으로 Step 1.4 (1일)
- V3, hV4 파라미터 재조정 (1일)

### 결과가 Poor (<0.30)

**문제 진단**:
- Step 1.1 실행 (데이터 완전성)
- 파라미터 grid search (smoothing, confounds, HRF)
- 방법론 재검토 (문헌 조사)

---

**Last updated**: 2026-01-10
**Expected execution**: 착륙 후 (6-8시간 후)
**Estimated time**: 30분 (필수) + 1시간 (선택)
