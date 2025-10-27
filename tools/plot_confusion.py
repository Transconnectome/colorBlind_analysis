#!/usr/bin/env python3
"""
Utility to plot and save a confusion matrix.

Usage examples:
  # from y_true/y_pred numpy artifacts produced by the baseline runner
  python tools/plot_confusion.py --y_true derivatives/sub-01/experiments/.../y_true_2025....npy \
    --y_pred derivatives/sub-01/experiments/.../y_pred_2025....npy \
    --out confusion_matrix_custom.png

  # from a precomputed confusion matrix numpy file
  python tools/plot_confusion.py --cm_npy path/to/cm.npy --out cm.png

This keeps plotting code centralized and prevents small typos (like a truncated
ylabel call) from being duplicated across scripts.
"""
import argparse
import datetime
import json
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix, accuracy_score


def save_confusion_matrix(cm, outpath, acc=None, labels=None, cmap='Blues'):
    """Save a confusion matrix image to `outpath`.

    cm: 2D array-like (square)
    outpath: str or Path to write PNG
    acc: optional float to show in title
    labels: optional list of tick labels
    """
    cm = np.asarray(cm)
    fig, ax = plt.subplots(figsize=(6, 6))
    im = ax.imshow(cm, interpolation='nearest', cmap=cmap)
    title = "Confusion matrix"
    if acc is not None:
        title = f"{title} (acc={acc:.3f})"
    ax.set_title(title)
    ax.set_xlabel('predicted')
    ax.set_ylabel('true')
    if labels is not None:
        ticks = np.arange(len(labels))
        ax.set_xticks(ticks)
        ax.set_yticks(ticks)
        ax.set_xticklabels(labels, rotation=45)
        ax.set_yticklabels(labels)
    else:
        # default ticks
        n = cm.shape[0]
        ax.set_xticks(np.arange(n))
        ax.set_yticks(np.arange(n))

    plt.colorbar(im, ax=ax)
    outpath = Path(outpath)
    outpath.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(str(outpath), dpi=150, bbox_inches='tight')
    plt.close(fig)


def _load_npy(path):
    return np.load(path)


def main():
    p = argparse.ArgumentParser(description='Plot confusion matrix from artifacts')
    p.add_argument('--y_true', help='Path to numpy file with y_true array')
    p.add_argument('--y_pred', help='Path to numpy file with y_pred array')
    p.add_argument('--cm_npy', help='Path to numpy file containing confusion matrix')
    p.add_argument('--out', help='Output PNG path (default: confusion_matrix_<ts>.png)')
    p.add_argument('--labels', help='Optional JSON list file with labels for axes')
    args = p.parse_args()

    cm = None
    acc = None

    if args.cm_npy:
        cm = _load_npy(args.cm_npy)
    elif args.y_true and args.y_pred:
        y_true = _load_npy(args.y_true)
        y_pred = _load_npy(args.y_pred)
        cm = confusion_matrix(y_true, y_pred)
        acc = accuracy_score(y_true, y_pred)
    else:
        raise SystemExit('Provide either --cm_npy or both --y_true and --y_pred')

    labels = None
    if args.labels:
        try:
            labels = json.load(open(args.labels, 'r'))
        except Exception:
            print('Warning: failed to read labels JSON; continuing without labels')

    if args.out is None:
        ts = datetime.datetime.now().strftime('%Y%m%dT%H%M%S')
        out = f'confusion_matrix_{ts}.png'
    else:
        out = args.out

    save_confusion_matrix(cm, out, acc=acc, labels=labels)
    print(f'Wrote confusion matrix image to {out}')


if __name__ == '__main__':
    main()
