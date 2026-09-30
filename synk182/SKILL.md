---
name: synk182
description: >-
  Synk182 (Synk): keeps two copies of a project in agreement without losing
  work - the user's copy and a working copy such as a sandbox or upload, a
  mounted or cloud-synced folder, a git worktree, another machine's copy, or a
  deployed copy of something developed elsewhere. Compares every file across
  the full similarity spectrum from identical to superset, proposes each change
  with its evidence, backs up into ARCHIVE/ before writing, verifies every
  write six ways and rolls back on failure. Only an exact hash match skips
  review. Use whenever the user says synk, s182, synk182 or synk it; asks to
  sync, mirror, push or pull files between two folders or machines; asks which
  copy is newer; says files are different, out of date or missing on one side;
  or when docs/PULSE.json records drift. Not
  for redundancy inside one copy (a consolidation tool), git merges or the
  rules of working in a repo (git, a repo-rules skill), or what two versions
  can do rather than what their files hold (a verification tool).
license: Freeware
metadata:
  version: "3.3"
  updated: "2026-09-30"
---

# Synk182 — The Symphonous Strategist
 Formerly **nothing**
> *Formally a link between sink, and sync. "Who thinks this shi don't stink? let that sync in" signed- A. Blinken.*

**Bidirectional file sync with surgical precision, paranoid safety, and adaptive depth that adjusts mid-operation.**

Works in any agent that reads a `SKILL.md`, on its own; the engine needs only Python 3.10 or later.

## Three Fixed Rules

1. Mandatory review for >60% similar (only 100% hash match skips review)
2. 60% threshold for intelligent merge
3. >100% superset/subset = ultra-careful handling, maximum scrutiny

## When the Request Is Ambiguous

