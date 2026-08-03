## 1. Config Layer

- [x] 1.1 In `get_projects_dirs()`, change the final fallback (fired only when overrides, `SESSION_INDEX_PROJECTS`, `config.json`, and `CLAUDE_CONFIG_DIR` are all unset) to glob `~/.claude-*/projects` and prepend `~/.claude/projects`
- [x] 1.2 Confirm `get_project_names()` needs no change — it already resolves directories via `get_projects_dirs()`
- [x] 1.3 Confirm `get_projects_dir()` (singular) needs no change — its only call site always passes an explicit override

## 2. Documentation

- [x] 2.1 Update `CLAUDE.md` config table and multi-environment section to describe auto-discovery as the default, `SESSION_INDEX_PROJECTS` as an override
- [x] 2.2 Update `README.md` "Multiple Claude environments" section to match
- [x] 2.3 Update `skills/session-index/SKILL.md` to match

## 3. Spec

- [x] 3.1 Add an `ADDED Requirements` delta to `specs/multi-projects-dir/spec.md` covering the no-explicit-config discovery scenario

## 4. Manual verification

- [x] 4.1 Verify discovery picks up sibling `~/.claude-*/projects` dirs with a temp-`HOME` script (see review notes)
- [x] 4.2 Verify explicit `SESSION_INDEX_PROJECTS`, `config.json`, and `CLAUDE_CONFIG_DIR` still take precedence over discovery
- [x] 4.3 Verify a `HOME` with no sibling `.claude-*` dirs still returns just `~/.claude/projects`
