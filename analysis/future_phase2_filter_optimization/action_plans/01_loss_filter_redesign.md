# Action Plan 01 — Loss / Filter 재설계

> 목적: 현 LOCO loss가 vuln rank에 과의존 → (a) 취약 방향 정보 소실, (b) HC false-positive 100% 문제. 취약 수준 + 방향(어느 색이 어느 방향으로 왜곡)을 동시에 잡고 HC 특이성을 회복하는 loss·필터 구조를 탐색한다.
>
> 진행 규칙: 4단계 cycle × 3회 — (1) 현황·문제·원인 분석, (2) 가설/실험 계획, (3) 제작 → smoke → main, (4) 비판 검토 후 다음 cycle. 본 문서는 시간순 로그.

---

## Cycle 1 — 시작 시점: 2026-04-29

(작성 진행 중)
