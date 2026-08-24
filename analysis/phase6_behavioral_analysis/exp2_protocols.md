# exp2 protocols — HYPO forward-prediction, self-tune, cross-swap

**Status (2026-05-30)**: Planning doc for exp2 under Path A (α'').

## 1. HYPO-pair forward-prediction protocol — selection-bias-free

### Why this matters
Reviewer #2 scenario: *"You defined HYPO pairs from Phase 1-2 LOCO data and then tested the same pairs in exp2 → circular."* This protocol avoids that by deriving HYPO pairs from the **forward prediction of the fitted 2-comp model**, not from data-driven selection.

### Train / Test split
- **Train**: Phase 1-2 exp1 data → fit (Δλ, g) per subject (2-comp model params: retinal cone shift + cortical rotation gain)
- **Test**: exp2 data → validate that (Δλ, g)-predicted HYPO pairs show selective improvement under Optimal vs Window

The split is clean because Phase 1-2 only outputs *parameter estimates* (Δλ, g). The HYPO pair *identification* comes from the model forward step, not from inspecting Phase 1-2 pair-level distances.

### Algorithm

```
Input:  subject's (Δλ_sub, g_sub) from Phase 1-2 best-fit
        8 hue Lab coords (L*=75, chroma=40 ring) — same as exp1/exp2 stimuli

Step 1: Forward 2-comp simulation for each hue h_i (i=1..8):
        rg_ret_i  = machado_shifted_hue(h_i, Δλ_sub, type=protan/deutan)  # retinal Δλ shift
        rg'_i     = rg_base_i + (1 + g_sub) * (rg_ret_i - rg_base_i)       # cortical gain
        → CVD-perceived Lab coord: lab_cvd_i = (L*, rg'_i, yb_i)

Step 2: Pairwise distance computation, all 28 pairs (i, j) with i<j:
        d_HC(i,j)   = ||h_i - h_j||_Lab                                    # HC perception
        d_CVD(i,j)  = ||lab_cvd_i - lab_cvd_j||_Lab                       # CVD perception per model

Step 3: Compression ratio per pair:
        CR(i,j) = d_HC(i,j) / d_CVD(i,j)
        # CR > 1 → CVD compresses this pair (HYPO candidate)
        # CR ≈ 1 → pair preserved (HC-equivalent)

Step 4: Rank pairs by CR (descending).
        HYPO_pairs            = top k=5 pairs (CR highest)
        HC_equivalent_pairs   = bottom k=5 pairs (CR ≈ 1)

Output: HYPO_pairs[sub], HC_equivalent_pairs[sub] (per-subject lists of pair indices)
        Saved BEFORE exp2 data analysis → pre-registered.
```

### Pre-registration
Before any exp2 data analysis:
- Compute HYPO / HC-equivalent lists per subject
- Save to `results/hypo_prediction/sub-{ID}_hypo_pairs.json` with timestamp
- Commit to git with tag `exp2_hypo_preregister`
- Document the (Δλ, g) values used (from `phase5_filter_optimization/results/...`)

### Validation hypothesis (analysis B)
```
H1_mech:  RDM_dist(HYPO, Optimal) − RDM_dist(HYPO, Window) >
          RDM_dist(HC_eq, Optimal) − RDM_dist(HC_eq, Window)

Test: paired contrast of within-subject pair-set means.
Per-subject test (N=2 underpowered for group) → report individual stats + Bayes factor.
```

### Robustness checks
- Use multiple k values (k=3, 5, 7) → report consistency
- Use threshold-based instead of top-k (e.g., CR > 1.3) → sensitivity
- Compare with random pair selection → null distribution

---

## 2. Self-tune (macOS color filter intensity) protocol

### Hardware
- Stimulus Mac with macOS 26.X.Y (record exact build)
- External monitor color-calibrated (target: match MRI projector when possible)
- Lighting: dim mesopic similar to scanner environment

