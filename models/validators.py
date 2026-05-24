"""
Pydantic 数据校验（边界校验，不改动现有 dataclass）
在配置加载、种子导入、存档恢复、AI响应解析处做类型校验
"""
from typing import Any, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class APIConfigValidator(BaseModel):
    base_url: str = "https://api.deepseek.com"
    api_key: str = ""
    model: str = "deepseek-v4-flash"

    @field_validator("base_url")
    @classmethod
    def url_must_have_scheme(cls, v):
        if not v.startswith(("http://", "https://")):
            raise ValueError("API地址必须以 http:// 或 https:// 开头")
        return v


class DisplayConfigValidator(BaseModel):
    resolution: str = "1280x720"
    font_family: str = "Microsoft YaHei"
    font_size: int = Field(default=12, ge=8, le=36)
    ui_color: str = "暗夜蓝"

    @field_validator("resolution")
    @classmethod
    def check_resolution_format(cls, v):
        parts = v.split("x")
        if len(parts) != 2:
            raise ValueError("分辨率格式应为 宽x高，如 1280x720")
        w, h = int(parts[0]), int(parts[1])
        if w < 640 or h < 480:
            raise ValueError("分辨率最低 640x480")
        return v


class AudioConfigValidator(BaseModel):
    music_volume: int = Field(default=80, ge=0, le=100)
    sfx_volume: int = Field(default=80, ge=0, le=100)


class ConfigValidator(BaseModel):
    api: APIConfigValidator = Field(default_factory=APIConfigValidator)
    display: DisplayConfigValidator = Field(default_factory=DisplayConfigValidator)
    audio: AudioConfigValidator = Field(default_factory=AudioConfigValidator)


class SeedCharacterValidator(BaseModel):
    name: str = "未命名"
    role: str = "主角"
    description: str = ""
    appearance: str = ""
    background: str = ""
    hp: int = Field(default=100, ge=0)
    max_hp: int = Field(default=100, ge=1)
    mp: int = Field(default=50, ge=0)
    max_mp: int = Field(default=50, ge=1)
    strength: int = Field(default=10, ge=0)
    agility: int = Field(default=10, ge=0)
    intelligence: int = Field(default=10, ge=0)
    charisma: int = Field(default=10, ge=0)
    luck: int = Field(default=5, ge=0)

    @model_validator(mode="after")
    def hp_not_exceed_max(self):
        if self.hp > self.max_hp:
            self.hp = self.max_hp
        return self


class SeedValidator(BaseModel):
    name: str = ""
    genre: str = ""
    era: str = ""
    tone: str = ""
    world_setting: str = ""
    protagonist: SeedCharacterValidator = Field(default_factory=SeedCharacterValidator)
    opening_scene: str = ""
    custom_notes: str = ""
    password: str = ""
    companions: list[dict[str, Any]] = Field(default_factory=list)
    enemies: list[dict[str, Any]] = Field(default_factory=list)

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v):
        if not v.strip():
            raise ValueError("种子名称不能为空")
        return v.strip()


class AIChoiceValidator(BaseModel):
    text: str
    type: str = "select"


class AIResponseValidator(BaseModel):
    story: str = ""
    choices: list[dict[str, Any]] = Field(default_factory=list)
    status_update: dict[str, Any] = Field(default_factory=dict)
    memory_anchor: Optional[dict[str, Any]] = None

    @field_validator("story")
    @classmethod
    def story_not_empty(cls, v):
        if not v.strip():
            raise ValueError("AI返回的故事内容为空")
        return v


class SaveSlotValidator(BaseModel):
    name: str
    modified: str
    path: str


def validate_config(data: dict) -> dict:
    return ConfigValidator(**data).model_dump()


def validate_seed(data: dict) -> dict:
    return SeedValidator(**data).model_dump()


def validate_ai_response(data: dict) -> dict:
    return AIResponseValidator(**data).model_dump()
