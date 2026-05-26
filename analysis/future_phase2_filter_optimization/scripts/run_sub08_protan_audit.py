"""
Sub-08 protan-axis audit run (Phase B v6 with family='protan' override).

User question 2026-05-26:
    "sub-08 혹시 protan axis (axis = 16) 적용해도 2-comp 44, 36 나오나 확인"

Sub-08 is deutan (θ_conf=150°). Under protan family (θ_conf=16°), forward δθ
is qualitatively different — e.g., (β_s=44, β_c=36) gives magenta δθ ≈ −14°
under protan vs −66° under deutan.

This script reuses s10b_v6_pca_rdm.fit_subject() with the SUBJECTS dict patched
so sub-08 runs under protan family. Output saved with `_protan_audit` suffix.

If (β_s=44, β_c=36) (or other cycle6b NEW candidates) STILL surfaces under the
protan model fit, the candidate is family-non-specific (likely general
RG-distortion absorbed by both axes). If it disappears, the candidate is
deutan-axis-specific.
"""
import json
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import s10b_v6_pca_rdm as v6

# Patch sub-08 family to 'protan' for this audit run
v6.SUBJECTS['sub-08'] = dict(v6.SUBJECTS['sub-08'], family='protan')
print(f"[AUDIT] sub-08 SUBJECTS patched: family={v6.SUBJECTS['sub-08']['family']}", flush=True)

OUT_DIR = SCRIPT_DIR.parent / "results" / "s10_inclusion"


def main():
    sid = 'sub-08'
    t0 = time.time()
    print(f"Running Phase B v6 for {sid} under PROTAN family (audit)...", flush=True)
    storage = v6.fit_subject(sid)
    summary = v6.summarize(storage)
    elapsed = round(time.time() - t0, 1)
    print(f"\n[{sid} protan audit] total elapsed: {elapsed}s", flush=True)

    out_file = OUT_DIR / f"s10b_v6_pca_rdm_results_{sid}_protan_audit.json"
    with open(out_file, 'w') as f:
        json.dump({
            'subject': sid,
            'family_override': 'protan',
            'storage_keys': list(storage.keys()),
            'summary': summary,
            'elapsed': elapsed,
            'meta': {
                'n_resamples': v6.N_RESAMPLES,
                'subset_size': v6.SUBSET_SIZE,
                'seed_base': v6.RNG_SEED,
                'note': 'AUDIT — sub-08 (true deutan) fit under PROTAN family. '
                        'Purpose: test family-specificity of cycle6b NEW candidates.',
            },
        }, f, indent=2, default=str)
    print(f"Saved: {out_file}", flush=True)


if __name__ == "__main__":
    main()
