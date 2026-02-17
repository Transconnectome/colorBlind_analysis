# Repo Hygiene Policy

## Non-negotiables
- NEVER auto-delete files.
- Propose changes as patches / diffs first.
- Preserve: raw data, essential results, IRB-sensitive materials.

## Artifact rules
- Large outputs go to: results/ or artifacts/ (not tracked by git)
- Logs/checkpoints: ignore by default

## Allowed cleanup actions
- Add / refine .gitignore rules
- Identify duplicate/obsolete scripts
- Propose archive moves (NOT execute)

## Forbidden
- rm -rf, bulk deletion, destructive moves without explicit approval
