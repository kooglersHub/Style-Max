# Style Max

A private styling studio: describe a vibe, add three photos, explore ten looks, choose favorites, add sizes, and find matching secondhand clothes.

Implementation is in progress. The backend foundation and adapter contracts are available; the React studio is the next milestone. See [the approved design](docs/superpowers/specs/2026-11-07-style-max-design.md) and [implementation record](docs/implementation-progress.md).

## Backend development

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```powershell
uv sync --extra dev
uv run uvicorn stylemax.app:app --host 127.0.0.1 --port 8000
```

API documentation: http://127.0.0.1:8000/docs

```powershell
uv run pytest
uv run ruff check src tests worker
```

The optional image worker needs a separate CUDA GPU environment. Marketplace credentials and model weights are not included. Demo mode never fabricates marketplace offers. Reference photos, databases and generated media stay in the ignored `data/` directory.
