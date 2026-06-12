## Context

`session_index/config.py` exposes a single `projects_dir` string resolved from (in priority order): function args → `SESSION_INDEX_PROJECTS` env var → `~/.session-index/config.json` → default `~/.claude/projects`. The `SessionIndexer` class receives this as one `Path` and walks it exclusively.

Users running multiple Claude Code environments (`CLAUDE_CONFIG_DIR=~/.claude-personal`, `~/.claude-work`, `~/.claude-bedrock`) each have a separate session store. Only the one `projects_dir` currently configured is indexed; the others are invisible.

## Goals / Non-Goals

**Goals:**
- Accept a list of project directories anywhere a single path is accepted today (config file, env var, function arg)
- Index all configured directories into one unified SQLite database in a single `index` run
- Track which environment each session came from via a `source_env` column
- Allow filtering to a specific environment via `--env` on browse commands
- Remain backward-compatible: existing single-path configs and env vars continue working without change

**Non-Goals:**
- Per-environment separate databases or DB federation
- Auto-discovery of Claude config directories (user explicitly configures the list)
- Per-environment filtering on retrieval commands (`search`, `context`) — these are always global

## Decisions

### D1: Coerce single values to lists at the config boundary

Rather than propagating a union type (`str | list[str]`) through the codebase, `config.py` normalizes every resolved value to `list[Path]` before it leaves the config layer. Downstream code (`SessionIndexer`) always receives a list and never needs to branch on type.

*Alternative considered*: Keep `projects_dir` as a string and add a separate `extra_projects_dirs` list. Rejected — two config keys for the same concept, awkward to merge.

### D2: Env var accepts colon-separated paths (POSIX PATH convention)

`SESSION_INDEX_PROJECTS=/path/a:/path/b` — consistent with how `PATH`, `PYTHONPATH`, and similar vars work on macOS/Linux. Single paths work unchanged.

*Alternative considered*: Comma-separated. Rejected — paths themselves can't contain colons, so colon is unambiguous and familiar.

### D3: `config.json` key renamed `projects_dirs` (plural), old `projects_dir` still accepted

The config loader checks for `projects_dirs` first, falls back to `projects_dir` if absent. Both are normalized to a list. This avoids a breaking change for existing config files.

### D4: `SessionIndexer` receives `projects_dirs: list[Path]`

Constructor signature changes from `projects_dir: Path = None` to `projects_dirs: list[Path] = None`. The backfill and incremental loops iterate over all dirs. Session IDs (UUIDs in filenames) are globally unique across environments so there are no collision concerns.

### D5: `source_env` column stores the projects directory root

Each session row gains a `source_env TEXT` column set to the `projects_dir` path the session was found under (e.g., `/Users/craig/.claude-personal/projects`). This makes env filtering a simple `WHERE source_env LIKE ?` without path string parsing at query time.

*Alternative considered*: Derive env from `file_path` at query time. Rejected — fragile if paths change, and requires joining config state into every query.

### D6: `--env` accepts a substring match against `source_env`

`sessions recent --env personal` filters `WHERE source_env LIKE '%personal%'`. No exact path required — the common case (environment name in the dir name) just works. Ambiguity (e.g., `work` matching both `~/.claude-work` and `~/.claude-work-backup`) is the user's responsibility to resolve with a more specific substring.

*Alternative considered*: Exact path match. Rejected — too verbose for interactive use.

### D7: `--env current` resolves to `CLAUDE_CONFIG_DIR`

The literal string `current` is a reserved value that expands to the value of `CLAUDE_CONFIG_DIR` at runtime. This lets users write `sessions recent --env current` in shell aliases without hardcoding a path. If `CLAUDE_CONFIG_DIR` is unset, the command fails with a clear error.

### D8: Browse commands default to global; retrieval commands are always global

`recent`, `find`, and `analytics` default to all environments — no ambient `CLAUDE_CONFIG_DIR` dependency in default behavior. `search` and `context` are always global (you don't know which env you used when searching by content). `--env` is only added to browse commands.

### D9: `env:<name>` label derived from `source_env` tail

The display label strips the `/projects` suffix, takes the last path segment, then strips a `claude-` prefix if present: `/Users/craig/.claude-personal/projects` → `personal`. The `env:` prefix is included in output to make the label self-describing.

## Risks / Trade-offs

- **Duplicate project slugs across environments**: Two environments working on the same project path produce the same directory name (e.g., `-Users-craig-work-myapp`). Sessions within are still unique (UUID filenames), but `project_name` display may be ambiguous. → Acceptable for now; the session ID still uniquely identifies the source.
- **First-run indexing time**: Indexing 3× the sessions on first backfill takes proportionally longer. → No mitigation needed; it's a one-time cost and the user controls which dirs to add.
- **`--projects-dir` CLI flag**: Currently accepts one value. Updated to be repeatable (`--projects-dir A --projects-dir B`) or accept colon-separated input. → Use repeatable flag for clarity.
- **Schema migration for existing DBs**: Existing sessions have no `source_env`. On `--backfill`, the indexer can populate `source_env` by matching `file_path` against the configured `projects_dirs`. Sessions whose path doesn't match any configured dir get `source_env = NULL`; these are included in all results and excluded from `--env` filters.

## Migration Plan

1. Ship the change; existing users see no behavior difference (single `projects_dir` coerces transparently to a one-element list, all queries default to global).
2. The `_create_schema()` call adds `source_env` to the `sessions` table if absent (SQLite `ALTER TABLE ADD COLUMN` is safe on existing DBs).
3. Users wanting multi-dir support add `projects_dirs` to `~/.session-index/config.json` or set `SESSION_INDEX_PROJECTS=/path/a:/path/b`.
4. Running `sessions index --backfill` after config change picks up the new dirs and populates `source_env` for all sessions.

Rollback: removing a dir from config stops new sessions from being indexed from that dir. Existing records remain; `source_env` values are inert if `--env` is not used.
