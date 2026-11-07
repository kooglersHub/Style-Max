from types import SimpleNamespace

import pytest

from stylemax.source_worker import kleinanzeigen


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
    result = kleinanzeigen({"keywords": "Leinenhemd", "size": "M"})
    assert len(result) == 1
    assert result[0]["price"] == 25
    assert result[0]["size"] == "M"
