### Fixed

- Synchronous graph operations now terminalize run and project records for profile/env routing failures as well as explicit model references. An ontology request returning HTTP 400 no longer leaves a permanent processing/0% run behind. Existing HTTP error semantics are preserved.
