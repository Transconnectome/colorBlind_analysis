# Group-Level Analysis 병렬 실행 가이드

**작성일**: 2025-12-16
**예상 실행 시간**: ~4시간 (무인 실행)

---

## 📦 **준비 사항**

### 1. 코드 업로드 (서버로)

```bash
# 로컬에서 실행
scp -r analysis/ haba6030@node2:/scratch/connectome/haba6030/colorBlind/
scp run_phase*.sbatch run_all_phases_parallel.sh haba6030@node2:/scratch/connectome/haba6030/colorBlind/
```

### 2. 서버 접속 및 디렉토리 확인

```bash
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind

# logs 디렉토리 확인 (없으면 자동 생성됨)
ls -la logs/
```

---

## 🚀 **실행 방법**

### Option 1: Master Script 사용 (추천)

```bash
./run_all_phases_parallel.sh
```

**이 스크립트가 하는 일**:
- Phase 1A, 1B, 1C, 2B를 모두 동시에 제출
- 총 16개 작업 (4 phases × 4 ROIs)
- 진행 상황 확인 명령어 안내

### Option 2: 개별 Phase 실행

```bash
# Phase 1A만
sbatch run_phase1a.sbatch

# Phase 1B만
sbatch run_phase1b.sbatch

# Phase 1C만 (가장 오래 걸림)
sbatch run_phase1c.sbatch

# Phase 2B만
sbatch run_phase2b.sbatch
```

---

## ⏱️ **예상 실행 시간**

| Phase | 시간 | 메모리 | 설명 |
|-------|------|--------|------|
| Phase 1A | ~30분 | 8GB | Voxel overlap (Jaccard) |
| Phase 1B | ~1시간 | 16GB | RSA (RDM similarity) |
| Phase 1C | **~2-4시간** | 32GB | ⏰ 가장 오래 걸림 (LOSO decoding) |
| Phase 2B | ~2시간 | 24GB | HC→CVD transfer |

**총 예상 시간**: ~4시간 (Phase 1C 기준)

---

## 📊 **진행 상황 확인**

### 작업 큐 확인

```bash
# 본인 작업 확인
squeue -u haba6030

# 특정 작업 상세
squeue -j <JOB_ID>
```

### 로그 실시간 확인

```bash
# Phase 1C (가장 오래 걸림) 확인
tail -f logs/phase1c_<JOB_ID>_0.out  # V1
tail -f logs/phase1c_<JOB_ID>_1.out  # V2
tail -f logs/phase1c_<JOB_ID>_2.out  # V3
tail -f logs/phase1c_<JOB_ID>_3.out  # hV4

# 모든 Phase 1C 로그
tail -f logs/phase1c_*.out
```

### 완료된 작업 확인

```bash
# 작업 히스토리
sacct -u haba6030 --format=JobID,JobName,State,Elapsed,MaxRSS

# 특정 Job ID만
sacct -j <JOB_ID> --format=JobID,JobName,State,Elapsed
```

---

## 📁 **결과 확인**

### 결과 디렉토리 구조

```
derivatives/group_level/baseline32_deob_determin/
├── V1/
│   ├── voxel_overlap/          # Phase 1A
│   │   ├── jaccard_matrix.csv
│   │   ├── jaccard_heatmap.png
│   │   ├── common_voxels_indices.npy
│   │   └── overlap_statistics.txt
│   │
│   ├── rsa/                    # Phase 1B
│   │   ├── rdm_per_subject.npz
│   │   ├── rdm_similarity_matrix.csv
│   │   ├── rdm_grid.png
│   │   └── rsa_statistics.txt
│   │
│   ├── cross_subject/          # Phase 1C
│   │   ├── loso_performance.csv
│   │   ├── loso_summary.txt
│   │   ├── loso_summary.png
│   │   ├── confusion_matrices.png
│   │   └── w_matrices/         # 각 fold별 W matrix
│   │
│   └── decoder_transfer/       # Phase 2B
│       ├── transfer_results.csv
│       ├── transfer_summary.txt
│       ├── transfer_summary.png
│       ├── per_color_errors.png
│       └── hc_group_decoder/
│           ├── w_matrix.npy
│           └── voxel_indices.npy
│
├── V2/  (동일 구조)
├── V3/  (동일 구조)
└── hV4/ (동일 구조)
```

### 빠른 확인

```bash
# Phase 1A 결과 (Jaccard index)
cat derivatives/group_level/baseline32_deob_determin/V1/voxel_overlap/overlap_statistics.txt

# Phase 1B 결과 (RDM similarity)
cat derivatives/group_level/baseline32_deob_determin/V1/rsa/rsa_statistics.txt

# Phase 1C 결과 (Cross-subject ΔACC)
cat derivatives/group_level/baseline32_deob_determin/V1/cross_subject/loso_summary.txt

# Phase 2B 결과 (HC→CVD transfer)
cat derivatives/group_level/baseline32_deob_determin/V1/decoder_transfer/transfer_summary.txt
```

### 로컬로 다운로드

