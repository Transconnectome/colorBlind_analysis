# Drift Processing Comparison Guide

## 🎯 실험 목적

**핵심 질문:** 왜 run-to-run reliability가 낮은가? (현재 ~0.02)

**가설:** Drift 처리 (highpass filter 또는 cosine regressors)가 신호를 제거하고 있음

**검증 방법:** Baseline32처럼 drift 처리를 **전혀 하지 않은** 조건 테스트

## 📊 실험 설계

### 4가지 Drift 전략

| Condition | Highpass | Drift Regressor | Motion Confounds | 설명 |
|-----------|----------|-----------------|------------------|------|
| **D0+M0** | **None** | **None** | None | **Baseline32 재현** ← 가장 중요! |
| **D1+M0** | 0.01 Hz | None | None | Highpass filter 효과 |
| **D2+M0** | None | Cosine | None | Cosine regressor 효과 |
| **D2+M1** | None | Standard | 6DOF+Tissue+Cosine | Full confounds |

**총 16 jobs**: 1 subject (sub-01) × 4 ROIs × 4 conditions

### 예상 결과

```
Condition    Run Correlation    해석
---------    ---------------    --------------------------------
D0+M0        ~0.7              ✅ Baseline32와 일치 → 문제는 drift!
D0+M0        ~0.3              ⚠️  부분적 개선 → drift + 다른 요인
D0+M0        ~0.02             ❌ 실패 → 문제는 drift가 아님

D1+M0        < D0              Highpass가 signal 손실 유발
D2+M0        < D0              Cosine이 signal 손실 유발
D2+M1        ? D2              Motion confounds 효과 불명확
```

## 🚀 실행 방법

### 1. 파일 업로드

```bash
# 1개 명령으로 업로드
scp analysis/phase1_preprocess_decoding/{fir_reconstruction_BH2009_system_clean.py,drift_comparison.sbatch,analyze_drift_results.py} haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/
```

### 2. 서버 실행

```bash
# SSH 접속
ssh haba6030@node2

# 작업 디렉토리
cd /scratch/connectome/haba6030/colorBlind

# sbatch 실행
sbatch analysis/phase1_preprocess_decoding/drift_comparison.sbatch

# 모니터링
squeue -u haba6030
watch -n 2 squeue -u haba6030
```

### 3. 진행 확인

```bash
# 로그 실시간 확인
tail -f analysis/phase1_preprocess_decoding/logs/drift_*.out

# D0+M0 조건 확인 (가장 중요!)
grep -A5 "D0+M0_NoDrift" analysis/phase1_preprocess_decoding/logs/drift_*.out

# Run correlation 빠른 체크
grep "Run correlation" analysis/phase1_preprocess_decoding/logs/drift_*.out
```

### 4. 결과 다운로드

```bash
# 로컬에서 실행
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis

# 결과 다운로드 (drift 조건만)
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/method3_header_mi/results/factorial_experiment/ analysis/phase1_preprocess_decoding/results/
```

### 5. 분석

```bash
# 로컬 분석 스크립트
python analysis/phase1_preprocess_decoding/analyze_drift_results.py

# 결과 확인
open analysis/phase1_preprocess_decoding/drift_analysis/drift_comparison.png
open analysis/phase1_preprocess_decoding/drift_analysis/drift_by_roi.png
cat analysis/phase1_preprocess_decoding/drift_analysis/drift_results.csv
```

## 🔍 주의사항

### D0 vs D1 구분

**문제:** D0과 D1 모두 `--motion none`이므로 같은 디렉토리에 저장됨
- Directory: `nzNone_moNo/`

**해결:** `results.json`의 `config.highpass_hz` 확인
```python
# D0: config.highpass_hz = null
# D1: config.highpass_hz = 0.01
```

분석 스크립트는 이를 자동으로 구분합니다.

### Baseline32와의 차이

Baseline32 (sub-07, 이전 코드):
- No highpass
- No drift regressors
- No z-scoring code (당시 존재 안 함)
- HRF L2 norm = 700
- Run correlation = 0.775

D0+M0 (sub-01, 현재 코드):
- No highpass ✓
- No drift regressors ✓
- Z-scoring code 있지만 normalize='none' 사용
- HRF L2 norm = ? (data scale에 따라 다름)
- Run correlation = ? (이게 핵심!)

