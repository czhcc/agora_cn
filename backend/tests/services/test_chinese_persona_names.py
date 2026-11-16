from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.contracts.persona_identity_contract import PersonaIdentityBinding
from app.contracts.simulation_language_contract import is_chinese_persona_name
from app.services.oasis_profile_core import _model_identity
from app.services.oasis_profile_demographics import pick_persona_name
from app.services.oasis_profile_generator import OasisProfileGenerator
from app.services.oasis_profile_batch import _dedupe_profile_names


@pytest.mark.parametrize('origin', ['synthetic_representative', 'synthetic_supplement'])
def test_english_model_name_becomes_chinese_for_synthetic_person(origin):
    generator = OasisProfileGenerator(api_key='test', base_url='http://localhost', language='zh')
    data = {'display_name': 'Sabine Weber', 'bio': 'Sabine Weber 关注人工智能。', 'persona': 'Sabine Weber 是一名研究者。'}
    name, _ = _model_identity(generator, data, PersonaIdentityBinding(origin=origin, source_name='研究者'), '研究者', 'researcher')
    assert is_chinese_persona_name(name)
    assert name in data['bio']
    assert name in data['persona']
    assert 'Sabine Weber' not in data['persona']


@pytest.mark.parametrize('name', ['王文清', '欧阳明远'])
def test_valid_chinese_model_name_is_preserved(name):
    generator = SimpleNamespace(language='zh')
    result, _ = _model_identity(generator, {'display_name': name}, PersonaIdentityBinding(origin='synthetic_supplement', source_name='研究者'), '研究者', 'researcher')
    assert result == name


@pytest.mark.parametrize('origin,name', [('source_person', '黄仁勋'), ('source_person', 'Jensen Huang'), ('source_collective', 'OpenAI')])
def test_source_identities_are_never_replaced(origin, name):
    result, _ = _model_identity(SimpleNamespace(language='zh'), {'display_name': '王文清'}, PersonaIdentityBinding(origin=origin, source_name=name), name, 'source')
    assert result == name


def test_chinese_prompt_uses_chinese_naming_instead_of_dach_distribution():
    generator = OasisProfileGenerator(api_key='test', base_url='http://localhost', language='zh')
    prompt = generator._build_individual_persona_prompt('研究者', 'Person', '研究人工智能', {}, '')
    assert '2-4 Han characters' in prompt
    assert 'DACH Mikrozensus 2024' not in prompt
    assert 'surname first' in prompt


def test_rule_based_payload_and_collision_renaming_use_chinese_names():
    generator = OasisProfileGenerator(api_key='test', base_url='http://localhost', language='zh')
    data = generator._build_generic_person_payload(entity_name='研究者', entity_type='Person', entity_summary='关注人工智能', assigned_gender='female', assigned_age=35, assigned_mbti='INTJ')
    assert is_chinese_persona_name(data['display_name'])
    profiles = [SimpleNamespace(name='王文清', user_name=f'agent_{i}', gender='female', persona_kind='individual', bio='王文清关注人工智能', persona='王文清关注人工智能') for i in range(2)]
    _dedupe_profile_names(generator, profiles)
    assert profiles[0].name != profiles[1].name
    assert all(is_chinese_persona_name(p.name) for p in profiles)
    assert profiles[1].name in profiles[1].persona


def test_batch_emergency_profile_with_english_name_is_normalized():
    generator = OasisProfileGenerator(api_key='test', base_url='http://localhost', language='zh')
    profile = SimpleNamespace(name='Sabine Weber', user_name='sabine', gender='female', persona_kind='individual', bio='Sabine Weber关注人工智能', persona='Sabine Weber关注人工智能')
    _dedupe_profile_names(generator, [profile])
    assert is_chinese_persona_name(profile.name)
    assert profile.name in profile.persona


@pytest.mark.parametrize('language', ['de', 'en'])
def test_other_languages_keep_existing_name_picker(language):
    generator = SimpleNamespace(language=language, _pick_dach_name=MagicMock(return_value='Sabine Weber'))
    assert pick_persona_name(generator, 'female') == 'Sabine Weber'
    generator._pick_dach_name.assert_called_once_with('female')
