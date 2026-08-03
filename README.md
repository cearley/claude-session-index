# Claude session index

**Every Claude Code session you've ever had, searchable in under a second.**

You've built things across hundreds of sessions. Solved problems, hit walls, found workarounds. But sessions disappear into `~/.claude/projects/` as unlabeled JSONL files — thousands of them, unsearchable, forgettable. This tool indexes them all into a fast SQLite database with full-text search, conversation retrieval, analytics, and cross-session synthesis.

Ask "what did I try last time I debugged webhooks?" and get an actual answer.

**This is a fork** of [lee-fuhr/claude-session-index](https://github.com/lee-fuhr/claude-session-index) that adds **multi-environment support**: index sessions from multiple Claude Code home directories (e.g. work + personal) into one database, tagged and filterable with `--env`. See [Multiple Claude environments](#multiple-claude-environments). Everything else works the same as upstream. Install via `uv tool install git+...` below, not `pip install claude-session-index` — that PyPI name still belongs to upstream.

---

## Quick start

```bash
uv tool install git+https://github.com/cearley/claude-session-index
```

(Not `pip install claude-session-index` — that name on PyPI is upstream's package, not this fork.)

Then install the Claude Code skill:

```bash
npx skills add cearley/claude-session-index
```

Or copy it manually:

```bash
cp skills/session-index/SKILL.md .claude/skills/session-index.md
```

That's it. The first time you ask a question, it auto-indexes all your existing sessions. After that, queries return in milliseconds.

---

## How it works (for you)

The interface is your Claude Code conversation. You ask questions naturally, Claude translates them into searches, and gives you conversational answers.

### "Didn't we discuss browser control recently?"

Claude searches your sessions, finds the matches, and tells you:

> You discussed browser control in 3 sessions last week. The most relevant was on Jan 18 where you figured out that synthetic MouseEvent dispatch bypasses the framework's event handling. The key insight was that the submit button was a `<div>`, not a `<button>`.
>
> → `claude --resume a5b111c6-dca0-4ee9-b237-74b75baf13cd`

### "What have I tried for form automation? What actually worked?"

Claude searches across sessions, extracts the relevant conversations, and synthesizes:

> **Approaches tried:** element.click() → failed (framework intercepts). Coordinate-based clicking → failed (dynamic elements). Synthetic MouseEvent dispatch → success.
>
> **What worked:** Native OS-level clicking for all button interaction. Persistent browser profiles for session continuity.
>
> **What failed:** All JavaScript-based clicking — the framework intercepts and blocks it.
>
> Sources: 5 sessions spanning Jan 10–Feb 1
> → `claude --resume abc123...`
> → `claude --resume def456...`

### "How did I spend my week?"

> 89 sessions this week. 302 hours total.
>
> Windmill Labs: 2 sessions, 47h
> GridSync: 2 sessions, 17h
> NovaTech: 4 sessions, 7h
>
> Top tools: Bash (3,214), Read (2,126), Edit (1,718)
> Task agent usage up 142% from last week.

Every answer includes `claude --resume` links so you can jump straight back into any session.

---

## What it does under the hood

1. **Indexes** all your Claude Code sessions into SQLite with FTS5 full-text search
2. **Searches** by content, client, project, tool, agent, tag, or date — results in milliseconds
3. **Retrieves context** — actual conversation exchanges (user + assistant), not just metadata
4. **Analyzes** your usage — time per client, tool trends, session frequency, topic patterns
5. **Synthesizes** across sessions — "What approaches have I tried for X?" via in-session Haiku subagent (no extra API cost)
6. **Tracks topics** live during sessions via Claude Code hooks

---

## The CLI

The skill handles the conversational interface. But if you want direct access from a terminal, everything goes through `sessions`:

```bash
# Search — just type what you're looking for
sessions "webhook debugging"
sessions "webhook" --context              # with conversation excerpts

# Browse a conversation
sessions context <id> "term"              # exchanges matching a term
sessions context <id>                     # all exchanges

# Analytics
sessions analytics                        # overall stats
sessions analytics --client "Acme"        # per-client
sessions analytics --week                 # this week
sessions analytics --month                # this month

# Synthesis (requires anthropic package + API key for standalone use)
sessions synthesize "topic"               # cross-session intelligence

# Browse & filter
sessions recent 20                        # last N sessions
sessions find --client "Acme"             # filter by client
sessions find --tool Task --week          # filter by tool + date
sessions topics <session_id>              # topic timeline
sessions tools                            # top tools across sessions
sessions stats                            # database overview

# Indexing
sessions index                            # index new/modified sessions
sessions index --backfill                 # re-index everything
```

Plain text defaults to search — `sessions "webhook debugging"` just works, no subcommand needed.

### CLI output

Search results look like this:

```
🔍 3 results for "silent failure"

  ◆ a5b111c6 · (unnamed)
    2026-01-18 · my-project · 51 exchanges
    "...This was a silent failure - appeared to work but didn't..."
    → claude --resume a5b111c6-dca0-4ee9-b237-74b75baf13cd

  ◆ 7b22239e · (unnamed)
    2026-01-18 · my-project · 50 exchanges
    "...The phrase 'silent failure, which is the ultimate sin'
    captures the core requirement: systems must fail loudly..."
    → claude --resume 7b22239e-9f90-466f-ad92-849840b2a6fd
```

Conversation context shows the actual chat:

```
╭─── Build automation debugging ─────────────────
│ 2026-01-20 · my-project · 96 exchanges · 7min
│ → claude --resume a5b111c6-dca0-4ee9-b237-74b75baf13cd
╰────────────────────────────────────────────────

  ┌─ Jan 20, 19:14 ──────────────────────────────
  │
  │  🧑 Breakthrough session. Successfully submitted forms #32 and #33
  │     using synthetic MouseEvent dispatch to bypass the framework's
  │     event handling.
  │
  │  🤖 I'll process these findings. Let me search for existing patterns...
  │     [Grep: framework|zone\.js|MouseEvent|click]
  │     [Read: /path/to/automation/docs.md]
  │
  └────────────────────────────────────────────────
```

Tool calls get collapsed into readable one-liners — `[Read: path]`, `[Edit: path]`, `[Bash: command]`, `[Task: "description" → agent]` — so you can follow the conversation without drowning in JSON.

---

## Live topic tracking

Capture what you're working on during sessions via Claude Code hooks. Topics get indexed for search.

Add to `~/.claude/settings.json` (or merge with your existing hooks):

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "session-topic-capture UserPromptSubmit"
          }
        ]
      }
    ],
    "PreCompact": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "session-topic-capture PreCompact"
          }
        ]
      }
    ],
    "SessionEnd": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "session-topic-capture SessionEnd"
          }
        ]
      }
    ]
  }
}
```

Topics are captured every 10 exchanges, before compaction, and at session end.

### Background indexing (macOS)

Keep the index fresh automatically:

```bash
cp launchagent/com.session-indexer.plist ~/Library/LaunchAgents/
# Edit the plist to point to your Python path
launchctl load ~/Library/LaunchAgents/com.session-indexer.plist
```

Runs `session-index --incremental` every 30 minutes. Only processes new or modified sessions.

---

## Configuration

Works out of the box with sensible defaults. All paths are configurable.

### Priority order

1. CLI flags (`--db-path`, `--projects-dir` (repeatable))
2. Environment variables (`SESSION_INDEX_DB`, `SESSION_INDEX_PROJECTS`, `SESSION_INDEX_TOPICS`)
3. Config file (`~/.session-index/config.json`)
4. `CLAUDE_CONFIG_DIR` (if set, derives default projects and topics paths)
5. Defaults

### Default paths

| What | Default location |
|------|-----------------|
| Database | `~/.session-index/sessions.db` |
| Sessions | `$CLAUDE_CONFIG_DIR/projects/` or `~/.claude/projects/` |
| Topics | `$CLAUDE_CONFIG_DIR/session-topics/` or `~/.claude/session-topics/` |
| Config | `~/.session-index/config.json` |

### Multiple Claude environments

If you run multiple Claude Code environments (e.g., `~/.claude-personal`, `~/.claude-work`), this tool finds them on its own — no shell integration or configuration needed. With nothing set, it globs `~/.claude-*/projects` alongside the default `~/.claude/projects` and indexes them all into one database.

To index a different set than what's on disk, override explicitly:

```bash
# Via environment variable (colon-separated)
export SESSION_INDEX_PROJECTS=~/.claude-personal/projects:~/.claude-work/projects