| Level | Phrases | Action |
|-------|---------|--------|
| 🟢 Immediate | "sync my project/files", "synchronize", "keep in sync" | Activate |
| 🟡 Confirm | "update my project files" | Clarify: Synk or direct edits? |
| 🔴 Clarify | "files are different", "don't see my file" | Offer Synk |
| ❌ Not Synk | Create/edit single files, move within dir, redundancy inside one copy (a consolidation tool), branch merges (git), repo and worktree rules (your repository's own rules), what a version can do rather than what its files hold (a verification tool) | — |

**Name the two copies first.** Say which is the user's copy (authority) and which is the working copy, in the user's words. Most sync damage starts with the two being swapped.

## Similarity Spectrum

| Range | Relationship | Action | Review |
|-------|-------------|--------|--------|
| >100% | Superset/subset | Ultra-careful merge | ⚠️ MAXIMUM |
| 100% | Identical (hash) | Nothing to do | None (only case) |
| 60-99% | High similarity | Intelligent merge | Mandatory |
| <60% | Low similarity | Manual/skip | Variable |
| — | Binary, not identical | Choose a side or keep both | Manual |
| — | Only on one side | Copy after approval | Standard |

## Six-Layer Verification

| # | Layer | Catches |
|---|-------|---------|
| 1 | Existence | Missing files, deletions |
| 2 | Hash (SHA-256) | Any content change — **gatekeeper**: match = skip 3-6 |
| 3 | Size | Truncation, corruption |
| 4 | Timestamp | Stale versions (2-second tolerance for filesystem rounding) |
| 5 | Line count | Partial writes |
| 6 | Content diff | Specific changes |

## Adaptive Depth

### Tier 1: Baseline from the last run
| Condition | Rigor |
|-----------|-------|
| `synk_last_run` < 24h, no signals | **Quick** — hash check only, skip unchanged |
| 1-7 days, minor signals, or no record of a last run | **Standard** — full six-layer on all files |
| >7 days or drift signals | **Thorough** — six-layer + relationship analysis + merge candidates |

The last run is read from `docs/PULSE.json`, which Synk writes only when asked (`--pulse`). With no such file, start at Standard.

### Tier 2: Adaptive Mid-Scan
**Downshift:** Quick scan finds 95%+ identical → summary report, skip detailed diff.
**Upshift:** Quick scan finds >10 non-identical files → escalate to Thorough.
Standard scan finds superset relationships → escalate to Thorough for those clusters.

**Report shifts:** `🔄 Rigor adjusted: Quick → Standard (15 files differ)`

### Tier 3: Signals left by other tools (optional)
Only where other tools share the project's `docs/PULSE.json`; see Optional integration. Signals only raise rigor, never lower it.

## Safety

**Backup before every write:** each file an apply will overwrite is copied first into `[user copy]/ARCHIVE/synk-[timestamp]/<side>/` with `manifest.json`, `rollback.md` and `apply-report.json`. Files that did not exist are recorded so rollback deletes them.
**Full-project backup:** before a large or first sync, copy the whole project aside first — the engine backs up per file, not per project.
**Auto-rollback:** any item that fails a verification layer after copying — or raises anything while being verified — is restored from the backup on the spot, and reported; a rollback that fails is reported with the backup to restore by hand, and the run exits 1.
**Never through a link:** nothing is written, deleted, restored or backed up through a junction or link, and no source is read through one; each is refused with the link named.
**Nothing writes without approval:** the dashboard and the plan are read-only.

## Workflow

1. **Inventory** — Scan both copies, fingerprint all files (skips `.git`, `node_modules`, build output, caches and the folder name `ARCHIVE`, where Synk writes its own backups — at a copy's root in any spelling where the file system folds case, as on Windows and default macOS, since `archive/` is that same folder there, and then it is named on the dashboard; `.git`, `.hg`, `.svn` and `node_modules` fold the same way there, so `.GIT/` is `.git/`, while a build-output name is skipped only as spelled, so a project's `Build/` or `Dist/` is compared like any folder; a nested `archive/` or `ARCHIVE/`, and a project's other archive-named folders, are content and stay in sync on every file system; only the root's `ARCHIVE` is Synk's own). Where both copies fold case, a folder skipped as spelled in one copy (`build/`) whose other spelling is content in the other (`Build/`) is one folder spelled two ways: it is named on the dashboard as not compared ("skipped: spelled build in the user copy and Build in the working copy; rename one to sync it") and nothing under it is offered to apply. A junction or link inside either copy, to a folder or a file, is never followed (a dangling one is named as such), a folder that cannot be listed or a file that cannot be read is never read as absent or empty, and a file where the `ARCHIVE` folder goes is not compared: each is named on the dashboard as not compared, with its reason. A user copy whose `ARCHIVE` is itself a junction or link is named too: apply makes no backup through it, so it writes nothing until `ARCHIVE` is a plain folder. Where both copies fold case, a name that differs only in case between them (`Readme.md` and `README.md`) is one file, compared under the user copy's spelling and named as the same file in different case
2. **Compare** — Classify by tier + direction (with adaptive depth adjustment); two copies that hold the same lines with different line endings are classed `line_endings`, each side's convention named, never as a merge (endings that differ line by line inside the same mix are said to differ within the file); two copies that differ only in a UTF-8 byte-order mark are said so, the side carrying it named
3. **Propose** — Dashboard: `🔄 ✓12 identical | ⚠️2 superset | 🔀3 merge | ⏎1 line endings | ➕3 new`; show diffs for every merge and superset
4. **Execute** — After approval: backup → copy or merged write → verify (six layers) → roll back failures → log
5. **Report** — `🔄 Synced: [n] | Verified: ✓ | Archive: [path]`; with `--pulse`, the run is recorded in `docs/PULSE.json`

## Scripts

**`scripts/synk_engine.py`** — the engine behind the workflow. Read-only unless told to apply.

```bash
python scripts/synk_engine.py USER_COPY WORKING_COPY                    # dashboard
python scripts/synk_engine.py USER_COPY WORKING_COPY --plan plan.json   # numbered plan, nothing written
python scripts/synk_engine.py USER_COPY WORKING_COPY --diff path/in/project.md    # --diff=-name for a name that starts with a dash
python scripts/synk_engine.py USER_COPY WORKING_COPY --apply plan.json --approve 2,5 [--pulse]
```

- Plan items carry `direction`: set for one-sided files; `null` for merges, supersets and line-ending-only pairs until the user decides. To apply a merge, write the merged file into one copy, set that item's direction to the other copy in the plan, and approve its id. An approved item whose direction is still `null`, or is not `user_to_working` or `working_to_user`, is skipped with that reason, and the run exits 1.
- An item is refused before any backup or write when its path leaves either copy (absolute, `..`, drive-relative or UNC forms), ends in a separator or a space, on Windows holds a form Windows reserves (a segment ending in a dot or a space, a `:` stream, `<>"|?*`) or names a device as the running Windows maps it (a bare `NUL` on Windows 11; `con.txt` too on Windows 10, so the engine asks the OS rather than keeping a list; under a copy on a network share, where the share maps no device, the OS is asked as for a local folder), lies in a folder the scan skips (`.git`, `node_modules`, the root's `ARCHIVE`, in any spelling the file system folds; a build-output folder as spelled, and one the destination spells so, as a plan's `Build/` where that copy holds `build/`), passes through or names a junction or link on either side, names a folder rather than a file (`sub`, or `.` for the copy itself), when its source or the file its destination would replace cannot be read, or when its destination changed since the plan was written — a file that appeared, or was edited, after `--plan`: re-plan. Copies given as `\\?\C:\...` (a prefix Windows allows on any path, a network share's too) are used in their plain form, where the OS maps devices, so they sync like any other and `NUL` never becomes a real file; a copy whose plain form would name another folder (`work.` would be `work`) or is too long for a plain path keeps the form it was given, and devices are still refused. A destination that already holds the source's content, whatever the item's status, is reported as already applied, and not counted as a failure: nothing is written, the run can exit 0, and `--pulse` sends no `sync_conflict` for it. The source is copied as it is at apply time: the plan pins the destination, not the source. Each refusal is reported and the run exits 1. An `--approve` id that names no plan item, an id that appears twice in a hand-edited plan, `--approve` without `--apply`, `--plan` beside `--apply`, `--diff` beside `--plan`, `--apply` or `--pulse`, a `--threshold` outside 0 to 1, and the same folder given for both copies are errors that stop the run before anything is written. A `--plan` file that cannot be written (a missing folder, or a folder in its place) is answered with the reason and exit 1, and a `--pulse` beside it still records the scan. An empty name given to `--plan`, `--apply` or `--diff` is answered the same way, and a hand-edited plan whose ids are not whole numbers or whose hashes are not objects is refused before anything is written; a plan saved with a UTF-8 BOM is read. When no backup folder can be made (a file named `ARCHIVE` in the user's copy, or an `ARCHIVE` that is a junction or link), or a backup fails midway (whatever is raised), every approved item is refused, nothing is written and no archive folder is left behind. `--diff` refuses a path that leaves the copies or names a link, names a file it cannot read, and says when the copies differ only in line endings (by convention, or line by line within the file) or only in a byte-order mark; a byte-order mark on one side is named beside any other difference too, on the dashboard, in the plan and by `--diff`, so it is never copied or stripped without a word. Everything the engine writes (the plan, the archive's files, `docs/PULSE.json`) is LF on every platform.
- `--approve new` approves every one-sided file at once — still an explicit approval, so show the list first. It names each item it leaves out, with the reason: `docs/PULSE.json`, which each copy keeps for itself (approve it by id to copy it), and any item it refuses (a path that leaves the copies, names a device or a form Windows reserves, lies in a skipped folder or passes through a link, or an item with no path), which is counted as refused, written to the archive's `apply-report.json` with the rest, and makes the run exit 1. When nothing is left to approve (no file is in one copy only, or only `docs/PULSE.json` is), it says so and exits 0, and a `--pulse` beside it still records the run.
- `--pulse` writes `synk_last_run`, `synk_drift_detected` and its signals into `USER_COPY/docs/PULSE.json`, plus `synk_files_changed` after an apply, keeping every other key. After an apply, `sync_completed` is emitted only when a file was written, and `new_files_synced` names only the files the apply created, not the ones it overwrote. A wrong-typed field (`"pending_signals": null`) is treated as empty with a note; a PULSE that does not parse, or holds no JSON object, is never touched, and the run says so; when none exists one is created holding only `cross_skill`. When `docs` is a file, `docs` or `PULSE.json` is a junction or link, or the PULSE cannot be written, the run warns that it is not recorded there, and an apply still reports what it wrote.
- The same operations are available as `SynkEngine(...).scan_and_compare()`, `.plan()`, `.diff()`, `.backup()`, `.apply()`, with `.refusal(path)` and `.new_ids(plan)` for the checks above. No answer outlives the call that asked it: each call asks about links afresh. Immediately before each write, `.apply()` asks again, uncached, about the destination's folders and the source's; before each file it reads into the archive or writes there (a backup copy, `manifest.json`, `rollback.md`, `apply-report.json`) and before it removes a backup that failed, about the folders on the way; before a rollback restores or deletes, about the copy's folders and the backup's. A junction or link found at any of those moments refuses the write, the backup or the rollback, names the link, and is never followed; the check and the write are separate calls, so a link made in the instant between them is outside what any check can see.

## Merge Strategies

**Standard (60-99%):** Shared base → user-unique + working-unique → merged → diff for review.
**Superset (>100%):** Identify superset → identify delta → assess intent → present with preview → **never auto-resolve**.
**Configs (JSON/YAML):** Structural key-value diff → user version as authority.

## Anti-Patterns
- Syncing build artifacts (node_modules, bin/, obj/)
- Auto-resolving superset merges
- Syncing mid-edit (verify saved first)
- Assuming newer = better
- Swapping which copy is the user's
- Copying secrets (`.env`, keys) into a copy the user did not mean to hold them
- Consolidating during sync (a consolidation tool's job)
- Skipping verification layers

## Optional integration

Synk182 needs nothing else. Where other tools share the project's `docs/PULSE.json` (its companions in The Triad, DevCom5 and Solid8, or any tool that follows the same protocol), `--pulse` leaves signals for them and Synk reads theirs; with none of them, or no PULSE file, nothing waits on these signals and Synk runs at its own tiers. Protocol: [references/TRIFECTA_PROTOCOL.md](references/TRIFECTA_PROTOCOL.md).

**Emits:** `sync_completed` → DevCom5 | `sync_conflict` → DevCom5 | `environment_diverged` → DevCom5 | `new_files_synced` → Solid8
**Consumes:** `drift_detected` (DevCom5) → at least Standard | `consolidation_complete` (Solid8) → new baseline, full comparison | `stale_project` (DevCom5) → Thorough | `docs_created` (DevCom5) → include the new docs in the next comparison
**PULSE writes:** `synk_last_run`, `synk_drift_detected`, `synk_files_changed`

## Changelog

- **3.3** — the engine refuses an unsafe plan item before any backup (a path that leaves either copy, a skipped folder in any spelling, a link, a device, a form Windows reserves, a destination changed since the plan), never writes, backs up, restores or deletes through a junction or link, names what it cannot compare, names differences in line endings or a byte-order mark as such, and writes everything LF; the skill names jobs rather than other tools, and stands alone in any agent.
- **3.2** — freeware; the description says what it is not for.
- **3.1** — any two copies, not one sandbox; the engine backs up, applies, verifies and rolls back.
- **3.0 and earlier** — comparison only.

*Synk has no prior alias. It has always been Synk. That's the joke.*
