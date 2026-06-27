from typing import TypeAlias

from app.schemas import GenerationSettings, NewsComicPageScript, SD35ComicPageScript


ComicPageScript: TypeAlias = NewsComicPageScript | SD35ComicPageScript


DEFAULT_STYLE_PRESET = "cinematic_anime"
SD35_FIXED_STYLE_PROMPT = (
    "bright social-media news explainer comic style, clean flat editorial color, bold readable silhouettes, "
    "simple character illustrations, large foreground news objects, clear object hierarchy, minimal cinematic shading"
)

SD35_STYLE_PROMPTS = {
    "cinematic_anime": SD35_FIXED_STYLE_PROMPT,
    "default": (
        "clean social-media news comic style, simplified everyday environments, clear character acting, "
        "large key objects, bright balanced color, readable infographic hierarchy"
    ),
    "monochrome_draft": (
        "black-and-white manga manuscript style, crisp ink line art, screentone shading, strong contrast, "
        "paper texture, no color"
    ),
    "shonen": (
        "energetic shonen manga style, dynamic poses, bold perspective, speed-line energy where appropriate, "
        "high contrast ink, vivid but controlled color"
    ),
    "gag_4koma": (
        "lighthearted gag manga style, simplified expressive faces, clear comedic timing, clean bright color, "
        "friendly character shapes"
    ),
    "infographic": (
        "editorial infographic manga style, clean organized composition, large simple icons and non-readable diagrams, "
        "bright restrained color palette, clear scene logic, simplified backgrounds, news explainer card feeling"
    ),
    "emotional": (
        "emotion-driven animated comic style, expressive body language, warm human lighting, soft painterly color, "
        "clear faces and atmospheric backgrounds"
    ),
    "taiwan_news": (
        "Taiwanese local news comic style, practical real-world locations, approachable people, restrained editorial color, "
        "clear public-interest news mood"
    ),
    "internet_meme": (
        "internet reaction manga style, exaggerated but readable expressions, bold timing, simple high-contrast shapes, "
        "playful social media energy without readable UI text"
    ),
}

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
    style_preset = _style_preset(generation_settings)
    return SD35_STYLE_PROMPTS.get(style_preset, SD35_STYLE_PROMPTS["cinematic_anime"])


def _sd35_color_consistency_rule(generation_settings: GenerationSettings | None) -> str:
    if _style_preset(generation_settings) == "monochrome_draft":
        return (
            "Black-and-white manga manuscript rendering. Use crisp ink contrast and clean screentone; "
            "do not add full-color lighting."
        )
    return (
        "Full-color news explainer comic with bright but controlled colors, cream paper whites, soft blue and yellow editorial accents, "
        "and clean black outlines. Match the article setting and season; do not drift into grayscale, monochrome sketch, "
        "washed-out pencil draft, rain, night scenes, dramatic blue grading, or sunset unless the panel scene explicitly calls for it."
    )


def _is_political_news(script: ComicPageScript) -> bool:
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
        "政府",
        "立法院",
        "總統",
        "選舉",
        "政黨",
        "公投",
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


def _is_medical_news(script: ComicPageScript) -> bool:
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
        "醫院",
        "診所",
        "醫師",
        "護理",
        "病患",
        "防疫",
        "疾病",
        "登革熱",
        "傳染病",
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


def _is_entertainment_news(script: ComicPageScript) -> bool:
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
        "影視",
        "戲劇",
        "韓劇",
        "電影",
        "演員",
        "藝人",
        "偶像",
        "粉絲",
        "道歉",
        "爭議",
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
        "entertainment",
        "controversy",
        "production",
        "film",
        "celebrity",
        "idol",
        "fandom",
        "streaming",
        "drama",
        "series",
        "actor",
        "director",
        "season",
    ]
    return any(keyword in haystack for keyword in entertainment_keywords)


def _is_campus_news(script: ComicPageScript) -> bool:
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
        "教師",
        "大學",
        "高中",
        "課堂",
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


