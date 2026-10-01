from __future__ import annotations

import io
from pathlib import Path
from typing import IO, Union

import numpy as np
from PIL import Image, ImageOps

from img2ascii.exceptions import ImageTooLargeError, UnsupportedImageError

MAX_PIXELS_DEFAULT = 50_000_000


def load_image(
    source: Union[str, Path, bytes, bytearray, IO[bytes], Image.Image],
    max_pixels: int = MAX_PIXELS_DEFAULT,
) -> np.ndarray:
    """Load image from file or bytes and return as RGBA NumPy array
    Args:
        source: The image source (file path, bytes, or PIL Image)
        max_pixels: The maximum number of pixels allowed
    Returns:
        np.ndarray: The RGBA image array
    """
    try:
        if isinstance(source, Image.Image):
            return _to_rgba_array(source, max_pixels)
        if isinstance(source, (str, Path)):
            # Pillow owns the file handle it opened, so it is closed here.
            with Image.open(source) as img:
                return _to_rgba_array(img, max_pixels)
        if isinstance(source, (bytes, bytearray)):
            with Image.open(io.BytesIO(source)) as img:
                return _to_rgba_array(img, max_pixels)
        if hasattr(source, "read"):
            # The caller owns the stream, so it is left open for them to close.
            return _to_rgba_array(Image.open(source), max_pixels)
        raise UnsupportedImageError(f"Unsupported image type: {type(source)}")
    except (UnsupportedImageError, ImageTooLargeError):
        raise
    except Exception as e:
        raise UnsupportedImageError(f"Error loading image: {e}") from e


def _to_rgba_array(img: Image.Image, max_pixels: int) -> np.ndarray:
    width, height = img.size
    if width * height > max_pixels:
        raise ImageTooLargeError(f"Image exceeds {max_pixels} pixels.")

    transposed = ImageOps.exif_transpose(img) or img
    if transposed.mode != "RGBA":
        transposed = transposed.convert("RGBA")

    return np.array(transposed, dtype=np.uint8)
