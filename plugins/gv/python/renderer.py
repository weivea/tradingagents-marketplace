"""Render report sections as images using Pillow.

Full layout: one tall scroll image (1080 x N pixels) + y_map.json.
Short layout: one 1080x1920 image per section.
"""

import asyncio
import json
import re
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from PIL import Image, ImageDraw, ImageFont

from .config import (
    WIDTH, HEIGHT, MARGIN_X,
    BG_COLOR, TEXT_COLOR, HEADING_COLOR, ACCENT_COLOR,
    RATING_SELL_COLOR, RATING_BUY_COLOR, HIGHLIGHT_BG,
    FONT_REGULAR, FONT_BOLD,
    FONT_SIZE_BODY, FONT_SIZE_H1, FONT_SIZE_H2, FONT_SIZE_H3, FONT_SIZE_SMALL,
    LINE_HEIGHT_MULTIPLIER,
    HEADER_HEIGHT, RATING_CARD_HEIGHT, SCROLL_AREA_HEIGHT,
    TEMPLATES_DIR, SHORT_V2_RENDER_WIDTH, SHORT_V2_RENDER_HEIGHT,
)


def _load_font(bold: bool = False, size: int = FONT_SIZE_BODY) -> ImageFont.FreeTypeFont:
    """Load font with CJK support.  Fallback chain covers Windows, macOS, Linux."""
    names = [
        # Configured / Windows
        FONT_BOLD if bold else FONT_REGULAR,
        "msyh.ttc",
        # macOS (full paths required for system fonts)
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
        "/System/Library/Fonts/Supplemental/Songti.ttc",
        # Linux
        "NotoSansCJKsc-Regular.otf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
        # Generic fallback
        "arial.ttf",
    ]
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    """Wrap text to fit within max_width pixels."""
    lines: list[str] = []
    for paragraph in text.split("\n"):
        if not paragraph.strip():
            lines.append("")
            continue
        current = ""
        for char in paragraph:
            test = current + char
            bbox = draw.textbbox((0, 0), test, font=font)
            if bbox[2] - bbox[0] > max_width:
                if current:
                    lines.append(current)
                current = char
            else:
                current = test
        if current:
            lines.append(current)
    return lines


