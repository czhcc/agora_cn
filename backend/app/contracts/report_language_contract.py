"""Canonical report language aliases, independent of UI and simulation locale."""

from typing import Literal

from pydantic import BaseModel, ConfigDict

ReportLanguage = Literal["de", "en", "zh"]


class ReportQuoteLabels(BaseModel):
    """Presentation labels for simulated quotes; evidence identifiers stay intact."""

    model_config = ConfigDict(frozen=True)

    title: str
    details: str
    persona: str
    evidence: str
    unknown: str


def report_quote_labels(raw: str | None) -> ReportQuoteLabels:
    language = resolve_report_language(raw)
    if language == "zh":
        return ReportQuoteLabels(title="模拟人物发言", details="引用详情", persona="人物标识（persona_id）", evidence="证据编号（seed_anchor）", unknown="未知")
    if language == "en":
        return ReportQuoteLabels(title="Simulated persona statement", details="Citation details", persona="persona_id", evidence="seed_anchor", unknown="unknown")
    return ReportQuoteLabels(title="Simulierter Persona-O-Ton", details="Zitatdetails", persona="persona_id", evidence="seed_anchor", unknown="unbekannt")


def resolve_report_language(raw: str | None) -> ReportLanguage:
    value = (raw or "").strip().lower().replace("_", "-")
    if value in {"zh", "zh-cn", "zh-hans", "chinese", "simplified chinese", "中文", "简体中文"}:
        return "zh"
    if value.startswith("en"):
        return "en"
    return "de"


def report_language_name(raw: str | None) -> str:
    """Use explicit language names in model prompts; retain custom languages."""
    language = resolve_report_language(raw)
    if language == "zh":
        return "Simplified Chinese"
    if language == "en":
        return "English"
    value = (raw or "").strip()
    if not value or value.lower().startswith(("de", "ger")):
        return "German"
    return value


def report_language_instruction(raw: str | None) -> str:
    return (
        f"Write all generated natural-language output in {report_language_name(raw)}. "
        "Keep JSON keys, enum values, identifiers and verbatim source evidence unchanged."
    )
