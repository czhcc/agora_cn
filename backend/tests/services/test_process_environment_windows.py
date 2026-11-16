"""Windows infrastructure variables must survive the simulation allowlist."""

import os
import subprocess
import sys

import pytest

from app.services.sim.process_environment import _build_subprocess_env


def test_windows_runtime_environment_is_preserved_without_inheriting_secrets(tmp_path, monkeypatch):
    expected = {"SYSTEMROOT": r"C:\Windows", "WINDIR": r"C:\Windows", "TEMP": str(tmp_path), "TMP": str(tmp_path)}
    for key, value in expected.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv("AGORA_AUTH_TOKEN", "must-not-be-inherited")
    monkeypatch.setenv("LLM_API_KEY", "must-not-be-inherited")
    env, pass_fds = _build_subprocess_env(None, tmp_path)
    assert {key: env[key] for key in expected} == expected
    assert "AGORA_AUTH_TOKEN" not in env
    assert "LLM_API_KEY" not in env
    assert pass_fds == ()


def test_home_and_model_cache_configuration_survives_filtering(tmp_path, monkeypatch):
    expected = {
        "HOME": str(tmp_path), "USERPROFILE": str(tmp_path),
        "HOMEDRIVE": "C:", "HOMEPATH": r"\Users\test",
        "HF_HOME": str(tmp_path / "hf"), "HF_HUB_CACHE": str(tmp_path / "hub"),
        "HUGGINGFACE_HUB_CACHE": str(tmp_path / "hub-legacy"),
        "HF_ASSETS_CACHE": str(tmp_path / "assets"),
        "TRANSFORMERS_CACHE": str(tmp_path / "transformers"),
        "SENTENCE_TRANSFORMERS_HOME": str(tmp_path / "sentence"),
        "HF_ENDPOINT": "https://huggingface.co", "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1",
        "AGORA_TWHIN_BERT_MODEL_DIR": str(tmp_path / "local-model"),
    }
    for key, value in expected.items():
        monkeypatch.setenv(key, value)
    env, _ = _build_subprocess_env(None, tmp_path)
    assert {key: env[key] for key in expected} == expected


def test_child_resolves_user_home_and_huggingface_cache(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setenv("HF_HUB_CACHE", str(tmp_path / "hub"))
    env, _ = _build_subprocess_env(None, tmp_path)
    code = (
        "import os; from pathlib import Path; from huggingface_hub import constants; "
        "assert Path.home() == Path(os.environ['USERPROFILE']); "
        "assert Path(constants.HF_HUB_CACHE).expanduser() == Path(os.environ['HF_HUB_CACHE']); "
        "import asyncio; asyncio.run(asyncio.sleep(0)); print('ok')"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], env=env, capture_output=True, text=True, encoding="utf-8", timeout=20,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "ok"


@pytest.mark.skipif(sys.platform != "win32", reason="Exercises Windows Winsock and overlapped I/O")
def test_filtered_windows_child_can_start_asyncio(tmp_path):
    assert os.environ.get("SYSTEMROOT")
    env, pass_fds = _build_subprocess_env(None, tmp_path)
    assert pass_fds == ()
    result = subprocess.run(
        [sys.executable, "-c", "import _overlapped, asyncio; asyncio.run(asyncio.sleep(0)); print('ok')"],
        env=env, capture_output=True, text=True, encoding="utf-8", timeout=20,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "ok"
