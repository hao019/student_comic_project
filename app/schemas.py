from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


StylePreset = Literal["balanced", "vivid", "soft", "cinematic"]
SeedMode = Literal["random", "fixed"]
CharacterConsistency = Literal["normal", "strong"]


class NewsInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=1, description="Story or post title")
    content: str = Field(..., min_length=10, description="Story or post content")


class ArticleInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    article: str = Field(..., min_length=3, description="Story, activity, or social post text")
    generation_settings: Optional["GenerationSettings"] = Field(
        default=None,
        description="Optional image generation settings",
    )


class GenerationSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    style_preset: StylePreset = Field(default="cinematic", description="Legacy frontend visual style preset")
    character_consistency: CharacterConsistency = Field(
        default="strong",
        description="Legacy frontend character consistency setting",
    )
    guidance_scale: float = Field(default=5.0, ge=4.0, le=7.0, description="Legacy frontend CFG scale")
    steps: int = Field(default=28, ge=20, le=36, description="Legacy frontend diffusion steps")
    seed_mode: SeedMode = Field(default="random", description="Legacy frontend seed mode")
    seed: Optional[int] = Field(default=None, ge=0, le=999999999, description="Legacy frontend fixed seed")


class NewsComicPagePanel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    panel_id: int = Field(..., ge=1, le=6, description="Panel number")
    panel_title: str = Field(..., min_length=1, description="Short title shown in the panel")
    visual: str = Field(..., min_length=1, description="Visual scene description")
    characters: List[str] = Field(default_factory=list, description="Visible people or groups")
    main_text: str = Field(..., min_length=1, description="Main readable panel text")
    speech: List[str] = Field(default_factory=list, description="Speech bubble text")
    callouts: List[str] = Field(default_factory=list, description="Short label or callout text")


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
