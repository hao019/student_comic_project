from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


StylePreset = Literal[
    "default",
    "monochrome_draft",
    "shonen",
    "gag_4koma",
    "infographic",
    "emotional",
    "taiwan_news",
    "internet_meme",
]

ImageModel = Literal[
    "gemini_image",
    "flux_kontext_local",
]


def normalize_string_list(value):
    if value is None:
        return []
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return value


class NewsInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=1, description="Story or post title")
    content: str = Field(..., min_length=10, description="Story or post content")


class ArticleInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    article: str = Field(..., min_length=3, description="Article text or a public news URL")
    generation_settings: Optional["GenerationSettings"] = Field(
        default=None,
        description="Optional image generation settings",
    )


class GenerationSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    style_preset: StylePreset = Field(default="default", description="Comic visual style preset")
    image_model: ImageModel = Field(default="flux_kontext_local", description="Image generation model")


class NewsComicPagePanel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    panel_id: int = Field(..., ge=1, le=6, description="Panel number")
    panel_title: str = Field(..., min_length=1, description="Short title shown in the panel")
    visual: str = Field(..., min_length=1, description="Visual scene description")
    characters: List[str] = Field(default_factory=list, description="Visible people or groups")
    main_text: str = Field(..., min_length=1, description="Main readable panel text")
    speech: List[str] = Field(default_factory=list, description="Speech bubble text")
    callouts: List[str] = Field(default_factory=list, description="Short label or callout text")

    @field_validator("characters", "speech", "callouts", mode="before")
    @classmethod
    def normalize_panel_lists(cls, value):
        return normalize_string_list(value)


class NewsComicPageScript(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=1, description="Comic page title")
    news_type: str = Field(..., min_length=1, description="News category")
    story_shape: str = Field(..., min_length=1, description="Story structure")
    tone: str = Field(..., min_length=1, description="Editorial tone")
    panel_count: int = Field(..., ge=4, le=6, description="Number of panels")
    summary: str = Field(..., min_length=1, description="One sentence news summary")
    allowed_facts: List[str] = Field(default_factory=list, description="Facts, names, and numbers allowed in the image")
    locked_text_blocks: List[str] = Field(default_factory=list, description="Exact short text blocks for the image")
    panels: List[NewsComicPagePanel] = Field(..., min_length=4, max_length=6)
    comic_page_url: Optional[str] = Field(default=None, description="Generated comic page URL")
    comic_error: Optional[str] = Field(default=None, description="Comic generation error")

    @field_validator("allowed_facts", "locked_text_blocks", mode="before")
    @classmethod
    def normalize_script_lists(cls, value):
        return normalize_string_list(value)
