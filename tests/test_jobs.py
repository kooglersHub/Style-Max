from concurrent.futures import ThreadPoolExecutor
from io import BytesIO

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from PIL import Image

from stylemax.app import create_app
from stylemax.config import Settings
from stylemax.demo import demo_looks
from stylemax.jobs import Jobs
from stylemax.marketplaces import MarketplaceSearch
from stylemax.models import LookPlan
from stylemax.store import Store
from worker.app import create_worker


def image_bytes():
    stream = BytesIO()
    Image.new("RGB", (40, 60), "olive").save(stream, "JPEG")
    return stream.getvalue()


class Planner:
    def plan(self, vibe, budget):
        return LookPlan(looks=[dict(look, status="queued") for look in demo_looks()])


class Renderer:
    def __init__(self):
        self.calls = 0

    def render(self, prompt, references):
        self.calls += 1
        if self.calls == 2:
            raise RuntimeError("temporary worker failure")
        return image_bytes()


def test_live_job_preserves_partial_results_and_retries_only_failed_images(tmp_path):
    renderer = Renderer()
    app = create_app(Settings(data_dir=tmp_path), planner=Planner(), renderer=renderer)
    with TestClient(app) as client:
        project = client.post("/api/projects", json={"vibe": "Earthy layers", "budget": 180}).json()
        base = f"/api/projects/{project['id']}"
        client.post(
            base + "/photos", files=[("photos", ("test.jpg", image_bytes(), "image/jpeg"))] * 3
        )
        assert client.post(base + "/generate").status_code == 200
        partial = client.get(base).json()
        assert partial["job"]["status"] == "failed"
        assert len([look for look in partial["looks"] if look["status"] == "completed"]) == 9
        first_image = partial["looks"][0]["image"]
        client.post(base + "/generate")
        completed = client.get(base).json()
        assert completed["job"]["status"] == "completed"
        assert completed["looks"][0]["image"] == first_image
        assert len(list((tmp_path / "media" / project["id"]).glob("*.jpg"))) == 13
        with TestClient(app) as other:
            assert other.get(first_image).status_code == 404
        client.delete(base)
        assert not (tmp_path / "media" / project["id"]).exists()


def test_concurrent_job_claims_allow_only_one_active_job(tmp_path):
    settings = Settings(data_dir=tmp_path)
    store = Store(tmp_path)
    project = store.create("owner", {"vibe": "Test", "budget": 180, "demo": False})
    jobs = Jobs(store, settings, Planner(), Renderer())

    def claim(_):
        try:
            return jobs.start(project["id"], "looks")
        except HTTPException as error:
            return error.status_code

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(claim, range(2)))
    assert sum(isinstance(result, str) for result in results) == 1
    assert 409 in results


def test_restart_marks_running_jobs_retryable_without_losing_completed_looks(tmp_path):
    store = Store(tmp_path)
    project = store.create("owner", {"vibe": "Test", "budget": 180, "demo": False})
    store.update(
        project["id"],
        lambda p: p.update(
            job={"status": "running"},
            looks=[{"id": "look-1", "status": "completed"}, {"id": "look-2", "status": "running"}],
        ),
    )
    store.recover()
    project = store.get(project["id"])
    assert project["job"]["status"] == "failed"
    assert project["looks"][0]["status"] == "completed"
    assert project["looks"][1]["status"] == "failed"
    assert "Retry" in project["error"]


def test_failed_source_does_not_discard_other_sources(tmp_path):
    class GoodSource:
        name = "ebay"

        def search(self, garment):
            from stylemax.models import Offer

            return [
                Offer(
                    id="one",
                    source="ebay",
                    external_id="123",
                    garment_id=garment.id,
                    url="https://www.ebay.de/itm/123",
                    title="Olive overshirt M",
                    price=15,
                    shipping=5,
                    size="M",
                )
            ]

    class FailedSource:
        name = "vinted"

        def search(self, garment):
            raise RuntimeError("blocked")

    project = {
        "demo": False,
        "budget": 50,
        "garments": [
            {
                "id": "g1",
                "category": "outerwear",
                "name": "Olive overshirt",
                "color": "olive",
                "keywords": "olive overshirt",
                "size": "M",
                "budget": 50,
            }
        ],
    }
    result = MarketplaceSearch(Settings(data_dir=tmp_path), [GoodSource(), FailedSource()]).run(
        project
    )
    assert len(result["offers"]) == 1
    assert (
        next(source for source in result["sources"] if source["source"] == "vinted")["status"]
        == "error"
    )
    assert result["basket"]["known_total"] == 20


def test_worker_contract_validates_auth_and_returns_rendered_image(monkeypatch):
    monkeypatch.setenv("STYLEMAX_IMAGE_WORKER_KEY", "local-test-secret")

    class Pipeline:
        def __call__(self, **kwargs):
            assert len(kwargs["image"]) == 3
            assert kwargs["prompt"] == "An olive outfit on the same person"
            return type("Result", (), {"images": [Image.new("RGB", (40, 60), "olive")]})()

    client = TestClient(create_worker(Pipeline()))
    files = [("images", ("photo.jpg", image_bytes(), "image/jpeg"))] * 3
    assert (
        client.post(
            "/generate", data={"prompt": "An olive outfit on the same person"}, files=files
        ).status_code
        == 401
    )
    response = client.post(
        "/generate",
        data={"prompt": "An olive outfit on the same person"},
        files=files,
        headers={"Authorization": "Bearer local-test-secret"},
    )
    assert response.status_code == 200
    assert Image.open(BytesIO(response.content)).size == (40, 60)


def test_image_metadata_is_removed_before_storage(tmp_path):
    from stylemax.media import normalize_image

    image = Image.new("RGB", (40, 60), "olive")
    exif = Image.Exif()
    exif[270] = "private photo description"
    output = BytesIO()
    image.save(output, "JPEG", exif=exif)
    assert not Image.open(BytesIO(normalize_image(output.getvalue()))).getexif()


@pytest.mark.parametrize("url", ["https://attacker.invalid", "http://testserver"])
def test_cross_origin_mutations_are_rejected(tmp_path, url):
    client = TestClient(create_app(Settings(data_dir=tmp_path)))
    # The testserver origin itself is allowed; an arbitrary Origin with mismatched Host is not.
    result = client.post(
        "/api/projects",
        json={"vibe": "Minimal layers"},
        headers={"origin": url, "host": "127.0.0.1:8000"},
    )
    assert result.status_code == 403
