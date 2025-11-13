# ⚡ Quick Server Workflow - 빠른 실행 가이드

**서버:** node2:/scratch/connectome/haba6030/colorBlind

---

## 🚀 Step-by-Step Execution (복사해서 실행하세요!)

### Step 1: 로컬에서 파일 업로드
```bash
# 로컬 Mac 터미널에서 실행
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis

# 필수 파일들 업로드
scp fir_reconstruction.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/
scp fir_reconstruction_universal_hrf.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/
scp config.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/
scp run_fir_reconstruction_single.sbatch haba6030@node2:/scratch/connectome/haba6030/colorBlind/
scp run_fir_reconstruction_parallel.sbatch haba6030@node2:/scratch/connectome/haba6030/colorBlind/
```

### Step 2: 서버 접속 및 환경 확인
```bash
# 서버 접속
ssh haba6030@node2

# 작업 디렉토리로 이동
cd /scratch/connectome/haba6030/colorBlind

# conda 환경 활성화
conda activate nilearn

# 데이터 존재 확인
ls /storage/connectome/haba6030/fmriprep_out/sub-P01/func/*res-2*preproc* | head -3

# ROI 마스크 존재 확인 (없으면 먼저 만들어야 함)
ls derivatives/sub-P01/roi/sub-P01_*_mask.nii.gz
```

### Step 3: 테스트 실행 (V2 ROI, PCA 사용)
```bash
# V2 ROI로 먼저 테스트 - 가장 성공 확률 높음
sbatch --export=ROI=V2,USE_PCA=1,N_COMPONENTS=20 run_fir_reconstruction_single.sbatch

# Job ID 확인
squeue -u haba6030

# 실시간 로그 확인
tail -f logs/fir_recon_*.out

# Ctrl+C로 빠져나오기
```

### Step 4: 결과 확인
```bash
# Job이 끝나면
ls derivatives/sub-P01/fir_reconstruction/V2/

# Summary 확인
cat derivatives/sub-P01/fir_reconstruction/V2/summary.csv

# 상세 로그 확인
less derivatives/sub-P01/fir_reconstruction/V2/log.txt
```

### Step 5: 성공했다면 전체 ROI 실행
```bash
# 모든 ROI 병렬 실행 (V1, V2, V3, hV4, VO1)
sbatch run_fir_reconstruction_parallel.sbatch

# 모든 Job 확인
squeue -u haba6030

# 전체 결과 합치기 (모두 끝난 후)
cat derivatives/sub-P01/fir_reconstruction/*/summary.csv > all_roi_results.csv
```

### Step 6: 결과 다운로드
```bash
# 로컬 Mac 터미널에서 실행
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis

# 결과 다운로드
scp haba6030@node2:/scratch/connectome/haba6030/colorBlind/all_roi_results.csv ./
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/derivatives/sub-P01/fir_reconstruction/ ./results_backup/
```

---

## 🛑 문제 해결

### ROI 마스크가 없는 경우
```bash
# 서버에서
cd /scratch/connectome/haba6030/colorBlind

# ROI 생성 스크립트 실행 (있다면)
python combine_atlas.py --subject P01 --output-dir derivatives/sub-P01/roi/

# 또는 수동으로 확인
ls ProbAtlas_v4/  # Wang atlas가 있는지
```

### Job이 실패하는 경우
```bash
# 에러 로그 확인
cat logs/fir_recon_*.err

# SLURM 작업 상태 확인
sacct -u haba6030 --format=JobID,JobName,State,ExitCode -j <JOB_ID>

# 상세 로그
less derivatives/sub-P01/fir_reconstruction/V2/log.txt
```

### Job 취소하기
```bash
# 특정 Job 취소
scancel <JOB_ID>

# 모든 내 Job 취소
scancel -u haba6030
```

---

## 📊 예상 결과 (정상인 경우)

### summary.csv 내용
```csv
ROI,N_voxels,Use_PCA,N_components,Classification_accuracy,Reconstruction_error_deg
V2,310,True,20,1.0,15.3
```

**체크포인트:**
- ✅ Classification_accuracy = 1.0 (100%) → Perfect!
- ✅ Reconstruction_error_deg < 30° → 성공!
- ❌ Classification_accuracy < 0.5 → 문제 있음
- ❌ Reconstruction_error_deg > 90° → Chance level, 실패

