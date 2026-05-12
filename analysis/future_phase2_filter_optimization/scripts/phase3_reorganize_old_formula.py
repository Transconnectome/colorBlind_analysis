"""phase3_reorganize_old_formula.py — consolidate OLD-formula artifacts.

Source folders (will be DELETED after copy):
  results/old_formula_refit_full/
  results/old_formula_refit_4term/
  results/old_formula_vulnsim_cache/
  results/old_formula_loss_variants/V*/
  results/phase3_candidates/old_formula_viz/         (OLD-specific files only)
  results/old_formula_refit/                          (legacy small)

Target folder:
  results/old_formula/   (flat, single folder)

Naming convention:
  - Cache:     sub-XX_VV_vulnsim_cache.json
  - Landscape: sub-XX_VV_{VARIANT}_landscape.json
  - Summary:   sub-XX_VV_{VARIANT}_summary.json
  - 4-col:     4col_sub-XX_VV_{VARIANT}.png
  - F4 figure: fig_F4_VV_{VARIANT}.{png,pdf}   (subject embedded in figure)
  - Compare:   compare_VV_{VARIANT1}_vs_{VARIANT2}.png
  - Analysis:  ANALYSIS_{VARIANT}.md

VARIANT in: simplified, 4term, V1demeaned, V2pearson, V3rankw03, V3rankw02, V4ccc
"""
from __future__ import annotations
import shutil
import json
from pathlib import Path

PHASE2 = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/'
              'colorBlind_analysis/analysis/future_phase2_filter_optimization')
RESULTS = PHASE2 / 'results'
TARGET = RESULTS / 'old_formula'
TARGET.mkdir(parents=True, exist_ok=True)

operations = []


def plan(src: Path, dst: Path):
    operations.append((src, dst))


# ---- 1. vuln_sim cache ----
for src in (RESULTS / 'old_formula_vulnsim_cache').glob('sub-*_*.json'):
    # sub-08_V4_cache.json -> sub-08_V4_vulnsim_cache.json
    name = src.name.replace('_cache.json', '_vulnsim_cache.json')
    plan(src, TARGET / name)


# ---- 2. Simplified full grid ----
for src in (RESULTS / 'old_formula_refit_full').glob('sub-*_*.json'):
    # sub-08_V4_landscape.json -> sub-08_V4_simplified_landscape.json
    name = src.name.replace('_landscape.json', '_simplified_landscape.json') \
                   .replace('_summary.json',   '_simplified_summary.json')
    plan(src, TARGET / name)


# ---- 3. 4-term full grid ----
for src in (RESULTS / 'old_formula_refit_4term').glob('sub-*_*.json'):
    name = src.name.replace('_landscape.json', '_4term_landscape.json') \
                   .replace('_summary.json',   '_4term_summary.json')
    plan(src, TARGET / name)


# ---- 4. Loss variants ----
variant_map = {
    'V1_demeaned_mse':   'V1demeaned',
    'V2_pearson_added':  'V2pearson',
    'V3_rank_w03':       'V3rankw03',
    'V3_rank_w02':       'V3rankw02',
    'V4_ccc':            'V4ccc',
}
for vdir, vtag in variant_map.items():
    base = RESULTS / 'old_formula_loss_variants' / vdir
    if not base.exists():
        continue
    for src in base.glob('sub-*_*.json'):
        name = src.name.replace('_landscape.json', f'_{vtag}_landscape.json') \
                       .replace('_summary.json',   f'_{vtag}_summary.json')
        plan(src, TARGET / name)
    for src in base.glob('4col_sub-*.png'):
        # 4col_sub-08.png -> 4col_sub-08_V4_V1demeaned.png
        subj = src.stem.split('_')[1]   # sub-08 or sub-09
        plan(src, TARGET / f'4col_{subj}_V4_{vtag}.png')
    for src in base.glob('fig_*.png'):
        plan(src, TARGET / f'fig_F4_V4_{vtag}.png')
    for src in base.glob('fig_*.pdf'):
        plan(src, TARGET / f'fig_F4_V4_{vtag}.pdf')
    for src in base.glob('ANALYSIS.md'):
        plan(src, TARGET / f'ANALYSIS_{vtag}.md')


# ---- 5. Figures in phase3_candidates/old_formula_viz/ ----
viz = RESULTS / 'phase3_candidates' / 'old_formula_viz'
if viz.exists():
    # F4-style figures
    for nm, vtag in [('fig_old_simplified', 'simplified'),
                     ('fig_old_4term', '4term')]:
        for ext in ['png', 'pdf']:
            src = viz / f'{nm}.{ext}'
            if src.exists():
                plan(src, TARGET / f'fig_F4_V4_{vtag}.{ext}')
    # 4-col files
    rename_4col = {
        '4col_sub-08_simplified.png': '4col_sub-08_V4_simplified.png',
        '4col_sub-08_4term.png':      '4col_sub-08_V4_4term.png',
        '4col_sub-09_simplified.png': '4col_sub-09_V4_simplified.png',
        '4col_sub-09_4term.png':      '4col_sub-09_V4_4term.png',
    }
    for old, new in rename_4col.items():
        src = viz / old
        if src.exists():
            plan(src, TARGET / new)
    # Old single-candidate renders (preserve as reference)
    rename_old = {
        'old_sub08_V4_primary.png':    'ref_4col_sub-08_V4_10n32_primary.png',
        'old_sub08_V4_p2a_top.png':    'ref_4col_sub-08_V4_40p26_p2a.png',
        'old_sub08_V4_behavPASS.png':  'ref_4col_sub-08_V4_38p7_v4only.png',
        'old_sub08_V1_primary.png':    'ref_4col_sub-08_V1_50p50_edge.png',
        'old_sub09_V4_primary.png':    'ref_4col_sub-09_V4_30p46_primary.png',
    }
    for old, new in rename_old.items():
        src = viz / old
        if src.exists():
            plan(src, TARGET / new)
    # Comparison figure
    src = viz / 'compare_40p26_vs_16p40.png'
    if src.exists():
        plan(src, TARGET / 'compare_sub-08_V4_40p26-vs-16p40.png')


