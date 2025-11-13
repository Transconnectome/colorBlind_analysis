#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
roi_builder.py
---------------
Combine left/right Wang ProbAtlas_v4 hemispheres and extract V1–V4 ROI masks.
Compatible with B&H(2009)-style analysis pipeline (atlas-based ROI definition).
"""

import os, re, csv, glob
import numpy as np
import nibabel as nib
from nilearn import image
from nilearn.masking import compute_epi_mask

# ==== 사용자 환경 설정 ====
atlas_dir = 'ProbAtlas_v4/subj_vol_all'
output_roi_dir = 'derivatives/sub-01/roi'
os.makedirs(output_roi_dir, exist_ok=True)

sub = '01' # 피험자 번호

project_dir = os.path.abspath('.') # 현재 프로젝트 디렉토리
output_dir = os.path.join(project_dir, f'output/pilot/sub-{sub}') # fMRIPrep 결과물이 있는 상위 폴더
fmriprep_dir = os.path.join(output_dir, 'func') # 전처리된 기능 영상 폴더
func_img = os.path.join(fmriprep_dir, f'sub-{sub}_task-rsvp_run-1_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz') # use first one

# ==== 4. 기능 데이터 기준 리샘플 + EPI 마스크 교집합 ====
# 주의: 아래 두 줄은 사용자 노트북 환경에 맞게 설정되어야 함
from nilearn import datasets
# 실제로는 fmri_glm.masker_.mask_img_ / func_imgs[0]을 불러오세요
ref_func_path = func_img  # 예시 placeholder
ref_img = nib.load(ref_func_path)
epi_mask_img = compute_epi_mask(ref_img)  # 없으면 자동 생성

# === 공용 유틸 ===
def resample_and_mask(bin_img):
    """기능 격자 최근접 리샘플 + EPI 마스크 교집합"""
    rs = image.resample_to_img(bin_img, ref_img, interpolation='nearest',
                               force_resample=True, copy_header=True)
    return image.math_img("a * (b > 0)", a=rs, b=epi_mask_img)

def save_and_report(name, img, outdir):
    out_path = os.path.join(outdir, f'{name}_mask.nii.gz')
    nib.save(img, out_path)
    nz = int(np.count_nonzero(img.get_fdata()))
    print(f"[{name}] nonzero voxels: {nz}  -> {out_path}")
    return out_path

# ==== 1. 좌/우 hemisphere 결합 ====
lh_atlas = nib.load(os.path.join(atlas_dir, 'maxprob_vol_lh.nii.gz'))
rh_atlas = nib.load(os.path.join(atlas_dir, 'maxprob_vol_rh.nii.gz'))
lh_data, rh_data = lh_atlas.get_fdata(), rh_atlas.get_fdata()
combined_data = lh_data + rh_data  # label disjoint → 단순 합산 OK
combined_atlas = nib.Nifti1Image(combined_data, lh_atlas.affine, lh_atlas.header)

combined_path = os.path.join(output_roi_dir, 'wang_atlas_combined.nii.gz')
nib.save(combined_atlas, combined_path)
print(f"[INFO] Combined atlas saved to: {combined_path}")

# === 2) LUT 시도 (있으면 maxprob에서 정수 ID로 추출) ===
def discover_label_lut(search_dir):
    lut = {}
    for root, _, files in os.walk(search_dir):
        for fname in files:
            if not fname.lower().endswith(('.txt', '.tsv', '.csv')):
                continue
            fpath = os.path.join(root, fname)
            try:
                with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                    reader = csv.reader(f, delimiter=('\t' if fname.endswith('.tsv') else ','))
                    for row in reader:
                        if len(row) < 2:
                            parts = re.split(r'\s+', ' '.join(row).strip())
                            if len(parts) >= 2 and parts[0].isdigit():
                                lut[int(parts[0])] = parts[1]
                            continue
                        idx, name = row[0].strip(), row[1].strip()
                        if idx.isdigit():
                            lut[int(idx)] = name
            except Exception:
                continue
    return lut

roi_regex = {
    'V1':  re.compile(r'^V1[vd]?$', re.IGNORECASE),
    'V2':  re.compile(r'^V2[vd]?$', re.IGNORECASE),
    'V3':  re.compile(r'^V3[vd]?$', re.IGNORECASE),
    'hV4': re.compile(r'^hV4$',     re.IGNORECASE),
}

def ids_from_lut(roi_name, lut):
    regex = roi_regex[roi_name]
    return sorted([idx for idx, nm in lut.items() if regex.match(nm)])

lut = discover_label_lut(atlas_dir)
print(f"[INFO] Discovered {len(lut)} label entries from {atlas_dir}")

roi_files = {}
if len(lut) > 0:
    print("[INFO] Using LUT + maxprob for ROI extraction")
    atlas_img = nib.load(combined_path)
    for roi in ['V1','V2','V3','hV4']:
        ids = ids_from_lut(roi, lut)
        if not ids:
            print(f"[WARN] No IDs found in LUT for {roi}. Will try prob-maps fallback later.")
            continue
        data = np.isin(atlas_img.get_fdata(), ids).astype(np.uint8)
        bin_img = nib.Nifti1Image(data, atlas_img.affine, atlas_img.header)
        roi_final = resample_and_mask(bin_img)
        roi_files[roi] = save_and_report(roi, roi_final, output_roi_dir)

# === 3) LUT 실패 또는 일부 ROI 누락 시: 확률 볼륨 기반 Fallback ===
needed = [r for r in ['V1','V2','V3','hV4'] if r not in roi_files]
if needed:
    print("[INFO] Falling back to probability maps for:", needed)

    # (재귀) 파일 검색: V1v/V1d, V2v/V2d, V3v/V3d, hV4 포함 파일
    cand_files = []
    for ext in ('*.nii', '*.nii.gz'):
        cand_files += glob.glob(os.path.join(atlas_dir, '**', ext), recursive=True)

    def pick_prob_files(keyword):
        # 파일명에 키워드 포함 & 'prob' 또는 'maxprob' 우선
        kw = keyword.lower()
        out = [p for p in cand_files if kw in os.path.basename(p).lower()]
        # prob 우선 정렬
        out.sort(key=lambda x: (('prob' not in os.path.basename(x).lower()),
                                ('maxprob' in os.path.basename(x).lower())))
        return out

    # 각 ROI별로 모을 키워드 정의
    roi_keywords = {
        'V1':  ['v1v', 'v1d', 'v1'],   # v/d 우선, 없으면 v1 범용
        'V2':  ['v2v', 'v2d', 'v2'],
        'V3':  ['v3v', 'v3d', 'v3'],
        'hV4': ['hv4', 'v4'],          # hV4 명시가 없으면 v4로 완화
    }

    THR = 0.30  # 확률 임계값 (필요시 0.2로 낮춰보세요)

    for roi in needed:
        files = []
        for kw in roi_keywords[roi]:
            files += pick_prob_files(kw)
        # 좌/우·v/d 중복을 허용하고 모두 합산
        if not files:
            print(f"[WARN] No probability files matched for {roi}. Please check atlas_dir.")
            continue

        # 확률 맵 합산 → 임계값
        acc = None
        for fp in files:
            try:
                img = nib.load(fp)
                dat = img.get_fdata()
                if acc is None:
                    # 좌표계가 다를 수 있으므로 먼저 atlas 기준으로 resample 후 누적
                    # (여기서는 일단 같은 그리드라고 가정하고 합산)
                    acc = np.zeros_like(dat, dtype=np.float32)
                if acc.shape != dat.shape:
                    # 형태가 다르면 atlas 결합 좌표로 맞춤
                    base = nib.load(combined_path)
                    img_r = image.resample_to_img(img, base, interpolation='continuous',
                                                  force_resample=True, copy_header=True)
                    dat = img_r.get_fdata()
                acc += dat
            except Exception as e:
                print(f"[WARN] skip {fp}: {e}")
                continue

        if acc is None:
            print(f"[WARN] Failed to build prob sum for {roi}")
            continue

        bin_data = (acc > THR).astype(np.uint8)
        bin_img = nib.Nifti1Image(bin_data, img.affine, img.header)
        roi_final = resample_and_mask(bin_img)
        roi_files[roi] = save_and_report(roi, roi_final, output_roi_dir)

print("\n[OK] ROI extraction completed.")
print("roi_files =", roi_files)