### log.txt에서 찾아야 할 것
```
[SUCCESS] Classification accuracy: 100.0%
[SUCCESS] Reconstruction error: 18.5°
[SUCCESS] p-value < 0.001
[INFO] PCA explained variance: 87.3%
```

---

## 🔄 자주 쓰는 명령어 모음

### SLURM 관련
```bash
# Job 제출
sbatch script.sbatch

# 내 Job 보기
squeue -u haba6030

# 특정 Job 상세정보
scontrol show job <JOB_ID>

# 완료된 Job 보기
sacct -u haba6030

# Job 취소
scancel <JOB_ID>
```

### 파일 관리
```bash
# 디스크 사용량 확인
du -sh derivatives/

# 파일 개수 세기
ls derivatives/sub-P01/roi/*.nii.gz | wc -l

# 최근 수정된 파일 찾기
find derivatives/ -mtime -1  # 하루 이내
```

### 데이터 확인
```bash
# NIfTI 파일 정보
fslinfo file.nii.gz

# NIfTI 파일 voxel 수
fslstats mask.nii.gz -V

# 빠른 이미지 확인 (X11 forwarding 필요)
fsleyes file.nii.gz &
```

---

## 📁 중요 경로 정리

### 입력 데이터
```bash
# fMRIPrep 결과
/storage/connectome/haba6030/fmriprep_out/sub-P01/func/

# Event 파일
/storage/connectome/haba6030/colorBlind_dataOct/sub-P01/func/

# Wang atlas
/scratch/connectome/haba6030/colorBlind/ProbAtlas_v4/
```

### 출력 데이터
```bash
# ROI 마스크
derivatives/sub-P01/roi/

# FIR 분석 결과
derivatives/sub-P01/fir_reconstruction/

# SLURM 로그
logs/
```

---

## ⚙️ 환경 설정 (첫 실행 시에만)

### Conda 환경 확인
```bash
# 환경 목록 보기
conda env list

# nilearn 환경 있는지 확인
conda activate nilearn

# 필수 패키지 확인
python -c "import nilearn, nibabel, sklearn; print('OK')"
```

### 디렉토리 구조 만들기
```bash
cd /scratch/connectome/haba6030/colorBlind

# 필수 디렉토리 생성
mkdir -p derivatives/sub-P01/{roi,fir_reconstruction}
mkdir -p derivatives/sub-{01,02,03,04}/{roi,fir_reconstruction}
mkdir -p logs
```

---

## 💡 Pro Tips

### Tip 1: 백그라운드 실행
```bash
# nohup으로 로그아웃해도 계속 실행
nohup tail -f logs/fir_recon_*.out > tail.log 2>&1 &

# screen 사용
screen -S fmri_analysis
# Ctrl+A, D로 detach
# screen -r fmri_analysis로 다시 attach
```

### Tip 2: 빠른 테스트
```bash
# Python 파일 문법 체크 (실행 전)
python -m py_compile fir_reconstruction.py

# Import 에러 체크
python -c "import fir_reconstruction"
```

### Tip 3: 디버깅
```bash
# Python 스크립트 직접 실행 (sbatch 없이)
python fir_reconstruction.py --roi V2 --use-pca --n-components 20

# Interactive Python으로 단계별 확인
python -i fir_reconstruction.py
```

---

## 📞 도움 요청하기

### 정보 수집
```bash
# 에러 발생 시 수집할 정보
1. Job ID: squeue로 확인
2. 에러 로그: logs/fir_recon_*.err
3. 상세 로그: derivatives/sub-P01/fir_reconstruction/V2/log.txt
4. 환경 정보: conda list | grep -E "nilearn|nibabel|sklearn"
```

### 체크리스트
- [ ] ROI 마스크가 존재하는가?
- [ ] Functional data 경로가 맞는가?
- [ ] Event file이 올바른 형식인가?
- [ ] Conda 환경이 활성화되었는가?
- [ ] SLURM 리소스가 충분한가?

---

**작성일:** 2025-11-09
**목적:** 빠른 실행과 문제 해결
**다음 단계:** RESTART_PLAN.md 참고

**화이팅! 단계별로 차근차근 진행하시면 됩니다! 💪**
