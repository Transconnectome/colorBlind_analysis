# ===================== Experiment infos =====================
global SamplePeriod

# 시작 시간
global DataSamplingOnTime, DataSamplingOnDatetime
DataSamplingOnTime=list()
DataSamplingOnDateTime=list()

# 종료 시간
global DataSamplingOffTime, DataSamplingOffDatetime
DataSamplingOffTime=list()
DataSamplingOffDateTime=list()

global hexSamplePeriod

# ===================== dataset infos (Not used) =====================
COLUMNS_DATA = [
    'subject', 'group', 'sess','block', 'trial',
    'choice', 'choice_answer', 'choice_result',
    'card1', 'card2', 'check', 'check_answer',
    'check_result', 'reward', 'time_scan',
    'time_fix1', 'time_choice',
    'rt_choice', 'time_fix2', 'time_first_card',
    'time_second_card', 'time_check', 'rt_check',
    'time_feedback', 'time_done',
    # 'airflow', 'vaping_start_time', 'vaping_end_time',
    'timestamp_scan']

# ===================== Settings =====================
FPS = 60 #Frames per second  It is the screen refresh rate  CHECK that it matches the FPS of monitor on which the experiment runs (Can be found in display settings)
ScreenResolutionWidth = 1920 #1280#1920 #in pixels  CHECK that it is inline with screen resolution of monitor on which the experiment runs  (Can be found in display settings)
ScreenResolutionLength = 1150 #720#1080 #in pixels  CHECK that it is inline with screen resolution of monitor on which the experiment runs  (Can be found in display settings)
#1920 by 1200 is resolution of the monitor shown to subjects.

# 시작 정보 입력, 종료 키 (참여자가 누르는 거)
ScannerSignal = 'quoteleft'#u'\x60'#["`"]
#ScannerSignal = ['s']
QuitKey = 'z'

# 기타 장비 안 쓸 거 같지만 혹시 몰라서
tgap1 = 0.01; #0.01 seconds or 10 millisecs. spp(tgap1) is used between writing to and reading from serial port. Gap of 10 ms works for writing on EEPROM but greater gap is required for operating digital port that is for say 'T' commands.
tgap2 = 0.1; #0.1 seconds or 100 millisecs. Used between writing to and reading from serial port.

# ========================== Packages ==========================
import random
import string
import json
from collections import OrderedDict
from pathlib import Path
import pandas as pd
import numpy as np, pathlib, random, time, warnings
from psychopy import visual, core, event, gui, data, monitors
import math
import logging
import os
import datetime
import random 
import yaml
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

# ========================== fMRI 관련 ==========================
from psychopy.hardware import keyboard
from psychopy import clock
from psychopy.tools.filetools import fromFile, toFile

# ========================== 경로 관련 ==========================

# 경로 관련
PATH_ROOT = Path(__file__).absolute().parent
PATH_SCHEDULE = PATH_ROOT / 'schedules'
PATH_IMAGE_DIR = PATH_ROOT / 'pictures'
# PATH_DATA_DIR = PATH_ROOT / 'data'

# ========================== 실험 설정 ==========================
# ========================== 실험 설정 (수정) ==========================
# CIE L*a*b* 색 공간에서 8가지 등간격 색상과 중립 회색을 정의합니다.
# L* (밝기, 0-100), a* (녹색-적색), b* (청색-황색)
COLOR_LAB = {
    'color_1': [75, -40.0, 0.0],       # 0도: Red
    'color_2': [75, -28.28, -28.28],     # 45도: Orange (a=b)
    'color_3': [75, 0.0, -40.0],        # 90도: Yellow
    'color_4': [75, 28.28, -28.28],  # 135도: Greenish
    'color_5': [75, 40.0, 0.0],         # 180도: Cyan
    'color_6': [75, 28.28, 28.28],     # 225도: Blue
    'color_7': [75, 0.0, 40.0],       # 270도: Violet (청색)
    'color_8': [75, -28.28, 28.28],   # 315도: Pinkish (Magenta)
    'blank': [75, 0.0, 0.0]           # L*=75, a*=0, b*=0 : Neutral Gray
}
# 기존 COLOR_RGB는 삭제하거나 주석 처리하고, COLOR_LAB을 사용합니다.

