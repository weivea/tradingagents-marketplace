"""Shared markdown discussion file + next_speaker directive parsing."""
from __future__ import annotations

import re
from pathlib import Path

DEFAULT_BASE = Path.home() / ".paper_trading"

VALID_SPEAKERS = {"aggressive", "neutral", "conservative"}
VALID_NEXT = {"aggressive", "neutral", "conservative", "end"}

CHINESE_LABEL = {
    "aggressive": "激进选手",
    "neutral": "中性选手",
    "conservative": "保守选手",
}

NEXT_SPEAKER_RE = re.compile(
    r"<!--\s*next_speaker:\s*(aggressive|neutral|conservative|end)\s*(?:/\s*reason:\s*[^>]*)?-->",
    re.IGNORECASE,
)


def _discussion_path(base_dir: Path, date: str) -> Path:
    return base_dir / "discussions" / f"{date}.md"


def init_discussion(
    date: str, *, pnl_summary: dict[str, float],
    base_dir: Path | None = None, force: bool = False,
) -> dict:
    """Create today's shared discussion markdown file with header + PnL summary.

    pnl_summary keys MUST be one of {"aggressive", "neutral", "conservative"}
    (no currency suffix). Values are interpreted as daily return PERCENTAGES,
    e.g. 1.23 renders as "+1.2%", -0.5 renders as "-0.5%".
    Unknown keys are silently ignored; missing keys are omitted from the header.

    Example:
        init_discussion("2026-04-21",
                        pnl_summary={"aggressive": 0.0,
                                     "neutral": 1.23,
                                     "conservative": -0.5})
        # renders: "**今日战绩** · 激进 +0.0% · 中性 +1.2% · 保守 -0.5%"
    """
    base = base_dir or DEFAULT_BASE
    path = _discussion_path(base, date)
    if path.exists() and not force:
        return {"ok": False, "error_code": "DISCUSSION_EXISTS",
                "message": f"{path} already exists; use force=True to overwrite"}
    path.parent.mkdir(parents=True, exist_ok=True)
    parts = [f"# {date} 交易心得讨论", ""]
    if pnl_summary:
        bits = []
        for key in ("aggressive", "neutral", "conservative"):
            if key in pnl_summary:
                sign = "+" if pnl_summary[key] >= 0 else ""
                bits.append(f"{CHINESE_LABEL[key][:2]} {sign}{pnl_summary[key]:.1f}%")
        parts.append("**今日战绩** · " + " · ".join(bits))
        parts.append("")
    parts.append("---")
    parts.append("")
    path.write_text("\n".join(parts), encoding="utf-8")
    return {"ok": True, "path": str(path)}


def read_discussion(date: str, *, base_dir: Path | None = None) -> str:
    base = base_dir or DEFAULT_BASE
    path = _discussion_path(base, date)
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def append_discussion(
    date: str, *, speaker: str, markdown: str, next_speaker: str,
    reason: str = "", base_dir: Path | None = None,
) -> dict:
    if speaker not in VALID_SPEAKERS:
        raise ValueError(f"Invalid speaker: {speaker}")
    if next_speaker not in VALID_NEXT:
        raise ValueError(f"Invalid next_speaker: {next_speaker}")
    base = base_dir or DEFAULT_BASE
    path = _discussion_path(base, date)
    if not path.exists():
        return {"ok": False, "error_code": "DISCUSSION_NOT_INITIALIZED",
                "message": f"call init_discussion first for {date}"}
    label = CHINESE_LABEL[speaker]
    block = (
        f"**{label}：** {markdown.strip()}\n"
        f"<!-- next_speaker: {next_speaker} / reason: {reason.strip()} -->\n\n"
    )
    with path.open("a", encoding="utf-8") as f:
        f.write(block)
    return {"ok": True, "path": str(path)}


def parse_last_next_speaker(content: str) -> str | None:
    matches = NEXT_SPEAKER_RE.findall(content)
    if not matches:
        return None
    return matches[-1].lower()
