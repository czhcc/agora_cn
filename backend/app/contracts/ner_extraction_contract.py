"""Source-language entity names and unchanged ontology identifiers for extraction."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class NerEntity(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    name: str = Field(min_length=1, description="Entity name in the source language; preserve Chinese names, never romanize or translate them.")
    type: str = Field(default="Entity", description="Exact ontology type identifier, unchanged.")
    aliases: list[str] = Field(default_factory=list, description="Alternative names attested in the input, including English equivalents when provided.")
    attributes: dict[str, Any] = Field(default_factory=dict)


class NerRelation(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    source: str = Field(min_length=1, description="Exact extracted entity name, in its source language.")
    target: str = Field(min_length=1, description="Exact extracted entity name, in its source language.")
    type: str = "RELATED_TO"
    fact: str = Field(default="", description="Relationship fact in the source language.")


class NerExtractionResult(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    entities: list[NerEntity] = Field(default_factory=list)
    relations: list[NerRelation] = Field(default_factory=list)
