"""Regressionstests zu Issue #1713 Slice S3 — TWHIN-BERT-Cache offline nach
Warmup + Ladereport-Uebersetzung.

Seam: ``ensure_twhin_cache`` und ``TwhinBertLoadReportFilter`` in
``backend.scripts._sim_common``. ``huggingface_hub`` wird per
``sys.modules``-Overlay gefaked — kein Netzwerk, kein echter Cache noetig
(gleiches Muster wie ``test_bert_memory_profile.py``).
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from unittest import mock

import pytest

_BACKEND_DIR = Path(__file__).resolve().parents[2]
_SCRIPTS_DIR = _BACKEND_DIR / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import _sim_common as sc  # noqa: E402


@pytest.fixture(autouse=True)
def _clean_offline_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "AGORA_TWHIN_BERT_MODEL_DIR"):
        monkeypatch.delenv(var, raising=False)


@pytest.fixture
def remove_load_report_filter():
    """``install_twhin_bert_load_report_filter`` haengt sich in den
    Root-Logger — ohne Teardown wuerde der Filter andere Tests im selben
    Prozess verunreinigen."""
    root_logger = logging.getLogger()
    before = list(root_logger.filters)
    yield root_logger
    for f in list(root_logger.filters):
        if f not in before:
            root_logger.removeFilter(f)


class TestEnsureTwhinCache:
    def test_relative_model_directory_is_resolved_from_project_root(self, tmp_path, monkeypatch):
        from types import SimpleNamespace

        directory = tmp_path / "models" / "twhin"
        directory.mkdir(parents=True)
        for name in ("config.json", "tokenizer.json", "model.safetensors"):
            (directory / name).write_text("{}", encoding="utf-8")
        monkeypatch.setattr(sc, "__file__", str(tmp_path / "backend" / "scripts" / "_sim_common.py"))
        monkeypatch.setenv("AGORA_TWHIN_BERT_MODEL_DIR", "models/twhin")
        load = mock.Mock()
        transformer = SimpleNamespace(AutoModel=SimpleNamespace(from_pretrained=load), AutoTokenizer=SimpleNamespace(from_pretrained=load))
        with mock.patch.dict(sys.modules, {"transformers": transformer}):
            assert sc.ensure_twhin_cache() is True
            transformer.AutoModel.from_pretrained("Twitter/twhin-bert-base")
        load.assert_called_once_with(str(directory.resolve()), local_files_only=True)

    @pytest.mark.parametrize("weight_file", ["model.safetensors", "pytorch_model.bin"])
    def test_configured_directory_redirects_model_and_tokenizer_without_hub(
        self, tmp_path, monkeypatch, weight_file,
    ):
        from types import SimpleNamespace

        directory = tmp_path / "本地 模型"
        directory.mkdir()
        for filename in ("config.json", "tokenizer.json", weight_file):
            (directory / filename).write_text("{}", encoding="utf-8")
        monkeypatch.setenv("AGORA_TWHIN_BERT_MODEL_DIR", str(directory))
        calls = []

        def original(*args, **kwargs):
            calls.append((args, kwargs))
            return "loaded"

        model = SimpleNamespace(from_pretrained=original)
        tokenizer = SimpleNamespace(from_pretrained=original)
        hub = mock.Mock()
        with mock.patch.dict(sys.modules, {
            "transformers": SimpleNamespace(AutoModel=model, AutoTokenizer=tokenizer),
            "huggingface_hub": hub,
        }):
            assert sc.ensure_twhin_cache() is True
            first_wrapper = model.from_pretrained
            assert sc.ensure_twhin_cache() is True
            assert model.from_pretrained is first_wrapper
            assert model.from_pretrained("Twitter/twhin-bert-base", local_files_only=False) == "loaded"
            assert tokenizer.from_pretrained(pretrained_model_name_or_path="Twitter/twhin-bert-base") == "loaded"
            assert model.from_pretrained("another/model", revision="main") == "loaded"
        hub.snapshot_download.assert_not_called()
        assert calls == [
            ((str(directory.resolve()),), {"local_files_only": True}),
            ((), {"pretrained_model_name_or_path": str(directory.resolve()), "local_files_only": True}),
            (("another/model",), {"revision": "main"}),
        ]

    @pytest.mark.parametrize("missing", ["directory", "config.json", "weights", "tokenizer"])
    def test_invalid_configured_directory_fails_without_download(self, tmp_path, monkeypatch, missing):
        directory = tmp_path / "model"
        if missing != "directory":
            directory.mkdir()
            for filename, category in (("config.json", "config.json"), ("model.safetensors", "weights"), ("tokenizer.json", "tokenizer")):
                if missing != category:
                    (directory / filename).write_text("{}", encoding="utf-8")
        monkeypatch.setenv("AGORA_TWHIN_BERT_MODEL_DIR", str(directory))
        hub = mock.Mock()
        with mock.patch.dict(sys.modules, {"huggingface_hub": hub}):
            with pytest.raises(sc.TwhinCacheError, match="AGORA_TWHIN_BERT_MODEL_DIR"):
                sc.ensure_twhin_cache()
        hub.snapshot_download.assert_not_called()

    @pytest.mark.parametrize("empty", ["", "  "])
    def test_empty_local_directory_keeps_default_cache_flow(self, monkeypatch, empty):
        monkeypatch.setenv("AGORA_TWHIN_BERT_MODEL_DIR", empty)
        hub = mock.Mock()
        with mock.patch.dict(sys.modules, {"huggingface_hub": hub}):
            assert sc.ensure_twhin_cache() is True
        hub.snapshot_download.assert_called_once_with(repo_id="Twitter/twhin-bert-base", local_files_only=True)

    def test_cache_complete_sets_offline_env_without_second_download(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        calls: list[dict] = []

        def _fake_snapshot_download(*, repo_id: str, local_files_only: bool):
            calls.append({"repo_id": repo_id, "local_files_only": local_files_only})
            return "/fake/cache/path"

        fake_module = mock.Mock()
        fake_module.snapshot_download = _fake_snapshot_download
        with mock.patch.dict(sys.modules, {"huggingface_hub": fake_module}):
            result = sc.ensure_twhin_cache()

        assert result is True
        assert len(calls) == 1, "Cache vollstaendig -> genau ein Aufruf (local_files_only=True)"
        assert calls[0]["local_files_only"] is True
        import os

        assert os.environ["HF_HUB_OFFLINE"] == "1"
        assert os.environ["TRANSFORMERS_OFFLINE"] == "1"

    def test_cache_incomplete_downloads_once_then_offline(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        calls: list[dict] = []

        def _fake_snapshot_download(*, repo_id: str, local_files_only: bool):
            calls.append({"repo_id": repo_id, "local_files_only": local_files_only})
            if local_files_only:
                raise OSError("cache incomplete (fake LocalEntryNotFoundError)")
            return "/fake/cache/path"

        fake_module = mock.Mock()
        fake_module.snapshot_download = _fake_snapshot_download
        with mock.patch.dict(sys.modules, {"huggingface_hub": fake_module}):
            result = sc.ensure_twhin_cache()

        assert result is False, "Warmup-Download fand statt"
        assert len(calls) == 2
        assert calls[0]["local_files_only"] is True
        assert calls[1]["local_files_only"] is False
        import os

        assert os.environ["HF_HUB_OFFLINE"] == "1"
        assert os.environ["TRANSFORMERS_OFFLINE"] == "1"

    def test_download_failure_raises_twhin_cache_error_and_stays_online(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def _fake_snapshot_download(*, repo_id: str, local_files_only: bool):
            if local_files_only:
                raise OSError("cache incomplete")
            raise RuntimeError("Hub unreachable (fake)")

        fake_module = mock.Mock()
        fake_module.snapshot_download = _fake_snapshot_download
        with mock.patch.dict(sys.modules, {"huggingface_hub": fake_module}):
            with pytest.raises(sc.TwhinCacheError):
                sc.ensure_twhin_cache()

        import os

        assert "HF_HUB_OFFLINE" not in os.environ, (
            "Bei einem gescheiterten Warmup darf der Prozess NICHT in den "
            "Offline-Modus geschaltet werden — er haette dann kein Cache und "
            "keinen Netzwerkzugriff mehr."
        )

    def test_missing_huggingface_hub_is_noop(self, monkeypatch: pytest.MonkeyPatch) -> None:
        with mock.patch.dict(sys.modules, {"huggingface_hub": None}):
            result = sc.ensure_twhin_cache()

        assert result is True
        import os

        assert "HF_HUB_OFFLINE" not in os.environ


class TestTwhinBertLoadReportFilter:
    @staticmethod
    def _record(name: str, message: str) -> logging.LogRecord:
        return logging.LogRecord(
            name=name,
            level=logging.WARNING,
            pathname=__file__,
            lineno=1,
            msg=message,
            args=(),
            exc_info=None,
        )

    def test_missing_pooler_weights_downgraded_to_info(self) -> None:
        record = self._record(
            "transformers.modeling_utils",
            "Some weights of BertModel were not initialized from the model "
            "checkpoint at Twitter/twhin-bert-base and are newly initialized: "
            "['pooler.dense.bias', 'pooler.dense.weight']\nYou should probably "
            "TRAIN this model on a down-stream task.",
        )

        kept = sc.TwhinBertLoadReportFilter().filter(record)

        assert kept is True
        assert record.levelno == logging.INFO
        assert "erwartet" in record.getMessage()

    def test_unexpected_cls_predictions_downgraded_to_info(self) -> None:
        record = self._record(
            "transformers.modeling_utils",
            "Some weights of the model checkpoint at Twitter/twhin-bert-base "
            "were not used when initializing BertModel: "
            "['cls.predictions.bias', 'cls.predictions.transform.dense.bias', "
            "'cls.predictions.decoder.weight']\n- This IS expected if you are "
            "initializing BertModel from the checkpoint of a model trained on "
            "another task.",
        )

        kept = sc.TwhinBertLoadReportFilter().filter(record)

        assert kept is True
        assert record.levelno == logging.INFO
        assert "erwartet" in record.getMessage()

    def test_other_missing_weights_stay_warning(self) -> None:
        """Ein zukuenftiger Checkpoint-Wechsel darf nicht in Info-Rauschen
        verschwinden — nur die BEKANNTEN erwarteten Namen werden gedaempft."""
        record = self._record(
            "transformers.modeling_utils",
            "Some weights of BertModel were not initialized from the model "
            "checkpoint at Twitter/twhin-bert-base and are newly initialized: "
            "['pooler.dense.bias', 'pooler.dense.weight', "
            "'encoder.layer.11.attention.self.query.weight']",
        )
        original_message = record.msg

        kept = sc.TwhinBertLoadReportFilter().filter(record)

        assert kept is True
        assert record.levelno == logging.WARNING
        assert record.msg == original_message

    def test_different_model_untouched(self) -> None:
        record = self._record(
            "transformers.modeling_utils",
            "Some weights of BertModel were not initialized from the model "
            "checkpoint at bert-base-uncased and are newly initialized: "
            "['pooler.dense.bias', 'pooler.dense.weight']",
        )
        original_message = record.msg

        kept = sc.TwhinBertLoadReportFilter().filter(record)

        assert kept is True
        assert record.levelno == logging.WARNING
        assert record.msg == original_message

    def test_non_transformers_logger_untouched(self) -> None:
        record = self._record(
            "some.other.logger",
            "Some weights ... Twitter/twhin-bert-base ... newly initialized: "
            "['pooler.dense.bias', 'pooler.dense.weight']",
        )
        original_message = record.msg

        kept = sc.TwhinBertLoadReportFilter().filter(record)

        assert kept is True
        assert record.levelno == logging.WARNING
        assert record.msg == original_message

    def test_install_is_idempotent(self, remove_load_report_filter) -> None:
        root_logger = remove_load_report_filter

        sc.install_twhin_bert_load_report_filter()
        sc.install_twhin_bert_load_report_filter()

        installed = [f for f in root_logger.filters if isinstance(f, sc.TwhinBertLoadReportFilter)]
        assert len(installed) == 1
