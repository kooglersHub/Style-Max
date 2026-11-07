import json
from io import BytesIO

import httpx
import pytest
from PIL import Image

from stylemax.ai import OllamaPlanner, WorkerRenderer
from stylemax.config import Settings
from stylemax.demo import demo_looks
from stylemax.marketplaces import EbaySource, search_links
from stylemax.models import Garment, LookPlan, Offer
from stylemax.ranking import choose_basket, rank_offers
from stylemax.remote_images import public_image_url


def garment():
    return Garment(
        id="g1",
        name="Olive overshirt",
        category="outerwear",
        color="olive",
        keywords="olive overshirt",
        size="M",
        budget=50,
    )


def offer(id="one", **values):
    base = dict(
        id=id,
        garment_id="g1",
        source="ebay",
        external_id=id,
        title="Olive overshirt M",
        url=f"https://www.ebay.de/itm/{id}",
        price=20,
        size="M",
    )
    return Offer(**(base | values))


def test_incompatible_sizes_are_excluded_and_unknown_shipping_is_not_free():
    result = rank_offers(
        garment(),
        [
            offer("wrong", size="XL"),
            offer("unknown", size=None, title="Olive overshirt"),
            offer("match", shipping=5),
        ],
    )
    assert [item.id for item in result][0] == "match"
    assert not any(item.id == "wrong" for item in result)
    unknown = next(item for item in result if item.id == "unknown")
    assert unknown.total is None
    assert unknown.size_status == "unknown"
    assert "Shipping not provided" in unknown.reasons


def test_basket_respects_combined_budget_and_reports_unknown_costs():
    offers = [
        offer("a", price=20, shipping=5),
        offer("b", garment_id="g2", price=30, shipping=5),
        offer("unknown", garment_id="g3", price=5),
    ]
    result = choose_basket(offers, 50)
    assert result["known_total"] <= 50
    assert result["complete"] is False
    assert result["unmatched"]


def test_search_urls_encode_user_keywords_and_sizes_without_inventing_offers():
    links = search_links([garment()])
    assert len(links) == 3
    assert all(link["kind"] == "search" for link in links)
    assert "overshirt" in links[0]["url"]
    assert "M" in links[0]["url"]


@pytest.mark.parametrize(
    "url",
    [
        "http://localhost/a.jpg",
        "https://127.0.0.1/a",
        "https://169.254.169.254/a",
        "https://[::1]/a",
        "file:///secret",
        "https://user:pass@ebay.de/a",
    ],
)
def test_remote_images_reject_private_network_and_credential_urls(url):
    with pytest.raises(ValueError):
        public_image_url(url)


def test_ollama_validates_ten_distinct_looks_and_sanitizes_untrusted_image_fields():
    raw = demo_looks()
    raw[0]["image"] = "http://attacker.invalid/photo"

    def transport(request):
        body = json.loads(request.content)
        assert body["stream"] is False
        assert "looks" in body["format"]["properties"]
        return httpx.Response(200, json={"message": {"content": json.dumps({"looks": raw})}})

    planner = OllamaPlanner(Settings(), httpx.Client(transport=httpx.MockTransport(transport)))
    plan = planner.plan("quiet luxury", 180)
    assert len(plan.looks) == 10
    assert all(look.image is None and look.status == "queued" for look in plan.looks)
    with pytest.raises(ValueError):
        LookPlan(looks=plan.looks[:2])


def test_image_worker_receives_all_reference_bytes_and_returns_real_image():
    output = BytesIO()
    Image.new("RGB", (16, 16), "red").save(output, "PNG")

    def transport(request):
        assert request.url.path == "/generate"
        assert request.content.count(b'name="images"') == 3
        return httpx.Response(200, content=output.getvalue(), headers={"content-type": "image/png"})

    renderer = WorkerRenderer(
        Settings(image_worker_url="http://localhost:8189"),
        httpx.Client(transport=httpx.MockTransport(transport)),
    )
    assert (
        renderer.render("Dress the same person in an olive outfit", [b"one", b"two", b"three"])
        == output.getvalue()
    )


def test_ebay_oauth_and_search_preserve_unknown_shipping():
    def transport(request):
        if "oauth2" in request.url.path:
            return httpx.Response(200, json={"access_token": "test-token", "expires_in": 7200})
        assert request.headers["X-EBAY-C-MARKETPLACE-ID"] == "EBAY_DE"
        assert "M" in request.url.params["q"]
        return httpx.Response(
            200,
            json={
                "itemSummaries": [
                    {
                        "itemId": "123",
                        "title": "Olive overshirt M",
                        "price": {"value": "25", "currency": "EUR"},
                        "itemWebUrl": "https://www.ebay.de/itm/123",
                    },
                    {
                        "itemId": "456",
                        "title": "Bad link",
                        "price": {"value": "1", "currency": "EUR"},
                        "itemWebUrl": "https://attacker.invalid/",
                    },
                ]
            },
        )

    source = EbaySource(
        Settings(ebay_client_id="client", ebay_client_secret="secret"),
        httpx.Client(transport=httpx.MockTransport(transport)),
    )
    results = source.search(garment())
    assert len(results) == 1
    assert results[0].price == 25
    assert results[0].shipping is None
