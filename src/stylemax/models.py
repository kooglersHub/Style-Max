from typing import Literal

from pydantic import BaseModel, Field, model_validator


class Brief(BaseModel):
    vibe: str = Field(min_length=3, max_length=1200)
    budget: float = Field(default=180, ge=20, le=10000)
    demo: bool = False


class Sizes(BaseModel):
    tops: str = Field(min_length=1, max_length=20)
    outerwear: str = Field(min_length=1, max_length=20)
    bottoms: str = Field(min_length=1, max_length=30)
    shoes: str = Field(min_length=1, max_length=20)
    fit: Literal["relaxed", "regular", "slim"] = "relaxed"
    category: Literal["menswear", "womenswear", "all"] = "all"


class Garment(BaseModel):
    id: str = Field(min_length=1, max_length=80, pattern=r"^[a-zA-Z0-9_-]+$")
    name: str = Field(min_length=2, max_length=120)
    category: Literal["tops", "outerwear", "bottoms", "shoes", "accessories"]
    color: str = Field(min_length=1, max_length=50)
    keywords: str = Field(min_length=2, max_length=200)
    size: str = Field(default="", max_length=30)
    budget: float = Field(default=40, ge=1, le=10000)
    look_ids: list[str] = Field(default_factory=list, max_length=10)


class Look(BaseModel):
    id: str = Field(pattern=r"^look-([1-9]|10)$")
    title: str = Field(min_length=2, max_length=80)
    description: str = Field(min_length=5, max_length=500)
    prompt: str = Field(min_length=10, max_length=2400)
    palette: list[str] = Field(min_length=3, max_length=5)
    garments: list[Garment] = Field(min_length=2, max_length=6)
    status: Literal["queued", "running", "completed", "failed"] = "queued"
    image: str | None = None
    error: str | None = None


class LookPlan(BaseModel):
    looks: list[Look] = Field(min_length=10, max_length=10)

    @model_validator(mode="after")
    def distinct_looks(self):
        if len({look.id for look in self.looks}) != 10:
            raise ValueError("Ten unique look IDs are required")
        if len({look.title.casefold() for look in self.looks}) != 10:
            raise ValueError("Ten distinct outfit titles are required")
        return self


class Selection(BaseModel):
    look_ids: list[str] = Field(min_length=1, max_length=10)


class ShoppingUpdate(BaseModel):
    sizes: Sizes
    garments: list[Garment] | None = Field(default=None, max_length=30)
    budget: float | None = Field(default=None, ge=20, le=10000)


class PreviewRequest(BaseModel):
    offer_ids: list[str] = Field(default_factory=list, max_length=30)


class Offer(BaseModel):
    id: str
    garment_id: str
    source: str
    external_id: str
    url: str
    title: str
    price: float = Field(ge=0, allow_inf_nan=False)
    currency: Literal["EUR"] = "EUR"
    shipping: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    image: str | None = None
    size: str | None = None
    condition: str = "Unknown"
    location: str = ""
    retrieved_at: str = ""
    score: float = 0
    reasons: list[str] = Field(default_factory=list)
    size_status: str = "unknown"
    total: float | None = None