```bash
# 로컬 머신에서
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/derivatives/group_level ./derivatives/

# 로그도 다운로드 (트러블슈팅용)
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/logs/phase*.out ./logs/
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/logs/phase*.err ./logs/
```

---

## 📈 **주요 지표 해석**

### Phase 1A: Voxel Overlap (Jaccard Index)

**지표**: Jaccard Index = |A ∩ B| / |A ∪ B|

- **의미**: 두 피험자 간 선택된 복셀의 겹침 정도
- **범위**: 0 (완전히 다름) ~ 1 (완전히 같음)

**해석**:
- **> 0.5**: ✅ 높은 일관성 - HC가 해부학적으로 유사한 복셀 사용
- **0.3 ~ 0.5**: ⚠️ 보통 일관성 - 어느 정도 겹침
- **< 0.3**: ❌ 낮은 일관성 - 개인차 큼

**추가 지표**:
- `Common voxels`: 모든 HC의 교집합 (가장 일관된 복셀)
- `Union voxels`: 모든 HC의 합집합
- `Overlap ratio`: Common / Union (전체 대비 공통 복셀 비율)

---

### Phase 1B: RSA (Representational Similarity Analysis)

**지표**: RDM Correlation (Spearman)

**RDM (Representational Dissimilarity Matrix)**:
- **계산**: RDM[i,j] = 1 - Spearman_corr(beta_color_i, beta_color_j) across voxels
- **의미**: 색상 간 neural representation 차이
- **크기**: (8, 8) - 8개 색상 간 dissimilarity

**RDM Similarity**:
- **계산**: Spearman_corr(RDM_subject_i, RDM_subject_j)
- **의미**: 두 피험자가 얼마나 유사한 representational geometry를 가지는가?

**해석**:
- **> 0.7**: ✅ 높은 유사성 - HC가 유사한 color representation 구조
- **0.5 ~ 0.7**: ⚠️ 보통 유사성
- **< 0.5**: ❌ 낮은 유사성 - 다른 구조

**Mantel Test**:
- **P < 0.05**: 통계적으로 유의한 RDM 유사성

---

### Phase 1C: Cross-Subject Decoding (LOSO)

**핵심 지표**: **ΔACC = ACC_within - ACC_cross_subject**

**계산 과정**:
1. **ACC_cross_subject**: 5명 HC로 학습 → 1명 HC로 테스트 (6 folds)
2. **ACC_within**: 같은 피험자 내에서 leave-one-run-out
3. **ΔACC**: 두 정확도의 차이

**의미**:
- ΔACC가 작을수록 → Cross-subject decoder가 잘 작동 → **공통 encoding system 존재**
- ΔACC가 클수록 → 개인 특이적 encoding

**해석**:
- **< 10%**: ✅ **강한 일반화** - HC가 공통 color encoding system 공유
  - 예: ACC_within = 0.85, ACC_cross = 0.78 → ΔACC = 0.07 (7%)
- **10 ~ 20%**: ⚠️ 보통 일반화 - 어느 정도 공유하지만 개인차 존재
- **> 20%**: ❌ 약한 일반화 - 개인 특이적 encoding 우세

**추가 지표**:
- **MSE (Mean Squared Error)**: (Circular distance)^2의 평균
  - 단위: degrees²
  - 낮을수록 좋음
- **ΔMSE = MSE_cross - MSE_within**: MSE 차이 (낮을수록 좋음)

**Classification Accuracy**:
- **Chance level**: 12.5% (8-way classification)
- **Good performance**: > 60%
- **Excellent**: > 80%

---

### Phase 2B: HC→CVD Decoder Transfer

**핵심 질문**: HC decoder가 CVD에게 적용 가능한가?

**지표**: **ΔACC_CVD = ACC_HC_decoder - ACC_CVD_individual**

**계산 과정**:
1. **HC group decoder 학습**:
   - 6명 HC 전체 데이터 pooling
   - W matrix 학습 (voxels → channels)

2. **CVD 테스트 (HC decoder)**:
   - 같은 voxel 위치
   - 같은 W matrix (재학습 없음!)
   - → ACC_HC_decoder

3. **CVD 테스트 (Individual decoder)**:
   - CVD 자신의 데이터로 학습한 decoder
   - → ACC_CVD_individual

4. **비교**: ΔACC_CVD

**해석**:
- **|ΔACC_CVD| < 15%**: ✅ **HC decoder가 CVD에 적용 가능!**
  - **같은 neural → color mapping!**
  - **필터 설계 feasible**
  - 예: ACC_HC = 0.70, ACC_CVD = 0.68 → ΔACC = 0.02 (2%)

- **15% < |ΔACC_CVD| < 30%**: ⚠️ 보통
  - Mapping이 부분적으로 공유
  - 필터 설계 가능하지만 조정 필요

- **|ΔACC_CVD| > 30%**: ❌ **다른 mapping**
  - HC와 CVD가 다른 neural → color mapping 사용
  - HC 기반 필터로는 부족, CVD-specific 접근 필요

**Per-Color Error Analysis**:
- **중요**: Red-Green axis (Color 3 vs Color 7)
  - CVD는 red-green discrimination에 문제
  - 이 색상들의 reconstruction error가 특히 크면 → 색맹 특징 반영

