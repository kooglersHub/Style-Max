# Implementation record

Plan: `docs/superpowers/plans/2026-11-07-style-max.md`
Spec approved by the user on 2026-11-07.

Ruling: execute inline in the existing checkout and push main at working milestones, honoring the user's explicit workflow. No separate worktree or additional plan approval gate.

Pre-flight: project schemas are shared by persistence, jobs, marketplace adapters and the frontend; JSON field names are the API contract. The optional image worker uses multipart `prompt` plus 1–3 `images` and returns raw image bytes.

Tasks 1–2 backend milestone: API workflow, protected uploads/media, SQLite persistence, recovery and generation/search/preview jobs, Ollama planner, image worker client/service, marketplace source adapters and ranking implemented. Watched missing implementation failures before implementation. Backend tests: 18 passed. Ruff check passed. Live provider responses and GPU inference remain unverified without configuration.

Ruling: a listing's explicit letter size in its title counts as size evidence; numeric title tokens alone do not because they can be years or model numbers. Corrected the unknown-size fixture to remove an explicit M from its title.

Frontend test-first milestone: tests fail because the look gallery and fit form do not exist yet. Installation completed after explicitly permitting esbuild's build script in pnpm workspace configuration.
