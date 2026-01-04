# MNI Chain Diagnosis - Server Execution Guide

## 🚀 빠른 실행 가이드

### 1단계: 파일 업로드

```bash
# 로컬에서 실행
scp diagnose_mni_chain.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/
scp run_mni_diagnosis.sbatch haba6030@node2:/scratch/connectome/haba6030/colorBlind/
```

### 2단계: 서버 접속 및 실행

```bash
# 서버 접속
ssh haba6030@node2

# 작업 디렉토리 이동
cd /scratch/connectome/haba6030/colorBlind

# 로그 디렉토리 생성
mkdir -p logs/mni_diagnosis

# 실행 옵션 선택:
```

#### Option A: 모든 피험자 진단 (1-10)

```bash
sbatch run_mni_diagnosis.sbatch
```

#### Option B: 특정 피험자만 진단

```bash
# 단일 피험자
sbatch --array=1 run_mni_diagnosis.sbatch

# 여러 피험자
sbatch --array=1,2,3 run_mni_diagnosis.sbatch

# 범위 지정
sbatch --array=1-5 run_mni_diagnosis.sbatch
```

#### Option C: CVD 피험자만 진단

```bash
sbatch --array=8-10 run_mni_diagnosis.sbatch
```

---

## 📊 진행 상황 모니터링

### 작업 상태 확인

```bash
# 현재 실행 중인 작업
squeue -u haba6030 | grep mni_diag

# 작업 상세 정보
scontrol show job <JOB_ID>
```

### 실시간 로그 확인

```bash
# 표준 출력 (진단 결과)
tail -f logs/mni_diagnosis/mni_diag_sub-01.out

# 에러 로그
tail -f logs/mni_diagnosis/mni_diag_sub-01.err
```

### 완료된 작업 결과 확인

```bash
# 모든 피험자의 요약 결과 보기
for sub in 01 02 03 04 05 06 07 08 09 10; do
    echo "=== sub-$sub ==="
    if [ -f logs/mni_diagnosis/mni_diag_sub-${sub}.out ]; then
        grep -A 3 "Summary" logs/mni_diagnosis/mni_diag_sub-${sub}.out
    else
        echo "Not completed yet"
    fi
    echo ""
done
```

---

## 📥 결과 다운로드

### 진단 결과 파일

```bash
# 로컬에서 실행
# 전체 진단 결과 디렉토리
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/logs/mni_diagnosis ./

# 특정 피험자 결과만
scp haba6030@node2:/scratch/connectome/haba6030/colorBlind/logs/mni_diagnosis/mni_chain_diagnosis_sub-01.txt ./
```

### fsleyes 명령어 파일

```bash
# 시각적 검증용 명령어 다운로드
scp haba6030@node2:/scratch/connectome/haba6030/colorBlind/logs/mni_diagnosis/mni_chain_diagnosis_sub-*.txt ./
```

---

## 🔍 결과 해석

### 출력 구조

각 피험자당 생성되는 파일:

```
logs/mni_diagnosis/
├── mni_diag_sub-01.out              # 진단 결과 (main output)
├── mni_diag_sub-01.err              # 에러 로그
└── mni_chain_diagnosis_sub-01.txt   # fsleyes 명령어
```

### 주요 체크 포인트

`mni_diag_sub-XX.out` 파일에서 확인할 항목:

```bash
# 1. Summary 섹션
grep -A 5 "Summary" logs/mni_diagnosis/mni_diag_sub-01.out

# 예상 출력:
# T1w → MNI:        ✅ OK / ❌ PROBLEM
# BOLD → MNI:       ✅ OK / ❌ PROBLEM
# Grid consistency: ✅ OK / ❌ PROBLEM
```

### 빠른 진단 요약

```bash
# 모든 피험자의 MNI 체인 상태 요약
echo "Subject | T1w→MNI | BOLD→MNI | Grid | Status"
echo "--------|---------|----------|------|--------"
for sub in 01 02 03 04 05 06 07 08 09 10; do
    if [ -f logs/mni_diagnosis/mni_diag_sub-${sub}.out ]; then
        t1=$(grep "T1w → MNI:" logs/mni_diagnosis/mni_diag_sub-${sub}.out | awk '{print $NF}')
        bold=$(grep "BOLD → MNI:" logs/mni_diagnosis/mni_diag_sub-${sub}.out | awk '{print $NF}')
        grid=$(grep "Grid consistency:" logs/mni_diagnosis/mni_diag_sub-${sub}.out | awk '{print $NF}')

        if [[ "$t1" == "OK" && "$bold" == "OK" && "$grid" == "OK" ]]; then
            status="✅ PASS"
        else
            status="❌ FAIL"
        fi

        echo "sub-$sub  | $t1 | $bold | $grid | $status"
    fi
done
```