# Or via config file
{
  "projects_dirs": [
    "~/.claude-personal/projects",
    "~/.claude-work/projects"
  ]
}
```

Each session is tagged with an `env:<name>` label. Filter by environment using `--env`:

```bash
sessions recent --env personal         # sessions from ~/.claude-personal
sessions recent --env current          # sessions from $CLAUDE_CONFIG_DIR
sessions find --week --env work
sessions analytics --month --env work
```

`--env current` resolves to `CLAUDE_CONFIG_DIR` at runtime — useful in shell aliases.

### Multi-machine syncing

To get one merged, queryable index across *physical machines* (not just local environments), sync each machine's raw session directories to the others using whatever sync tool you already use (Syncthing, Dropbox, iCloud Drive, rsync — this project doesn't manage the sync itself, same as it doesn't manage `~/.claude-*/projects`).

**Example:** a MacBook Pro with three local environments (`~/.claude-bedrock`, `~/.claude-personal`, `~/.claude-work`) and a Mac Studio with two (`~/.claude-bedrock`, `~/.claude-work` — no `personal`). Each machine's `~/SessionSync/` holds *only inbound* copies of the other machine's environments — nothing of your own ever lands there:

```
On the Mac Studio:                          On the MacBook Pro:
~/SessionSync/macbook-pro/                  ~/SessionSync/mac-studio/
  .claude-bedrock/projects/  ← from MBP       .claude-bedrock/projects/  ← from Studio
  .claude-personal/projects/ ← from MBP       .claude-work/projects/     ← from Studio
  .claude-work/projects/     ← from MBP
