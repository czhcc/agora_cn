"""Blocking sidecar-file locks shared by POSIX and Windows stores."""

from __future__ import annotations

import errno
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from typing import IO, Iterator

if sys.platform == "win32":
    import msvcrt
else:
    import fcntl


@contextmanager
def process_file_lock(path: Path) -> Iterator[IO[str]]:
    """Hold an exclusive process lock without truncating or deleting its file.

    Windows locks the first byte, which may be beyond EOF. Retry contention
    indefinitely to match blocking flock rather than LK_LOCK's ten retries.
    All callers must use the same stable sidecar path across atomic writes.
    """
    with open(path, "a", encoding="utf-8") as lock_fh:
        if sys.platform == "win32":
            lock_fh.seek(0)
            while True:
                try:
                    msvcrt.locking(lock_fh.fileno(), msvcrt.LK_NBLCK, 1)
                    break
                except OSError as exc:
                    if exc.errno != errno.EACCES:
                        raise
                    time.sleep(0.05)
        else:
            fcntl.flock(lock_fh, fcntl.LOCK_EX)
        try:
            yield lock_fh
        finally:
            if sys.platform == "win32":
                lock_fh.seek(0)
                msvcrt.locking(lock_fh.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(lock_fh, fcntl.LOCK_UN)