def render_frames(
    sections_path: str,
    layout: str,
    output_dir: str,
) -> dict:
    """Render sections to images.

    Args:
        sections_path: Path to JSON file containing Section list.
        layout: "full" for scroll image, "short" for per-slide images.
        output_dir: Directory to write output images.

    Returns:
        dict with keys: image_paths, y_map_path (full only)
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    with open(sections_path, "r", encoding="utf-8") as f:
        sections = json.load(f)

    if layout == "full":
        return _render_full(sections, out)
    else:
        return _render_short(sections, out)


def _render_full(sections: list[dict], out: Path) -> dict:
    """Render a single tall scroll image for the full version."""
    usable_width = WIDTH - 2 * MARGIN_X
    font_body = _load_font(bold=False, size=FONT_SIZE_BODY)
    font_h1 = _load_font(bold=True, size=FONT_SIZE_H1)
    font_h2 = _load_font(bold=True, size=FONT_SIZE_H2)
    font_h3 = _load_font(bold=True, size=FONT_SIZE_H3)
    line_spacing = int(FONT_SIZE_BODY * LINE_HEIGHT_MULTIPLIER)

    # --- First pass: calculate total height ---
    temp_img = Image.new("RGB", (WIDTH, 100))
    temp_draw = ImageDraw.Draw(temp_img)

    y_map: list[dict] = []  # [{section_index, y_start, y_end}]
    total_height = 40  # top padding

    for idx, section in enumerate(sections):
        y_start = total_height
        section_type = section.get("type", "paragraph")
        text = section.get("text", "")

        if section_type == "divider":
            total_height += 30
        elif section_type in ("title", "heading", "rating_card"):
            level = section.get("level", 2)
            font = {1: font_h1, 2: font_h2, 3: font_h3}.get(level, font_h2)
            wrapped = _wrap_text(temp_draw, text, font, usable_width)
            h = int(font.size * LINE_HEIGHT_MULTIPLIER)
            total_height += len(wrapped) * h + 20  # +20 margin
        elif section_type == "table":
            rows = section.get("rows", [])
            total_height += (len(rows) + 1) * (FONT_SIZE_BODY + 16) + 20
        else:  # paragraph
            wrapped = _wrap_text(temp_draw, text, font_body, usable_width)
            total_height += len(wrapped) * line_spacing + 16

        y_map.append({
            "section_index": idx,
            "y_start": y_start,
            "y_end": total_height,
            "type": section_type,
            "text_preview": text[:50],
        })

    total_height += 60  # bottom padding

    # --- Second pass: actually draw ---
    img = Image.new("RGB", (WIDTH, total_height), BG_COLOR)
    draw = ImageDraw.Draw(img)
    y = 40

    for section in sections:
        section_type = section.get("type", "paragraph")
        text = section.get("text", "")

        if section_type == "divider":
            draw.line([(MARGIN_X, y + 15), (WIDTH - MARGIN_X, y + 15)], fill=ACCENT_COLOR, width=1)
            y += 30

        elif section_type in ("title", "heading", "rating_card"):
            level = section.get("level", 2)
            font = {1: font_h1, 2: font_h2, 3: font_h3}.get(level, font_h2)
            color = HEADING_COLOR
            if section_type == "rating_card":
                color = RATING_SELL_COLOR if "卖出" in text or "减持" in text else (
                    RATING_BUY_COLOR if "买入" in text or "增持" in text else HEADING_COLOR
                )
            # Draw accent bar for headings
            if section_type == "heading":
                draw.rectangle([(MARGIN_X, y + 4), (MARGIN_X + 4, y + font.size - 4)], fill=ACCENT_COLOR)
            wrapped = _wrap_text(draw, text, font, usable_width)
            h = int(font.size * LINE_HEIGHT_MULTIPLIER)
            x_offset = MARGIN_X + (12 if section_type == "heading" else 0)
            for line in wrapped:
                draw.text((x_offset, y), line, font=font, fill=color)
                y += h
            y += 20

        elif section_type == "table":
            rows = section.get("rows", [])
            if rows:
                row_height = FONT_SIZE_BODY + 16
                col_count = max(len(r) for r in rows)
                col_width = usable_width // max(col_count, 1)
                font_table = _load_font(bold=False, size=FONT_SIZE_BODY - 2)
                for ri, row in enumerate(rows):
                    row_y = y + ri * row_height
                    # Alternate row background
                    if ri % 2 == 0:
                        draw.rectangle(
                            [(MARGIN_X, row_y), (WIDTH - MARGIN_X, row_y + row_height)],
                            fill=(15, 20, 50),
                        )
                    for ci, cell in enumerate(row):
                        cx = MARGIN_X + ci * col_width + 8
                        draw.text((cx, row_y + 8), cell, font=font_table, fill=TEXT_COLOR)
                y += len(rows) * row_height + 20

        else:  # paragraph
            wrapped = _wrap_text(draw, text, font_body, usable_width)
            for line in wrapped:
                draw.text((MARGIN_X, y), line, font=font_body, fill=TEXT_COLOR)
                y += line_spacing
            y += 16

    # Save image and y_map
    image_path = out / "scroll.png"
    img.save(str(image_path), "PNG")

    y_map_path = out / "y_map.json"
    with open(y_map_path, "w", encoding="utf-8") as f:
        json.dump(y_map, f, ensure_ascii=False, indent=2)

    return {
        "image_paths": [str(image_path)],
        "y_map_path": str(y_map_path),
    }


def _is_v2_format(sections: list[dict]) -> bool:
    """Detect whether sections use v2 format (headline/body/tts_text) or legacy (text)."""
    if not sections:
        return False
    first = sections[0]
    return "headline" in first and "tts_text" in first


def _build_template_context(
    section: dict,
    idx: int,
    total: int,
    ticker: str,
    date: str,
) -> dict:
    """Build Jinja2 template context from a v2 section."""
    progress_pct = round(((idx + 1) / total) * 100)
    ctx = {
        "headline": section.get("headline", ""),
        "body": section.get("body", ""),
        "highlights": section.get("highlights", []),
        "ticker": ticker,
        "date": date,
        "progress_pct": progress_pct,
        "index": section.get("index", idx),
        "sub_body": section.get("sub_body", ""),
        "metrics": section.get("metrics", []),
    }
    # Rating class
    if section.get("type") == "rating":
        h = section.get("headline", "")
        if "卖出" in h or "减持" in h:
            ctx["rating_class"] = "sell"
        elif "买入" in h or "增持" in h:
            ctx["rating_class"] = "buy"
        else:
            ctx["rating_class"] = "hold"
    # Progress indicator unicode numbers
    circled = "❶❷❸❹❺❻❼❽❾"
    ctx["progress_icon"] = circled[min(idx, len(circled) - 1)]
    return ctx


def _render_short(sections: list[dict], out: Path) -> dict:
    """Render short slides — v2 (HTML/Playwright) or legacy (Pillow) based on format."""
    if _is_v2_format(sections):
        return asyncio.run(_render_short_v2(sections, out))
    else:
        return _render_short_legacy(sections, out)


async def _render_short_v2(sections: list[dict], out: Path) -> dict:
    """Render short slides using HTML templates + Playwright screenshots."""
    from playwright.async_api import async_playwright

    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    image_paths: list[str] = []

    # Extract ticker/date from title section or fallback
    ticker = "STOCK"
    date = ""
    for s in sections:
        if s.get("type") == "title":
            headline = s.get("headline", "")
            parts = headline.split()
            for p in parts:
                if p.isascii() and p.isalpha():
                    ticker = p
                    break
            break
    for s in sections:
        body = s.get("body", "")
        m = re.search(r"(\d{4}[-年/]\d{1,2}[-月/]\d{1,2})", body)
        if m:
            date = m.group(1)
            break

    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        page = await browser.new_page(
            viewport={"width": SHORT_V2_RENDER_WIDTH, "height": SHORT_V2_RENDER_HEIGHT},
        )

        for idx, section in enumerate(sections):
            section_type = section.get("type", "point")
            template_name = f"{section_type}.html"
            try:
                template = env.get_template(template_name)
            except Exception:
                template = env.get_template("point.html")

            ctx = _build_template_context(section, idx, len(sections), ticker, date)
            html = template.render(**ctx)

            # Replace relative base.css with absolute file:/// path so Playwright finds it
            css_abs = (TEMPLATES_DIR / "base.css").resolve().as_posix()
            html = html.replace('href="base.css"', f'href="file:///{css_abs}"')

            html_path = out / f"_temp_{idx}.html"
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html)

            await page.goto(f"file:///{html_path.resolve().as_posix()}")
            await page.wait_for_load_state("networkidle")

            slide_path = out / f"slide_{idx:02d}.png"
            await page.screenshot(path=str(slide_path))
            image_paths.append(str(slide_path))

            html_path.unlink(missing_ok=True)

        await browser.close()

    # Save sections JSON alongside frames for composer to read
    sections_json_path = out / "_sections.json"
    with open(sections_json_path, "w", encoding="utf-8") as f:
        json.dump(sections, f, ensure_ascii=False)

    return {"image_paths": image_paths}


def _render_short_legacy(sections: list[dict], out: Path) -> dict:
    """Legacy Pillow renderer for backward compatibility with old section format."""
    image_paths: list[str] = []
    font_big = _load_font(bold=True, size=28)
    font_body = _load_font(bold=False, size=21)
    font_label = _load_font(bold=False, size=FONT_SIZE_SMALL)

    for idx, section in enumerate(sections):
        img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
        draw = ImageDraw.Draw(img)
        text = section.get("text", "")
        section_type = section.get("type", "paragraph")
        usable_width = WIDTH - 2 * MARGIN_X

        if section_type == "rating_card":
            color = RATING_SELL_COLOR if "卖出" in text or "减持" in text else (
                RATING_BUY_COLOR if "买入" in text or "增持" in text else HEADING_COLOR
            )
            label_text = "最终评级"
            lbbox = draw.textbbox((0, 0), label_text, font=font_label)
            lw = lbbox[2] - lbbox[0]
            draw.text(((WIDTH - lw) // 2, HEIGHT // 2 - 80), label_text, font=font_label, fill=ACCENT_COLOR)
            bbox = draw.textbbox((0, 0), text, font=font_big)
            tw = bbox[2] - bbox[0]
            draw.text(((WIDTH - tw) // 2, HEIGHT // 2 - 30), text, font=font_big, fill=color)
        else:
            wrapped = _wrap_text(draw, text, font_body, usable_width)
            line_h = int(font_body.size * LINE_HEIGHT_MULTIPLIER)
            total_text_h = len(wrapped) * line_h
            start_y = (HEIGHT - total_text_h) // 2
            for li, line in enumerate(wrapped):
                bbox = draw.textbbox((0, 0), line, font=font_body)
                lw = bbox[2] - bbox[0]
                draw.text(((WIDTH - lw) // 2, start_y + li * line_h), line, font=font_body, fill=TEXT_COLOR)

        dot_y = HEIGHT - 80
        total_dots = len(sections)
        dot_spacing = 16
        dots_width = total_dots * dot_spacing
        dot_start_x = (WIDTH - dots_width) // 2
        for di in range(total_dots):
            cx = dot_start_x + di * dot_spacing + 4
            fill = ACCENT_COLOR if di <= idx else (50, 55, 80)
            draw.ellipse([(cx, dot_y), (cx + 8, dot_y + 8)], fill=fill)

        path = out / f"slide_{idx:02d}.png"
        img.save(str(path), "PNG")
        image_paths.append(str(path))

    return {"image_paths": image_paths}
