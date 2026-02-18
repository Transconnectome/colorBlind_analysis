---
name: server-sync
description: 로컬-서버 간 파일 전송 명령(SCP/rsync)을 생성합니다. "upload to server", "서버 업로드", "download results", "결과 다운로드", "scp", "rsync" 요청 시 사용.
recommended-model: haiku
---

> **Model hint**: Use `model: "haiku"` when spawning subagents for this skill (mechanical task: SCP/rsync command assembly).

# 서버 파일 동기화 (server-sync)

## 목적

로컬 ↔ SLURM 클러스터 간 최적화된 SCP/rsync 명령을 생성합니다.

---

## 경로 매핑

| | 경로 |
|---|------|
| **서버** | `haba6030@node3:/scratch/connectome/haba6030/colorBlind/` |
| **로컬** | `/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/` |

---

## 업로드 규칙 (로컬 → 서버)

### 업로드 대상
- `*.py` — 분석 스크립트
- `*.sbatch` — SLURM 작업 파일
- `*.sh` — 셸 스크립트
- `*.md` — 문서 (README 등)
- `utils/` — 유틸리티 모듈

### 업로드 제외
- `results/` — 서버에서 생성
- `logs/` — 서버에서 생성
- `*.nii.gz` — 뇌영상 데이터 (이미 서버에 존재)
- `*.npy` — 대용량 배열
- `__pycache__/` — 파이썬 캐시
- `.DS_Store` — macOS 메타데이터

### 업로드 명령 패턴

**단일 phase 업로드 (SCP):**
```bash
# 특정 phase의 모든 스크립트 + sbatch
scp analysis/phase2_SRM_across_between/{*.py,*.sbatch} haba6030@node3:/scratch/connectome/haba6030/colorBlind/analysis/phase2_SRM_across_between/
```

**유틸리티 업로드:**
```bash
scp analysis/utils/*.py haba6030@node3:/scratch/connectome/haba6030/colorBlind/analysis/utils/
```

**대량 업로드 (rsync 권장):**
```bash
rsync -avz --exclude='results/' --exclude='logs/' --exclude='*.nii.gz' --exclude='*.npy' --exclude='*.npz' --exclude='__pycache__/' --exclude='.DS_Store' --exclude='*.out' --exclude='*.err' --exclude='validation/' analysis/phase2_SRM_across_between/ haba6030@node3:/scratch/connectome/haba6030/colorBlind/analysis/phase2_SRM_across_between/
```

---

## 다운로드 규칙 (서버 → 로컬)

### 다운로드 대상
- `*.json` — 결과 파일 (results.json, settings.json)
- `*.png` / `*.pdf` — 시각화 결과
- `*.csv` — 데이터 테이블
- `*.txt` — 텍스트 출력

### 다운로드 제외 (기본)
- `*.npy` — 대용량 (필요 시만 다운로드)
- `*.nii.gz` — 뇌영상 원본
- `*.out` / `*.err` — SLURM 로그 (디버깅 시만)

### 다운로드 명령 패턴

**결과 JSON 다운로드:**
```bash
scp haba6030@node3:/scratch/connectome/haba6030/colorBlind/derivatives/phase2_procrustes/{date}_{jobid}/results.json analysis/phase2_SRM_across_between/results/
```

**시각화 결과 다운로드:**
```bash
scp "haba6030@node3:/scratch/connectome/haba6030/colorBlind/analysis/phase2_SRM_across_between/results/*.png" analysis/phase2_SRM_across_between/results/
```

**전체 결과 디렉토리 다운로드 (rsync):**
```bash
rsync -avz --include='*.json' --include='*.png' --include='*.pdf' --include='*.csv' --include='*/' --exclude='*' haba6030@node3:/scratch/connectome/haba6030/colorBlind/derivatives/phase2_procrustes/ analysis/phase2_SRM_across_between/results/
```

**SLURM 로그 다운로드 (디버깅 시):**
```bash
scp "haba6030@node3:/scratch/connectome/haba6030/colorBlind/analysis/phase2_SRM_across_between/logs/*.{out,err}" analysis/phase2_SRM_across_between/logs/
```

---

## SCP 작성 규칙 (CRITICAL)

1. **줄바꿈 금지**: SCP 명령은 반드시 한 줄로 작성
2. **같은 목적지 합침**: 동일 디렉토리로 가는 파일은 `{file1,file2}` 또는 `*.ext`로 합침
3. **와일드카드 활용**: 같은 확장자면 `*.py` 사용
4. **별도 scp는 목적지가 다를 때만**:
   ```bash
   # 좋은 예: 2개 명령 (목적지 다름)
   scp analysis/phase2_SRM_across_between/{*.py,*.sbatch} haba6030@node3:.../phase2_SRM_across_between/
   scp analysis/utils/*.py haba6030@node3:.../utils/

   # 나쁜 예: 파일마다 별도 명령
   scp analysis/phase2_SRM_across_between/script1.py haba6030@node3:...
   scp analysis/phase2_SRM_across_between/script2.py haba6030@node3:...
   ```

---

## 동작 순서

1. **전송 방향 확인**: 업로드 vs 다운로드
2. **대상 phase 확인**: 어떤 분석 단계의 파일인지
3. **파일 목록 확인**: `git status` 또는 `ls`로 전송 대상 파악
4. **명령 생성**: SCP (소수 파일) 또는 rsync (대량) 선택
5. **명령 출력**: 복사-붙여넣기 가능한 형태로

---

## 체크리스트

- [ ] node3 사용 (SSH/SCP 접속용)
- [ ] 줄바꿈 없는 한 줄 명령
- [ ] 같은 목적지 파일 합쳐짐
- [ ] 대용량 파일(nii.gz, npy) 제외됨
- [ ] 서버 경로가 올바른지 확인
