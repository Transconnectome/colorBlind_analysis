# 새로운 sbatch 실행 구조 요약

## 🎯 핵심 개선사항

### Before (문제점)
- ❌ 20개 SLURM jobs (5 subjects × 4 ROIs)
- ❌ 로그 파일 20개로 분산되어 추적 어려움
- ❌ 리소스 부족: 320GB 메모리, 80 CPUs 필요
- ❌ Exit code 120 에러 발생

### After (해결)
- ✅ **5개 SLURM jobs** (각 subject당 1개)
- ✅ 각 job이 4개 ROI를 순차적으로 처리
- ✅ 로그가 subject별로 정리
- ✅ 리소스: 80GB 메모리, 20 CPUs (현실적)
- ✅ 깔끔한 진행 상황 모니터링

---

## 📁 새로운 파일 구조

### 실행 스크립트
```
run_all_subjects.sh          # Master wrapper (5 jobs 제출)
└── run_subject_all_rois.sh  # 각 subject의 모든 ROI 처리
```

### 로그 구조
```
logs/
├── pilot/
│   └── reconstruction_20250117_143022.out  # P01의 모든 ROI 진행 상황
├── sub-01/
│   └── reconstruction_20250117_143022.out  # sub-01의 모든 ROI 진행 상황
├── sub-02/
│   └── reconstruction_20250117_143022.out
├── sub-03/
│   └── reconstruction_20250117_143022.out
└── sub-04/
    └── reconstruction_20250117_143022.out
```

### 결과 구조 (동일)
```
derivatives/20250117_143022/
├── pilot/sub-01/fir_reconstruction_uni_hrf/
│   ├── V1_universal_hrf/results.pkl
│   ├── V2_universal_hrf/results.pkl
│   ├── V3_universal_hrf/results.pkl
│   └── hV4_universal_hrf/results.pkl
├── sub-01/ ... sub-04/ (같은 구조)
```

---

## 🚀 빠른 사용법

```bash
# 1. 업로드 (로컬)
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis
scp run_all_subjects.sh run_subject_all_rois.sh \
    haba6030@node2:/scratch/connectome/haba6030/colorBlind/

# 2. 실행 (서버)
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind
chmod +x run_all_subjects.sh run_subject_all_rois.sh

bash run_all_subjects.sh universal_hrf --use-pca --n-components 6

# 3. 모니터링 (서버)
squeue -u $USER                           # 5개 job 확인
tail -f logs/sub-01/reconstruction_*.out  # 특정 subject 추적
tail -f logs/*/reconstruction_*.out       # 모든 subject 동시 추적
```

---

## 📊 각 로그 파일의 내용

각 `logs/sub-XX/reconstruction_{TIMESTAMP}.out` 파일은 다음을 포함:

```
========================================================================
Reconstruction Job - All ROIs for sub-01
========================================================================
Job ID: 64870
Processing ROIs: V1, V2, V3, hV4
Start time: Mon Nov 17 00:50:54 KST 2025
========================================================================

========================================================================
[1/4] Processing ROI: V1
========================================================================
Start time: Mon Nov 17 00:51:05 KST 2025

[진행 상황 메시지들...]

✓ V1 completed successfully!
End time: Mon Nov 17 01:12:33 KST 2025
------------------------------------------------------------------------

========================================================================
[2/4] Processing ROI: V2
========================================================================
... (V2 진행)

========================================================================
[3/4] Processing ROI: V3
========================================================================
... (V3 진행)

========================================================================
[4/4] Processing ROI: hV4
========================================================================
... (hV4 진행)

========================================================================
FINAL SUMMARY - sub-01
========================================================================
Total ROIs processed: 4
Successful: 4
Failed: 0

✓ All ROIs completed successfully!

Results saved to:
  derivatives/20250117_143022/sub-01/
========================================================================
```

---

## 🔧 주요 기능

### 1. 순차 처리
각 subject job이 ROI를 순차적으로 처리:
- V1 완료 → V2 시작 → V3 시작 → hV4 시작
- 메모리 오버플로우 방지
- 진행 상황 명확

### 2. 자동 에러 추적
각 ROI별 성공/실패 기록:
```bash
✓ V1 completed successfully!
✓ V2 completed successfully!
✗ V3 failed with exit code: 1
✓ hV4 completed successfully!
```

### 3. 최종 요약
각 subject의 처리 결과를 한눈에 확인:
```
FINAL SUMMARY - sub-01
Total ROIs processed: 4
Successful: 3
Failed: 1
✗ Some ROIs failed:
  - V3
```

### 4. 깔끔한 모니터링
```bash
# 모든 subject가 어느 ROI를 처리 중인지
grep "Processing ROI" logs/*/reconstruction_*.out

# 출력 예시:
logs/pilot/reconstruction_20250117_143022.out:[2/4] Processing ROI: V2
logs/sub-01/reconstruction_20250117_143022.out:[3/4] Processing ROI: V3
logs/sub-02/reconstruction_20250117_143022.out:[1/4] Processing ROI: V1
logs/sub-03/reconstruction_20250117_143022.out:[4/4] Processing ROI: hV4
logs/sub-04/reconstruction_20250117_143022.out:[2/4] Processing ROI: V2
```

---

## ⚙️ 리소스 사용량

### 각 subject job
- 메모리: 16GB
- CPU: 4 cores
- 시간: 최대 8시간 (4 ROIs × ~2시간)

### 전체 (5 jobs 동시 실행)
- 총 메모리: 80GB
- 총 CPU: 20 cores
- **이전 구조(320GB, 80 CPUs)보다 75% 절감**

---

## 📝 Troubleshooting

### 특정 subject의 특정 ROI가 실패한 경우

```bash
# 1. 로그에서 실패한 ROI 확인
grep -A 10 "FINAL SUMMARY" logs/sub-01/reconstruction_*.out

# 2. 해당 ROI의 에러 메시지 찾기
grep -B 5 -A 10 "✗ V3 failed" logs/sub-01/reconstruction_*.out

# 3. Python traceback 확인
grep -A 20 "Traceback" logs/sub-01/reconstruction_*.err
```

### 재실행이 필요한 경우

특정 subject만 재실행:
```bash
# 새 timestamp 생성
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# sub-01만 재실행
sbatch --job-name=sub-01_${TIMESTAMP} \
       run_subject_all_rois.sh 01 $TIMESTAMP universal_hrf "--use-pca --n-components 6"
```

---

## 🎯 추천 워크플로우

1. **첫 실행**: `bash run_all_subjects.sh universal_hrf --use-pca --n-components 6`
2. **모니터링**: `tail -f logs/*/reconstruction_*.out`
3. **확인**: `grep "FINAL SUMMARY" logs/*/reconstruction_*.out`
4. **실패 있으면**: 해당 subject만 재실행
5. **성공하면**: CVD metrics 추출

---

**작성일**: 2025-11-17
**구조 변경 이유**: 리소스 부족 및 로그 관리 개선
