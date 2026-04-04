"""Parse Chinese Markdown analysis reports into structured sections."""

import re
from pathlib import Path


def parse_report(report_path: str) -> dict:
    """Parse a *_zh.md report file into structured data.

    Returns dict with keys:
      ticker, company, date, rating, sections, key_sections
    """
    path = Path(report_path)
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")

    # --- Extract metadata from filename: {TICKER}_{DATE}_zh.md ---
    filename = path.stem  # e.g. "NIO_2026-04-04_zh"
    parts = filename.rsplit("_", 2)
    ticker = parts[0] if len(parts) >= 3 else "UNKNOWN"
    date = parts[1] if len(parts) >= 3 else "UNKNOWN"

    # --- Extract company name from first H1 ---
    company = ""
    title_match = re.search(r"^#\s+.+[（(](.+?)[）)]", text, re.MULTILINE)
    if title_match:
        company = title_match.group(1)

    # --- Extract rating from "# **卖出（Sell）**" pattern ---
    rating = ""
    rating_match = re.search(r"^#\s+\*\*(.+?)\*\*", text, re.MULTILINE)
    if rating_match:
        rating = rating_match.group(1)

    # --- Parse into sections ---
    sections: list[dict] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Skip empty lines
        if not stripped:
            i += 1
            continue

        # Divider: ---
        if re.match(r"^-{3,}\s*$", stripped):
            sections.append({
                "type": "divider",
                "level": 0,
                "text": "",
                "raw": stripped,
            })
            i += 1
            continue

        # Headings: # ## ###
        heading_match = re.match(r"^(#{1,3})\s+(.+)$", stripped)
        if heading_match:
            level = len(heading_match.group(1))
            raw_text = heading_match.group(2)
            # Strip bold markers for TTS
            clean_text = re.sub(r"\*\*(.+?)\*\*", r"\1", raw_text)
            section_type = "title" if level == 1 and not sections else "heading"

            # Detect rating card: "# **卖出（Sell）**"
            if level == 1 and re.search(r"(卖出|买入|持有|增持|减持)", clean_text):
                section_type = "rating_card"

            sections.append({
                "type": section_type,
                "level": level,
                "text": clean_text,
                "raw": stripped,
            })
            i += 1
            continue

        # Table: lines starting with |
        if stripped.startswith("|"):
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i].strip())
                i += 1
            rows = _parse_table(table_lines)
            # Build TTS text from table rows (skip separator row)
            tts_parts = []
            for row in rows:
                tts_parts.append("，".join(cell for cell in row if cell.strip()))
            sections.append({
                "type": "table",
                "level": 0,
                "text": "。".join(tts_parts),
                "raw": "\n".join(table_lines),
                "rows": rows,
            })
            continue

        # Blockquote: > ...
        if stripped.startswith(">"):
            quote_text = re.sub(r"^>\s*", "", stripped)
            # Strip bold/italic markers
            quote_text = re.sub(r"\*\*(.+?)\*\*", r"\1", quote_text)
            quote_text = re.sub(r"\*(.+?)\*", r"\1", quote_text)
            sections.append({
                "type": "paragraph",
                "level": 0,
                "text": quote_text,
                "raw": stripped,
            })
            i += 1
            continue

        # Regular paragraph: collect consecutive non-empty, non-special lines
        para_lines = []
        while i < len(lines):
            l = lines[i].strip()
            if not l or l.startswith("#") or l.startswith("|") or re.match(r"^-{3,}", l):
                break
            para_lines.append(l)
            i += 1
        if para_lines:
            raw = "\n".join(para_lines)
            # Strip markdown formatting for TTS
            clean = raw
            clean = re.sub(r"\*\*(.+?)\*\*", r"\1", clean)
            clean = re.sub(r"\*(.+?)\*", r"\1", clean)
            clean = re.sub(r"`(.+?)`", r"\1", clean)
            clean = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", clean)
            # Strip numbered list prefixes for cleaner TTS
            clean = re.sub(r"^\d+\.\s+", "", clean, flags=re.MULTILINE)
            sections.append({
                "type": "paragraph",
                "level": 0,
                "text": clean,
                "raw": raw,
            })
            continue

        i += 1

    # --- Extract key sections for short version ---
    key_sections = _extract_key_sections(sections, rating)

    return {
        "ticker": ticker,
        "company": company,
        "date": date,
        "rating": rating,
        "sections": sections,
        "key_sections": key_sections,
    }


def _parse_table(lines: list[str]) -> list[list[str]]:
    """Parse Markdown table lines into a list of row lists. Skips separator rows."""
    rows = []
    for line in lines:
        # Skip separator row (|---|---|)
        if re.match(r"^\|[\s\-:|]+\|$", line):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        # Strip bold markers
        cells = [re.sub(r"\*\*(.+?)\*\*", r"\1", c) for c in cells]
        rows.append(cells)
    return rows


def _extract_key_sections(sections: list[dict], rating: str) -> list[dict]:
    """Extract core sections for the short video version.

    Selects: title+disclaimer, rating, top 3 investment arguments, conclusion.
    Target: 250-400 Chinese characters total.
    """
    key: list[dict] = []

    # 1. Title (first section of type "title")
    for s in sections:
        if s["type"] == "title":
            key.append(s)
            break

    # 2. Disclaimer (first paragraph containing "免责声明")
    for s in sections:
        if s["type"] == "paragraph" and "免责声明" in s["text"]:
            key.append(s)
            break

    # 3. Rating card
    for s in sections:
        if s["type"] == "rating_card":
            key.append(s)
            break

    # 2. Find "投资论点" or "为何" section and grab the first 3 points after it
    in_thesis = False
    point_count = 0
    for s in sections:
        if s["type"] == "heading" and ("投资论点" in s["text"] or "为何" in s["text"]):
            in_thesis = True
            key.append(s)
            continue
        if in_thesis and s["type"] == "paragraph" and point_count < 3:
            key.append(s)
            point_count += 1
        if point_count >= 3:
            break

    # 3. Find conclusion (研究经理决策 or 交易员判定)
    for s in sections:
        if s["type"] == "paragraph" and ("研究经理决策" in s["text"] or "交易员判定" in s["text"]):
            key.append(s)
            break

    return key
