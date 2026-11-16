### Fixed

- Preserve terminal simulation outcomes while terminating lingering processes during shutdown; use native Windows PID existence checks through the existing psutil dependency.
- Honor explicitly configured OpenAI-compatible connections for native tool calls, rather than overriding their protocol with an unknown-URL fallback.
- Do not classify a bare `Final Answer:` marker as a removed internal work trace.
- Repair report agent/console log argument forwarding and stream payloads so incremental polling returns log entries instead of HTTP 500 or a filesystem path.
- Retry invalid report metadata once with schema feedback. Missing evidence references remain invalid and repeated extraction failures remain visible.
