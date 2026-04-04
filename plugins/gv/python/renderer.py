"""Render report sections as images using Pillow.

Full layout: one tall scroll image (1080 x N pixels) + y_map.json.
Short layout: one 1080x1920 image per section.
"""

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .config import (
    WIDTH, HEIGHT, MARGIN_X,
    BG_COLOR, TEXT_COLOR, HEADING_COLOR, ACCENT_COLOR,
    RATING_SELL_COLOR, RATING_BUY_COLOR, HIGHLIGHT_BG,
    FONT_REGULAR, FONT_BOLD,
    FONT_SIZE_BODY, FONT_SIZE_H1, FONT_SIZE_H2, FONT_SIZE_H3, FONT_SIZE_SMALL,
    LINE_HEIGHT_MULTIPLIER,
    HEADER_HEIGHT, RATING_CARD_HEIGHT, SCROLL_AREA_HEIGHT,
)


def _load_font(bold: bool = False, size: int = FONT_SIZE_BODY) -> ImageFont.FreeTypeFont:
    """Load font with fallback."""
    names = [FONT_BOLD if bold else FONT_REGULAR, "msyh.ttc", "NotoSansCJKsc-Regular.otf", "arial.ttf"]
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


def _render_short(sections: list[dict], out: Path) -> dict:
    """Render one 1080x1920 image per section for the short version."""
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

        # Center content vertically
        if section_type == "rating_card":
            # Large centered rating
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
            # Wrapped text centered
            wrapped = _wrap_text(draw, text, font_body, usable_width)
            line_h = int(font_body.size * LINE_HEIGHT_MULTIPLIER)
            total_text_h = len(wrapped) * line_h
            start_y = (HEIGHT - total_text_h) // 2

            for li, line in enumerate(wrapped):
                bbox = draw.textbbox((0, 0), line, font=font_body)
                lw = bbox[2] - bbox[0]
                draw.text(((WIDTH - lw) // 2, start_y + li * line_h), line, font=font_body, fill=TEXT_COLOR)

        # Progress dots at bottom
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

    return {
        "image_paths": image_paths,
    }
