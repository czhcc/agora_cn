### Fixed

- Das Frontend deklariert pnpm 10.33.2 als Paketmanager und übernimmt die vorhandenen Dependency-Overrides auch für pnpm. Installation und Vite-Start erfolgen direkt in `frontend/`; die Root-Orchestrierung und Bun-spezifischen Prüfskripte bleiben separat.
