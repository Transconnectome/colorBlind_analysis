"""phase3_old_formula_4term_sub09.py — sub-09 V4 4-term refit only."""
from __future__ import annotations
import sys
from pathlib import Path

_THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_THIS_DIR))

from phase3_old_formula_4term import fit_subject_roi


def main():
    fit_subject_roi('09', 'V4')


if __name__ == '__main__':
    main()
