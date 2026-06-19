import io
import pytest
import numpy as np
from PIL import Image
from img2ascii.core.loader import load_image
from img2ascii.exceptions import ImageTooLargeError, UnsupportedImageError

def test_load_pillow_image():
    # Create an RGB image
    img = Image.new("RGB", (10, 20), color=(255, 0, 0))
    arr = load_image(img)
    # Check shape is (height, width, channels)
    assert arr.shape == (20, 10, 4)
    # Check alpha is 255
    assert np.all(arr[:, :, 3] == 255)
    # Check RGB values
    assert np.all(arr[:, :, 0] == 255)
    assert np.all(arr[:, :, 1] == 0)
    assert np.all(arr[:, :, 2] == 0)

def test_load_bytes():
    # Create an image and save to bytes
    img = Image.new("RGBA", (5, 5), color=(0, 255, 0, 128))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    png_bytes = buf.getvalue()

    arr = load_image(png_bytes)
    assert arr.shape == (5, 5, 4)
    assert np.all(arr[:, :, 1] == 255)
    assert np.all(arr[:, :, 3] == 128)

def test_image_too_large():
    img = Image.new("RGB", (100, 100)) # 10000 pixels
    with pytest.raises(ImageTooLargeError):
        load_image(img, max_pixels=5000)

def test_unsupported_source_type():
    with pytest.raises(UnsupportedImageError):
        load_image(12345) # type: ignore

def test_corrupt_bytes():
    with pytest.raises(UnsupportedImageError):
        load_image(b"invalid image bytes header")
