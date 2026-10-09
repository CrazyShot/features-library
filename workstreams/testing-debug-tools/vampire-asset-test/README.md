# Vampire asset test (sprite integration + debug spawn panel)

| Field | Value |
|---|---|
| Feature ID | `VAMPIRE-ASSET-TEST-1.0.0` |
| Workstream | `testing-debug-tools` |
| Issue / Project | [#6](https://github.com/CrazyShot/features-library/issues/6) · status is tracked in the [Project](https://github.com/users/CrazyShot/projects/1) |
| Target game revision | Prototype "Emberfall — RTS Map Prototype" (single-file index.html) as supplied 2026-10-08; main-repo commit: **to be filled in by the integrator** |
| Depends on | none |

## What it does
Draws the user's vampire art (front + back view, no animation) as the visual of the **existing** enemy, plus a debug panel (Stand, Front+Back, Move, Chase, Attack, Group ×6, Clear) that spawns real enemy objects. Movement, targeting, combat, fog and tree-depth are the game's own code. Front/back is chosen from the screen heading (waypoint) with a dead-zone; sideways keeps the previous view. Modes: `all` / `tagged` / `off` (original art).

## Files
- `src/FEATURE_VAMPIRE-ASSET-TEST-1.0.0.template.html` — the feature block with the two sprite data-URIs **replaced by placeholders**
- `src/embed_sprites.py` — re-embeds your private PNGs: `python3 src/embed_sprites.py front.png back.png out.html`
- `tests/`

> **The sprite PNGs are not in this public repository.** The committed block is therefore a *template*; run `embed_sprites.py` with the private PNGs to produce the real block.

## Limitations
Only front and back views; no walk/attack animation, no left/right mirroring; at far zoom with "Unrestricted zoom" the old enemy blob is drawn under the sprite; the back sprite shows a red vest from behind (check that this is intended).