```

With Syncthing, that's one Folder per (origin machine × environment) pair — 3 shared out from the MacBook Pro, 2 from the Mac Studio:

- On the **origin** machine, the Folder's local path is the real, live environment directory (e.g. `~/.claude-bedrock/projects`), type **Send Only**.
- On the **peer** machine, the same shared Folder gets its own local path — `~/SessionSync/macbook-pro/.claude-bedrock/projects` — type **Receive Only**.

Send Only / Receive Only matters, not just as a default: it guarantees a peer's mirrored copy can never write back into your live `~/.claude-*/projects`, which is Claude Code's actual working directory. Keep the leading dot on the mirrored environment folder names (`.claude-bedrock`, not `claude-bedrock`) so the `env:<name>` label renders identically whether a session came from the local copy or a synced peer copy.

On each machine, add the **peer** machines' synced folders — not your own — to `projects_dirs`, and map each to a friendly name in `machine_names`. Multiple directories can (and often will) map to the same machine, since one physical machine can have several environments:

MacBook Pro's `~/.session-index/config.json`:

```json
{
  "projects_dirs": [
    "~/.claude-bedrock/projects",
    "~/.claude-personal/projects",
    "~/.claude-work/projects",
    "~/SessionSync/mac-studio/.claude-bedrock/projects",
    "~/SessionSync/mac-studio/.claude-work/projects"
  ],
  "machine_names": {
    "~/SessionSync/mac-studio/.claude-bedrock/projects": "mac-studio",
    "~/SessionSync/mac-studio/.claude-work/projects": "mac-studio"
  },
  "machine_name": "macbook-pro"
}
```

Mac Studio's `~/.session-index/config.json`:

```json
{
  "projects_dirs": [
    "~/.claude-bedrock/projects",
    "~/.claude-work/projects",
    "~/SessionSync/macbook-pro/.claude-bedrock/projects",
    "~/SessionSync/macbook-pro/.claude-personal/projects",
    "~/SessionSync/macbook-pro/.claude-work/projects"
  ],
  "machine_names": {
    "~/SessionSync/macbook-pro/.claude-bedrock/projects": "macbook-pro",
    "~/SessionSync/macbook-pro/.claude-personal/projects": "macbook-pro",
    "~/SessionSync/macbook-pro/.claude-work/projects": "macbook-pro"
  },
  "machine_name": "mac-studio"
}
```

> **Don't add your own machine's synced mirror of itself.** Your local sessions are already covered by your local `~/.claude-*/projects` directories directly; adding both paths for the same origin causes the `machine` label assigned to those sessions to flap between runs, depending on directory-scan order. (This shouldn't come up with the Send Only / Receive Only setup above, since nothing of your own ever lands in your own `~/SessionSync/` — but it's an easy mistake if you set sync up differently.)

Run `sessions index --backfill` on each machine after adding a new peer directory so its sessions get picked up (and their `machine` label backfilled if you're upgrading an existing database). Each session is tagged with a `machine:<name>` label alongside `env:<name>`, and filterable the same way:

```bash
sessions recent --machine mac-studio
sessions recent --machine current      # sessions from this machine
sessions find --week --machine mac-studio
sessions analytics --month --machine mac-studio
```

An unmapped `projects_dirs` entry falls back to a name derived from its path (with a warning printed during indexing) rather than being silently mislabeled as the local machine — add it to `machine_names` to fix.

### Optional config file

```json
{
  "projects_dirs": ["~/.claude-personal/projects", "~/.claude-work/projects"],
  "db_path": "~/.session-index/sessions.db",
  "topics_dir": "~/.claude/session-topics",
  "clients": ["Acme Corp", "Internal"],
  "project_names": {
    "-Users-me-projects-myapp": "My App"
  },
  "machine_names": {
    "~/SessionSync/imac-work/projects": "imac-work"
  },
  "machine_name": "macbook-personal"
}
```

Single-path `"projects_dir"` still works for backward compatibility.

- **`clients`** — Optional. If provided, sessions are auto-tagged with matching client names. If empty, client detection is skipped.
- **`project_names`** — Optional. Maps Claude's directory-based project names to friendly labels. If empty, auto-generates from directory names.
- **`machine_names`** — Optional. Maps a `projects_dir` path to a friendly machine label, for directories synced in from other machines. Unmapped local default directories fall back to `machine_name` or the local hostname; unmapped non-default directories fall back to a path-derived label with a warning.
- **`machine_name`** — Optional. Overrides this machine's own label (used for its local default directories). Falls back to the local hostname if unset.

---

## How it works (technically)

```
~/.claude/projects/          session-index              Your conversation
  ├── -project-a/              ┌──────────┐
  │   ├── abc123.jsonl ──────▶│ SQLite   │◀──── "Didn't we discuss X?"
  │   └── def456.jsonl ──────▶│ + FTS5   │◀──── "How'd I spend my week?"
  ├── -project-b/              └──────────┘◀──── "What worked for Y?"
  │   └── ghi789.jsonl ──────▶     │
  └── ...                          │
                                   ▼
                            sessions.db
                          ┌─────────────────┐
                          │ sessions        │  metadata, timestamps, tools
                          │ session_content │  FTS5 full-text index
                          │ session_topics  │  live topic timeline
                          │ session_tools   │  tool usage per session
                          │ session_agents  │  agent invocations
                          └─────────────────┘
```

The indexer parses JSONL files once, extracts metadata (timestamps, tools, agents, topics), and stores everything in SQLite. FTS5 handles the full-text search. Context retrieval reads JSONL on-demand — only the files you ask about.

## Tech stack

- **Python 3.10+** — stdlib only for core features (no dependencies)
- **SQLite + FTS5** — fast full-text search, no server needed
- **Anthropic SDK** — optional, only for standalone `synthesize` command

---

## Requirements

- Python 3.10+
- Claude Code (the sessions to index)
- That's it. No server, no database setup, no API keys for core features.

---

Originally built by [Lee Fuhr](https://leefuhr.com). This fork is maintained by [Craig Earley](https://github.com/cearley).
