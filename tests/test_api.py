import numpy as np
from PIL import Image
from unittest.mock import patch
from img2ascii.api import (
    convert_to_ascii,
    AsciiConfig,
    convert_to_pixels,
    PixelConfig,
    convert_to_svg,
    convert_to_html,
    HtmlConfig,
)
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
    result = convert_to_ascii(img)  # defaults to 80 columns
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


def test_convert_to_pixels_too_large():
    img = Image.new("RGB", (1000, 1000), color=(0, 0, 0))
    config = PixelConfig(width=5000, height=5000)
    with pytest.raises(ImageTooLargeError):
        convert_to_pixels(img, config)

    # Check that allow_large overrides the limit and bypasses the check
    config_large = PixelConfig(width=5000, height=5000, allow_large=True)
    with patch("img2ascii.api.sample_grid") as mock_sample:
        mock_sample.return_value = (
            np.zeros((2, 2, 3)),
            np.zeros((2, 2)),
            np.ones((2, 2)),
        )
        html = convert_to_pixels(img, config_large)
        assert "<html" in html


def test_convert_to_pixels_aspect_mode_css():
    img = Image.new("RGB", (10, 20), color=(255, 0, 0))

    # Under aspect_mode="css", char_aspect is ignored during sampling (treated as 1.0)
    config = PixelConfig(width=10, aspect_mode="css", char_aspect=2.0)
    html = convert_to_pixels(img, config)
    assert "line-height: 0.5;" in html

    # Under aspect_mode="resize", char_aspect=2.0 is used during sampling
    config_resize = PixelConfig(width=10, aspect_mode="resize", char_aspect=2.0)
    html_resize = convert_to_pixels(img, config_resize)
    assert "line-height: 1.0;" in html_resize


def test_convert_to_pixels_aspect_mode_invalid():
    img = Image.new("RGB", (10, 10), color=(255, 0, 0))
    config = PixelConfig(aspect_mode="invalid")
    with pytest.raises(ValueError, match="Invalid aspect_mode"):
        convert_to_pixels(img, config)


def test_convert_to_pixels_palette_size():
    img = Image.new("RGB", (10, 1), color=(0, 0, 0))
    # Put 10 distinct colors in the image
    for x in range(10):
        img.putpixel((x, 0), (x * 20, x * 20, x * 20))

    # Without palette quantization, we should have 10 colors
    config_no_quant = PixelConfig(width=10)
    html_no_quant = convert_to_pixels(img, config_no_quant)

    # With palette quantization (e.g. 3 colors)
    config_quant = PixelConfig(width=10, palette_size=3)
    html_quant = convert_to_pixels(img, config_quant)

    import re

    classes_no_quant = set(re.findall(r"\.c_[0-9a-fA-F]{6}", html_no_quant))
    classes_quant = set(re.findall(r"\.c_[0-9a-fA-F]{6}", html_quant))

    assert len(classes_no_quant) == 10
    assert len(classes_quant) <= 3

    # Also test SVG palette quantization
    svg_quant = convert_to_svg(img, config_quant)
    fills_quant = set(re.findall(r'fill="#[0-9a-fA-F]{6}"', svg_quant))
    assert len(fills_quant) <= 4


def test_convert_to_pixels_palette_size_invalid():
    img = Image.new("RGB", (10, 10), color=(255, 0, 0))
    with pytest.raises(ValueError, match="palette_size must be between 2 and 256"):
        convert_to_pixels(img, PixelConfig(palette_size=1))
    with pytest.raises(ValueError, match="palette_size must be between 2 and 256"):
        convert_to_pixels(img, PixelConfig(palette_size=300))
    with pytest.raises(ValueError, match="palette_size must be between 2 and 256"):
        convert_to_svg(img, PixelConfig(palette_size=1))
    with pytest.raises(ValueError, match="palette_size must be between 2 and 256"):
        convert_to_svg(img, PixelConfig(palette_size=300))


def test_convert_to_html_basic():
    # Test convert_to_html with default config
    img = Image.new("RGB", (10, 10), color=(255, 255, 255))
    html = convert_to_html(img)

    assert "<!DOCTYPE html>" in html
    assert ".c_ffffff" in html
    assert "@@@@" in html  # white/full luma maps to "@" in standard ramp


def test_convert_to_html_custom_config():
    img = Image.new("RGB", (10, 10), color=(128, 128, 128))
    config = HtmlConfig(
        width=5,
        char_aspect=1.5,
        charset="standard",
        invert=True,
        bg_color="#ffffff",
        aspect_mode="resize",
        fast=False,
        edges=False,
    )
    html = convert_to_html(img, config)
    assert "<!DOCTYPE html>" in html
    assert "background-color: #ffffff" in html


