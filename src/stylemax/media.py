import io
import warnings
from uuid import uuid4

from fastapi import HTTPException
from PIL import Image, ImageOps, UnidentifiedImageError

Image.MAX_IMAGE_PIXELS = 25_000_000


def normalize_image(content: bytes, max_bytes: int = 10 * 1024 * 1024) -> bytes:
    if not content or len(content) > max_bytes:
        raise HTTPException(422, "Each photo must be under 10 MB")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(content)) as image:
                if image.format not in ("JPEG", "PNG", "WEBP"):
                    raise ValueError("Unsupported format")
                image.load()
                normalized = ImageOps.exif_transpose(image).convert("RGB")
                normalized.thumbnail((1600, 2000))
                output = io.BytesIO()
                normalized.save(output, "JPEG", quality=90)
                return output.getvalue()
    except (
        UnidentifiedImageError,
        ValueError,
        OSError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ):
        raise HTTPException(
            422, "Upload valid JPEG, PNG or WebP photos under 25 megapixels"
        ) from None


def save_image(settings, project_id, content):
    directory = settings.data_dir / "media" / project_id
    directory.mkdir(parents=True, exist_ok=True)
    name = f"{uuid4().hex}.jpg"
    (directory / name).write_bytes(normalize_image(content))
    return f"/api/projects/{project_id}/media/{name}"


def image_path(settings, url):
    parts = url.split("/")
    return settings.data_dir / "media" / parts[3] / parts[-1]
