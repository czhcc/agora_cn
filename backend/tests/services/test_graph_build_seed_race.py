"""Terminalzustände bei einem Seed-Race nach Run-/Task-Erzeugung (#897)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.contracts.ai_provider_contract import AiModelRef
from app.models.project import ProjectStatus
from app.services.graph_build import (
    AI_MODEL_REF_ROUTING_FAILURE_MESSAGE,
    AiModelRefRoutingInputError,
    GraphBuildService,
)


PROJECT_ID = "proj_0123456789ab"
SECRET_SENTINEL = "sk-seed-race-secret-must-not-leak"


def _ref() -> AiModelRef:
    return AiModelRef(
        provider_connection_id="conn-race",
        model_id="race-model",
        source="explicit",
    )


def _seed_race(*_args, **_kwargs):
    raise ValueError(f"route changed concurrently: {SECRET_SENTINEL}")


@pytest.mark.parametrize("phase", ["routing", "generation"])
def test_legacy_profile_failure_terminalizes_run_and_preserves_error(monkeypatch, phase):
    project = SimpleNamespace(project_id=PROJECT_ID, status=ProjectStatus.CREATED, error=None)
    registry = MagicMock()
    registry.create_run.return_value = {"run_id": "run-legacy-failure"}
    save = MagicMock()
    monkeypatch.setattr("app.services.graph_build.ProjectManager.get_project", lambda _id: project)
    monkeypatch.setattr("app.services.graph_build.ProjectManager.save_project", save)
    monkeypatch.setattr("app.services.graph_build.run_registry", registry)
    original = ValueError("Provider connection unavailable")
    if phase == "routing":
        monkeypatch.setattr("app.services.graph_build.seed_run_stage_routing", MagicMock(side_effect=original))
    else:
        monkeypatch.setattr("app.services.graph_build.seed_run_stage_routing", MagicMock())
        monkeypatch.setattr("app.services.graph_build.StageModelRouter", MagicMock())
        monkeypatch.setattr("app.services.graph_build.LLMClient.from_route", MagicMock(side_effect=original))
    with pytest.raises(ValueError) as caught:
        GraphBuildService.generate_ontology(
            project_id=PROJECT_ID, simulation_requirement="Question", document_texts=["Document"],
            llm_profile_id="profile-test",
        )
    assert caught.value is original
    assert project.status == ProjectStatus.FAILED
    save.assert_called_once_with(project)
    registry.update_run.assert_called_once()
    assert registry.update_run.call_args.kwargs["status"] == "failed"
    assert registry.update_run.call_args.kwargs["error"] == project.error


def test_ontology_seed_race_terminalizes_run_and_project(monkeypatch):
    project = SimpleNamespace(
        project_id=PROJECT_ID,
        status=ProjectStatus.CREATED,
        error=None,
    )
    save_project = MagicMock()
    run_registry = MagicMock()
    run_registry.create_run.return_value = {"run_id": "run-ontology-race"}
    monkeypatch.setattr(
        "app.services.graph_build.ProjectManager.get_project", lambda _id: project
    )
    monkeypatch.setattr(
        "app.services.graph_build.ProjectManager.save_project", save_project
    )
    monkeypatch.setattr("app.services.graph_build.run_registry", run_registry)
    monkeypatch.setattr("app.services.graph_build.seed_run_stage_routing", _seed_race)

    # Der konkrete Typ ist Teil der Zusicherung: ein argumentloser
    # ``_AiModelRefRoutingInputError`` hat ein leeres ``str()``, die
    # Sentinel-Prüfung allein wäre auch bei jedem anderen ValueError grün.
    with pytest.raises(AiModelRefRoutingInputError) as exc_info:
        GraphBuildService.generate_ontology(
            project_id=PROJECT_ID,
            simulation_requirement="Analyse the document.",
            document_texts=["document"],
            ai_model_ref=_ref(),
        )

    assert SECRET_SENTINEL not in str(exc_info.value)
    assert project.status == ProjectStatus.FAILED
    assert project.error == AI_MODEL_REF_ROUTING_FAILURE_MESSAGE
    save_project.assert_called_once_with(project)
    failed_update = run_registry.update_run.call_args
    assert failed_update.args == ("run-ontology-race",)
    assert failed_update.kwargs["status"] == "failed"


def test_graph_seed_race_terminalizes_run_task_and_project(monkeypatch):
    project = SimpleNamespace(
        project_id=PROJECT_ID,
        name="Race project",
        status=ProjectStatus.ONTOLOGY_GENERATED,
        graph_id=None,
        graph_build_task_id=None,
        error=None,
        chunk_size=500,
        chunk_overlap=50,
        ontology={"entity_types": [], "edge_types": []},
        llm_profile_id=None,
    )
    save_project = MagicMock()
    task_manager = MagicMock()
    task_manager.create_task.return_value = "task-race"
    run_registry = MagicMock()
    run_registry.create_run.return_value = {"run_id": "run-graph-race"}
    enqueue = MagicMock()
    monkeypatch.setattr(
        "app.services.graph_build.ProjectManager.get_project", lambda _id: project
    )
    monkeypatch.setattr(
        "app.services.graph_build.ProjectManager.get_extracted_text", lambda _id: "text"
    )
    monkeypatch.setattr(
        "app.services.graph_build.ProjectManager._get_project_dir", lambda _id: "/tmp/project"
    )
    monkeypatch.setattr(
        "app.services.graph_build.ProjectManager.save_project", save_project
    )
    monkeypatch.setattr("app.services.graph_build.TaskManager", lambda: task_manager)
    monkeypatch.setattr("app.services.graph_build.run_registry", run_registry)
    monkeypatch.setattr("app.services.graph_build.seed_run_stage_routing", _seed_race)
    monkeypatch.setattr(
        "app.services.graph_build.ArtifactLocator.existing_paths", lambda _paths: {}
    )
    monkeypatch.setattr("app.jobs.enqueue", enqueue)

    with pytest.raises(AiModelRefRoutingInputError) as exc_info:
        GraphBuildService.build_graph(
            project_id=PROJECT_ID,
            graph_name="Race graph",
            container=MagicMock(),
            ai_model_ref=_ref(),
        )

    assert SECRET_SENTINEL not in str(exc_info.value)
    assert project.status == ProjectStatus.FAILED
    assert project.error == AI_MODEL_REF_ROUTING_FAILURE_MESSAGE
    assert project.graph_build_task_id == "task-race"
    assert save_project.call_count == 2
    task_manager.fail_task.assert_called_once()
    assert task_manager.fail_task.call_args.args[0] == "task-race"
    failed_update = run_registry.update_run.call_args
    assert failed_update.args == ("run-graph-race",)
    assert failed_update.kwargs["status"] == "failed"
    enqueue.assert_not_called()