---

## 🛠️ 문제 해결

### 일반적인 에러

#### 1. fMRIPrep 출력 없음

```
❌ ERROR: fMRIPrep output not found for sub-XX
```

**해결:**
```bash
# fMRIPrep 출력 확인
ls /storage/connectome/haba6030/fmriprep_out_deoblique_v2/sub-*/

# 해당 피험자 제외하고 실행
sbatch --array=1,2,3,5-10 run_mni_diagnosis.sbatch  # sub-04 제외
```

#### 2. Template 파일 없음

```
⚠️ No template found
```

**해결:**
```bash
# TemplateFlow 캐시 확인
ls ~/.cache/templateflow/tpl-MNI152NLin2009cAsym/

# 없으면 다운로드
python -c "from templateflow import api; api.get('MNI152NLin2009cAsym', resolution=2, suffix='T1w')"
```

#### 3. Python 모듈 없음

```
ModuleNotFoundError: No module named 'nibabel'
```

**해결:**
```bash
# conda 환경 확인
conda activate nilearn
conda list | grep nibabel

# 없으면 설치
conda install nibabel nilearn
```

---

## 📋 체크리스트

### 실행 전

- [ ] `diagnose_mni_chain.py` 업로드 완료
- [ ] `run_mni_diagnosis.sbatch` 업로드 완료
- [ ] 로그 디렉토리 생성 (`logs/mni_diagnosis/`)
- [ ] conda 환경 활성화 가능 확인

### 실행 중

- [ ] 작업 제출 성공 (`sbatch` 명령 실행)
- [ ] 작업 ID 기록
- [ ] 큐 상태 정상 (`squeue` 확인)

### 실행 후

- [ ] 모든 피험자 `.out` 파일 생성 확인
- [ ] Summary 섹션 확인
- [ ] 에러 로그 확인 (`.err` 파일)
- [ ] fsleyes 명령어 파일 다운로드

---

## 🎯 다음 단계: 시각적 검증

진단 스크립트 완료 후:

1. **fsleyes 명령어 파일 다운로드**
   ```bash
   scp haba6030@node2:/scratch/connectome/haba6030/colorBlind/logs/mni_diagnosis/mni_chain_diagnosis_sub-01.txt ./
   ```

2. **필요한 이미지 파일 다운로드**
   ```bash
   # Template (로컬에 없는 경우)
   scp haba6030@node2:~/.cache/templateflow/tpl-MNI152NLin2009cAsym/tpl-MNI152NLin2009cAsym_res-02_T1w.nii.gz ./

   # T1w MNI
   scp 'haba6030@node2:/storage/connectome/haba6030/fmriprep_out_deoblique_v2/sub-01/anat/*space-MNI*T1w.nii.gz' ./

   # BOLD MNI
   scp 'haba6030@node2:/storage/connectome/haba6030/fmriprep_out_deoblique_v2/sub-01/func/*run-1*space-MNI*boldref.nii.gz' ./
   ```

3. **fsleyes로 시각적 검증 수행**
   ```bash
   # mni_chain_diagnosis_sub-01.txt 파일의 명령어 실행
   ```

---

## 💡 추가 팁

### 병렬 실행 최적화

10명 전체를 동시 실행하면 30분 안에 완료:

```bash
# 모든 피험자 동시 실행
sbatch run_mni_diagnosis.sbatch

# 각 작업은 독립적이므로 병렬 처리 안전
```

### 재실행 시

```bash
# 특정 피험자만 재진단
sbatch --array=4 run_mni_diagnosis.sbatch

# 이전 로그는 자동으로 덮어씀
```

### 결과 백업

```bash
# 전체 진단 결과 압축
cd /scratch/connectome/haba6030/colorBlind
tar -czf mni_diagnosis_results_$(date +%Y%m%d).tar.gz logs/mni_diagnosis/

# 로컬로 다운로드
scp haba6030@node2:/scratch/connectome/haba6030/colorBlind/mni_diagnosis_results_*.tar.gz ./
```

---

## 📞 문제 발생 시

1. **로그 파일 확인**
   ```bash
   cat logs/mni_diagnosis/mni_diag_sub-XX.err
   ```

2. **SLURM 작업 로그 확인**
   ```bash
   sacct -j <JOB_ID> --format=JobID,JobName,State,ExitCode,Elapsed
   ```

3. **대화형 모드로 디버깅**
   ```bash
   srun --qos=shared --nodelist=node2 --cpus-per-task=4 --mem=16G --pty bash
   conda activate nilearn
   cd /scratch/connectome/haba6030/colorBlind
   python diagnose_mni_chain.py --subject 01 --fmriprep-dir /storage/... --run 1
   ```
