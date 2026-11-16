"""Regression coverage for real process locks on Windows and POSIX."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from app.process_lock import process_file_lock


def test_lock_blocks_another_process_and_releases_after_exception(tmp_path: Path) -> None:
    lock_path = tmp_path / "store.lock"
    script = """
import sys
from pathlib import Path
from app.process_lock import process_file_lock
print('waiting', flush=True)
with process_file_lock(Path(sys.argv[1])):
    print('acquired', flush=True)
"""
    child = None
    try:
        with pytest.raises(RuntimeError, match="rollback"):
            with process_file_lock(lock_path) as lock_fh:
                # Unlock must still target byte zero if a caller moves the cursor.
                lock_fh.seek(10)
                child = subprocess.Popen(
                    [sys.executable, "-c", script, str(lock_path)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                assert child.stdout is not None
                assert child.stdout.readline().strip() == "waiting"
                with pytest.raises(subprocess.TimeoutExpired):
                    child.communicate(timeout=0.3)
                raise RuntimeError("rollback")
        assert child is not None
        stdout, stderr = child.communicate(timeout=15)
        assert child.returncode == 0, stderr
        assert stdout.strip() == "acquired"
    finally:
        if child is not None and child.poll() is None:
            child.kill()
            child.communicate()


def test_concurrent_read_modify_write_does_not_lose_updates(tmp_path: Path) -> None:
    counter = tmp_path / "counter"
    counter.write_text("0", encoding="utf-8")
    script = """
import sys
import time
from pathlib import Path
from app.process_lock import process_file_lock
counter = Path(sys.argv[1])
for _ in range(15):
    with process_file_lock(counter.with_suffix('.lock')):
        value = int(counter.read_text(encoding='utf-8'))
        time.sleep(0.002)
        counter.write_text(str(value + 1), encoding='utf-8')
"""
    children = []
    try:
        for _ in range(3):
            children.append(subprocess.Popen(
                [sys.executable, "-c", script, str(counter)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            ))
        for child in children:
            _, stderr = child.communicate(timeout=20)
            assert child.returncode == 0, stderr
        assert counter.read_text(encoding="utf-8") == "45"
    finally:
        for child in children:
            if child.poll() is None:
                child.kill()
                child.communicate()


def test_sidecar_is_preserved(tmp_path: Path) -> None:
    path = tmp_path / "store.lock"
    path.write_text("existing lock file", encoding="utf-8")
    with process_file_lock(path):
        pass
    assert path.read_text(encoding="utf-8") == "existing lock file"
