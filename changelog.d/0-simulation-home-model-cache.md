### Fixed

- Simulation subprocesses preserve user-home variables and Hugging Face/Transformers cache configuration. Windows model initialization no longer fails with `Could not determine home directory` after the environment allowlist removed `USERPROFILE`.
- Add real subprocess checks for home resolution, Hugging Face cache paths and asyncio startup together.
