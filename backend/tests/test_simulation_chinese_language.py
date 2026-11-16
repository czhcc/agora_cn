"""Chinese output must survive preparation and both runtime action paths."""

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.contracts.simulation_language_contract import (
    SimulationLanguageSelection,
    parse_simulation_language,
)
from app.services.oasis_profile_generator import OasisProfileGenerator
from app.services.simulation_config_events import _generate_event_config

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))


@pytest.mark.parametrize("language", ["de", "en", "zh"])
def test_supported_languages(language):
    assert parse_simulation_language(f" {language.upper()} ") == language
    assert SimulationLanguageSelection(language=language).language == language


@pytest.mark.parametrize("value", [None, 5, "fr", ""])
def test_invalid_prepare_language_remains_absent(value):
    assert parse_simulation_language(value) is None


def test_chinese_persona_prompts_keep_schema_and_identity_rules():
    generator = OasisProfileGenerator(api_key="test", base_url="https://example.test/v1", language="zh")
    assert "Simplified Chinese" in generator._get_system_prompt(True)
    for method in (generator._build_individual_persona_prompt, generator._build_group_persona_prompt):
        prompt = method("Source entity", "Person", "Summary", {}, "Context")
        assert "Simplified Chinese" in prompt
        assert "Use English" not in prompt
        assert "voice_register" in prompt
    for kind in ("individual", "collective"):
        prompt = generator._build_drift_correction_prompt(
            entity_name="Source", entity_type="Person", persona_kind=kind,
            profession="", bio="", persona_text="", drifted_domains=["IT"], source_text="Source",
        )
        assert "Simplified Chinese" in prompt
        assert "empty string for profession" in prompt


def test_initial_posts_are_generated_in_chinese():
    generator = SimpleNamespace(
        language="zh", EVENT_CONFIG_CONTEXT_LENGTH=1000, _call_llm_with_retry=MagicMock(return_value={}),
    )
    _generate_event_config(generator, "Context", "Question", [])
    _, system_prompt, _ = generator._call_llm_with_retry.call_args.args
    assert "Simplified Chinese" in system_prompt
    assert "enum values" in system_prompt


def test_chinese_runtime_updates_live_original_and_memory_prompts():
    from simulation_language import apply_simulation_language

    agent = SimpleNamespace(
        system_message=SimpleNamespace(content="Persona"),
        _original_system_message=SimpleNamespace(content="Persona"), init_messages=MagicMock(),
    )
    graph = SimpleNamespace(get_agents=lambda: [(0, agent)])
    apply_simulation_language(graph, "zh")
    apply_simulation_language(graph, "zh")
    assert agent.system_message.content.count("Simplified Chinese") == 1
    assert agent._original_system_message.content == agent.system_message.content
    agent.init_messages.assert_called_once()


def test_tool_action_prompt_requires_chinese():
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    from agent_tools import build_agent_prompt_with_tools

    tools = MagicMock()
    tools.get_tools_description.return_value = "Tools"
    prompt = build_agent_prompt_with_tools("Name", "Role", "Bio", "Feed", ["CREATE_POST"], tools, language="zh")
    assert "ALWAYS respond in Simplified Chinese" in prompt


@pytest.mark.asyncio
@pytest.mark.parametrize("language,expected", [("de", "German"), ("en", "English"), ("zh", "Simplified Chinese")])
async def test_oasis_interview_keeps_language_before_response_format(language, expected):
    from oasis.social_agent.agent import SocialAgent
    from simulation_language import apply_simulation_language

    original = "Persona description\n# RESPONSE FORMAT\nSimulation action format"
    agent = SimpleNamespace(
        social_agent_id=1, interview_record=False,
        system_message=SimpleNamespace(role_name="system", content=original),
        _original_system_message=SimpleNamespace(content=original),
        init_messages=MagicMock(), memory=MagicMock(),
        _aget_model_response=AsyncMock(return_value=SimpleNamespace(
            output_messages=[SimpleNamespace(content="模拟回复")],
        )),
        env=SimpleNamespace(action=SimpleNamespace(
            perform_action=AsyncMock(return_value={"success": True}),
        )),
    )
    agent.memory.get_context.return_value = ([], 0)
    graph = SimpleNamespace(get_agents=lambda: [(1, agent)])
    apply_simulation_language(graph, language)
    apply_simulation_language(graph, language)
    result = await SocialAgent.perform_interview(agent, "请重述你的观点。")
    messages = agent._aget_model_response.call_args.kwargs["openai_messages"]
    assert f"Write all natural-language output in {expected}" in messages[0]["content"]
    assert "# RESPONSE FORMAT" not in messages[0]["content"]
    assert agent._original_system_message.content.count(expected) == 1
    agent.init_messages.assert_called_once()
    assert result["success"] is True
    assert messages[-1]["content"] == "请重述你的观点。"


def test_synthetic_skeptic_profile_is_chinese():
    from app.services.prepare_skeptic_profiles import build_skeptic_profiles

    profiles = build_skeptic_profiles({"agent_configs": [{
        "agent_id": 1, "entity_uuid": "synthetic-skeptic-1", "entity_name": "Skeptic",
    }]}, [], language="zh")
    assert len(profiles) == 1
    assert "反对" in profiles[0].bio
    assert "不要编造" in profiles[0].persona
