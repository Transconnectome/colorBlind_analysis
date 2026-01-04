#!/usr/bin/env python3
"""
fMRIPrep 단계별 중간 결과 추적
목적: 어느 단계에서 posterior visual cortex가 손실되는지 파악

정상 피험자 (sub-05) vs 문제 피험자 (sub-01) 비교
"""

import nibabel as nib
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import subprocess

# Paths
# Work directory는 피험자별로 분리됨
work_dir_base = Path("/storage/connectome/haba6030")

fmriprep_out = Path("/storage/connectome/haba6030/fmriprep_out_afni_deoblique")
afni_input = Path("/storage/connectome/haba6030/colorBlind_data_afni_deoblique")
output_dir = Path("/scratch/connectome/haba6030/colorBlind/diagnostics/fmriprep_stage_tracking")
output_dir.mkdir(parents=True, exist_ok=True)

# 비교할 피험자
subjects = {
    "정상": "05",  # 100% overlap
    "문제": "01"   # 0% overlap
}

print("="*80)
print("fMRIPrep 단계별 중간 결과 추적")
print("="*80)
print()

# V1 ROI 위치 (참고용)
roi_dir = Path("/scratch/connectome/haba6030/colorBlind/derivatives")

def get_work_dir(subj_id):
    """피험자의 work directory 찾기"""
    # 패턴: fmriprep_work_afni_fast_01, fmriprep_work_afni_fast_05 등
    work_dir_pattern = work_dir_base / f"fmriprep_work_afni_fast_{subj_id}"
    if work_dir_pattern.exists():
        print(f"  ✓ Found work dir: {work_dir_pattern}")
        return work_dir_pattern

    # 다른 패턴도 시도
    for pattern in ["fmriprep_work_afni_fast_", "fmriprep_work_deoblique_v2_", "fmriprep_work_"]:
        work_dir = work_dir_base / f"{pattern}{subj_id}"
        if work_dir.exists():
            print(f"  ✓ Found work dir: {work_dir}")
            return work_dir

    # sub-XX 형태로도 찾기
    import glob
    matches = glob.glob(str(work_dir_base / f"fmriprep_work*/sub-{subj_id}"))
    if matches:
        work_dir = Path(matches[0]).parent
        print(f"  ✓ Found work dir: {work_dir}")
        return work_dir

    print(f"  ✗ Work directory not found for sub-{subj_id}")
    return None

def check_coverage(img_path, name, v1_data=None):
    """Image coverage 확인"""
    if not img_path.exists():
        print(f"    ✗ {name}: 파일 없음")
        return None

    img = nib.load(img_path)
    data = img.get_fdata()

    # Non-zero voxels
    coords = np.where(data > 0)
    if len(coords[0]) == 0:
        print(f"    ✗ {name}: 데이터 없음")
        return None

    n_voxels = len(coords[0])

    # Z-range (posterior-anterior)
    z_min, z_max = coords[2].min(), coords[2].max()
    z_range = z_max - z_min

    # Center of mass
    com = [np.mean(coords[i]) for i in range(3)]

    print(f"    ✓ {name}:")
    print(f"      - Voxels: {n_voxels}")
    print(f"      - Z-range: {z_min}-{z_max} ({z_range} slices)")
    print(f"      - Center: ({com[0]:.1f}, {com[1]:.1f}, {com[2]:.1f})")

    # V1 ROI와 비교 (있으면)
    if v1_data is not None:
        try:
            # Resample V1 to this space if needed
            if v1_data.shape == data.shape:
                overlap = np.sum((data > 0) & (v1_data > 0))
                v1_total = np.sum(v1_data > 0)
                if v1_total > 0:
                    overlap_pct = overlap / v1_total * 100
                    print(f"      - V1 overlap: {overlap}/{v1_total} voxels ({overlap_pct:.1f}%)")
        except:
            pass

    return {
        'n_voxels': n_voxels,
        'z_min': z_min,
        'z_max': z_max,
        'z_range': z_range,
        'com': com,
        'data': data,
        'img': img
    }

# ============================================================================
# 메인 추적
# ============================================================================

all_results = {}