# RGB -> CIELab Translation code. Add if needed (주석 제거)
def lab2rgb(L,a,b,clip=True):
    L,a,b = float(L),float(a),float(b)
    y=(L+16)/116; x=a/500+y; z=y-b/200
    xyz=np.array([x,y,z]); xyz=np.where(xyz>.206893, xyz**3,(xyz-16/116)/7.787)
    xyz*=[.95047,1.,1.08883]
    rgb=np.dot([[ 3.2406,-1.5372,-.4986],[-.9689,1.8758,.0415],[.0557,-.2040,1.0570]],xyz)
    rgb=np.where(rgb<=.0031308,12.92*rgb,1.055*rgb**(1/2.4)-.055)
    
    # ----------------------------------------------------
    # PsychoPy에서 사용하는 [-1.0, 1.0] 범위로 RGB 값을 변환하는 단계 추가
    if clip: 
        rgb = np.clip(rgb, 0, 1) # 먼저 0~1 범위로 클램프
        
    # [0.0, 1.0] -> [-1.0, 1.0] 변환: (x * 2) - 1
    # PsychoPy의 'rgb' colorspace는 -1.0(min) ~ 1.0(max)을 사용합니다.
    rgb_psychopy = (rgb * 2) - 1
    # ----------------------------------------------------
    
    # return rgb.tolist() # 기존 코드 대신 수정된 값 반환
    return rgb_psychopy.tolist()

# COLOR_LAB을 기반으로 PsychoPy용 COLOR_RGB 딕셔너리를 새로 생성
COLOR_RGB = {}
for key, lab_vals in COLOR_LAB.items():
    L, a, b = lab_vals
    COLOR_RGB[key] = lab2rgb(L, a, b)

TRIAL_DURATION = 1.5
RSVP_INTERVAL = 0.4
RSVP_WAIT = 0.35

TTL_KEY, SPACE_KEY, ESC_KEY = '5', 'space', 'escape'
MODES = ['scanner', 'laptop']
WIN_SIZE = (1024, 768)
FULL_LAPTOP, FULL_SCANNER = False, True
MON_NAME = 'MRIProjector'

GRAT_DIAM_DEG, GRAT_DIAM_PX = 10, 500
SPAT_FREQ  = 5      # radial cycles
DRIFT_CPS  = .30    # cycles / sec
STIM_DUR   = 0.8
ISI_LIST   = [3.0, 4.5, 6.0]
REP_PER_COL, N_BLANK = 8, 8

