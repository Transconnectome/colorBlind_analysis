# MNI Chain Diagnosis - Quick Start

## 🚀 3단계로 시작하기

### 1️⃣ 파일 업로드 (로컬에서 실행)

```bash
scp diagnose_mni_chain.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/
scp run_mni_diagnosis.sbatch haba6030@node2:/scratch/connectome/haba6030/colorBlind/
```

### 2️⃣ 서버에서 실행

```bash
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind
mkdir -p logs/mni_diagnosis

# 모든 피험자 진단
sbatch run_mni_diagnosis.sbatch

# 또는 특정 피험자만
sbatch --array=1,2,3 run_mni_diagnosis.sbatch
```

### 3️⃣ 결과 확인

```bash
# 실시간 모니터링
tail -f logs/mni_diagnosis/mni_diag_sub-01.out

# 완료 후 요약
grep -A 3 "Summary" logs/mni_diagnosis/mni_diag_sub-01.out
```

---

## 📥 결과 다운로드 (로컬에서 실행)

```bash
# 전체 결과
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/logs/mni_diagnosis ./

# 특정 파일만
scp haba6030@node2:/scratch/connectome/haba6030/colorBlind/logs/mni_diagnosis/mni_chain_diagnosis_sub-01.txt ./
```

---

## 🔍 빠른 진단 요약

```bash
# 서버에서 실행
for sub in 01 02 03 04 05 06 07 08 09 10; do
    echo "=== sub-$sub ==="
    grep -A 3 "Summary" logs/mni_diagnosis/mni_diag_sub-${sub}.out
done
```

---

## 📚 상세 문서

- **전체 가이드**: `docs/MNI_CHAIN_DIAGNOSIS_GUIDE.md`
- **서버 실행 가이드**: `docs/MNI_DIAGNOSIS_SERVER_GUIDE.md`
- **리포트 템플릿**: `docs/MNI_DIAGNOSIS_REPORT_TEMPLATE.md`

---

## ✅ 체크리스트

- [ ] 파일 업로드 완료
- [ ] sbatch 제출 완료
- [ ] 로그 확인 완료
- [ ] 결과 다운로드 완료
- [ ] fsleyes 시각적 검증 완료 (중요!)
