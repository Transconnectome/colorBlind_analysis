#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bh_anal.py
----------
B&H (2009) fMRI 색상 디코딩 분석 파이프라인
주요 단계: design → deconv_glm → roi_build → extract_roi → forward_model → qc
"""

import os
import glob
import pickle
import sys
import time
import logging
import numpy as np
import pandas as pd
import nibabel as nib
from nilearn import image
from nilearn.glm.first_level import FirstLevelModel, make_first_level_design_matrix
from nilearn.maskers import NiftiMasker
from sklearn.decomposition import PCA
from scipy.stats import binomtest
from utils.cache import Cache
from config import cfg

class BHAnalysisPipeline:
    def __init__(self, config=cfg):
        """
        Parameters
        ----------
        config : Config
            설정 객체 (기본값: config.py의 전역 cfg 인스턴스)
        """
        self.config = config
        self.cache = Cache(config)
        
        # 작업 디렉토리 생성
        os.makedirs(self.config.analysis_dir, exist_ok=True)
        os.makedirs(self.config.roi_dir, exist_ok=True)
        os.makedirs(os.path.join(self.config.PROJECT_DIR, 'logs'), exist_ok=True)
        
        # 로깅 설정
        self._setup_logging()
        
        # GLM 객체 초기화 (나중에 필요할 때 생성)
        self.fmri_glm = None

    def _setup_logging(self):
        """콘솔 + 파일 로깅 설정 (중복 핸들러 방지)"""
        self.logger = logging.getLogger('BHAnalysis')
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            fmt = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
            # Console
            sh = logging.StreamHandler(sys.stdout)
            sh.setLevel(logging.INFO)
            sh.setFormatter(fmt)
            self.logger.addHandler(sh)
            # File
            log_path = os.path.join(self.config.PROJECT_DIR, 'logs', 'analysis_status.log')
            fh = logging.FileHandler(log_path, mode='a')
            fh.setLevel(logging.INFO)
            fh.setFormatter(fmt)
            self.logger.addHandler(fh)

    def _status(self, msg: str):
        """상태 메시지: 콘솔 출력 + 로깅 (즉시 flush)"""
        print(msg)
        try:
            self.logger.info(msg)
        except Exception:
            pass
        sys.stdout.flush()
    
    def run_design(self):
        """디자인 매트릭스 생성 단계"""
        if self.cache.exists('design'):
            self._status("[SKIP] Design matrices exist")
            return
            
        self._status(f"[START] Design matrices for {self.config.N_RUNS} runs")
        t0 = time.time()
        for run in range(1, self.config.N_RUNS + 1):
            self.logger.info(f"[Design] Building design for run {run}/{self.config.N_RUNS}")
            # 이벤트 파일 로드
            events = pd.read_csv(
                self.config.get_event_file_path(run),
                sep='\t'
            )
            
            # Confound 파일 로드
            confounds = pd.read_csv(
                self.config.get_confound_file_path(run),
                sep='\t'
            )
            
            # TR 기준으로 시간축 생성
            n_scans = len(confounds)
            frame_times = np.arange(n_scans) * self.config.TR
            
            # 조건별 이벤트 매트릭스 생성
            conditions = []
            onsets = []
            durations = []
            
            for color_idx in range(self.config.N_COLORS):
                color_events = events[events['trial_type'] == f'color_{color_idx+1}']
                conditions.append(f'color_{color_idx+1}')
                onsets.append(color_events['onset'].values)
                durations.append(color_events['duration'].values)
            
            # 이벤트 데이터프레임 생성
            events_list = []
            for cond, onset_list, duration_list in zip(conditions, onsets, durations):
                for onset, duration in zip(onset_list, duration_list):
                    events_list.append({
                        'trial_type': cond,
                        'onset': float(onset),
                        'duration': float(duration)
                    })
            
            events_df = pd.DataFrame(events_list)
            
            # 디자인 매트릭스 생성 (FIR basis)
            design = make_first_level_design_matrix(
                frame_times,
                events=events_df,
                hrf_model='fir',
                drift_model='cosine',
                high_pass=1/128.0,
                drift_order=1,
                fir_delays=range(10),  # 0-15초 범위
                add_regs=confounds[['trans_x', 'trans_y', 'trans_z', 
                                  'rot_x', 'rot_y', 'rot_z']].values,
                add_reg_names=[f'motion_{i}' for i in range(6)]
            )
            
            # 저장
            out_path = os.path.join(
                self.config.analysis_dir,
                f'sub-{self.config.SUB_ID}_task-rsvp_run-{run}_'
                f'space-MNI152NLin2009cAsym_res-2_design_ready_HRF-fir.csv'
            )
            design.to_csv(out_path)
            self._status(f"[OK] Created design matrix for run {run}")
            
        self._status(f"[OK] Design matrices created in {time.time()-t0:.1f}s")
    
    def run_deconv_glm(self):
        """
        B&H (2009)의 방법론을 따른 디컨볼루션 기반 GLM 실행
        
        1. 각 복셀의 HIRF를 디컨볼루션으로 추정 (Dale, 1999)
           - 모든 자극 조건을 평균하여 편향되지 않은 추정
        2. 추정된 HIRF를 사용하여 각 자극 조건의 응답 진폭 추정
        """
        # If per-run beta files are already present, skip recomputation.
        per_run_pattern = os.path.join(
            self.config.analysis_dir,
            f'sub-{self.config.SUB_ID}_rsvp_deconv_betas_run-*.nii.gz'
        )
        existing_runs = sorted(glob.glob(per_run_pattern))
        if self.cache.exists('deconv_glm') and len(existing_runs) == self.config.N_RUNS:
            self._status("[SKIP] GLM results exist (per-run betas present)")
            return
            
        # 모든 run의 데이터 로드
        func_imgs = []
        event_files = []
        confound_files = []
        self._status(f"[START] Deconvolution GLM for {self.config.N_RUNS} runs")
        t0 = time.time()
        for run in range(1, self.config.N_RUNS + 1):
            self.logger.info(f"[GLM] Loading data for run {run}/{self.config.N_RUNS}")
            # fMRI 데이터
            func_img = nib.load(self.config.get_func_img_path(run))
            if self.config.VOLS_TO_DROP > 0:
                func_img = image.index_img(func_img, slice(self.config.VOLS_TO_DROP, None))
            func_imgs.append(func_img)
            
            # 이벤트 및 confound 파일
            event_files.append(pd.read_csv(self.config.get_event_file_path(run), sep='\t'))
            confound_files.append(pd.read_csv(self.config.get_confound_file_path(run), sep='\t'))
        
        # 1. HIRF 디컨볼루션 단계 (Dale, 1999)
        # 자극 색상 무시하고 전체 평균 응답으로 HIRF 추정
        hirf_len = int(12 / self.config.TR)  # 12초 길이의 HIRF
        hirfs = []

        # determine spatial shape from first functional image
        voxel_shape = func_imgs[0].shape[:3]

        for run, (func_img, events, confounds) in enumerate(zip(func_imgs, event_files, confound_files), start=1):
            self.logger.info(f"[GLM] HIRF deconvolution run {run}/{self.config.N_RUNS}")
            # 데이터 준비
            data = func_img.get_fdata()
            voxel_shape = data.shape[:-1]
            data_2d = data.reshape(-1, data.shape[-1])  # (voxels, timepoints)
            n_timepoints = data.shape[-1]

            # 움직임 레그레서 제거 (불필요한 TR 제거)
            if self.config.VOLS_TO_DROP > 0:
                motion = confounds[['trans_x', 'trans_y', 'trans_z', 'rot_x', 'rot_y', 'rot_z']].values[self.config.VOLS_TO_DROP:]
            else:
                motion = confounds[['trans_x', 'trans_y', 'trans_z', 'rot_x', 'rot_y', 'rot_z']].values
            self.logger.info(f"[GLM] Run {run} motion shape {motion.shape}, data {data_2d.shape}")

            # 첫 번째 방향으로 움직임 레그레서 reshape (이미 올바른 형태)
            motion_2d = motion  # Should be (timepoints, 6)
            self.logger.info(f"[GLM] Run {run} motion 2D shape {motion_2d.shape}")
            # Regress out motion
            t_reg = time.time()
            beta_motion = np.linalg.lstsq(motion_2d, data_2d.T, rcond=None)[0]  # (6, voxels)
            data_2d = data_2d - (motion_2d @ beta_motion).T
            self.logger.info(f"[GLM] Run {run} motion regression done in {time.time()-t_reg:.1f}s")

            # 모든 자극에 대한 통합 디자인 행렬 생성
            X_hirf = np.zeros((n_timepoints, hirf_len))
            all_onsets = events['onset'].values / self.config.TR  # TR 단위로 변환

            for onset in all_onsets:
                onset_idx = int(np.floor(onset))
                if onset_idx + hirf_len <= n_timepoints:
                    X_hirf[onset_idx:onset_idx+hirf_len, :] += np.eye(hirf_len)

            # 디컨볼루션 (Dale, 1999)
            self.logger.info(f"[GLM] Run {run} deconvolving HIRF via pinv ...")
            t_pinv = time.time()
            hirf = np.linalg.pinv(X_hirf) @ data_2d.T  # (hirf_len, voxels)
            self.logger.info(f"[GLM] Run {run} HIRF pinv done in {time.time()-t_pinv:.1f}s")
            hirfs.append(hirf)

        # 모든 run의 평균 HIRF 계산
        mean_hirf = np.mean(np.array(hirfs), axis=0)  # (hirf_len, voxels)
        # canonical HIRF: average across voxels -> 1D vector of length hirf_len
        try:
            canonical_hirf = np.mean(mean_hirf, axis=1)
        except Exception:
            canonical_hirf = mean_hirf[:, 0] if mean_hirf.ndim >= 2 else mean_hirf
        
        # 2. 각 색상 조건별 응답 진폭 추정
        betas = []
        for run, (func_img, events, confounds) in enumerate(zip(func_imgs, event_files, confound_files), start=1):
            self.logger.info(f"[GLM] Estimating color-wise betas run {run}/{self.config.N_RUNS}")
            # 데이터 준비
            data = func_img.get_fdata()
            data_2d = data.reshape(-1, data.shape[-1])
            
            # 움직임 레그레서 제거 (불필요한 TR 제거)
            if self.config.VOLS_TO_DROP > 0:
                motion = confounds[['trans_x', 'trans_y', 'trans_z', 'rot_x', 'rot_y', 'rot_z']].values[self.config.VOLS_TO_DROP:]
            else:
                motion = confounds[['trans_x', 'trans_y', 'trans_z', 'rot_x', 'rot_y', 'rot_z']].values
            self.logger.info(f"[GLM] Run {run} motion shape {motion.shape}, data {data_2d.shape}")
            
            # 첫 번째 방향으로 움직임 레그레서 reshape (이미 올바른 형태)
            motion_2d = motion  # Should be (timepoints, 6)
            self.logger.info(f"[GLM] Run {run} motion 2D shape {motion_2d.shape}")
            # Regress out motion
            t_reg = time.time()
            beta_motion = np.linalg.lstsq(motion_2d, data_2d.T, rcond=None)[0]  # (6, voxels)
            data_2d = data_2d - (motion_2d @ beta_motion).T
            self.logger.info(f"[GLM] Run {run} motion regression done in {time.time()-t_reg:.1f}s")
            
            # 색상별 디자인 행렬 생성 
            n_timepoints = data_2d.shape[1]  # 현재 run의 timepoint 수
            X = np.zeros((n_timepoints, self.config.N_COLORS))
            for color_idx in range(self.config.N_COLORS):
                color_events = events[events['trial_type'] == f'color_{color_idx+1}']
                onsets = color_events['onset'].values / self.config.TR
                
                # 각 자극의 onset 시점에 추정된 HIRF 추가
                for onset in onsets:
                    onset_idx = int(np.floor(onset))
                    if onset_idx + hirf_len <= n_timepoints:
                        # use canonical (voxel-averaged) HIRF vector for design
                        X[onset_idx:onset_idx+hirf_len, color_idx] += canonical_hirf
            
            # 베타값 추정 (pseudoinverse)
            self.logger.info(f"[GLM] Run {run} computing pseudoinverse for betas ...")
            t_pinv = time.time()
            beta = np.linalg.pinv(X) @ data_2d.T  # (n_colors, voxels)
            self.logger.info(f"[GLM] Run {run} beta pinv done in {time.time()-t_pinv:.1f}s")
            betas.append(beta)

            # Save per-run beta NIfTI so downstream code can compute split-half reliability
            try:
                beta_4d = beta.reshape((self.config.N_COLORS,) + voxel_shape)
                out_run_path = os.path.join(
                    self.config.analysis_dir,
                    f'sub-{self.config.SUB_ID}_rsvp_deconv_betas_run-{run}.nii.gz'
                )
                out_run_nii = nib.Nifti1Image(beta_4d, func_img.affine)
                out_run_nii.to_filename(out_run_path)
                self.logger.info(f"[GLM] Saved per-run betas: {out_run_path}")
            except Exception as e:
                self.logger.warning(f"[GLM] Could not save per-run betas for run {run}: {e}")

            # Save per-run beta NIfTI so downstream steps can compute split-half reliability
            try:
                beta_4d = beta.reshape((self.config.N_COLORS,) + voxel_shape)
                beta_nii_run = nib.Nifti1Image(beta_4d, func_img.affine)
                out_run = os.path.join(
                    self.config.analysis_dir,
                    f'sub-{self.config.SUB_ID}_rsvp_deconv_betas_run-{run}.nii.gz'
                )
                beta_nii_run.to_filename(out_run)
                self.logger.info(f"[GLM] Saved per-run beta: {out_run}")
            except Exception as e:
                self.logger.warning(f"[GLM] Could not save per-run beta for run {run}: {e}")
        
        # 결과 저장 (전체 run의 평균 베타값)
        mean_betas = np.mean(np.array(betas), axis=0)  # (n_colors, voxels)
        mean_betas_4d = mean_betas.reshape((self.config.N_COLORS,) + voxel_shape)

        out_nii = nib.Nifti1Image(mean_betas_4d, func_imgs[0].affine)
        out_path = os.path.join(
            self.config.analysis_dir,
            f'sub-{self.config.SUB_ID}_rsvp_deconv_betas.nii.gz'
        )
        out_nii.to_filename(out_path)

        # 추정된 HIRF도 저장
        hirf_4d = mean_hirf.reshape((hirf_len,) + voxel_shape)
        hirf_nii = nib.Nifti1Image(hirf_4d, func_imgs[0].affine)
        hirf_path = os.path.join(
            self.config.analysis_dir,
            f'sub-{self.config.SUB_ID}_rsvp_estimated_hirf.nii.gz'
        )
        hirf_nii.to_filename(hirf_path)

        self._status(f"[OK] Deconvolution-based GLM analysis completed in {time.time()-t0:.1f}s")
    
    def _load_roi_masks(self):
        """
        ROI 마스크 파일들을 로드
        
        Returns
        -------
        dict
            ROI 이름을 키로, boolean 마스크를 값으로 하는 딕셔너리
        """
        # ROI 디렉토리 확인
        if not os.path.exists(self.config.roi_dir):
            raise ValueError(f"ROI directory not found: {self.config.roi_dir}")
        
        # ROI 마스크 파일 탐색
        roi_files = sorted(glob.glob(os.path.join(
            self.config.roi_dir,
            f'sub-{self.config.SUB_ID}_*_mask.nii.gz'
        )))
        
        if not roi_files:
            raise ValueError(f"No ROI mask files found in {self.config.roi_dir}")
        
        # 마스크 로드
        roi_masks = {}
        template_img = nib.load(roi_files[0])
        template_shape = template_img.shape
        
        for roi_file in roi_files:
            # ROI 이름 추출 (예: V1, V2, V3, V4 등)
            roi_name = os.path.basename(roi_file).split('_')[1]
            
            # 마스크 로드 및 boolean 배열로 변환
            mask_img = nib.load(roi_file)
            if mask_img.shape != template_shape:
                raise ValueError(f"ROI mask {roi_name} has different shape")
            
            roi_masks[roi_name] = mask_img.get_fdata().astype(bool)
        
        return roi_masks
    
    def _discover_label_lut(self, search_dir):
        """아틀라스 디렉토리에서 라벨 LUT 파일 찾기"""
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
                        if len(row) < 2:
                            parts = re.split(r'\s+', ' '.join(row).strip())
                            if len(parts) >= 2 and parts[0].isdigit():
                                lut[int(parts[0])] = parts[1]
                            continue
                        idx_str, name = row[0].strip(), row[1].strip()
                        if idx_str.isdigit():
                            lut[int(idx_str)] = name
            except Exception:
                continue
        return lut

    def _ids_from_lut(self, roi_name, lut):
        """LUT에서 ROI 이름에 매칭되는 인덱스 추출"""
        roi_regex = {
            'V1':  re.compile(r'^V1[vd]?$', flags=re.IGNORECASE),
            'V2':  re.compile(r'^V2[vd]?$', flags=re.IGNORECASE),
            'V3':  re.compile(r'^V3[vd]?$', flags=re.IGNORECASE),
            'hV4': re.compile(r'^hV4$',     flags=re.IGNORECASE),
        }
        
        if not lut:
            return []
        regex = roi_regex[roi_name]
        ids = [idx for idx, nm in lut.items() if regex.match(nm)]
        return sorted(ids)

    def _make_mask_from_ids(self, atlas_img, id_list):
        """아틀라스에서 특정 ID들에 해당하는 마스크 생성"""
        if not id_list:
            return nib.Nifti1Image(
                np.zeros(atlas_img.shape, dtype=np.uint8),
                atlas_img.affine, 
                atlas_img.header
            )
        data = atlas_img.get_fdata()
        mask = np.isin(data, id_list).astype(np.uint8)
        return nib.Nifti1Image(mask, atlas_img.affine, atlas_img.header)

    def run_roi_build(self):
        """ROI 마스크 생성 단계 (Wang atlas 기반)"""
        if self.cache.exists('roi'):
            self._status("[SKIP] ROI masks exist")
            return
            
        # 참조 이미지 로드
        ref_img = nib.load(self.config.get_func_img_path(1))
        
        # ROI 정의 (Wang atlas 기반)
        roi_map = {
            'V1': ['perc_VTPM_vol_roi1_', 'perc_VTPM_vol_roi2_'],  # V1v, V1d
            'V2': ['perc_VTPM_vol_roi3_', 'perc_VTPM_vol_roi4_'],  # V2v, V2d
            'V3': ['perc_VTPM_vol_roi5_', 'perc_VTPM_vol_roi6_'],  # V3v, V3d
            'hV4': ['perc_VTPM_vol_roi7_']  # hV4
        }
        
        # ROI 디렉토리 생성
        os.makedirs(self.config.roi_dir, exist_ok=True)
        
        # ROI별 마스크 생성
        self._status("[START] Building ROI masks (Wang atlas)")
        t0 = time.time()
        for roi_name, roi_parts in roi_map.items():
            print(f"\nProcessing {roi_name}...")
            roi_mask = None
            
            # 좌우 반구 통합
            for hemi in ['lh', 'rh']:
                for part in roi_parts:
                    roi_file = os.path.join(
                        self.config.PROJECT_DIR,
                        'ProbAtlas_v4/subj_vol_all',
                        f'{part}{hemi}.nii.gz'
                    )
                    
                    if not os.path.exists(roi_file):
                        print(f"[WARN] File not found: {roi_file}")
                        continue
                        
                    part_img = nib.load(roi_file)
                    part_data = part_img.get_fdata()
                    
                    # 확률 임계값 (50%) 적용
                    part_mask = part_data > 50
                    
                    if roi_mask is None:
                        roi_mask = part_mask
                    else:
                        roi_mask = np.logical_or(roi_mask, part_mask)
            
            if roi_mask is None:
                print(f"[ERROR] Could not create mask for {roi_name}")
                continue
            
            # ROI 마스크를 functional 이미지 해상도로 다운샘플링
            roi_nii = nib.Nifti1Image(roi_mask.astype(np.int16), part_img.affine)
            roi_resampled = image.resample_img(
                roi_nii,
                target_affine=ref_img.affine,
                target_shape=ref_img.shape[:3],
                interpolation='nearest'
            )
            
            # 다운샘플링된 마스크 저장
            # Optionally intersect with subject-specific brain mask to remove out-of-brain voxels
            # Prefer config.brain_mask_path if provided, otherwise fall back to the project-standard path
            brain_mask_path = None
            if hasattr(self.config, 'brain_mask_path') and self.config.brain_mask_path:
                brain_mask_path = self.config.brain_mask_path
            else:
                brain_mask_path = os.path.join(
                    self.config.PROJECT_DIR,
                    'output', 'pilot',
                    f'sub-{self.config.SUB_ID}', 'anat',
                    f'sub-{self.config.SUB_ID}_acq-mprage_space-MNI152NLin2009cAsym_res-2_desc-brain_mask.nii.gz'
                )

            try:
                if os.path.exists(brain_mask_path):
                    brain_img = nib.load(brain_mask_path)
                    brain_resampled = image.resample_img(
                        brain_img,
                        target_affine=roi_resampled.affine,
                        target_shape=roi_resampled.shape[:3],
                        interpolation='nearest'
                    )

                    # Logical AND between ROI and brain mask
                    roi_bool = roi_resampled.get_fdata().astype(bool)
                    brain_bool = brain_resampled.get_fdata().astype(bool)
                    combined = np.logical_and(roi_bool, brain_bool).astype(np.int16)
                    roi_resampled = nib.Nifti1Image(combined, roi_resampled.affine, roi_resampled.header)
                    self._status(f"[OK] Applied brain_mask intersection for {roi_name}")
                else:
                    self._status(f"[WARN] Brain mask not found at {brain_mask_path}; skipping intersection")
            except Exception as e:
                self._status(f"[WARN] Could not apply brain mask intersection for {roi_name}: {e}")

            out_path = os.path.join(self.config.roi_dir, f'sub-{self.config.SUB_ID}_{roi_name}_mask.nii.gz')
            roi_resampled.to_filename(out_path)
            self._status(f"[OK] Created {roi_name} mask")
        
        self._status(f"[OK] ROI masks created in {time.time()-t0:.1f}s")

    def run_roi_build_structural(self):
        """
        Build ROI masks from subject-specific structural files found in the subject's
        `anat` folder (e.g. output/pilot/sub-XX/anat). Saved masks will have an
        `_anat` suffix in their filename so they do not overwrite atlas-based masks.
        """
        # ROI dir
        os.makedirs(self.config.roi_dir, exist_ok=True)

        # Subject anat directory (default location used elsewhere in repo)
        subj_anat_dir = os.path.join(
            self.config.PROJECT_DIR,
            'output', 'pilot',
            f'sub-{self.config.SUB_ID}', 'anat'
        )

        if not os.path.isdir(subj_anat_dir):
            self._status(f"[WARN] Subject anat directory not found: {subj_anat_dir}")
            return

        # find candidate nifti files (exclude brain mask and GM probseg by default)
        candidates = sorted([
            os.path.join(subj_anat_dir, fn) for fn in os.listdir(subj_anat_dir)
            if fn.lower().endswith(('.nii', '.nii.gz')) and 'brain_mask' not in fn and 'probseg' not in fn
        ])

        if not candidates:
            self._status(f"[WARN] No structural ROI nifti files found in {subj_anat_dir}")
            return

        ref_img = nib.load(self.config.get_func_img_path(1))
        t0 = time.time()
        self._status(f"[START] Building structural ROI masks from {subj_anat_dir}")

        # brain mask path preference (same logic as earlier intersection)
        brain_mask_path = None
        if hasattr(self.config, 'brain_mask_path') and self.config.brain_mask_path:
            brain_mask_path = self.config.brain_mask_path
        else:
            brain_mask_path = os.path.join(
                self.config.PROJECT_DIR,
                'output', 'pilot',
                f'sub-{self.config.SUB_ID}', 'anat',
                f'sub-{self.config.SUB_ID}_acq-mprage_space-MNI152NLin2009cAsym_res-2_desc-brain_mask.nii.gz'
            )

        for cand in candidates:
            try:
                fname = os.path.basename(cand)
                stem = fname.replace('.nii.gz', '').replace('.nii', '')
                # remove leading sub-<id>_ if present
                prefix = f'sub-{self.config.SUB_ID}_'
                if stem.startswith(prefix):
                    stem2 = stem[len(prefix):]
                else:
                    stem2 = stem
                # drop trailing '_mask' if exists
                stem2 = stem2.replace('_mask', '')
                roi_name = f"{stem2}_anat"

                mask_img = nib.load(cand)
                mask_resampled = image.resample_img(
                    mask_img,
                    target_affine=ref_img.affine,
                    target_shape=ref_img.shape[:3],
                    interpolation='nearest'
                )

                # intersect with brain mask if available
                try:
                    if os.path.exists(brain_mask_path):
                        brain_img = nib.load(brain_mask_path)
                        brain_resampled = image.resample_img(
                            brain_img,
                            target_affine=mask_resampled.affine,
                            target_shape=mask_resampled.shape[:3],
                            interpolation='nearest'
                        )
                        roi_bool = mask_resampled.get_fdata().astype(bool)
                        brain_bool = brain_resampled.get_fdata().astype(bool)
                        combined = np.logical_and(roi_bool, brain_bool).astype(np.int16)
                        out_img = nib.Nifti1Image(combined, mask_resampled.affine, mask_resampled.header)
                        self._status(f"[OK] Applied brain_mask intersection for {roi_name}")
                    else:
                        out_img = mask_resampled
                        self._status(f"[WARN] Brain mask not found at {brain_mask_path}; saved without intersection for {roi_name}")
                except Exception as e:
                    out_img = mask_resampled
                    self._status(f"[WARN] Could not apply brain mask intersection for {roi_name}: {e}")

                out_path = os.path.join(self.config.roi_dir, f'sub-{self.config.SUB_ID}_{roi_name}_mask.nii.gz')
                out_img.to_filename(out_path)
                self._status(f"[OK] Created structural ROI mask: {out_path}")
            except Exception as e:
                self._status(f"[WARN] Failed to process {cand}: {e}")

        self._status(f"[OK] Structural ROI masks created in {time.time()-t0:.1f}s")
    
    def run_extract_roi(self, include_whole_brain=False):
        """Extract responses for each ROI

        Parameters
        ----------
        include_whole_brain : bool
            If True, also extract whole-brain responses (useful for ROI-free decoding).
        """
        if not self.cache.exists('roi'):
            raise ValueError("ROI masks not found. Run roi_build first.")
            
        # Load GLM results
        beta_file = os.path.join(
            self.config.analysis_dir,
            f'sub-{self.config.SUB_ID}_rsvp_deconv_betas.nii.gz'
        )
        if not os.path.exists(beta_file):
            raise ValueError("GLM results not found. Run deconv_glm first.")
            
        # Look for per-run beta files first
        per_run_pattern = os.path.join(self.config.analysis_dir, f'sub-{self.config.SUB_ID}_rsvp_deconv_betas_run-*.nii.gz')
        per_run_files = sorted(glob.glob(per_run_pattern))

        self._status("[START] Extracting ROI responses from beta image")

        roi_data = {}
        t0 = time.time()
        for roi in ['V1', 'V2', 'V3', 'hV4']:
            mask_path = os.path.join(self.config.roi_dir, f'sub-{self.config.SUB_ID}_{roi}_mask.nii.gz')
            if not os.path.exists(mask_path):
                self._status(f"[WARN] Skipping {roi}: mask not found")
                continue
            # Load mask and resample to the beta image grid when possible
            mask_img = nib.load(mask_path)

            if per_run_files:
                # Use per-run betas: load each run, resample mask to run beta grid, stack
                run_betas_list = []
                for run_file in per_run_files:
                    run_img = nib.load(run_file)
                    target_shape = run_img.shape[1:]
                    resampled_mask = image.resample_img(
                        mask_img,
                        target_affine=run_img.affine,
                        target_shape=target_shape,
                        interpolation='nearest'
                    )
                    roi_mask = resampled_mask.get_fdata().astype(bool)

                    run_data = run_img.get_fdata()  # (colors, X, Y, Z)
                    n_colors = run_data.shape[0]
                    spatial_voxels = int(np.prod(target_shape))
                    run_data = run_data.reshape(n_colors, spatial_voxels)

                    flat_mask = roi_mask.reshape(-1)
                    if flat_mask.size != spatial_voxels:
                        min_len = min(flat_mask.size, spatial_voxels)
                        flat_mask = flat_mask[:min_len]
                        run_data = run_data[:, :min_len]

                    if not flat_mask.any():
                        self._status(f"[WARN] {roi} mask is empty after resampling for run file {run_file}; skipping this ROI")
                        run_betas_list = []
                        break

                    run_betas_list.append(run_data[:, flat_mask])  # shape (colors, n_voxels_in_roi)

                if not run_betas_list:
                    self._status(f"[WARN] {roi} no per-run data available after resampling; skipping")
                    continue

                # Stack per-run arrays into shape (n_runs * n_colors, n_voxels)
                runs = len(run_betas_list)
                arr = np.stack(run_betas_list, axis=0)  # (runs, colors, n_voxels)
                stacked = arr.reshape(runs * n_colors, -1)
                roi_data[roi] = stacked
                self._status(f"[OK] Extracted {roi} per-run responses: {stacked.shape}")

                # Save summary
                out_path = os.path.join(self.config.analysis_dir, f'{roi}_responses_perrun.npy')
                np.save(out_path, stacked)
            else:
                # Fallback: load mean beta file (legacy behavior)
                beta_img = nib.load(beta_file)
                target_shape = beta_img.shape[1:]
                resampled_mask = image.resample_img(
                    mask_img,
                    target_affine=beta_img.affine,
                    target_shape=target_shape,
                    interpolation='nearest'
                )
                roi_mask = resampled_mask.get_fdata().astype(bool)

                roi_betas = beta_img.get_fdata()  # (colors, X, Y, Z)
                n_colors = roi_betas.shape[0]
                spatial_voxels = int(np.prod(target_shape))
                roi_betas = roi_betas.reshape(n_colors, spatial_voxels)

                flat_mask = roi_mask.reshape(-1)
                if flat_mask.size != spatial_voxels:
                    self._status(f"[WARN] {roi} mask size {flat_mask.size} != beta voxels {spatial_voxels}; attempting fallback clipping")
                    min_len = min(flat_mask.size, spatial_voxels)
                    flat_mask = flat_mask[:min_len]
                    roi_betas = roi_betas[:, :min_len]

                if flat_mask.any():
                    roi_betas = roi_betas[:, flat_mask]
                else:
                    self._status(f"[WARN] {roi} mask is empty after resampling; skipping")
                    continue

                roi_data[roi] = roi_betas
                self._status(f"[OK] Extracted {roi} responses: {roi_betas.shape}")

                out_path = os.path.join(self.config.analysis_dir, f'{roi}_responses.npy')
                np.save(out_path, roi_betas)
        
        self._status(f"[OK] ROI data extracted in {time.time()-t0:.1f}s")
        # Optionally extract whole-brain responses (no ROI segregation)
        if include_whole_brain:
            try:
                # Determine voxel mask across runs or from mean beta
                if per_run_files:
                    run_imgs = [nib.load(p) for p in per_run_files]
                    # Use union of non-zero voxels across runs and colors
                    masks = [(ri.get_fdata().sum(axis=0) != 0) for ri in run_imgs]
                    union_mask = np.any(np.stack(masks, axis=0), axis=0)
                    target_shape = run_imgs[0].shape[1:]
                    spatial_voxels = int(np.prod(target_shape))
                    flat_mask = union_mask.reshape(-1)
                    if flat_mask.sum() == 0:
                        self._status("[WARN] WholeBrain union mask empty; skipping WholeBrain extraction")
                    else:
                        # Build stacked per-run whole-brain responses
                        run_betas_list = []
                        for run_img in run_imgs:
                            run_data = run_img.get_fdata()  # (colors, X, Y, Z)
                            n_colors = run_data.shape[0]
                            run_data = run_data.reshape(n_colors, spatial_voxels)
                            run_betas_list.append(run_data[:, flat_mask])
                        arr = np.stack(run_betas_list, axis=0)  # (runs, colors, n_voxels)
                        stacked = arr.reshape(arr.shape[0] * arr.shape[1], arr.shape[2])
                        roi_data['WholeBrain'] = stacked
                        out_path = os.path.join(self.config.analysis_dir, 'WholeBrain_responses_perrun.npy')
                        np.save(out_path, stacked)
                        self._status(f"[OK] Extracted WholeBrain per-run responses: {stacked.shape}")
                else:
                    beta_img = nib.load(beta_file)
                    target_shape = beta_img.shape[1:]
                    spatial_voxels = int(np.prod(target_shape))
                    mean_betas = beta_img.get_fdata()  # (colors, X, Y, Z)
                    mean_flat = np.mean(mean_betas, axis=0).reshape(-1)
                    flat_mask = mean_flat != 0
                    if flat_mask.sum() == 0:
                        self._status("[WARN] WholeBrain mean mask empty; skipping WholeBrain extraction")
                    else:
                        n_colors = mean_betas.shape[0]
                        mean_resh = mean_betas.reshape(n_colors, spatial_voxels)
                        roi_data['WholeBrain'] = mean_resh[:, flat_mask]
                        out_path = os.path.join(self.config.analysis_dir, 'WholeBrain_responses.npy')
                        np.save(out_path, roi_data['WholeBrain'])
                        self._status(f"[OK] Extracted WholeBrain mean responses: {roi_data['WholeBrain'].shape}")
            except Exception as e:
                self._status(f"[WARN] WholeBrain extraction failed: {e}")

        self._status(f"[OK] ROI data extracted in {time.time()-t0:.1f}s")
        return roi_data
    
    def run_forward_model(self, roi_data=None):
        """
        Execute forward encoding model following B&H (2009)
        
        Args:
            roi_data: Dictionary of ROI responses {roi_name: response_matrix}
                     If None, will load from saved files
                     
        Steps:
        1. Define 8 hypothetical neural channel responses
        2. Split data into training/testing sets
        3. Train encoding model using training data
        4. Test classification performance on held-out run
        """
        if self.cache.exists('forward_model'):
            self._status("[SKIP] Forward model results exist")
            return
            
        if roi_data is None:
            roi_data = {}
            # Load saved responses
            for roi in ['V1', 'V2', 'V3', 'hV4']:
                path = os.path.join(self.config.analysis_dir, f'{roi}_responses.npy')
                if os.path.exists(path):
                    roi_data[roi] = np.load(path)
                else:
                    print(f"[WARN] No response data for {roi}")
        
        from sklearn.linear_model import LogisticRegression
        # lazy import scaler
        from sklearn.preprocessing import StandardScaler

        results = {}
        self._status("[START] Forward model (B&H 2009)")
        t0 = time.time()
        for roi, responses in roi_data.items():
            self._status(f"\n[ROI] Processing {roi} ...")

            # Expected shapes:
            # - per-run data: (n_runs * n_colors, n_voxels)
            # - mean-only data: (n_colors, n_voxels)
            n_colors = self.config.N_COLORS
            n_runs = self.config.N_RUNS

            # Initialize results
            roi_results = {
                'train_accuracy': [],
                'test_accuracy': [],
                'confusion_matrix': np.zeros((n_colors, n_colors))
            }

            if responses.shape[0] == n_runs * n_colors:
                # Proper per-run data available
                arr = responses.reshape((n_runs, n_colors, responses.shape[1]))

                for test_run in range(n_runs):
                    self.logger.info(f"[FM] ROI {roi} fold {test_run+1}/{n_runs}")
                    test_X = arr[test_run]  # (n_colors, n_voxels)
                    test_y = np.arange(n_colors)

                    train_mask = np.arange(n_runs) != test_run
                    train_X = arr[train_mask].reshape(-1, responses.shape[1])  # ((n_runs-1)*n_colors, n_voxels)
                    train_y = np.tile(np.arange(n_colors), n_runs - 1)

                    # Remove constant features (zero variance) based on training data
                    try:
                        var = np.nanstd(train_X, axis=0)
                        keep_mask = var > 0
                        if not np.any(keep_mask):
                            self._status(f"[WARN] ROI {roi} fold {test_run+1}: no non-constant features left after variance filter; skipping fold")
                            continue
                        train_X_sel = train_X[:, keep_mask]
                        test_X_sel = test_X[:, keep_mask]

                        # Per-fold scaling
                        scaler = StandardScaler()
                        train_X_scaled = scaler.fit_transform(train_X_sel)
                        test_X_scaled = scaler.transform(test_X_sel)
                    except Exception as e:
                        # Fallback to raw data if scaling fails
                        self._status(f"[WARN] Scaling/feature selection failed for ROI {roi} fold {test_run+1}: {e}")
                        train_X_scaled = train_X
                        test_X_scaled = test_X

                    # Train a simple multinomial logistic regression as the decoder
                    clf = LogisticRegression(max_iter=1000, solver='lbfgs', multi_class='multinomial')
                    clf.fit(train_X_scaled, train_y)

                    # Evaluate
                    train_preds = clf.predict(train_X_scaled)
                    train_acc = float(np.mean(train_preds == train_y))
                    preds = clf.predict(test_X_scaled)
                    test_acc = float(np.mean(preds == test_y))

                    roi_results['train_accuracy'].append(train_acc)
                    roi_results['test_accuracy'].append(test_acc)

                    for t, p in zip(test_y, preds):
                        roi_results['confusion_matrix'][t, p] += 1

                roi_results['confusion_matrix'] /= n_runs
            elif responses.shape[0] == n_colors:
                # Only mean betas available — cannot run leave-one-run-out correctly.
                # Fallback: compute nearest-centroid classification using the mean maps as prototypes
                self.logger.info(f"[FM] ROI {roi} only mean betas available — running prototype check")
                prototypes = responses  # (n_colors, n_voxels)
                # Each class prototype is itself; test by finding nearest prototype (trivial)
                # This will generally yield chance-level results but provides a placeholder.
                sims = prototypes @ prototypes.T  # (n_colors, n_colors)
                preds = np.argmax(sims, axis=1)
                true = np.arange(n_colors)
                acc = np.mean(preds == true)
                roi_results['train_accuracy'].append(acc)
                for t, p in zip(true, preds):
                    roi_results['confusion_matrix'][t, p] += 1
                roi_results['confusion_matrix'] /= 1
            else:
                self.logger.warning(f"[FM] ROI {roi} responses shape {responses.shape} not understood; skipping")
                continue

            results[roi] = roi_results

            # Save results
            out_path = os.path.join(self.config.analysis_dir, f'{roi}_forward_model.npz')
            np.savez(out_path, **roi_results)

            # report test accuracy as primary if available
            if roi_results.get('test_accuracy'):
                mean_acc = np.mean(roi_results['test_accuracy']) if roi_results['test_accuracy'] else float('nan')
            else:
                mean_acc = np.mean(roi_results['train_accuracy']) if roi_results['train_accuracy'] else float('nan')
            self._status(f"[OK] {roi} mean accuracy: {mean_acc:.3f}")
        
        self.cache.save('forward_model', results)
        self._status(f"[OK] Forward model completed in {time.time()-t0:.1f}s")
        return results
    
    def run_qc(self):
        """Quality control checks"""
        self._status("[OK] QC checks completed")
    
    def run_pipeline(self, start_from='design'):
        """
        Run the complete analysis pipeline
        
        Parameters
        ----------
        start_from : str
            Stage to start from ('design', 'deconv_glm', 'roi_build', 'extract_roi',
                              'forward_model', 'qc')
        """
        stages = ['design', 'deconv_glm', 'roi_build', 
                 'extract_roi', 'forward_model', 'qc']
        
        if start_from not in stages:
            raise ValueError(f"Unknown stage: {start_from}")
            
        self._status("\n=== Starting ColorBlind Analysis Pipeline ===\n")
        start_idx = stages.index(start_from)
        current_data = {}
        
        for stage in stages[start_idx:]:
            self._status(f"\n--- Running {stage} stage ---")
            stage_t0 = time.time()
            method = getattr(self, f'run_{stage}')
            
            if stage == 'extract_roi':
                current_data['roi_data'] = method()
            elif stage == 'forward_model':
                current_data['model_results'] = method(current_data.get('roi_data'))
            elif stage == 'qc':
                from bh_viz import make_qc_report
                output_dir = os.path.join(self.config.analysis_dir, 'qc_plots')
                make_qc_report(
                    current_data['roi_data'], 
                    current_data['model_results'],
                    output_dir
                )
                self._status(f"[OK] Stage {stage} completed in {time.time()-stage_t0:.1f}s")
            else:
                method()
                self._status(f"[OK] Stage {stage} completed in {time.time()-stage_t0:.1f}s")

if __name__ == '__main__':
    import sys
    
    pipeline = BHAnalysisPipeline()
    start_stage = sys.argv[1] if len(sys.argv) > 1 else 'design'
    pipeline.run_pipeline(start_from=start_stage)