**중요:** HRF L2 norm이 700이 아니어도 괜찮습니다. Run correlation이 중요합니다!

## 📈 결과 해석

### Scenario 1: D0 성공 (r~0.7)

```
✅ 문제 확정: Drift 처리가 원인
→ Solution: D0 전략 사용 (no drift processing)
→ Trade-off: Drift 노이즈 vs Signal 보존
```

**다음 단계:**
1. D0 전략으로 전체 subjects 실행
2. Drift 없이도 decoding이 잘 되는지 확인
3. 필요시 최소한의 drift 처리 방법 탐색

### Scenario 2: D0 부분 성공 (0.3 < r < 0.5)

```
⚠️  Drift + 다른 요인
→ D0가 최선이지만 완벽하지 않음
→ 추가 조사 필요:
   - Masker standardization 설정
   - Subject 차이 (sub-01 vs sub-07)
   - ROI 차이
```

**다음 단계:**
1. D0로 sub-07 테스트 (Baseline32 subject)
2. Masker 설정 확인
3. 다른 preprocessing 단계 점검

### Scenario 3: D0 실패 (r < 0.3)

```
❌ 문제는 drift가 아님!
→ 근본적인 차이 존재:
   - fMRIPrep 데이터 버전/설정
   - Subject 특성
   - 코드 변경사항
   - 기타 preprocessing
```

**다음 단계:**
1. Baseline32 시절 코드 복원
2. 정확히 같은 조건으로 재실행
3. Diff 분석으로 차이점 찾기

## 🔧 디버깅

### 단일 job 테스트 (D0+M0, V1)

```bash
# 서버에서
cd /scratch/connectome/haba6030/colorBlind

python analysis/phase1_preprocess_decoding/fir_reconstruction_BH2009_system_clean.py \
    --subject 01 \
    --roi V1 \
    --dataset method3_header_mi \
    --smooth 0 \
    --motion none \
    --compcor 0 \
    --drift none \
    --normalize-level none
    # ← highpass argument 없음 = None

# 결과 확인
python3 << 'EOF'
import json
with open('analysis/phase1_preprocess_decoding/method3_header_mi/results/factorial_experiment/nzNone_moNo/sub-01/V1/results.json') as f:
    data = json.load(f)
print(f"Highpass: {data['config']['highpass_hz']}")
print(f"Run correlation: {data['run_correlation_mean']:.4f}")
EOF
```

### 로그 체크리스트

```bash
# 1. Highpass 적용 여부
grep "Applied.*Hz high-pass\|Skipping high-pass" logs/drift_*.out

# 2. Confounds 로드 여부
grep "Loaded.*confounds\|motion_type" logs/drift_*.out

# 3. 1st-level normalization
grep "1st-level Normalization" logs/drift_*.out

# 4. 최종 metrics
grep "run_correlation_mean\|classification_accuracy" logs/drift_*.out
```

## 📋 체크포인트

실행 전 확인:
- [ ] fir_reconstruction_BH2009_system_clean.py 최신 버전
- [ ] drift_comparison.sbatch 검토
- [ ] 로그 디렉토리 존재 확인
- [ ] Baseline32 결과 비교용 데이터 준비

실행 중 확인:
- [ ] 16 jobs 모두 실행 중
- [ ] 로그에 에러 없음
- [ ] D0+M0 조건이 highpass=None 확인

분석 전 확인:
- [ ] 16개 results.json 모두 생성
- [ ] D0 vs D1 구분 가능 (highpass_hz 확인)
- [ ] Baseline32 참조 데이터 준비

## 🎯 핵심 메트릭

**가장 중요한 지표:**
```python
run_correlation_mean  # Run-to-run reliability
```

**참고 지표:**
```python
classification_accuracy    # Decoding 성능
reconstruction_error       # 재구성 오차
amplitude_std             # Amplitude 안정성
hrf_peak_delay            # HRF shape 정상성
```

**무시해도 되는 지표:**
```python
hrf_l2_norm               # Scale에 따라 변하므로 절대값 무의미
amplitude_mean            # Scale 의존적
```

## 📚 참고

- Baseline32 로그: `results/factorial_experiment/phase0_m3_24g_sub-7_82545.out`
- 이전 factorial 결과: `factorial_analysis/factorial_results.csv`
- 원본 설계 문서: `FACTORIAL_EXPERIMENT_GUIDE.md`
