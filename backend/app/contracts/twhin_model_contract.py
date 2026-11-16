"""Optional local source for the Twitter recommender model."""

from pathlib import Path

from pydantic import BaseModel, ConfigDict, field_validator

TWHIN_MODEL_DIR_ENV = "AGORA_TWHIN_BERT_MODEL_DIR"


class TwhinModelSource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    local_model_dir: Path | None = None

    @field_validator("local_model_dir", mode="before")
    @classmethod
    def empty_directory_means_default(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip() or None
        return value
