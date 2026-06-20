---
name: redteam-project
description: "현재 프로젝트 산출물/주장/분석을 Nature/NeurIPS reviewer #2 관점에서 공격적으로 비판하고 중화 실험 제안."
recommended-model: opus
---

> **Model hint**: Use `model: "opus"` when spawning subagents for this skill (deep reasoning task: critical analysis + neutralization experiments).

Inputs to read (project-local):
- .Codex/memory/project_brief.md
- .Codex/memory/repo_policy.md

Procedure:
1) Collect evidence pointers (read-only):
   - recent commits (git log)
   - key result files (list a few)
   - any draft text/figures if present
2) Call redteam-project agent.
3) Produce a report at results/redteam/YYYY-MM-DD.md:
   - Top 5 criticisms
   - fatal vs addressable
   - 1 concrete neutralization experiment/analysis each
   - level of effort: 2h / 2d / 2w

Rules:
- Only use provided sources / available repo artifacts.
- Be harsh, technical, precise.
