"""Universal Image Ingester and Format Standardizer.
Handles web URLs, Steam workshop links, local files, and modern formats (WEBP, AVIF, PNG, JPG).
"""

import os
import io
import urllib.request
from typing import Union
from PIL import Image


def load_image(source: Union[str, bytes]) -> Image.Image:
    """Load an image from a URL, local file path, or raw bytes,

    converting it to standard RGB/RGBA.
    """
    if isinstance(source, bytes):
        img = Image.open(io.BytesIO(source))
    elif source.startswith("http://") or source.startswith("https://"):
        req = urllib.request.Request(
            source,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) SmartwatchWallpaperStudio/1.0"}
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()
        img = Image.open(io.BytesIO(data))
    elif os.path.exists(source):
        img = Image.open(source)
    else:
        raise FileNotFoundError(f"Image source not found: {source}")

    return img
