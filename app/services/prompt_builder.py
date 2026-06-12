from app.schemas import NewsComicPageScript


def build_page_prompt(script: NewsComicPageScript) -> str:
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

    layout = {
        4: "four-panel grid, two panels on top row and two panels on bottom row",
        5: "five-panel news layout, two panels on top row, two panels in the middle row, one wide panel at the bottom",
        6: "six-panel grid, two columns and three rows",
    }.get(script.panel_count, "balanced multi-panel news comic layout")
    allowed_facts = "\n".join(f"- {fact}" for fact in script.allowed_facts) or "- none"
    locked_text = "\n".join(f"- {text}" for text in script.locked_text_blocks) or "- none"

    return f"""Create a complete one-page Traditional Chinese news explainer manga infographic.

Overall style:
clean editorial manga, soft watercolor color, ink outlines, newspaper comic page,
clear black panel borders, balanced text boxes, readable Traditional Chinese text.

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
