from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from stylemax.app import create_app
from stylemax.config import Settings


@pytest.fixture
def app(tmp_path):
    return create_app(Settings(data_dir=tmp_path))


@pytest.fixture
def client(app):
    with TestClient(app) as client:
        yield client


def photo():
    output = BytesIO()
    Image.new("RGB", (32, 48), "olive").save(output, "PNG")
    return output.getvalue()


def demo_project(client):
    response = client.post(
        "/api/projects", json={"vibe": "Relaxed earth tones", "budget": 180, "demo": True}
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_demo_journey_produces_ten_looks_sized_list_and_explicit_search_links(client):
    project = demo_project(client)
    assert len(project["looks"]) == 10
    assert project["demo"] is True
    selected = client.put(
        f"/api/projects/{project['id']}/selection", json={"look_ids": ["look-1", "look-2"]}
    )
    assert selected.status_code == 200
    response = client.put(
        f"/api/projects/{project['id']}/shopping-list",
        json={
            "sizes": {
                "tops": "M",
                "outerwear": "L",
                "bottoms": "W32 L32",
                "shoes": "42",
                "fit": "relaxed",
                "category": "menswear",
            }
        },
    )
    assert response.status_code == 200, response.text
    garments = response.json()["garments"]
    assert len(garments) > 0
    assert all(item["size"] for item in garments)
    response = client.post(f"/api/projects/{project['id']}/search")
    assert response.status_code == 200
    result = client.get(f"/api/projects/{project['id']}").json()
    assert result["search_links"]
    assert result["offers"] == []  # Demo must not invent purchasable listings.
    assert result["sources"][0]["status"] == "demo"
    response = client.post(f"/api/projects/{project['id']}/preview", json={"offer_ids": []})
    assert response.status_code == 200
    assert client.get(f"/api/projects/{project['id']}").json()["preview"]["demo"] is True


def test_projects_and_media_are_isolated_between_sessions(app, client):
    project = demo_project(client)
    with TestClient(app) as other:
        assert other.get(f"/api/projects/{project['id']}").status_code == 404
        assert other.get("/api/projects").json() == []
        assert other.delete(f"/api/projects/{project['id']}").status_code == 404


def test_live_project_requires_three_real_images_and_normalizes_uploads(client):
    project = client.post(
        "/api/projects", json={"vibe": "Quiet luxury", "budget": 200, "demo": False}
    ).json()
    endpoint = f"/api/projects/{project['id']}/photos"
    assert (
        client.post(
            endpoint, files=[("photos", ("fake.jpg", b"not image", "image/jpeg"))] * 3
        ).status_code
        == 422
    )
    assert (
        client.post(endpoint, files=[("photos", ("a.png", photo(), "image/png"))]).status_code
        == 422
    )
    response = client.post(
        endpoint, files=[("photos", ("../portrait.png", photo(), "image/png"))] * 3
    )
    assert response.status_code == 200, response.text
    project = response.json()
    assert len(project["photos"]) == 3
    media = client.get(project["photos"][0])
    assert media.status_code == 200
    assert media.headers["content-type"] == "image/jpeg"
    assert ".." not in project["photos"][0]


def test_invalid_selection_and_size_profiles_are_rejected(client):
    project = demo_project(client)
    base = f"/api/projects/{project['id']}"
    assert client.put(base + "/selection", json={"look_ids": ["missing"]}).status_code == 422
    assert client.put(base + "/shopping-list", json={"sizes": {}}).status_code == 422
    assert client.post("/api/projects", json={"vibe": "", "budget": -1}).status_code == 422


def test_delete_project_removes_metadata_and_media(client):
    project = demo_project(client)
    assert client.delete(f"/api/projects/{project['id']}").status_code == 204
    assert client.get(f"/api/projects/{project['id']}").status_code == 404
    assert client.get("/api/projects").json() == []


def test_live_generation_requires_photos_and_configured_providers(client):
    project = client.post("/api/projects", json={"vibe": "Minimalist", "budget": 200}).json()
    result = client.post(f"/api/projects/{project['id']}/generate")
    assert result.status_code == 422
