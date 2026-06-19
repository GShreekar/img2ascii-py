import io
from pathlib import Path
from typing import Union
import numpy as np
from PIL import Image, ImageOps
from img2ascii.exceptions import ImageTooLargeError, UnsupportedImageError

MAX_PIXELS_DEFAULT = 50_000_000

def load_image(source: Union[str, Path, bytes, bytearray, Image.Image], max_pixels: int = MAX_PIXELS_DEFAULT) -> np.ndarray:
    """ Load image from file or bytes and return as RGBA NumPy array
    Args:
        source: The image source (file path, bytes, or PIL Image)
        max_pixels: The maximum number of pixels allowed
    Returns:
        np.ndarray: The RGBA image array
    """
    img = None
    try:
        if isinstance(source, Image.Image):
            img = source.copy()
        elif isinstance(source, (str, Path)):
            img = Image.open(source)
        elif isinstance(source, (bytes, bytearray)):
            img = Image.open(io.BytesIO(source))
        elif hasattr(source, "read"):
            img = Image.open(source)
        else:
            raise UnsupportedImageError(f"Unsupported image type: {type(source)}")
        
        width, height = img.size
        if width * height > max_pixels:
            raise ImageTooLargeError(f"Image exceeds {max_pixels} pixels.")
        
        img = ImageOps.exif_transpose(img)
        if img.mode != "RGBA":
            img = img.convert("RGBA")
        
        return np.array(img).astype(np.uint8)
    except UnsupportedImageError:
        raise
    except ImageTooLargeError:
        raise
    except Exception as e:
        raise UnsupportedImageError(f"Error loading image: {e}") from e