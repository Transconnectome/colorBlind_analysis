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
COLOR_RGB = {
    'color_1': [-0.84,  0.20,  0.08],  # reddish
    'color_2': [-0.96, -0.24,  0.64],  # orange
    'color_3': [-0.98, -0.80,  0.96],  # yellow
    'color_4': [ 0.60, -0.56,  0.52],  # greenish
    'color_5': [ 1.00, -0.48, -0.56],  # cyan
    'color_6': [ 0.90,  0.24, -0.90],  # blue
    'color_7': [-0.24,  0.20, -0.72],  # violet
    'color_8': [-0.90, -0.20, -0.70],  # pinkish
    'blank':    [0.5, 0.5, 0.5]     # neutral gray
}

## RGB -> CIELab Translation code. Add if needed
# def lab2rgb(L,a,b,clip=True):
#     L,a,b = float(L),float(a),float(b)
#     y=(L+16)/116; x=a/500+y; z=y-b/200
#     xyz=np.array([x,y,z]); xyz=np.where(xyz>.206893, xyz**3,(xyz-16/116)/7.787)
#     xyz*=[.95047,1.,1.08883]
#     rgb=np.dot([[ 3.2406,-1.5372,-.4986],[-.9689,1.8758,.0415],[.0557,-.2040,1.0570]],xyz)
#     rgb=np.where(rgb<=.0031308,12.92*rgb,1.055*rgb**(1/2.4)-.055)
#     if clip: rgb=np.clip(rgb,0,1)
#     return rgb.tolist()
# rgb_colors=[lab2rgb(75,40*np.cos(t),40*np.sin(t)) for t in np.deg2rad(np.arange(0,360,45))]

TRIAL_DURATION = 1.5
RSVP_INTERVAL = 0.4
RSVP_WAIT = 0.35

TTL_KEY, SPACE_KEY, ESC_KEY = '5', 'space', 'escape'
MODES = ['laptop', 'scanner']
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
                interpolate=True, color=[0.5, 0.5, 0.5], colorSpace='rgb',
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
                interpolate=True, color=[0.5, 0.5, 0.5], colorSpace='rgb'
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

        # listen for scanner
        keys = event.waitKeys(keyList=['5'], timeStamped = True)
        now = datetime.datetime.now()

        time_scan = keys[0][1]
        timestamp_scan = str(now)

        with open(f'results/{self.subj_id}/scan_times_{self.block}.txt', 'w') as f:  
            f.write(f"Time scan: {time_scan}\n")
            f.write(f"Timestamp scan: {timestamp_scan}\n")
            f.write("\n")  # Add a blank line between entries

        # START TASK
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
                fixation_start_time = self.global_clock.getTime()
                self.drawer.draw_fixation()
                self.win.flip()
                core.wait(fixation_duration)
                fixation_end_time = self.global_clock.getTime()            

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
            
            # FIRST VIEW
            self.win.flip()
            stim_clock = core.Clock()
            stim_onset_global_time = self.global_clock.getTime()

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
                    self.drawer.draw_patch(stim_color)  # %1.0: phase wrap-around
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

                keys = event.getKeys(timeStamped=stim_clock)
                for k, t in keys:
                    if k in ['space', '1']:
                        response_log.append({'key': k, 'time': t,
                                             'global_time': self.global_clock.getTime()})

                rsvp_log.append({
                    'letter': current_letter,
                    'color': current_color,
                    'time': stim_clock.getTime(),
                    'global_time': self.global_clock.getTime()
                })

            # turn off the circle
            self.win.flip()
            stim_end_global_time = self.global_clock.getTime()

            # wait until Next onset : DONE BY FIXATION (0706)
            # if idx < len(self.schedule) - 1:
            #     next_onset = self.schedule.iloc[idx + 1]['onset']
            #     ISI = max(0, next_onset - (onset + TRIAL_DURATION))
            #     self.win.flip()
            #     core.wait(ISI)

            self.results.append({
                'subj_id': self.subj_id,
                'group': self.group,
                'session': self.session,
                'trial': int(row['trial']),
                'stimulus_label': stim_label,
                'stim_color_rgb': stim_color,
                'direction': 'inward' if direction == 1 else 'outward',
                'onset': onset,
                'rsvp_stream': rsvp_log,
                'responses': response_log,
                'target_presented': target_shown
            })

            # === 로그 저장 ===
            trial_log.update({
                'subj_id': self.subj_id,
                'group': self.group,
                'session': self.session,
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
        output = []
        for trial in self.results:
            for r in trial['responses']:
                output.append({
                    'subj_id': trial['subj_id'],
                    'group': trial['group'],
                    'session': trial['session'],
                    'trial': trial['trial'],
                    'stimulus_label': trial['stimulus_label'],
                    'direction': trial['direction'],
                    'onset': trial['onset'],
                    'response_key': r['key'],
                    'response_time': r['time'],
                    'target_presented': trial['target_presented']
                })
        df = pd.DataFrame(output)
        Path(filename).parent.mkdir(exist_ok=True, parents=True)
        df.to_csv(filename, sep='\t', index=False)

# ========================== main ==========================
def main():
    # Year
    year_now = int(data.getDateStr('%Y'))

    # =============== 참가자 정보 입력 ========================
    dlg = gui.Dlg(title='Subject Information')
    dlg.addField('Study code', 'CDX')
    dlg.addField('Subject #', 1)
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

    
    subj_id = f'{study_code}{subj:03d}'

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
                allowStencil=True
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