# ========================== Drawer 클래스 ==========================
class ColorDetectDrawer:
    def __init__(self,
                 win: visual.Window,
                 size: float,
                 fixation_size: float = 3,
                 wait_height: float = 3,
                 text_height: float = 3,
                 wrap_width: float = 30
                 ):
        self.win = win
        self.size = size

        self.fixation_size = fixation_size * size
        self.wait_height = wait_height * size
        self.rsvp_text = visual.TextStim(win, text='', 
                                         height=2.4 if win.units == 'deg' else 52,
                                         pos=(0,0 if win.units=='deg' else -40),
                                         alignText='center',
                                         anchorHoriz='center',
                                         anchorVert='center'
                                         )

        self.text_height = text_height * size
        self.wrap_width = wrap_width * size
        self.data = pd.DataFrame(None, columns=COLUMNS_DATA)        

        fn_inst = PATH_ROOT / 'instructions.yaml'
        with open(fn_inst, 'r', encoding='utf-8') as f:
            self.instructions = yaml.load(f, Loader=Loader)

        # 원 그리고 재사용
        self.draw_circle()
        
    def draw_circle(self):
        # 원 만들기
        size = GRAT_DIAM_PX if self.win.units == 'pix' else GRAT_DIAM_DEG
        try:
            self.stim = visual.RadialStim(
                win=self.win, tex='sin', mask='circle',
                size= size, units= self.win.units,
                radialCycles=SPAT_FREQ,       # 동심원
                angularCycles=0,
                radialPhase=0.0,
                visibleWedge=(0, 360),
                texRes=512,
                interpolate=True, color=[0, 0, 0], colorSpace='rgb',
                contrast = 1.0
            )
            stim_type = 'radial'
        except TypeError:
            warnings.warn('RadialStim 실패 → GratingStim 대체',RuntimeWarning)
            self.stim = visual.GratingStim(
                win=self.win, tex='sin', mask='circle',
                size=size, units= self.win.units,
                sf=(0,SPAT_FREQ),       # 동심원
                angularCycles=0,
                radialPhase=0.0,
                visibleWedge=(0, 360),
                texRes=512,
                interpolate=True, color=[0, 0, 0], colorSpace='rgb'
            )
            stim_type = 'grating'

    # Try 움직이는 동심원
    def draw_patch(self, color, radial_phase=0.0):
        # 원 색상 변경
        self.stim.color = color
        self.stim.radialPhase = radial_phase  # animate inward/outward
        self.stim.draw()

    # RSVP 알파벳 생성기 
    def draw_rsvp(self, letter, color):
        self.rsvp_text.text = letter
        self.rsvp_text.color = color
        self.rsvp_text.draw()

    # 텍스트를 쓴다면
    def draw_text(self, text):
        stim = visual.TextStim(self.win, text=text, height=1.2)
        stim.draw()
        self.win.flip()
        event.waitKeys()

    #### Belows are from project vaping ####
    def draw_fixation(self):
        fixation = visual.GratingStim(self.win,
                                      color='#FFFFFF',
                                      tex=None,
                                      mask='cross',
                                      size=self.fixation_size,
                                      )
        fixation.draw()    

    def draw_wait(self):
        wait = visual.TextStim(self.win,
                               'WAIT',
                               font='NanumGothic',
                               pos=(0, 0),
                               wrapWidth=self.wrap_width,
                               # alignVert='center',
                               bold=True,
                               height=self.wait_height)
        wait.draw()
    
    def draw_countdown(self, text):
        count = visual.TextStim(self.win, text=text,
                                pos=(0.0, 0.0), height=self.wait_height)
        count.draw()

    def draw_intro(self):
        intro = visual.ImageStim(
            self.win,
            str((PATH_IMAGE_DIR / 'intro.png').absolute()),
            pos = (0,0)
        )
        intro.draw()

    def draw_main_before(self, block):
        text = visual.TextStim(
            self.win,
            self.instructions['main_before'][block % 6],
            font='NanumGothic',
            pos=(0, 0),
            wrapWidth=self.wrap_width,
            # alignVert='center',
            height=self.text_height)
        text.draw()

    def draw_main_after(self, block):
        text = visual.TextStim(
            self.win,
            self.instructions['main_after'][block % 6],
            font='NanumGothic',
            pos=(0, 0),
            wrapWidth=self.wrap_width,
            # alignVert='center',
            height=self.text_height)
        text.draw()

    def draw_outro(self):
        text = visual.TextStim(
            self.win,
            self.instructions['outro'],
            font='NanumGothic',
            pos=(0, 0),
            wrapWidth=self.wrap_width,
            # alignVert='center',
            height=self.text_height)
        text.draw()


