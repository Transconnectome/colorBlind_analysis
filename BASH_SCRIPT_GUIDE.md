# Bash 스크립트 완전 정복 가이드

## 기본 개념

### 스크립트란?
- 여러 명령어를 하나의 파일에 저장
- 한 번에 실행 가능
- 반복 작업 자동화

### 왜 사용하나?
```bash
# 매번 이렇게 치는 대신:
cd /path/to/project
rm -f cache/*
python script.py
python check_results.py

# 스크립트로 한 번에:
./run_analysis.sh
```

---

## 1. chmod +x: 실행 권한 부여

### chmod란?
- **ch**ange **mod**e (권한 변경)
- Linux 파일 권한 설정 명령어

### 권한의 종류

```bash
ls -l script.sh
# 출력: -rw-r--r-- 1 user group 1234 Nov 5 script.sh
#       ^^^^^^^^
#       권한 부분
```

**권한 구조:**
```
-  rw-  r--  r--
│   │    │    │
│   │    │    └─ Others (다른 사용자): 읽기만 가능
│   │    └────── Group (그룹): 읽기만 가능
│   └─────────── Owner (소유자): 읽기/쓰기 가능
└─────────────── 파일 타입 (- = 일반 파일)
```

**각 권한의 의미:**
- `r` (read): 읽기 - 파일 내용 볼 수 있음
- `w` (write): 쓰기 - 파일 수정 가능
- `x` (execute): 실행 - 프로그램으로 실행 가능
- `-`: 권한 없음

### chmod +x의 의미

```bash
chmod +x script.sh
```

- `+x`: 실행(execute) 권한 **추가**
- 모든 사용자에게 실행 권한 부여

**변화:**
```bash
# Before:
-rw-r--r--  script.sh  # 실행 불가

# After:
-rwxr-xr-x  script.sh  # 실행 가능!
      ^^^
```

### chmod 사용 예시

```bash
# 실행 권한 추가
chmod +x script.sh

# 실행 권한 제거
chmod -x script.sh

# 소유자만 모든 권한, 다른 사람은 읽기만
chmod 744 script.sh
#      ^^^
#      7=rwx (소유자), 4=r-- (그룹), 4=r-- (기타)

# 모두에게 모든 권한 (주의!)
chmod 777 script.sh

# 여러 파일 한 번에
chmod +x *.sh
```

### 숫자로 권한 설정

```
r (read)    = 4
w (write)   = 2
x (execute) = 1

rwx = 4+2+1 = 7
rw- = 4+2+0 = 6
r-x = 4+0+1 = 5
r-- = 4+0+0 = 4
```

**예시:**
```bash
chmod 755 script.sh
# 7 (소유자): rwx (읽기/쓰기/실행)
# 5 (그룹):   r-x (읽기/실행)
# 5 (기타):   r-x (읽기/실행)
```

---

## 2. ./script.sh: 스크립트 실행

### ./ 의 의미

```bash
./script.sh
││
│└─ script.sh 파일 이름
└── 현재 디렉토리
```

**왜 `./`를 붙이나?**

Linux는 보안상 현재 디렉토리를 자동으로 검색하지 않습니다:

```bash
# 이건 안 됨:
script.sh
# 에러: command not found

# 이렇게 해야 함:
./script.sh  # 현재 디렉토리의 script.sh 실행
```

### 다른 실행 방법

```bash
# 1. 현재 디렉토리에서 실행
./script.sh

# 2. 절대 경로로 실행
/home/user/project/script.sh

# 3. bash 명령어로 실행 (chmod +x 없이도 가능)
bash script.sh

# 4. sh로 실행
sh script.sh

# 5. source로 실행 (현재 쉘에서 실행)
source script.sh
# 또는
. script.sh
```

### PATH 디렉토리에 추가하기

자주 쓰는 스크립트를 어디서든 실행:

