import re


def normalized_size(value):
    return re.sub(r"[^a-z0-9]", "", value.casefold().replace("eu", ""))


def size_evidence(requested, offer):
    requested = normalized_size(requested)
    if offer.size:
        text = offer.size.upper()
        if normalized_size(text) == requested:
            return "match"
        letters = set(re.findall(r"(?<!\w)(?:XXXL|XXL|XL|XS|XXS|S|M|L)(?!\w)", text))
        if requested.upper() in letters:
            return "match" if len(letters) == 1 else "unknown"
        if requested in {"xxs", "xs", "s", "m", "l", "xl", "xxl", "xxxl"} and letters:
            return "mismatch"
        # Mixed regional numeric labels and ranges need seller confirmation.
        if re.fullmatch(r"\d+(?:[.,]\d+)?", text.strip()):
            return "mismatch" if requested.isdigit() else "unknown"
        return "unknown"
    tokens = re.findall(r"(?<!\w)(?:XXXL|XXL|XL|XS|XXS|S|M|L)(?!\w)", offer.title.upper())
    if requested in {"xxs", "xs", "s", "m", "l", "xl", "xxl", "xxxl"} and tokens:
        return "match" if requested in [x.lower() for x in tokens] else "mismatch"
    # Numeric sizes require an explicit size field; a title number may be a model or year.
    return "unknown"


def rank_offers(garment, offers):
    result = []
    terms = set(re.findall(r"\w+", garment.keywords.casefold()))
    for original in offers:
        item = original.model_copy(deep=True)
        item.size_status = size_evidence(garment.size, item)
        if item.size_status == "mismatch":
            continue
        item.total = round(item.price + item.shipping, 2) if item.shipping is not None else None
        words = set(re.findall(r"\w+", item.title.casefold()))
        relevance = len(terms & words) / max(1, len(terms))
        cost = item.total if item.total is not None else item.price
        item.score = round(
            relevance * 45
            + (30 if item.size_status == "match" else 0)
            + (15 if cost <= garment.budget else 0)
            + (10 if item.shipping is not None else 0),
            1,
        )
        item.reasons = [
            "Size matches listing" if item.size_status == "match" else "Confirm size with seller"
        ]
        item.reasons.append(
            "Shipping included in total" if item.shipping is not None else "Shipping not provided"
        )
        item.reasons.append("Within item budget" if cost <= garment.budget else "Above item budget")
        if relevance > 0:
            item.reasons.append("Matches your search terms")
        result.append(item)
    return sorted(
        result,
        key=lambda item: (-item.score, item.total if item.total is not None else float("inf")),
    )


def choose_basket(offers, budget, garment_ids=None):
    groups = {key: [] for key in (garment_ids or dict.fromkeys(item.garment_id for item in offers))}
    for item in offers:
        if (
            item.garment_id in groups
            and item.shipping is not None
            and item.size_status != "mismatch"
        ):
            groups[item.garment_id].append(item)
    # Lowest known delivered cost reserves enough budget for the remaining garments.
    chosen, unmatched, total, used = [], [], 0.0, set()
    for garment_id, candidates in groups.items():
        candidates.sort(key=lambda item: (item.price + item.shipping, -item.score))
        candidates = [item for item in candidates if (item.source, item.external_id) not in used]
        if candidates and total + candidates[0].price + candidates[0].shipping <= budget:
            selected = candidates[0]
            chosen.append(selected.id)
            used.add((selected.source, selected.external_id))
            total += selected.price + selected.shipping
        else:
            unmatched.append(garment_id)
    return {
        "offer_ids": chosen,
        "known_total": round(total, 2),
        "unmatched": unmatched,
        "complete": not unmatched and bool(chosen),
        "sizes_confirmed": all(item.size_status == "match" for item in offers if item.id in chosen),
    }