# ---- 6. Legacy small file ----
src = RESULTS / 'old_formula_refit' / 'sub-08_V4_old_vs_current.json'
if src.exists():
    plan(src, TARGET / 'legacy_sub-08_V4_old_vs_current.json')


# ---- Execute ----
print(f'Planned {len(operations)} file operations')
print(f'Target: {TARGET}')
print()
print('Sample plan (first 15):')
for src, dst in operations[:15]:
    print(f'  {src.name}  →  {dst.name}')
print(f'  ... {len(operations) - 15} more' if len(operations) > 15 else '')

print('\nExecuting moves...')
for src, dst in operations:
    if src.exists():
        shutil.move(str(src), str(dst))
print(f'Moved {len(operations)} files.')


# ---- Delete now-empty source folders ----
folders_to_delete = [
    RESULTS / 'old_formula_vulnsim_cache',
    RESULTS / 'old_formula_refit_full',
    RESULTS / 'old_formula_refit_4term',
    RESULTS / 'old_formula_loss_variants',
    RESULTS / 'old_formula_refit',
    RESULTS / 'phase3_candidates' / 'old_formula_viz',
]
print('\nDeleting legacy folders...')
for d in folders_to_delete:
    if d.exists():
        shutil.rmtree(d)
        print(f'  rm -rf {d}')
print('Done.')

# ---- Write README ----
readme = TARGET / 'README.md'
readme_content = f"""# OLD-Formula Refit Results

All artifacts from OLD CIElab-direct 2-component refit (`δθ = β_s·cos(θ−90°) + β_c·cos(θ−150°)`)
consolidated in this single folder. Naming convention:

```
sub-XX_VV_{{VARIANT}}_{{TYPE}}.{{ext}}
```

## VARIANT codes
| Code | Loss formula |
|---|---|
| `simplified` | 1.0·L_vuln + 0.5·L_rank (original 2-term) |
| `4term`      | 1.0·L_vuln + 0.5·L_rank + 0.2·L_rdm + 0.1·L_smooth (§3 canonical 4-term) |
| `V1demeaned` | demeaned MSE: removes offset penalty |
| `V2pearson`  | adds L_pearson term (0.5·L_pearson) |
| `V3rankw03`  | L_rank weight reduced to 0.3 |
| `V3rankw02`  | L_rank weight reduced to 0.2 |
| `V4ccc`      | CCC-based: 1.0·L_ccc + 0.1·L_smooth |

## TYPE codes
- `landscape.json`: full 1326-cell grid (β_s × β_c)
- `summary.json`: best params + top-N
- `4col_sub-XX_VV_VARIANT.png`: 4-column color visualization (Original / CVD perceives / Pre-image / CVD(filtered))
- `fig_F4_VV_VARIANT.{{png,pdf}}`: F4-style figure (sub-08 + sub-09 in one image)
- `compare_*.png`: side-by-side comparison
- `ANALYSIS_{{VARIANT}}.md`: variant analysis

## Optima summary (sub-08 V4)

| VARIANT | argmin (β_s, β_c) | ρ | P2a |
|---|---|---|---|
| simplified  | (10, −32) | 0.833 | 0.250 |
| 4term       | (10, −32) | 0.833 | 0.250 |
| V1demeaned  | (10, −32) | 0.833 | 0.250 |
| V2pearson   | (10, −32) | 0.833 | 0.250 |
| V3rankw03   | (10, −32) | 0.833 | 0.250 |
| V3rankw02   | (10, −32) | 0.833 | 0.250 |
| **V4ccc**   | **(16, +40)** | 0.381 | 0.537 |

## Reference (not loss-variant argmin, separately rendered)
- `ref_4col_sub-08_V4_40p26_p2a.png`: (β_s=40, β_c=+26) — P2a-behavior-best within OLD top 10 (P2a=0.575, 4/8 exact)
- `ref_4col_sub-08_V4_38p7_v4only.png`: V4-only OLD (38, +7) — behaviorally PASS (P1=2+3p/8)
- `ref_4col_sub-08_V1_50p50_edge.png`: sub-08 V1 OLD grid-edge degenerate
- `compare_sub-08_V4_40p26-vs-16p40.png`: P2a-best vs V4 CCC argmin side-by-side

## Cache
- `sub-XX_V4_vulnsim_cache.json`: 1326-cell vuln_sim cache (re-used by loss variants)

## Related documents (in parent dir)
- `../../phase3_loss_variants_comparison.md`: full 4-variant comparison
- `../../phase3_old_rendering_optima.md`: original OLD §3 application
- `../../phase3_justify_v4only.md`: 3-approach justification
"""
readme.write_text(readme_content)
print(f'Wrote {readme}')
