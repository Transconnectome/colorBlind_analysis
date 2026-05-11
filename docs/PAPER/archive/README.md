# Color Vision Deficiency fMRI Paper

LaTeX 소스 파일 for 논문 작성 및 로컬 컴파일

## 📁 프로젝트 구조

```
PAPER/
├── main.tex                 # 메인 문서 (여기서 컴파일)
├── bibliography.bib         # 참고문헌 데이터베이스 (32개)
├── compile.sh              # 컴파일 스크립트
├── .gitignore              # Git 무시 파일 (auxiliary files)
│
├── Introduction/           # Introduction 섹션
│   └── introduction.tex
│
├── Methods/                # Methods 섹션
│   └── methods.tex        # ✅ 완성됨
│
├── Results/                # Results 섹션
│   └── results.tex
│
├── Discussion/             # Discussion 섹션
│   └── discussion.tex
│
└── Figures/                # 그림 파일 폴더
    └── (여기에 PDF/PNG 추가)
```

## 🚀 빠른 시작

### 1. 로컬 컴파일

```bash
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/docs/PAPER

# 자동 컴파일 (추천)
./compile.sh

# 수동 컴파일
pdflatex main.tex
biber main
pdflatex main.tex
pdflatex main.tex
```

### 2. PDF 열기

```bash
open main.pdf
```

## 📝 작성 상태

### ✅ 완성
- **main.tex** - 메인 문서 구조
- **bibliography.bib** - 전체 참고문헌 (32개)
- **Methods/methods.tex** - Methods 섹션 (완전 작성)

### 📝 작성 중 (placeholder)
- **Introduction/introduction.tex** - 초안 작성됨, 확장 필요
- **Results/results.tex** - 구조만 작성됨
- **Discussion/discussion.tex** - 초안 작성됨, 확장 필요

### 📊 추가 필요
- **Abstract** - main.tex에서 수정 필요
- **Figures** - Figures/ 폴더에 추가
- **Title/Author/Affiliation** - main.tex에서 수정

## 🔧 요구사항

### LaTeX 배포판
- **macOS**: MacTeX (TeX Live)
- **설치 확인**:
  ```bash
  pdflatex --version
  biber --version
  ```

### 필수 패키지
main.tex에서 사용하는 패키지들:
- `apa6` - APA 6th edition 문서 클래스
- `biblatex` - 참고문헌 관리 (biber backend)
- `amsmath`, `amssymb` - 수식
- `graphicx` - 그림
- `hyperref` - 하이퍼링크
- `csquotes` - 인용부호

## 📖 사용 방법

### 섹션 수정하기

각 섹션은 별도 파일로 관리됩니다:

```latex
% 예: Introduction/introduction.tex 수정
\section{Introduction}

Color vision deficiency affects...
```

저장 후 `./compile.sh` 실행 → PDF 업데이트

### 그림 추가하기