def _is_weather_or_disaster_news(script: ComicPageScript) -> bool:
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
    weather_keywords = [
        "天氣",
        "氣象",
        "豪雨",
        "大雨",
        "雷雨",
        "暴雨",
        "降雨",
        "颱風",
        "鋒面",
        "西南氣流",
        "積水",
        "淹水",
        "災情",
        "災害",
        "極端氣候",
        "rain",
        "storm",
        "flood",
        "typhoon",
        "weather",
        "climate",
    ]
    return any(keyword in haystack for keyword in weather_keywords)


def _is_earthquake_news(script: ComicPageScript) -> bool:
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
    earthquake_keywords = [
        "地震",
        "強震",
        "震度",
        "餘震",
        "震央",
        "規模",
        "搖晃",
        "earthquake",
        "quake",
        "magnitude",
        "aftershock",
        "seismic",
    ]
    return any(keyword in haystack for keyword in earthquake_keywords)


def _is_institutional_budget_news(script: ComicPageScript) -> bool:
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
    budget_keywords = [
        "預算",
        "特別預算",
        "行政院",
        "國會",
        "立法院",
        "委員會",
        "審查",
        "協商",
        "封殺",
        "法案",
        "政策",
        "國防",
        "撥款",
        "財政",
        "budget",
        "appropriation",
        "legislature",
        "parliament",
        "committee",
        "bill",
        "policy",
        "funding",
        "defense",
    ]
    return any(keyword in haystack for keyword in budget_keywords)


def _scene(subject: str, composition: str, lighting: str) -> dict[str, str]:
    return {
        "subject": subject,
        "composition": composition,
        "lighting": lighting,
    }


def _sd35_safe_scene_templates(script: ComicPageScript) -> list[dict[str, str]]:
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


def _sd35_safe_panel_scene(script: ComicPageScript, panel_id: int) -> dict[str, str]:
    templates = _sd35_safe_scene_templates(script)
    index = max(0, (panel_id - 1) % len(templates))
    return templates[index]


def _sd35_safe_page_context(script: ComicPageScript) -> str:
    if _is_entertainment_news(script) or _is_campus_news(script):
        return "Cinematic entertainment and campus issue atmosphere, studio lights, blank screens, quiet corridors, reflective windows."
    if _is_medical_news(script):
        return "Calm health news atmosphere, clinics, labs, blank reports, abstract charts, hopeful window light."
    if _is_political_news(script):
        return "Civic news atmosphere, institutions, press rooms, blank documents, adult silhouettes, reflective floors."
    return "Cinematic public-interest news atmosphere, adult silhouettes, blank documents, windows, reflections, warm-cool light."


def _sd35_context_guardrails(script: ComicPageScript) -> str:
    guardrails = []

    if _is_earthquake_news(script):
        guardrails.append(
            "Earthquake news: prioritize large, clear evidence objects such as shaking furniture, people under a table, "
            "cracked walls, fallen glass, stretchers, stopped trains, seismograph wave screens, emergency radios, "
            "helmets, and evacuation bags. Use simple explanatory composition with one main object/action per panel. "
            "Avoid scenic empty streets, tiny rubble, decorative interiors, and distant damage that is hard to read."
        )

    if _is_weather_or_disaster_news(script):
        guardrails.append(
            "Weather/disaster news: make each panel show concrete evidence and action, not generic atmosphere. "
            "Use visible rainfall, water depth, flooded curbs, sandbags, raincoats, umbrellas, weather staff, "
            "blank radar maps with simple colored cloud shapes, emergency supplies, or cleanup tools. "
            "For outlook or warning panels, show preparation or response actions in the foreground. "
            "Avoid generic crowds simply looking at the sky, symbolic climate scenes, empty streets without evidence, "
            "and beautiful scenery that does not explain the news."
        )

    if _is_institutional_budget_news(script):
        guardrails.append(
            "Institutional budget or policy news: show legislative committee rooms, plain meeting tables, microphones, "
            "stacks of blank budget binders, folder piles, non-readable vote boards, simple abstract budget charts, "
            "committee nameplates without text, and officials pointing at documents. The main evidence should be "
            "budget folders, documents, charts, voting process, or negotiation table items, not suits or faces. "
            "Avoid courtrooms, judges, gavels unless the article is judicial, foreign flags, national emblems, seals, "
            "ornate palace halls, military propaganda posters, readable documents, and fake interface text."
        )

    if _is_political_news(script):
        guardrails.append(
            "Political: adult politicians, journalists, voters; parliament, podiums, ballot boxes, maps, documents; "
            "avoid celebrity likeness, teenagers, school uniforms, foreign flags, official seals, and courtroom imagery unless explicitly required."
        )

    if _is_medical_news(script):
        guardrails.append(
            "Medical: adult doctors, nurses, patients in clinics or labs; blank reports, abstract charts; "
            "avoid teenagers, idol lineups, gore, exposed organs."
        )

    if _is_entertainment_news(script):
        guardrails.append(
            "Entertainment/news controversy: frame scenes as modern reporting, audience reaction, press conference, "
            "or behind-the-scenes production. If historical or fantasy drama imagery is needed, show it as a film set "
            "with cameras, lighting rigs, crew, blank monitors, or stage markings. Do not portray fictional palace scenes "
            "as real history. Avoid exact celebrity likeness, logos, readable titles, season text, and fan-poster text."
        )

    return " ".join(guardrails)


