## Why

The `multi-projects-dir` capability lets one machine index sessions from several local Claude environments (personal/work/Bedrock), and each result is tagged with an `env:<name>` label. It has no notion of *which physical machine* produced a session. Once session directories are synced between machines (e.g. via Syncthing/Dropbox into a shared folder that every machine also indexes), sessions from different laptops become indistinguishable in query results — there's no way to filter to "just my work laptop's sessions" or see at a glance where a result originated.

## What Changes

- Add a `machine_names` config dict (`projects_dir` path → friendly machine label), plus an optional top-level `machine_name` override for the local machine's own label. Resolved via a new `config.get_machine_name(projects_dir)`.
- Add a `machine` column to the `sessions` table, populated at index time with the **resolved** friendly name (mirrors how `project_name` is stored today, not how `source_env`'s raw-path-plus-derived-label works). Safe `ALTER TABLE` migration plus backfill relabeling for existing rows, matching the existing `source_env` migration pattern.
- Add a `--machine <substring>` filter to `recent`, `find`, and `analytics`, matching `--env`'s shape. `--machine current` resolves to the local machine's own name.
- Add a `machine:<name>` label to session result output, alongside the existing `env:<name>` label.
- Document (README only, no code) a recommended synced-folder convention (e.g. `~/SessionSync/<machine-name>/projects/`) for full-mesh multi-machine syncing, and the "don't add your own machine's synced mirror of itself" gotcha. The sync mechanism itself (Syncthing/Dropbox/iCloud/rsync) stays out of scope, same as this project doesn't manage `~/.claude-*/projects` creation.

No changes to how `projects_dirs` itself is resolved — a synced peer folder is just another entry in that list, which the system already supports.

## Capabilities

### New Capabilities
- `machine-tagging`: config-driven resolution of a friendly machine name per projects directory, stored per-session at index time, filterable via `--machine`, and shown as a `machine:<name>` label in results — the same treatment `multi-projects-dir` already gives `env:<name>`, but for physical-machine identity instead of local-environment identity.

### Modified Capabilities
(none — `multi-projects-dir`'s existing requirements are unchanged; `machine_names` resolution is additive on top of the existing `projects_dirs` config surface)

## Impact

- `session_index/config.py` — new `get_machine_name()`, new `machine_names`/`machine_name` config keys. This touches the same resolution-precedence chain that has broken silently in production twice before (per project history); the `verify-config-resolution` regression script must pass before this is considered done.
- `session_index/indexer.py` — schema migration for `machine` column; `_parse_session`, `_upsert_session`, `backfill_all`, `index_incremental` resolve and persist `machine`.
- `session_index/search.py` — mirrored schema migration; `--machine` filter clause; `machine:<name>` result label.
- `session_index/cli.py` — `--machine` flag wired into `recent`, `find`, `analytics`.
- `session_index/analyzer.py` — `analytics()` gains a `machine` filter clause mirroring the existing `env` clause.
- `README.md` — recommended sync-folder convention and self-sync-duplication caveat.
- No new dependencies. Purely additive — existing rows get `machine = NULL` until backfilled, no breaking behavior change for single-machine users.
