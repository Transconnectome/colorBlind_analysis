#!/usr/bin/env python3
"""
Phase 2A: fMRI 패턴 추출

Phase 1 분석 결과에서 8개 색에 대한 fMRI 패턴 행렬 추출
출력: (8, n_voxels) numpy array
"""

import numpy as np
from pathlib import Path
import json

# 경로 설정
BASE_DIR = Path("/scratch/connectome/haba6030/colorBlind")
DERIVATIVES_DIR = BASE_DIR / "derivatives/V3_Comprehensive/BH2009_original_v3/baseline32_original_v3"
OUTPUT_DIR = BASE_DIR / "results/group_level/phase2a_data/patterns"

# 피험자 및 ROI 정보
HC_SUBJECTS = ['01', '02', '03', '04', '05', '06', '07']
CVD_SUBJECTS = ['08', '09', '10']
ALL_SUBJECTS = HC_SUBJECTS + CVD_SUBJECTS
ROIS = ['V1', 'V2', 'V3', 'hV4']

# 색 순서 (amplitudes에서의 순서)
COLOR_NAMES = ['Red', 'Orange', 'Yellow', 'Chartreuse',
               'Green', 'Cyan', 'Blue', 'Magenta']


def extract_pattern(subject_id, roi):
    """
    단일 피험자, 단일 ROI의 패턴 추출

    Returns:
        pattern: (8, n_voxels) - 8개 색에 대한 복셀별 활성
        n_voxels: 선택된 복셀 수
    """
    # New structure: derivatives/.../sub-{subject}/{roi}
    roi_dir = DERIVATIVES_DIR / f"sub-{subject_id}" / roi

    if not roi_dir.exists():
        print(f"  Warning: No ROI directory for sub-{subject_id} {roi} at {roi_dir}")
        return None, 0

    # 파일 경로
    amp_file = roi_dir / "amplitudes_z.npy"

    if not amp_file.exists():
        print(f"  Warning: amplitudes_z.npy not found in {roi_dir}")
        return None, 0

    # 데이터 로드
    # Shape: (n_runs, n_colors, n_selected_voxels)
    amplitudes = np.load(amp_file)

    # Transpose to (n_colors, n_selected_voxels, n_runs)
    amplitudes = amplitudes.transpose(1, 2, 0)

    # 런 간 평균
    pattern = amplitudes.mean(axis=2)  # (8, n_selected)

    n_voxels = pattern.shape[1]

    print(f"  Extracted: sub-{subject_id} {roi} - {n_voxels} voxels")

    return pattern, n_voxels


def compute_hc_mean(roi):
    """
    HC 피험자들의 평균 패턴 계산

    Returns:
        hc_mean: (8, n_voxels) - HC 그룹 평균
        n_voxels: 복셀 수 (첫 번째 HC 기준)
    """
    print(f"\nComputing HC mean for {roi}...")

    hc_patterns = []
    voxel_counts = []

    for subj in HC_SUBJECTS:
        pattern, n_vox = extract_pattern(subj, roi)
        if pattern is not None:
            hc_patterns.append(pattern)
            voxel_counts.append(n_vox)

    if not hc_patterns:
        print(f"  Error: No HC patterns found for {roi}")
        return None, 0

    # 복셀 수 확인
    if len(set(voxel_counts)) > 1:
        print(f"  Warning: Inconsistent voxel counts: {voxel_counts}")
        print(f"  Using minimum: {min(voxel_counts)}")
        # 최소 복셀 수로 truncate
        min_voxels = min(voxel_counts)
        hc_patterns = [p[:, :min_voxels] for p in hc_patterns]

    # 평균
    hc_mean = np.mean(hc_patterns, axis=0)  # (8, n_voxels)

    print(f"  HC mean: {hc_mean.shape} from {len(hc_patterns)} subjects")

    return hc_mean, hc_mean.shape[1]