```bash
# 1. 스크립트를 PATH에 있는 디렉토리로 복사
sudo cp script.sh /usr/local/bin/myscript
sudo chmod +x /usr/local/bin/myscript

# 2. 이제 어디서든 실행 가능:
myscript  # ./ 없이!

# 3. 또는 PATH에 디렉토리 추가 (~/.bashrc에):
export PATH="$PATH:$HOME/bin"
```

---

## 3. Bash 스크립트 작성법

### 기본 구조

```bash
#!/bin/bash
# ^^^^^^^^^
# Shebang: 어떤 인터프리터로 실행할지 지정

# 주석은 #으로 시작

echo "Hello, World!"  # 화면에 출력

# 변수 사용
NAME="John"
echo "Hello, $NAME"

# 명령어 실행
cd /path/to/dir
python script.py
```

### 실용적인 예제

```bash
#!/bin/bash

# ============================================
# 연구 분석 자동화 스크립트
# ============================================

# 1. 설정
PROJECT_DIR="/scratch/connectome/myproject"
OUTPUT_DIR="$PROJECT_DIR/results"

# 2. 에러 발생시 즉시 중단
set -e

# 3. 진행 상황 출력
echo "Starting analysis..."
echo "Working directory: $(pwd)"

# 4. 디렉토리 생성
mkdir -p $OUTPUT_DIR

# 5. 캐시 삭제
echo "Clearing cache..."
rm -f cache/*.joblib

# 6. 분석 실행
echo "Running analysis..."
python analysis.py --output $OUTPUT_DIR

# 7. 결과 확인
if [ -f "$OUTPUT_DIR/results.csv" ]; then
    echo "✅ Analysis complete!"
    echo "Results saved to: $OUTPUT_DIR/results.csv"
else
    echo "❌ Analysis failed!"
    exit 1
fi
```

---

## 4. 유용한 Bash 기법

### 변수

```bash
# 변수 선언 (= 앞뒤 공백 없이!)
NAME="value"
NUMBER=42

# 변수 사용
echo $NAME
echo ${NAME}  # 더 명확한 방법

# 명령어 결과를 변수에 저장
CURRENT_DIR=$(pwd)
DATE=$(date +%Y-%m-%d)
FILE_COUNT=$(ls | wc -l)

echo "Current directory: $CURRENT_DIR"
echo "Today: $DATE"
echo "Number of files: $FILE_COUNT"
```

### 조건문

```bash
# if 문
if [ -f "file.txt" ]; then
    echo "파일이 존재합니다"
else
    echo "파일이 없습니다"
fi

# 여러 조건
if [ -f "file.txt" ] && [ -r "file.txt" ]; then
    echo "파일이 존재하고 읽을 수 있습니다"
fi

# 숫자 비교
if [ $NUMBER -gt 10 ]; then
    echo "10보다 큽니다"
fi

# 문자열 비교
if [ "$NAME" = "John" ]; then
    echo "이름이 John입니다"
fi
```

**자주 쓰는 조건:**
```bash
# 파일 확인
[ -f file ]      # 파일 존재?
[ -d dir ]       # 디렉토리 존재?
[ -e path ]      # 경로 존재?
[ -r file ]      # 읽기 가능?
[ -w file ]      # 쓰기 가능?
[ -x file ]      # 실행 가능?

# 숫자 비교
[ $a -eq $b ]    # 같음
[ $a -ne $b ]    # 다름
[ $a -gt $b ]    # 큼 (greater than)
[ $a -lt $b ]    # 작음 (less than)
[ $a -ge $b ]    # 크거나 같음
[ $a -le $b ]    # 작거나 같음

# 문자열 비교
[ "$a" = "$b" ]  # 같음
[ "$a" != "$b" ] # 다름
[ -z "$a" ]      # 빈 문자열?
[ -n "$a" ]      # 비어있지 않음?
```

### 반복문

