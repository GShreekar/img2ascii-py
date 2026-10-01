import os

import numpy as np


def supports_color() -> bool:
    """Check if the terminal supports color."""
    if os.getenv("NO_COLOR"):
        return False
    colorterm = os.getenv("COLORTERM")
    if colorterm in ("truecolor", "24bit"):
        return True
    term = os.getenv("TERM")
    return bool(term and ("xterm" in term or "color" in term))


def build_ansi_output(
    char_grid: list[list[str]], grid_rgb: np.ndarray, use_color: bool = True
) -> str:
    """Builds an ANSI escape-code formatted string from a character grid and RGB data.
    Args:
        char_grid: The grid of characters to use for the output.
        grid_rgb: The grid of RGB values corresponding to the character grid.
        use_color: Whether to use color in the output.
    Returns:
        The ANSI escape-code formatted string.
    """
    if not use_color:
        return "\n".join("".join(row) for row in char_grid)

    row_count, col_count = grid_rgb.shape[:2]
    rows = []

    for r in range(row_count):
        row_text = []
        active_color = None
        for c in range(col_count):
            char_glyph = char_grid[r][c]
            if char_glyph.isspace():
                if active_color is not None:
                    row_text.append("\x1b[0m")
                    active_color = None
                row_text.append(char_glyph)
            else:
                target_color = (
                    int(grid_rgb[r, c, 0]),
                    int(grid_rgb[r, c, 1]),
                    int(grid_rgb[r, c, 2]),
                )
                if target_color != active_color:
                    row_text.append(
                        f"\x1b[38;2;{target_color[0]};{target_color[1]};{target_color[2]}m"
                    )
                    active_color = target_color
                row_text.append(char_glyph)
        if active_color is not None:
            row_text.append("\x1b[0m")
        rows.append("".join(row_text))
    return "\n".join(rows)
