import numpy as np
from img2ascii.renderers.ascii_art import map_luma_to_ascii, AsciiArtRenderer


def test_map_luma_to_ascii_extreme_mapping():
    # 2x2 grid: luma values 0, 127.5, and 255
    # Ramp of length 3: "ABC"
    # Index mapping:
    # 0 -> 0 ("A")
    # 127.5 -> round(0.5 * 2) = 1 ("B")
    # 255 -> 2 ("C")
    grid_luma = np.array([[0.0, 127.5], [255.0, 255.0]], dtype=np.float32)

    # Disable auto_contrast to check exact mapping
    result = map_luma_to_ascii(grid_luma, ramp="ABC", auto_contrast=False)
    lines = result.splitlines()
    assert lines[0] == "AB"
    assert lines[1] == "CC"


def test_map_luma_to_ascii_auto_contrast():
    # 2x2 grid: luma range is [100, 200]
    # With auto_contrast enabled, 100 should map to 0 (ramp[0]), 200 should map to 255 (ramp[-1])
    grid_luma = np.array([[100.0, 150.0], [150.0, 200.0]], dtype=np.float32)

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


def test_map_luma_to_ascii_with_edges():
    grid_luma = np.array(
        [[0.0, 255.0, 255.0], [0.0, 255.0, 255.0], [0.0, 255.0, 255.0]],
        dtype=np.float32,
    )

    result = map_luma_to_ascii(
        grid_luma, ramp="ABC", auto_contrast=False, use_edges=True
    )
    assert "|" in result


def test_map_luma_to_ascii_with_horizontal_edges():
    grid_luma = np.array(
        [[0.0, 0.0, 0.0], [255.0, 255.0, 255.0], [255.0, 255.0, 255.0]],
        dtype=np.float32,
    )

    result = map_luma_to_ascii(
        grid_luma, ramp="ABC", auto_contrast=False, use_edges=True
    )
    assert "-" in result


def test_map_luma_to_ascii_with_diagonal_edges():
    # Diagonal falling
    grid_luma_falling = np.array(
        [[255.0, 0.0, 0.0], [0.0, 255.0, 0.0], [0.0, 0.0, 255.0]], dtype=np.float32
    )

    result_falling = map_luma_to_ascii(
        grid_luma_falling, ramp="ABC", auto_contrast=False, use_edges=True
    )
    assert "\\" in result_falling

    # Diagonal rising
    grid_luma_rising = np.array(
        [[0.0, 0.0, 255.0], [0.0, 255.0, 0.0], [255.0, 0.0, 0.0]], dtype=np.float32
    )

    result_rising = map_luma_to_ascii(
        grid_luma_rising, ramp="ABC", auto_contrast=False, use_edges=True
    )
    assert "/" in result_rising


def test_map_luma_to_ascii_edges_missing_scipy():
    grid_luma = np.array([[0.0, 255.0], [255.0, 0.0]], dtype=np.float32)
    from unittest.mock import patch
    import pytest

    with patch("img2ascii.renderers.ascii_art.HAS_SCIPY", False):
        with pytest.raises(ImportError) as exc_info:
            map_luma_to_ascii(grid_luma, ramp="ABC", use_edges=True)
        assert "scipy" in str(exc_info.value)


def test_map_luma_to_ascii_transparency():
    # 2x2 grid: luma is all 0 (black/A) but second column is transparent (alpha = 0.0)
    grid_luma = np.zeros((2, 2), dtype=np.float32)
    grid_alpha = np.array([[1.0, 0.0], [1.0, 0.0]], dtype=np.float32)

    result = map_luma_to_ascii(
        grid_luma, ramp="ABC", auto_contrast=False, grid_alpha=grid_alpha
    )
    lines = result.splitlines()
    # Opaque column 0 maps to "A". Transparent column 1 maps to " "
    assert lines[0] == "A "
    assert lines[1] == "A "
