from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


StylePreset = Literal[
    "default",
    "monochrome_draft",
    "realistic_people",
]

ImageModel = Literal[
    "gemini_image",
    "sd35_medium_local",
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
    image_model: ImageModel = Field(default="sd35_medium_local", description="Image generation model")
    sd35: Optional["SD35GenerationSettings"] = Field(
        default=None,
        description="Optional SD3.5 local image generation parameters",
    )

    @model_validator(mode="after")
    def enforce_style_model_compatibility(self):
        if self.style_preset == "realistic_people":
            self.image_model = "gemini_image"
        return self


class SD35GenerationSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    steps: Optional[int] = Field(default=None, ge=1, le=100, description="SD3.5 inference steps")
    width: Optional[int] = Field(default=None, ge=256, le=2048, description="SD3.5 target width or panel size baseline")
    height: Optional[int] = Field(default=None, ge=256, le=2048, description="SD3.5 target height or panel size baseline")
    guidance_scale: Optional[float] = Field(default=None, ge=0, le=20, description="SD3.5 CFG/FPG guidance scale")
    seed: Optional[int] = Field(default=None, ge=0, le=2147483647, description="Optional generation seed")
    max_sequence_length: Optional[int] = Field(default=None, ge=64, le=1024, description="SD3.5 T5 max sequence length")


class NewsComicPagePanel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    panel_id: int = Field(..., ge=1, le=6, description="Panel number")
    panel_title: str = Field(..., min_length=1, description="Short title shown in the panel")
    visual: str = Field(..., min_length=1, description="Visual scene description")
    visual_prompt_en: str = Field(default="", description="English visual prompt for SD3.5 image generation")
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
    visual_prompt_en: str = Field(default="", description="English page-level visual prompt for SD3.5 image generation")
    allowed_facts: List[str] = Field(default_factory=list, description="Facts, names, and numbers allowed in the image")
    locked_text_blocks: List[str] = Field(default_factory=list, description="Exact short text blocks for the image")
    panels: List[NewsComicPagePanel] = Field(..., min_length=4, max_length=6)
    comic_page_url: Optional[str] = Field(default=None, description="Generated comic page URL")
    comic_error: Optional[str] = Field(default=None, description="Comic generation error")

    @field_validator("allowed_facts", "locked_text_blocks", mode="before")
    @classmethod
    def normalize_script_lists(cls, value):
        return normalize_string_list(value)


class SD35ComicPagePanel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    panel_id: int = Field(..., ge=1, le=6, description="Panel number")
    panel_title: str = Field(..., min_length=1, description="Short title shown in the composed panel")
    visual: str = Field(..., min_length=1, description="Traditional Chinese scene note for storyboard review")
    visual_prompt_en: str = Field(default="", description="Backup English prompt for one SD3.5 panel image")
    evidence_type_en: str = Field(default="", description="Generic news evidence role for this panel")
    must_show_en: List[str] = Field(default_factory=list, description="Mandatory visible evidence objects or actions for SD3.5")
    proxy_objects_en: List[str] = Field(default_factory=list, description="Concrete proxy objects that turn abstract news into visible evidence")
    setting_en: str = Field(default="", description="Concrete physical setting for SD3.5")
    foreground_subject_en: str = Field(default="", description="Main visible foreground subject for SD3.5")
    action_en: str = Field(default="", description="Visible action or state for SD3.5")
    props_en: List[str] = Field(default_factory=list, description="Concrete visible props for SD3.5")
    composition_en: str = Field(default="", description="Camera distance, angle, and framing for SD3.5")
    lighting_en: str = Field(default="", description="Lighting and color direction for SD3.5")
    avoid_en: List[str] = Field(default_factory=list, description="Panel-specific visual avoid list for SD3.5")
    characters: List[str] = Field(default_factory=list, description="Visible people or groups")
    main_text: str = Field(..., min_length=1, description="Main readable overlay text added by Pillow")
    speech: List[str] = Field(default_factory=list, description="Short overlay narration lines")
    callouts: List[str] = Field(default_factory=list, description="Short overlay label text")

    @field_validator("characters", "speech", "callouts", "must_show_en", "proxy_objects_en", "props_en", "avoid_en", mode="before")
    @classmethod
    def normalize_panel_lists(cls, value):
        return normalize_string_list(value)


class SD35ComicPageScript(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=1, description="Comic page title drawn by Pillow")
    news_type: str = Field(..., min_length=1, description="News category")
    story_shape: str = Field(..., min_length=1, description="Story structure")
    tone: str = Field(..., min_length=1, description="Editorial tone")
    panel_count: int = Field(..., ge=4, le=6, description="Number of generated panels")
    summary: str = Field(..., min_length=1, description="One sentence news summary")
    visual_prompt_en: str = Field(default="", description="Page-level SD3.5 visual style and continuity prompt")
    character_reference_en: List[str] = Field(default_factory=list, description="Reusable character design notes for SD3.5 consistency")
    allowed_facts: List[str] = Field(default_factory=list, description="Facts allowed in storyboard text")
    locked_text_blocks: List[str] = Field(default_factory=list, description="Exact overlay text blocks")
    panels: List[SD35ComicPagePanel] = Field(..., min_length=4, max_length=6)
    comic_page_url: Optional[str] = Field(default=None, description="Generated comic page URL")
    comic_error: Optional[str] = Field(default=None, description="Comic generation error")

    @field_validator("character_reference_en", "allowed_facts", "locked_text_blocks", mode="before")
    @classmethod
    def normalize_script_lists(cls, value):
        return normalize_string_list(value)
