---
name: session-index
description: Use when the user asks about past sessions, what they tried before, previous conversations, or wants to search their Claude Code history, measure effort, or synthesize across sessions.
version: 0.4.1
author: Lee Fuhr
contributors:
  - Craig Earley
tags:
  - session-search
  - session-history
  - analytics
  - memory
  - productivity
requires:
  - python3
  - uv
---

# Session index skill

You have access to a session index — a SQLite database with FTS5 full-text search across all Claude Code sessions. Use it whenever the user asks about past sessions, previous conversations, or wants to know what they've tried before.

**The user's interface is this conversation.** They ask naturally ("Didn't we discuss browser control recently?"), you translate to CLI commands, and present results conversationally. They should never need to know the CLI syntax.

## How to handle session queries

### 1. Extract keywords from the question

The user says: "Didn't we discuss browser control recently?"
You search: `sessions "browser control"`

The user says: "What approaches have I tried for form automation?"
You search: `sessions "form automation"`

The user says: "How much time did I spend on Acme this week?"
You run: `sessions analytics --client "Acme" --week`

### 2. Run the right command via Bash

**Search** — find sessions by topic:
```bash
sessions "relevant keywords"
sessions "relevant keywords" --context    # includes conversation excerpts
```

**Context** — read the actual conversation from a session:
```bash
sessions context <session_id> "search term"   # exchanges matching a term
sessions context <session_id>                 # all exchanges
```

**Analytics** — effort, time, tool usage:
```bash
sessions analytics                    # overall
sessions analytics --client "Acme"    # per client
sessions analytics --week             # this week
sessions analytics --month            # this month
sessions analytics --env personal     # one Claude environment
```

**Filter** — find sessions by metadata:
```bash
sessions find --client "Acme"              # by client
sessions find --tool Task --week           # by tool + date
sessions find --project myapp              # by project
sessions find --week --env work            # by date + environment
sessions recent 20                         # last N sessions
sessions recent --env personal             # one Claude environment
sessions recent --env current              # active CLAUDE_CONFIG_DIR environment
```

If the user mentions a specific Claude environment (personal, work, bedrock, etc.), add `--env <name>` to scope results. `--env current` resolves to `CLAUDE_CONFIG_DIR` at runtime. All `find`, `recent`, and `analytics` commands accept `--env`.

### 3. For synthesis ("what worked?", "what have I tried?")

This is the most valuable capability. When the user asks a question that spans multiple sessions:

1. Search: `sessions "topic" -n 10`
2. For the top 3-5 results, extract context: `sessions context <id> "topic" -n 3`
3. Spawn a Task with `model="haiku"` to synthesize:
   - What approaches were tried?
   - What worked / what failed?
   - Recurring patterns?
   - Current state?
4. Present the synthesis conversationally with `claude --resume <id>` links for each source session

This uses an in-session Haiku subagent — no external API key needed.

### 4. Present results conversationally

Don't dump raw CLI output. Summarize:
- "You discussed browser control in 3 sessions last week..."
- "The main approach that worked was..."
- Include `claude --resume <session_id>` links so they can jump back in
- If context is relevant, quote key exchanges

## Installation

```bash
uv tool install git+https://github.com/cearley/claude-session-index
```

First run of any command auto-indexes all existing sessions.

**Multiple Claude environments:** To index several Claude configs into one database, set `SESSION_INDEX_PROJECTS` to a colon-separated list of `projects/` directories, or add `projects_dirs` (list) to `~/.session-index/config.json`:

```bash
export SESSION_INDEX_PROJECTS=~/.claude-personal/projects:~/.claude-work/projects
```

The `--projects-dir` flag is also repeatable for one-off overrides:

```bash
sessions --projects-dir ~/.claude-personal/projects --projects-dir ~/.claude-work/projects index
```

Each session is tagged with an `env:<name>` label (derived from its source directory path).

## Data location

- **Database:** `~/.session-index/sessions.db`
- **Topics:** `~/.claude/session-topics/`
- **Config:** `~/.session-index/config.json` (optional)