for group_name, subj_id in subjects.items():
    print(f"\n{'='*80}")
    print(f"{group_name}: sub-{subj_id}")
    print(f"{'='*80}\n")

    results = {}
    all_results[subj_id] = results

    # V1 ROI 로드 (참고용)
    v1_file = roi_dir / f"sub-{subj_id}" / "roi_pipeline_afni_v3_fixed" / "V1_mask_afni_fixed.nii.gz"
    if v1_file.exists():
        v1_img = nib.load(v1_file)
        v1_data = v1_img.get_fdata()
        v1_coords = np.where(v1_data > 0)
        print(f"V1 ROI 참고 정보:")
        print(f"  - Z-range: {v1_coords[2].min()}-{v1_coords[2].max()}")
        print(f"  - Voxels: {len(v1_coords[0])}")
        print()
    else:
        v1_data = None
        print("V1 ROI 파일 없음\n")

    # ========================================================================
    # Stage 0: AFNI Deoblique Input (fMRIPrep 전)
    # ========================================================================
    print("Stage 0: AFNI Deoblique Input (fMRIPrep 입력)")
    print("-"*80)

    # Original BOLD (AFNI deobliqued)
    bold_input = afni_input / f"sub-{subj_id}" / "func" / f"sub-{subj_id}_task-rsvp_run-1_bold.nii.gz"
    results['input_bold'] = check_coverage(bold_input, "BOLD (AFNI deobliqued)")

    # T1w (AFNI deobliqued)
    t1w_input = afni_input / f"sub-{subj_id}" / "anat" / f"sub-{subj_id}_acq-mprage_T1w.nii.gz"
    results['input_t1w'] = check_coverage(t1w_input, "T1w (AFNI deobliqued)")

    print()

    # ========================================================================
    # Stage 1: Brain Extraction
    # ========================================================================
    print("Stage 1: Brain Extraction")
    print("-"*80)

    # Work directory 찾기
    work_dir = get_work_dir(subj_id)
    if work_dir is None:
        print("  ✗ Work directory 찾을 수 없음")
    else:
        print(f"  Work dir: {work_dir}")

        # T1w brain extraction - 여러 패턴으로 찾기
        anat_patterns = [
            "anat_preproc_wf",
            "**/anat_preproc_wf",
            "fmriprep_wf/single_subject*/anat_preproc_wf"
        ]

        for pattern in anat_patterns:
            anat_matches = list(work_dir.glob(pattern))
            if anat_matches:
                anat_preproc = anat_matches[0]
                print(f"    Found anat_preproc_wf: {anat_preproc.relative_to(work_dir)}")

                # ANTs brain extraction 결과 찾기
                brain_extraction_dirs = list(anat_preproc.glob("**/brain_extraction*"))
                if brain_extraction_dirs:
                    print(f"    Brain extraction directories: {len(brain_extraction_dirs)}")
                    for be_dir in brain_extraction_dirs[:2]:  # 처음 2개만
                        print(f"      {be_dir.relative_to(work_dir)}")

                        # Brain mask 찾기
                        brain_masks = list(be_dir.glob("**/*BrainExtractionMask.nii.gz"))
                        for mask_file in brain_masks[:1]:
                            results['t1w_brain_mask'] = check_coverage(mask_file, "T1w brain mask", v1_data)

                        # Brain extracted T1w
                        brain_files = list(be_dir.glob("**/*BrainExtractionBrain.nii.gz"))
                        for brain_file in brain_files[:1]:
                            results['t1w_brain'] = check_coverage(brain_file, "T1w brain extracted")
                break

    # Final output brain mask (anat)
    t1w_brain_final = fmriprep_out / f"sub-{subj_id}" / "anat" / f"sub-{subj_id}_space-MNI152NLin2009cAsym_desc-brain_mask.nii.gz"
    results['t1w_brain_mask_final'] = check_coverage(t1w_brain_final, "T1w brain mask (final, MNI)")

    print()

    # ========================================================================
    # Stage 2: BOLD → T1w Registration
    # ========================================================================
    print("Stage 2: BOLD → T1w Registration")
    print("-"*80)

    if work_dir:
        # BOLD preprocessing workflow 찾기
        func_patterns = [
            "func_preproc_*_wf",
            "**/func_preproc_*_wf",
            "fmriprep_wf/single_subject*/func_preproc_*_wf"
        ]

        for pattern in func_patterns:
            func_matches = list(work_dir.glob(pattern))
            if func_matches:
                func_preproc = func_matches[0]
                print(f"    Found func_preproc_wf: {func_preproc.relative_to(work_dir)}")

                # BOLD reference
                boldref_dirs = list(func_preproc.glob("**/bold_reference_wf"))
                for boldref_dir in boldref_dirs[:1]:
                    boldref_files = list(boldref_dir.glob("**/boldref.nii.gz"))
                    for boldref_file in boldref_files[:1]:
                        results['boldref'] = check_coverage(boldref_file, "BOLD reference")

                # BOLD brain mask (before registration)
                bold_brain_mask_dirs = list(func_preproc.glob("**/bold_brain_wf"))
                for mask_dir in bold_brain_mask_dirs[:1]:
                    mask_files = list(mask_dir.glob("**/bold_brain_mask.nii.gz"))
                    for mask_file in mask_files[:1]:
                        results['bold_brain_mask'] = check_coverage(mask_file, "BOLD brain mask (native)", v1_data)

                # BBR registration 결과
                reg_dirs = list(func_preproc.glob("**/bold_reg_wf"))
                if reg_dirs:
                    print(f"    Registration directories: {len(reg_dirs)}")
                    for reg_dir in reg_dirs[:1]:
                        # Registered BOLD
                        reg_files = list(reg_dir.glob("**/bold_reg.nii.gz"))
                        for reg_file in reg_files[:1]:
                            results['bold_reg_t1w'] = check_coverage(reg_file, "BOLD registered to T1w")
                break

    print()

    # ========================================================================
    # Stage 3: T1w → MNI Normalization
    # ========================================================================
    print("Stage 3: T1w → MNI Normalization")
    print("-"*80)

    # T1w in MNI
    t1w_mni = fmriprep_out / f"sub-{subj_id}" / "anat" / f"sub-{subj_id}_space-MNI152NLin2009cAsym_desc-preproc_T1w.nii.gz"
    results['t1w_mni'] = check_coverage(t1w_mni, "T1w in MNI space")

    # T1w brain mask in MNI
    t1w_mask_mni = fmriprep_out / f"sub-{subj_id}" / "anat" / f"sub-{subj_id}_space-MNI152NLin2009cAsym_desc-brain_mask.nii.gz"
    results['t1w_mask_mni'] = check_coverage(t1w_mask_mni, "T1w brain mask in MNI")

    print()

    # ========================================================================
    # Stage 4: BOLD → MNI (Final Output)
    # ========================================================================
    print("Stage 4: BOLD → MNI (Final Output)")
    print("-"*80)

    # BOLD in MNI
    bold_mni = fmriprep_out / f"sub-{subj_id}" / "func" / f"sub-{subj_id}_task-rsvp_run-1_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz"
    results['bold_mni'] = check_coverage(bold_mni, "BOLD in MNI space")

    # BOLD brain mask in MNI
    bold_mask_mni = fmriprep_out / f"sub-{subj_id}" / "func" / f"sub-{subj_id}_task-rsvp_run-1_space-MNI152NLin2009cAsym_res-2_desc-brain_mask.nii.gz"
    results['bold_mask_mni'] = check_coverage(bold_mask_mni, "BOLD brain mask in MNI (FINAL)", v1_data)

    print()

