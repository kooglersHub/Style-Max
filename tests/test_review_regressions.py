from urllib.parse import parse_qs, urlsplit

import pytest
from fastapi.testclient import TestClient

from stylemax.app import create_app
from stylemax.config import Settings
from stylemax.demo import build_shopping_list, demo_looks
from stylemax.marketplaces import search_links
from stylemax.models import Garment, Offer
from stylemax.ranking import choose_basket, rank_offers


def test_fit_and_category_preferences_reach_marketplace_searches():
    project = {"selected": ["look-1"], "looks": demo_looks(), "budget": 180}
    sizes = {
        "tops": "M",
        "outerwear": "L",
        "bottoms": "32",
        "shoes": "42",
        "fit": "slim",
        "category": "womenswear",
    }
    garments = [Garment.model_validate(item) for item in build_shopping_list(project, sizes)]
    query = parse_qs(urlsplit(search_links(garments)[0]["url"]).query)["_nkw"][0]
    assert "slim" in query.lower()
    assert "damen" in query.lower()


@pytest.mark.parametrize("size", ["M / 38 / 10", "M (38)", "M / L"])
def test_compatible_composite_sizes_remain_candidates(size):
    garment = Garment(
        id="g", name="Overshirt", keywords="overshirt", category="tops", color="olive", size="M"
    )
    offer = Offer(
        id="one",
        garment_id="g",
        source="vinted",
        external_id="1",
        url="https://www.vinted.de/items/1",
        title="Overshirt",
        size=size,
        price=20,
    )
    result = rank_offers(garment, [offer])
    assert len(result) == 1
    assert result[0].size_status in ("match", "unknown")


def test_basket_never_allocates_a_physical_listing_twice():
    offers = [
        Offer(
            id=f"offer-{index}",
            garment_id=f"g{index}",
            source="ebay",
            external_id="123",
            url="https://www.ebay.de/itm/123",
            title="Overshirt M",
            size="M",
            price=10,
            shipping=2,
        )
        for index in (1, 2)
    ]
    basket = choose_basket(offers, 100)
    assert len(basket["offer_ids"]) == 1
    assert basket["known_total"] == 12
    assert basket["complete"] is False


def test_all_ten_demo_looks_can_reach_the_editable_shopping_list(tmp_path):
    with TestClient(create_app(Settings(data_dir=tmp_path))) as client:
        project = client.post(
            "/api/projects", json={"vibe": "Earth tones", "demo": True, "budget": 20}
        ).json()
        base = f"/api/projects/{project['id']}"
        client.put(
            base + "/selection", json={"look_ids": [look["id"] for look in project["looks"]]}
        )
        sizes = {
            "tops": "M",
            "outerwear": "L",
            "bottoms": "32",
            "shoes": "42",
            "fit": "relaxed",
            "category": "all",
        }
        result = client.put(base + "/shopping-list", json={"sizes": sizes})
        assert result.status_code == 200, result.text
        garments = result.json()["garments"]
        assert len(garments) == 40
        assert all(Garment.model_validate(item) for item in garments)
        assert (
            client.put(
                base + "/shopping-list", json={"sizes": sizes, "garments": garments}
            ).status_code
            == 200
        )


def test_new_search_invalidates_old_outfit_preview(tmp_path):
    app = create_app(Settings(data_dir=tmp_path))
    with TestClient(app) as client:
        project = client.post("/api/projects", json={"vibe": "Earth tones", "demo": True}).json()
        base = f"/api/projects/{project['id']}"
        client.put(base + "/selection", json={"look_ids": ["look-1"]})
        client.put(
            base + "/shopping-list",
            json={"sizes": {"tops": "M", "outerwear": "L", "bottoms": "32", "shoes": "42"}},
        )
        client.post(base + "/search")
        client.post(base + "/preview", json={"offer_ids": []})
        assert client.get(base).json()["preview"] is not None
        client.post(base + "/search")
        assert client.get(base).json()["preview"] is None


def test_manual_preview_rejects_the_same_physical_listing_for_two_garments(tmp_path):
    app = create_app(Settings(data_dir=tmp_path))
    with TestClient(app) as client:
        project = client.post("/api/projects", json={"vibe": "Earth tones", "demo": True}).json()
        offers = [
            Offer(
                id=f"offer-{index}",
                garment_id=f"g{index}",
                source="ebay",
                external_id="123",
                url="https://www.ebay.de/itm/123",
                title="Overshirt M",
                price=10,
                shipping=2,
            ).model_dump()
            for index in (1, 2)
        ]
        app.state.store.update(project["id"], lambda p: p.update(demo=False, offers=offers))
        result = client.post(
            f"/api/projects/{project['id']}/preview", json={"offer_ids": ["offer-1", "offer-2"]}
        )
        assert result.status_code == 422
