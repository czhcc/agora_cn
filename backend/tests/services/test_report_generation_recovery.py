"""Regressions from the local completed simulation and Chinese report run."""

import json
from unittest.mock import MagicMock

import pytest
from flask import Flask
from pydantic import ValidationError

from app.api import report_bp
from app.contracts.report_v3 import Threshold
from app.services.report_agent.manager import ReportManager
from app.services.report_agent.output_contract import sanitize_final_content
from app.services.report_agent.run_degradation import events_for
from app.services.report_agent.workflow_finalization import generate_section_metadata
from app.services.sim import process_termination
from app.services.sim.run_state_store import RunnerStatus, SimulationRunState


@pytest.mark.parametrize("status", [RunnerStatus.COMPLETED, RunnerStatus.FAILED, RunnerStatus.STOPPED, RunnerStatus.RUNNING])
def test_shutdown_preserves_terminal_outcome_but_terminates_idle_process(monkeypatch, status):
    process = MagicMock()
    process.poll.return_value = None
    state = SimulationRunState(simulation_id="sim_completed", runner_status=status)
    state.current_round = state.total_rounds = 24
    state.completed_at = "2026-11-16T14:33:18"
    state.error = None if status == RunnerStatus.COMPLETED else "original reason"
    original = (state.runner_status, state.completed_at, state.error)
    terminate = MagicMock()
    save = MagicMock()
    store_update = MagicMock()
    monkeypatch.setattr(process_termination, "terminate_process", terminate)
    process_termination.cleanup_all_simulations(
        processes={"sim_completed": process}, stdout_files={}, stderr_files={},
        graph_memory_enabled={}, action_queues={}, get_run_state=lambda _: state,
        save_state=save, stop_all_graph_memory=lambda: None,
        update_store_state=store_update, cleanup_done_flag=[False],
    )
    terminate.assert_called_once()
    if status == RunnerStatus.RUNNING:
        assert state.runner_status == RunnerStatus.STOPPED
        assert state.error == "Server closed, simulation terminated"
        save.assert_called_once_with(state)
        store_update.assert_called_once_with("sim_completed")
    else:
        assert (state.runner_status, state.completed_at, state.error) == original
        save.assert_not_called()
        store_update.assert_not_called()


def test_final_answer_marker_is_not_a_removed_work_trace():
    body = "模拟显示利益相关者存在分歧，现有证据不足以推断实际人群的反应，需要进一步收集资料并开展独立验证。"
    result = sanitize_final_content("Final Answer:\n\n" + body)
    assert result.content == body
    assert result.removed_segments == []


def test_real_work_trace_before_final_answer_is_still_reported():
    result = sanitize_final_content("Thought: I should summarize the evidence.\nFinal Answer:\nThe observed simulated reactions differ between groups.")
    assert result.removed_segments == ["Thought: I should summarize the evidence."]
    assert result.content.startswith("The observed")


@pytest.fixture
def log_client(tmp_path, monkeypatch):
    monkeypatch.setattr(ReportManager, "REPORTS_DIR", str(tmp_path))
    folder = tmp_path / "report_abcdef123456"
    folder.mkdir()
    (folder / "console_log.txt").write_text("first\n第二行\n", encoding="utf-8")
    (folder / "agent_log.jsonl").write_text(
        json.dumps({"action": "start"}) + "\n" + json.dumps({"action": "done"}) + "\n",
        encoding="utf-8",
    )
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.register_blueprint(report_bp, url_prefix="/api/report")
    return app.test_client()


@pytest.mark.parametrize("kind,last", [("console", "第二行"), ("agent", {"action": "done"})])
def test_incremental_report_log_endpoints(log_client, kind, last):
    response = log_client.get(f"/api/report/report_abcdef123456/{kind}-log?from_line=1")
    assert response.status_code == 200
    assert response.json["data"]["logs"] == [last]
    assert response.json["data"]["total_lines"] == 2
    assert response.json["data"]["from_line"] == 1
    stream = log_client.get(f"/api/report/report_abcdef123456/{kind}-log/stream")
    assert stream.status_code == 200
    assert stream.json["data"]["count"] == 2
    assert stream.json["data"]["logs"][-1] == last


def _invalid_threshold_error():
    try:
        Threshold.model_validate({
            "id": "T1", "label": "验收阈值", "value": 80, "unit": "percent",
            "purpose": "target", "origin": "model_proposal", "evidence_status": "verified",
            "evidence_refs": [],
        })
    except ValidationError as error:
        assert len(error.errors()) == 1
        assert "evidence_ref" in error.errors()[0]["msg"]
        return error
    raise AssertionError("Unreferenced verified threshold must fail validation")


def test_metadata_retries_schema_error_without_weakening_evidence_validation():
    agent = MagicMock()
    agent.evidence_map = {}
    error = _invalid_threshold_error()
    agent.llm.chat_json.side_effect = [error, {"section_title": "分析", "thresholds": []}]
    result = generate_section_metadata(agent, "分析", "没有可验证的阈值。", 3)
    assert result["thresholds"] == []
    assert agent.llm.chat_json.call_count == 2
    prompt = agent.llm.chat_json.call_args.kwargs["messages"][-1]["content"]
    assert "Regenerate" in prompt
    assert "Do not invent facts or evidence references" in prompt
    assert 3 not in events_for(agent).metadata_failed_sections


def test_metadata_second_invalid_output_remains_a_visible_failure():
    agent = MagicMock()
    agent.evidence_map = {}
    agent.llm.chat_json.side_effect = _invalid_threshold_error()
    assert generate_section_metadata(agent, "分析", "未提供证据。", 3) == {}
    assert agent.llm.chat_json.call_count == 2
    assert 3 in events_for(agent).metadata_failed_sections
