# Label/Rendering Cleanup Plan (2026-05-16)

**Purpose**: Identify and archive results produced under OLD label scheme (pre-2026-05-16) so future works are not contaminated by superseded P2a rankings.

**Trigger**: User request 2026-05-16 — "Remove outdated results and rankings; remove results from previous rendering or labels from memory for future works."

**Policy**: This document inventories — does **NOT** delete or move files. User confirms each block before any `mv`/`rm`.

---

## Label-scheme cutoff

| Scheme | Files defining it | HC bin count | Adopted |
|---|---|---|---|
| **OLD** | `scripts/phase3_candidate_analysis_v2.py` (`HC_NAME_BINS`, `SUB08_ORIGINAL_HC_EQUIV`) | 13 bins (red, red-orange, orange, yellow-orange, yellow, yellow-green, green, cyan, sky, blue, violet, magenta, pink) | pre-2026-05-16 |
| **NEW (CORRECTED)** | `scripts/c3_relabel_p2a.py`, `scripts/c3_relabel_both_subjects.py` (`HC_NAME_BINS_NEW`, `SUB08_ORIG_NEW`, `SUB09_ORIG_NEW`) | 9 bins matching STIM_LAB renderer (pink, red-orange, olive, green, cyan, sky-cyan, sky-blue, violet, blue-violet) | 2026-05-15→ |

**Why the change matters** — rank-reversals between schemes:
- V4 voxRDM (28, −18) sub-08: OLD P2a=0.400, NEW P2a=0.750
- Option C (40, +26) sub-08: OLD P2a=0.575★, NEW P2a=0.500 (worst)
- OPT-1 (40, +26): OLD 0.575★ vs NEW 0.500 (worst)

Any ranking, "best filter" claim, or filter-selection narrative produced under OLD scheme is **potentially wrong** under current labels.

---

## Inventory of result directories (by scheme)

### KEEP — NEW (CORRECTED) scheme

| Dir | Files | Status |
|---|---|---|
| `results/c3_relabel/` | 91 | **Single source of truth** for current P2a numbers. Contains CORRECTED_* viz, SYNTHESIS_2026-05-16.md, SCIENTIFIC_NARRATIVE_2026-05-16.md, LABEL_CLEANUP_PLAN_2026-05-16.md (this), all Track A/B docs. |

### KEEP — neural-fit data, label-independent

| Dir | Files | Reason |
|---|---|---|
| `results/fits/` | 91 | Neural fit JSONs (β, ρ, perm_p, vuln_sim). No label dependency — these are pure model fits to fMRI. The (38,−14), (6,−22), R+C pre-image all live here. |

### KEEP — already archived/superseded

| Dir | Files | Status |
|---|---|---|
| `results/_archive/` | 14 | Pre-existing archive. |
| `results/_superseded/` | 86 | Explicitly marked superseded before 2026-05-16. |

### PROPOSE ARCHIVE — OLD scheme viz/rankings

These directories were produced before 2026-05-16 using OLD `HC_NAME_BINS`. Any P2a number, ranking, or filter recommendation in them is superseded.

