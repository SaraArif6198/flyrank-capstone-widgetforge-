from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

RESERVED_FIELD_NAMES = {"website", "widget_id", "fields"}


class FormField(BaseModel):
    name: str = Field(pattern=r"^[a-z][a-z0-9_]{0,39}$")
    label: str = Field(min_length=1, max_length=80)
    type: Literal["text", "email"]
    required: bool = False
    max_length: int = Field(default=120, ge=1, le=254)

    @field_validator("name")
    @classmethod
    def name_must_not_be_reserved(cls, value: str) -> str:
        if value in RESERVED_FIELD_NAMES:
            raise ValueError("Field name is reserved")
        return value


class WidgetBase(BaseModel):
    widget_type: Literal["signup", "contact"]
    title: str = Field(min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=1000)
    form_fields: list[FormField] = Field(min_length=1, max_length=8)
    button_text: str = Field(min_length=1, max_length=80)
    display_options: dict = Field(default_factory=dict)

    @model_validator(mode="after")
    def field_names_are_unique(self):
        names = [field.name for field in self.form_fields]
        if len(names) != len(set(names)):
            raise ValueError("Field names must be unique")
        return self


class WidgetCreate(WidgetBase):
    pass


class WidgetUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    widget_type: Literal["signup", "contact"] | None = None
    title: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=1000)
    form_fields: list[FormField] | None = Field(default=None, min_length=1, max_length=8)
    button_text: str | None = Field(default=None, min_length=1, max_length=80)
    display_options: dict | None = None
    is_active: bool | None = None

    @model_validator(mode="after")
    def update_field_names_are_unique(self):
        if self.form_fields is not None:
            names = [field.name for field in self.form_fields]
            if len(names) != len(set(names)):
                raise ValueError("Field names must be unique")
        return self


class WidgetResponse(WidgetBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    public_id: str
    is_active: bool
    config_version: int


class EmbedResponse(BaseModel):
    snippet: str
