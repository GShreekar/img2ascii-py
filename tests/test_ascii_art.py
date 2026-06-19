import numpy as np
from img2ascii.renderers.ascii_art import map_luma_to_ascii, AsciiArtRenderer

def test_map_luma_to_ascii_extreme_mapping():
    # 2x2 grid: luma values 0, 127.5, and 255
    # Ramp of length 3: "ABC"
    # Index mapping:
    # 0 -> 0 ("A")
    # 127.5 -> round(0.5 * 2) = 1 ("B")
    # 255 -> 2 ("C")
    grid_luma = np.array([
        [0.0, 127.5],
        [255.0, 255.0]
    ], dtype=np.float32)

    # Disable auto_contrast to check exact mapping
    result = map_luma_to_ascii(grid_luma, ramp="ABC", auto_contrast=False)
    lines = result.splitlines()
    assert lines[0] == "AB"
    assert lines[1] == "CC"

def test_map_luma_to_ascii_auto_contrast():
    # 2x2 grid: luma range is [100, 200]
    # With auto_contrast enabled, 100 should map to 0 (ramp[0]), 200 should map to 255 (ramp[-1])
    grid_luma = np.array([
        [100.0, 150.0],
        [150.0, 200.0]
    ], dtype=np.float32)

    result = map_luma_to_ascii(grid_luma, ramp="ABC", auto_contrast=True)
    lines = result.splitlines()
    # 100 -> normalized to 0 -> "A"
    # 150 -> normalized to 127.5 -> "B"
    # 200 -> normalized to 255 -> "C"
    assert lines[0] == "AB"
    assert lines[1] == "BC"

def test_ascii_art_renderer_class():
    grid_rgb = np.zeros((2, 2, 3), dtype=np.float32)
    grid_luma = np.array([[0.0, 255.0], [255.0, 0.0]], dtype=np.float32)
    grid_alpha = np.ones((2, 2), dtype=np.float32)

    renderer = AsciiArtRenderer(ramp="xy", auto_contrast=False)
    result = renderer.render(grid_rgb, grid_luma, grid_alpha)
    assert result == "xy\nyx"
