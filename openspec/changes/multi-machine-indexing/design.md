## Context

See `proposal.md` - Why. Relevant existing state this design builds on:

- `config.py` already resolves `projects_dirs` from a layered priority chain (overrides → env var → `config.json` → auto-discovery) and already accepts arbitrary paths in that list — a synced peer machine's folder is just another entry, no new discovery mechanism needed.
- `indexer.py` and `search.py` already carry a precedent for this exact shape of feature: `source_env` is stored on `sessions` at index time, migrated in via a guarded `ALTER TABLE`, backfilled for pre-existing rows, filterable via `--env`, and shown as an `env:<name>` label. `machine` follows the same shape but a different storage/derivation choice (see Decisions).
- `config.py`'s resolution chain has broken silently in production twice before (a multi-env hook crash, a version-drift bug), which is why a dedicated `verify-config-resolution` regression script exists for that file specifically.

## Goals / Non-Goals

**Goals:**
- Resolve and persist a friendly machine name per session, with an explicit-config-first, safe-fallback resolution order.
- Filter and display `machine` with the same ergonomics `env` already has (`--machine`, `machine:<name>` label, `current` shorthand).
- Migrate existing databases without a forced full reindex.

**Non-Goals:**
- Implementing, managing, or configuring the file-sync mechanism itself (Syncthing/Dropbox/iCloud/rsync). This design assumes session directories from other machines simply appear on disk somehow, same as `~/.claude-*/projects` does today.
- Auto-deriving machine names from synced-folder path segments. Rejected during brainstorming in favor of explicit `machine_names` config (see Decisions).
- Query-time federation across multiple separate DB files. Rejected during brainstorming (see Decisions).
- A `by_machine` breakdown in `sessions stats`. Not requested; easy follow-up if needed.
- Automatic relabeling of already-indexed rows when a machine is renamed in config, beyond what the existing NULL-backfill pattern already provides.

## Decisions

**1. Store the resolved friendly name in a new `machine` column, not a raw path + query-time label.**
`project_name` already does this (resolved once via `project_name_map`, stored directly); `source_env` does the opposite (raw path stored, `_env_label()` derives the display label at query time). Machine resolution depends on an explicit config dict (`machine_names`), not a fixed string-parsing rule, so deriving it at query time would mean threading config lookups through every read path (`search.py`, `cli.py`, `analyzer.py`). Storing the resolved value keeps filtering and display trivial string operations, at the cost of requiring a backfill to relabel history after a rename in config — the same trade-off `project_name` already accepts today, so this sets no new precedent.

**2. Explicit `machine_names` config mapping, not auto-derivation from folder paths.**
`_env_label()` can safely parse `env` from a path because this project controls that naming convention (`~/.claude-<name>/projects`). Peer sync folders have no such guarantee — their layout is whatever the user's sync tool produces. Auto-deriving from path segments was considered and explicitly rejected in favor of an explicit map, mirroring `project_names`' existing shape.

**3. Reuse `projects_dirs` for peer machines; no new discovery mechanism.**
`get_projects_dirs()` already accepts arbitrary paths via config or env var. A dedicated `sync_root` glob (mirroring the `.claude-*` auto-discovery) was considered and rejected as unneeded — it would require enforcing a folder-naming convention this project doesn't control, for no benefit over just adding the path explicitly.

**4. Sync transport/topology is out of scope; query-time DB federation was considered and rejected.**
An alternative design would keep every machine's DB fully separate and `ATTACH` them at query time instead of merging data at index time. This was explored and rejected because it doesn't remove the sync requirement (`ATTACH` still needs a locally reachable file, so a synced folder is needed either way), it couples every machine to an identical schema version before federated queries can run, it requires `search.py`/`cli.py`/`analyzer.py` to issue per-DB FTS5 queries and merge/re-rank results in Python (FTS5 doesn't federate across attached DBs natively), and it breaks `analyzer.get_context()` for remote sessions since a federated row's `file_path` points to a path that doesn't exist on the querying machine. Indexing synced raw JSONL locally (this design) avoids all of that by only ever writing to one local DB.

**5. Fallback order distinguishes local-default directories from unmapped explicit directories.**
Unmapped *local default* dirs (`~/.claude/projects`, sibling `~/.claude-*/projects`) safely fall back to the configured `machine_name` or hostname — they are, by definition, local. Any *other* unmapped directory (an explicitly-added peer folder someone forgot to map) instead gets a path-derived fallback label plus a printed warning, rather than silently defaulting to the local machine's own name — silently mislabeling a peer machine's sessions as local would actively corrupt `--machine` filtering rather than just being cosmetically imprecise.

## Risks / Trade-offs

- **[Risk]** Renaming a machine in `machine_names` doesn't retroactively relabel already-indexed sessions — `backfill_all()`'s skip-on-matching-hash logic only patches `machine` when it's currently `NULL`, so a rename to an already-labeled row is a no-op. → **Mitigation**: document this limitation (identical to `project_names`' existing behavior today); no code changes needed to accept it, a dedicated relabel path can be added later if it becomes a real pain point.
- **[Risk]** Self-sync duplication — if a user's sync tool mirrors their own machine's directory back to itself and they mistakenly add that mirrored copy to `projects_dirs` alongside their real local directory, the same `session_id` gets indexed from two source paths, and the assigned `machine` becomes dependent on directory-iteration order, flapping between runs. → **Mitigation**: documented as a setup gotcha in the README; not code-enforced, since it's a configuration mistake rather than a design gap, and detecting it reliably would require guessing at sync-tool-specific folder semantics this project doesn't own.
- **[Risk]** `config.py`'s resolution chain has broken silently in production twice before. `get_machine_name()` adds new logic to that same file. → **Mitigation**: the `verify-config-resolution` regression script must pass before this change is considered done; extend it with machine-name resolution scenarios during implementation.
- **[Trade-off]** Unmapped non-default directories get a best-effort path-derived label rather than a hard failure, so indexing never breaks on a missed `machine_names` entry — accepted because the accompanying warning makes the gap visible without taking indexing down.

## Migration Plan

- Add `machine` to `sessions` via `ALTER TABLE sessions ADD COLUMN machine TEXT`, guarded by the same `existing_cols` check already used for `source_env`, applied in both `indexer.py`'s `_create_schema()` and the equivalent schema-check path in `search.py`.
- Extend `backfill_all()`'s existing "patch `source_env` when NULL on an unchanged file" branch to also patch `machine` when NULL, so upgrading an existing database backfills machine labels without a full reparse of unchanged session files.
- The column is additive and nullable — no rollback procedure beyond reverting the code; existing data and behavior for single-machine users is unaffected either way.
