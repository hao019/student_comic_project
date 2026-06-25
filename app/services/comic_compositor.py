from __future__ import annotations

from pathlib import Path
from typing import TypeAlias

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

from app.schemas import NewsComicPageScript, SD35ComicPageScript


ComicPageScript: TypeAlias = NewsComicPageScript | SD35ComicPageScript


PAGE_SIZE = 1600
PAGE_MARGIN = 24
TITLE_HEIGHT = 112
GUTTER = 18
PANEL_BORDER = 4
TEXT_PAD = 14
TAG_FILL = (255, 225, 92, 205)
HEADER_FILL = (255, 255, 255, 232)
INK = (10, 14, 24, 255)
SPEECH_FILL = (255, 255, 255, 238)
WARNING_FILL = (255, 237, 120, 230)
BADGE_FILL = (54, 109, 137, 235)
BADGE_TEXT = (255, 255, 255, 255)


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        r"C:\Windows\Fonts\msjhbd.ttc" if bold else r"C:\Windows\Fonts\msjh.ttc",
        r"C:\Windows\Fonts\NotoSansCJK-Regular.ttc",
        r"C:\Windows\Fonts\mingliu.ttc",
        r"C:\Windows\Fonts\arial.ttf",
    ]
    for path in candidates:
        if path and Path(path).exists():
            try:
                return ImageFont.truetype(path, size=size)
            except OSError:
                continue
    return ImageFont.load_default()


def _text_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> int:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0]


def _wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
    max_width: int,
    max_lines: int,
) -> list[str]:
    text = " ".join(str(text or "").split())
    if not text:
        return []

    lines: list[str] = []
    current = ""
    for char in text:
        candidate = current + char
        if current and _text_width(draw, candidate, font) > max_width:
            lines.append(current)
            current = char
            if len(lines) >= max_lines:
                break
        else:
            current = candidate

    if current and len(lines) < max_lines:
        lines.append(current)

    if len(lines) == max_lines and len("".join(lines)) < len(text):
        lines[-1] = lines[-1].rstrip("，,。.") + "..."

    return lines


def _fit_text_lines(
    draw: ImageDraw.ImageDraw,
    text: str,
    max_width: int,
    max_lines: int,
    start_size: int,
    min_size: int,
    bold: bool = False,
) -> tuple[ImageFont.ImageFont, list[str]]:
    for size in range(start_size, min_size - 1, -2):
        font = _font(size, bold=bold)
        lines = _wrap_text(draw, text, font, max_width, max_lines)
        if all(_text_width(draw, line, font) <= max_width for line in lines):
            return font, lines
    font = _font(min_size, bold=bold)
    return font, _wrap_text(draw, text, font, max_width, max_lines)


def _panel_boxes(panel_count: int) -> list[tuple[int, int, int, int]]:
    left = PAGE_MARGIN
    right = PAGE_SIZE - PAGE_MARGIN
    top = PAGE_MARGIN + TITLE_HEIGHT
    bottom = PAGE_SIZE - PAGE_MARGIN
    area_w = right - left
    area_h = bottom - top
    col_w = (area_w - GUTTER) // 2

    if panel_count == 4:
        row_h = (area_h - GUTTER) // 2
        return [
            (left, top, left + col_w, top + row_h),
            (left + col_w + GUTTER, top, right, top + row_h),
            (left, top + row_h + GUTTER, left + col_w, bottom),
            (left + col_w + GUTTER, top + row_h + GUTTER, right, bottom),
        ]

    if panel_count == 5:
        row_h = (area_h - (GUTTER * 2)) // 3
        return [
            (left, top, left + col_w, top + row_h),
            (left + col_w + GUTTER, top, right, top + row_h),
            (left, top + row_h + GUTTER, left + col_w, top + row_h * 2 + GUTTER),
            (left + col_w + GUTTER, top + row_h + GUTTER, right, top + row_h * 2 + GUTTER),
            (left, top + row_h * 2 + GUTTER * 2, right, bottom),
        ]

    row_h = (area_h - (GUTTER * 2)) // 3
    return [
        (left, top, left + col_w, top + row_h),
        (left + col_w + GUTTER, top, right, top + row_h),
        (left, top + row_h + GUTTER, left + col_w, top + row_h * 2 + GUTTER),
        (left + col_w + GUTTER, top + row_h + GUTTER, right, top + row_h * 2 + GUTTER),
        (left, top + row_h * 2 + GUTTER * 2, left + col_w, bottom),
        (left + col_w + GUTTER, top + row_h * 2 + GUTTER * 2, right, bottom),
    ]


