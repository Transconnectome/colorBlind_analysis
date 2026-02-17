---
name: daily-checkin
description: "논문 요약 파일 기반 daily summary 생성. Pending Validations에서 내일 할 일 추출, Phase별 진행률 계산, git diff로 오늘 변경분 감지. results/daily/YYYY-MM-DD.md로 저장."
---

Inputs to read (project-local):
- analysis/METHODS_RESULTS_SUMMARY_FOR_PAPER.md  (primary source)
- .claude/memory/project_brief.md
- .claude/memory/repo_policy.md

Procedure:
1) Read `analysis/METHODS_RESULTS_SUMMARY_FOR_PAPER.md` — this is the single source of truth.
2) Parse **Pending Validations** table → extract Tomorrow's Tasks (High priority first, top 3).
3) Parse **Validation Status** checkboxes in each Phase → compute completion rate (e.g., "Phase 1: 6/6 (100%)").
4) Run `git diff HEAD~1 -- analysis/METHODS_RESULTS_SUMMARY_FOR_PAPER.md` → extract today's changes (added lines).
5) Parse **Key Findings Summary** → include as Key Results.
6) Parse **Limitations & Caveats** → flag items containing "pending", "not yet", "needed" as Blockers.
7) Write daily log at `results/daily/YYYY-MM-DD.md` using this structure:

```markdown
# Daily Summary — YYYY-MM-DD
## Project: colorblind
**Branch:** main | **Source:** METHODS_RESULTS_SUMMARY_FOR_PAPER.md

## Today's Progress
- [git diff additions from summary file]

## Key Results
1. [from Key Findings Summary]

## Blockers
- [High priority pending validations + limitation items with "pending"/"not yet"]

## Tomorrow's Tasks
1. [High] Task name (Phase N)
2. [High] Task name (Phase N)
3. [Medium] Task name (Phase N)

## Pipeline Status
- Phase 1: X/Y validations complete (Z%)
- Phase 2: X/Y validations complete (Z%)
- Pending validations: N (High: H, Medium: M)
```

8) Notion auto-sync follows (handled by run_daily_pipeline.sh).

Automation:
- `python ~/research_ops/generate_project_daily.py --date YYYY-MM-DD` produces the same output programmatically.
- The pipeline (`run_daily_pipeline.sh --summary`) calls this script automatically.

Rules:
- Do not propose deletions.
- If summary file has no changes today, write "No changes to summary file today" under Today's Progress and focus on Tomorrow's Tasks.
- If summary file does not exist, fall back to git-based summary (git log, diff, status).
