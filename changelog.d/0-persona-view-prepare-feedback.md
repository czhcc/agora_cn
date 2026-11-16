### Fixed

- Preserve the simulation ID when opening personas from run tabs and stage actions. Project IDs no longer accidentally reach simulation profile endpoints through these links.
- Force regeneration when explicitly requesting another prepare run. Show preparation progress and errors on the page, and require both profiles and configuration before reporting successful completion. Handle persisted-ready polling responses as terminal results.
