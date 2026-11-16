"""Separate model instructions from the question shown in interview history."""

from typing import Literal

from pydantic import BaseModel

REPORT_QUESTION_MARKER = "\n[AGORA_REPORT_INTERVIEW_QUESTIONS]\n"
REPORT_PREFIX = "You are being interviewed. Draw on your character profile and on whatever "
USER_PREFIX = "Based on your persona, all your past memories and actions, reply directly to me with text without calling any tools:"
LEGACY_REPORT_END = "Write this line only once, at the very end.\n"


class InterviewPromptPresentation(BaseModel):
    display_prompt: str
    origin: Literal["user", "report", "unknown"] = "unknown"


def present_interview_prompt(prompt: str) -> InterviewPromptPresentation:
    """Recognize only application-owned wrappers; leave ambiguous text intact."""
    text = prompt
    origin: Literal["user", "report", "unknown"] = "unknown"
    if text.startswith(USER_PREFIX):
        text = text[len(USER_PREFIX):].lstrip()
        origin = "user"
    if text.startswith(REPORT_PREFIX):
        if REPORT_QUESTION_MARKER in text:
            return InterviewPromptPresentation(display_prompt=text.split(REPORT_QUESTION_MARKER, 1)[1], origin="report")
        if LEGACY_REPORT_END in text:
            return InterviewPromptPresentation(display_prompt=text.split(LEGACY_REPORT_END, 1)[1].lstrip(), origin="report")
    return InterviewPromptPresentation(display_prompt=text, origin=origin)