def _sd35_panel_role(panel) -> str:
    title = str(getattr(panel, "panel_title", "") or "").strip()
    main_text = str(getattr(panel, "main_text", "") or "").strip()
    callouts = [str(item).strip() for item in (getattr(panel, "callouts", []) or []) if str(item).strip()]
    role_parts = []
    if title:
        role_parts.append(f"planned panel title: {title}")
    if main_text:
        role_parts.append(f"planned overlay idea: {main_text}")
    if callouts:
        role_parts.append("planned callout idea: " + ", ".join(callouts[:2]))
    return "; ".join(role_parts) or "Use the English scene description as the visual source of truth."


def _sd35_focal_evidence(panel) -> str:
    evidence_type = str(getattr(panel, "evidence_type_en", "") or "").strip()
    must_show = [str(item).strip() for item in (getattr(panel, "must_show_en", []) or []) if str(item).strip()]
    proxies = [str(item).strip() for item in (getattr(panel, "proxy_objects_en", []) or []) if str(item).strip()]
    props = [str(item).strip() for item in (getattr(panel, "props_en", []) or []) if str(item).strip()]
    action = str(getattr(panel, "action_en", "") or "").strip()
    foreground = str(getattr(panel, "foreground_subject_en", "") or "").strip()
    evidence = []
    if evidence_type:
        evidence.append(f"evidence role: {evidence_type}")
    if must_show:
        evidence.append("must-show evidence: " + ", ".join(must_show[:3]))
    if proxies:
        evidence.append("proxy objects: " + ", ".join(proxies[:4]))
    if foreground:
        evidence.append(f"foreground subject: {foreground}")
    if action:
        evidence.append(f"visible action: {action}")
    if props:
        evidence.append("key props: " + ", ".join(props[:4]))
    if evidence:
        return _limit_words("; ".join(evidence), 46)

    title = str(getattr(panel, "panel_title", "") or "").strip()
    main_text = str(getattr(panel, "main_text", "") or "").strip()
    visual = str(getattr(panel, "visual", "") or "").strip()
    fallback = "; ".join(part for part in (title, main_text, visual) if part)
    return _limit_words(fallback, 36)


