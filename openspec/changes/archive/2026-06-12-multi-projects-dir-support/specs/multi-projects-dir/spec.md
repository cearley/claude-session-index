## ADDED Requirements

### Requirement: Config accepts multiple project directories
The system SHALL accept a list of Claude projects directories in place of a single directory. A single path value SHALL be treated as a one-element list for backward compatibility.

#### Scenario: Single path in config (backward compat)
- **WHEN** `~/.session-index/config.json` contains `"projects_dir": "/path/to/projects"`
- **THEN** the system SHALL index that one directory, unchanged from prior behavior

#### Scenario: Multiple paths via config file
- **WHEN** `~/.session-index/config.json` contains `"projects_dirs": ["/path/a", "/path/b"]`
- **THEN** the system SHALL index sessions from both directories into a single database

#### Scenario: Multiple paths via environment variable
- **WHEN** `SESSION_INDEX_PROJECTS` is set to `/path/a:/path/b` (colon-separated)
- **THEN** the system SHALL index sessions from both `/path/a` and `/path/b`

#### Scenario: Single path via environment variable (backward compat)
- **WHEN** `SESSION_INDEX_PROJECTS` is set to a single path with no colon
- **THEN** the system SHALL index that one directory, unchanged from prior behavior

### Requirement: Indexer walks all configured directories
The system SHALL index sessions from every configured projects directory in a single incremental or backfill pass.

#### Scenario: Backfill across multiple directories
- **WHEN** the user runs `sessions index --backfill` with two directories configured
- **THEN** the system SHALL index all sessions found in both directories into the same database

#### Scenario: Incremental index across multiple directories
- **WHEN** the user runs `sessions index` with two directories configured
- **THEN** the system SHALL check both directories for new or modified sessions and index any changes

#### Scenario: Session ID uniqueness across environments
- **WHEN** two configured directories contain sessions with distinct UUID filenames
- **THEN** the system SHALL index all sessions without collision, using the UUID as the primary key

### Requirement: CLI flag accepts multiple project directories
The `--projects-dir` flag SHALL be repeatable to allow specifying multiple directories from the command line.

#### Scenario: Multiple --projects-dir flags
- **WHEN** the user runs `sessions --projects-dir /path/a --projects-dir /path/b index`
- **THEN** the system SHALL index sessions from both `/path/a` and `/path/b`

### Requirement: Sessions record their source environment
Each indexed session SHALL store the projects directory it was found in as `source_env`. This enables per-environment filtering without relying on file path string matching at query time.

#### Scenario: source_env populated on index
- **WHEN** a session JSONL file is indexed from `/path/a/project/session.jsonl`
- **THEN** the session record SHALL have `source_env` set to `/path/a`

#### Scenario: source_env backfilled for existing sessions
- **WHEN** a user runs `sessions index --backfill` after upgrading to this version
- **THEN** `source_env` SHALL be populated for all existing sessions by matching `file_path` against the configured `projects_dirs`

### Requirement: Queries default to all environments
Browse and filter commands (`recent`, `find`, `analytics`) SHALL return results from all configured environments by default.

#### Scenario: recent with no filter
- **WHEN** the user runs `sessions recent`
- **THEN** the system SHALL return the most recent sessions across all indexed environments

### Requirement: --env flag filters to a specific environment
The `--env` flag on `recent`, `find`, and `analytics` commands SHALL restrict results to sessions whose `source_env` contains the given substring.

#### Scenario: --env with substring match
- **WHEN** the user runs `sessions recent --env personal`
- **THEN** the system SHALL return only sessions where `source_env` contains `"personal"` (e.g., `~/.claude-personal/projects`)

#### Scenario: --env current resolves to CLAUDE_CONFIG_DIR
- **WHEN** the user runs `sessions recent --env current` and `CLAUDE_CONFIG_DIR` is set
- **THEN** the system SHALL filter to sessions whose `source_env` matches `CLAUDE_CONFIG_DIR`

#### Scenario: --env current without CLAUDE_CONFIG_DIR
- **WHEN** the user runs `sessions recent --env current` and `CLAUDE_CONFIG_DIR` is not set
- **THEN** the system SHALL print a clear error: `--env current requires CLAUDE_CONFIG_DIR to be set`

### Requirement: Session display includes environment label
When sessions from multiple environments are present in results, each result SHALL include an `env:<name>` label derived from the tail of `source_env`.

#### Scenario: env label in output
- **WHEN** a session result has `source_env` of `/Users/craig/.claude-personal/projects`
- **THEN** the display SHALL include the label `env:personal` in the session summary line

#### Scenario: env label derivation
- **WHEN** `source_env` is `/Users/craig/.claude-work/projects`
- **THEN** the label SHALL be `env:work` (last path segment of the parent directory, stripped of `claude-` prefix if present)