# ============================================================================
# 비교 분석
# ============================================================================

print("\n")
print("="*80)
print("단계별 비교 분석 (정상 vs 문제)")
print("="*80)
print()

stages = [
    ('input_bold', 'Stage 0: AFNI Input BOLD'),
    ('input_t1w', 'Stage 0: AFNI Input T1w'),
    ('t1w_brain_mask', 'Stage 1: T1w Brain Mask (extraction)'),
    ('bold_brain_mask', 'Stage 2: BOLD Brain Mask (native)'),
    ('bold_reg_t1w', 'Stage 2: BOLD → T1w (registered)'),
    ('t1w_mni', 'Stage 3: T1w → MNI'),
    ('t1w_mask_mni', 'Stage 3: T1w Mask → MNI'),
    ('bold_mni', 'Stage 4: BOLD → MNI (final)'),
    ('bold_mask_mni', 'Stage 4: BOLD Mask → MNI (FINAL)'),
]

print(f"{'Stage':<45} | {'정상(05)':<25} | {'문제(01)':<25} | {'차이'}")
print("-"*120)

for stage_key, stage_name in stages:
    normal_data = all_results.get("05", {}).get(stage_key)
    problem_data = all_results.get("01", {}).get(stage_key)

    if normal_data and problem_data:
        normal_z = f"Z:{normal_data['z_min']}-{normal_data['z_max']}"
        problem_z = f"Z:{problem_data['z_min']}-{problem_data['z_max']}"

        # Z-range 차이 (posterior coverage 지표)
        z_diff = normal_data['z_min'] - problem_data['z_min']

        if z_diff > 5:
            diff_msg = f"✗ 문제: {abs(z_diff)} slices 차이"
        elif z_diff < -5:
            diff_msg = f"⚠ 역전: {abs(z_diff)} slices"
        else:
            diff_msg = f"✓ 유사 ({z_diff} slices)"

        print(f"{stage_name:<45} | {normal_z:<25} | {problem_z:<25} | {diff_msg}")
    elif normal_data:
        normal_z = f"Z:{normal_data['z_min']}-{normal_data['z_max']}"
        print(f"{stage_name:<45} | {normal_z:<25} | {'MISSING':<25} | -")
    elif problem_data:
        problem_z = f"Z:{problem_data['z_min']}-{problem_data['z_max']}"
        print(f"{stage_name:<45} | {'MISSING':<25} | {problem_z:<25} | -")
    else:
        print(f"{stage_name:<45} | {'MISSING':<25} | {'MISSING':<25} | -")

