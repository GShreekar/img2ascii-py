import numpy as np
import pytest
from PIL import Image

from img2ascii.api import PixelConfig, convert_to_svg
from img2ascii.exceptions import ImageTooLargeError
from img2ascii.renderers.svg import SvgRenderer


def test_svg_renderer_basic():
    # 2x2 grid, all opaque
    grid_rgb = np.zeros((2, 2, 3), dtype=np.float32)
    grid_rgb[0, 0] = [255, 0, 0]  # Red
    grid_rgb[0, 1] = [255, 0, 0]  # Red (run of 2)
    grid_rgb[1, 0] = [0, 255, 0]  # Green
    grid_rgb[1, 1] = [0, 0, 255]  # Blue

    grid_luma = np.zeros((2, 2), dtype=np.float32)
    grid_alpha = np.ones((2, 2), dtype=np.float32)

    renderer = SvgRenderer(bg_color="#111111", char_aspect=2.0)
    svg = renderer.render(grid_rgb, grid_luma, grid_alpha)

    assert "<svg" in svg
    assert "</svg>" in svg
    assert 'viewBox="0 0 2 4.0"' in svg
    assert 'width="2"' in svg
    assert 'height="4.0"' in svg
    assert 'fill="#111111"' in svg

    # Check RLE output:
    # Row 0 has a run of length 2 of Red (#ff0000)
    assert '<rect x="0" y="0.0" width="2" height="2.0" fill="#ff0000" />' in svg
    # Row 1 has Green (#00ff00) at 0 and Blue (#0000ff) at 1
    assert '<rect x="0" y="2.0" width="1" height="2.0" fill="#00ff00" />' in svg
    assert '<rect x="1" y="2.0" width="1" height="2.0" fill="#0000ff" />' in svg


def test_svg_renderer_transparency():
    grid_rgb = np.zeros((2, 2, 3), dtype=np.float32)
    grid_rgb[0, 0] = [255, 0, 0]
    grid_rgb[0, 1] = [255, 0, 0]
    grid_rgb[1, 0] = [0, 255, 0]
    grid_rgb[1, 1] = [0, 255, 0]

    grid_luma = np.zeros((2, 2), dtype=np.float32)

    # Row 0 is transparent (alpha = 0.5), Row 1 is fully transparent (alpha = 0.0)
    grid_alpha = np.zeros((2, 2), dtype=np.float32)
    grid_alpha[0, :] = 0.5
    grid_alpha[1, :] = 0.0

    renderer = SvgRenderer(bg_color="transparent")
    svg = renderer.render(grid_rgb, grid_luma, grid_alpha)

    # Background rect shouldn't be added if background is transparent
    assert 'fill="transparent"' not in svg
    # Row 0 has a run of 2 at half opacity. SVG 1.1 has no rgba() color syntax, so
    # transparency has to travel in fill-opacity.
    assert (
        '<rect x="0" y="0.0" width="2" height="2.0" fill="#ff0000" fill-opacity="0.5" />'
        in svg
    )
    assert "rgba(" not in svg
    # Row 1 has run of 2 with alpha = 0.0, so no rects should be output
    assert 'y="2.0"' not in svg


def test_convert_to_svg_api():
    # Make a dummy image
    img = Image.new("RGBA", (10, 10), color=(255, 0, 0, 255))

    config = PixelConfig(width=5, height=5, char_aspect=2.0)
    svg = convert_to_svg(img, config)

    assert "<svg" in svg
    assert 'viewBox="0 0 5 10.0"' in svg

    # Test default config fallback
    svg_default = convert_to_svg(img, config=None)
    assert "<svg" in svg_default


def test_svg_renderer_empty_row():
    renderer = SvgRenderer()
    assert renderer.run_length_encode_row([]) == []


def test_convert_to_svg_size_limit():
    img = Image.new("RGBA", (100, 100), color=(255, 0, 0, 255))

    config = PixelConfig(width=50, height=50, max_cells=100, allow_large=False)
    with pytest.raises(ImageTooLargeError):
        convert_to_svg(img, config)