| Dir | Files | Modified | Notes |
|---|---|---|---|
| `results/CANDIDATE/` | 132 | 2026-05-12 | Pre-Option-C filter candidates with OLD P2a. |
| `results/phase2_artifacts/` | 266 | 2026-05-12 | Fixed-W viz, OLD P2a. |
| `results/old_formula/` | 124 | 2026-05-12 | V4-CCC formula landscapes — JSONs label-independent, viz superseded. |
| `results/BAYESIAN_BEST/` | 13 | 2026-05-12 | Bayesian filter with OLD P2a rankings. |
| `results/axis_3way/` | 7 | 2026-05-12 | 3-way comparison with OLD labels. |
| `results/LIT2Neural/` | 6 | 2026-05-13 | LIT2Neural endpoints with OLD P2a (sub-08 0.600, sub-09 0.812 per today's NEW verification — already superseded). |
| `results/p2amax_neural_deep/` | 1 | 2026-05-13 | OLD scheme. |
| `results/p2amax_neural_no_sign/` | 1 | 2026-05-13 | OLD scheme. |
| `results/p2amax_neural_only_loss/` | 1 | 2026-05-13 | OLD scheme. |
| `results/p2amax_unified_loss/` | 1 | 2026-05-13 | OLD scheme. |
| `results/p2amax_updated/` | 2 | 2026-05-13 | OLD scheme (only OLD_hits detected). |
| `results/literature_applied/` | 1 | 2026-05-13 | OLD scheme. |
| `results/literature_recovery/` | 3 | 2026-05-13 | OLD scheme. |
| `results/principled_justification/` | 1 | 2026-05-13 | OLD scheme. |
| `results/identifiability/` | 3 | 2026-05-13 | OLD scheme. |
| `results/c3_proposals/` | 6 | 2026-05-15 | Mid-May c3 work; uses `phase3_candidate_analysis_v2.SUB08_ORIGINAL_HC_EQUIV` (OLD). |
| `results/c3_canonical_search/` | 1 | 2026-05-15 | OLD scheme (verified). |
| `results/c3_candidate_search/` | 1 | 2026-05-15 | OLD scheme (verified). |

**Total OLD-era files**: ~570

---

## Recommended archive structure

```
results/_archive/
└── old_labels_pre_2026-05-16/
    ├── README.md              # explains cutoff date, scheme difference
    ├── CANDIDATE/
    ├── phase2_artifacts/
    ├── old_formula/
    ├── BAYESIAN_BEST/
    ├── axis_3way/
    ├── LIT2Neural/
    ├── p2amax_neural_deep/
    ├── p2amax_neural_no_sign/
    ├── p2amax_neural_only_loss/
    ├── p2amax_unified_loss/
    ├── p2amax_updated/
    ├── literature_applied/
    ├── literature_recovery/
    ├── principled_justification/
    ├── identifiability/
    ├── c3_proposals/
    ├── c3_canonical_search/
    └── c3_candidate_search/
```

`mv` (not `rm`) — preserves data for forensic comparison; user can `rm` later if confident.

---

## Scripts to flag for caveat or update

Scripts still importing OLD scheme from `phase3_candidate_analysis_v2`:

```
scripts/p2amax_new_loss_sweep.py
scripts/dissociation_map_figure.py
scripts/fixedW_onlyTest_v4ccc.py
scripts/LIT2Neural_original_visualize.py
scripts/LIT2Neural_hybrid_unified.py
scripts/p2amax_options_visualize.py
scripts/p2amax_option_C_visualize.py
scripts/phase3_loss_behav_concordance.py
scripts/LIT2Neural_filterBest_visualize.py
scripts/c8_target_sensitivity.py
scripts/neural_only_unified_loss.py
scripts/p2amax_loss_search.py
scripts/p2a_loss_reverse_engineer.py
scripts/p2a_gap_diagnosis.py
scripts/candidates_visualize_all.py
scripts/LIT2Neural_visualize.py
scripts/loss_alternatives_sweep.py
scripts/fixedW_onlyTest_ltopk_sweep.py
scripts/p2a_landscape_explore.py
scripts/phase3_fit_opponent_gain_v2.py
scripts/p2amax_neural_derived_deep.py
scripts/p2amax_option_C_F4_v2.py
scripts/unified_loss_bootstrap_anchor.py
scripts/fixedW_onlyTest_p2a_ranking.py
scripts/neural_primary_composite.py
scripts/c3_canonical_search.py
scripts/neural_only_deep_sweep.py
scripts/c3_candidate_search.py
scripts/c3_canonical_search.py
scripts/c3_render_corrected_p2a.py  ← uses OLD as side effect of monkey-patching, but produces NEW outputs (this one OK)
scripts/c3_track_b_alternative_loss.py  ← imports OLD but uses NEW p2a_corrected
scripts/c3_relabel_p2a.py  ← defines NEW (the canonical NEW source)
```

**Recommendation**: Do not modify these scripts. Instead, add a top-of-file comment in `phase3_candidate_analysis_v2.py` itself warning that `HC_NAME_BINS` and `SUB08_ORIGINAL_HC_EQUIV` are OLD scheme — superseded by `c3_relabel_p2a.HC_NAME_BINS_NEW` and `SUB08_ORIG_NEW`. Any future P2a evaluation must use the NEW source.

---

## MEMORY entries to update (project memory + auto-memory)

### Project memory files

- `~/.claude/projects/.../memory/project_phase2_closure.md` (Phase 2 Closure entry) — references OLD-scheme decisions; add header note pointing to corrected labels
- `~/.claude/projects/.../memory/project_stim_lab_rendering.md` — already documents STIM_LAB fix at 2026-05-10; add label-correction note 2026-05-16

### Auto-memory MEMORY.md entries containing OLD-scheme P2a

Sections to amend with "[OLD-scheme; superseded by NEW c3_relabel_p2a]" markers:

1. **"LOCO-Primary Filter Design (updated 2026-04-09)"** — references hV4 LOCO 2-comp results (β values are label-independent), but if any P2a number cited, mark.
2. **"2-Component Pre-Image (2026-04-09)"** — pre-image numbers label-independent (8/8 exact in model space), but P2a citations would be OLD.
3. **"R+C Model & 2-Component Findings (2026-04-07)"** — sub-08 LOCO V1 p=0.047, etc. — these are label-independent (neural-only). Keep.
4. **Any P2a citation post-2026-05-13 Option C entry** — mark OLD.

**Decision rule for MEMORY**:
- **Keep**: neural metrics (β params, ρ, perm_p, ΔRDM cosines, voxel counts)
- **Mark OLD**: any P2a/P1/exact-count number from before 2026-05-15

---

## Phase 2 closure decision flagged

Under NEW labels:
- Current Option C (40, +26) sub-08 → P2a = 0.500 (worst zone cell)
- OLD LOCO-canonical (38, −14) sub-08 → P2a = 0.750 (top of zone)

**Phase 2 final filter for sub-08 needs re-evaluation** under NEW labels. Either:
1. Revert from Option C → LOCO-canonical (38, −14)
2. Or select another zone cell (24,−22), (28,−18), etc. (all P2a=0.750)

This is a user decision, flagged in `SCIENTIFIC_NARRATIVE_2026-05-16.md` CORRECTION NOTE.

---

## Action items (status as of 2026-05-16 23:00)

| # | Action | Status |
|---|---|---|
| 1 | Create `results/_archive/old_labels_pre_2026-05-16/` and README | ✅ done |
| 2 | `mv` 18 OLD-era result dirs into archive | ✅ done (all 18 moved) |
| 3 | Add top-of-file warning to `scripts/phase3_candidate_analysis_v2.py` | ✅ done |
| 4 | Append "[OLD-scheme; superseded]" markers to MEMORY entries | ✅ done (`feedback_label_scheme_cutoff.md` + headers in `project_phase2_closure.md`, `project_stim_lab_rendering.md`) |
| 5 | `git rm` + `rm` 49 OLD-scheme leaf scripts | ✅ done (37 git rm + 12 rm; `_deletion_manifest.md` written) |
| 6 | Restore label-independent JSON data accidentally caught in archive | ✅ done (`old_formula/` 87 JSONs, `axis_3way/` 7 JSONs, `CANDIDATE/tier2_v4ccc_srm_rdm/` 6 JSONs restored; viz remains archived) |
| 7 | Update CLAUDE.md §3 P2a numbers (currently OLD-scheme) | ⏳ pending — user decision (do we keep Option C or revert to LOCO-canonical?) |
| 8 | Resolve Phase 2 closure: Option C vs LOCO-canonical for sub-08 | ⏳ pending — manuscript decision |

## Final state (2026-05-16)

### Live `results/` directories
- `c3_relabel/` — NEW scheme single source of truth
- `fits/` — neural fit JSONs (label-independent)
- `old_formula/` — landscape JSONs restored (data only, viz archived)
- `axis_3way/` — Stockman landscape JSONs restored (data only)
- `CANDIDATE/tier2_v4ccc_srm_rdm/` — V4-CCC + SRM RDM landscape JSONs restored
- `fixedW_onlyTest/`, `phase3_candidates/` — empty, untouched
- `_archive/`, `_superseded/` — archives

### Archived
- 17 dirs (axis_3way shell removed as empty after JSON restore): `BAYESIAN_BEST/`, `LIT2Neural/`, `phase2_artifacts/`, `c3_proposals/`, `c3_canonical_search/`, `c3_candidate_search/`, `literature_applied/`, `literature_recovery/`, `principled_justification/`, `identifiability/`, `p2amax_neural_deep/`, `p2amax_neural_no_sign/`, `p2amax_neural_only_loss/`, `p2amax_unified_loss/`, `p2amax_updated/`, plus residual viz dirs `CANDIDATE/` (minus tier2 JSONs) and `old_formula/` (viz only, 48 PNG/PDF)

### Scripts deleted (49 total)
See `_archive/old_labels_pre_2026-05-16/_deletion_manifest.md`

### NEW chain verified operational
```python
from c3_relabel_both_subjects import p2a_corrected, SUB08_ORIG_NEW, SUB09_ORIG_NEW
p2a_corrected(38, -14, 150.0, SUB08_ORIG_NEW)  # → P2a=0.750, exact=2/8 ✓
p2a_corrected(6, -22, 16.0, SUB09_ORIG_NEW)    # → P2a=0.975, exact=7/8 ✓
```