def _cover_image(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    image = image.convert("RGB")
    target_w, target_h = size
    scale = max(target_w / image.width, target_h / image.height)
    resized = image.resize((round(image.width * scale), round(image.height * scale)), Image.Resampling.LANCZOS)
    left = (resized.width - target_w) // 2
    top = (resized.height - target_h) // 2
    return resized.crop((left, top, left + target_w, top + target_h))


def _enhance_panel_image(image: Image.Image) -> Image.Image:
    image = ImageEnhance.Contrast(image).enhance(1.04)
    image = ImageEnhance.Color(image).enhance(1.03)
    return image.filter(ImageFilter.UnsharpMask(radius=0.85, percent=45, threshold=4))


def _draw_title(draw: ImageDraw.ImageDraw, script: ComicPageScript) -> None:
    badge = _page_badge_text(script)
    badge_w = 0
    if badge:
        badge_font = _font(28, bold=True)
        badge_lines = _wrap_text(draw, badge, badge_font, 80, 2)
        badge_w = 86
        badge_h = 72
        badge_box = (PAGE_MARGIN, PAGE_MARGIN - 6, PAGE_MARGIN + badge_w, PAGE_MARGIN - 6 + badge_h)
        draw.rounded_rectangle(badge_box, radius=6, fill=BADGE_FILL)
        line_y = badge_box[1] + 8
        for line in badge_lines:
            line_w = _text_width(draw, line, badge_font)
            draw.text((badge_box[0] + (badge_w - line_w) // 2, line_y), line, font=badge_font, fill=BADGE_TEXT)
            line_y += int(badge_font.size * 1.08)

    title_x = PAGE_MARGIN + badge_w + (18 if badge else 0)
    max_width = PAGE_SIZE - title_x - PAGE_MARGIN
    font, lines = _fit_text_lines(
        draw,
        script.title,
        max_width=max_width,
        max_lines=2,
        start_size=56,
        min_size=34,
        bold=True,
    )
    y = PAGE_MARGIN - 4
    for line in lines:
        draw.text((title_x, y), line, font=font, fill=INK)
        y += int(font.size * 1.18) if hasattr(font, "size") else 34


def _page_badge_text(script: ComicPageScript) -> str:
    haystack = " ".join(
        str(value or "")
        for value in (
            getattr(script, "title", ""),
            getattr(script, "news_type", ""),
            getattr(script, "summary", ""),
            " ".join(getattr(script, "allowed_facts", []) or []),
        )
    )
    if any(keyword in haystack for keyword in ("地震", "強震", "震度", "餘震")):
        return "地震\n警示"
    if any(keyword in haystack for keyword in ("豪雨", "暴雨", "大雨", "颱風", "淹水", "防汛")):
        return "生活\n警示"
    if any(keyword in haystack for keyword in ("防疫", "疾病", "醫療", "健康")):
        return "健康\n警示"
    return ""


def _draw_text_lines(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    lines: list[str],
    font: ImageFont.ImageFont,
    fill: tuple[int, int, int, int] = INK,
) -> int:
    x, y = xy
    line_h = int(font.size * 1.15) if hasattr(font, "size") else 24
    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        y += line_h
    return y


def _narration_text(panel: dict) -> str:
    title = str(panel.get("panel_title") or "").strip()
    main_text = str(panel.get("main_text") or "").strip()
    if main_text == title:
        main_text = ""
    return main_text


def _panel_header_height(panel_w: int, panel: dict) -> int:
    return 58 if panel_w < 1000 else 64


def _draw_panel_header(draw: ImageDraw.ImageDraw, header_box: tuple[int, int, int, int], panel: dict) -> int:
    x1, y1, x2, y2 = header_box
    panel_w = x2 - x1
    header_h = y2 - y1
    draw.rectangle(header_box, fill=HEADER_FILL)

    tag = str(panel.get("panel_title") or "").strip() or f"P{panel.get('panel_id') or ''}"
    tag_font, tag_lines = _fit_text_lines(
        draw,
        tag,
        max_width=max(86, panel_w // 4),
        max_lines=1,
        start_size=28,
        min_size=20,
        bold=True,
    )
    tag_text = tag_lines[0] if tag_lines else tag
    tag_w = min(max(_text_width(draw, tag_text, tag_font) + 30, 108), panel_w // 3)
    tag_box = (header_box[0], header_box[1], header_box[0] + tag_w, header_box[3])
    draw.rectangle(tag_box, fill=TAG_FILL, outline=INK, width=2)
    tag_y = tag_box[1] + max(4, (header_h - (tag_font.size if hasattr(tag_font, "size") else 20)) // 2 - 1)
    draw.text((tag_box[0] + 15, tag_y), tag_text, font=tag_font, fill=INK)

    main_text = _narration_text(panel)
    main_x = tag_box[2] + 12
    main_w = max(80, header_box[2] - main_x - 12)
    main_font, main_lines = _fit_text_lines(
        draw,
        main_text,
        max_width=main_w,
        max_lines=2 if header_h < 62 else 3,
        start_size=28,
        min_size=18,
        bold=True,
    )
    line_h = int(main_font.size * 1.15) if hasattr(main_font, "size") else 22
    main_y = header_box[1] + max(5, (header_h - line_h * len(main_lines)) // 2)
    _draw_text_lines(draw, (main_x, main_y), main_lines, main_font)
    draw.line((header_box[0], header_box[3], header_box[2], header_box[3]), fill=INK, width=2)
    return header_box[3]


def _draw_callouts(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], callouts: list[str]) -> None:
    if not callouts:
        return

    x1, y1, x2, y2 = box
    primary = str(callouts[0]).strip() if callouts else ""
    if primary:
        font, lines = _fit_text_lines(
            draw,
            primary,
            max_width=max(150, (x2 - x1) // 3),
            max_lines=1,
            start_size=25,
            min_size=18,
            bold=True,
        )
        if lines:
            label_w = min(_text_width(draw, lines[0], font) + 40, x2 - x1 - 56)
            label_h = (font.size if hasattr(font, "size") else 25) + 20
            label_box = _primary_label_box(box, label_w, label_h)
            draw.rounded_rectangle(label_box, radius=8, fill=TAG_FILL, outline=INK, width=3)
            draw.text((label_box[0] + 20, label_box[1] + 9), lines[0], font=font, fill=INK)

    y = y2 - PANEL_BORDER - 14
    secondary_callouts = [str(item).strip() for item in callouts[1:3] if str(item).strip()]
    for callout in reversed(secondary_callouts):
        font, lines = _fit_text_lines(
            draw,
            callout,
            max_width=max(132, (x2 - x1) // 3),
            max_lines=1,
            start_size=23,
            min_size=17,
            bold=True,
        )
        if not lines:
            continue
        text_w = _text_width(draw, lines[0], font)
        tag_w = min(text_w + 30, x2 - x1 - 48)
        tag_h = (font.size if hasattr(font, "size") else 23) + 18
        y -= tag_h
        tag_box = (x2 - PANEL_BORDER - 18 - tag_w, y, x2 - PANEL_BORDER - 18, y + tag_h)
        draw.rectangle(tag_box, fill=TAG_FILL, outline=INK, width=2)
        draw.text((tag_box[0] + 15, tag_box[1] + 8), lines[0], font=font, fill=INK)
        y -= 8


def _primary_label_box(box: tuple[int, int, int, int], label_w: int, label_h: int) -> tuple[int, int, int, int]:
    x1, y1, x2, y2 = box
    panel_w = x2 - x1
    panel_h = y2 - y1
    if panel_w > panel_h * 1.65:
        x = x1 + PANEL_BORDER + 24
        y = y1 + PANEL_BORDER + 24
    else:
        x = x1 + PANEL_BORDER + 18
        y = y1 + PANEL_BORDER + 18
    return (x, y, min(x + label_w, x2 - PANEL_BORDER - 18), y + label_h)


def _draw_speech_overlay(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], speech: list[str]) -> None:
    speech_lines = [str(item).strip() for item in speech if str(item).strip()]
    if not speech_lines:
        return

    x1, y1, x2, y2 = box
    text = speech_lines[0]
    measure_font = _font(24, bold=True)
    desired_w = _text_width(draw, text, measure_font) + 72
    bubble_w = min(x2 - x1 - 54, max(180, min(desired_w, 430, int((x2 - x1) * 0.46))))
    font, lines = _fit_text_lines(
        draw,
        text,
        max_width=bubble_w - 34,
        max_lines=2,
        start_size=24,
        min_size=17,
        bold=True,
    )
    if not lines:
        return

    line_h = int(font.size * 1.18) if hasattr(font, "size") else 24
    bubble_h = max(54, line_h * len(lines) + 26)
    bubble_x2 = x2 - PANEL_BORDER - 22
    bubble_x1 = bubble_x2 - bubble_w
    bubble_y1 = y1 + PANEL_BORDER + 18
    bubble_y2 = bubble_y1 + bubble_h
    if bubble_y2 > y2 - 80:
        return

    draw.rounded_rectangle((bubble_x1, bubble_y1, bubble_x2, bubble_y2), radius=18, fill=SPEECH_FILL, outline=INK, width=3)
    tail = [
        (bubble_x2 - 52, bubble_y2 - 2),
        (bubble_x2 - 18, bubble_y2 + 30),
        (bubble_x2 - 86, bubble_y2 - 2),
    ]
    draw.polygon(tail, fill=SPEECH_FILL, outline=INK)
    _draw_text_lines(draw, (bubble_x1 + 17, bubble_y1 + 14), lines, font)


def _is_warning_panel(panel: dict) -> bool:
    haystack = " ".join(
        str(value or "")
        for value in [
            panel.get("panel_title"),
            panel.get("main_text"),
            panel.get("visual"),
            " ".join(panel.get("callouts") or []),
        ]
    )
    return any(keyword in haystack for keyword in ("警", "雨", "災", "汛", "颱", "防災", "豪雨", "淹水", "氣候"))


def _draw_warning_icon(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    x1, y1, _, _ = box
    cx = x1 + 48
    top = y1 + 20
    points = [(cx, top), (cx - 34, top + 62), (cx + 34, top + 62)]
    draw.polygon(points, fill=WARNING_FILL, outline=INK)
    font = _font(34, bold=True)
    draw.text((cx - 6, top + 16), "!", font=font, fill=INK)


def _panel_regions(box: tuple[int, int, int, int], panel: dict) -> tuple[tuple[int, int, int, int], tuple[int, int, int, int]]:
    x1, y1, x2, y2 = box
    header_h = _panel_header_height(x2 - x1, panel)
    header_box = (x1 + PANEL_BORDER, y1 + PANEL_BORDER, x2 - PANEL_BORDER, y1 + PANEL_BORDER + header_h)
    image_box = (x1 + PANEL_BORDER, header_box[3] + 3, x2 - PANEL_BORDER, y2 - PANEL_BORDER)
    return header_box, image_box


def panel_image_dimensions(script: ComicPageScript) -> dict[int, tuple[int, int]]:
    panels = [panel.model_dump() for panel in script.panels]
    boxes = _panel_boxes(script.panel_count)
    dimensions: dict[int, tuple[int, int]] = {}
    for panel, box in zip(panels, boxes):
        panel_id = int(panel.get("panel_id") or 0)
        _, image_box = _panel_regions(box, panel)
        dimensions[panel_id] = (image_box[2] - image_box[0], image_box[3] - image_box[1])
    return dimensions


def _draw_panel_overlays(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], panel: dict) -> None:
    header_box, image_box = _panel_regions(box, panel)
    _draw_panel_header(draw, header_box, panel)
    if _is_warning_panel(panel):
        _draw_warning_icon(draw, image_box)
    _draw_speech_overlay(draw, image_box, panel.get("speech") or [])
    _draw_callouts(draw, image_box, panel.get("callouts") or [])


def compose_comic_page(
    script: ComicPageScript,
    panel_image_paths: dict[int, Path],
    output_path: Path,
) -> None:
    page = Image.new("RGB", (PAGE_SIZE, PAGE_SIZE), (248, 247, 242))
    draw = ImageDraw.Draw(page, "RGBA")
    _draw_title(draw, script)

    panels = [panel.model_dump() for panel in script.panels]
    boxes = _panel_boxes(script.panel_count)
    for panel, box in zip(panels, boxes):
        panel_id = int(panel.get("panel_id") or 0)
        image_path = panel_image_paths.get(panel_id)
        if not image_path or not image_path.exists():
            continue

        x1, y1, x2, y2 = box
        _, image_box = _panel_regions(box, panel)
        image_w = image_box[2] - image_box[0]
        image_h = image_box[3] - image_box[1]
        panel_image = _cover_image(Image.open(image_path), (image_w, image_h))
        panel_image = _enhance_panel_image(panel_image)
        page.paste(panel_image, (image_box[0], image_box[1]))
        draw.rectangle(box, outline=(13, 17, 23, 255), width=PANEL_BORDER)
        _draw_panel_overlays(draw, box, panel)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    page.save(output_path)
