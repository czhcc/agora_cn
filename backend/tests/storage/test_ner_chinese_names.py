from unittest.mock import MagicMock

from app.contracts.ner_extraction_contract import NerExtractionResult
from app.storage.ner_extractor import NERExtractor, _SYSTEM_PROMPT


def test_chinese_source_name_and_english_alias_share_relation_endpoint():
    payload = NerExtractionResult.model_validate({
        "entities": [
            {"name": "Jensen Huang", "type": "TechExecutive", "aliases": ["黄仁勋"]},
            {"name": "英伟达", "type": "AICompany", "aliases": ["NVIDIA"]},
        ],
        "relations": [{"source": "Jensen Huang", "target": "NVIDIA", "type": "LEADS", "fact": "黄仁勋领导英伟达。"}],
    })
    result = NERExtractor(llm_client=MagicMock())._validate_and_clean(
        payload.model_dump(), {}, "黄仁勋（Jensen Huang）领导英伟达（NVIDIA）。",
    )
    assert [e["name"] for e in result["entities"]] == ["黄仁勋", "英伟达"]
    assert result["entities"][0]["attributes"]["aliases"] == ["Jensen Huang"]
    assert result["entities"][1]["attributes"]["aliases"] == ["NVIDIA"]
    assert result["relations"] == [{"source": "黄仁勋", "target": "英伟达", "type": "LEADS", "fact": "黄仁勋领导英伟达。"}]


def test_does_not_replace_original_brand_with_unattested_translation():
    result = NERExtractor(llm_client=MagicMock())._validate_and_clean({
        "entities": [{"name": "OpenAI", "type": "AICompany", "aliases": ["开放人工智能"]}],
    }, {}, "OpenAI 发布新模型。")
    assert result["entities"][0]["name"] == "OpenAI"


def test_extraction_prompt_requires_source_language_and_exact_endpoints():
    assert "never translate them into English" in _SYSTEM_PROMPT
    assert "endpoints must exactly match" in _SYSTEM_PROMPT


def test_duplicate_chinese_names_merge_aliases_without_losing_relationships():
    result = NERExtractor(llm_client=MagicMock())._validate_and_clean({
        "entities": [
            {"name": "黄仁勋", "type": "Person"},
            {"name": "黄仁勋", "type": "Person", "aliases": ["Jensen Huang"]},
            {"name": "英伟达", "type": "Company"},
        ],
        "relations": [{"source": "Jensen Huang", "target": "英伟达", "type": "LEADS"}],
    }, {}, "黄仁勋领导英伟达。")
    assert len(result["entities"]) == 2
    assert result["entities"][0]["attributes"]["aliases"] == ["Jensen Huang"]
    assert result["relations"][0]["source"] == "黄仁勋"


def test_ontology_display_labels_are_additive_metadata():
    from app.services.ontology_generator import OntologyEntityType, OntologyEdgeType

    entity = OntologyEntityType(name="AICompany", description="AI company", display_name_zh="人工智能公司")
    edge = OntologyEdgeType(name="LEADS", description="Leads", display_name_zh="领导")
    assert entity.model_dump()["display_name_zh"] == "人工智能公司"
    assert entity.name == "AICompany"
    assert edge.name == "LEADS"
    assert OntologyEntityType(name="Person", description="Person").display_name_zh is None
