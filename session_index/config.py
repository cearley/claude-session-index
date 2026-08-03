"""Configuration resolution for claude-session-index.

Priority order:
1. Function arguments (passed directly)
2. Environment variables
3. Config file (~/.session-index/config.json)
4. Sensible defaults
"""

import json
import os
import socket
import sys
from pathlib import Path
from typing import Optional

DEFAULTS = {
    "projects_dir": str(Path.home() / ".claude" / "projects"),
    "db_path": str(Path.home() / ".session-index" / "sessions.db"),
    "topics_dir": str(Path.home() / ".claude" / "session-topics"),
    "clients": [],
    "project_names": {},
    "machine_names": {},
    "machine_name": None,
}

CONFIG_FILE = Path.home() / ".session-index" / "config.json"

_cached_config: Optional[dict] = None


def _load_config_file() -> dict:
    """Load config from ~/.session-index/config.json if it exists."""
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def get_config() -> dict:
    """Resolve config from all sources. Result is cached after first call."""
    global _cached_config
    if _cached_config is not None:
        return _cached_config

    # Start with defaults
    config = dict(DEFAULTS)

    # Layer on config file
    file_config = _load_config_file()
    for key, value in file_config.items():
        if key in config and value is not None:
            config[key] = value

    # Layer on environment variables
    env_map = {
        "SESSION_INDEX_PROJECTS": "projects_dir",
        "SESSION_INDEX_DB": "db_path",
        "SESSION_INDEX_TOPICS": "topics_dir",
    }
    for env_key, config_key in env_map.items():
        val = os.environ.get(env_key)
        if val:
            config[config_key] = val

    _cached_config = config
    return config


def get_projects_dirs(overrides: list[str] = None) -> list[Path]:
    """Get all configured projects directories as a list of Paths.

    Priority: overrides → SESSION_INDEX_PROJECTS (colon-sep) →
              config.json projects_dirs (list) → config.json projects_dir →
              CLAUDE_CONFIG_DIR/projects →
              ~/.claude/projects + discovered ~/.claude-*/projects
    """
    if overrides:
        return [Path(p).expanduser() for p in overrides if p]

    env_val = os.environ.get("SESSION_INDEX_PROJECTS")
    if env_val:
        return [Path(p).expanduser() for p in env_val.split(":") if p.strip()]

    file_config = _load_config_file()
    if "projects_dirs" in file_config:
        val = file_config["projects_dirs"]
        if isinstance(val, list):
            return [Path(p).expanduser() for p in val if p]
        elif isinstance(val, str):
            return [Path(val).expanduser()]

    if "projects_dir" in file_config:
        return [Path(file_config["projects_dir"]).expanduser()]

    claude_config = os.environ.get("CLAUDE_CONFIG_DIR")
    if claude_config:
        return [(Path(claude_config) / "projects").expanduser()]

    # No explicit config: default env plus any sibling ~/.claude-<name>
    # directories discovered on disk.
    default_dir = Path.home() / ".claude" / "projects"
    discovered = sorted(Path.home().glob(".claude-*/projects"))
    return [default_dir] + discovered


def get_projects_dir(override: str = None) -> Path:
    """Get projects directory path (single-dir backward-compat accessor)."""
    if override:
        return Path(override).expanduser()
    return Path(get_config()["projects_dir"]).expanduser()


def get_db_path(override: str = None) -> Path:
    """Get database path, creating parent directory if needed."""
    if override:
        p = Path(override).expanduser()
    else:
        p = Path(get_config()["db_path"]).expanduser()
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def get_topics_dir(override: str = None) -> Path:
    """Get topics directory path."""
    if override:
        return Path(override).expanduser()
    return Path(get_config()["topics_dir"]).expanduser()


def get_clients() -> list[str]:
    """Get list of known client names (optional — used for auto-detection)."""
    return get_config().get("clients", [])


def get_project_names() -> dict[str, str]:
    """Get project directory → friendly name mapping.

    If not configured, auto-generates from directory names:
    '-Users-lee-CC-LFI' → 'LFI'
    '-Users-foo-projects-myapp' → 'myapp'
    """
    configured = get_config().get("project_names", {})
    if configured:
        return configured

    # Auto-generate from directory names
    mapping = {}
    for projects_dir in get_projects_dirs():
        if not projects_dir.exists():
            continue
        for d in projects_dir.iterdir():
            if d.is_dir():
                name = d.name
                parts = [p for p in name.split("-") if p]
                if parts:
                    friendly = " ".join(parts[-2:]) if len(parts) > 1 else parts[-1]
                    mapping[name] = friendly

    return mapping


def get_machine_name(projects_dir: Path) -> str:
    """Resolve a friendly machine name for a projects directory.

    Priority:
    1. An explicit `machine_names` config entry keyed by the directory's path.
    2. If the directory is a local default (`~/.claude/projects` or a sibling
       `~/.claude-*/projects`), the configured `machine_name`, or the local
       hostname if unset.
    3. Otherwise (an unmapped, explicitly-added directory — typically a synced
       peer machine's folder), a path-derived fallback label. A warning is
       printed since this usually means a missing `machine_names` entry.
    """
    machine_names = get_config().get("machine_names", {})
    key = str(projects_dir)
    if key in machine_names:
        return machine_names[key]

    default_dir = Path.home() / ".claude" / "projects"
    is_local_default = projects_dir == default_dir or (
        projects_dir.name == "projects"
        and projects_dir.parent.parent == Path.home()
        and projects_dir.parent.name.startswith(".claude-")
    )
    if is_local_default:
        configured = get_config().get("machine_name")
        if configured:
            return configured
        return socket.gethostname().split(".")[0]

    fallback = projects_dir.parent.name or projects_dir.name
    print(
        f"Warning: no machine_names entry for '{projects_dir}' — "
        f"falling back to '{fallback}'. Add it to machine_names in "
        f"~/.session-index/config.json to set an explicit label.",
        file=sys.stderr,
    )
    return fallback


def init_config():
    """Create a default config file if one doesn't exist."""
    if CONFIG_FILE.exists():
        return False

    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(DEFAULTS, indent=2) + "\n")
    return True


def ensure_indexed(db_path: Path = None) -> bool:
    """Auto-index on first use if database is empty or missing.

    Returns True if backfill was triggered.
    """
    import sqlite3

    if db_path is None:
        db_path = get_db_path()

    needs_backfill = False
    if not db_path.exists():
        needs_backfill = True
    else:
        try:
            conn = sqlite3.connect(str(db_path))
            has_table = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'"
            ).fetchone()
            if has_table:
                count = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
                needs_backfill = (count == 0)
            else:
                needs_backfill = True
            conn.close()
        except Exception:
            needs_backfill = True

    if needs_backfill:
        print("\n  First run — indexing all your sessions...")
        print("  (This only happens once.)\n")
        try:
            from session_index.indexer import SessionIndexer
        except ImportError:
            try:
                from .indexer import SessionIndexer
            except ImportError:
                from indexer import SessionIndexer
        indexer = SessionIndexer(db_path=db_path)
        indexer.connect()
        indexer.backfill_all()
        indexer.close()
        return True
    return False
