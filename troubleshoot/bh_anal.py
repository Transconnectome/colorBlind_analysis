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
import argparse
import numpy as np
import pandas as pd
import nibabel as nib
import matplotlib.pyplot as plt

from nilearn import image
from nilearn.glm.first_level import FirstLevelModel, make_first_level_design_matrix
from nilearn.maskers import NiftiMasker
from sklearn.decomposition import PCA
from scipy.stats import binomtest
from utils.cache import Cache
from roi_build import build_wang_rois, build_structural_rois
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
        ### TODO: HRF 추정 결과 및 기존 FIR과 비교 
        # 자극 색상 무시하고 전체 평균 응답으로 HIRF 추정
        hirf_len = int(12 / self.config.TR)  # 12초 길이의 HIRF
        hirfs = []

        # determine spatial shape from first functional image
        ### 왜 첫 번째 이미지의 3번까지 쉐이프인가? -> Time 축 제외
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

        # 모든 run의 평균 HIRF 계산 : 각 voxel에 대한 평균 HIRF
        mean_hirf = np.mean(np.array(hirfs), axis=0)  # (hirf_len, voxels)
        # canonical HIRF: average across voxels -> 1D vector of length hirf_len
        try:
            canonical_hirf = np.mean(mean_hirf, axis=1)
        except Exception:
            canonical_hirf = mean_hirf[:, 0] if mean_hirf.ndim >= 2 else mean_hirf

        # HIRF 비교 플롯 함수
        per_run_curves = []
        for hirf in hirfs:
            try:
                per_run_curves.append(np.mean(hirf, axis=1))
            except Exception:
                continue
        if per_run_curves:
            self._plot_hirf_comparison(canonical_hirf, per_run_curves, hirf_len)
        
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
            
            ### STUDY: 중복 코드 확인
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
        ## STUDY: ROI 마스크 생성 완전히 마무리하기
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

        print(roi_masks.keys(), "loaded.")
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


    @staticmethod
    def _channel_basis(num_channels=6, num_hues=360):
        hs = np.deg2rad(np.arange(num_hues))
        centers = np.deg2rad(np.linspace(0, 360, num_channels, endpoint=False))
        channels = []
        for c in centers:
            t = np.cos(hs - c)
            t = np.clip(t, 0, None)
            channels.append(t ** 2)
        return np.array(channels)

    def _label_indices_to_deg(self, idx_array):
        step = 360.0 / self.config.N_COLORS
        return (idx_array.astype(float) * step) % 360.0

    @staticmethod
    def _circular_diff_deg(a, b):
        d = np.abs(a - b) % 360.0
        return np.minimum(d, 360.0 - d)

    def _forward_model_fit_predict(self, train_B, train_labels, test_B, hue_table, lam=1e-2):
        train_labels = np.asarray(train_labels, dtype=int)
        step = int(round(360.0 / self.config.N_COLORS))
        train_hue_idx = np.mod(train_labels * step, 360)

        C1 = hue_table[:, train_hue_idx]
        B1 = train_B.T
        k = C1.shape[0]

        W = (B1 @ C1.T) @ np.linalg.pinv(C1 @ C1.T + lam * np.eye(k))

        B2 = test_B.T
        C_hat = np.linalg.pinv(W.T @ W + lam * np.eye(k)) @ (W.T @ B2)

        C_hat_norm = C_hat / (np.linalg.norm(C_hat, axis=0, keepdims=True) + 1e-8)
        hue_norm = hue_table / (np.linalg.norm(hue_table, axis=0, keepdims=True) + 1e-8)
        sims = C_hat_norm.T @ hue_norm
        hues_pred = sims.argmax(axis=1)
        return hues_pred.astype(float)
    
    def _plot_hirf_comparison(self, canonical_hirf, per_run_curves, hirf_len):
        """Save comparison plot between estimated HIRF and FIR impulse."""
        try:
            time_axis = np.arange(hirf_len) * self.config.TR
            plt.figure(figsize=(6, 4))
            for idx, curve in enumerate(per_run_curves):
                plt.plot(time_axis, curve, color='gray', alpha=0.3,
                         label='Per-run mean' if idx == 0 else None)
            plt.plot(time_axis, canonical_hirf, color='tab:red', linewidth=2,
                     label='Voxel-avg HIRF')
            fir_unit = np.zeros(hirf_len)
            fir_unit[0] = 1.0
            plt.plot(time_axis, fir_unit, color='tab:blue', linestyle='--',
                     label='FIR unit impulse')
            plt.xlabel('Time (s)')
            plt.ylabel('Response (a.u.)')
            plt.title('Estimated HIRF vs FIR Reference')
            plt.legend(loc='best', fontsize=8)
            plt.tight_layout()
            out_path = os.path.join(
                self.config.analysis_dir,
                f"sub-{self.config.SUB_ID}_hirf_vs_fir.png"
            )
            plt.savefig(out_path, dpi=150)
            plt.close()
            self._status(f"[OK] Saved HIRF comparison plot: {out_path}")
        except Exception as exc:
            plt.close()
            self._status(f"[WARN] Failed to plot HIRF comparison: {exc}")

    @staticmethod
    def _diag_linear_predict(train_X, train_y, test_X):
        classes = np.unique(train_y)
        means = np.stack([train_X[train_y == c].mean(axis=0) for c in classes])
        vars_ = np.stack([train_X[train_y == c].var(axis=0) + 1e-8 for c in classes])
        ll = []
        for k in range(len(classes)):
            ll_k = -0.5 * (np.log(2 * np.pi * vars_[k]).sum() + ((test_X - means[k]) ** 2 / vars_[k]).sum(axis=1))
            ll.append(ll_k)
        ll = np.stack(ll, axis=1)
        preds = classes[ll.argmax(axis=1)]
        return preds


    def run_roi_build(self):
        """ROI 마스크 생성 단계 (외부 모듈 호출)"""
        pattern = os.path.join(self.config.roi_dir, f'sub-{self.config.SUB_ID}_*_mask.nii.gz')
        existing = glob.glob(pattern)
        required = {f'sub-{self.config.SUB_ID}_{roi}_mask.nii.gz' for roi in ['V1', 'V2', 'V3', 'hV4']}
        required.add(f'sub-{self.config.SUB_ID}_BrainMask_mask.nii.gz')

        existing_names = {os.path.basename(p) for p in existing}
        have_required = required.issubset(existing_names)

        if have_required and existing:
            self._status(f'[SKIP] ROI masks exist ({len(existing)})')
            return

        build_wang_rois(self.config, status=self._status, skip_existing=have_required)

    def run_roi_build_structural(self):
        """Build structural ROI masks using external helper."""
        created = build_structural_rois(self.config, status=self._status, skip_existing=True)
        if not created:
            self._status('[INFO] Structural ROI build skipped or already satisfied')


    def run_extract_roi(self, include_whole_brain=False):
        """Extract responses for each ROI

        Parameters
        ----------
        include_whole_brain : bool
            If True, also extract whole-brain responses (useful for ROI-free decoding).
        """
        pattern = os.path.join(self.config.roi_dir, f'sub-{self.config.SUB_ID}_*_mask.nii.gz')
        roi_masks = glob.glob(pattern)
        if not roi_masks:
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
        base_rois = ['V1', 'V2', 'V3', 'hV4']
        brain_mask_roi = 'BrainMask'
        brain_mask_path = os.path.join(
            self.config.roi_dir,
            f'sub-{self.config.SUB_ID}_{brain_mask_roi}_mask.nii.gz'
        )
        if os.path.exists(brain_mask_path):
            base_rois.append(brain_mask_roi)

        for roi in base_rois:
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
    
    def run_classification(self, roi_data=None, roi_list=None):
        """Diag-linear LOAO classification for selected ROIs."""
        start_t = time.time()
        if roi_data is None:
            roi_data = {}
            for roi in ['V1', 'V2', 'V3', 'hV4', 'BrainMask']:
                perrun_path = os.path.join(self.config.analysis_dir, f'{roi}_responses_perrun.npy')
                if os.path.exists(perrun_path):
                    roi_data[roi] = np.load(perrun_path)
                else:
                    mean_path = os.path.join(self.config.analysis_dir, f'{roi}_responses.npy')
                    if os.path.exists(mean_path):
                        roi_data[roi] = np.load(mean_path)

        if not roi_data:
            raise ValueError("No ROI response data available for classification.")

        available_rois = sorted(roi_data.keys())
        if roi_list:
            roi_targets = [roi for roi in roi_list if roi in roi_data]
            missing = [roi for roi in roi_list if roi not in roi_data]
            for miss in missing:
                self._status(f"[WARN] Requested ROI {miss} not available; skipping classification")
            if not roi_targets:
                raise ValueError("None of the requested ROIs have response data for classification.")
        else:
            roi_targets = available_rois

        results = {}
        n_colors = self.config.N_COLORS

        for roi in roi_targets:
            responses = roi_data[roi]
            total_samples, n_vox = responses.shape
            if total_samples % n_colors != 0:
                self._status(f"[WARN] ROI {roi} samples not divisible by {n_colors}; skipping classification")
                continue

            n_runs = total_samples // n_colors
            if n_runs < 2:
                self._status(f"[WARN] ROI {roi} classification skipped (n_runs={n_runs})")
                continue

            arr = responses.reshape(n_runs, n_colors, n_vox)
            run_acc = []
            confusion = np.zeros((n_colors, n_colors), dtype=int)
            preds_runs = []
            labels_runs = []

            for test_run in range(n_runs):
                test_X = arr[test_run]
                test_y = np.arange(n_colors)
                train_mask = np.ones(n_runs, dtype=bool)
                train_mask[test_run] = False
                train_X = arr[train_mask].reshape(-1, n_vox)
                train_y = np.tile(np.arange(n_colors), train_mask.sum())
                y_pred = self._diag_linear_predict(train_X, train_y, test_X)
                preds_runs.append(y_pred)
                labels_runs.append(test_y)
                acc = float(np.mean(y_pred == test_y))
                run_acc.append(acc)
                for t, p in zip(test_y, y_pred):
                    confusion[t, p] += 1
                self._status(f"[Classify][{roi}] run {test_run+1}/{n_runs}: acc={acc:.3f}")

            counts = confusion.sum(axis=1)
            with np.errstate(divide='ignore', invalid='ignore'):
                per_color_acc = np.where(counts > 0, confusion.diagonal() / counts, np.nan)
            mean_acc = float(np.mean(run_acc)) if run_acc else float('nan')

            valid_idx = np.where(~np.isnan(per_color_acc))[0]
            if valid_idx.size > 0:
                best_idx = valid_idx[int(np.nanargmax(per_color_acc[valid_idx]))]
                worst_idx = valid_idx[int(np.nanargmin(per_color_acc[valid_idx]))]
                self._status(
                    f"[Classify][{roi}] mean acc={mean_acc:.3f}, best=color_{best_idx+1} ({per_color_acc[best_idx]:.3f}), "
                    f"worst=color_{worst_idx+1} ({per_color_acc[worst_idx]:.3f})"
                )
            else:
                self._status(f"[Classify][{roi}] mean acc={mean_acc:.3f}")

            preds_array = np.vstack(preds_runs)
            labels_array = np.vstack(labels_runs)
            class_out = os.path.join(self.config.analysis_dir, f"{roi}_diag_classification.npz")
            np.savez(class_out,
                     run_accuracy=np.array(run_acc),
                     mean_accuracy=mean_acc,
                     confusion=confusion,
                     per_color_accuracy=per_color_acc,
                     predictions=preds_array,
                     labels=labels_array)

            results[roi] = {
                'run_accuracy': run_acc,
                'mean_accuracy': mean_acc,
                'confusion': confusion.tolist(),
                'per_color_accuracy': per_color_acc.tolist(),
                'predictions': preds_array.tolist(),
                'labels': labels_array.tolist(),
            }

            txt_out = os.path.join(self.config.analysis_dir, f"{roi}_diag_classification.txt")
            with open(txt_out, 'w', encoding='utf-8') as f:
                f.write(f"ROI: {roi}\n")
                f.write(f"Mean accuracy: {mean_acc:.4f}\n")
                f.write("Run accuracies:\n")
                for idx, acc in enumerate(run_acc, 1):
                    f.write(f"  Run {idx}: {acc:.4f}\n")
                f.write("Per-color accuracy:\n")
                for idx, acc in enumerate(per_color_acc, 1):
                    if np.isnan(acc):
                        acc_str = "nan"
                    else:
                        acc_str = f"{float(acc):.4f}"
                    f.write(f"  Color {idx}: {acc_str}\n")
                f.write("Confusion matrix:\n")
                for row in confusion:
                    row_str = " ".join(f"{int(x):3d}" for x in row)
                    f.write(f"  {row_str}\n")
                f.write("\n")

        self.cache.save('classification', results)
        self._status(f"[OK] Classification completed in {time.time()-start_t:.1f}s")
        return results

    def run_forward_model(self, roi_data=None, roi_list=None, lam=1e-2, tol_deg=22.5, num_channels=6, classification_results=None):
        """Forward encoding reconstruction following B&H (2009)."""
        start_t = time.time()
        if roi_data is None:
            roi_data = {}
            for roi in ['V1', 'V2', 'V3', 'hV4']:
                perrun_path = os.path.join(self.config.analysis_dir, f'{roi}_responses_perrun.npy')
                if os.path.exists(perrun_path):
                    roi_data[roi] = np.load(perrun_path)
                    continue
                mean_path = os.path.join(self.config.analysis_dir, f'{roi}_responses.npy')
                if os.path.exists(mean_path):
                    roi_data[roi] = np.load(mean_path)
                else:
                    self._status(f"[WARN] No response data for {roi}")

        if not roi_data:
            raise ValueError("No ROI response data available for forward model.")

        available_rois = sorted(roi_data.keys())
        if roi_list:
            roi_targets = [roi for roi in roi_list if roi in roi_data]
            missing = [roi for roi in roi_list if roi not in roi_data]
            for miss in missing:
                self._status(f"[WARN] Requested ROI {miss} not available; skipping forward model")
            if not roi_targets:
                raise ValueError("None of the requested ROIs have response data for forward model.")
        else:
            roi_targets = available_rois

        if classification_results is None:
            classification_results = {}
            for roi in roi_targets:
                class_path = os.path.join(self.config.analysis_dir, f"{roi}_diag_classification.npz")
                if os.path.exists(class_path):
                    data = np.load(class_path, allow_pickle=True)
                    classification_results[roi] = {
                        'run_accuracy': data['run_accuracy'].tolist(),
                        'mean_accuracy': float(data['mean_accuracy']),
                        'confusion': data['confusion'].tolist(),
                        'per_color_accuracy': data['per_color_accuracy'].tolist(),
                        'predictions': data['predictions'].tolist(),
                        'labels': data['labels'].tolist(),
                    }

        hue_table = self._channel_basis(num_channels=num_channels, num_hues=360)
        results = {}

        for roi in roi_targets:
            responses = roi_data[roi]
            total_samples, n_vox = responses.shape
            n_colors = self.config.N_COLORS
            if total_samples % n_colors != 0:
                self._status(f"[WARN] ROI {roi} samples not divisible by {n_colors}; skipping forward model")
                continue

            n_runs = total_samples // n_colors
            if n_runs < 2:
                self._status(f"[WARN] ROI {roi} requires at least 2 runs for LOAO; skipping forward model")
                continue

            arr = responses.reshape(n_runs, n_colors, n_vox)

            run_hits = []
            run_mae = []
            pred_records = []
            true_records = []

            self._status(f"[START] Forward reconstruction ROI={roi} (runs={n_runs}, voxels={n_vox})")
            for test_run in range(n_runs):
                test_B = arr[test_run]
                train_mask = np.ones(n_runs, dtype=bool)
                train_mask[test_run] = False
                train_B = arr[train_mask].reshape(-1, n_vox)
                y_train = np.tile(np.arange(n_colors), train_mask.sum())
                y_test = np.arange(n_colors)

                preds_idx = self._forward_model_fit_predict(train_B, y_train, test_B, hue_table, lam=lam)
                true_deg = self._label_indices_to_deg(y_test)
                diff = self._circular_diff_deg(preds_idx, true_deg)
                hit = float((diff <= tol_deg).mean())
                mae = float(diff.mean())

                run_hits.append(hit)
                run_mae.append(mae)
                pred_records.append(preds_idx)
                true_records.append(true_deg)
                self._status(f"[Forward][{roi}] run {test_run+1}/{n_runs}: hit={hit:.3f}, mae={mae:.2f}°")

            if not run_hits:
                continue

            pred_stack = np.vstack(pred_records)
            true_stack = np.vstack(true_records)

            roi_result = {
                'hit_rate_mean': float(np.mean(run_hits)),
                'mae_deg_mean': float(np.mean(run_mae)),
                'run_hits': run_hits,
                'run_mae': run_mae,
                'pred_deg': pred_stack.tolist(),
                'true_deg': true_stack.tolist(),
                'tolerance_deg': tol_deg,
                'lambda': lam,
                'num_channels': num_channels,
            }

            out_path = os.path.join(self.config.analysis_dir, f'{roi}_forward_recon.npz')
            np.savez(out_path,
                     pred_deg=pred_stack,
                     true_deg=true_stack,
                     run_hits=np.array(run_hits),
                     run_mae=np.array(run_mae),
                     hit_rate_mean=roi_result['hit_rate_mean'],
                     mae_deg_mean=roi_result['mae_deg_mean'],
                     tolerance_deg=tol_deg,
                     lam=lam,
                     num_channels=num_channels)

            self._status(f"[OK] ROI {roi} mean hit={roi_result['hit_rate_mean']:.3f}, mean mae={roi_result['mae_deg_mean']:.2f}°")
            entry = {
                'reconstruction': roi_result
            }
            if roi in classification_results:
                entry['classification'] = classification_results[roi]
            results[roi] = entry

            txt_out = os.path.join(self.config.analysis_dir, f"{roi}_forward_model.txt")
            with open(txt_out, 'w', encoding='utf-8') as f:
                f.write(f"ROI: {roi}\n")
                f.write(f"Mean hit rate: {roi_result['hit_rate_mean']:.4f}\n")
                f.write(f"Mean MAE (deg): {roi_result['mae_deg_mean']:.4f}\n")
                f.write(f"Tolerance (deg): {roi_result['tolerance_deg']}\n")
                f.write(f"Lambda: {roi_result['lambda']:.4g}\n")
                f.write("Run hit rates:\n")
                for idx, hit in enumerate(run_hits, 1):
                    f.write(f"  Run {idx}: {hit:.4f}\n")
                f.write("Run MAE (deg):\n")
                for idx, mae_val in enumerate(run_mae, 1):
                    f.write(f"  Run {idx}: {mae_val:.4f}\n")
                f.write("\n")

        self.cache.save('forward_model', results)
        self._status(f"[OK] Forward reconstruction completed in {time.time()-start_t:.1f}s")
        return results

    def run_qc(self):
        """Quality control checks"""
        self._status("[OK] QC checks completed")
    
    def run_pipeline(self, start_from='design', roi_list=None):
        """
        Run the complete analysis pipeline
        
        Parameters
        ----------
        start_from : str
            Stage to start from ('design', 'deconv_glm', 'roi_build', 'extract_roi',
                              'classification', 'forward_model', 'qc')
        """
        stages = ['design', 'deconv_glm', 'roi_build', 
                 'extract_roi', 'classification', 'forward_model', 'qc']
        
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
            elif stage == 'classification':
                current_data['class_results'] = method(current_data.get('roi_data'), roi_list=roi_list)
            elif stage == 'forward_model':
                current_data['model_results'] = method(
                    current_data.get('roi_data'),
                    roi_list=roi_list,
                    classification_results=current_data.get('class_results')
                )
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
    parser = argparse.ArgumentParser(description="ColorBlind analysis pipeline")
    parser.add_argument('stage', nargs='?', default='design',
                        help="Stage to start from (design, deconv_glm, roi_build, extract_roi, classification, forward_model, qc)")
    parser.add_argument('--roi', dest='rois', action='append',
                        help="Specify ROI name (can be used multiple times). Applies to forward_model stage.")

    args = parser.parse_args()

    pipeline = BHAnalysisPipeline()
    pipeline.run_pipeline(start_from=args.stage, roi_list=args.rois)