```bash
# for 문
for i in 1 2 3 4 5; do
    echo "Number: $i"
done

# 파일 반복
for file in *.txt; do
    echo "Processing: $file"
    python analyze.py $file
done

# 배열 사용
ROIS=("V1" "V2" "V3" "hV4")
for roi in "${ROIS[@]}"; do
    echo "Processing ROI: $roi"
    python analyze_roi.py --roi $roi
done

# C 스타일 for 문
for ((i=1; i<=10; i++)); do
    echo "Iteration $i"
done

# while 문
counter=1
while [ $counter -le 5 ]; do
    echo "Count: $counter"
    ((counter++))
done
```

### 함수

```bash
# 함수 정의
my_function() {
    echo "함수가 호출되었습니다"
    echo "첫 번째 인자: $1"
    echo "두 번째 인자: $2"
}

# 함수 호출
my_function arg1 arg2

# 리턴 값이 있는 함수
get_date() {
    echo $(date +%Y-%m-%d)
}

TODAY=$(get_date)
echo "오늘 날짜: $TODAY"
```

---

## 5. SLURM과 통합

### sbatch 스크립트

```bash
#!/bin/bash
#SBATCH --job-name=my_job        # 작업 이름
#SBATCH --output=logs/%j.out     # 출력 파일 (%j = job ID)
#SBATCH --error=logs/%j.err      # 에러 파일
#SBATCH --time=01:00:00          # 최대 실행 시간 (1시간)
#SBATCH --mem=16G                # 메모리
#SBATCH --cpus-per-task=4        # CPU 코어 수
#SBATCH --partition=normal       # 파티션 (선택)

# 여기부터 일반 bash 스크립트
echo "Job started at $(date)"
echo "Running on node: $(hostname)"

# 환경 설정
module load python/3.9
source activate myenv

# 분석 실행
python my_analysis.py

echo "Job finished at $(date)"
```

### 여러 작업 제출

```bash
#!/bin/bash

# 여러 파라미터로 작업 제출
for alpha in 0.01 0.1 1.0 10.0; do
    sbatch --job-name="test_${alpha}" \
           --export=ALPHA=$alpha \
           my_script.sh
done

# 작업 배열 사용 (더 효율적)
sbatch --array=1-4 my_array_script.sh
```

---

## 6. 실전 패턴

### 패턴 1: 안전한 스크립트

```bash
#!/bin/bash

# 에러 발생시 즉시 중단
set -e

# 정의되지 않은 변수 사용시 에러
set -u

# 파이프라인 중 하나라도 실패하면 에러
set -o pipefail

# 디버그 모드 (모든 명령어 출력)
# set -x

echo "스크립트 시작"

# 필수 파일 확인
if [ ! -f "data.txt" ]; then
    echo "❌ 에러: data.txt 파일이 없습니다"
    exit 1
fi

# 작업 수행
echo "✅ 데이터 파일 확인 완료"
```

### 패턴 2: 진행 상황 표시

```bash
#!/bin/bash

STEPS=("데이터 로드" "전처리" "분석" "결과 저장")
TOTAL=${#STEPS[@]}

for i in "${!STEPS[@]}"; do
    STEP_NUM=$((i + 1))
    echo ""
    echo "[$STEP_NUM/$TOTAL] ${STEPS[$i]}..."
    echo "========================================"

    # 실제 작업
    sleep 2  # 예시

    echo "✅ 완료"
done

echo ""
echo "🎉 모든 단계 완료!"
```

### 패턴 3: 로그 저장

```bash
#!/bin/bash

# 로그 디렉토리 생성
LOG_DIR="logs"
mkdir -p $LOG_DIR

# 타임스탬프
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$LOG_DIR/analysis_${TIMESTAMP}.log"

# 모든 출력을 로그 파일과 화면 모두에
exec > >(tee -a $LOG_FILE)
exec 2>&1

echo "분석 시작: $(date)"
echo "로그 파일: $LOG_FILE"

# 작업 수행
python analysis.py

echo "분석 완료: $(date)"
```

### 패턴 4: 인자 처리