def _sd35_structured_panel_scene(panel) -> str:
    evidence_type = str(getattr(panel, "evidence_type_en", "") or "").strip()
    must_show = [str(item).strip() for item in (getattr(panel, "must_show_en", []) or []) if str(item).strip()]
    proxies = [str(item).strip() for item in (getattr(panel, "proxy_objects_en", []) or []) if str(item).strip()]
    setting = str(getattr(panel, "setting_en", "") or "").strip()
    foreground = str(getattr(panel, "foreground_subject_en", "") or "").strip()
    action = str(getattr(panel, "action_en", "") or "").strip()
    props = [str(item).strip() for item in (getattr(panel, "props_en", []) or []) if str(item).strip()]
    composition = str(getattr(panel, "composition_en", "") or "").strip()
    lighting = str(getattr(panel, "lighting_en", "") or "").strip()
    avoid = [str(item).strip() for item in (getattr(panel, "avoid_en", []) or []) if str(item).strip()]
    callouts = [str(item).strip() for item in (getattr(panel, "callouts", []) or []) if str(item).strip()]

    structured_parts = []
    if evidence_type:
        structured_parts.append(f"Evidence role: {evidence_type}.")
    if must_show:
        structured_parts.append(f"Mandatory must-show evidence: {', '.join(must_show[:3])}.")
    if proxies:
        structured_parts.append(f"Concrete proxy objects: {', '.join(proxies[:4])}.")
    if setting:
        structured_parts.append(f"Setting: {setting}.")
    if foreground:
        structured_parts.append(f"Foreground subject: {foreground}.")
    if action:
        structured_parts.append(f"Visible action: {action}.")
    if props:
        structured_parts.append(f"Visible props: {', '.join(props[:6])}.")
    if callouts:
        structured_parts.append(f"Internal focus cues that must be visually supported by objects/actions: {', '.join(callouts[:3])}.")
    if must_show or proxies or props or callouts:
        structured_parts.append(
            "Make the must-show evidence and key props large, foreground, unobstructed, and easy to recognize at thumbnail size; "
            "the main evidence should occupy roughly one quarter to one third of the image area."
        )
    if composition:
        structured_parts.append(f"Composition: {composition}.")
    if lighting:
        structured_parts.append(f"Lighting and color: {lighting}.")
    if avoid:
        structured_parts.append(f"Panel-specific avoid: {', '.join(avoid[:6])}.")

    if structured_parts:
        return " ".join(structured_parts)

    return (getattr(panel, "visual_prompt_en", "") or "").strip()


def _limit_words(text: str, max_words: int) -> str:
    words = str(text or "").split()
    if len(words) <= max_words:
        return str(text or "").strip()
    return " ".join(words[:max_words]).rstrip(" ,.;:") + "."


def _sd35_plain_scene_rule() -> str:
    return (
        "Make this a plain scene illustration with no graphic overlay layer. "
        "Screens, charts, posters, documents, and signs may show simple non-readable diagrams, icons, shapes, or blank blocks. "
        "Do not render readable text, letters, numbers, captions, logos, labels, or speech bubbles. "
        "Avoid national flags, official seals, and emblem-like symbols unless the scene blueprint explicitly requires them. "
        "Pillow will add only the panel header and short speech text later; focus the generated image on the required physical objects."
    )


def _sd35_story_context(script: ComicPageScript) -> str:
    parts = [
        f"News topic: {script.title}",
        f"Category: {script.news_type}",
        f"Summary: {script.summary}",
    ]
    facts = [str(item).strip() for item in script.allowed_facts[:4] if str(item).strip()]
    if facts:
        parts.append("Key facts: " + "; ".join(facts))
    return _limit_words(". ".join(parts), 54)


def _sd35_character_reference(script: ComicPageScript) -> str:
    references = [str(item).strip() for item in (getattr(script, "character_reference_en", []) or []) if str(item).strip()]
    if not references:
        return ""
    return _limit_words("Character consistency reference: " + " | ".join(references[:4]), 70)


def _sd35_page_visual(script: ComicPageScript) -> str:
    prompt = (getattr(script, "visual_prompt_en", "") or "").strip()
    if prompt:
        return _limit_words(prompt, 34)
    return (
        "A square Traditional Chinese current-affairs news guide manga infographic with clearly separated panels, "
        "headline area, news category badges, attention-level badge, article-specific scenes, "
        "stakeholders, evidence, responses, and next-step visuals."
    )


def _sd35_panel_visuals(script: ComicPageScript) -> str:
    lines = []
    for panel in script.panels:
        prompt = (getattr(panel, "visual_prompt_en", "") or "").strip()
        if not prompt:
            prompt = (
                "A clear editorial news guide panel showing the article's main event, "
                "stakeholders, response, and public reaction, medium-wide manga composition."
            )
        lines.append(f"P{panel.panel_id}: {_limit_words(prompt, 28)}")
    return "\n".join(lines)


def _sd35_infographic_card_rule() -> str:
    return (
        "Gemini-style news explainer direction: each panel should read like a simple illustrated information card, "
        "not a cinematic still. Use one large evidence object, one supporting human reaction or gesture, one simple background proxy "
        "such as a blank poster, phone, photo, map, document, book, screen, chart, product box, or city silhouette, and clean bright color. "
        "Avoid lonely symbolic scenes, vast empty windows, art-film composition, heavy realism, and gray pencil-draft panels."
    )


