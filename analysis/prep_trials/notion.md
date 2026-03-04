# Preprocessing: BOLD-T1w Registration 방법 비교
> Limited FOV + 높은 obliquity(29.5°) 조건에서 최적의 BOLD→T1w 정합 방법 탐색. **Method 3 (Header → MI) 채택**

## 배경
- **BOLD**: 29.5° sagittal obliquity, Partial FOV (후두엽만), 저해상도
- **T1w**: 정상 방향, 전뇌, 고해상도
- 기존 방법 (FLIRT→BBR): Partial FOV에서 BBR (Boundary-Based Registration, 경계 기반 정합)이 잘못된 경계에 맞출 위험
- 테스트 피험자: Sub-01, 03, 06

## 핵심 개념

> 💡 **BBR (Boundary-Based Registration)**: GM/WM 경계선에 맞추는 "주름 맞춤법"
> - ⚠️ Partial FOV에서는 보이지 않는 경계를 찾으려 하여 오정렬 위험
>
> **MI (Mutual Information, 상호 정보량)**: 전체 밝기 패턴의 통계적 관계로 정렬하는 "패턴 맞춤법"
> - ✅ 뇌의 일부만 보여도 겹치는 영역의 텍스처로 안전하게 정렬

---

## 방법 비교

| 방법 | 초기화 | 정밀 정합 | 예상 Dice | 위험도 |
|------|--------|-----------|-----------|--------|
| Method 1: FLIRT → BBR (baseline) | Blind search (360° 탐색) | BBR | 0.889 ✅ | 중 (운 좋게 성공) |
| Method 2: Header → BBR (FreeSurfer) | Header 좌표 (29.5°) | BBR | 0.80-0.92 | 중 |
| **Method 3: Header → MI** ⭐ | Header 좌표 (29.5°) | MI only | **0.90-0.95** | **낮음** |
| Method 4: Header → BBR 1-pass | Header 좌표 | BBR (Pass 1 생략) | < 0.80 | 높음 |

### ⭐ Method 3 채택 이유
- ✅ **Partial FOV에 강건** — 누락된 경계 무시, 보이는 영역의 텍스처만 사용
- ✅ **빠름** — ~30분 (vs Method 2의 ~10시간)
- ✅ **안전** — BBR의 잘못된 경계 스냅 위험 없음
- 정밀도 ~1mm (2mm fMRI 해상도에 충분)

> ⚠️ **BBR을 건너뛰는 이유**: BBR은 0.1mm 정밀도를 추구하지만, Partial FOV에서는 10mm 오차 위험. MI는 1mm 정밀도를 거의 무위험으로 보장

---

## 실행 상태

| 방법 | 소요 시간 | 상태 |
|------|-----------|------|
| Method 3 (Header → MI) | 3피험자 × 30분 = 1.5시간 | ✅ 완료 |
| Method 2 (Header → BBR) | 3피험자 × 8-10시간 = 24-30시간 | 시간 여유 시 |
| Method 1 (FLIRT → BBR) | 기존 결과에서 Dice 추출 | 재실행 불필요 |
| Method 4 (Header → BBR 1-pass) | — | Method 2 Dice > 0.85 시만 |

- **평가 지표**: MNI space brain mask의 Dice coefficient
- **비교 도구**: `compare_methods.py`

### 🔽 서버 운영 주의사항

**스토리지 관리**
- ❌ `/scratch/` (임시) → ✅ `/storage/` (영구)에 work directory 설정
- `--work-dir /storage/connectome/haba6030/fmriprep_work_method3/`

**컨테이너 권한**
- ❌ `apptainer run` → root 소유 파일 생성, 삭제 불가
- ✅ `apptainer exec --userns` 또는 `singularity exec --cleanenv`
