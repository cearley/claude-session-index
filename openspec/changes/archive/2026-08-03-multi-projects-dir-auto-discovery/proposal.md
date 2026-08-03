## Why

Prior to this change, indexing multiple Claude Code environments (e.g. `~/.claude-personal`, `~/.claude-work`) required manually exporting `SESSION_INDEX_PROJECTS` as a colon-separated list in `.zshrc`, per this project's own README instructions.

That manual step turns out to be unnecessary: sibling environments already live at a predictable, discoverable location (`~/.claude-*/projects`). There's no need to ask users to compute and export that list themselves when the tool can just find it — convention over configuration. That realization is the motivation for this change.

The existing `multi-projects-dir` spec documents `SESSION_INDEX_PROJECTS`, `projects_dirs`/`projects_dir` in `config.json`, and `CLAUDE_CONFIG_DIR` as explicit ways to configure multiple directories, but has no scenario for the no-explicit-config case — which is exactly the case this change adds behavior for.

## What Changes

- `get_projects_dirs()`'s final fallback (previously `[~/.claude/projects]` only, when nothing else is configured) now also globs sibling `~/.claude-*/projects` directories and includes them.
- Every priority tier above the fallback (overrides → `SESSION_INDEX_PROJECTS` → `config.json` `projects_dirs`/`projects_dir` → `CLAUDE_CONFIG_DIR`) is unchanged and still takes precedence — this only fires when none of those are set.
- `SESSION_INDEX_PROJECTS` remains supported, reframed in docs as an explicit override for users who want a different set than what's actually on disk, rather than a requirement for multi-env support.
- `CLAUDE.md`, `README.md`, and `skills/session-index/SKILL.md` updated to describe automatic discovery as the new default.

## Capabilities

### Modified Capabilities

- `multi-projects-dir`: add a requirement covering automatic discovery of sibling `~/.claude-*/projects` directories when no explicit configuration is present.

## Impact

- **`session_index/config.py`**: `get_projects_dirs()` fallback branch only — no signature or priority-order changes to the function.
- **`session_index/indexer.py`, `topic_capture.py`, `cli.py`**: no changes needed. All three already resolve directories through `get_projects_dirs()` with no override, so they inherit the new fallback automatically. Missing directories are already skipped defensively (`if not projects_dir.exists(): continue`) in both the indexer and `topic_capture.py`, so a stale or unrelated `~/.claude-*/projects` glob hit is a no-op rather than an error.
- **`get_project_names()`**: no change needed — it already iterates `get_projects_dirs()` and inherits the new discovery for free.
- **`get_projects_dir()`** (singular, legacy accessor): unaffected — its only caller (`indexer.py` `main()`) invokes it exclusively with an explicit `--projects-dir` override, never on the no-args default path.
- **`CLAUDE.md`, `README.md`, `skills/session-index/SKILL.md`**: updated to document auto-discovery as the default and reframe `SESSION_INDEX_PROJECTS` as an override.
- No schema changes, no CLI flag changes, no breaking changes to existing configured setups.
