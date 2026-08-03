## ADDED Requirements

### Requirement: Automatic discovery of sibling environments when unconfigured
When no explicit configuration is present (no `overrides`, no `SESSION_INDEX_PROJECTS`, no `projects_dirs`/`projects_dir` in `config.json`, no `CLAUDE_CONFIG_DIR`), the system SHALL discover multi-environment directories on its own by globbing sibling `~/.claude-*/projects` directories, rather than requiring shell-side cooperation to export them.

#### Scenario: Sibling environments present, nothing explicitly configured
- **WHEN** no explicit configuration is present and `~/.claude-personal/projects` and `~/.claude-work/projects` both exist on disk
- **THEN** the system SHALL index sessions from `~/.claude/projects`, `~/.claude-personal/projects`, and `~/.claude-work/projects`

#### Scenario: No sibling environments present
- **WHEN** no explicit configuration is present and no `~/.claude-*/projects` directories exist besides the default
- **THEN** the system SHALL index only `~/.claude/projects`, unchanged from prior behavior

#### Scenario: Explicit configuration takes precedence over discovery
- **WHEN** `SESSION_INDEX_PROJECTS`, `config.json` (`projects_dirs` or `projects_dir`), or `CLAUDE_CONFIG_DIR` is set
- **THEN** the system SHALL use that configuration exactly as specified and SHALL NOT additionally glob for sibling `~/.claude-*/projects` directories
