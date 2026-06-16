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


def _build_flux_kontext_prompt(script: NewsComicPageScript, generation_settings: GenerationSettings | None = None) -> str:
    panel_lines = _panel_lines(script)
    style_prompt = _style_prompt(generation_settings)

    characters = []
    for panel in script.panels:
        characters.extend(panel.characters or [])
    unique_characters = list(dict.fromkeys(characters))
    character_lines = "\n".join(f"- {character}" for character in unique_characters) or "- No recurring named character."

    return f"""Create a finished one-page Traditional Chinese news manga infographic.

Use FLUX.1 Kontext [dev] style prompt following. The prompt describes a complete comic page, not separate images.

Visual style:
{style_prompt}

Page composition:
- Square 1:1 canvas.
- Use exactly {script.panel_count} panels.
- Layout: {_layout_prompt(script)}.
- Clear black panel borders.
- Keep characters visually consistent across panels.
- Use expressive faces, clear camera angles, and readable news infographic composition.

News understanding:
- Title: {script.title}
- News type: {script.news_type}
- Story shape: {script.story_shape}
- Overall tone: {script.tone}
- Summary: {script.summary}

Recurring characters and groups:
{character_lines}

Allowed factual content:
{_fact_lines(script)}

Panel plan:
{chr(10).join(panel_lines)}

Text blocks to place in the artwork:
{_locked_text_lines(script)}

Text and fidelity rules:
- Use only the exact Traditional Chinese text blocks listed above.
- Do not add unrelated Chinese, English, logos, watermarks, signatures, UI text, or random captions.
- If Chinese text rendering is difficult, prioritize larger title bars, labels, and speech bubbles over dense small text.
- Do not invent unsupported people, brands, numbers, dates, places, or outcomes.
- Keep the page suitable for a student news explainer comic."""


def build_page_prompt(script: NewsComicPageScript, generation_settings: GenerationSettings | None = None) -> str:
    image_model = getattr(generation_settings, "image_model", "gemini_image") if generation_settings else "gemini_image"
    if image_model == "flux_kontext_local":
        return _build_flux_kontext_prompt(script, generation_settings)
    return _build_gemini_image_prompt(script, generation_settings)
