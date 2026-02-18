---
name: repo-hygiene
description: "중복 코드/대형 산출물/추적 불필요 파일을 찾아 .gitignore/구조 개선을 제안 (삭제 실행 금지)."
recommended-model: haiku
---

> **Model hint**: Use `model: "haiku"` when spawning subagents for this skill (mechanical task: file scanning + gitignore suggestions).

Inputs to read (project-local):
- .claude/memory/repo_policy.md

Procedure (safe):
1) Identify large files/dirs (suggest commands):
   - du -sh * | sort -h
   - find . -maxdepth 3 -type f -size +200M
2) Identify common junk paths to ignore:
   - __pycache__, .pytest_cache, logs/, checkpoints/, results/, artifacts/
3) Propose a patch:
   - .gitignore additions
   - README updates (directory map, how to reproduce)
4) Output a "Cleanup proposal" with:
   - what to ignore
   - what to archive (proposal only)
   - what to keep

Rules:
- No destructive actions.
- Prefer reversible changes (gitignore, docs).
