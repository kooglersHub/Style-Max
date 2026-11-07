# Style-Max design

Date: 2026-11-07
Status: approved by the user on 2026-11-07; implementation in progress.

## Purpose

Help someone turn a style direction into affordable outfits they can actually buy. The user describes a vibe and uploads three photos of themselves. Style-Max generates ten distinct outfit concepts on that person, lets them choose favorites, collects their clothing sizes, creates an editable shopping list, finds matching secondhand listings, and produces previews of the selected offers with links.

Success means completing this flow with real provider responses and traceable listings. Demo content must be identified as demo content. A search link is useful, but must never be presented as a verified offer.

## Approaches considered

1. **Standalone Style-Max with reusable Deal-Finder patterns — selected.** React styling studio and Python service, independently deployable. Reuse the collector boundary, normalization, bounded search, deduplication, and scoring ideas from the sibling project. This gives the photo and outfit workflow its own interface without coupling it to a monitoring dashboard.
2. **Extend Deal-Finder.** Less initial backend setup, but its listing-monitoring model and server-rendered UI do not fit the photo-generation workflow well. Rejected in favor of the standalone app.
3. **Hosted frontend with external automation.** Easy initial hosting, but adds dependencies between uploads, image workers, and marketplace clients. Not selected; the user selected a self-hosted application.

## First release scope

- A responsive styling studio with six stages: brief, ten looks, favorites, fit, offers, and final outfit.
- Three validated photo uploads, editable vibe text, optional preset directions, and a total shopping-list budget in EUR.
- Ten independently tracked look generations. Each has an outfit description and structured garment specifications, used both for rendering and the shopping list.
- Favorite selection and a size profile: tops, outerwear, trouser waist/inseam or labeled size, EU shoe size, and preferred fit. Gendered shopping categories are chosen by the user rather than inferred from photos.
- An editable shopping list derived from selected looks. Each garment carries category, color, material/style keywords, requested size, budget allocation, and originating look IDs. Deduplicate shared garments. Builder choice: the budget applies to the entire confirmed shopping list across all selected looks, not separately to each look; state this beside the budget input and allow edits before searching.
- Read-only marketplace searches, explicit provider status, ranked results, shipping visibility, size evidence, direct listing links, and manual marketplace search links when live search cannot run.
- User selection of offers for a final outfit visualization. Clearly label visualizations as approximations, not fit guarantees.
- Saved local projects, recoverable job state, project deletion, and a clearly labeled demo journey available without AI or marketplace credentials.
- Windows setup/start instructions, Docker packaging, automated tests, formatting/linting, and CI.

No checkout, automatic purchases, seller messaging, subscription billing, wardrobe social network, or public account system is included. Multi-user public hosting is outside the first release; the initial deployment is a private/self-hosted studio.

## Architecture

Builder choice: React + TypeScript + Vite frontend; FastAPI + Pydantic backend; SQLite project/job metadata; a git-ignored local data directory for uploads and generated media. Production serves the frontend and API from one origin. Development uses a Vite API proxy.

Use small feature modules for projects/uploads, looks/jobs, shopping lists, marketplace adapters, ranking, and image generation. External clients are dependency-injected for testing. Keep the application independent of the sibling Deal-Finder checkout; it must work when cloned alone.

Reuse open-source UI primitives where appropriate, with shadcn/Radix-style accessible controls and Lucide icons. The visual direction is a fashion studio: warm off-white background, dark typography, large portrait cards, restrained green accents, and compact navigation. Avoid a generic analytics dashboard. Document dependencies and attribution, and do not copy third-party code without checking its license.

## AI and image generation

Use configurable adapters instead of binding the product to one paid vendor. Default supported open-source path: a local Ollama-compatible chat endpoint for structured styling plans and a separately launched Qwen-Image-Edit worker using Diffusers for image generation. The model supports one to three input images; the three reference photos inform the initial looks. Keep GPU/model dependencies optional so a normal web installation does not download model weights.

Ship the image-worker service and its documented HTTP contract, model configuration, and launch instructions. The application sends actual image bytes and prompts, and stores returned image files. A configured worker produces real images; when unavailable, show a setup/error state with retry instead of fabricating generation success. Demo mode uses explicitly labeled sample concepts, never claims to depict the uploaded user, and does not silently replace failed live work.

The language-model response must validate against a schema: exactly ten distinct look IDs, titles, rendering descriptions, and garment specifications. The model prompt includes the user's brief and explicit preferences. Treat listing descriptions and all model output as untrusted data. A malformed response fails with an actionable retry message; do not turn it into ten copies of one outfit.

