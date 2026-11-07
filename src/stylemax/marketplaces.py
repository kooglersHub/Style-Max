import json
import logging
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from threading import RLock
from urllib.parse import quote, urlencode, urlsplit

import httpx

from .models import Garment, Offer
from .ranking import choose_basket, rank_offers
from .store import now

log = logging.getLogger(__name__)
HOSTS = {
    "ebay": ("ebay.de", "ebay.com"),
    "vinted": ("vinted.de",),
    "kleinanzeigen": ("kleinanzeigen.de",),
}


def valid_listing(source, url):
    parsed = urlsplit(url)
    host = (parsed.hostname or "").lower()
    return (
        parsed.scheme == "https"
        and not parsed.username
        and not parsed.password
        and any(host == value or host == "www." + value for value in HOSTS[source])
    )


def search_query(garment):
    parts = [garment.keywords, garment.size]
    if garment.category not in ("shoes", "accessories") and garment.fit != "regular":
        parts.append(garment.fit)
    audience = {"menswear": "Herren", "womenswear": "Damen"}.get(garment.audience)
    if audience:
        parts.append(audience)
    return " ".join(parts).strip()


def search_links(garments):
    links = []
    for garment in garments:
        query = search_query(garment)
        urls = {
            "ebay": "https://www.ebay.de/sch/i.html?" + urlencode({"_nkw": query, "_sop": "15"}),
            "vinted": "https://www.vinted.de/catalog?" + urlencode({"search_text": query}),
            "kleinanzeigen": f"https://www.kleinanzeigen.de/s-{quote(query.replace(' ', '-'), safe='')}/k0",
        }
        links.extend(
            {"garment_id": garment.id, "source": source, "url": url, "kind": "search"}
            for source, url in urls.items()
        )
    return links


class EbaySource:
    name = "ebay"

    def __init__(self, settings, client=None):
        self.settings = settings
        self.client = client or httpx.Client(timeout=settings.marketplace_timeout)
        self.token, self.expires = None, 0
        self.lock = RLock()

    def access_token(self):
        with self.lock:
            if not self.token or time.monotonic() >= self.expires:
                response = self.client.post(
                    "https://api.ebay.com/identity/v1/oauth2/token",
                    auth=(self.settings.ebay_client_id, self.settings.ebay_client_secret),
                    data={
                        "grant_type": "client_credentials",
                        "scope": "https://api.ebay.com/oauth/api_scope",
                    },
                )
                response.raise_for_status()
                self.token = response.json()["access_token"]
                self.expires = time.monotonic() + max(
                    0, response.json().get("expires_in", 7200) - 60
                )
            return self.token

    def search(self, garment):
        response = self.client.get(
            "https://api.ebay.com/buy/browse/v1/item_summary/search",
            headers={
                "Authorization": "Bearer " + self.access_token(),
                "X-EBAY-C-MARKETPLACE-ID": "EBAY_DE",
            },
            params={
                "q": search_query(garment),
                "limit": "12",
                "filter": "priceCurrency:EUR,buyingOptions:{FIXED_PRICE}",
                "sort": "price",
            },
        )
        response.raise_for_status()
        results = []
        for row in response.json().get("itemSummaries", [])[:12]:
            try:
                if (
                    not valid_listing(self.name, row["itemWebUrl"])
                    or row["price"]["currency"] != "EUR"
                ):
                    continue
                shipping = [
                    float(option["shippingCost"]["value"])
                    for option in row.get("shippingOptions", [])
                    if option.get("shippingCost", {}).get("currency") == "EUR"
                ]
                aspects = {
                    item["name"].casefold(): item["value"]
                    for item in row.get("localizedAspects", [])
                }
                results.append(
                    Offer(
                        id="ebay:" + row["itemId"] + ":" + garment.id,
                        garment_id=garment.id,
                        source=self.name,
                        external_id=row["itemId"],
                        title=row["title"],
                        url=row["itemWebUrl"],
                        price=float(row["price"]["value"]),
                        shipping=min(shipping) if shipping else None,
                        image=row.get("image", {}).get("imageUrl"),
                        size=aspects.get("größe") or aspects.get("size"),
                        condition=row.get("condition", "Unknown"),
                        location=row.get("itemLocation", {}).get("country", ""),
                        retrieved_at=now(),
                    )
                )
            except (KeyError, ValueError, TypeError):
                continue
        return results