# ========================== Runner 클래스 ==========================
class ColorDetectRunner:
    def __init__(self, win, drawer, schedule_file, subj_id, group, session,
                 block, path_data):
        self.win = win
        self.drawer = drawer
        self.schedule = pd.read_csv(schedule_file)
        self.results = []
        self.subj_id = subj_id
        self.group = group
        self.session = session
        self.block = block
        self.path_data = path_data
        self.global_clock = core.Clock()
        self.kb = keyboard.Keyboard(clock=self.global_clock)

    def show_texts(self):
        self.drawer.draw_text("Color Detection fMRI Experiment\n\nPress any key to begin.")
        self.drawer.draw_text("Focus on the center.\nPress when you see white 'K' followed by black 'K'.\n\nPress any key to start.")

    ### from Vaping ###
    # instructions
    def show_countdown(self):
        logging.info('3')
        self.drawer.draw_countdown('3')
        self.win.flip()
        core.wait(1)

        logging.info('2')
        self.drawer.draw_countdown('2')
        self.win.flip()
        core.wait(1)

        logging.info('1')
        self.drawer.draw_countdown('1')
        self.win.flip()
        core.wait(1)

    def show_intro(self):
        self.drawer.draw_intro()
        self.win.flip()
        _ = event.waitKeys(keyList=['1', 'num_1'])

    def show_outro(self):
        self.drawer.draw_outro()
        self.win.flip()
        _ = event.waitKeys(keyList=['1', 'num_1'])

    def show_block_start(self, block):
        logging.info(f'Block {block} starts... confirm?')
        self.drawer.draw_main_before(block-1)
        self.win.flip()
        _ = event.waitKeys(keyList=['1', 'num_1'])

    def show_block_end(self, block):
        logging.info(f'Block {block} ends...')
        self.drawer.draw_main_after(block-1)
        self.win.flip()
        _ = event.waitKeys(keyList=['1', 'num_1'])
    ### to this, from vaping ###

    def run_block(self):
        self.trial_logs = []
        self.rsvp_logs = []

        # wait
        self.show_countdown()
        self.drawer.draw_wait()
        self.win.flip()

        # (1) listen for scanner & record time
        self.kb.clearEvents()
        event.clearEvents(eventType='keyboard')

        ttl_press = self.kb.waitKeys(keyList=[TTL_KEY], waitRelease=False, clear=False)[0]
        ttl_pre_rel = ttl_press.rt                     # experiment relative time
        ttl_pre_abs = core.getAbsTime()                # absolute TTL time

        # (2) Set next frame as 'onset frame(t=0)'
        self.win.callOnFlip(self.global_clock.reset, 0.0)
        self.win.flip()                         
        run0_abs = core.getAbsTime()            # absolute time of run0

        # (3) Log the scan time info
        #     - time_scan        : TTL time(before reset, exp time)
        #     - timestamp_scan   : absolute time (ISO format)
        time_scan = ttl_pre_rel
        timestamp_scan = datetime.datetime.now().isoformat(timespec='milliseconds')
        os.makedirs(f'results/{self.subj_id}', exist_ok=True)

        with open(f'results/{self.subj_id}/scan_times_{self.block}.txt', 'w') as f:
            f.write(f"Time scan (pre-reset, expClock): {time_scan:.6f}\n")
            f.write(f"Timestamp scan (run0, ISO): {timestamp_scan}\n")
            f.write(f"TTL abs time (pre-reset): {ttl_pre_abs:.6f}\n")
            f.write(f"Run0 abs time: {run0_abs:.6f}\n")
            f.write("\n")

        # START TASK
        fixation_start_time, fixation_end_time = None, None  
        for idx, row in self.schedule.iterrows():
            # parameters from schedule
            stim_label = row['stimulus_label']
            onset = row['onset'] + 5 # wait for 5 second
            stim_color = COLOR_RGB[stim_label]

            # parameters for spinning
            direction = 1 if random.random() < 0.5 else -1

            # log for times
            trial_log = {}

            # 1) Show a fixation cross
            # Set fixation duration (e.g., random 2 or 4)
            fixation_duration = 2 if random.random() < 0.5 else 4
            fix_start = onset - fixation_duration

            # Wait until it's time to show fixation
            if fix_start > 0:
                while self.global_clock.getTime() < fix_start:
                    core.wait(0.001)
                
                # Fixation
                self.drawer.draw_fixation()
                fix_start_list = []
                self.win.callOnFlip(lambda: fix_start_list.append(self.global_clock.getTime())) 
                self.win.flip()
                fixation_start_time = fix_start_list[0]
                core.wait(fixation_duration)

            #### Onset ####
            while self.global_clock.getTime() < onset:
                core.wait(0.001)

            # Informations
            rsvp_log = []
            response_log = []

            # View CIRCLE
            if stim_label != 'blank':
                radial_phase = 0.0  # 위상 초기화
            frameDur = 1/((self.win.getActualFrameRate()) or 60)

            if stim_label != 'blank':
                self.drawer.stim.radialPhase = radial_phase
                self.drawer.draw_patch(stim_color, radial_phase)

            # Check TARGET RSVP
            target_shown = False
            target_probability = 0.33  
            if random.random() < target_probability:
                target_shown = True

            # FIRST RSVP
            if target_shown:
                current_letter, current_color = 'K', 'white'
            else:
                current_letter = random.choice(string.ascii_uppercase)
                current_color = 'white' if random.random() < 0.5 else 'black'
            rsvp_timer = 0
            
            # FIRST VIEW & record time
            stim_clock = core.Clock() # stimulus relative time (LOCAL)
            onset_list = []
            fix_end_list = []

            self.win.callOnFlip(stim_clock.reset, 0.0) # LOCAL clock reset
            self.win.callOnFlip(lambda: onset_list.append(self.global_clock.getTime()))
            self.win.callOnFlip(lambda: fix_end_list.append(self.global_clock.getTime()))
            self.win.flip()

            fixation_end_time = fix_end_list[0]
            stim_onset_global_time = onset_list[0] # onset of colored circle

            ##### Main Loop #####
            while stim_clock.getTime() < TRIAL_DURATION:
                # Always able to escape
                if event.getKeys(keyList=[ESC_KEY]): 
                    self.win.close()
                    core.quit()

                # set colored circle
                if stim_label != 'blank':
                    radial_phase += direction * DRIFT_CPS * frameDur  # inward / outward drift
                    # self.drawer.stim.radialPhase = radial_phase % 1.0 # change stim for movement
                    self.drawer.draw_patch(stim_color, radial_phase)  # %1.0: phase wrap-around
                    # 위상 초기화
                    if stim_clock.getTime() < 0.001:  # 트라이얼 시작시
                        self.drawer.stim.radialPhase = 0

                # if needed, change to second RSVP
                if stim_clock.getTime() - rsvp_timer >= RSVP_WAIT + RSVP_INTERVAL:
                    if target_shown:
                        current_letter, current_color = 'K', 'black'
                    else:
                        current_letter = random.choice(string.ascii_uppercase)
                        current_color = 'white' if random.random() < 0.5 else 'black'    
                    rsvp_timer = stim_clock.getTime()

                # draw RSVP during the period
                if (stim_clock.getTime() >= RSVP_WAIT) and (stim_clock.getTime() <= TRIAL_DURATION - RSVP_WAIT):
                    self.drawer.draw_rsvp(current_letter, current_color)

                self.win.flip()

                keys = self.kb.getKeys(keyList=['space', '1'], waitRelease=False, clear=False)
                for k in keys:
                    if k.name in ['space', '1']:
                        response_log.append({
                            'key': k.name,
                            'time_local': k.rt - stim_onset_global_time,  # 로컬(트라이얼 기준)
                            'time_global': k.rt                           # 글로벌(런 기준)
                        })

                rsvp_log.append({
                    'letter': current_letter,
                    'color': current_color,
                    'time': stim_clock.getTime(),
                    'global_time': self.global_clock.getTime()
                })

            # turn off the circle
            off_list = []
            self.win.callOnFlip(lambda: off_list.append(self.global_clock.getTime()))  # ✅ flip 직후
            self.win.flip()
            stim_end_global_time = off_list[0]
            stim_duration = stim_end_global_time - stim_onset_global_time

            self.results.append({
                'subj_id': self.subj_id,
                'group': self.group,
                'session': self.session,
                'block': self.block,                      
                'trial': int(row['trial']),
                'stimulus_label': stim_label,
                'stim_color_rgb': stim_color,
                'direction': 'inward' if direction == 1 else 'outward',
                'onset_scheduled': onset,                
                'onset_actual': stim_onset_global_time,  
                'duration_actual': stim_duration,
                'rsvp_stream': rsvp_log,
                'responses': response_log,
                'target_presented': target_shown
            })

            # === 로그 저장 ===
            trial_log.update({
                'subj_id': self.subj_id,
                'group': self.group,
                'session': self.session,
                'block': self.block,                      
                'trial': int(row['trial']),
                'stimulus_label': stim_label,
                'stim_color_rgb': stim_color,
                'direction': 'inward' if direction == 1 else 'outward',
                'onset_scheduled': onset,
                'fixation_start': fixation_start_time,
                'fixation_end': fixation_end_time,
                'stimulus_onset_time': stim_onset_global_time,
                'stimulus_end_time': stim_end_global_time,
                'rsvp_stream': rsvp_log,
                'responses': response_log,
                'target_presented': target_shown
            })

            self.trial_logs.append(trial_log)
            self.rsvp_logs.append(rsvp_log)

        flat_logs = [
            {
                'trial': t['trial'],
                'stimulus_label': t['stimulus_label'],
                'fixation_start': t['fixation_start'],
                'fixation_end': t['fixation_end'],
                'stimulus_onset_time': t['stimulus_onset_time'],
                'target_presented': t['target_presented'],
                'n_rsvp': len(t['rsvp_stream']),
                'n_response': len(t['responses']),
            } for t in self.trial_logs
        ]

        df = pd.DataFrame(flat_logs)
        df.to_csv(f"results/{self.subj_id}/trial_log_summary_{self.block}.csv", index=False)

        rsvp_flat = []
        for trial_idx, rsvp_trial in enumerate(self.rsvp_logs):
            for r in rsvp_trial:
                rsvp_flat.append({
                    'trial': trial_idx,
                    'letter': r['letter'],
                    'color': r['color'],
                    'time_local': r['time'],  # stim_clock 기준
                    'time_global': r['global_time']  # global_clock 기준
                })

        df_rsvp = pd.DataFrame(rsvp_flat)
        df_rsvp.to_csv(f"results/{self.subj_id}/rsvp_log_summary_{self.block}.csv", index=False)

    def save_results(self, filename):
        """
        BIDS 호환 events.tsv (trial-per-row).
        - onset, duration: 초[run-relative]
        - trial_type: 색상 라벨 (분석은 이걸 조건으로 사용)
        - 추가 열: run, block, trial, target_presented, L*a*b*, RGB 등 (선택)
        별도 행동 로그는 *_beh.tsv로 저장(선택).
        """

        beh_rows = [] # RSVP
        events_rows = [] # Colors

        for tr in self.results:
            onset = float(tr.get('onset_actual', np.nan))
            duration = float(tr.get('duration_actual', np.nan))
            trial_type = tr.get('stimulus_label', 'NA')
            color_rgb = tr.get('stim_color_rgb', [np.nan, np.nan, np.nan])
            r, g, b = float(color_rgb[0]), float(color_rgb[1]), float(color_rgb[2])

            # color log
            events_rows.append({
                'onset': onset,
                'duration': duration,
                'trial_type': trial_type,
                'block': self.block,
                'trial': int(tr["trial"]),
                'target_presented': int(bool(tr.get('target_presented', False)))
            })

            # RSVP log
            for rlog in tr.get("responses", []):
                beh_rows.append({
                    'trial': int(tr["trial"]),
                    'stimulus_label': trial_type,
                    'onset': onset,
                    'response_key': rlog.get('key', 'NA'),
                    'target_presented': int(bool(tr.get('target_presented', False))),
                    'response_time_local': rlog.get('time_local', np.nan),   
                    'response_time_global': rlog.get('time_global', np.nan)  
                })
                
        # save events
        events_df = pd.DataFrame(events_rows).sort_values("onset").reset_index(drop=True)
        Path(filename).parent.mkdir(exist_ok=True, parents=True)
        events_df.to_csv(filename, sep='\t', index=False)

        # save behavior
        beh_filename = str(filename).replace('_events.tsv', '_beh.tsv')
        if beh_rows:
            pd.DataFrame(beh_rows).to_csv(beh_filename, sep='\t', index=False)

