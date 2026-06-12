## Why

Users running multiple Claude Code environments (e.g., `~/.claude-personal`, `~/.claude-work`, `~/.claude-bedrock`) have separate session stores per environment, but the tool only indexes one `projects_dir`. Sessions from other environments are invisible to search.

## What Changes

- The tool accepts a list of project directories instead of a single `projects_dir`
- Config file, environment variable, and function-arg resolution all support multiple paths
- The indexer walks all configured directories in a single pass, writing to one unified DB
- The `sessions` CLI gains no new commands — the change is transparent to the user

## Capabilities

### New Capabilities

- `multi-projects-dir`: Support configuring multiple Claude projects directories so sessions from all Claude Code environments are indexed into a single searchable database

### Modified Capabilities

<!-- none — no existing specs to update -->

## Impact

- **`session_index/config.py`**: `projects_dir` (string) becomes `projects_dirs` (list of strings); backward-compatible single-string values are coerced to a one-element list
- **`session_index/indexer.py`**: `SessionIndexer.__init__` and the backfill/incremental walk loop updated to iterate over all configured dirs
- **`session_index/cli.py`**: `--projects-dir` flag updated to accept multiple values (or accept comma-separated paths)
- **`CLAUDE.md`**: Documented new config key and env var behavior
- No schema changes, no new dependencies, no breaking changes to the CLI surface
