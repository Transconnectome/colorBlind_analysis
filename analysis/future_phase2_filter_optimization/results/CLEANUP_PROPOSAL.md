# results/ 폴더 정리 제안 (2026-05-13)

**원칙**: 삭제 실행 금지. 분류 + 이동 제안만. 사용자 승인 후 일괄 실행.

총 30개 폴더 → 4개 그룹으로 분류:

---

## 🟢 ACTIVE — keep at top level (8 folders, 41 MB)

현재 작업 중이거나 BEST/SUMMARY/논문 figure 참조 폴더.

| Folder | Size | Status |
|---|---|---|
| **`LIT2Neural/`** | 2.2 MB | 현재 BEST + 통합 수식 결과 + 모든 viz |
| `BAYESIAN_BEST/` | 800K | Prior BEST (α=0.3 Hierarchical Bayesian) |
| `CANDIDATE/` | 9.1 MB | demoted BEST + HC sanity landscape (specificity 참조) |
| `fits/` | 28 MB | phase_a_2component (sub-{08,09} V1/V4 LOCO anchor 출처) |
| `axis_3way/` | 7.2 MB | axis 비교 landscape (Stockman/CIELab) |
| `old_formula/` | 23 MB | V4-CCC wretrained landscape cached (반복 시뮬 회피) |
| `literature_recovery/` | 332K | 문헌 anchor recovery figure |
| `_archive/` | 4.5 MB | 기존 archive (그대로 유지) |

---

## 🟡 PHASE2-DOC — group under `phase2_artifacts/` (5 folders, 12 MB)

논문 figure/diagnostic 산출물이지만 매일 참조 안 함. 한 단계 deeper 폴더로 묶기.

```bash
mkdir -p results/phase2_artifacts
mv results/diagnostics      results/phase2_artifacts/
mv results/fixedW_onlyTest  results/phase2_artifacts/
mv results/cycles           results/phase2_artifacts/   # 11 MB, Cycle 9-14 통합 기록
mv results/inventory        results/phase2_artifacts/   # loss inventory CSV
mv results/older_cycles     results/phase2_artifacts/   # 2026-05-04 이전
```

---

## 🟠 SUPERSEDED — group under `_superseded/` (12 folders, 9 MB)

LIT2Neural/BAYESIAN_BEST에 의해 대체된 exploration 결과. 참조 가능성 낮음.

```bash
mkdir -p results/_superseded
mv results/axis_free_4d              results/_superseded/   # 4D refit, 미사용
mv results/brettel_reconciliation    results/_superseded/   # axis reconciliation, LIT2Neural에 통합
mv results/cardinal_axis_amplitude   results/_superseded/   # 2026-05-04 single use
mv results/candidates_p2             results/_superseded/   # P2a candidate ranking (구버전)
mv results/loss_alternatives         results/_superseded/   # loss exploration
mv results/loss_role_analysis        results/_superseded/   # loss 항 기여도, BAYESIAN_BEST에 통합
mv results/loss_simplification       results/_superseded/   # 단순화 시도, LIT2Neural에 통합
mv results/neural_only_deep          results/_superseded/   # LIT2Neural의 초기 sweep
mv results/neural_only_loss          results/_superseded/   # 동상
mv results/neural_primary            results/_superseded/   # LIT2Neural에 통합
mv results/p2a_landscape             results/_superseded/   # P2a-max 탐색 초기
mv results/p2a_loss_reverse          results/_superseded/   # P2a 역공학 시도
mv results/p2amax_F4                 results/_superseded/   # F4 prototype
mv results/p2amax_loss_search        results/_superseded/   # 빈 폴더 (0 B)
mv results/p2amax_new_loss           results/_superseded/   # 동상
mv results/phase3_candidates         results/_superseded/   # behavioral candidate ranking 구버전
mv results/sub09_protan_refit        results/_superseded/   # sub-09 axis 재피팅, axis_3way에 통합
```

`p2amax_loss_search`는 0 B (빈 폴더) — 단독 `rmdir` 가능:

```bash
rmdir results/p2amax_loss_search
```

---

## 🔴 PROPOSED DELETE — none (단계 1)

사용자 승인 전에는 어떤 폴더도 직접 삭제하지 않음. `_superseded/` 폴더는 3개월 후 재검토 (2026-08-13) → 그때까지 참조 없으면 `_archive/`로 압축 후 git LFS / 외부 백업 검토.

---

## 영향 요약

```
Before:  30 folders, 110 MB (results/ root)
After:   8 ACTIVE folders + phase2_artifacts/ + _superseded/ + _archive/
         ~Root에서 8 folders + 4 categorical containers = 12 entries (현재 30 → 60%↓)
```

`SUMMARY.md`의 file map는 ACTIVE 폴더만 참조하므로 경로 수정 불필요.

---

## 실행 스크립트 (사용자 승인 후)

```bash
#!/usr/bin/env bash
set -e
cd analysis/future_phase2_filter_optimization/results/

# Step 1: Create container dirs
mkdir -p phase2_artifacts _superseded

# Step 2: Move phase2-doc
mv diagnostics fixedW_onlyTest cycles inventory older_cycles phase2_artifacts/

# Step 3: Move superseded
mv axis_free_4d brettel_reconciliation cardinal_axis_amplitude \
   candidates_p2 loss_alternatives loss_role_analysis loss_simplification \
   neural_only_deep neural_only_loss neural_primary \
   p2a_landscape p2a_loss_reverse p2amax_F4 p2amax_new_loss \
   phase3_candidates sub09_protan_refit \
   _superseded/

# Step 4: Remove empty
rmdir p2amax_loss_search 2>/dev/null || echo "p2amax_loss_search not empty"

echo "Done. Active folders at top level:"
ls -d */
```

스크립트 파일: `results/cleanup_2026-05-13.sh` (미생성, 실행 승인 시 작성).

---

## 추가 권고

1. **SUMMARY.md 경로 검증**: 이동 후 SUMMARY.md 내부 grep `results/{moved_folder}` 패턴 확인 필요.
2. **Script 경로 영향**: 일부 script가 hard-coded 경로 (`results/phase3_candidates/...` 등) 사용 → grep 확인 후 update.
3. **CLAUDE.md 경로 영향**: `analysis/future_phase2_filter_optimization/CLAUDE.md` §3, §6, §2.5 등에서 폴더 경로 참조 → ACTIVE 폴더만 사용하므로 영향 없음.
