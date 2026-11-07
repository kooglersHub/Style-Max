from types import SimpleNamespace

import pytest

from stylemax.source_worker import kleinanzeigen


def test_current_vinted_client_preserves_product_images_and_composite_size_labels(monkeypatch):
    package = pytest.importorskip("vinted_scraper")
    from vinted_scraper.models import VintedItem

    from stylemax.source_worker import vinted

    row = VintedItem(
        json_data={
            "id": 123,
            "url": "https://www.vinted.de/items/123",
            "title": "Leinenhemd",
            "price": {"amount": "20", "currency_code": "EUR"},
            "size_title": "M / 38 / 10",
            "photo": {"url": "https://images1.vinted.net/product.jpg"},
        }
    )
    monkeypatch.setattr(package, "VintedScraper", lambda _: SimpleNamespace(search=lambda _: [row]))
    monkeypatch.setattr("stylemax.source_worker.time.sleep", lambda _: None)
    result = vinted(
        {
            "id": "g1",
            "name": "Leinenhemd",
            "keywords": "Leinenhemd",
            "category": "tops",
            "color": "beige",
            "size": "M",
        }
    )
    assert result[0]["image"] == "https://images1.vinted.net/product.jpg"
    assert result[0]["size"] == "M / 38 / 10"
    assert result[0]["price"] == 20


def test_kleinanzeigen_preserves_native_specified_amount_prices_and_excludes_unknown_zero(
    monkeypatch,
):
    kleinanzeigen_api = pytest.importorskip("kleinanzeigen_api")

    rows = [
        SimpleNamespace(
            id="123",
            url="https://www.kleinanzeigen.de/s-anzeige/123",
            title="Leinenhemd M",
            price=25,
            price_type="SPECIFIED_AMOUNT",
            attributes={"Größe": "M"},
            images=[],
            city="Berlin",
        ),
        SimpleNamespace(
            id="456",
            url="https://www.kleinanzeigen.de/s-anzeige/456",
            title="Preis auf Anfrage",
            price=0,
            price_type="PLEASE_CONTACT",
            attributes={},
            images=[],
            city="Berlin",
        ),
    ]
    monkeypatch.setattr(
        kleinanzeigen_api, "KleinanzeigenAPI", lambda **_: SimpleNamespace(search=lambda **_: rows)
    )
    result = kleinanzeigen(
        {
            "id": "g1",
            "name": "Leinenhemd",
            "keywords": "Leinenhemd",
            "category": "tops",
            "color": "beige",
            "size": "M",
        }
    )
    assert len(result) == 1
    assert result[0]["price"] == 25
    assert result[0]["size"] == "M"
