import io

import numpy as np
import pytest
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
    img = Image.new("RGB", (100, 100))  # 10000 pixels
    with pytest.raises(ImageTooLargeError):
        load_image(img, max_pixels=5000)


def test_unsupported_source_type():
    with pytest.raises(UnsupportedImageError):
        load_image(12345)  # type: ignore


def test_corrupt_bytes():
    with pytest.raises(UnsupportedImageError):
        load_image(b"invalid image bytes header")


def test_file_like_object():
    img = Image.new("RGBA", (5, 5), color=(0, 255, 0, 128))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    arr = load_image(buf)
    assert arr.shape == (5, 5, 4)
    assert np.all(arr[:, :, 1] == 255)


def test_path_input_closes_the_file_handle(tmp_path, monkeypatch):
    """Pillow used to be left holding the handle, raising ResourceWarning on GC."""
    # GIF keeps its handle open for frame seeking, so it exposes the leak.
    img_path = tmp_path / "leak.gif"
    Image.new("P", (8, 8), color=3).save(img_path)

    handles = []
    real_open = Image.open

    def spy(*args, **kwargs):
        img = real_open(*args, **kwargs)
        # Captured now, because Pillow drops the attribute during load() without
        # necessarily closing the underlying file.
        handles.append(img.fp)
        return img

    monkeypatch.setattr("img2ascii.core.loader.Image.open", spy)
    assert load_image(img_path).shape == (8, 8, 4)

    assert handles, "Image.open was never called"
    for fp in handles:
        assert fp.closed, "the file handle opened by Pillow was never closed"


def test_file_like_input_is_left_open_for_the_caller():
    img = Image.new("RGBA", (4, 4), color=(9, 9, 9, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    load_image(buf)
    # The caller owns the stream, so it must still be usable afterwards.
    assert not buf.closed
    buf.seek(0)
    assert load_image(buf).shape == (4, 4, 4)


def test_returned_array_is_writable_and_independent():
    source = Image.new("RGB", (4, 4), color=(10, 20, 30))
    arr = load_image(source)
    arr[0, 0, 0] = 200
    assert np.array(source)[0, 0, 0] == 10
