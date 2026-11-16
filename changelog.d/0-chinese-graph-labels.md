### Fixed

- Preserve source-language entity names and relationship facts during extraction. Prefer source-attested Chinese names over English aliases, persist aliases for search, and resolve relation endpoints through unambiguous aliases without duplicating nodes.
- Generate optional Chinese ontology display labels and use them in graph reader/edit sidebars, tables, details and type selectors. Existing common types have Chinese fallback labels; machine identifiers and edit payloads remain unchanged. Existing entity names require re-extraction to change.
