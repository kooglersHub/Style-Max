from .models import Garment, Look

STYLES = [
    (
        "The everyday edit",
        "Easy layers. Earthy tones. Nothing trying too hard.",
        ["#7b826b", "#e8dfce", "#333b38"],
        "Olive overshirt",
        "Ecru cotton tee",
        "Charcoal straight trousers",
        "White leather sneakers",
    ),
    (
        "Soft tailoring",
        "A little structure, with room to breathe.",
        ["#c3b59a", "#f0e9dc", "#544e44"],
        "Sand unstructured blazer",
        "Cream knit polo",
        "Brown pleated trousers",
        "Brown suede loafers",
    ),
    (
        "Off-duty blue",
        "Worn-in denim meets clean, quiet essentials.",
        ["#506b7c", "#e8e4da", "#293c49"],
        "Indigo denim jacket",
        "White cotton tee",
        "Navy relaxed jeans",
        "Canvas sneakers",
    ),
    (
        "A slower Sunday",
        "Soft textures for the days with no agenda.",
        ["#a9977e", "#f1e8d8", "#716f62"],
        "Taupe cardigan",
        "Oatmeal cotton tee",
        "Olive wide trousers",
        "Suede clogs",
    ),
    (
        "After hours",
        "Deep tones and a sharper silhouette.",
        ["#353936", "#171e1b", "#777e72"],
        "Black chore jacket",
        "Black knit tee",
        "Charcoal tailored trousers",
        "Black derby shoes",
    ),
    (
        "City explorer",
        "Practical pieces with an outdoors point of view.",
        ["#7d8569", "#b7a085", "#333f39"],
        "Olive field jacket",
        "Sand pocket tee",
        "Dark green cargo trousers",
        "Trail sneakers",
    ),
    (
        "Coffee in Copenhagen",
        "Scandinavian simplicity with a playful stripe.",
        ["#a3a4a0", "#e7e4d9", "#3d4b57"],
        "Grey wool overshirt",
        "Navy striped long sleeve",
        "Cream straight trousers",
        "Grey retro sneakers",
    ),
    (
        "Vintage state of mind",
        "Old favorites, rediscovered in warm shades.",
        ["#9e6c4c", "#d8c7a7", "#4e5849"],
        "Brown corduroy jacket",
        "Cream vintage shirt",
        "Olive straight jeans",
        "Brown leather boots",
    ),
    (
        "Less, but better",
        "A thoughtful palette. A really good silhouette.",
        ["#d0c9b8", "#f6f2e9", "#535950"],
        "Stone linen overshirt",
        "White heavyweight tee",
        "Dark grey wool trousers",
        "Minimal white sneakers",
    ),
    (
        "Weekend somewhere",
        "Sun-faded colors and an easy getaway feel.",
        ["#bfa689", "#e8ddcb", "#7c8a8a"],
        "Sand linen shirt",
        "Cream tank top",
        "Blue linen trousers",
        "Leather sandals",
    ),
]


def demo_looks():
    looks = []
    for index, (title, description, palette, *names) in enumerate(STYLES, 1):
        look_id = f"look-{index}"
        garments = [
            Garment(
                id=f"{look_id}-{category}",
                name=name,
                category=category,
                color=palette[position % 3],
                keywords=name,
                look_ids=[look_id],
            )
            for position, (category, name) in enumerate(
                zip(["outerwear", "tops", "bottoms", "shoes"], names, strict=True)
            )
        ]
        looks.append(
            Look(
                id=look_id,
                title=title,
                description=description,
                prompt=description,
                palette=palette,
                garments=garments,
                status="completed",
            ).model_dump()
        )
    return looks


def build_shopping_list(project, sizes):
    unique = {}
    for look in project["looks"]:
        if look["id"] not in project["selected"]:
            continue
        for garment in look["garments"]:
            key = (garment["name"].casefold(), garment["category"])
            if key in unique:
                unique[key]["look_ids"].append(look["id"])
                continue
            item = dict(garment)
            item["look_ids"] = [look["id"]]
            item["size"] = sizes.get(item["category"], "One size")
            item["fit"] = sizes.get("fit", "regular")
            item["audience"] = sizes.get("category", "all")
            unique[key] = item
    garments = list(unique.values())
    weights = {"outerwear": 1.4, "tops": 0.6, "bottoms": 1, "shoes": 1.3, "accessories": 0.4}
    total = sum(weights[item["category"]] for item in garments)
    for item in garments:
        item["budget"] = round(project["budget"] * weights[item["category"]] / total, 2)
    return garments