```bash
#!/bin/bash

# 사용법 출력
usage() {
    echo "사용법: $0 [-r ROI] [-m MEMORY] [-t TIME]"
    echo "  -r ROI     : ROI 이름 (V1, V2, V3, hV4)"
    echo "  -m MEMORY  : 메모리 (기본: 16G)"
    echo "  -t TIME    : 시간 (기본: 01:00:00)"
    exit 1
}

# 기본값
ROI="V1"
MEMORY="16G"
TIME="01:00:00"

# 인자 파싱
while getopts "r:m:t:h" opt; do
    case $opt in
        r) ROI="$OPTARG" ;;
        m) MEMORY="$OPTARG" ;;
        t) TIME="$OPTARG" ;;
        h) usage ;;
        *) usage ;;
    esac
done

echo "설정:"
echo "  ROI: $ROI"
echo "  Memory: $MEMORY"
echo "  Time: $TIME"

# 작업 수행
sbatch --mem=$MEMORY --time=$TIME \
       --export=ROI=$ROI \
       my_script.sh
```

---

## 7. 자주 쓰는 명령어 조합

### 파일 찾기

```bash
# 이름으로 파일 찾기
find . -name "*.py"

# 최근 수정된 파일
ls -lt | head -10

# 특정 패턴 검색
grep -r "TODO" *.py

# 큰 파일 찾기
du -sh * | sort -rh | head -10
```

### 병렬 실행

```bash
# GNU parallel 사용
parallel python process.py ::: file1.txt file2.txt file3.txt

# xargs 사용
ls *.txt | xargs -P 4 -I {} python process.py {}

# background 실행
python script1.py &
python script2.py &
python script3.py &
wait  # 모두 완료될 때까지 대기
```

### 조건부 실행

```bash
# 성공하면 다음 실행
python step1.py && python step2.py && python step3.py

# 실패하면 다음 실행
python step1.py || echo "Step 1 failed!"

# 항상 다음 실행
python step1.py; python step2.py
```

---

## 8. 디버깅 팁

### 에러 추적

```bash
# 상세 모드 (모든 명령어 출력)
bash -x script.sh

# 또는 스크립트 내부에
set -x  # 디버그 시작
# 문제 구간
set +x  # 디버그 종료

# 실행되는 명령어 확인
echo "Will execute: python $SCRIPT_NAME"
```

### 변수 확인

```bash
# 변수 내용 출력
echo "ROI = [$ROI]"
echo "Files found: $(ls *.txt | wc -l)"

# 타입 확인
declare -p VARIABLE
```

---

## 9. 실전 예제: ROI 분석 스크립트

