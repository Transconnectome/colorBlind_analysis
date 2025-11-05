#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
config.py
---------
B&H (2009) 분석 파이프라인을 위한 전역 설정
"""

import os
import glob
from pathlib import Path

class Config:
    # 프로젝트 기본 경로
    PROJECT_DIR = os.path.abspath(os.path.dirname(__file__))
    DERIVATIVES_DIR = os.path.join(PROJECT_DIR, 'derivatives')
    
    # 피험자 정보
    SUB_ID = '01'
    
    # fMRI 파라미터
    TR = 1.5  # TR (초)
    N_RUNS = 6  # 총 run 수
    VOLS_TO_DROP = 4  # 시작 시 제거할 볼륨 수
    N_COLORS = 8  # 자극 색상 수
    
    # ROI 설정
    ROI_Z_THRESH = 3.1
    MIN_CLUSTER_SIZE = 50
    
    # 파생 경로들
    @property
    def output_dir(self):
        return os.path.join(self.PROJECT_DIR, f'output/pilot/sub-{self.SUB_ID}')
    
    @property
    def fmriprep_dir(self):
        return os.path.join(self.output_dir, 'func')
    
    @property
    def analysis_dir(self):
        return os.path.join(self.DERIVATIVES_DIR, f'sub-{self.SUB_ID}')
    
    @property
    def roi_dir(self):
        return os.path.join(self.analysis_dir, 'roi')
    
    # 파일 경로 생성 메소드
    def get_func_img_path(self, run):
        return os.path.join(
            self.fmriprep_dir,
            f'sub-{self.SUB_ID}_task-rsvp_run-{run}_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz'
        )
    
    def get_event_file_path(self, run):
        return os.path.join(
            self.PROJECT_DIR,
            f'pilot/sub-{self.SUB_ID}/func/sub-{self.SUB_ID}_task-rsvp_run-{run}_events.tsv'
        )
    
    def get_confound_file_path(self, run):
        return os.path.join(
            self.fmriprep_dir,
            f'sub-{self.SUB_ID}_task-rsvp_run-{run}_desc-confounds_timeseries.tsv'
        )
    
    # 캐시 확인 메소드
    def check_derivatives_exist(self):
        """디자인 매트릭스 파일들이 존재하는지 확인"""
        pattern = os.path.join(self.DERIVATIVES_DIR, f'sub-{self.SUB_ID}', 
                             f'*task-rsvp_run-*_space-*_design_ready_HRF-*.csv')
        return len(glob.glob(pattern)) > 0

# 전역 설정 인스턴스
cfg = Config()