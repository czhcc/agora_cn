### Fixed

- Support Chinese report output via `REPORT_LANGUAGE=Simplified Chinese`, `zh` or `zh-CN`. Normalize prompt language names for outline, sections and chat; metadata and red-team prompts follow the configured language instead of implicitly or explicitly requesting German.
- Recognize Chinese completeness requirements and phased-rollout questions without bypassing missing-aspect checks. UI and simulation language remain independent; the German default is unchanged.
