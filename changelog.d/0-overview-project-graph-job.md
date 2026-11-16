### Fixed

- Restore graph status, model, duration and measured token usage in run overviews by looking up project-scoped graph-build jobs, which are created before a simulation exists.
- Match the simulation's graph ID before choosing a job; avoid using later builds of a different graph in the same project. The graph row reports graph-build usage only, without merging the separate ontology-generation task.
