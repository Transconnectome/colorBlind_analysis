# SBATCH 일괄 실행 가이드

여러 subject와 ROI를 한 번에 실행하되, **모든 결과를 같은 timestamp 폴더에 저장**하는 방법입니다.

---

## 🎯 핵심 개념

**문제:**
- sbatch로 여러 job을 동시 제출하면 각각 다른 timestamp가 생성됨
- 결과가 여러 폴더에 분산됨

**해결:**
- Wrapper 스크립트가 공통 timestamp를 **한 번만** 생성
- 모든 job에 같은 timestamp를 argument로 전달
- 모든 결과가 `derivatives/{TIMESTAMP}/`에 저장됨

---

## 📁 새 파일들

### 1. `run_all_subjects_rois.sh` ⭐
- 공통 timestamp 생성
- 모든 subject × ROI 조합에 대해 job 제출

### 2. `run_reconstruction.sh`
- 개별 job용 SLURM 스크립트
- Subject, ROI, timestamp를 argument로 받음

### 3. 수정된 Python 스크립트 (3개)
- `fir_reconstruction_universal_hrf.py`
- `fir_reconstruction_zScore.py`
- `fir_reconstruction_zScore_voxelSelect.py`
- 모두 `--timestamp` argument 추가됨

---

## 🚀 빠른 시작

### 1. 파일 업로드 (로컬 → 서버)

```bash
# 로컬에서
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis

scp run_all_subjects_rois.sh \run_reconstruction.sh \visualize_Edits/fir_reconstruction_universal_hrf.py \visualize_Edits/fir_reconstruction_zScore.py \visualize_Edits/fir_reconstruction_zScore_voxelSelect.py \haba6030@node2:/scratch/connectome/haba6030/colorBlind/
```

### 2. 서버에서 실행 권한 부여

```bash
# 서버에서
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind

chmod +x run_all_subjects_rois.sh
chmod +x run_reconstruction.sh
```

### 3. 한 번에 모든 조합 실행

```bash
# 서버에서
cd /scratch/connectome/haba6030/colorBlind

# Universal HRF method (PCA-6 사용)
bash run_all_subjects.sh universal_hrf --use-pca --n-components 6 --save-zmaps

# 또는 zScore method
bash run_all_subjects.sh zScore --use-pca --n-components 6 --save-zmaps

# 또는 voxelSelect method
bash run_all_subjects.sh voxelSelect --use-pca --n-components 6 --save-zmaps
```

**예상 출력:**
```
========================================================================
Running Reconstruction for All Subjects × ROIs
========================================================================
Timestamp: 20250116_143022
Subjects: P01 01 02 03 04
ROIs: V1 V2 V3 hV4

Method: universal_hrf
Extra arguments: --use-pca --n-components 6

Submitting jobs...
------------------------------------------------------------------------
  Submitted: P01_V1_20250116_143022
  Submitted: P01_V2_20250116_143022
  Submitted: P01_V3_20250116_143022
  Submitted: P01_hV4_20250116_143022
  Submitted: 01_V1_20250116_143022
  ...
------------------------------------------------------------------------
Total jobs submitted: 20

Results will be saved to:
  derivatives/20250116_143022/
```

---

## 📊 결과 확인

### Job 상태 모니터링

```bash
# 서버에서
squeue -u $USER

# 예시 출력:
# JOBID     USER       NAME                ST   TIME  NODES
# 12345     haba6030   P01_V1_20250116...  R    5:23  node2
# 12346     haba6030   P01_V2_20250116...  R    4:58  node2
# 12347     haba6030   P01_V3_20250116...  PD   0:00  (Resources)
```

### 로그 확인

```bash
# 서버에서
ls logs/

# 최신 로그 확인
tail -f logs/slurm_P01_V1_20250116_143022_*.out
```

### 결과 폴더 확인

```bash
# 서버에서
ls derivatives/20250116_143022/

# 예시 출력:
# pilot/
# sub-01/
# sub-02/
# sub-03/
# sub-04/

# 특정 subject 결과 확인
ls derivatives/20250116_143022/sub-01/fir_reconstruction_uni_hrf/

# 예시 출력:
# V1_universal_hrf/
# V2_universal_hrf/
# V3_universal_hrf/
# hV4_universal_hrf/
```

---

## 🔧 고급 사용법

### 1. 특정 subject만 실행

`run_all_subjects_rois.sh`를 수정:
```bash
# Line 19 수정
SUBJECTS=(P01)  # 원하는 subject만
ROIS=(V1 V2)    # 원하는 ROI만
```

### 2. 직접 timestamp 지정

```bash
# 이미 있는 timestamp에 추가하고 싶을 때
TIMESTAMP=20250116_143022

# 개별 job 제출
sbatch --job-name=01_V1_$TIMESTAMP \
       run_reconstruction.sh 01 V1 $TIMESTAMP universal_hrf "--use-pca --n-components 6"
```

### 3. 여러 method 동시 실행

