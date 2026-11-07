import logging
import re
import secrets
import shutil
from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, Request, Response, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .ai import OllamaPlanner, WorkerRenderer
from .config import Settings
from .demo import build_shopping_list, demo_looks
from .jobs import Jobs
from .marketplaces import MarketplaceSearch
from .media import image_path, normalize_image, save_image
from .models import Brief, PreviewRequest, Selection, ShoppingUpdate
from .remote_images import fetch_product_image, product_collage
from .store import Store, owner_key

log = logging.getLogger(__name__)


def ensure_idle(project):
    if project.get("job") and project["job"]["status"] in ("queued", "running"):
        raise HTTPException(409, "Wait for the current job to finish")


def clear_downstream(project):
    project.update(offers=[], sources=[], search_links=[], preview=None, basket=None)


def create_app(settings=None, planner=None, renderer=None, sources=None):
    settings = settings or Settings()
    store = Store(settings.data_dir)
    jobs = Jobs(
        store, settings, planner or OllamaPlanner(settings), renderer or WorkerRenderer(settings)
    )
    search = MarketplaceSearch(settings, sources)

    @asynccontextmanager
    async def lifespan(app):
        store.recover()
        yield

    app = FastAPI(title="Style Max", version="0.1.0", lifespan=lifespan)
    app.state.store, app.state.jobs = store, jobs

    @app.middleware("http")
    async def private_session(request: Request, call_next):
        if request.method not in ("GET", "HEAD", "OPTIONS"):
            origin = request.headers.get("origin")
            if origin and origin.rstrip("/") != str(request.base_url).rstrip("/"):
                # Vite forwards the original browser host in development.
                from urllib.parse import urlsplit

                if urlsplit(origin).netloc != request.headers.get("host"):
                    return Response("Cross-origin request rejected", status_code=403)
            length = request.headers.get("content-length", "0")
            if not length.isdigit() or int(length) > 32 * 1024 * 1024:
                return Response("Request too large", status_code=413)
        session = request.cookies.get("stylemax_session", "")
        fresh = not re.fullmatch(r"[A-Za-z0-9_-]{48}", session)
        if fresh:
            session = secrets.token_urlsafe(36)
        request.state.owner = owner_key(session)
        response = await call_next(request)
        if fresh:
            response.set_cookie(
                "stylemax_session",
                session,
                httponly=True,
                samesite="strict",
                secure=settings.secure_cookies,
                max_age=60 * 60 * 24 * 365,
            )
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Frame-Options"] = "DENY"
        return response

    def owned(project_id, request):
        return store.get(project_id, request.state.owner)

    @app.get("/api/config")
    def config():
        return {
            "image_worker_configured": bool(settings.image_worker_url),
            "planner": settings.ollama_model,
            "photo_destination": "Your configured local AI services",
            "sources": {
                "ebay": bool(settings.ebay_client_id and settings.ebay_client_secret),
                "kleinanzeigen": settings.enable_kleinanzeigen,
                "vinted": settings.enable_vinted,
            },
        }

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    @app.get("/api/projects")
    def projects(request: Request):
        return store.list(request.state.owner)

    @app.post("/api/projects", status_code=201)
    def create(brief: Brief, request: Request):
        if not brief.vibe.strip():
            raise HTTPException(422, "Describe a style direction")
        project = store.create(request.state.owner, brief.model_dump())
        if brief.demo:
            project = store.update(project["id"], lambda p: p.update(looks=demo_looks()))
        return project

    @app.get("/api/projects/{project_id}")
    def project(project_id: str, request: Request):
        return owned(project_id, request)

    @app.delete("/api/projects/{project_id}", status_code=204)
    def delete(project_id: str, request: Request):
        with store.lock:
            store.delete(project_id, request.state.owner)
            shutil.rmtree(settings.data_dir / "media" / project_id, ignore_errors=True)
        return Response(status_code=204)

    @app.post("/api/projects/{project_id}/photos")
    async def photos(project_id: str, request: Request, photos: list[UploadFile] = File(...)):
        ensure_idle(owned(project_id, request))
        if len(photos) != 3:
            raise HTTPException(422, "Upload exactly three photos")
        contents = [
            normalize_image(
                await photo.read(settings.max_photo_bytes + 1), settings.max_photo_bytes
            )
            for photo in photos
        ]
        with store.lock:
            current = owned(project_id, request)
            ensure_idle(current)
            if current["looks"] and not current["demo"]:
                raise HTTPException(
                    409, "Start a new project to change reference photos after generation"
                )
            old = current["photos"]
            urls = [save_image(settings, project_id, content) for content in contents]
            updated = store.update(project_id, lambda p: p.update(photos=urls))
            for url in old:
                image_path(settings, url).unlink(missing_ok=True)
        return updated

    @app.get("/api/projects/{project_id}/media/{filename}")
    def media(project_id: str, filename: str, request: Request):
        owned(project_id, request)
        if not re.fullmatch(r"[a-f0-9]{32}\.jpg", filename):
            raise HTTPException(404)
        path = settings.data_dir / "media" / project_id / filename
        if not path.is_file():
            raise HTTPException(404)
        return FileResponse(path, media_type="image/jpeg")

    @app.post("/api/projects/{project_id}/generate")
    def generate(project_id: str, request: Request, background: BackgroundTasks):
        project = owned(project_id, request)
        if project["demo"]:
            raise HTTPException(422, "Demo looks are already available")
        if len(project["photos"]) != 3:
            raise HTTPException(422, "Upload three photos before generating looks")
        if renderer is None and not settings.image_worker_url:
            raise HTTPException(
                503, "Connect the local image worker in .env first. See the setup guide."
            )
        if project["looks"] and all(item["status"] == "completed" for item in project["looks"]):
            return project
        job_id = jobs.start(project_id, "looks")
        background.add_task(jobs.generate, project_id, job_id)
        return store.get(project_id)

    @app.put("/api/projects/{project_id}/selection")
    def selection(project_id: str, body: Selection, request: Request):
        with store.lock:
            project = owned(project_id, request)
            ensure_idle(project)
            available = {look["id"] for look in project["looks"] if look["status"] == "completed"}
            if len(set(body.look_ids)) != len(body.look_ids) or not set(body.look_ids) <= available:
                raise HTTPException(422, "Select only completed looks from this project")

            def change(p):
                p.update(selected=body.look_ids, garments=[], sizes=None)
                clear_downstream(p)

            return store.update(project_id, change)

    @app.put("/api/projects/{project_id}/shopping-list")
    def shopping_list(project_id: str, body: ShoppingUpdate, request: Request):
        with store.lock:
            project = owned(project_id, request)
            ensure_idle(project)
            if not project["selected"]:
                raise HTTPException(422, "Choose at least one look first")
            if body.budget is not None:
                project["budget"] = body.budget
            garments = (
                [item.model_dump() for item in body.garments]
                if body.garments is not None
                else build_shopping_list(project, body.sizes.model_dump())
            )
            if not garments or len({g["id"] for g in garments}) != len(garments):
                raise HTTPException(422, "Provide a nonempty shopping list with unique item IDs")
            if len(garments) > 30 or any(not g["size"].strip() for g in garments):
                raise HTTPException(422, "Use at most 30 garments and specify each size")

            def change(p):
                p.update(sizes=body.sizes.model_dump(), garments=garments, budget=project["budget"])
                clear_downstream(p)

            return store.update(project_id, change)

    def run_search(project_id, job_id):
        try:
            current = jobs.patch(project_id, job_id, lambda p: p["job"].update(status="running"))
            if not current:
                return
            result = search.run(current)
            jobs.patch(
                project_id,
                job_id,
                lambda p: (p.update(**result), p["job"].update(status="completed", completed=1)),
            )
        except Exception as error:
            jobs.fail(project_id, job_id, error)

    @app.post("/api/projects/{project_id}/search")
    def find_offers(project_id: str, request: Request, background: BackgroundTasks):
        project = owned(project_id, request)
        if not project["garments"]:
            raise HTTPException(422, "Confirm your shopping list first")
        job_id = jobs.start(project_id, "search")
        background.add_task(run_search, project_id, job_id)
        return store.get(project_id)

    def render_preview(project_id, job_id, offer_ids):
        try:
            project = jobs.patch(project_id, job_id, lambda p: p["job"].update(status="running"))
            if not project:
                return
            if project["demo"]:
                jobs.patch(
                    project_id,
                    job_id,
                    lambda p: (
                        p.update(
                            preview={
                                "demo": True,
                                "image": None,
                                "offer_ids": [],
                                "missing_images": [],
                            }
                        ),
                        p["job"].update(status="completed", completed=1),
                    ),
                )
                return
            offers = [item for item in project["offers"] if item["id"] in offer_ids]
            images, missing = [], []
            for item in offers:
                try:
                    images.append(fetch_product_image(item["image"]))
                except Exception:
                    missing.append(item["title"])
            references = [image_path(settings, project["photos"][0]).read_bytes()]
            collage = product_collage(images)
            if collage:
                references.append(collage)
            prompt = (
                "Dress the same person from reference 1 in the selected garments in reference 2 "
                "(if present). Preserve face and body. Full body photograph. Garments: "
                + "; ".join(item["title"] for item in offers)
            )
            with jobs.gpu:
                content = jobs.renderer.render(prompt, references)
            with store.lock:
                store.get(project_id)
                url = save_image(settings, project_id, content)
                jobs.patch(
                    project_id,
                    job_id,
                    lambda p: (
                        p.update(
                            preview={
                                "demo": False,
                                "image": url,
                                "offer_ids": offer_ids,
                                "missing_images": missing,
                            }
                        ),
                        p["job"].update(status="completed", completed=1),
                    ),
                )
        except Exception as error:
            jobs.fail(project_id, job_id, error)

    @app.post("/api/projects/{project_id}/preview")
    def preview(
        project_id: str, body: PreviewRequest, request: Request, background: BackgroundTasks
    ):
        project = owned(project_id, request)
        offers = {item["id"]: item for item in project["offers"]}
        if not project["demo"]:
            if not body.offer_ids or not set(body.offer_ids) <= offers.keys():
                raise HTTPException(422, "Choose valid offers from this project")
            if len({offers[key]["garment_id"] for key in body.offer_ids}) != len(body.offer_ids):
                raise HTTPException(422, "Choose one offer per garment")
            if renderer is None and not settings.image_worker_url:
                raise HTTPException(503, "Connect the image worker first")
        job_id = jobs.start(project_id, "preview")
        background.add_task(render_preview, project_id, job_id, body.offer_ids)
        return store.get(project_id)

    if settings.frontend_dir.is_dir():
        app.mount("/", StaticFiles(directory=settings.frontend_dir, html=True), name="studio")
    return app


app = create_app()