def _sd35_universal_evidence_rule() -> str:
    return (
        "Universal evidence-role system: every panel must choose a concrete evidence role and show physical proof, not a mood. "
        "For event_scene use a location plus actors plus the key object or action. For data_or_amount use a large blank chart, counter, "
        "stack, pile, map marker, or measured object. For document_or_decision use folders, handoff, podium, meeting table, or blank forms. "
        "For place_or_route use map shapes, route lines as non-readable diagrams, vehicles, stations, doors, or street objects. "
        "For stakeholder_reaction use people holding blank phones, audience seats, comment cards, or discussion table items. "
        "For process_or_timeline use calendar, checklist, ordered objects, repair steps, or workflow table. "
        "For risk_or_warning use warning triangle, barrier, safety gear, damaged object, emergency kit, or alert device. "
        "For impact_or_consequence use affected person, closed shelf, stopped vehicle, bill, damaged site, empty seat, or blocked entrance. "
        "For response_or_solution use worker action, supplies, tools, clinic desk, help counter, or official document handoff. "
        "For future_next_step use calendar, checklist, monitoring screen with abstract shapes, waiting queue, or follow-up meeting. "
        "Do not let generic people, generic rooms, empty screens, scenic backgrounds, or symbolic poses replace the evidence objects."
    )


def _panel_lines(script: ComicPageScript) -> list[str]:
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


def _layout_prompt(script: ComicPageScript) -> str:
    return {
        4: "four-panel grid, two panels on top row and two panels on bottom row",
        5: "five-panel news layout, two panels on top row, two panels in the middle row, one wide panel at the bottom",
        6: "six-panel grid, two columns and three rows",
    }.get(script.panel_count, "balanced multi-panel news comic layout")


def _sd35_layout_prompt(script: ComicPageScript) -> str:
    return {
        4: "four separate rectangles: P1 P2 top row, P3 P4 bottom row",
        5: "five separate rectangles: P1 P2 top row, P3 P4 middle row, P5 wide bottom panel",
        6: "six separate rectangles in a strict two-column by three-row grid",
    }.get(script.panel_count, f"{script.panel_count} separate rectangular comic panels")


def _fact_lines(script: ComicPageScript) -> str:
    return "\n".join(f"- {fact}" for fact in script.allowed_facts) or "- none"


def _locked_text_lines(script: ComicPageScript) -> str:
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


def _build_sd35_medium_prompt(script: ComicPageScript, generation_settings: GenerationSettings | None = None) -> str:
    style_prompt = _sd35_style_prompt(generation_settings)
    color_rule = _sd35_color_consistency_rule(generation_settings)
    page_visual = _sd35_page_visual(script)
    panel_visuals = _sd35_panel_visuals(script)

    clip_prompt = (
        f"A square Traditional Chinese news guide manga infographic with {script.panel_count} separate panels, "
        "visible gutters, clean black panel borders, headline area, category badges, bright flat editorial color, article-specific current-affairs scenes."
    )

    return f"""CLIP prompt:
{clip_prompt}

T5 prompt:
Create one square manga news page with exactly {script.panel_count} panels.
Layout: {_sd35_layout_prompt(script)}.
Direction: {page_visual}
Evidence-role priority: every panel should show physical proof of its news claim through evidence objects and proxy objects, not mood, generic crowds, or symbolism.
{color_rule}
Style: {style_prompt}.
Use visible gutters, black borders, simple illustrated information-card panels, expressive characters, clear environments.
Preserve concrete article facts, people, institutions, places, dates, numbers, impacts, reactions, and next steps through the scene plan.
Match the article shape: crisis, achievement, accident, policy change, investigation, human interest, announcement, trend, or other.
{_sd35_infographic_card_rule()}
{_sd35_universal_evidence_rule()}
Avoid single scene, close-up portrait, generic empty rooms, unrelated trivia, logos, watermarks, readable letters inside the generated illustration.
Panel plan:
{panel_visuals}

Final image: coherent finished manga news page with balanced hierarchy and clear scene changes."""