```bash
# 서버에서
bash run_all_subjects_rois.sh universal_hrf --use-pca --n-components 6 &
bash run_all_subjects_rois.sh zScore --use-pca --n-components 6 &
bash run_all_subjects_rois.sh voxelSelect --use-pca --n-components 6 &

# 주의: 각 method는 다른 timestamp를 가짐
# 만약 같은 timestamp에 저장하고 싶다면:
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

for METHOD in universal_hrf zScore voxelSelect; do
    for SUBJECT in P01 01 02 03 04; do
        for ROI in V1 V2 V3 hV4; do
            sbatch --job-name=${SUBJECT}_${ROI}_${METHOD}_${TIMESTAMP} \
                   run_reconstruction.sh $SUBJECT $ROI $TIMESTAMP $METHOD "--use-pca --n-components 6"
        done
    done
done
```

---

## 🎯 CVD Analysis와 연동

### 1. 모든 reconstruction 완료 확인

```bash
# 서버에서
# 모든 job이 완료될 때까지 대기
watch -n 10 'squeue -u $USER'
# (모든 job이 사라지면 완료)
```

### 2. CVD 메트릭 추출

```bash
# 서버에서
TIMESTAMP=20250116_143022  # 위에서 사용한 timestamp

for sub in P01 01 02 03 04; do
    python visualize_Edits/extract_colorblind_metrics.py \
        --subject $sub \
        --timestamp $TIMESTAMP \
        --output-dir cvd_metrics_${TIMESTAMP}
done
```

### 3. 그룹 비교

```bash
# 서버에서
python visualize_Edits/compare_subjects_cvd.py \
    --cvd-subjects P01 \
    --non-cvd-subjects 01 02 03 04 \
    --metrics-dir cvd_metrics_${TIMESTAMP} \
    --output-dir cvd_comparison_${TIMESTAMP}
```

### 4. 결과 다운로드

```bash
# 로컬에서
export TS=20250116_143022

# 분석 결과만 다운로드
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/cvd_comparison_${TS} ./

# 또는 derivatives 전체 다운로드 (용량 주의!)
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/derivatives/${TS} ./derivatives/
```

---

## 📝 Troubleshooting

### 문제 1: "Permission denied" 에러

**해결:**
```bash
# 서버에서
chmod +x run_all_subjects_rois.sh
chmod +x run_reconstruction.sh
```

### 문제 2: Job이 제출되지 않음

**확인:**
```bash
# SLURM이 작동하는지 확인
sinfo

# node2가 available한지 확인
sinfo -n node2
```

**해결:**
```bash
# run_reconstruction.sh의 #SBATCH 설정 확인
# 필요시 --nodelist=node2 제거 또는 변경
```

### 문제 3: 모든 job이 실패

**확인:**
```bash
# 로그 파일 확인
cat logs/slurm_P01_V1_*_*.err

# conda 환경 확인
source /opt/ohba/anaconda/etc/profile.d/conda.sh
conda activate nilearn
python --version
```

### 문제 4: Timestamp 폴더가 여러 개 생성됨

**원인:** `run_all_subjects_rois.sh`를 여러 번 실행

**해결:** 괜찮습니다! 각 실행은 독립적인 버전입니다.
```bash
# 서버에서 모든 timestamp 확인
ls -lt derivatives/ | head

# 특정 timestamp만 분석하면 됨
```

---

## 💡 유용한 명령어

```bash
# 서버에서

# 1. 실행 중인 job 개수 확인
squeue -u $USER | wc -l

# 2. 완료된 결과 개수 확인
find derivatives/20250116_143022 -name "results.pkl" | wc -l
# 예상: 20개 (5 subjects × 4 ROIs)

# 3. 특정 subject의 모든 ROI 결과 확인
ls derivatives/20250116_143022/sub-01/fir_reconstruction_uni_hrf/

# 4. 모든 job 취소 (필요시)
scancel -u $USER

# 5. 특정 timestamp의 모든 summary 확인
find derivatives/20250116_143022 -name "summary.csv" -exec cat {} \;
```

---

## 📦 완전 자동화 스크립트

전체 workflow를 한 번에:

```bash
#!/bin/bash
# complete_workflow.sh

# 1. Reconstruction 실행
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
echo "Starting reconstruction with timestamp: $TIMESTAMP"

bash run_all_subjects_rois.sh universal_hrf --use-pca --n-components 6

# 2. Job 완료 대기
echo "Waiting for jobs to complete..."
while [ $(squeue -u $USER | wc -l) -gt 1 ]; do
    sleep 60
done

# 3. CVD 메트릭 추출
echo "Extracting CVD metrics..."
for sub in P01 01 02 03 04; do
    python visualize_Edits/extract_colorblind_metrics.py \
        --subject $sub \
        --timestamp $TIMESTAMP \
        --output-dir cvd_metrics_${TIMESTAMP}
done

# 4. 그룹 비교
echo "Comparing groups..."
python visualize_Edits/compare_subjects_cvd.py \
    --cvd-subjects P01 \
    --non-cvd-subjects 01 02 03 04 \
    --metrics-dir cvd_metrics_${TIMESTAMP} \
    --output-dir cvd_comparison_${TIMESTAMP}

echo "Complete! Results in:"
echo "  derivatives/$TIMESTAMP/"
echo "  cvd_comparison_$TIMESTAMP/"
```

---

**작성일:** 2025-01-16
**최종 수정:** 2025-01-16
