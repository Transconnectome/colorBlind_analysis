---
name: github-update
description: 뇌영상 프로젝트에 맞는 안전한 git commit/push를 수행합니다. "commit", "push", "커밋", "깃 업데이트", "git update" 요청 시 사용.
recommended-model: haiku
---

> **Model hint**: Use `model: "haiku"` when spawning subagents for this skill (mechanical task: git staging + commit).

# GitHub 업데이트 (github-update)

## 목적

neuroimaging 프로젝트에 맞는 안전한 git commit/push를 수행합니다. 대용량 뇌영상 파일 차단, 선택적 스테이징, 프로젝트 스타일 커밋 메시지를 적용합니다.

---

## 동작 순서

### Step 1: Pre-commit 안전 검사 (CRITICAL)

변경 파일을 확인하기 전에 반드시 다음을 체크:

```bash
# 1. 파일 크기 확인 (10MB 초과 차단)
find . -name "*.py" -o -name "*.md" -o -name "*.sbatch" | xargs ls -la

# 2. 위험 파일 확인
git status
```

**커밋 차단 파일 (절대 스테이징 금지):**
- `*.nii.gz` — 뇌영상 데이터
- `*.npy` / `*.npz` — NumPy 배열
- `*.pkl` / `*.pickle` — 피클 파일
- `derivatives/` — 분석 결과 디렉토리 전체
- `logs/*.out` / `logs/*.err` — SLURM 로그
- `results/full_dataset*` — 전체 데이터셋 결과
- `*.nii` — 비압축 뇌영상
- `__pycache__/` — 파이썬 캐시
- 10MB 초과 파일

**스테이징 위반 발견 시:**
```
⚠️ 경고: 다음 파일이 스테이징에 포함되어 있습니다:
- derivatives/phase2_procrustes/results.npy (45MB)
이 파일들은 커밋에서 제외합니다.
```

### Step 2: 변경 파일 확인

```bash
git status
git diff --stat
```

변경된 파일 목록을 사용자에게 보여주기.

### Step 3: 선택적 스테이징

**반드시 `git add {specific_files}` 사용. `git add .` 또는 `git add -A` 절대 금지.**

커밋 대상 파일:
- `*.py` — 분석 스크립트
- `*.sbatch` — SLURM 작업 파일
- `*.sh` — 셸 스크립트
- `*.md` — 문서
- `utils/` — 유틸리티 모듈
- `*.json` — 설정/소규모 결과 (10MB 미만)
- `.claude/skills/` — 스킬 파일

```bash
# 예시: 특정 파일 스테이징
git add analysis/phase2_SRM_across_between/new_script.py
git add analysis/phase2_SRM_across_between/run_script.sbatch
```

### Step 4: 커밋 메시지 생성

프로젝트 히스토리 스타일을 따름:

| 변경 위치 | 커밋 메시지 패턴 | 예시 |
|----------|----------------|------|
| `analysis/{phase}/*.py` | `phase{N}: {설명}` | `phase2: add permutation validation for SRM` |
| `*.sbatch` | `slurm: {설명}` | `slurm: update job configuration for node2` |
| `*.md` 문서 | `docs: update {파일명}` | `docs: update METHODS_RESULTS_SUMMARY` |
| `validation/` | `validation: {설명}` | `validation: add split-half ICC analysis` |
| `utils/` | `utils: {설명}` | `utils: update output_paths for phase3` |
| 여러 phase | `{주요변경}: {설명}` | `phase2: add SRM alignment with validation` |
| `.claude/skills/` | `skills: {설명}` | `skills: add server-sync and slurm-monitor` |

```bash
# 최근 커밋 스타일 확인
git log --oneline -10
```

### Step 5: 커밋

```bash
git commit -m "$(cat <<'EOF'
phase2: add permutation validation for SRM

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
```

### Step 6: 푸시 (사용자 확인 후)

```bash
git push origin main
```

---

## 체크리스트

- [ ] `*.nii.gz`, `*.npy`, `*.npz` 스테이징 안 됨
- [ ] `derivatives/` 스테이징 안 됨
- [ ] 10MB 초과 파일 없음
- [ ] `git add .` 사용하지 않음
- [ ] 커밋 메시지가 프로젝트 스타일 따름
- [ ] push 전 사용자 확인
- [ ] `Co-Authored-By` 태그 포함
