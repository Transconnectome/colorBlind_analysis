#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cache.py
--------
분석 파이프라인의 중간 결과물 캐싱 시스템
"""

import os
import glob
from pathlib import Path

class Cache:
    def __init__(self, config):
        self.config = config
        
    def exists(self, stage, run=None):
        """
        특정 분석 단계의 결과물이 존재하는지 확인
        
        Parameters
        ----------
        stage : str
            검사할 단계 ('design', 'fir_glm', 'roi', 'forward_model')
        run : int, optional
            특정 run 번호 (해당되는 경우)
            
        Returns
        -------
        bool
            결과물 존재 여부
        """
        check_methods = {
            'design': self._check_design_files,
            'deconv_glm': self._check_glm_files,
            'roi': self._check_roi_files,
            'forward_model': self._check_forward_model
        }
        
        if stage not in check_methods:
            raise ValueError(f"Unknown stage: {stage}")
            
        return check_methods[stage](run)
    
    def _check_design_files(self, run=None):
        """디자인 매트릭스 파일 존재 확인"""
        if run:
            pattern = os.path.join(
                self.config.DERIVATIVES_DIR,
                f'sub-{self.config.SUB_ID}',
                f'*task-rsvp_run-{run}_space-*_design_ready_HRF-*.csv'
            )
        else:
            pattern = os.path.join(
                self.config.DERIVATIVES_DIR,
                f'sub-{self.config.SUB_ID}',
                f'*task-rsvp_run-*_space-*_design_ready_HRF-*.csv'
            )
        return len(glob.glob(pattern)) > 0
    
    def _check_glm_files(self, run=None):
        """GLM 결과 파일 존재 확인"""
        pattern = os.path.join(
            self.config.analysis_dir,
            f'sub-{self.config.SUB_ID}_rsvp_deconv_betas.nii.gz'
        )
        return os.path.exists(pattern)
    
    def _check_roi_files(self, _=None):
        """ROI 마스크 파일 존재 확인"""
        roi_files = [f'sub-{self.config.SUB_ID}_{roi}_mask.nii.gz' 
                    for roi in ['V1', 'V2', 'V3', 'hV4']]
        return all(
            os.path.exists(os.path.join(self.config.roi_dir, f))
            for f in roi_files
        )
    
    def _check_forward_model(self, _=None):
        """순방향 모델 결과 존재 확인"""
        pattern = os.path.join(
            self.config.analysis_dir,
            'forward_model_results.npz'
        )
        return os.path.exists(pattern)

    def save(self, key, obj):
        """간단한 캐시 저장: 객체를 pickle로 저장합니다.

        Parameters
        ----------
        key : str
            저장 키(예: 'forward_model')
        obj : any
            직렬화 가능한 파이썬 객체
        """
        import pickle
        out_path = os.path.join(self.config.analysis_dir, f'{key}_cache.pkl')
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, 'wb') as f:
            pickle.dump(obj, f)

    def load(self, key):
        """캐시 로드: 존재하면 pickle로부터 객체를 복원합니다. 없으면 None 반환."""
        import pickle
        path = os.path.join(self.config.analysis_dir, f'{key}_cache.pkl')
        if not os.path.exists(path):
            return None
        with open(path, 'rb') as f:
            return pickle.load(f)