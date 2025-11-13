import os, re, csv
import numpy as np
import nibabel as nib
from nilearn import image

# --- 입력 경로 (당신이 이미 만든 결합 아틀라스) ---
atlas_dir = 'ProbAtlas_v4/subj_vol_all'  # 라벨 LUT가 여기 있을 가능성 큼
combined_atlas_path = 'derivatives/sub-01/roi/wang_atlas_combined.nii.gz'  # 위에서 저장한 경로

# --- 출력 경로 ---
output_roi_dir = 'derivatives/sub-01/roi'
os.makedirs(output_roi_dir, exist_ok=True)

# --- 참조 이미지(기능 데이터 격자) & EPI 마스크 ---
ref_img = nib.load(func_imgs[0])
try:
    epi_mask_img = fmri_glm.masker_.mask_img_
except Exception:
    print("exception")
    from nilearn.masking import compute_epi_mask
    epi_mask_img = compute_epi_mask(ref_img)

# 1) 라벨 LUT(인덱스→이름) 자동 탐지
def discover_label_lut(search_dir):
    lut = {}
    if not os.path.isdir(search_dir):
        return lut
    for fname in os.listdir(search_dir):
        if not fname.lower().endswith(('.txt', '.tsv', '.csv')):
            continue
        path = os.path.join(search_dir, fname)
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.reader(f, delimiter=('\t' if fname.lower().endswith('.tsv') else ','))
                for row in reader:
                    # 후보 포맷: idx name ...  / idx,name ...
                    if len(row) < 2:
                        # 공백 구분 가능성
                        parts = re.split(r'\s+', ' '.join(row).strip())
                        if len(parts) >= 2 and parts[0].isdigit():
                            lut[int(parts[0])] = parts[1]
                        continue
                    # 콤마/탭 2열이면
                    idx_str, name = row[0].strip(), row[1].strip()
                    if idx_str.isdigit():
                        lut[int(idx_str)] = name
        except Exception:
            continue
    return lut

lut = discover_label_lut(atlas_dir)
print(f"[INFO] Discovered {len(lut)} label entries from '{atlas_dir}'")
if lut:
    # 상위 10개 프리뷰
    print("Sample LUT:", list(lut.items())[:10])

# 2) 관심 ROI를 이름으로 매칭 (정규식)
#    V1v/V1d, V2v/V2d, V3v/V3d만 포함 (V3A/V3B 등 제외)
roi_regex = {
    'V1':  re.compile(r'^V1[vd]?$', flags=re.IGNORECASE),
    'V2':  re.compile(r'^V2[vd]?$', flags=re.IGNORECASE),
    'V3':  re.compile(r'^V3[vd]?$', flags=re.IGNORECASE),
    'hV4': re.compile(r'^hV4$',     flags=re.IGNORECASE),
}

def ids_from_lut(roi_name, lut):
    """LUT 이름에서 정규식으로 해당 ROI의 인덱스들 추출"""
    if not lut:
        return []  # LUT 못 찾으면 빈 리스트 반환
    regex = roi_regex[roi_name]
    ids = [idx for idx, nm in lut.items() if regex.match(nm)]
    return sorted(ids)

# LUT가 있으면 이름 기반으로, 없으면 데이터에서 unique만 안내
atlas_img = nib.load(combined_atlas_path)
atlas_data = atlas_img.get_fdata()
unique_vals = np.unique(atlas_data)
print("[INFO] Combined atlas uniques (first 30):", unique_vals[:30])

roi_id_map = {}
if lut:
    for roi in ['V1','V2','V3','hV4']:
        ids = ids_from_lut(roi, lut)
        roi_id_map[roi] = ids
        print(f"[MAP] {roi} → ids={ids}")
else:
    # LUT 없을 때는 수동으로 채워야 함(여기선 안내만)
    # 예시) roi_id_map = {'V1':[1,2], 'V2':[3,4], 'V3':[5,6], 'hV4':[7]}
    roi_id_map = {k: [] for k in ['V1','V2','V3','hV4']}
    print("[WARN] 라벨 LUT를 찾지 못했습니다. 위 unique 값을 참고해 roi_id_map을 수동 지정하세요.")

# 3) 각 ROI 마스크 생성 → 기능 격자에 최근접 리샘플 → EPI 마스크와 교집합 → 저장
def make_mask_from_ids(atlas_img, id_list):
    """정수 라벨 atlas에서 id_list에 해당하는 voxel을 1로 묶은 마스크"""
    if not id_list:
        # 빈 리스트면 전부 0 마스크
        return nib.Nifti1Image(np.zeros(atlas_img.shape, dtype=np.uint8),
                               atlas_img.affine, atlas_img.header)
    A = atlas_img.get_fdata()
    mask = np.isin(A, id_list).astype(np.uint8)
    return nib.Nifti1Image(mask, atlas_img.affine, atlas_img.header)

for roi_name, id_list in roi_id_map.items():
    roi_lab_img = make_mask_from_ids(atlas_img, id_list)

    # (안전) 기능 격자로 최근접 리샘플: 라벨 소실 방지
    roi_resampled = image.resample_to_img(roi_lab_img, ref_img, interpolation='nearest')

    # EPI 마스크와 교집합(뇌 밖 제거)
    roi_final = image.math_img("a * (b > 0)", a=roi_resampled, b=epi_mask_img)

    nz = int(np.count_nonzero(roi_final.get_fdata()))
    print(f"[{roi_name}] voxels after resample∩EPI =", nz)

    out_path = os.path.join(output_roi_dir, f'{roi_name}_mask.nii.gz')
    nib.save(roi_final, out_path)
    print(f"  -> saved: {out_path}")

# 최종 roi_files 딕셔너리 갱신(당신 노트북에서 쓰던 형식)
roi_files = {
    'V1':  os.path.join(output_roi_dir, 'V1_mask.nii.gz'),
    'V2':  os.path.join(output_roi_dir, 'V2_mask.nii.gz'),
    'V3':  os.path.join(output_roi_dir, 'V3_mask.nii.gz'),
    'hV4': os.path.join(output_roi_dir, 'hV4_mask.nii.gz'),
}
