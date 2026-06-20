from app.schemas import GenerationSettings, NewsComicPageScript


COMIC_STYLE_PROMPTS = {
    "default": """clean editorial manga, soft color, ink outlines, newspaper comic page,
clear black panel borders, balanced text boxes, readable Traditional Chinese text.""",
    "monochrome_draft": """black-and-white manga manuscript style, crisp ink line art, screentone shading,
visible pen texture, strong black panel borders, no color except black, white, and gray,
readable Traditional Chinese text.""",
    "shonen": """energetic shonen manga style, bold dynamic poses, expressive faces, speed lines,
dramatic impact framing, high-contrast ink outlines, vivid but controlled color,
readable Traditional Chinese text.""",
    "gag_4koma": """lighthearted gag four-panel comic style, simple cute characters, clear reactions,
rounded speech bubbles, playful facial expressions, clean bright colors,
readable Traditional Chinese text.""",
    "infographic": """information graphic comic style, clean editorial layout, icons, arrows, labels,
simple character illustrations, organized data callouts, restrained colors,
readable Traditional Chinese text with strong hierarchy.""",
    "emotional": """emotion-driven animated comic style, cinematic facial expressions, warm lighting,
soft painterly color, atmospheric but clear scenes, expressive body language,
readable Traditional Chinese text.""",
    "taiwan_news": """Taiwanese news comic style, clean local newspaper and TV news explainer feeling,
approachable characters, realistic Taiwan street and school details when relevant,
clear title bars, callout boxes, restrained editorial colors, readable Traditional Chinese text.""",
    "internet_meme": """internet meme comic style, exaggerated reaction faces, bold punchline timing,
simple high-contrast panels, playful sticker-like callouts, social media humor energy,
readable Traditional Chinese text without adding unrelated meme captions.""",
}


def _style_prompt(generation_settings: GenerationSettings | None) -> str:
    style_preset = "default"
    if generation_settings:
        style_preset = generation_settings.style_preset

    return COMIC_STYLE_PROMPTS.get(style_preset, COMIC_STYLE_PROMPTS["default"])


def _sd35_style_prompt(generation_settings: GenerationSettings | None) -> str:
    style_prompt = _style_prompt(generation_settings)
    removals = [
        "balanced text boxes, ",
        "rounded speech bubbles, ",
        "clear title bars, callout boxes, ",
        "labels,\n",
        "readable Traditional Chinese text with strong hierarchy",
        "readable Traditional Chinese text without adding unrelated meme captions",
        "readable Traditional Chinese text",
    ]
    for text_rule in removals:
        style_prompt = style_prompt.replace(text_rule, "")
    style_prompt = style_prompt.replace(", .", ".").replace(",,", ",")
    style_prompt = " ".join(style_prompt.split()).strip(" ,.")
    return style_prompt or "clean editorial manga, soft color, polished ink outlines"


def _limit_words(text: str, max_words: int) -> str:
    words = str(text or "").split()
    if len(words) <= max_words:
        return str(text or "").strip()
    return " ".join(words[:max_words]).rstrip(" ,.;:") + "."


def _sd35_plain_scene_rule() -> str:
    return (
        "Make this a plain scene illustration with no graphic overlay layer. "
        "Use blank, abstract shapes for screens, papers, signs, uniforms, and props."
    )


def _sd35_page_visual(script: NewsComicPageScript) -> str:
    prompt = (getattr(script, "visual_prompt_en", "") or "").strip()
    if prompt:
        return _limit_words(prompt, 34)
    return (
        "A square editorial manga news explainer illustration with clearly separated panels, "
        "multiple people, informative visual storytelling, modern public-interest news atmosphere, "
        "soft color ink artwork, clean backgrounds, cinematic lighting."
    )


def _sd35_panel_visuals(script: NewsComicPageScript) -> str:
    lines = []
    for panel in script.panels:
        prompt = (getattr(panel, "visual_prompt_en", "") or "").strip()
        if not prompt:
            prompt = (
                "A clear editorial news scene with people reacting to an important public issue, "
                "medium shot, environment visible, soft cinematic lighting, polished manga ink style."
            )
        lines.append(f"P{panel.panel_id}: {_limit_words(prompt, 24)}")
    return "\n".join(lines)


def _panel_lines(script: NewsComicPageScript) -> list[str]:
    panel_lines = []
    for panel in script.panels:
        panel_lines.append(
            "\n".join(
                [
                    f"Panel {panel.panel_id}: {panel.panel_title}",
                    f"Visual: {panel.visual}",
                    f"Characters: {', '.join(panel.characters) if panel.characters else 'none'}",
                    f"Main text: {panel.main_text}",
                    f"Speech bubbles: {' / '.join(panel.speech) if panel.speech else 'none'}",
                    f"Callout boxes: {' / '.join(panel.callouts) if panel.callouts else 'none'}",
                ]
            )
        )
    return panel_lines


def _layout_prompt(script: NewsComicPageScript) -> str:
    return {
        4: "four-panel grid, two panels on top row and two panels on bottom row",
        5: "five-panel news layout, two panels on top row, two panels in the middle row, one wide panel at the bottom",
        6: "six-panel grid, two columns and three rows",
    }.get(script.panel_count, "balanced multi-panel news comic layout")