def save_pattern(pattern, subject_id, roi):
    """패턴 저장"""
    if pattern is None:
        return

    # 디렉토리 생성
    if subject_id == 'HC_mean':
        output_dir = OUTPUT_DIR / "HC_mean"
    else:
        output_dir = OUTPUT_DIR / f"sub-{subject_id}"

    output_dir.mkdir(parents=True, exist_ok=True)

    # 저장
    output_file = output_dir / f"{roi}_pattern.npy"
    np.save(output_file, pattern)

    print(f"  Saved: {output_file}")


def create_metadata():
    """메타데이터 생성"""
    metadata = {
        "description": "fMRI patterns for Phase 2A",
        "created_date": "2025-12-19",
        "source": "derivatives/V3_Comprehensive/BH2009_original_v3/baseline32_original_v3",
        "preprocessing": "baseline32_deob_determin (deoblique, deterministic HRF)",
        "subjects": {
            "HC": HC_SUBJECTS,
            "CVD": CVD_SUBJECTS
        },
        "rois": ROIS,
        "colors": COLOR_NAMES,
        "pattern_shape": "(8 colors, n_voxels)",
        "voxel_selection": "selected_voxels_mask.npy from Phase 1",
        "averaging": "mean across runs"
    }

    metadata_file = OUTPUT_DIR / "metadata.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"\nMetadata saved: {metadata_file}")


def main():
    """메인 실행"""
    print("=" * 70)
    print("Phase 2A: Extracting fMRI Patterns")
    print("=" * 70)

    # 출력 디렉토리 생성
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # ROI별 처리
    for roi in ROIS:
        print(f"\n{'='*70}")
        print(f"Processing ROI: {roi}")
        print(f"{'='*70}")

        # 1. HC 개별 패턴 추출 및 저장
        print(f"\nExtracting individual HC patterns for {roi}...")
        hc_patterns = []
        for subj in HC_SUBJECTS:
            pattern, n_vox = extract_pattern(subj, roi)
            if pattern is not None:
                hc_patterns.append(pattern)
                save_pattern(pattern, subj, roi)

        # 2. HC 평균 계산
        if hc_patterns:
            # 복셀 수 맞추기
            voxel_counts = [p.shape[1] for p in hc_patterns]
            if len(set(voxel_counts)) > 1:
                print(f"  Warning: Inconsistent voxel counts: {voxel_counts}")
                min_voxels = min(voxel_counts)
                print(f"  Using minimum: {min_voxels}")
                hc_patterns = [p[:, :min_voxels] for p in hc_patterns]

            hc_mean = np.mean(hc_patterns, axis=0)
            n_voxels_hc = hc_mean.shape[1]
            print(f"  HC mean: {hc_mean.shape} from {len(hc_patterns)} subjects")
            save_pattern(hc_mean, 'HC_mean', roi)
        else:
            print(f"  Error: No HC patterns found for {roi}")
            hc_mean = None
            n_voxels_hc = 0

        # 2. CVD 피험자들
        print(f"\nExtracting CVD patterns for {roi}...")
        for subj in CVD_SUBJECTS:
            pattern, n_voxels = extract_pattern(subj, roi)

            # 복셀 수 맞추기
            if pattern is not None and n_voxels_hc > 0:
                if n_voxels != n_voxels_hc:
                    print(f"  Warning: sub-{subj} has {n_voxels} voxels, HC has {n_voxels_hc}")
                    print(f"  Truncating to {min(n_voxels, n_voxels_hc)} voxels")
                    pattern = pattern[:, :min(n_voxels, n_voxels_hc)]

            save_pattern(pattern, subj, roi)

    # 메타데이터 저장
    create_metadata()

    print("\n" + "="*70)
    print("Pattern extraction complete!")
    print("="*70)
    print(f"\nOutput directory: {OUTPUT_DIR}")
    print("\nNext steps:")
    print("1. Run: python phase2a_compute_rdm.py")
    print("2. Run: python phase2a_compute_metrics.py")
    print("3. Run: python phase2a_train_filter.py")


if __name__ == "__main__":
    main()
