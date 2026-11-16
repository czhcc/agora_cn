### Fixed

- Direct single and batch persona interviews use the persisted simulation language contract (`de`, `en`, `zh`), rather than treating every non-German language as English.
- Place simulation language instructions before OASIS's response-format boundary so live interviews retain the selected language when OASIS constructs their prompts. Stored interview history is unchanged.
