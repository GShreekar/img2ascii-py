"""Output-escaping and input-validation tests for the HTML and SVG writers."""

import xml.etree.ElementTree as ET
from html.parser import HTMLParser

import pytest
from PIL import Image

from img2ascii.api import (
    HtmlConfig,
    PixelConfig,
    convert_to_html,
    convert_to_pixels,
    convert_to_svg,
)
from img2ascii.exceptions import InvalidColorError, InvalidGlyphError
from img2ascii.renderers.pixel_exact import PixelExactRenderer
from img2ascii.renderers.svg import SvgRenderer


@pytest.fixture
def image():
    img = Image.new("RGB", (16, 12))
    pixels = img.load()
    for y in range(12):
        for x in range(16):
            pixels[x, y] = (x * 16 % 256, y * 20 % 256, (x + y) * 8 % 256)
    return img


class _TagCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)


def _tags(html):
    collector = _TagCollector()
    collector.feed(html)
    return collector.tags


def test_glyph_cannot_inject_markup():
    with pytest.raises(InvalidGlyphError):
        PixelExactRenderer(glyph="<script>alert(1)</script>")


def test_glyph_must_be_a_single_printable_character():
    for bad in ["", "ab", "\n", "\t", "█x"]:
        with pytest.raises(InvalidGlyphError):
            PixelExactRenderer(glyph=bad)
    # A single space is a legitimate glyph.
    assert PixelExactRenderer(glyph=" ").glyph == " "


def test_bg_color_cannot_inject_css(image):
    with pytest.raises(InvalidColorError):
        convert_to_pixels(
            image, PixelConfig(width=4, bg_color="red; } body::after{content:'pwn'}")
        )


def test_bg_color_cannot_inject_svg_elements(image):
    payload = '#000" /><script>alert(1)</script><rect fill="#fff'
    with pytest.raises(InvalidColorError):
        convert_to_svg(image, PixelConfig(width=4, bg_color=payload))


def test_bg_color_is_canonicalised_not_echoed():
    # A valid but non-hex spelling still reaches the output as parsed channels.
    assert SvgRenderer(bg_color="red").bg_color == "#ff0000"
    assert PixelExactRenderer(bg_color="rgb(255, 0, 0)").bg_color == "#ff0000"
    assert PixelExactRenderer(bg_color="rgba(255, 0, 0, 0.5)").bg_color == (
        "rgba(255, 0, 0, 0.5)"
    )


def test_ascii_glyphs_are_escaped_in_html(image):
    # The "detailed" ramp contains &, < and >, which are markup in HTML.
    html = convert_to_html(image, HtmlConfig(width=60, charset="detailed"))
    body = html.split("<pre>")[1].split("</pre>")[0]

    # The markup-significant glyphs are present, and present only as entities.
    assert "&amp;" in body
    assert "&lt;" in body
    assert "&gt;" in body
    for glyph, entity in (("&", "&amp;"), ("<", "&lt;"), (">", "&gt;")):
        assert f">{glyph}<" not in body, f"{glyph} emitted raw instead of {entity}"

    # Only the tags we emit ourselves survive parsing.
    assert set(_tags(html)) <= {"html", "head", "meta", "style", "body", "pre", "span"}


def test_generated_svg_is_well_formed_xml(image):
    svg = convert_to_svg(image, PixelConfig(width=8, bg_color="#112233"))
    root = ET.fromstring(svg)
    assert root.tag.endswith("svg")
    # rgba() is not valid in an SVG fill, so it must never be emitted.
    assert "rgba(" not in svg


def test_generated_html_is_parseable_with_every_preset(image):
    from img2ascii.charsets import CHARSETS

    for name in CHARSETS:
        html = convert_to_html(image, HtmlConfig(width=40, charset=name))
        assert set(_tags(html)) <= {
            "html",
            "head",
            "meta",
            "style",
            "body",
            "pre",
            "span",
        }, name


def test_glyph_must_be_a_string():
    with pytest.raises(InvalidGlyphError):
        PixelExactRenderer(glyph=None)  # type: ignore[arg-type]


def test_alphas_sharing_a_class_name_cannot_disagree():
    """Two alphas that quantise to the same byte must not emit conflicting rules."""
    import numpy as np

    grid_rgb = np.zeros((1, 2, 3), dtype=np.float32)
    grid_rgb[0, 0] = [255, 0, 0]
    grid_rgb[0, 1] = [255, 0, 0]
    grid_luma = np.zeros((1, 2), dtype=np.float32)
    # 0.5001 and 0.5019 both round to byte 0x80.
    grid_alpha = np.array([[0.5001, 0.5019]], dtype=np.float32)

    html = PixelExactRenderer().render(grid_rgb, grid_luma, grid_alpha)
    style = html.split("<style>")[1].split("</style>")[0]
    assert style.count(".c_ff000080 {") == 1, "duplicate rules for one class name"