1. **Figures/** 폴더에 그림 저장 (PDF 또는 PNG 추천)
2. 해당 섹션 .tex 파일에 추가:

```latex
\begin{figure}[htbp]
\centering
\includegraphics[width=0.8\textwidth]{figure1.pdf}
\caption{Stimulus configuration in CIE L*a*b* space.}
\label{fig:stimulus}
\end{figure}
```

3. 본문에서 참조:
```latex
As shown in Figure~\ref{fig:stimulus}...
```

### 참고문헌 인용하기

bibliography.bib에 있는 논문 인용:

```latex
\cite{brouwer2009}                    % (Brouwer & Heeger, 2009)
\textcite{brouwer2009}                % Brouwer and Heeger (2009)
\cite{haxby2011, guntupalli2016}      % (Haxby et al., 2011; Guntupalli et al., 2016)
```

새로운 참고문헌 추가:
1. bibliography.bib 열기
2. 끝에 BibTeX entry 추가:
```bibtex
@article{yourkey2024,
  author = {Last, F. M. and Second, A.},
  title = {Your paper title},
  journal = {Journal Name},
  volume = {10},
  pages = {100--120},
  year = {2024},
  doi = {10.xxxx/xxxxx}
}
```
3. 본문에서 `\cite{yourkey2024}` 사용

## 📤 PI에게 공유하기

### 옵션 1: 소스 파일 전체 공유 (추천)

```bash
# PAPER 폴더 전체를 압축
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/docs
zip -r CVD_Paper.zip PAPER/ -x "*.aux" "*.log" "*.out" "*.bbl" "*.blg" "*.bcf" "*.run.xml"

# PI에게 CVD_Paper.zip 전송
```

PI가 받으면:
1. 압축 해제
2. `compile.sh` 실행
3. `main.pdf` 열기

### 옵션 2: PDF만 공유

```bash
# PDF만 전송
cp main.pdf ~/Desktop/CVD_Paper_$(date +%Y%m%d).pdf
```

### 옵션 3: GitHub/Git 저장소

```bash
# 이미 git 저장소에 있으면
git add .
git commit -m "Add complete paper structure"
git push

# PI에게 repository URL 공유
```

## 🐛 문제 해결

### 컴파일 에러

**"File 'bibliography.bib' not found"**
```bash
# 현재 디렉토리 확인
pwd  # /Users/.../docs/PAPER 여야 함
ls bibliography.bib  # 파일 존재 확인
```

**"Undefined control sequence"**
- main.log 파일 확인
- 수식 기호 ($, _, ^)가 text mode에 있는지 확인
- methods.tex나 다른 섹션에서 에러 위치 찾기

**"Citation undefined"**
- 정상입니다! `./compile.sh` 한 번 더 실행
- 또는 수동으로: `pdflatex main.tex` 다시 실행

### 참고문헌이 안 나올 때

```bash
# Biber 캐시 삭제
rm -f *.bcf *.run.xml *.bbl *.blg

# 처음부터 다시 컴파일
./compile.sh
```

### 그림이 안 보일 때

```bash
# 그림 파일이 Figures/ 폴더에 있는지 확인
ls Figures/

# 파일 이름 대소문자 확인 (figure1.pdf vs Figure1.pdf)
```

## 📋 체크리스트 (제출 전)

- [ ] Title, Author, Affiliation 수정 (main.tex)
- [ ] Abstract 작성 (main.tex)
- [ ] Keywords 확인 (main.tex)
- [ ] Introduction 완성
- [ ] Methods 검토 (이미 완성됨)
- [ ] Results 작성 및 Figure 추가
- [ ] Discussion 작성
- [ ] 모든 인용 확인 (Citation undefined 없음)
- [ ] 모든 Figure 참조 확인
- [ ] 컴파일 성공 (에러 없음)
- [ ] PDF 최종 검토

## 🔗 유용한 명령어

```bash
# 특정 섹션만 컴파일 (디버깅용)
# main.tex에서 다른 \input 주석 처리

# 에러 로그 확인
tail -50 main.log

# 참고문헌 로그 확인
cat main.blg

# Auxiliary 파일 전체 삭제
rm -f *.aux *.log *.out *.bbl *.blg *.bcf *.run.xml

# PDF viewer 새로고침 (Preview.app이 자동으로 안 될 때)
open -a Preview main.pdf
```

## 💡 팁

1. **자주 컴파일**: 작은 변경 후에도 컴파일해서 에러 조기 발견
2. **버전 관리**: Git commit으로 중요한 변경사항 저장
3. **백업**: 정기적으로 PAPER 폴더 백업
4. **주석 활용**: TODO 주석으로 작성 필요 부분 표시
5. **섹션별 작업**: 한 섹션씩 집중해서 작성

## 📞 도움말

문제가 있으면:
1. main.log 파일 확인
2. 에러 메시지 마지막 50줄 복사
3. Claude에게 문의

---

**현재 상태**: Methods 완성, Introduction/Results/Discussion 초안 작성됨

**다음 단계**:
1. Introduction 확장
2. Results 데이터 추가
3. Figure 제작 및 추가
4. Discussion 정제
