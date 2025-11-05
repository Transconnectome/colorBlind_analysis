# Git Push 가이드

## ✅ 완료된 것
- Git 저장소 초기화 완료
- 59개 파일 커밋 완료 (23,570줄)
- 모든 Python 코드, 문서, 스크립트 포함

## 🚀 GitHub에 푸시하기

### 방법 1: GitHub Desktop 사용 (가장 쉬움)

1. **GitHub Desktop 다운로드**
   - https://desktop.github.com/

2. **현재 폴더 추가**
   - File → Add Local Repository
   - `/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis` 선택

3. **GitHub에 Publish**
   - "Publish repository" 버튼 클릭
   - Repository name: `colorBlind_analysis`
   - Description: "fMRI color perception analysis and CVD correction"
   - ✅ Private 체크 (개인 연구)
   - Publish!

### 방법 2: 명령줄 사용

#### Step 1: GitHub에서 새 저장소 만들기

1. GitHub.com 로그인
2. 우측 상단 "+" → "New repository"
3. 설정:
   - Repository name: `colorBlind_analysis`
   - Description: `fMRI color perception decoding and CVD correction filter`
   - ⚪ Private (추천)
   - ❌ "Initialize this repository with a README" 체크 해제
4. "Create repository" 클릭

#### Step 2: Remote 추가 및 Push

```bash
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis

# Remote 추가 (yourusername을 실제 GitHub 사용자명으로 변경)
git remote add origin https://github.com/yourusername/colorBlind_analysis.git

# 브랜치 이름을 main으로 변경 (최신 GitHub 표준)
git branch -M main

# Push
git push -u origin main
```

**첫 Push시 인증:**
- Username: GitHub 사용자명
- Password: Personal Access Token (PAT) 사용
  - Settings → Developer settings → Personal access tokens
  - "Generate new token (classic)"
  - Scopes: ✅ repo
  - 생성된 토큰을 비밀번호로 사용

#### Step 3: 확인

```bash
# Remote 확인
git remote -v

# 출력:
# origin  https://github.com/yourusername/colorBlind_analysis.git (fetch)
# origin  https://github.com/yourusername/colorBlind_analysis.git (push)
```

---

## 🔄 앞으로 변경사항 커밋 & 푸시

### 일반적인 워크플로우

```bash
# 1. 변경사항 확인
git status

# 2. 변경된 파일 추가
git add .

# 또는 특정 파일만:
git add naive_analysis.py RECONSTRUCTION_ANALYSIS.md

# 3. 커밋
git commit -m "Add V2 ROI analysis results

- V2 achieved 37.5% hit rate, p=0.042 (significant!)
- Updated documentation with findings
- Added parallel ROI comparison script"

# 4. 푸시
git push
```

### 유용한 커밋 메시지 패턴

```bash
# 새 기능
git commit -m "Add parallel ROI testing script"

# 버그 수정
git commit -m "Fix Lab hue calculation for pilot data"

# 문서 업데이트
git commit -m "Update ROI comparison results"

# 성능 개선
git commit -m "Optimize GLM caching to reduce runtime"

# 결과 추가
git commit -m "Add V1-V4 reconstruction results

- V2: 37.5% (p=0.042) ✅
- V1: 31.2% (p=0.123)
- V3: 26.5% (p=0.234)
- hV4: 19.8% (p=0.456)"
```

---

## 📁 저장소 구조

푸시 후 GitHub에서 보일 구조:

```
colorBlind_analysis/
├── README.md (자동 생성된 CLAUDE.md)
├── Analysis Scripts/
│   ├── naive_analysis.py          # Main canonical HRF analysis
│   ├── bh_anal.py                  # FIR model analysis
│   ├── roi_build.py                # ROI construction
│   └── config.py                   # Configuration
├── Utilities/
│   ├── check_roi_setup.py          # ROI verification
│   ├── test_roi_reconstruction.py  # Results comparison
│   ├── inspect_cache.py            # Cache inspection
│   └── compare_all_colors.py       # Color space comparison
├── Parallel Execution/
│   ├── submit_roi_parallel.sh      # Submit all ROIs
│   ├── check_parallel_results.sh   # Check results
│   └── run_all_rois_parallel.sh    # Alternative method
├── Experiment Code/
│   ├── colorBlind_pilotTest.py     # Pilot experiment
│   └── colorBlind_test.py          # Main experiment
├── Documentation/
│   ├── RECONSTRUCTION_ANALYSIS.md  # Problem diagnosis
│   ├── NEXT_STEPS.md               # Action plan
│   ├── PARALLEL_ROI_GUIDE.md       # Parallel testing guide
│   ├── BASH_SCRIPT_GUIDE.md        # Bash tutorial
│   └── COLOR_COMPARISON_SUMMARY.md # Pilot vs Main colors
└── SLURM Scripts/
    ├── sbatch_diagnostic.sub       # Diagnostic analysis
    └── sbatch_ml_comparison.sub    # ML comparison
```

---

## 🔐 OneDrive와 Git 함께 사용

### 현재 상황
- ✅ 코드는 OneDrive에 동기화
- ✅ Git으로 버전 관리
- ✅ GitHub에 백업

### 주의사항

**OneDrive 충돌 방지:**
```bash
# .git 폴더를 OneDrive 동기화에서 제외하는 것이 좋음
# 설정 → 동기화 및 백업 → 제외할 폴더 선택
```

**권장 워크플로우:**
1. 로컬에서 작업 (OneDrive 동기화됨)
2. Git commit (버전 관리)
3. Git push (GitHub 백업)
4. OneDrive는 파일만 동기화, Git 히스토리는 GitHub에

---

## 🛡️ Private vs Public

### Private 저장소 (추천)
✅ 연구 데이터/분석 보호
✅ 논문 출판 전까지 비공개
✅ 팀원만 접근 가능

### Public 저장소
- 오픈 소스로 공유
- 논문 출판 후 고려
- 재현성 향상

---

## 📊 나중에: GitHub Actions로 자동화

논문 제출 후 고려할 수 있는 것들:

```yaml
# .github/workflows/test.yml
name: Run Tests
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
      - name: Run tests
        run: python -m pytest tests/
```

---

## 🔍 유용한 Git 명령어

```bash
# 변경 이력 보기
git log --oneline --graph

# 특정 파일 이력
git log -- naive_analysis.py

# 이전 버전으로 롤백 (위험!)
git revert <commit-hash>

# 브랜치 만들기 (실험용)
git checkout -b experiment-fir-model
git push -u origin experiment-fir-model

# 변경사항 임시 저장
git stash
git stash pop

# 원격 저장소 최신 상태 가져오기
git pull
```

---

## ❓ 문제 해결

### "Permission denied"
→ Personal Access Token 사용하거나 SSH 키 설정

### "Already exists"
→ 저장소가 이미 있음, git pull 먼저

### "Large files"
→ .gitignore 확인, Git LFS 고려

### OneDrive 충돌
→ .git 폴더를 동기화에서 제외

---

## 📞 도움말

- GitHub Docs: https://docs.github.com
- Git 가이드: https://git-scm.com/doc
- GitHub Desktop: https://desktop.github.com

---

**지금 할 일:**
1. GitHub 계정 있는지 확인
2. 새 저장소 만들기 (Private 추천)
3. Remote 추가하고 push
4. GitHub에서 확인!

🎉 이제 모든 작업이 안전하게 백업됩니다!