# ========================== main ==========================
def main():
    # Year
    year_now = int(data.getDateStr('%Y'))

    # =============== 참가자 정보 입력 ========================
    dlg = gui.Dlg(title='Subject Information')
    dlg.addField('Study code', 'CVD')
    dlg.addField('Subject #', 2)
    dlg.addField('Group', 1)
    dlg.addField('Session', 1)
    dlg.addField('Block', 1)
    dlg.addField('Show instruction', True)
    dlg.addField('Date', data.getDateStr('%Y/%m/%d %H:%M'))
    dlg.addField('Mode', choices=MODES)  # 여기에서 mode 설정

    ok_data = dlg.show()
    if not dlg.OK:
        core.quit()

    study_code = ok_data[0]
    subj = int(ok_data[1])
    group = int(ok_data[2])
    sess = int(ok_data[3])
    block = int(ok_data[4])
    show_inst = ok_data[5]
    date = ok_data[6]
    mode = ok_data[7]
    size = 12 # UI size

    
    subj_id = f'{study_code}-{subj:02d}'

    path_info = Path(f'results/{subj_id}/ses-{sess}_colorDetect_run-{block}_info.json')
    path_data = Path(f'results/{subj_id}/ses-{sess}_colorDetect_run-{block}_events.tsv')
    path_info.parent.mkdir(parents=True, exist_ok=True)

    fields = ['Study code', 'Subject #', 'Group', 'Session', 'Block',
          'Show instruction', 'Date', 'Mode']
    info_dict = OrderedDict(zip(fields, ok_data))
    
    logging.info(f'The data will be saved to {str(path_data):s}.')
    with open(path_info, 'w') as f:
        json.dump(info_dict, f, indent=4)

    # =============== 창 설정(스캐너, 윈도우) =======================
    mon = monitors.Monitor(MON_NAME) # for fMRI
    use_pix = not mon.getSizePix() # True if moniter

    # For each monitor and fMRI
    if use_pix: 
        warnings.warn('Pixel mode (monitor not registered)',RuntimeWarning)
        units  ='pix'
    else:
        units = 'deg'

    # Full only with scanner
    if mode=='laptop': 
        fullscr = FULL_LAPTOP #False : monitor for test
    else:  
        fullscr = FULL_SCANNER #True
    
    # Set information for window size
    win_kw=dict(size=WIN_SIZE, 
                fullscr=fullscr, 
                units=units, 
                color='#333333', 
                waitBlanking=True,
                allowStencil=True, 
                screen = 1 if mode == 'scanner' else 0
                )
    
    if not use_pix: 
        win_kw['monitor'] = mon 

    # Open a window
    win = visual.Window(**win_kw)       
    if use_pix: 
        win.monitor.setSizePix(WIN_SIZE) 

    # =============== 키 설정  =======================
    event.globalKeys.clear()
    event.globalKeys.add(key=ESC_KEY, func=core.quit, name = 'shutdown') # ESC 전역 취소
    event.globalKeys.add(key=QuitKey, func=core.quit, name = 'shutdown') # ESC 전역 취소

    # =============== 자극 생성 및 진행  =======================
    # schedule_path = "schedules/optimized_schedule_test.csv" # for test and guide
    # schedule_path = PATH_SCHEDULE / f"pilot/optimized_schedule_run{block}.csv" # for pilot
    schedule_path = PATH_SCHEDULE / f"real/optimized_schedule_run{block}.csv" # for real
    # schedule_path = PATH_SCHEDULE / f"real/checkColor_schedule_run{block}.csv" # for colorCheck

    drawer = ColorDetectDrawer(win, size)
    runner = ColorDetectRunner(win, drawer, schedule_path, subj_id, group, sess,
                               block, path_data)

    if block == 1:
        runner.show_intro()
    runner.show_block_start(block)

    runner.run_block()
    runner.save_results(path_data)

    # runner.show_outro()
    if block == 6: 
        runner.show_outro()
    elif block < 12:
        runner.show_block_end(block)
    else:
        runner.show_outro()
    # drawer.draw_text("Experiment complete. Thank you!")

    win.close()
    core.quit()

if __name__ == '__main__':
    main()

# 여러 run, block 구현해야 함 (run_trials)
# you should add time_scan part!!