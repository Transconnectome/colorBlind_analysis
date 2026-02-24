#!/usr/bin/env python3
"""Quick architecture sweep: FE baseline vs various MLP Sequential configs."""
import sys
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_loco_comparison import (
    loco_cv, LOCOForwardEncodingDecoder, HybridMLPSequential,
    load_amplitudes,
)

baseline = Path(__file__).resolve().parents[4] / \
    "analysis/phase1_preprocess_decoding/results/full_dataset_C010"

configs = [
    ("FE baseline (no MLP)", None),
    ("MLP (64,32) a=0.1",   ((64, 32), 0.1)),
    ("MLP (64,32) a=1.0",   ((64, 32), 1.0)),
    ("MLP (16,)   a=0.1",   ((16,),    0.1)),
    ("MLP (16,)   a=1.0",   ((16,),    1.0)),
    ("MLP (8,)    a=0.1",   ((8,),     0.1)),
    ("MLP (8,)    a=1.0",   ((8,),     1.0)),
    ("MLP (8,)    a=10.",   ((8,),     10.0)),
]

subjects = ["01", "03", "05"]

header = "{:<25s} | {:>8s} {:>8s} {:>8s} | {:>8s}  {:>6s}".format(
    "Config", "sub-01", "sub-03", "sub-05", "Mean", "params"
)
print(header)
print("-" * len(header))

for name, cfg in configs:
    maes = []
    for subj in subjects:
        amp = load_amplitudes(str(baseline), subj, "V1", "procrustes")

        if cfg is None:
            folds = loco_cv(amp, LOCOForwardEncodingDecoder, "ForwardEncoding")
        else:
            hidden, alpha = cfg

            class TempMLP(HybridMLPSequential):
                _h, _a = hidden, alpha
                def __init__(self):
                    super().__init__(fe_alpha=0, n_channels=6,
                                    hidden_layer_sizes=self._h,
                                    mlp_alpha=self._a)

            folds = loco_cv(amp, TempMLP, "HybridMLP_Sequential")

        mae = np.mean([f["mae"] for f in folds])
        maes.append(mae)

    if cfg is None:
        p = "N/A"
    else:
        hidden, _ = cfg
        layers = [6] + list(hidden) + [6]
        params = sum(layers[i] * layers[i+1] + layers[i+1]
                     for i in range(len(layers) - 1))
        p = str(params)

    print("{:<25s} | {:7.1f}  {:7.1f}  {:7.1f}  | {:7.1f}   {:>6s}".format(
        name, maes[0], maes[1], maes[2], np.mean(maes), p
    ))