Generate images as persisted background jobs, sequentially by default to bound GPU memory. Track queued/running/completed/failed status per image, show partial results, support retries, and prevent duplicate active requests. Interruptions must leave an understandable recoverable state. Provider timeouts and result-size limits are configurable and finite.

Final offer previews use the user's reference image plus a collage of the chosen garment images, keeping within the worker's supported reference count. Only fetch validated image URLs with response-size/time limits and protections against private-network targets and unsafe redirects. If product imagery is missing, explain which garments are represented by text only. Preserve the chosen listing links separately from generated imagery.

Local image inference requires suitable GPU resources and downloaded model weights. Deliver and test the integration contract with fake services if such a worker is unavailable on this machine; report the absence of a real generation test explicitly.

## Marketplace integrations and ranking

- **eBay:** official Browse API, application credentials supplied through environment variables, server-side OAuth token management, Germany/EUR defaults, bounded read-only search, and normalized item records. Document that API access is separate from open-source client code.
- **Kleinanzeigen:** optional `kleinanzeigen-api` client, following the existing Deal-Finder adapter's mapping and validation approach. It is unofficial and may be unavailable or blocked. Preserve a bounded request rate and surface errors without bypassing challenges.
- **Vinted:** optional open-source `vinted_scraper` client behind the same adapter boundary. It is unofficial. Handle blocked/unavailable responses explicitly; no CAPTCHA bypass or automatic source switching that misrepresents where data came from.
- **Fallback:** real, encoded marketplace search URLs for each garment. Label them “Search marketplace”; do not manufacture prices, seller information, size confirmation, or availability.

A normalized offer contains source, external ID, URL, title, image URL, item price, currency, known shipping cost, size evidence, condition, location when known, and retrieval time. Reject invalid URLs, prices, currency mismatches, and duplicate identities. Validate marketplace URLs against the corresponding marketplace host.

Rank by garment relevance, explicit size compatibility, budget, known delivered cost, and condition. Explain the ranking with concise reasons. Missing shipping is unknown, not free. Unknown size requires confirmation; an explicitly incompatible size is excluded. Do not claim a discount without a defensible comparison or claim to have searched the entire marketplace. Select a compatible basket within budget where possible, otherwise expose the shortfall and alternatives.

Search only the garments in the confirmed shopping list, with bounded per-source concurrency, query/result limits, timeouts, and a short cache. One failed source must not discard successful results from another. Listing availability is a point-in-time observation and the marketplace is the source of truth at purchase time.

## Data handling and application behavior

Upload only JPEG, PNG, or WebP images whose bytes can be decoded, with explicit file and pixel limits. Normalize orientation and remove metadata. Store random file names rather than user-provided paths. Photos and generated media remain in the local data directory, excluded from Git.

Use an opaque browser session to isolate projects and protect project/media endpoints. Return only media owned by that session. Support deletion of project records and associated files. Keep keys server-side, redact provider failures in logs, and give users useful error messages without exposing credentials. Explain which configured AI service receives photos before generation.

For the initial private deployment, document local/private-network operation. Public Internet deployment needs additional authentication, access controls, and operational hardening; do not describe the first release as a public multi-tenant service.

## Delivery and validation

Work in logical commits and push to `kooglersHub/Style-Max` on `main` at working milestones, as explicitly requested. Never include `.env`, reference photos, generated media, model weights, or runtime databases. Confirm the actual push result and report any authentication blocker.

Validation includes backend unit/integration tests for uploads, session ownership, schema rejection, job transitions/retries, provider normalization/failures, unknown shipping, incompatible sizes, budget ranking, and project deletion. Frontend tests cover the guided flow, validation, favorites, size entry, and error/retry states. Run a browser smoke test of the demo journey and responsive layouts if browser tooling is available. CI runs the test suites, type checks, linting, and production build.

Document setup, launch, test commands, architecture, provider configuration, demo/live differences, GPU requirements, and marketplace limitations in the README. A successful demo/build is not evidence of live AI generation or live API access; report what was actually exercised.

## References inspected

Builder review completed. The reviewer identified budget scope as ambiguous; the explicit total-shopping-list rule above resolves it. No other implementation-blocking questions remained.

- Sibling repository: `../Deal-Finder`, remote `https://github.com/kooglersHub/deal-radar.git`; inspected collector, scoring, schemas, web app, and Kleinanzeigen ADR. Do not modify it for this project.
- UI primitives and blocks: https://ui.shadcn.com/blocks/dashboard
- eBay Browse API: https://developer.ebay.com/develop/api/buy
- Kleinanzeigen client: https://github.com/monkrel/kleinanzeigen-api
- Vinted client: https://github.com/Giglium/vinted_scraper
- Qwen image model: https://huggingface.co/Qwen/Qwen-Image-Edit-2509
