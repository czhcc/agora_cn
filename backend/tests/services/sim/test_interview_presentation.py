import pytest

from app.contracts.interview_presentation_contract import (
    LEGACY_REPORT_END, REPORT_PREFIX, REPORT_QUESTION_MARKER, USER_PREFIX,
    present_interview_prompt,
)
from app.services.interview_stance import stance_prompt_requirement
from app.services.sim.interview_client import get_interview_history


@pytest.mark.parametrize('statement', [None, '你认为人工智能发展过快吗？'])
@pytest.mark.parametrize('wrapped', [False, True])
def test_old_report_history_hides_instructions_but_keeps_questions(statement, wrapped):
    question = '1. 你怎么看？\n2. 为什么？'
    raw = REPORT_PREFIX + 'other instructions\n' + stance_prompt_requirement(statement) + question
    if wrapped:
        raw = USER_PREFIX + raw
    result = present_interview_prompt(raw)
    assert result.origin == 'report'
    assert result.display_prompt == question


def test_new_report_marker_and_ambiguous_user_text():
    raw = REPORT_PREFIX + 'instructions' + REPORT_QUESTION_MARKER + '1. 观点？'
    assert present_interview_prompt(raw).display_prompt == '1. 观点？'
    assert present_interview_prompt('user quotes: ' + LEGACY_REPORT_END + 'question').origin == 'unknown'
    assert present_interview_prompt(REPORT_PREFIX + 'incomplete wrapper').display_prompt == REPORT_PREFIX + 'incomplete wrapper'
    assert present_interview_prompt(USER_PREFIX + '真实问题').origin == 'user'


def test_history_adds_presentation_fields_without_changing_stored_prompt(tmp_path, monkeypatch):
    raw = REPORT_PREFIX + 'instructions' + REPORT_QUESTION_MARKER + '1. 真实问题？'
    row = {'agent_id': 1, 'prompt': raw, 'response': '回答', 'timestamp': '2026-11-16'}
    monkeypatch.setattr('app.services.sim.interview_client._get_interview_history_from_db', lambda **kwargs: [dict(row)])
    result = get_interview_history('sim_test', platform='reddit', run_state_dir=str(tmp_path))
    assert result[0]['display_prompt'] == '1. 真实问题？'
    assert result[0]['origin'] == 'report'
    assert result[0]['prompt'] == raw
    assert result[0]['response'] == '回答'
