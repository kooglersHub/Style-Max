import ipaddress
import math
import socket
from io import BytesIO
from urllib.parse import urlsplit

import httpx
from PIL import Image, ImageOps

from .media import normalize_image

IMAGE_HOSTS = ("ebayimg.com", "vinted.net", "kleinanzeigen.de", "kleinanzeigen.com")


def public_image_url(url):
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Only public HTTPS image URLs are supported")
    if parsed.port not in (None, 443):
        raise ValueError("Unsupported image port")
    addresses = socket.getaddrinfo(parsed.hostname, 443, type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(value[4][0]).is_global for value in addresses):
        raise ValueError("Private-network image URL rejected")
    return url


def fetch_product_image(url):
    host = urlsplit(url).hostname or ""
    if not any(host == suffix or host.endswith("." + suffix) for suffix in IMAGE_HOSTS):
        raise ValueError("Unrecognized marketplace image host")
    public_image_url(url)
    with httpx.stream("GET", url, timeout=10, follow_redirects=False) as response:
        response.raise_for_status()
        if response.is_redirect or not response.headers.get("content-type", "").startswith(
            "image/"
        ):
            raise ValueError("Invalid image response")
        content = bytearray()
        for chunk in response.iter_bytes():
            content.extend(chunk)
            if len(content) > 5 * 1024 * 1024:
                raise ValueError("Product image too large")
    return normalize_image(bytes(content))


def product_collage(images):
    if not images:
        return None
    columns = min(5, math.ceil(math.sqrt(len(images))))
    rows = math.ceil(len(images) / columns)
    canvas = Image.new("RGB", (columns * 320, rows * 320), "#f4f2ea")
    for index, content in enumerate(images):
        with Image.open(BytesIO(content)) as image:
            tile = ImageOps.contain(image.convert("RGB"), (300, 300))
            canvas.paste(
                tile,
                (
                    (index % columns) * 320 + (320 - tile.width) // 2,
                    (index // columns) * 320 + (320 - tile.height) // 2,
                ),
            )
    output = BytesIO()
    canvas.save(output, "JPEG", quality=88)
    return output.getvalue()
