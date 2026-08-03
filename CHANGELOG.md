# Changelog

## v0.5.0 — Multi-environment discovery, no configuration required

Multi-environment support used to require manually exporting `SESSION_INDEX_PROJECTS` in your shell profile. That's no longer necessary.

- **Automatic sibling-environment discovery** — with nothing configured, the tool now globs `~/.claude-*/projects` alongside the default `~/.claude/projects` and indexes them all. `SESSION_INDEX_PROJECTS`, `config.json`, and `CLAUDE_CONFIG_DIR` still work exactly as before and take precedence when set.
- **README clarifies why this fork exists** — front-and-center explanation of the multi-environment support this fork adds, why `pip install` won't work (upstream owns the PyPI package name), and credit for both authors.
- **Fixed version drift** — `pyproject.toml` had hardcoded `0.4.1` while `session_index.__init__.py` independently said `0.3.0`. `session_index.__version__` is now the single source of truth; `pyproject.toml` resolves it dynamically.

## v0.4.1 — Fix multi-env hook crash

- **Hotfix**: a multi-path `SESSION_INDEX_PROJECTS` (colon-separated) crashed all three hook handlers (`UserPromptSubmit`, `PreCompact`, `SessionEnd`) with `FileNotFoundError`. The singular `get_projects_dir()` accessor was treating the whole colon-joined string as one path; `find_session_file` and `get_project_names` now correctly iterate the plural `get_projects_dirs()`.

## v0.4.0 — Multi-Claude-environment support

Index sessions from multiple Claude home directories (e.g. personal, work, Bedrock) into one database, each tagged with the environment it came from.

- **`SESSION_INDEX_PROJECTS`** env var accepts colon-separated paths; **`projects_dirs`** list key in `config.json` (`projects_dir` still works for a single path)
- **`--projects-dir` flag is now repeatable** — `sessions --projects-dir /path/a --projects-dir /path/b`
- **`source_env` column** on the sessions table, migrating existing databases automatically
- **`--env <substring>`** filter on `recent`, `find`, and `analytics`; `--env current` resolves to `CLAUDE_CONFIG_DIR`
- **`env:<name>` label** shown in session results whenever multiple environments are present
- Skill and README updated with multi-environment usage guidance; install via `uv tool install` from this fork

## v0.3.1 — Stop titling everything "## Curation Data"

- **Smarter title auto-generation** — skips markdown headers, agent system prompts, and system caveats when picking a title from user messages. Tries up to 5 messages before giving up.
- Previously, 84+ sessions were titled "## Curation Data" and 20+ were titled "You are QA testing...". Now those get proper titles or null instead of garbage.

## v0.3.0 — Sessions have names now

The biggest annoyance is fixed: most sessions showed "(unnamed)" because only manually-titled sessions had display names. Now titles are auto-generated from compaction summaries or the first user message. Re-index with `sessions index --backfill` to see the difference.

- **Auto-generated session titles** — compaction summaries get parsed (including JSON blobs), and untitled sessions fall back to the first user message. No more walls of "(unnamed)".
- **`--days N` filter** — `sessions find --days 14` for arbitrary date ranges, not just `--week`
- **`--exclude-project` filter** — `sessions find --exclude-project "share memory"` to cut the noise
- **FTS5 crash fixes** — queries with periods (`CLAUDE.md`), hyphens (`session-index`), and reserved words (`index`) no longer crash. All search terms get quoted for safe literal matching.
- **CLI flag parsing fix** — `sessions "query" -n 5` now works correctly (the flag value was getting split from the flag)
- **`npx skills add` support** — skill moved to `skills/session-index/SKILL.md` to match the skills.sh registry convention. Install with `npx skills add lee-fuhr/claude-session-index`.
- **Conversational interface as primary UX** — README and skill rewritten to emphasize the natural language experience in Claude Code. The CLI is still there for power users.

## v0.2.0 — It looks good now

The output got a proper makeover. Conversations read like conversations. Analytics have visual hierarchy. And you don't have to set anything up anymore.

- **One command to rule them all** — `sessions` replaces the old `session-search` / `session-analyze` / `session-index` trio. Plain text defaults to search: `sessions "webhook debugging"` just works.
- Chat-like conversation display with 🧑/🤖 markers — you can actually tell who said what
- Box-drawing characters for session cards and exchange blocks
- Section headers with emoji in analytics (📊 📈 🔧 💬) for scannable output
- Cleaner search results with ◆ bullets and → resume commands
- Auto-indexing on first use — no more separate `--backfill` step, just run any command and it handles the rest
- Better stats display with visual structure instead of raw JSON
- The old commands still work if you prefer them

## v0.1.0 — Initial release

- Full-text search across all Claude Code sessions (SQLite + FTS5)
- Filter by client, project, tool, agent, tag, date
- Conversation context retrieval from session JSONL files
- Analytics: time per client, tool trends, session frequency, topic analysis
- Cross-session synthesis via Anthropic API (optional dependency)
- Live topic capture via Claude Code hooks (UserPromptSubmit, PreCompact, SessionEnd)
- Background indexing via macOS LaunchAgent
- Claude Code skill for natural language session queries
- Configurable paths via CLI flags, env vars, or config file