def _sd35_layout_prompt(script: NewsComicPageScript) -> str:
    return {
        4: "four separate rectangles: P1 P2 top row, P3 P4 bottom row",
        5: "five separate rectangles: P1 P2 top row, P3 P4 middle row, P5 wide bottom panel",
        6: "six separate rectangles in a strict two-column by three-row grid",
    }.get(script.panel_count, f"{script.panel_count} separate rectangular comic panels")


def _fact_lines(script: NewsComicPageScript) -> str:
    return "\n".join(f"- {fact}" for fact in script.allowed_facts) or "- none"


def _locked_text_lines(script: NewsComicPageScript) -> str:
    return "\n".join(f"- {text}" for text in script.locked_text_blocks) or "- none"


def _build_gemini_image_prompt(script: NewsComicPageScript, generation_settings: GenerationSettings | None = None) -> str:
    panel_lines = _panel_lines(script)

    layout = _layout_prompt(script)
    allowed_facts = _fact_lines(script)
    locked_text = _locked_text_lines(script)

    style_prompt = _style_prompt(generation_settings)

    return f"""Create a complete one-page Traditional Chinese news explainer manga infographic.

Overall style:
{style_prompt}

Canvas and layout:
square 1:1 composition.
Use exactly {script.panel_count} panels.
Layout: {layout}.
Do not leave blank panels.
Do not create extra panels.

News title:
{script.title}

News type:
{script.news_type}

Tone:
{script.tone}

Summary:
{script.summary}

Allowed facts, names, numbers, and outcomes:
{allowed_facts}

Exact text blocks allowed in the image:
{locked_text}

Panels:
{chr(10).join(panel_lines)}

Important text rules:
Text accuracy is the highest priority.
Use only the exact Traditional Chinese text blocks listed above.
Do not paraphrase, translate, summarize, rewrite, or invent any Chinese text.
Do not add extra names, numbers, dates, organizations, logos, UI labels, signs, captions, or facts.
If there is not enough space, omit less important callouts instead of rewriting text.
Keep all Chinese text large, horizontal, bold, and readable.
Use fewer text boxes with larger characters.
Maximum one speech bubble per panel.
Maximum two callout boxes per panel.
Avoid tiny dense text.
Avoid garbled characters.

Final result:
Make it look like a finished news comic page similar to a social media news explainer.
The composition should integrate panels, speech bubbles, arrows, title labels, and callouts naturally."""


def _build_sd35_medium_prompt(script: NewsComicPageScript, generation_settings: GenerationSettings | None = None) -> str:
    style_prompt = _sd35_style_prompt(generation_settings)
    page_visual = _sd35_page_visual(script)
    panel_visuals = _sd35_panel_visuals(script)

    clip_prompt = (
        f"A square editorial manga news explainer illustration with {script.panel_count} separate panels, "
        "visible gutters, clean black panel borders, several characters, soft color ink style."
    )

    return f"""CLIP prompt:
{clip_prompt}

T5 prompt:
Create one square editorial manga news explainer page with exactly {script.panel_count} panels.
Layout: {_sd35_layout_prompt(script)}.
Direction: {page_visual}
Use visible gutters, clean black borders, medium or wide shots, expressive characters, clear environments, cinematic lighting, and {style_prompt}.
Avoid a single scene, three-strip layout, close-up portrait, dense writing, logos, watermarks, or readable letters.
Panel plan:
{panel_visuals}

Final image: coherent finished manga news page with balanced hierarchy and clear scene changes."""


def build_sd35_panel_prompt(
    script: NewsComicPageScript,
    panel_id: int,
    generation_settings: GenerationSettings | None = None,
) -> str:
    style_prompt = _sd35_style_prompt(generation_settings)
    panel = next((item for item in script.panels if item.panel_id == panel_id), None)
    if panel is None:
        raise ValueError(f"Panel {panel_id} not found in script.")

    page_visual = _sd35_page_visual(script)
    panel_visual = (getattr(panel, "visual_prompt_en", "") or "").strip()
    if not panel_visual:
        panel_visual = (
            "A clear editorial manga news scene with people reacting to an important public issue, "
            "medium shot, visible environment, cinematic lighting, polished ink style."
        )

    clip_prompt = (
        "A high quality detailed anime editorial news illustration, clear focal subject, "
        "expressive characters, fine ink linework, polished color shading."
    )

    return f"""CLIP prompt:
{clip_prompt}

T5 prompt:
Create one standalone editorial manga news panel.
Scene: {_limit_words(panel_visual, 58)}
Page context: {_limit_words(page_visual, 24)}
Use medium or wide camera framing, clear focal subject, clean readable composition, rich background detail, natural body language, cinematic lighting, and {style_prompt}.
Add detailed clothing folds, well-drawn faces, natural hands, meaningful props, layered environment depth, crisp fine ink linework, subtle texture, and polished color shading.
Keep the anatomy coherent, faces attractive and consistent, and the scene finished rather than sketchy.
{_sd35_plain_scene_rule()}
Fill the illustration naturally from edge to edge without leaving large empty blank areas.
Final image: polished manga news panel with clear storytelling."""


def build_page_prompt(script: NewsComicPageScript, generation_settings: GenerationSettings | None = None) -> str:
    image_model = getattr(generation_settings, "image_model", "gemini_image") if generation_settings else "gemini_image"
    if image_model == "sd35_medium_local":
        return _build_sd35_medium_prompt(script, generation_settings)
    return _build_gemini_image_prompt(script, generation_settings)
