#!/usr/bin/env python3
"""
capture_rsvp.py — capture actual PsychoPy stimulus frames for Figure 1
Run:  conda run -n colorBlind python docs/PAPER/Figures/scripts/capture_rsvp.py
      (from project root)

Outputs: docs/PAPER/Figures/rsvp_fix.png
         docs/PAPER/Figures/rsvp_stim_red.png     (white K)
         docs/PAPER/Figures/rsvp_stim_kblack.png  (black K)
"""
import sys, time
import numpy as np
from pathlib import Path

OUT = Path(__file__).parent.parent   # docs/PAPER/Figures/

# ── PsychoPy-compatible LAB→RGB ([-1,1] range) ────────────────────────────────
def lab2rgb_pp(L, a, b):
    """CIELab → PsychoPy [-1,1] RGB, clipped."""
    y=(L+16)/116; x=a/500+y; z=y-b/200
    xyz=np.array([x,y,z])
    xyz=np.where(xyz>.206893, xyz**3,(xyz-16/116)/7.787)
    xyz*=[.95047,1.,1.08883]
    rgb=np.dot([[3.2406,-1.5372,-.4986],[-.9689,1.8758,.0415],[.0557,-.2040,1.0570]],xyz)
    rgb=np.where(rgb<=.0031308,12.92*rgb,1.055*rgb**(1/2.4)-.055)
    return (np.clip(rgb,0,1)*2-1).tolist()

# Red = color_1 from colorBlind_test.py: L=75, a=-40, b=0
COLOR_RED = lab2rgb_pp(75, -40.0, 0.0)

WIN_SZ  = 600
GRAT_SZ = 480   # diameter in px — matches ~GRAT_DIAM_PX=500 at 96%
FIX_SZ  = 40    # fixation cross size in px
RSVP_H  = 80    # RSVP letter height in px

from psychopy import visual, core

win = visual.Window(
    size=(WIN_SZ, WIN_SZ),
    fullscr=False,
    units='pix',
    color=[0, 0, 0],      # mid-gray (PsychoPy [-1,1] neutral = experiment bg)
    colorSpace='rgb',
    screen=0,
    winType='pyglet',
)

fixation = visual.GratingStim(
    win=win, tex=None, mask='cross',
    size=FIX_SZ, units='pix',
    color=[1, 1, 1], colorSpace='rgb',
)

stim = visual.RadialStim(
    win=win, tex='sin', mask='circle',
    size=GRAT_SZ, units='pix',
    radialCycles=5,
    angularCycles=0,
    radialPhase=0.0,
    visibleWedge=(0, 360),
    texRes=512,
    interpolate=True,
    color=COLOR_RED, colorSpace='rgb',
    contrast=1.0,
)

rsvp_letter = visual.TextStim(
    win=win, text='K',
    height=RSVP_H, units='pix',
    pos=(0, 0),                    # centered, no vertical offset
    color=[1, 1, 1], colorSpace='rgb',
    bold=True,
)

def capture(fname):
    """Capture the current back buffer and save."""
    win.getMovieFrame()
    win.saveMovieFrames(str(OUT / fname))
    win.movieFrames = []
    print(f"  Saved: {OUT / fname}")

# ── Frame 1: Fixation only ─────────────────────────────────────────────────────
win.clearBuffer()
fixation.draw()
win.flip()
time.sleep(0.1)
win.getMovieFrame(buffer='front')
win.saveMovieFrames(str(OUT / 'rsvp_fix.png'))
win.movieFrames = []

# ── Frame 2: Red stimulus + RSVP letter (no fixation — avoids overlap with letter)
win.clearBuffer()
stim.draw()
rsvp_letter.draw()
win.flip()
time.sleep(0.1)
win.getMovieFrame(buffer='front')
win.saveMovieFrames(str(OUT / 'rsvp_stim_red.png'))
win.movieFrames = []

# ── Frame 3: Red stimulus + BLACK K ───────────────────────────────────────────
rsvp_letter.color = [-1, -1, -1]   # black K
win.clearBuffer()
stim.draw()
rsvp_letter.draw()
win.flip()
time.sleep(0.1)
win.getMovieFrame(buffer='front')
win.saveMovieFrames(str(OUT / 'rsvp_stim_kblack.png'))
win.movieFrames = []

win.close()
core.quit()
print("Done.")
