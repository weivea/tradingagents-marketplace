"""Markdown journal file storage per account per day."""
from __future__ import annotations

from pathlib import Path

DEFAULT_BASE = Path.home() / ".paper_trading"


def _journal_path(base_dir: Path, account_id: str, date: str) -> Path:
    return base_dir / "journals" / f"{account_id}-{date}.md"


def append_journal(
    account_id: str, date: str, markdown: str, *, base_dir: Path | None = None,
) -> dict:
    base = base_dir or DEFAULT_BASE
    path = _journal_path(base, account_id, date)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(markdown.rstrip() + "\n\n")
    return {"ok": True, "path": str(path)}


def read_journal(
    account_id: str, date: str, *, base_dir: Path | None = None,
) -> str:
    base = base_dir or DEFAULT_BASE
    path = _journal_path(base, account_id, date)
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")
