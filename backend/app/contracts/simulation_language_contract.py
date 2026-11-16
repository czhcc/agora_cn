"""Supported simulation output languages, independent of UI and report locale."""

import re
from typing import Literal, cast

from pydantic import BaseModel

SimulationLanguage = Literal["de", "en", "zh"]
SIMULATION_LANGUAGES: tuple[SimulationLanguage, ...] = ("de", "en", "zh")


class SimulationLanguageSelection(BaseModel):
    language: SimulationLanguage | None = None


def parse_simulation_language(value: object) -> SimulationLanguage | None:
    """Keep the prepare API's absent/unsupported-value semantics."""
    if not isinstance(value, str):
        return None
    normalized = value.strip().lower()
    if normalized in SIMULATION_LANGUAGES:
        return cast(SimulationLanguage, normalized)
    return None


def simulation_language_name(value: object) -> str:
    return {"de": "German", "en": "English", "zh": "Simplified Chinese"}[
        parse_simulation_language(value) or "de"
    ]


def simulation_language_instruction(value: object) -> str:
    return (
        f"Write all natural-language output in {simulation_language_name(value)}. "
        "Keep JSON keys, enum values, identifiers and source names unchanged."
    )


def synthetic_persona_name_instruction(value: object) -> str:
    """Naming applies to invented people; source-bound identities stay locked."""
    if parse_simulation_language(value) == "zh":
        return (
            "For synthetic individual personas, display_name must be a realistic Chinese "
            "personal name of 2-4 Han characters, surname first. Do not use English names, "
            "pinyin or DACH name-origin quotas. Preserve source-bound real-person names "
            "and collective organization names; never replace them with invented people."
        )
    return ""


def is_chinese_persona_name(value: str) -> bool:
    """Validate the display name of a synthetic Chinese-language individual."""
    return re.fullmatch(r"[\u3400-\u9fff]{2,4}", value) is not None