---

## 🎯 **결과 종합 해석 가이드**

### 시나리오 1: 이상적인 경우 (필터 설계 가능!)

```
Phase 1A: Mean Jaccard > 0.5          → ✅ HC 복셀 일관성 높음
Phase 1B: Mean RDM corr > 0.7         → ✅ HC 표상 구조 유사
Phase 1C: Mean ΔACC < 10%             → ✅ HC 간 강한 일반화
Phase 2B: Mean ΔACC_CVD < 15%         → ✅ HC decoder가 CVD에 적용됨!

결론: HC와 CVD가 **같은 neural → color mapping** 사용
     → Color filter 설계 FEASIBLE
     → HC의 W matrix를 target으로 filter 최적화
```

### 시나리오 2: 보통 경우 (필터 설계 도전적)

```
Phase 1A: Mean Jaccard = 0.3-0.5      → ⚠️ 보통 일관성
Phase 1B: Mean RDM corr = 0.5-0.7     → ⚠️ 보통 유사성
Phase 1C: Mean ΔACC = 10-20%          → ⚠️ 보통 일반화
Phase 2B: Mean ΔACC_CVD = 15-30%      → ⚠️ 부분적 전이

결론: Mapping이 부분적으로 공유
     → Filter 설계 가능하지만 개인화 필요
     → CVD 개별 W matrix도 고려
```

### 시나리오 3: 어려운 경우 (다른 접근 필요)

```
Phase 1A: Mean Jaccard < 0.3          → ❌ 낮은 일관성
Phase 1B: Mean RDM corr < 0.5         → ❌ 다른 구조
Phase 1C: Mean ΔACC > 20%             → ❌ 약한 일반화
Phase 2B: Mean ΔACC_CVD > 30%         → ❌ 전이 실패

결론: HC와 CVD가 다른 mapping 사용
     → HC 기반 filter로는 부족
     → CVD-specific 접근 또는 behavioral training 필요
```

---

## 🔧 **트러블슈팅**

### 작업이 PENDING 상태로 멈춤

```bash
# 작업 상태 확인
squeue -j <JOB_ID>

# 이유 확인
squeue -j <JOB_ID> -o "%.18i %.9P %.8j %.8u %.2t %.10M %.6D %R"
```

**가능한 원인**:
- 리소스 부족 (메모리/CPU)
- node2가 다른 작업으로 busy
- Priority 문제

**해결**:
- 대기 (보통 곧 시작됨)
- 또는 시간/메모리 요구사항 줄이기

### 작업이 FAILED 상태

```bash
# 에러 로그 확인
cat logs/phase*_<JOB_ID>_*.err

# 출력 로그도 확인
cat logs/phase*_<JOB_ID>_*.out
```

**흔한 에러**:
1. **FileNotFoundError**: Baseline 결과 없음
   - 확인: `ls derivatives/BH2009_deoblique_v2/baseline32_deob_determin/`

2. **MemoryError**: 메모리 부족
   - 해결: SBATCH의 `--mem` 증가

3. **Import Error**: 환경 문제
   - 확인: `conda list` (nilearn, nibabel 등)

### Phase 1A 결과가 없어서 Phase 1B, 2B 에러

**Phase 1B, 2B는 `--use-common-voxels` 플래그를 사용하면 Phase 1A 필요**

**해결**:
1. Option 1: Phase 1A 완료 후 Phase 1B, 2B 재실행
2. Option 2: `--use-common-voxels` 플래그 제거하고 재실행

---

## 📝 **체크리스트**

### 실행 전

- [ ] 코드 업로드 완료
- [ ] logs/ 디렉토리 존재 확인
- [ ] conda 환경 활성화 확인 (`conda activate nilearn`)
- [ ] Baseline 결과 존재 확인

### 실행 중

- [ ] 모든 작업 제출 완료 (16개)
- [ ] squeue로 작업 상태 확인
- [ ] Phase 1C 진행 상황 모니터링 (가장 오래 걸림)

### 실행 후

- [ ] 모든 작업 COMPLETED 확인 (`sacct`)
- [ ] 에러 로그 확인 (`*.err` 파일들)
- [ ] 결과 파일 생성 확인
- [ ] 로컬로 다운로드
- [ ] 지표 해석 및 결론 도출

---

## 💡 **추가 팁**

### 디버깅 모드 (단일 ROI로 빠른 테스트)

```bash
# V1만 먼저 테스트
python analysis/group_level/phase1_voxel_overlap.py --roi V1 --timestamp baseline32_deob_determin --subjects 01 02 03
```

### 결과 간단히 확인

```bash
# 모든 Phase summary 한번에
grep -r "Mean" derivatives/group_level/baseline32_deob_determin/V1/*/
```

### 시각화 파일만 모으기

```bash
# PNG 파일 모두 복사
find derivatives/group_level -name "*.png" -exec cp {} ./all_figures/ \;
```

---

**작성자**: Claude Code
**문서 버전**: 1.0
**업데이트**: 2025-12-16