```bash
#!/bin/bash
#================================================================
# ROI 분석 자동화 스크립트
# 사용법: ./analyze_roi.sh V2
#================================================================

set -e  # 에러시 중단

# 색상 정의 (출력 이쁘게)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'  # No Color

# ROI 이름 받기
ROI=${1:-V2}  # 인자 없으면 V2 기본값

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}ROI 분석: $ROI${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 1. 디렉토리 확인
PROJECT_DIR="/scratch/connectome/haba6030/colorBlind"
if [ ! -d "$PROJECT_DIR" ]; then
    echo -e "${RED}❌ 에러: 프로젝트 디렉토리 없음${NC}"
    exit 1
fi

cd $PROJECT_DIR
echo -e "${GREEN}✅${NC} 작업 디렉토리: $(pwd)"

# 2. ROI 마스크 확인
ROI_MASK="derivatives/sub-01/roi/sub-01_${ROI}_mask.nii.gz"
if [ ! -f "$ROI_MASK" ]; then
    echo -e "${RED}❌ 에러: ROI 마스크 없음: $ROI_MASK${NC}"
    exit 1
fi
echo -e "${GREEN}✅${NC} ROI 마스크: $ROI_MASK"

# 3. 캐시 삭제
CACHE_DIR="hrf_test_outputs/cache_${ROI}"
echo ""
echo "캐시 삭제: $CACHE_DIR"
rm -rf $CACHE_DIR/*
mkdir -p $CACHE_DIR
echo -e "${GREEN}✅${NC} 캐시 초기화 완료"

# 4. 분석 스크립트 생성
echo ""
echo "분석 스크립트 생성..."
sed "s/ROI_SELECTION = \[.*\]/ROI_SELECTION = [\"${ROI}\"]/" \
    naive_analysis.py > temp_${ROI}.py
echo -e "${GREEN}✅${NC} temp_${ROI}.py 생성"

# 5. 작업 제출
echo ""
echo "SLURM 작업 제출..."
JOB_ID=$(sbatch --job-name="roi_${ROI}" \
                --output="logs/roi_${ROI}_%j.out" \
                --mem=16G \
                --time=00:30:00 \
                --wrap="python temp_${ROI}.py && rm temp_${ROI}.py" \
                | grep -oP '\d+')

if [ ! -z "$JOB_ID" ]; then
    echo -e "${GREEN}✅ 작업 제출 완료: Job ID ${JOB_ID}${NC}"
    echo ""
    echo "진행 상황 확인:"
    echo "  squeue -j $JOB_ID"
    echo ""
    echo "로그 확인:"
    echo "  tail -f logs/roi_${ROI}_${JOB_ID}.out"
else
    echo -e "${RED}❌ 작업 제출 실패${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}분석 진행 중... 약 15-20분 소요${NC}"
```

---

## 10. 치트시트

### 필수 명령어

```bash
# 권한 관리
chmod +x script.sh          # 실행 권한 추가
chmod 755 script.sh         # rwxr-xr-x
ls -l                       # 권한 확인

# 스크립트 실행
./script.sh                 # 현재 디렉토리
bash script.sh              # bash로 실행
sh script.sh                # sh로 실행

# 변수
NAME="value"                # 변수 선언
echo $NAME                  # 변수 사용
RESULT=$(command)           # 명령 결과 저장

# 조건문
if [ condition ]; then      # if 시작
    commands                # 실행 내용
fi                          # if 종료

# 반복문
for i in 1 2 3; do         # for 시작
    echo $i                 # 실행 내용
done                        # for 종료

# 함수
func_name() {              # 함수 정의
    echo "Hello $1"         # $1 = 첫 번째 인자
}
func_name "World"          # 함수 호출

# 파일 확인
[ -f file ]                # 파일 존재?
[ -d dir ]                 # 디렉토리 존재?
[ -e path ]                # 경로 존재?

# 에러 처리
set -e                     # 에러시 중단
set -u                     # 미정의 변수 에러
set -x                     # 디버그 모드
```

### SLURM 관련

```bash
# 작업 제출
sbatch script.sh           # 스크립트 제출
sbatch --wrap="command"    # 직접 명령어 제출

# 상태 확인
squeue                     # 모든 작업
squeue -u $USER            # 내 작업만
squeue -j 12345            # 특정 작업

# 작업 관리
scancel 12345              # 작업 취소
scancel -u $USER           # 내 모든 작업 취소

# 결과 확인
sacct                      # 완료된 작업
sacct -j 12345 --format=JobID,JobName,State,ExitCode
```

---

## 마무리

이제 bash 스크립트를 자유자재로 사용하실 수 있을 거예요!

**핵심 기억할 것:**
1. `chmod +x` = 실행 권한 부여
2. `./script.sh` = 현재 디렉토리에서 실행
3. `set -e` = 에러시 중단 (안전!)
4. 변수는 `$NAME` 또는 `${NAME}`
5. 조건문 `[ ]` 안에 공백 필수!

**다음 단계:**
- 간단한 스크립트부터 작성해보기
- 자주 쓰는 명령어 스크립트로 만들기
- 복잡한 작업을 함수로 나누기
- 디버그 모드(`set -x`)로 동작 확인

화이팅! 🚀
