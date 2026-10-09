# Contributing (for agents: Claude chats, Codex, humans)

Follow these steps in order. They exist to prevent two agents building the same thing or editing the same files.

## 1. Before you start
- Open the [Project](https://github.com/users/CrazyShot/projects/1) and the Issues list. Search for your idea by keyword and by **workstream** label (`ws:*`).
- Read `FEATURE_INDEX.md` and the `INTEGRATION.md` of any feature that touches the same game code ("host touch points").
- If a feature already covers it: comment on its Issue. If it must be replaced, say so in the Issue and plan a new version that **supersedes** it.
- Do not start work that is *In Progress* under another Owner. If you depend on it, mark your Issue *Blocked* and name the dependency.

## 2. Claim the work
- Create (or take) **one Issue** using the *Feature task* form. Add it to the Project.
- Set Project fields: **Status = In Progress**, **Owner** (your chat/agent name), **Workstream**, **Priority**, **Feature path**, **Target game revision**, **Dependencies**.

## 3. Work in the right place, on a dedicated branch
- Branch: `feature/<workstream>/<feature-slug>` (fixes: `fix/<feature-slug>-<short>`).
- Folder: `workstreams/<workstream>/<feature-slug>/` — copy `templates/feature/`. **Only edit your own feature folder.** Need a change in someone else's feature? Open an Issue; do not edit it.
- A feature is a self-contained block marked `FEATURE: <NAME> START/END` with a unique id/version (e.g. `UNIT-INFO-PANEL-1.1.0`). Prefer **wrapping** host functions at load time over editing them. If a host edit is unavoidable keep it minimal, guarded, and list it exactly in `INTEGRATION.md`.
- Keep source in `src/`, tests in `tests/`. Keep files small; no generated bulk data unless it is a documented fixture.

## 4. Do not commit
- the complete game `index.html` or any full-game copy/backup/zip;
- credentials, tokens, keys, `.env` files, private URLs;
- binary art that is not meant to be public (embed it via a script and keep the images private, see `vampire-asset-test`).
Run `tools/check-repo.sh` before every commit.

## 5. Test and document
- Run your tests against a real game build (they run the game in a headless browser). Record **what you actually ran and the real results** in `INTEGRATION.md` — including failures and known limitations. Never claim an untested thing works.
- Fill `README.md` (what it does) and `INTEGRATION.md` (target revision, dependencies, host touch points, step-by-step integration, wrapper/ordering notes, test results, limitations).

## 6. Pull request
- Open a PR from your branch to `main` using the PR template. Link the Issue (`Closes #N` only when the work is complete; otherwise `Refs #N`).
- Update `FEATURE_INDEX.md` if you added/renamed a feature.

## 7. Update the Issue and the Project
- Project **Status**: *In Progress* → *Ready for Integration* when the PR is merged and tests are documented. Fill **Test evidence** (short string + link to the `INTEGRATION.md` section).
- Never set *Integrating*, *Integrated* or *Verified* yourself unless you are the main-game integrator (see `FEATURE_WORKFLOW.md`).
- If you find a problem while integrating, file an *Integration problem* Issue linked to the feature and set the feature *Blocked* if it cannot proceed.
