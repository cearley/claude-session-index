## 1. Config Layer

- [x] 1.1 Add `get_projects_dirs()` to `config.py` that returns `list[Path]`, coercing a single-string `projects_dir` value to a one-element list
- [x] 1.2 Update config resolution to check `projects_dirs` (list) before `projects_dir` (string) in `config.json`
- [x] 1.3 Update `SESSION_INDEX_PROJECTS` env var parsing to split on `:` and return all paths
- [x] 1.4 Update `DEFAULTS` to keep `projects_dir` as the default key for backward compat

## 2. Indexer

- [x] 2.1 Change `SessionIndexer.__init__` to accept `projects_dirs: list[Path] = None` (replacing `projects_dir: Path = None`)
- [x] 2.2 Update `backfill_all()` to iterate over all dirs in `self.projects_dirs`
- [x] 2.3 Update the incremental index walk to iterate over all dirs in `self.projects_dirs`
- [x] 2.4 Update `_find_session_file()` to search across all configured dirs when resolving a session ID prefix

## 3. CLI

- [x] 3.1 Change `--projects-dir` flag to `action="append"` so it can be repeated (`--projects-dir A --projects-dir B`)
- [x] 3.2 Update the `db_path` / projects resolution block in `main()` to pass a list to `SessionIndexer`
- [x] 3.3 Ensure colon-separated `SESSION_INDEX_PROJECTS` is handled transparently (covered by config layer — verify end-to-end)

## 4. Schema & source_env

- [x] 4.1 Add `source_env TEXT` column to the `sessions` table in `_create_schema()` using `ALTER TABLE ADD COLUMN IF NOT EXISTS` (safe on existing DBs)
- [x] 4.2 Populate `source_env` in `index_session()` with the `projects_dir` root the session was found under
- [x] 4.3 During `--backfill`, populate `source_env` for existing sessions by matching `file_path` against each configured `projects_dirs` entry; leave `NULL` for unmatched rows

## 5. --env flag

- [x] 5.1 Add `--env` argument to `recent`, `find`, and `analytics` subparsers in `cli.py`
- [x] 5.2 In `SessionSearch`, add `env` parameter to `recent()`, `find()`, and the analytics query; apply `WHERE source_env LIKE '%<env>%'` when set
- [x] 5.3 Resolve `--env current` to `CLAUDE_CONFIG_DIR` before passing to search; print a clear error if `CLAUDE_CONFIG_DIR` is unset

## 6. Display

- [x] 6.1 Add a helper to derive the `env:<name>` label from a `source_env` path (strip `/projects` suffix → take last segment → strip `claude-` prefix)
- [x] 6.2 Update `format_result()` in `search.py` to include the `env:<name>` label in the session summary line when `source_env` is set

## 7. Documentation

- [x] 7.1 Update `CLAUDE.md` config table to document `projects_dirs` (list) and colon-separated env var
- [x] 7.2 Update `README.md` Configuration section with the new `projects_dirs` key, multi-path env var syntax, and `--env` flag usage
