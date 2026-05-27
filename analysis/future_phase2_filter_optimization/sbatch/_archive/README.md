# sbatch/_archive/ — Stale SLURM job scripts

22 .sbatch files moved 2026-05-28 (Phase B'). All call Python scripts that
are either (a) archived under `scripts/_archive_pre_closure/`,
(b) archived under `scripts/<subdir>/_archive/`, or (c) never existed at
the cited paths (e.g., `scripts/cycle_filter_refinement/*`,
`scripts/cycle_loss_redesign/*`, `scripts/preimage_filter_search.py`).

None of these jobs targets a closure-active script. They are retained for
audit of historical SLURM runs only.

## Files and the script they call

(See `grep -hoE "scripts/[^ ]+\.py" *.sbatch` for full list.)

Closure-active jobs would call: `scripts/s10a_precondition.py`,
`scripts/s10b_v6_pca_rdm.py`, `scripts/s10b_v6_srm_rdm.py`,
`scripts/s10b_v6_srm_disparity.py`, `scripts/s17_hc_loo.py`,
`scripts/cycle6b_extended_raw_weight.py`, `scripts/s13_round3.py` — but no
sbatch file currently in this directory targets any of them, so a new
closure-targeted sbatch is needed before re-running Phase B v6 on the
server.

Per CLAUDE.md SLURM section: SLURM submissions require `--chdir=<abs>`,
no `--partition`/`--qos` flags, `--no-requeue` for validation jobs.
