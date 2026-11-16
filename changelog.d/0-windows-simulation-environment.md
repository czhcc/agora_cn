### Fixed

- Preserve Windows system-directory and temporary-directory environment variables when starting simulation subprocesses. Missing `SystemRoot` could cause `asyncio`/`_overlapped` initialization to fail with WinError 10106 before the first round.
- Add a real Windows subprocess regression check for asyncio event-loop startup.