class OptionalSource:
    """Isolate unofficial clients so parent-enforced timeouts cannot be ignored."""

    def __init__(self, name, settings):
        self.name, self.settings = name, settings

    def search(self, garment):
        response = subprocess.run(
            [sys.executable, "-m", "stylemax.source_worker", self.name],
            input=garment.model_dump_json(),
            text=True,
            capture_output=True,
            timeout=self.settings.marketplace_timeout + 5,
            check=True,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        results = []
        for row in json.loads(response.stdout)[:12]:
            try:
                if valid_listing(self.name, row["url"]):
                    results.append(
                        Offer(
                            **row,
                            garment_id=garment.id,
                            source=self.name,
                            id=f"{self.name}:{row['external_id']}:{garment.id}",
                            retrieved_at=now(),
                        )
                    )
            except (ValueError, TypeError, KeyError):
                continue
        return results


def configured_sources(settings):
    sources = []
    if settings.ebay_client_id and settings.ebay_client_secret:
        sources.append(EbaySource(settings))
    for name in ("kleinanzeigen", "vinted"):
        if getattr(settings, "enable_" + name):
            sources.append(OptionalSource(name, settings))
    return sources


class MarketplaceSearch:
    def __init__(self, settings, sources=None):
        self.sources = configured_sources(settings) if sources is None else sources
        self.cache, self.lock = {}, RLock()

    def cached_search(self, source, garment):
        key = (source.name, search_query(garment))
        with self.lock:
            cached = self.cache.get(key)
            if cached and time.monotonic() - cached[0] < 300:
                return [
                    item.model_copy(
                        update={
                            "garment_id": garment.id,
                            "id": f"{source.name}:{item.external_id}:{garment.id}",
                        }
                    )
                    for item in cached[1]
                ]
        results = source.search(garment)
        with self.lock:
            if len(self.cache) >= 256:
                self.cache.pop(next(iter(self.cache)))
            self.cache[key] = (time.monotonic(), results)
        return results

    def run(self, project):
        garments = [Garment.model_validate(item) for item in project["garments"]]
        statuses, offers = [], []
        if project["demo"]:
            statuses = [
                {
                    "source": source,
                    "status": "demo",
                    "message": "Demo — use search links to explore real offers",
                }
                for source in HOSTS
            ]
        else:

            def collect(source):
                rows, errors, deadline = [], 0, time.monotonic() + 90
                for garment in garments:
                    if time.monotonic() > deadline:
                        errors += 1
                        break
                    try:
                        rows.extend(rank_offers(garment, self.cached_search(source, garment)))
                    except Exception as error:
                        errors += 1
                        log.warning("Marketplace %s failed: %s", source.name, type(error).__name__)
                        # Stop a blocked source rather than repeat the same failed request.
                        break
                status = "partial" if errors and rows else "error" if errors else "connected"
                return rows, {
                    "source": source.name,
                    "status": status,
                    "message": "Source unavailable; use search links"
                    if errors
                    else f"{len(rows)} size-compatible candidates",
                }

            with ThreadPoolExecutor(max_workers=3) as pool:
                for rows, status in pool.map(collect, self.sources):
                    offers.extend(rows)
                    statuses.append(status)
            for source in HOSTS:
                if source not in {item["source"] for item in statuses}:
                    statuses.append(
                        {
                            "source": source,
                            "status": "not_configured",
                            "message": "Not connected — search links available",
                        }
                    )
        unique = {}
        for offer in offers:
            unique[(offer.source, offer.external_id, offer.garment_id)] = offer
        offers = sorted(unique.values(), key=lambda item: -item.score)
        return {
            "offers": [item.model_dump() for item in offers],
            "sources": statuses,
            "search_links": search_links(garments),
            "basket": choose_basket(offers, project["budget"], [item.id for item in garments]),
        }
