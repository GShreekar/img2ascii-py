import numpy as np
from PIL import Image
from img2ascii.api import convert_to_ascii, AsciiConfig, convert_to_pixels, PixelConfig
from img2ascii.exceptions import ImageTooLargeError
import pytest

def test_convert_to_ascii_pillow_image():
    # 10x10 white image
    img = Image.new("RGB", (10, 10), color=(255, 255, 255))
    
    # 4 columns, char aspect 2.0. Expected height:
    # row_count = round(4 * 10 / (10 * 2.0)) = 2 rows
    config = AsciiConfig(width=4, char_aspect=2.0, charset="standard")
    
    result = convert_to_ascii(img, config)
    lines = result.splitlines()
    assert len(lines) == 2
    assert all(len(line) == 4 for line in lines)
    # White image -> luma = 255 -> standard charset ramp " .:-=+*#%@" -> maps to "@"
    assert lines[0] == "@@@@"
    assert lines[1] == "@@@@"

def test_convert_to_ascii_invert():
    img = Image.new("RGB", (10, 10), color=(255, 255, 255))
    config = AsciiConfig(width=4, char_aspect=2.0, charset="standard", invert=True)
    result = convert_to_ascii(img, config)
    lines = result.splitlines()
    # Inverted standard charset ramp ends with space " " instead of "@" for max luma
    assert lines[0] == "    "

def test_convert_to_ascii_default_config():
    img = Image.new("RGB", (100, 100), color=(0, 0, 0))
    result = convert_to_ascii(img) # defaults to 80 columns
    lines = result.splitlines()
    assert len(lines) > 0
    assert len(lines[0]) == 80

def test_convert_to_pixels():
    img = Image.new("RGB", (10, 10), color=(255, 0, 0))
    config = PixelConfig(width=5, char_aspect=1.0)
    html = convert_to_pixels(img, config)
    
    assert "<!DOCTYPE html>" in html
    assert ".c_ff0000" in html

def test_convert_to_pixels_default_config():
    img = Image.new("RGB", (20, 20), color=(0, 255, 0))
    html = convert_to_pixels(img)
    assert "<!DOCTYPE html>" in html
    assert ".c_00ff00" in html

from unittest.mock import patch

def test_convert_to_pixels_too_large():
    img = Image.new("RGB", (1000, 1000), color=(0, 0, 0))
    config = PixelConfig(width=5000, height=5000)
    with pytest.raises(ImageTooLargeError):
        convert_to_pixels(img, config)
    
    # Check that allow_large overrides the limit and bypasses the check
    config_large = PixelConfig(width=5000, height=5000, allow_large=True)
    with patch("img2ascii.api.sample_grid") as mock_sample:
        mock_sample.return_value = (np.zeros((2, 2, 3)), np.zeros((2, 2)), np.ones((2, 2)))
        html = convert_to_pixels(img, config_large)
        assert "<html" in html


