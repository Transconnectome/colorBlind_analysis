# Phase 3 Filter-Validation Pipeline

Autonomous SLURM chain for sub-08/09 **ses-02** (filter-applied) scans.

## What it does

```
01_preprocess_filter.sbatch  (array, sub-08 + sub-09)
    method3_header_mi registration
        mri_coreg (BOLD->T1w) + FLIRT/FNIRT (T1w->MNI)
    generate_confounds.py
    roi_pipeline_selected_1202used.py    -> V1/V2/V3/V4 masks
                |
                |  --dependency=afterok
                v
02_downstream_filter.sbatch  (sequential)
    run_full_dataset_C010.py             -> amplitudes_procrustes.npy
    project_filtered_session.py          -> SRM RDM vs frozen HC W
    phase1_cross_subject_loso.py         -> LORO + LOCO per ROI
    generate_phase_summary.py            -> COMPREHENSIVE_SUMMARY_*.txt
```

HC reference is **frozen**: existing N=7 HC amplitudes and SRM weights are
reused unchanged. The pipeline only processes the two CVD subjects' new ses-02
data and projects them onto the existing reference.

## Files

| File | Purpose |
|---|---|
| `01_preprocess_filter.sbatch` | array job (1-2) per subject: registration + confounds + ROI |
| `02_downstream_filter.sbatch` | sequential: amplitudes -> SRM RDM -> LORO/LOCO -> summary |
| `submit_pipeline.sh` | submits both with `afterok` dependency |
| `logs/` | stdout/stderr from SLURM |

## Usage on server

```bash
ssh haba6030@node3
cd /scratch/connectome/haba6030/colorBlind
bash analysis/phase6_behavioral_analysis/comprehensive_pipeline/submit_pipeline.sh
```

## Prerequisites — `--session` flag in 4 scripts

These existing scripts iterate subjects by hardcoded ID lists and accept no
session arg. **Patch them before submitting**, or the pipeline will silently
process ses-01 data:

| Script | Required change |
|---|---|
| `analysis/phase0_preprocessing/scripts/generate_confounds.py` | argparse: `--subject --session --dataset`; emit outputs under `sub-{ID}/ses-{S}/` |
| `analysis/phase1_procrustes_decoding/roi_pipeline_selected_1202used.py` | accept `--session`; reads BIDS from `sub-{ID}/ses-{S}/func/`; writes masks under ses-{S} namespace |
| `analysis/phase1_procrustes_decoding/run_full_dataset_C010.py` | accept `--subject --session --dataset`; writes amplitudes under `derivatives/full_dataset_C010/sub-{ID}/ses-{S}/{ROI}/` |
| `analysis/phase3_decoder_comparing/phase1_cross_subject_loso.py` | accept `--session`; amplitudes glob includes `ses-{S}` segment |

For the frozen-HC reuse, `project_filtered_session.py` expects the HC SRM
weights and reference RDM under `results/srm_loo_consistent/{ROI}/`. If the
filenames written by `rerun_loo_consistent.py` differ, extend the
`load_hc_w` / `load_hc_rdm` candidate lists in `project_filtered_session.py`.

## Smoke run (recommended before real ses-02 data)

### A. Static checks (1 min)

```bash
# CRLF check
file analysis/phase6_behavioral_analysis/comprehensive_pipeline/*.sbatch \
     analysis/phase6_behavioral_analysis/comprehensive_pipeline/submit_pipeline.sh
# expect: 'ASCII text'  (no 'with CRLF line terminators')

# sbatch lint
sbatch --test-only analysis/phase6_behavioral_analysis/comprehensive_pipeline/01_preprocess_filter.sbatch
sbatch --test-only analysis/phase6_behavioral_analysis/comprehensive_pipeline/02_downstream_filter.sbatch
# expect 'Job N would be submitted' for each
```

### B. Env activation check (1 min)

```bash
srun --nodelist=node2 --qos=shared --time=00:05:00 --pty bash -lc \
  'conda activate nilearn && python -c "import nilearn, numpy, scipy, sklearn; print(nilearn.__version__)"'
```

### C. Dry-run on existing ses-01 data (~1 h)

Temporarily edit both sbatch files: set `SESSION=01`, `SUBJECTS=(08)`, and
change the SRM/LOSO output dirs to a throwaway `_SMOKE` suffix. Then submit:

```bash
bash analysis/phase6_behavioral_analysis/comprehensive_pipeline/submit_pipeline.sh
squeue -u $USER
tail -f analysis/phase6_behavioral_analysis/comprehensive_pipeline/logs/*.out
```

Expected end state:
- `${OUTPUT_DIR}/sub-08/ses-01/func/sub-08_ses-01_task-rsvp_run-*_space-MNI*.nii.gz`
- `derivatives/full_dataset_C010/sub-08/ses-01/V4/amplitudes_procrustes.npy`
- `results/srm_filter_validation_*_SMOKE/srm_rdm_filter_validation.json`
- `analysis/phase3_decoder_comparing/results/filter_validation_*_SMOKE/`
- no `Invalid qos`, `unrecognized arguments`, or `mpirun: not found`

Clean up + revert `SESSION=02, SUBJECTS=(08 09)`:

```bash
rm -rf results/srm_filter_validation_*_SMOKE
rm -rf analysis/phase3_decoder_comparing/results/filter_validation_*_SMOKE
```

## Outputs (real run)

```
${OUTPUT_DIR}/sub-08/ses-02/                                # preprocessed BOLD in MNI
${OUTPUT_DIR}/sub-09/ses-02/
derivatives/full_dataset_C010/sub-08/ses-02/V4/amplitudes_procrustes.npy
results/srm_filter_validation_${TIMESTAMP}/
    srm_rdm_filter_validation.json
    sub-{08,09}_ses-02_{V1,V2,V3,V4}_S.npy
    sub-{08,09}_ses-02_{V1,V2,V3,V4}_rdm.npy
analysis/phase3_decoder_comparing/results/filter_validation_${TIMESTAMP}/
analysis/comprehensive/results/COMPREHENSIVE_SUMMARY_${TIMESTAMP}.txt
```

## Gotchas

- **CRLF**: never edit these files in a CRLF-emitting tool. The Phase A `file`
  check catches it.
- **`--qos=shared`**: matches the working `run_method3_header_mi.sbatch`. Do
  NOT remove without re-testing.
- **`--chdir`** is absolute (`/scratch/connectome/haba6030/colorBlind`) so log
  paths resolve regardless of where `sbatch` is invoked.
- **ses-02 anat**: if T1w wasn't re-acquired, `01_preprocess_filter.sbatch`
  falls back to `ses-01/anat` automatically; warning printed in log.
- **MNI template missing**: pipeline aborts in Step 3. Verify
  `templates/MNI152NLin2009cAsym_res-2_T1_brain.nii.gz` exists on server.
- **BrainIAK**: `project_filtered_session.py` uses pure numpy/scipy, so bare
  `python` is fine. If you swap in a BrainIAK-backed projection, prefix with
  `mpirun -np 1`.
