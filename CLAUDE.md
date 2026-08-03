# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> Forked from [lee-fuhr/claude-session-index](https://github.com/lee-fuhr/claude-session-index). This fork is maintained at [cearley/claude-session-index](https://github.com/cearley/claude-session-index).

## Setup & Commands

```bash
# Install for local development (editable)
pip install -e .

# Optional: enable the `synthesize` command (requires Anthropic API key)
pip install -e ".[synthesis]"
```

The package installs five entry points: `sessions` (unified CLI), `session-index`, `session-search`, `session-analyze`, `session-topic-capture`.

```bash
# Common CLI usage
sessions "webhook debugging"          # full-text search (default)
sessions index                        # index new/modified sessions
sessions index --backfill             # re-index everything
sessions stats                        # database overview
sessions recent 20                    # last N sessions
sessions analytics --week             # this week's stats

# Re-index a single session by ID prefix
sessions index --session a5b111c6
```

There are no tests in this repository.

## Architecture

The package (`session_index/`) has five modules with clear separation of concerns:

**`indexer.py`** — `SessionIndexer` class. Walks `~/.claude/projects/**/*.jsonl` (Claude Code session files), parses each JSONL, and writes to SQLite. Schema has four tables: `sessions`, `session_topics`, `session_tools`, `session_agents`. Uses file hashes for incremental updates and FTS5 virtual table for full-text search over session content.

**`search.py`** — `SessionSearch` class. Pure SQL/FTS5 queries against the DB. FTS5 queries are sanitized via `_escape_fts_query()` — wraps tokens in double-quotes to prevent reserved-word crashes (AND/OR/NOT/NEAR).

**`analyzer.py`** — Three independent capabilities: (A) `get_context()` reads the raw JSONL file and extracts conversation exchanges around a search match; (B) `analytics()` runs pure SQL aggregations for time/tool/client stats; (C) `synthesize()` searches the DB, reads matching JSONL files, and calls Haiku via the Anthropic API to synthesize across sessions.

**`topic_capture.py`** — Claude Code hook handler (stdin JSON → topic extraction → write to DB + `~/.claude/session-topics/{session_id}.txt`). Handles three hook events: `UserPromptSubmit` (every 10 exchanges), `PreCompact`, `SessionEnd`. No API calls — parses the last 3 user messages from JSONL directly. `SessionEnd` also triggers an incremental index pass.

**`config.py`** — Configuration resolution with layered priority: function args → env vars → `~/.session-index/config.json` → defaults. Key paths: DB at `~/.session-index/sessions.db`, source sessions at `~/.claude/projects/`, topics dir at `~/.claude/session-topics/`. Auto-generates friendly project names from directory names if not configured.

**`cli.py`** — Unified `sessions` entry point. Detects bare text (no subcommand) and routes it to `search`. Calls `config.ensure_indexed()` on every invocation — auto-backfills on first run.

## Configuration

Config file: `~/.session-index/config.json`

| Env var | Config key | Default |
|---|---|---|
| `SESSION_INDEX_PROJECTS` | `projects_dirs` (list) or `projects_dir` (string) | derived from `CLAUDE_CONFIG_DIR`, or `~/.claude/projects` + discovered `~/.claude-*/projects` |
| `SESSION_INDEX_DB` | `db_path` | `~/.session-index/sessions.db` |
| `SESSION_INDEX_TOPICS` | `topics_dir` | `~/.claude/session-topics` |

**Multi-environment support:** with no explicit config, `get_projects_dirs()` globs sibling `~/.claude-*/projects` directories itself (no shell integration required — this used to depend on a shell plugin exporting `SESSION_INDEX_PROJECTS`, now it's self-sufficient). `SESSION_INDEX_PROJECTS` still accepts colon-separated paths as an override when you want a different set than what's on disk:
```
SESSION_INDEX_PROJECTS=~/.claude-personal/projects:~/.claude-work/projects:~/.claude-bedrock/projects
```
Or use `projects_dirs` (list) in `config.json`. Single-path values work unchanged for backward compat.

Each session is tagged with an `env:<name>` label in results (derived from its source directory). Use `--env` on `recent`, `find`, and `analytics` to filter by environment — pass a substring or `current` to resolve `CLAUDE_CONFIG_DIR`:
```bash
sessions recent --env personal
sessions recent --env current      # resolves CLAUDE_CONFIG_DIR
sessions find --week --env work
```

Optional `clients` list and `project_names` dict (dir → friendly name) in the config file enable client attribution and custom display names.

## Claude Code Integration

**Skill** (`skills/session-index/SKILL.md`): Install to `.claude/skills/session-index.md`. Provides the conversational interface — Claude translates natural-language questions into CLI commands and presents results in prose.

**Hooks** (`hooks/settings-snippet.json`): Add to `~/.claude/settings.json` to enable live topic tracking. Hooks call `session-topic-capture` on `UserPromptSubmit`, `PreCompact`, and `SessionEnd`.

**LaunchAgent** (`launchagent/com.session-indexer.plist`): macOS LaunchAgent for background incremental indexing.
