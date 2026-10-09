# Feature workflow

## Statuses (Project field **Status**)

| Status | Meaning | Who sets it |
|---|---|---|
| **Backlog** | Idea/task recorded, nobody working on it | anyone |
| **In Progress** | An agent owns it and is building/testing it | the feature's Owner |
| **Blocked** | Cannot continue; the Issue says what it waits for | Owner or integrator |
| **Ready for Integration** | PR merged here, tests documented, waiting for the main-game integrator | Owner |
| **Integrating** | The integrator is applying it to the private main game | **integrator only** |
| **Integrated** | Applied in the main game (record the **Integration commit**) | **integrator only** |
| **Verified** | Passed testing **in the main game** | **integrator only**, only after real testing there |
| **Superseded** | Replaced by a newer feature/version (link it in the Issue) | Owner or integrator |

GitHub cannot restrict a single Project field by person on a user-owned Project, so the three integrator-only statuses are a **rule enforced by convention and review**: agents must not set them.

## Project fields

Status · **Owner** (agent/chat name) · **Workstream** · **Priority** (P0 Critical, P1 High, P2 Normal, P3 Low) · **Feature path** · **Target game revision** · **Dependencies** · **Test evidence** · **Integration commit**.
Individual tasks are GitHub **Issues** linked to the Project; the Project is the source of truth for status.

## Feature folder

```
workstreams/<workstream>/<feature-slug>/
  README.md        what it does, id/version, workstream, links (Issue, Project), files, limitations
  INTEGRATION.md   target game revision, dependencies, host touch points, steps, ordering, test results, limitations
  src/             FEATURE_*.html blocks, patch scripts, fixtures
  tests/           automated tests (headless browser) + how to run them
```
Start from `templates/feature/`. Slugs are lowercase-kebab and descriptive (`building-repair`, not `repair2`).

## Naming and versioning
- Block markers: `FEATURE: <NAME> START (id: <NAME>-<major>.<minor>.<patch>)` … `END`.
- Bump the version when behaviour changes; a replacement that cannot coexist **supersedes** the old one (keep the old folder, mark the Issue *Superseded*).

## Avoiding conflicts and duplicates
- One Owner per Issue; check Status/Owner before starting.
- List every **host touch point** (function wrapped, host line edited, DOM id used, global read) in `INTEGRATION.md`. Before starting, grep the other features for the same touch points and note order dependencies.
- Prefer wrappers (`window.fn = function(...){ …; return orig(...) }`) and unique DOM ids (`#<feature>-…`). The host's own ids may collide — check before choosing one.

## Target game revision
Say which build the feature was tested on (commit hash of the main game if known, otherwise the build name/date). The integrator re-tests on the current main game; anchors that moved are reported in an *Integration problem* Issue.

## Test evidence
Record the command, the build used, the pass/fail counts and any known-failing checks with the reason. Example:
`t1 control groups + keys: 35/35 (headless Chromium, software rendering, real keyboard/mouse input)`.

## Integration protocol (main-game integrator)
1. Set *Integrating*; read the feature's `INTEGRATION.md`; apply on a branch of the main game.
2. Re-run the feature tests on the main-game build; run the main game's own regression.
3. Merge; set *Integrated* and fill **Integration commit**.
4. After the feature has passed testing in the main game, set *Verified*.
