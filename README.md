# Style Max

A private personal styling studio for better secondhand outfits.

Describe a vibe → upload three photos → generate ten outfit ideas → save favorites → enter sizes → edit a shopping list → compare marketplace offers → preview your chosen pieces.

**Ready without accounts:** the complete demo journey, ten illustrated look concepts, size profiles, editable shopping lists, and real marketplace search links. Demo illustrations are labeled and never claim to show the user or purchasable listings.

**Connected mode:** an Ollama stylist, a separate Qwen image worker, official eBay Browse integration, and optional community Kleinanzeigen/Vinted clients. These require their respective services and access; the website does not include API credentials or a GPU.

## Quick start on Windows

Install Python 3.12+, Node.js 22.12+ (24 recommended), [uv](https://docs.astral.sh/uv/) and pnpm 11.25.0. From this repository:

```powershell
Copy-Item .env.example .env
./start.ps1
```

Open **http://127.0.0.1:8000** and choose **Try the demo lookbook**. The script installs dependencies, builds the React frontend, and serves both frontend and API from one origin. Stop with Ctrl+C. Use `./start.ps1 -Marketplaces` to install the optional marketplace clients too.

Manual launch, without the PowerShell script:

```powershell
uv sync --frozen --extra marketplaces
pnpm --dir frontend install --frozen-lockfile
pnpm --dir frontend build
uv run --no-sync uvicorn stylemax.app:app --host 127.0.0.1 --port 8000
```

For frontend development, run `pnpm --dir frontend dev` in another terminal. Its `/api` requests proxy to the backend on port 8000. Restart the production server after building the frontend for the first time; it mounts the frontend directory at startup.

## Connect the AI stylist

Install and start [Ollama](https://github.com/ollama/ollama). Pull a structured-output capable model:

```powershell
ollama pull qwen2.5:7b
ollama serve
```

If the desktop service already runs, do not start a second server. Set `STYLEMAX_OLLAMA_URL` and `STYLEMAX_OLLAMA_MODEL` in `.env` if needed. The stylist produces ten validated, distinct outfits with garment specifications; their prompts drive the image worker. Photos are used for image editing rather than guessing sizes or sensitive attributes.

## Connect image generation

The included worker uses [Qwen-Image-Edit-2509](https://huggingface.co/Qwen/Qwen-Image-Edit-2509), an Apache-2.0 model with multi-image editing. It runs separately so web installations never download GPU libraries or model weights.

Use a supported NVIDIA CUDA machine with sufficient GPU/system memory and disk for this large model. CPU offloading is enabled; requirements and speed depend on your GPU and Diffusers setup. Integrated Intel graphics cannot run this worker. You can run it on another private GPU host and point the studio at it.

In a **separate Python environment**, install an appropriate CUDA PyTorch build, then:

```powershell
# From the worker directory in your separate GPU environment:
python -m pip install -r requirements.txt
# Return to the repository root:
python -m uvicorn worker.app:app --host 127.0.0.1 --port 8189
```

Configure the web app:

```dotenv
STYLEMAX_IMAGE_WORKER_URL=http://127.0.0.1:8189
STYLEMAX_IMAGE_WORKER_KEY=
```

The model loads and downloads weights on its first generation request. For a remote worker set the same `STYLEMAX_IMAGE_WORKER_KEY` on both processes, use a private network/TLS, and supply its URL. Keep the worker bound to loopback unless you have configured that protection. The worker reads its key from its process environment; the web app reads `.env`. Generation is sequential, with per-look progress, finite timeouts and retries of only unfinished looks. A slow initial download can exceed the request timeout; let the worker finish loading before retrying.

Worker API: `POST /generate`, multipart `prompt` and one to three `images` files, optional bearer key, returning PNG bytes. `GET /health` reports service/model-load state. Other image services can implement this contract. Final previews use the reference person plus a collage of selected product images, retaining listing links and marking missing product imagery.

## Connect marketplaces

All searches are read-only. Buying and seller contact stay on the marketplace.

| Source | Setup | Behavior |
| --- | --- | --- |
| eBay | Developer credentials in `STYLEMAX_EBAY_CLIENT_ID` and `STYLEMAX_EBAY_CLIENT_SECRET` | Official Browse API, application OAuth, Germany and EUR. Developer production access may be required. |
| Kleinanzeigen | Install the `marketplaces` extra; set `STYLEMAX_ENABLE_KLEINANZEIGEN=true` | Unofficial `kleinanzeigen-api`, one page per query, bounded subprocess timeout and client rate limit. |
| Vinted | Install the `marketplaces` extra; set `STYLEMAX_ENABLE_VINTED=true` | Unofficial `vinted_scraper`, bounded searches. Session/anti-bot changes can make it unavailable. |

Restart after changing `.env`. Keys remain on the server. Settings show whether a source is enabled; each search reports connected, unavailable, partial, or unconfigured status. No challenge bypass is implemented. Missing connections and failures leave useful **Search marketplace** links, never fabricated offers.

Results are ranked by keyword relevance, size evidence, budget and known shipping. Explicit size mismatches are excluded. Letter sizes in a listing title count as evidence; numeric tokens alone do not establish shoe/trouser sizes. Unknown size requires seller confirmation. Unknown shipping is not free; automatic basket selection uses known delivered costs. The total budget covers the **entire confirmed shopping list**, across selected looks. Verify measurements, fees, availability and condition before purchasing.

The app compares bounded search results, not every listing. Platform fees and unknown charges are not included unless supplied by a source. Source clients are open source; that does not make marketplaces open APIs. See [third-party notes](THIRD_PARTY.md).

## Docker

```sh
docker compose up --build
```

The studio binds to `127.0.0.1:8000`; a named volume stores projects and media. Ollama uses `host.docker.internal:11434`. For an image worker on the host, set `STYLEMAX_IMAGE_WORKER_URL=http://host.docker.internal:8189`. The GPU worker is not included in the web container. Docker packaging has not been built on the development machine because Docker is unavailable there.

## Tests and checks

```powershell
uv sync --frozen --extra dev --extra marketplaces
uv run --no-sync pytest
uv run --no-sync ruff check src tests worker
uv run --no-sync ruff format --check src tests worker
pnpm --dir frontend test
pnpm --dir frontend lint
pnpm --dir frontend build
```

CI runs backend checks on Windows and Linux and frontend checks/build on Linux. Tests inject external services at the network/inference boundary and exercise actual upload, project, job, ranking and rendering-contract logic. They do not certify third-party availability or GPU model quality.

## Privacy and deployment scope

SQLite metadata, uploads and generated images live in ignored `data/`. Photos are decoded, orientation-normalized, resized and stripped of metadata. JPEG/PNG/WebP inputs have file/pixel limits. Opaque HttpOnly browser sessions isolate projects and media. Project deletion removes its records and files. Clearing your browser cookie removes access to saved projects; account recovery is outside this private first release.

Do not expose this release as a public multi-tenant service. Bind locally or use an authenticated private deployment. Internet hosting needs user authentication, quotas, durable job workers and operational controls. Use HTTPS and `STYLEMAX_SECURE_COOKIES=true` behind a correctly configured reverse proxy. Run a single Uvicorn worker: process-local locks, the generation semaphore and restart recovery assume one application process.

The interface loads Google Fonts with system fallbacks. Listing images load directly from marketplace image hosts. Final-preview image fetching uses host allowlists, public-address validation, no redirects, and byte/time limits.

## Structure

```text
frontend/src/components/     Guided styling flow and demo illustrations
src/stylemax/app.py          Protected HTTP API and orchestration
src/stylemax/store.py        SQLite persistence and restart recovery
src/stylemax/jobs.py         Image job transitions and retries
src/stylemax/ai.py           Ollama and image-worker clients
src/stylemax/marketplaces.py Sources, bounded search/cache and normalization
src/stylemax/ranking.py      Size evidence, ranking and budget basket
worker/                     Optional Qwen/Diffusers GPU service
tests/                      API, provider, media, job and ranking tests
```

Deal-Finder informed the adapter/scoring approach; this repository runs independently. See the [approved design](docs/superpowers/specs/2026-11-07-style-max-design.md), [implementation plan](docs/superpowers/plans/2026-11-07-style-max.md) and [execution record](docs/implementation-progress.md).
