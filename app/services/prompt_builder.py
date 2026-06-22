from app.schemas import GenerationSettings, NewsComicPageScript


DEFAULT_STYLE_PRESET = "cinematic_anime"
SD35_FIXED_STYLE_PROMPT = (
    "cinematic Japanese anime film comic style, airy scene-first composition, "
    "clean manga linework, cool rain atmosphere with warm lamp light, soft luminous color, "
    "detailed backgrounds, atmospheric depth, reflective surfaces, appealing finished panels"
)

COMIC_STYLE_PROMPTS = {
    "cinematic_anime": """cinematic Japanese anime film comic style, clean manga linework,
soft luminous color, detailed backgrounds, atmospheric depth, gentle backlight,
glossy reflections when appropriate, finished full-color manga panels.""",
    "default": """finished editorial manga comic style, expressive ink outlines,
soft vivid color, dynamic character acting, clear news comic panels.""",
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
    style_preset = _style_preset(generation_settings)
    return COMIC_STYLE_PROMPTS.get(style_preset, COMIC_STYLE_PROMPTS["default"])


def _style_preset(generation_settings: GenerationSettings | None) -> str:
    if generation_settings:
        return generation_settings.style_preset
    return DEFAULT_STYLE_PRESET


def _sd35_style_prompt(generation_settings: GenerationSettings | None) -> str:
    return SD35_FIXED_STYLE_PROMPT


def _sd35_color_consistency_rule(generation_settings: GenerationSettings | None) -> str:
    return "Full-color manga: cool rainy blues balanced by warm amber lamps; avoid all-blue grading."


def _is_political_news(script: NewsComicPageScript) -> bool:
    haystack = " ".join(
        str(value or "")
        for value in (
            script.title,
            script.news_type,
            script.story_shape,
            script.summary,
            " ".join(script.allowed_facts),
        )
    ).lower()
    political_keywords = [
        "政治",
        "政壇",
        "政黨",
        "政府",
        "內閣",
        "國會",
        "議會",
        "首相",
        "總統",
        "市長",
        "選舉",
        "改選",
        "公投",
        "脫歐",
        "工黨",
        "保守黨",
        "parliament",
        "government",
        "cabinet",
        "prime minister",
        "president",
        "election",
        "referendum",
        "campaign",
        "party",
        "brexit",
    ]
    return any(keyword in haystack for keyword in political_keywords)


def _is_medical_news(script: NewsComicPageScript) -> bool:
    haystack = " ".join(
        str(value or "")
        for value in (
            script.title,
            script.news_type,
            script.story_shape,
            script.summary,
            " ".join(script.allowed_facts),
        )
    ).lower()
    medical_keywords = [
        "健康",
        "醫療",
        "醫師",
        "醫界",
        "醫院",
        "診所",
        "健檢",
        "檢查",
        "抽血",
        "病症",
        "疾病",
        "糖尿病",
        "心臟",
        "心衰",
        "腎臟",
        "血管",
        "死亡風險",
        "國衛院",
        "ckm",
        "clinic",
        "hospital",
        "doctor",
        "nurse",
        "patient",
        "medical",
        "health",
        "diabetes",
        "heart",
        "kidney",
        "vascular",
        "blood test",
    ]
    return any(keyword in haystack for keyword in medical_keywords)


def _is_entertainment_news(script: NewsComicPageScript) -> bool:
    haystack = " ".join(
        str(value or "")
        for value in (
            script.title,
            script.news_type,
            script.story_shape,
            script.summary,
            " ".join(script.allowed_facts),
        )
    ).lower()
    entertainment_keywords = [
        "娛樂",
        "影集",
        "導演",
        "主演",
        "演員",
        "客串",
        "續拍",
        "第二季",
        "校園劇",
        "netflix",
        "streaming",
        "drama",
        "series",
        "actor",
        "director",
        "season",
    ]
    return any(keyword in haystack for keyword in entertainment_keywords)


def _is_campus_news(script: NewsComicPageScript) -> bool:
    haystack = " ".join(
        str(value or "")
        for value in (
            script.title,
            script.news_type,
            script.story_shape,
            script.summary,
            " ".join(script.allowed_facts),
        )
    ).lower()
    campus_keywords = [
        "校園",
        "學校",
        "學生",
        "老師",
        "師生",
        "管教",
        "教室",
        "走廊",
        "classroom",
        "school",
        "student",
        "teacher",
        "campus",
    ]
    return any(keyword in haystack for keyword in campus_keywords)


def _scene(subject: str, composition: str, lighting: str) -> dict[str, str]:
    return {
        "subject": subject,
        "composition": composition,
        "lighting": lighting,
    }


def _sd35_safe_scene_templates(script: NewsComicPageScript) -> list[dict[str, str]]:
    if _is_entertainment_news(script) or _is_campus_news(script):
        return [
            _scene("studio lounge, blank screen, two adult silhouettes talking", "wide shot, eye level, reflective floor", "warm window light, cool shadows, no text or logos"),
            _scene("empty school corridor, blank bulletin boards, no students", "wide hallway view, deep perspective", "long window light, calm after-class mood"),
            _scene("film set corner, director chair, camera silhouettes, blank monitor", "medium-wide shot, layered equipment foreground", "amber studio lamps, cool teal shadows"),
            _scene("one adult holding a blank document by a rainy window", "over-the-shoulder medium shot", "soft city reflections, quiet warm lamp light"),
            _scene("audience silhouettes facing a large blank screen", "rear wide shot, theater depth", "gentle backlight, reflective floor, no title text"),
        ]

    if _is_medical_news(script):
        return [
            _scene("empty clinic room, blank health report, stethoscope on table", "wide shot, eye level, window visible", "after-rain reflections, warm desk lamp"),
            _scene("blank lab reports on desk, coffee cup, rain-streaked window", "still-life medium shot, no people", "amber lamp, cool blue city reflections"),
            _scene("quiet hospital waiting room, distant adult silhouettes, plants", "far wide shot, strong depth", "warm ceiling lamps, polished reflective floor"),
            _scene("adult hands holding blank health report, stethoscope, blood tubes", "close view of hands, shallow depth", "warm wooden desk, soft rainy window light"),
            _scene("medical instruments, blank monitors, dim laboratory", "wide equipment shot, no people in focus", "warm device lights, cool rainy reflections"),
        ]

    if _is_political_news(script):
        return [
            _scene("parliament corridor, adult silhouettes, blank documents", "wide corridor shot, tall windows", "polished reflections, no flags or text"),
            _scene("empty podium, microphones, blank press backdrop", "centered medium-wide press room", "warm overhead lights, cool shadows"),
            _scene("adult voters from behind near blank ballot box", "rear medium-wide shot", "soft daylight, calm civic hall"),
            _scene("rainy government building exterior, distant silhouettes", "wide establishing shot", "street light reflections, cinematic rain"),
            _scene("adult analysts, blank papers, abstract map shape", "side-view table composition", "warm desk lamp, restrained shadows"),
        ]

    return [
        _scene("adult silhouettes near window, blank papers on desk", "medium-wide interior shot", "warm-cool contrast, reflective surfaces"),
        _scene("quiet city interior, blank screen, layered room depth", "wide shot with foreground elements", "soft window light, calm reflections"),
        _scene("adult silhouettes walking through corridor, blank posters", "long hallway perspective", "long shadows, polished floor reflections"),
        _scene("hands holding blank document beside rainy window", "close view of hands", "warm lamp light, rain reflections"),
        _scene("small public space, distant adult figures, blank board", "wide airy composition", "trees outside, hopeful soft light"),
    ]


def _sd35_safe_panel_scene(script: NewsComicPageScript, panel_id: int) -> dict[str, str]:
    templates = _sd35_safe_scene_templates(script)
    index = max(0, (panel_id - 1) % len(templates))
    return templates[index]


def _sd35_safe_page_context(script: NewsComicPageScript) -> str:
    if _is_entertainment_news(script) or _is_campus_news(script):
        return "Cinematic entertainment and campus issue atmosphere, studio lights, blank screens, quiet corridors, reflective windows."
    if _is_medical_news(script):
        return "Calm health news atmosphere, clinics, labs, blank reports, abstract charts, hopeful window light."
    if _is_political_news(script):
        return "Civic news atmosphere, institutions, press rooms, blank documents, adult silhouettes, reflective floors."
    return "Cinematic public-interest news atmosphere, adult silhouettes, blank documents, windows, reflections, warm-cool light."


def _sd35_context_guardrails(script: NewsComicPageScript) -> str:
    guardrails = []

    if _is_political_news(script):
        guardrails.append(
            "Political: adult politicians, journalists, voters; parliament, podiums, ballot boxes, maps; "
            "avoid celebrity likeness, teenagers, school uniforms."
        )

    if _is_medical_news(script):
        guardrails.append(
            "Medical: adult doctors, nurses, patients in clinics or labs; blank reports, abstract charts; "
            "avoid teenagers, idol lineups, gore, exposed organs."
        )

    if _is_entertainment_news(script):
        guardrails.append(
            "Entertainment: directors, actors, film crew, studio, audience; blank screens and posters; "
            "avoid logos, readable titles, season text, celebrity likeness."
        )

    return " ".join(guardrails)


def _limit_words(text: str, max_words: int) -> str:
    words = str(text or "").split()
    if len(words) <= max_words:
        return str(text or "").strip()
    return " ".join(words[:max_words]).rstrip(" ,.;:") + "."


def _sd35_plain_scene_rule() -> str:
    return (
        "Make this a plain scene illustration with no graphic overlay layer. "
        "Use blank, abstract shapes for screens, papers, signs, uniforms, and props. "
        "Do not render readable text, letters, numbers, captions, logos, labels, or speech bubbles."
    )


def _sd35_page_visual(script: NewsComicPageScript) -> str:
    return _limit_words(_sd35_safe_page_context(script), 18)


def _sd35_panel_visuals(script: NewsComicPageScript) -> str:
    lines = []
    for panel in script.panels:
        scene = _sd35_safe_panel_scene(script, panel.panel_id)
        prompt = (
            f"{scene['subject']}; {scene['composition']}; {scene['lighting']}"
        )
        lines.append(f"P{panel.panel_id}: {_limit_words(prompt, 22)}")
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
    color_rule = _sd35_color_consistency_rule(generation_settings)
    page_visual = _sd35_page_visual(script)
    panel_visuals = _sd35_panel_visuals(script)
    context_guardrails = _sd35_context_guardrails(script)

    clip_prompt = (
        f"A square editorial manga comic news explainer with {script.panel_count} separate panels, "
        "visible gutters, clean black panel borders, expressive characters, soft color ink style."
    )

    return f"""CLIP prompt:
{clip_prompt}

T5 prompt:
Create one square manga news page with exactly {script.panel_count} panels.
Layout: {_sd35_layout_prompt(script)}.
Direction: {page_visual}
{context_guardrails}
{color_rule}
Style: {style_prompt}.
Use visible gutters, black borders, medium or wide shots, expressive characters, clear environments.
Avoid single scene, close-up portrait, dense writing, logos, watermarks, readable letters.
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
    color_rule = _sd35_color_consistency_rule(generation_settings)
    context_guardrails = _sd35_context_guardrails(script)
    scene = _sd35_safe_panel_scene(script, panel.panel_id)

    clip_prompt = (
        "A high quality editorial manga comic panel, clear focal subject, expressive characters, "
        "fine ink linework, polished color shading, finished comic art."
    )

    return f"""CLIP prompt:
{clip_prompt}

T5 prompt:
Create one standalone editorial manga news panel.
Subject and action: {_limit_words(scene["subject"], 20)}
Composition and framing: {_limit_words(scene["composition"], 14)}
Lighting and color: {_limit_words(scene["lighting"], 14)}
Context: {_limit_words(page_visual, 18)}
{context_guardrails}
{color_rule}
Style: {style_prompt}; crisp ink, natural hands, finished comic art.
Keep anatomy coherent, faces appealing, body language readable.
{_sd35_plain_scene_rule()}
Fill the illustration naturally from edge to edge without leaving large empty blank areas.
Final image: polished manga news panel with clear storytelling."""


def build_page_prompt(script: NewsComicPageScript, generation_settings: GenerationSettings | None = None) -> str:
    image_model = getattr(generation_settings, "image_model", "gemini_image") if generation_settings else "gemini_image"
    if image_model == "sd35_medium_local":
        return _build_sd35_medium_prompt(script, generation_settings)
    return _build_gemini_image_prompt(script, generation_settings)
