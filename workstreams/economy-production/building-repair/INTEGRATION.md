# Integration — Building repair + Repair All

## Target game revision
Prototype "Emberfall — RTS Map Prototype" (single-file index.html) as supplied 2026-10-08; main-repo commit: **to be filled in by the integrator**

## Dependencies
Soft: `FEATURE_CTRLGROUPS_V2.selectedBuildings()` (falls back to the host's single `SB`). Insert last (after DOUBLE-CLICK-SELECT).

## Host touch points
Wraps `stepSim` (repair tick), `uiUpdate` (buttons), `drawWorld` (green "+" / amber "!" marker). Reads `B E G COST RESN BT SB X Y g dpr toast`; DOM `#pn #tr #bar`.
**DOM ids added:** `repair-btn`, `repair-note`, `repair-all`. (The host already uses `id="rp"` for another element — the first version collided with it; do **not** reuse `rp`.)
**Repair All is deliberately NOT a child of `#bar`:** the host loops over `bar.children` and reads `dataset.k`, so a foreign child would break it every frame. It floats above the bar, positioned from the bar's measured rectangle.
No host edits.

## Integration steps
Insert `src/FEATURE_BUILDING-REPAIR.html` before `</body>` (or use the patcher in `../../rts-controls-qol/control-groups-v2/src/`).

## Test results (Playwright (Python), headless Chromium, real input)
- `test_repair.py`: **30/30** — damage → Repair → full HP (gradual: ≥8 distinct intermediate values, no big jumps), cost ≈ 40% × HP fraction, pause freezes repair, manual stop, damage during repair, destroyed during repair, removed-from-world during repair, under construction refused then allowed after completion, no resources / running dry, multi-building.
- `test_followup_multi_hp_and_repair.py`: **51/51**, three consecutive runs — enemy at 14/10.5/10/9.9/6/2 tiles; per-building blocking; enemy approaching mid-repair pauses (HP frozen, nothing charged, toast, still active), resumes after the clear delay; manual stop while paused; Repair All over a settlement with every state (eligible / already repairing / full / under construction / destroyed / blocked by enemy) with correct counts; nothing healed or charged at the click; healing gradual; second Repair All finishes the previously blocked building; no resources → starts nothing and says why; shared shortage → only 2 of 3 start; running dry mid-repair stops with one toast and never goes negative.

## Limitations / open questions
See `README.md`. The test pins the day phase (`G.t`) so a real wave does not start mid-test.