def build_sd35_panel_prompt(
    script: ComicPageScript,
    panel_id: int,
    generation_settings: GenerationSettings | None = None,
) -> str:
    style_prompt = _sd35_style_prompt(generation_settings)
    panel = next((item for item in script.panels if item.panel_id == panel_id), None)
    if panel is None:
        raise ValueError(f"Panel {panel_id} not found in script.")

    page_visual = _sd35_page_visual(script)
    story_context = _sd35_story_context(script)
    character_reference = _sd35_character_reference(script)
    context_guardrails = _sd35_context_guardrails(script)
    focal_evidence = _sd35_focal_evidence(panel)
    color_rule = _sd35_color_consistency_rule(generation_settings)
    panel_visual = _sd35_structured_panel_scene(panel)
    if not panel_visual:
        panel_visual = (
            "Setting: concrete article-relevant location. Foreground subject: people or objects involved in the news. "
            "Visible action: a clear action that explains the panel. Visible props: unbranded documents, blank screens, tools. "
            "Composition: medium-wide editorial shot. Lighting and color: natural news photography lighting."
        )

    clip_prompt = (
        "A bright editorial manga explainer information-card panel, large obvious key news evidence objects, simplified background, expressive characters, "
        "specific real-world props, clean confident linework, readable composition."
    )
    panel_role = _sd35_panel_role(panel)

    return f"""CLIP prompt:
{clip_prompt}

T5 prompt:
Create one standalone editorial manga news panel.
Evidence-role priority: use the panel's evidence_type_en, must_show_en, and proxy_objects_en as the visual source of truth. Show physical proof of the news claim, not mood or symbolism.
Must visibly prioritize this evidence: {focal_evidence}
Story context for choosing scene only, not for rendering text: {story_context}
{character_reference}
Panel role for choosing scene only, not for rendering text: {panel_role}
Scene blueprint: {_limit_words(panel_visual, 96)}
Context: {_limit_words(page_visual, 18)}
{color_rule}
Style: {style_prompt}; crisp ink, natural hands, clean faces, controlled line density, simplified backgrounds, readable finished comic art.
{_sd35_infographic_card_rule()}
{_sd35_universal_evidence_rule()}
{context_guardrails}
Keep anatomy coherent, faces appealing, body language readable, and the article's specific issue clear through concrete action and props.
Keep recurring characters visually consistent across panels: same apparent age, hair color, hair length, outfit family, body type, and accessories when the same role appears again.
Universal news explainer rule: each panel must visually prove its first callout with one large physical object or action. The main evidence should occupy about 25% to 35% of the image area, sit in the foreground or clear center, and have an uncluttered silhouette. If the news fact is abstract, convert it into a concrete proxy such as sunlight on skin, supplement bottle without text, food tray, blank chart, product box, map, document, equipment, barrier, warning sign, damaged object, supply bag, tool, queue, meeting table, or stakeholder gesture.
Key objects and actions are more important than cinematic beauty or background detail. Make required props and foreground action obvious, centered, large, and unobstructed. Do not let a doctor, expert, official, analyst, student, crowd, room, or screen dominate the frame when a concrete evidence object should be the main subject.
The mandatory evidence is non-negotiable. If the scene becomes crowded, remove decorative background detail first.
Use simple readable shapes and reduce decorative background detail. Avoid rough sketch artifacts, over-sharpened scratch lines, muddy low-contrast areas, unfinished backgrounds, messy micro-lines, distorted faces, inconsistent facial proportions, washed-out monochrome unless requested, and tiny unreadable pseudo-text.
Avoid generic scenery-only panels unless the article is specifically about weather or landscape; include a foreground subject that explains this panel.
{_sd35_plain_scene_rule()}
Fill the illustration naturally from edge to edge without leaving large empty blank areas.
Final image: polished manga news panel with clear storytelling."""


def build_page_prompt(script: ComicPageScript, generation_settings: GenerationSettings | None = None) -> str:
    image_model = getattr(generation_settings, "image_model", "sd35_medium_local") if generation_settings else "sd35_medium_local"
    if image_model == "sd35_medium_local":
        return _build_sd35_medium_prompt(script, generation_settings)
    return _build_gemini_image_prompt(script, generation_settings)
