"""Bounded subprocess entrypoint for optional community marketplace clients."""

import contextlib
import json
import sys
import time

from .marketplaces import search_query
from .models import Garment


def kleinanzeigen(garment):
    from kleinanzeigen_api import KleinanzeigenAPI

    client = KleinanzeigenAPI(rate_limit=1.5, timeout=15, max_retries=1)
    query = search_query(Garment.model_validate(garment))
    rows = client.search(q=query, pages=1, size=12)
    results = []
    for row in rows[:12]:
        price_type = (row.price_type or "").upper()
        free = price_type in ("FREE", "GIVE_AWAY")
        if not free and (row.price is None or row.price <= 0):
            continue
        attributes = row.attributes or {}
        results.append(
            dict(
                external_id=str(row.id),
                url=row.url,
                title=row.title,
                price=0.0 if free else float(row.price),
                image=(row.images or [None])[0],
                size=attributes.get("Größe"),
                location=row.city or "",
            )
        )
    return results


def vinted(garment):
    from vinted_scraper import VintedScraper

    time.sleep(1.5)
    client = VintedScraper("https://www.vinted.de")
    query = search_query(Garment.model_validate(garment))
    rows = client.search({"search_text": query, "per_page": 12})
    results = []
    for row in rows[:12]:
        price = row.price
        currency = getattr(row, "currency", "EUR")
        if isinstance(price, dict):
            currency, price = price.get("currency_code"), price.get("amount")
        if currency != "EUR":
            continue
        photo = getattr(row, "photo", None)
        image = photo.get("url") if isinstance(photo, dict) else getattr(photo, "url", None)
        results.append(
            dict(
                external_id=str(row.id),
                url=row.url,
                title=row.title,
                price=float(price),
                size=getattr(row, "size_title", None),
                image=image,
                condition=str(getattr(row, "status", "Unknown")),
            )
        )
    return results


def main():
    garment = json.load(sys.stdin)
    # Some libraries print transport diagnostics; keep the JSON channel separate.
    with contextlib.redirect_stdout(sys.stderr):
        rows = {"kleinanzeigen": kleinanzeigen, "vinted": vinted}[sys.argv[1]](garment)
    print(json.dumps(rows))


if __name__ == "__main__":
    main()
