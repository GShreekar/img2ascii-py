import os
import numpy as np
from unittest import mock
from img2ascii.renderers.ansi import supports_color, build_ansi_output


def test_supports_color():
    with mock.patch.dict(os.environ, {"NO_COLOR": "1"}):
        assert not supports_color()

    with mock.patch.dict(os.environ, {"COLORTERM": "truecolor"}, clear=True):
        assert supports_color()

    with mock.patch.dict(os.environ, {"COLORTERM": "24bit"}, clear=True):
        assert supports_color()

    with mock.patch.dict(os.environ, {"TERM": "xterm-256color"}, clear=True):
        assert supports_color()

    with mock.patch.dict(os.environ, {"TERM": "vt100"}, clear=True):
        assert not supports_color()

    with mock.patch.dict(os.environ, {}, clear=True):
        assert not supports_color()


def test_build_ansi_output_no_color():
    char_grid = [["x", "y"], ["z", " "]]
    grid_rgb = np.zeros((2, 2, 3), dtype=np.float32)

    result = build_ansi_output(char_grid, grid_rgb, use_color=False)
    assert result == "xy\nz "


def test_build_ansi_output_with_color():
    char_grid = [["x", "y", "y"], ["z", "w", " "], [" ", "a", " "]]
    # Row 0: Red, Red, Red
    # Row 1: Green, Blue, (Black/ignored)
    # Row 2: (Black/ignored), Red, (Black/ignored)
    grid_rgb = np.zeros((3, 3, 3), dtype=np.float32)
    grid_rgb[0, 0] = [255, 0, 0]
    grid_rgb[0, 1] = [255, 0, 0]
    grid_rgb[0, 2] = [255, 0, 0]
    grid_rgb[1, 0] = [0, 255, 0]
    grid_rgb[1, 1] = [0, 0, 255]
    grid_rgb[2, 1] = [255, 0, 0]

    result = build_ansi_output(char_grid, grid_rgb, use_color=True)
    lines = result.splitlines()

    # Red escape: \x1b[38;2;255;0;0m
    # Reset escape: \x1b[0m
    expected_line_0 = "\x1b[38;2;255;0;0mxyy\x1b[0m"
    assert lines[0] == expected_line_0

    # Green escape: \x1b[38;2;0;255;0m
    # Blue escape: \x1b[38;2;0;0;255m
    expected_line_1 = "\x1b[38;2;0;255;0mz\x1b[38;2;0;0;255mw\x1b[0m "
    assert lines[1] == expected_line_1

    # Row 2 space then red then space:
    expected_line_2 = " \x1b[38;2;255;0;0ma\x1b[0m "
    assert lines[2] == expected_line_2
