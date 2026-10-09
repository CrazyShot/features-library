# features-library

Shared, public library of **modular features for The Bastion** (a dark-fantasy survival RTS: dwarves defending against vampires).
Several Claude chats and Codex work here in parallel. Every feature is a self-contained module that the **main-game integrator** merges into the private main-game repository.

> **The private main-game repository is the authoritative playable version.** This library never contains the full game.

## Hard rules

1. **Never commit** the complete game `index.html`, full-game backups/zips, credentials, tokens or secrets. `tools/check-repo.sh` and the `repo-guard` workflow reject them.
2. **Do not modify the main game from here.** Deliver a feature module plus integration instructions; the integrator applies it.
3. **The [GitHub Project](https://github.com/users/CrazyShot/projects/1) is the source of truth for task status.** Do not duplicate status in files.
4. **One feature = one folder = one Issue = one branch = one pull request.**
5. Only the **main-game integrator** may set a feature to *Integrated*, and *Verified* only after it passed testing **in the main game**.

## Start here (agents)

1. Read `CONTRIBUTING.md` (the step-by-step protocol) and `FEATURE_WORKFLOW.md` (statuses, fields, folder template).
2. Check the [Project](https://github.com/users/CrazyShot/projects/1), the open [Issues](https://github.com/CrazyShot/features-library/issues) and `FEATURE_INDEX.md` for an existing or overlapping feature **before** starting. Do not duplicate; extend or supersede explicitly.
3. Claim the Issue (status *In Progress*, set *Owner*), create the branch `feature/<workstream>/<feature-slug>`, work only in `workstreams/<workstream>/<feature-slug>/`.
4. Test, document results in the feature's `INTEGRATION.md`, open a PR, update the Issue and the Project.

## Layout

```
README.md  CONTRIBUTING.md  FEATURE_WORKFLOW.md  FEATURE_INDEX.md
.github/            issue forms, PR template, repo-guard workflow
templates/feature/  README.md + INTEGRATION.md skeletons for a new feature
tools/              check-repo.sh (forbidden-file / secret scan)
workstreams/
  combat-ai/  rts-controls-qol/  waves-survival/  environment-visuals/  testing-debug-tools/
  economy-production/  research-progression/  save-load-session/  map-data-integration/  performance-rendering/
    <feature-slug>/  README.md  INTEGRATION.md  src/  tests/
```

Features are organised **by type of work (workstream), not by agent**. See each workstream's `README.md` for its scope.

## Status model

`Backlog` → `In Progress` ⇄ `Blocked` → `Ready for Integration` → `Integrating` → `Integrated` → `Verified`; `Superseded` for replaced features. Details and who may set each status: `FEATURE_WORKFLOW.md`.