### Software
- PsychoPy script `selftune_macos.py` (TODO write):
  - Displays 8 hues in ring arrangement at full chroma=40, L*=75
  - Floating overlay with instructions
  - Background: macOS Color Filter ON (type = subject's deficiency: Deuteranopia or Protanopia)

### Procedure
1. Pre-condition (5 min): subject confirms personal CVD type matches macOS filter type (deutan → Deuteranopia setting, protan → Protanopia setting). Type fixed by clinical diagnosis (sub-08 deutan, sub-09 protan).
2. Open System Settings > Accessibility > Display > Color Filters → enable filter type. Subject adjusts intensity slider (0–100%) freely while watching the 8-hue display.
3. Instruction (verbal + on-screen): *"Adjust the intensity slider until the 8 colors look most distinct from each other. There is no right answer. When you are satisfied, press SPACE to confirm."*
4. Subject explores for 30–60 s.
5. Confirm with SPACE → script reads slider value via:
   ```bash
   defaults read com.apple.universalaccess differentiateColor
   # or: defaults read com.apple.MediaAccessibility __Color__-MADisplayFilterCategoryUserIntensity
   ```
6. Screenshot of Settings panel saved.
7. Re-confirmation: subject does a 2-AFC discrimination on 5 random hue pairs at selected intensity → if accuracy < chance (failsafe), repeat tuning.

### Output (`config_sub-{ID}.json`)
```json
{
  "subject": "sub-08",
  "deficiency_type": "Deuteranopia",
  "macos_version": "26.X.Y (build XXX)",
  "color_filter_intensity": 0.62,
  "selftune_timestamp": "2026-MM-DD HH:MM:SS",
  "settings_screenshot": "selftune/sub-08_settings.png",
  "failsafe_2afc_accuracy": 0.78,
  "operator_check": "passed"
}
```

### Pre-scan use
On scan day:
- Experimenter opens Settings, sets intensity to recorded value (slider increments via arrow keys for precision).
- Verifies screenshot matches.
- Toggles ON/OFF per `run_filter_assignment.csv` during inter-run rest.

---

## 3. Cross-subject filter swap (behavioral session)

### Design
2 (filter source: own / other CVD subject's optimal) × 2 (CVD subject: sub-08 / sub-09) = 2×2 within-subject interaction.

Plus reference conditions: no filter (raw stimuli baseline) and macOS Window (deployed standard reference).

### Conditions (4 total)
| Code | Stimuli rendered with |
|---|---|
| **NF** | no filter (raw Lab) |
| **MAC** | macOS color filter (subject's own intensity from self-tune) |
| **OWN** | subject's own Phase 2 optimal δθ filter via PsychoPy |
| **OTH** | the OTHER CVD subject's optimal δθ filter via PsychoPy |

NF and MAC give ecological reference points; OWN vs OTH gives the personalization-specificity test.

### Task
Two-alternative forced choice (2-AFC) hue pair discrimination:
- Trial: two flickering rings (8 colors used as in scanner, 0.8s drift)
- Question: "Are the two rings the same hue or different?" (or odd-one-out variant)
- Subject responds via keypress
- Adaptive staircase on hue distance → estimate JND threshold per pair per condition

### Block structure
- 4 conditions × 28 pairs × 8 trials/pair = 896 trials per subject
- Split into 8 blocks (~7 min each), 2 blocks per condition
- Counterbalance condition order across blocks (Latin square)
- Total session ~70 min + breaks

### Pre-registered analyses
**Personalization test** (primary):
```
H1_pers: JND_own[sub-08] < JND_oth[sub-08]
         AND
         JND_own[sub-09] < JND_oth[sub-09]
         (both within-subject paired tests)

→ 2×2 interaction: filter_source × subject. Significant interaction with own < oth in both subjects = personalization-specific.
```

**Deployment test** (secondary):
```
H1_dep:  JND_own < JND_mac  per subject
         (paired t-test on per-pair JND)
```

**HYPO-pair restriction** (mechanism strengthener):
- Restrict analysis to HYPO pairs only (from Section 1 forward prediction)
- Predicts: own filter improvement over mac concentrates on HYPO pairs

### Output
- `results/cross_swap/sub-{ID}_jnd_4conditions.csv` (per-trial level)
- `results/cross_swap/summary.json` (per-subject JND per condition per pair)
- Analysis notebook `cross_swap_analysis.ipynb`

### Practical notes
- Apply OTH filter: sub-08 session uses sub-09's δθ vector (and vice versa) — both rendered via the SAME `filters_exp2.py` PsychoPy path → pipeline confound absent between OWN and OTH
- Subject can do session post-scan (same day or different day) — order does not affect within-session validity
- Inter-rater reliability not needed (within-subject design)
- Time budget: 1 visit ~90 min including consent/breaks
