import logging
from threading import Semaphore
from uuid import uuid4

from fastapi import HTTPException

from .media import image_path, save_image

log = logging.getLogger(__name__)


class Jobs:
    def __init__(self, store, settings, planner, renderer):
        self.store, self.settings = store, settings
        self.planner, self.renderer = planner, renderer
        self.gpu = Semaphore(1)

    def start(self, project_id, kind):
        job_id = uuid4().hex

        def claim(project):
            if project.get("job") and project["job"]["status"] in ("running", "queued"):
                raise HTTPException(409, "This project already has a job in progress")
            project["job"] = {
                "id": job_id,
                "kind": kind,
                "status": "queued",
                "completed": 0,
                "total": 10 if kind == "looks" else 1,
            }
            project["error"] = None

        self.store.update(project_id, claim)
        return job_id

    def patch(self, project_id, job_id, change):
        def guarded(project):
            if project.get("job", {}).get("id") == job_id:
                change(project)

        return self.store.update(project_id, guarded)

    def generate(self, project_id, job_id):
        try:
            project = self.patch(project_id, job_id, lambda p: p["job"].update(status="running"))
            if not project:
                return
            if not project["looks"]:
                plan = self.planner.plan(project["vibe"], project["budget"])
                self.patch(
                    project_id,
                    job_id,
                    lambda p: p.update(looks=[look.model_dump() for look in plan.looks]),
                )
            project = self.store.get(project_id)
            references = [image_path(self.settings, url).read_bytes() for url in project["photos"]]
            for index, look in enumerate(project["looks"]):
                if look["status"] == "completed":
                    continue
                if not self.patch(
                    project_id,
                    job_id,
                    lambda p, i=index: p["looks"][i].update(status="running", error=None),
                ):
                    return
                try:
                    with self.gpu:
                        content = self.renderer.render(look["prompt"], references)
                    # Deletion while rendering must not resurrect files.
                    with self.store.lock:
                        self.store.get(project_id)
                        url = save_image(self.settings, project_id, content)
                        self.patch(
                            project_id,
                            job_id,
                            lambda p, i=index, u=url: p["looks"][i].update(
                                status="completed", image=u
                            ),
                        )
                except HTTPException as error:
                    if error.status_code == 404:
                        return
                    raise
                except Exception as error:
                    log.warning("Look render failed: %s", type(error).__name__)
                    self.patch(
                        project_id,
                        job_id,
                        lambda p, i=index: p["looks"][i].update(
                            status="failed",
                            error="Image worker failed. Check its connection and retry.",
                        ),
                    )
                self.patch(
                    project_id,
                    job_id,
                    lambda p: p["job"].update(
                        completed=sum(x["status"] == "completed" for x in p["looks"])
                    ),
                )

            def finish(p):
                failed = any(x["status"] != "completed" for x in p["looks"])
                p["job"]["status"] = "failed" if failed else "completed"
                p["error"] = (
                    "Some images could not be generated. Retry to finish them." if failed else None
                )

            self.patch(project_id, job_id, finish)
        except Exception as error:
            self.fail(project_id, job_id, error)

    def fail(self, project_id, job_id, error):
        log.warning("Generation job failed: %s", type(error).__name__)
        self.patch(
            project_id,
            job_id,
            lambda p: (
                p["job"].update(status="failed"),
                p.update(
                    error="AI service unavailable or returned an invalid response. Check provider settings, then retry."
                ),
            ),
        )