# ============================================================================
# 시각화
# ============================================================================

print("\n")
print("="*80)
print("시각화 생성 중...")
print("="*80)

fig, axes = plt.subplots(4, 2, figsize=(12, 16))
fig.suptitle("fMRIPrep 단계별 추적: 정상(sub-05) vs 문제(sub-01)\n(Sagittal view, Z=20 slice)",
             fontsize=14, fontweight='bold')

stages_to_plot = [
    ('input_bold', 'Stage 0: AFNI Input BOLD'),
    ('t1w_brain_mask', 'Stage 1: T1w Brain Mask'),
    ('bold_brain_mask', 'Stage 2: BOLD Brain Mask'),
    ('bold_mask_mni', 'Stage 4: BOLD Mask (MNI, FINAL)'),
]

for idx, (stage_key, stage_name) in enumerate(stages_to_plot):
    # 정상 (sub-05)
    normal_data = all_results.get("05", {}).get(stage_key)
    if normal_data:
        data = normal_data['data']
        # 4D BOLD 처리 (시계열)
        if data.ndim == 4:
            data = data.mean(axis=3)  # 시간축 평균
        slice_data = data[:, :, 20].T
        axes[idx, 0].imshow(slice_data, cmap='gray', origin='lower')
        axes[idx, 0].set_title(f"정상(05): {stage_name}")
    else:
        axes[idx, 0].text(0.5, 0.5, "No Data", ha='center', va='center')
        axes[idx, 0].set_title(f"정상(05): {stage_name}")
    axes[idx, 0].axis('off')

    # 문제 (sub-01)
    problem_data = all_results.get("01", {}).get(stage_key)
    if problem_data:
        data = problem_data['data']
        # 4D BOLD 처리 (시계열)
        if data.ndim == 4:
            data = data.mean(axis=3)  # 시간축 평균
        slice_data = data[:, :, 20].T
        axes[idx, 1].imshow(slice_data, cmap='gray', origin='lower')
        axes[idx, 1].set_title(f"문제(01): {stage_name}")
    else:
        axes[idx, 1].text(0.5, 0.5, "No Data", ha='center', va='center')
        axes[idx, 1].set_title(f"문제(01): {stage_name}")
    axes[idx, 1].axis('off')

plt.tight_layout()
output_file = output_dir / "fmriprep_stage_tracking.png"
plt.savefig(output_file, dpi=150, bbox_inches='tight')
print(f"✓ Saved: {output_file}")
plt.close()

# ============================================================================
# 결론
# ============================================================================

print("\n")
print("="*80)
print("결론")
print("="*80)
print()

print("어느 단계에서 posterior coverage가 손실되는지 확인:")
print()

# Z-min 추적 (낮을수록 posterior 포함)
print("Posterior Coverage 추적 (Z-min):")
print("-"*80)
print(f"{'Stage':<45} | {'정상(05) Z-min':<15} | {'문제(01) Z-min':<15} | {'차이'}")
print("-"*80)

for stage_key, stage_name in stages:
    normal_data = all_results.get("05", {}).get(stage_key)
    problem_data = all_results.get("01", {}).get(stage_key)

    if normal_data and problem_data:
        normal_z = normal_data['z_min']
        problem_z = problem_data['z_min']
        diff = problem_z - normal_z

        if diff > 5:
            status = f"✗ 문제: +{diff}"
        elif diff > 0:
            status = f"⚠ 약간: +{diff}"
        else:
            status = f"✓ OK: {diff}"

        print(f"{stage_name:<45} | {normal_z:<15} | {problem_z:<15} | {status}")

print()
print()
print("다음 단계:")
print("1. Z-min이 크게 차이나는 stage 확인")
print("2. 해당 stage의 work directory 로그 확인")
print("3. 원인 파악 후 해결 방안 선택")
print()
print("="*80)