def test_convert_to_html_aspect_mode_css():
    img = Image.new("RGB", (10, 20), color=(255, 0, 0))

    # Under aspect_mode="css", char_aspect is ignored during sampling (treated as 1.0)
    config = HtmlConfig(width=10, aspect_mode="css", char_aspect=2.0)
    html = convert_to_html(img, config)
    assert "line-height: 0.5;" in html

    # Under aspect_mode="resize", char_aspect=2.0 is used during sampling
    config_resize = HtmlConfig(width=10, aspect_mode="resize", char_aspect=2.0)
    html_resize = convert_to_html(img, config_resize)
    assert "line-height: 1.0;" in html_resize


def test_convert_to_html_aspect_mode_invalid():
    img = Image.new("RGB", (10, 10), color=(255, 0, 0))
    config = HtmlConfig(aspect_mode="invalid")
    with pytest.raises(ValueError, match="Invalid aspect_mode"):
        convert_to_html(img, config)


def test_convert_to_html_too_large():
    img = Image.new("RGB", (1000, 1000), color=(0, 0, 0))
    config = HtmlConfig(width=5000, height=5000)
    with pytest.raises(ImageTooLargeError):
        convert_to_html(img, config)

    # Check that allow_large overrides the limit and bypasses the check
    config_large = HtmlConfig(width=5000, height=5000, allow_large=True)
    with patch("img2ascii.api.sample_grid") as mock_sample:
        mock_sample.return_value = (
            np.zeros((2, 2, 3)),
            np.zeros((2, 2)),
            np.ones((2, 2)),
        )
        html = convert_to_html(img, config_large)
        assert "<html" in html


def test_convert_to_html_palette_size():
    img = Image.new("RGB", (10, 1), color=(0, 0, 0))
    # Put 10 distinct colors in the image
    for x in range(10):
        img.putpixel((x, 0), (x * 20, x * 20, x * 20))

    # Without palette quantization, we should have 10 colors
    html_no_quant = convert_to_html(img, HtmlConfig(width=10))

    # With palette quantization (e.g. 3 colors)
    html_quant = convert_to_html(img, HtmlConfig(width=10, palette_size=3))

    import re

    classes_no_quant = set(re.findall(r"\.c_[0-9a-fA-F]{6}", html_no_quant))
    classes_quant = set(re.findall(r"\.c_[0-9a-fA-F]{6}", html_quant))

    assert len(classes_no_quant) == 10
    assert len(classes_quant) <= 3


def test_convert_to_html_palette_size_invalid():
    img = Image.new("RGB", (10, 10), color=(255, 0, 0))
    with pytest.raises(ValueError, match="palette_size must be between 2 and 256"):
        convert_to_html(img, HtmlConfig(palette_size=1))
    with pytest.raises(ValueError, match="palette_size must be between 2 and 256"):
        convert_to_html(img, HtmlConfig(palette_size=300))


def test_luma_method_selection():
    img = Image.new("RGB", (10, 10), color=(0, 255, 0))
    config_601 = AsciiConfig(width=5, charset="standard", luma_method="bt601")
    config_709 = AsciiConfig(width=5, charset="standard", luma_method="bt709")

    res_601 = convert_to_ascii(img, config_601)
    res_709 = convert_to_ascii(img, config_709)

    assert len(res_601) > 0
    assert len(res_709) > 0

    with pytest.raises(ValueError, match="Invalid luma_method"):
        convert_to_ascii(img, AsciiConfig(luma_method="invalid"))

    with pytest.raises(ValueError, match="Invalid luma_method"):
        convert_to_pixels(img, PixelConfig(luma_method="invalid"))

    with pytest.raises(ValueError, match="Invalid luma_method"):
        convert_to_svg(img, PixelConfig(luma_method="invalid"))

    with pytest.raises(ValueError, match="Invalid luma_method"):
        convert_to_html(img, HtmlConfig(luma_method="invalid"))


def test_dithering_ascii():
    img = Image.new("RGB", (20, 20))
    for x in range(20):
        for y in range(20):
            val = int((x / 19) * 255)
            img.putpixel((x, y), (val, val, val))

    config_no_dither = AsciiConfig(width=20, charset="standard", dither=False)
    config_dither = AsciiConfig(width=20, charset="standard", dither=True)

    ascii_no_dither = convert_to_ascii(img, config_no_dither)
    ascii_dither = convert_to_ascii(img, config_dither)

    assert ascii_no_dither != ascii_dither
    assert len(ascii_dither) > 0


def test_dithering_html():
    img = Image.new("RGB", (20, 20))
    for x in range(20):
        for y in range(20):
            val = int((x / 19) * 255)
            img.putpixel((x, y), (val, val, val))

    config_no_dither = HtmlConfig(width=20, charset="standard", dither=False)
    config_dither = HtmlConfig(width=20, charset="standard", dither=True)

    html_no_dither = convert_to_html(img, config_no_dither)
    html_dither = convert_to_html(img, config_dither)

    assert html_no_dither != html_dither
    assert len(html_dither) > 0
