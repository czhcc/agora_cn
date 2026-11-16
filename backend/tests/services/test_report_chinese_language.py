"""Chinese report prompts and completeness checks must use the same locale."""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from app.config import Config
from app.contracts.report_language_contract import report_language_name, resolve_report_language
from app.contracts.report_v3 import ReportV3
from app.services.report_agent.agent import ReportAgent
from app.services.report_agent.planning import plan_outline
from app.services.report_agent.requirement_checker import (
    DEFAULT_REQUIREMENT_CHECKLIST,
    checklist_for_intent,
    find_missing_requirements,
)
from app.services.report_agent.workflow_finalization import (
    _run_red_team_review,
    generate_section_metadata,
)
from app.services.report_agent.workflow_react import _build_initial_section_messages
from app.services.report_agent import workflow
from app.services.report_intent import ReportIntent


@pytest.mark.parametrize("alias", ["zh", "zh-CN", "zh_Hans", "Chinese", "Simplified Chinese", "中文", "简体中文"])
def test_chinese_aliases_share_generation_and_checking_language(alias):
    assert resolve_report_language(alias) == "zh"
    assert report_language_name(alias) == "Simplified Chinese"


@pytest.mark.parametrize("raw,code,name", [(None, "de", "German"), ("de", "de", "German"), ("German", "de", "German"), ("en", "en", "English"), ("English", "en", "English")])
def test_existing_languages(raw, code, name):
    assert resolve_report_language(raw) == code
    assert report_language_name(raw) == name


CHINESE_ASPECTS = (
    "利益相关者存在分歧，劳资双方的冲突尚未解决。",
    "预警指标是参与度持续下降。",
    "停止条件：投诉率超过阈值时暂停实施。",
    "扩大推广的条件：试点通过验收后逐步推广。",
    "未观察到立场变化。",
    "尚未形成联盟。",
)


def test_complete_chinese_report_uses_configured_language(monkeypatch):
    monkeypatch.setattr(Config, "REPORT_LANGUAGE", "Simplified Chinese")
    assert find_missing_requirements(CHINESE_ASPECTS) == []


@pytest.mark.parametrize("index", range(6))
def test_missing_chinese_aspect_remains_blocking(index):
    texts = CHINESE_ASPECTS[:index] + CHINESE_ASPECTS[index + 1:]
    missing = find_missing_requirements(texts, language="zh")
    assert [req.id for req in missing] == [DEFAULT_REQUIREMENT_CHECKLIST[index].id]


def test_chinese_checker_does_not_accept_unrelated_or_foreign_text():
    assert len(find_missing_requirements(["模拟进行了二十四轮，参与者发布了帖子。"], language="zh")) == 6
    assert len(find_missing_requirements(["Widersprüche, Frühwarnindikatoren, Stopkriterien, Ausweitungskriterien, Positionswechsel, Koalitionen."], language="zh")) == 6


def test_chinese_pilot_question_keeps_stop_and_expand_checks():
    requirements = checklist_for_intent(ReportIntent.FULL, has_contested_question=False, simulation_requirement="分阶段试点并逐步推广")
    assert {req.id for req in requirements} == {
        "stakeholder_widersprueche", "fruehwarnindikatoren", "stop_bedingungen", "expand_bedingungen",
    }


def _agent():
    agent = MagicMock()
    agent.graph_tools.get_simulation_context.return_value = {}
    agent.simulation_requirement = "评估试点方案"
    agent.llm.provider = "openai_compatible"
    agent.llm.model = "test-model"
    agent.SECTION_SYSTEM_PROMPT_TEMPLATE = ReportAgent.SECTION_SYSTEM_PROMPT_TEMPLATE
    agent.SECTION_USER_PROMPT_TEMPLATE = ReportAgent.SECTION_USER_PROMPT_TEMPLATE
    return agent


def test_outline_and_sections_request_chinese(monkeypatch):
    monkeypatch.setattr(Config, "REPORT_LANGUAGE", "zh")
    agent = _agent()
    agent.llm.chat_json.return_value = {
        "title": "试点评估", "summary": "模拟结果", "sections": [
            {"title": "利益相关者反应", "description": "分析分歧", "section_kind": "stakeholder_voices"},
        ],
    }
    outline = plan_outline(agent)
    assert "MUST be written in Simplified Chinese" in agent.llm.chat_json.call_args.kwargs["messages"][0]["content"]
    messages = _build_initial_section_messages(agent, outline.sections[0], outline, [])
    assert "MUST be written in Simplified Chinese" in messages[0]["content"]
    assert outline.sections[0].kind == "stakeholder_voices"


@pytest.mark.parametrize("language,expected", [("zh", "Simplified Chinese"), ("en", "English"), ("German", "German")])
def test_red_team_and_metadata_follow_report_language(monkeypatch, language, expected):
    monkeypatch.setattr(Config, "REPORT_LANGUAGE", language)
    agent = _agent()
    agent.llm.chat_json.return_value = {"findings": ["审查结果"]}
    report = ReportV3(report_id="chinese-report", generated_at=datetime.now(timezone.utc))
    _run_red_team_review(agent, report, 0.8, intent=ReportIntent.FULL)
    prompt = agent.llm.chat_json.call_args.kwargs["messages"][0]["content"]
    assert f"natural-language output in {expected}" in prompt
    assert "ausschliesslich auf Deutsch" not in prompt
    generate_section_metadata(agent, "分析结论", "存在分歧。", 1)
    prompt = agent.llm.chat_json.call_args.kwargs["messages"][0]["content"]
    assert f"natural-language output in {expected}" in prompt
    assert "Keep JSON keys, enum values, identifiers and verbatim source evidence unchanged" in prompt


@pytest.mark.parametrize("mode", ["native", "xml"])
def test_report_chat_follows_chinese_language(monkeypatch, mode):
    monkeypatch.setattr(Config, "REPORT_LANGUAGE", "zh-CN")
    monkeypatch.setattr(Config, "REPORT_TOOLCALL_MODE", mode)
    monkeypatch.setattr(workflow.ReportManager, "get_report_by_simulation", lambda _: None)
    agent = _agent()
    agent.CHAT_SYSTEM_PROMPT_TEMPLATE = ReportAgent.CHAT_SYSTEM_PROMPT_TEMPLATE
    agent._parse_tool_calls.return_value = []
    agent.llm.chat.return_value = "模拟中存在分歧。"
    agent.llm.chat_with_tools.return_value = {"content": "模拟中存在分歧。", "tool_calls": []}
    result = workflow.chat(agent, "有什么主要发现？")
    call = agent.llm.chat_with_tools if mode == "native" else agent.llm.chat
    assert "ALWAYS respond in Simplified Chinese" in call.call_args.kwargs["messages"][0]["content"]
    assert result["response"] == "模拟中存在分歧。"
