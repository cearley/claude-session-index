## Purpose

Defines requirements for tagging each indexed session with the physical machine it originated from, so sessions synced in from multiple machines into a merged index remain distinguishable and filterable, the same way `multi-projects-dir` already distinguishes local environments.

## ADDED Requirements

### Requirement: Config accepts a machine name mapping
The system SHALL accept a `machine_names` mapping in `~/.session-index/config.json` from a configured projects directory path to a friendly machine label. The system SHALL also accept an optional top-level `machine_name` value overriding the local machine's own label.

#### Scenario: Explicit mapping for a projects directory
- **WHEN** `config.json` contains `"machine_names": {"/Users/craig/SessionSync/imac-work/projects": "imac-work"}`
- **THEN** sessions indexed from that directory SHALL be recorded with machine name `imac-work`

#### Scenario: Local machine label override
- **WHEN** `config.json` contains `"machine_name": "macbook-personal"` and no explicit `machine_names` entry exists for the local default projects directory
- **THEN** sessions indexed from the local default directory SHALL be recorded with machine name `macbook-personal`

### Requirement: Machine name resolves with a defined fallback order
For each configured projects directory, the system SHALL resolve a machine name in this order: (1) an explicit entry in `machine_names` keyed by that directory's path; (2) if the directory is one of the local default/auto-discovered directories (the default `~/.claude/projects` or a sibling `~/.claude-*/projects`), the configured `machine_name` value, or the local hostname if `machine_name` is unset; (3) otherwise, a label derived from the directory's path, accompanied by a warning that the directory is unmapped.

#### Scenario: Unmapped local default directory falls back to hostname
- **WHEN** no `machine_names` entry and no `machine_name` override exist, and sessions are indexed from the default `~/.claude/projects`
- **THEN** those sessions SHALL be recorded with the local machine's hostname as the machine name

#### Scenario: Unmapped non-default directory produces a warning, not a silent mislabel
- **WHEN** a projects directory outside the local default set (e.g. a synced peer folder) has no corresponding `machine_names` entry
- **THEN** the system SHALL derive a fallback label from that directory's path, SHALL NOT label it with the local machine's own name, and SHALL print a warning during indexing

### Requirement: Sessions record their resolved machine name
Each indexed session SHALL store the resolved machine name (per the fallback order above) as `machine`, computed once at index time.

#### Scenario: machine populated on index
- **WHEN** a session JSONL file is indexed from a projects directory that resolves to machine name `imac-work`
- **THEN** the session record SHALL have `machine` set to `imac-work`

#### Scenario: machine backfilled for existing sessions
- **WHEN** a user runs `sessions index --backfill` after upgrading to this version
- **THEN** `machine` SHALL be populated for all existing sessions whose `machine` is currently unset, without requiring a full reindex of unchanged files

### Requirement: --machine flag filters to a specific machine
The `--machine` flag on `recent`, `find`, and `analytics` commands SHALL restrict results to sessions whose stored `machine` value contains the given substring.

#### Scenario: --machine with substring match
- **WHEN** the user runs `sessions recent --machine work`
- **THEN** the system SHALL return only sessions whose `machine` contains `"work"`

#### Scenario: --machine current resolves to the local machine
- **WHEN** the user runs `sessions recent --machine current`
- **THEN** the system SHALL filter to sessions whose `machine` equals the name that would currently be resolved for this machine's local default projects directory

### Requirement: Session display includes machine label
When sessions from more than one machine are present in results, each result SHALL include a `machine:<name>` label alongside any existing `env:<name>` label.

#### Scenario: machine label in output
- **WHEN** a session result has `machine` of `imac-work`
- **THEN** the display SHALL include the label `machine:imac-work` in the session summary line
