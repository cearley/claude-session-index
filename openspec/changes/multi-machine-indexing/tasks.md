## 1. Config resolution (`session_index/config.py`)

- [x] 1.1 Add `machine_names` (dict) and `machine_name` (string) to `DEFAULTS` and the config-file layering in `get_config()`
- [x] 1.2 Implement `get_machine_name(projects_dir: Path) -> str` with the fallback order from design.md: (1) explicit `machine_names[str(projects_dir)]`, (2) `machine_name` config value or local hostname if `projects_dir` is the default `~/.claude/projects` or a sibling `~/.claude-*/projects`, (3) path-derived fallback label plus a printed warning for any other unmapped directory
- [x] 1.3 Extend the `verify-config-resolution` regression script with scenarios covering `get_machine_name()`'s three fallback tiers, and run it to confirm the existing resolution chain isn't broken (also fixed a pre-existing module-reimport bug in `_reset_config_module()` that this work surfaced — see script comments)

## 2. Indexer schema & population (`session_index/indexer.py`)

- [x] 2.1 Add `machine` column via guarded `ALTER TABLE sessions ADD COLUMN machine TEXT` in `_create_schema()`, mirroring the existing `source_env` migration
- [x] 2.2 Resolve `machine = config.get_machine_name(projects_dir)` once per `projects_dir` loop in `backfill_all()` and `index_incremental()`, and pass it into `_parse_session()` alongside `source_env`
- [x] 2.3 Resolve `machine` in `index_session()`'s single-file path (match `projects_dir` from `self.projects_dirs`, same way `source_env` is matched today)
- [x] 2.4 Persist `machine` in `_upsert_session()`'s INSERT column list and `ON CONFLICT` UPDATE clause
- [x] 2.5 In `backfill_all()`, extend the existing "patch `source_env` when NULL on an unchanged file" branch to also patch `machine` when NULL

## 3. Search & display (`session_index/search.py`)

- [x] 3.1 Add the same guarded `machine` column migration used in 2.1 to `search.py`'s schema-check path
- [x] 3.2 Add a `machine: str = None` parameter to `find()` and `recent()` (not the FTS `search()` method — `--env` doesn't filter full-text `search` either, per `cli.py`'s existing subcommand wiring, so `--machine` follows the same precedent), appending a `machine LIKE ?` condition when set
- [x] 3.3 Add `machine:<name>` to the per-result metadata label list, alongside the existing `env:<name>` label

## 4. CLI wiring (`session_index/cli.py`)

- [x] 4.1 Add a `--machine` flag to the `recent`, `find`, and `analytics` subcommands
- [x] 4.2 Wire `--machine current` to resolve via `config.get_machine_name()` against the local default projects directory, matching how `--env current` resolves via `CLAUDE_CONFIG_DIR`
- [x] 4.3 Pass the resolved `--machine` value through to the corresponding `search.py`/`analyzer.py` calls

## 5. Analytics filter (`session_index/analyzer.py`)

- [x] 5.1 Add a `machine: str = None` parameter to `analytics()` and an `AND s.machine LIKE ?` clause mirroring the existing `source_env` clause

## 6. Documentation (`README.md`)

- [x] 6.1 Document the `machine_names` / `machine_name` config keys and the resolution fallback order
- [x] 6.2 Document the recommended synced-folder convention (e.g. `~/SessionSync/<machine-name>/projects/`) for full-mesh multi-machine syncing, and note that the sync tool itself is out of scope
- [x] 6.3 Document the self-sync-duplication gotcha: don't add your own machine's synced mirror of itself to `projects_dirs`
- [x] 6.4 Document `--machine` usage alongside the existing `--env` documentation

## 7. Verification

- [x] 7.1 Run the `verify-config-resolution` regression script (with 1.3's new scenarios) and confirm all pass — 12/12 passed
- [x] 7.2 Backfill against an existing local database and confirm `machine` is populated for all previously-indexed sessions without a full reparse — verified against the real `~/.session-index/sessions.db` (backed up first, backup removed after passing verification); all NULL-`machine` rows correspond to source files no longer on disk, same pre-existing limitation `source_env` already has
- [x] 7.3 Manually verify `--machine <substring>`, `--machine current`, and the `machine:<name>` display label against a DB with sessions from more than one configured directory — verified against real data; single-machine setup with three local `.claude-*` environments all correctly resolved to the same hostname-derived machine name
- [x] 7.4 Add a CHANGELOG entry for this change — added under "Unreleased" (no version bump; that's a separate release decision)
