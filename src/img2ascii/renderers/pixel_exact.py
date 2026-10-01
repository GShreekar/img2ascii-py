from __future__ import annotations

from html import escape
from typing import Dict, Optional, Sequence, Set, Tuple, Union, cast

import numpy as np

from img2ascii.color import parse_color, rgb_to_hex, to_css_color
from img2ascii.exceptions import InvalidGlyphError
from img2ascii.renderers.base import BaseRenderer

ColorTuple = Union[Tuple[int, int, int], Tuple[int, int, int, float]]


def validate_glyph(glyph: str) -> str:
    """Checks that a glyph is a single printable character.

    Multi-character glyphs would break column alignment, and control characters would
    shift the rendered grid.
    """
    if not isinstance(glyph, str):
        raise InvalidGlyphError(f"Glyph must be a string, got {type(glyph).__name__}.")
    if len(glyph) != 1:
        raise InvalidGlyphError(
            f"Glyph must be exactly one character, got {len(glyph)}: {glyph!r}"
        )
    if not glyph.isprintable():
        raise InvalidGlyphError(f"Glyph must be printable, got {glyph!r}")
    return glyph


class PixelExactRenderer(BaseRenderer):
    """Renderer that outputs pixel-exact HTML table with CSS background colors."""

    def __init__(
        self,
        glyph: str = "█",
        bg_color: str = "#000000",
        aspect_mode: str = "resize",
        char_aspect: float = 2.0,
    ):
        super().__init__()
        self.glyph = validate_glyph(glyph)
        # Parsed up front so the caller's string never reaches the stylesheet.
        self.bg_color = to_css_color(parse_color(bg_color))
        if aspect_mode not in ("resize", "css"):
            raise ValueError(
                f"Invalid aspect_mode: {aspect_mode}. Must be 'resize' or 'css'."
            )
        self.aspect_mode = aspect_mode
        self.char_aspect = char_aspect

    def run_length_encode_row(
        self,
        colors: Sequence[ColorTuple],
        glyphs: Sequence[str],
    ) -> list[tuple[ColorTuple, str, int]]:
        """Run-length encode a single row of colors and glyphs.
        Args:
            colors: list of RGB or RGBA tuples
            glyphs: list of glyphs
        Returns:
            list of (color, glyph, count) tuples
        """
        if not colors:
            return []
        runs = []
        current_color = colors[0]
        current_glyph = glyphs[0]
        run_len = 1
        for i in range(1, len(colors)):
            if colors[i] == current_color and glyphs[i] == current_glyph:
                run_len += 1
            else:
                runs.append((current_color, current_glyph, run_len))
                current_color = colors[i]
                current_glyph = glyphs[i]
                run_len = 1
        runs.append((current_color, current_glyph, run_len))
        return runs

    def render(
        self,
        grid_rgb: np.ndarray,
        grid_luma: np.ndarray,
        grid_alpha: np.ndarray,
        glyphs: Optional[Sequence[Sequence[str]]] = None,
    ) -> str:
        """Render the grid as an HTML table.
        Args:
            grid_rgb: (row, col, 3) array of RGB values
            grid_luma: (row, col) array of luma values (ignored)
            grid_alpha: (row, col) array of alpha values
            glyphs: Optional custom 2D grid of glyph characters to render
        Returns:
            str: HTML table string with pixel-exact colors
        """
        row_count, col_count = grid_rgb.shape[:2]
        unique_colors: Set[ColorTuple] = set()
        encoded_runs = []

        for r in range(row_count):
            row_colors: list[ColorTuple] = [
                (
                    int(grid_rgb[r, c, 0]),
                    int(grid_rgb[r, c, 1]),
                    int(grid_rgb[r, c, 2]),
                    float(grid_alpha[r, c]),
                )
                for c in range(col_count)
            ]
            row_glyphs = glyphs[r] if glyphs is not None else [self.glyph] * col_count
            runs = self.run_length_encode_row(row_colors, row_glyphs)
            encoded_runs.append(runs)
            for color in row_colors:
                unique_colors.add(color)

        line_height_val = (1.0 / self.char_aspect) if self.aspect_mode == "css" else 1.0
        style_rules = [
            "body {",
            f"    background-color: {self.bg_color};",
            "    margin: 0;",
            "    padding: 10px;",
            "}",
            "pre {",
            "    font-family: monospace;",
            f"    line-height: {line_height_val};",
            "    margin: 0;",
            "    white-space: pre;",
            "}",
        ]

        rgb2css: Dict[ColorTuple, str] = {}
        emitted_classes: Set[str] = set()
        for color in sorted(unique_colors):
            r, g, b, a = cast(Tuple[int, int, int, float], color)

            if a >= 0.999:
                rgb_hex = rgb_to_hex(r, g, b)
                class_name = f"c_{rgb_hex[1:]}"
                declaration = f".{class_name} {{ color: {rgb_hex}; }}"
            else:
                # The class name and the declaration are derived from the same quantised
                # alpha, so two cells sharing a name cannot disagree on the color.
                alpha_byte = round(a * 255)
                class_name = f"c_{r:02x}{g:02x}{b:02x}{alpha_byte:02x}"
                a_val = round(alpha_byte / 255.0, 3)
                declaration = f".{class_name} {{ color: rgba({r}, {g}, {b}, {a_val}); }}"

            rgb2css[color] = class_name
            if class_name not in emitted_classes:
                emitted_classes.add(class_name)
                style_rules.append(declaration)

        style_block = "<style>\n" + "\n".join(style_rules) + "\n</style>"

        markup_lines = ["<pre>"]
        for r in range(row_count):
            row_spans = []
            for color, glyph, length in encoded_runs[r]:
                class_name = rgb2css[color]
                repeated_text = escape(glyph * length, quote=False)
                row_spans.append(f'<span class="{class_name}">{repeated_text}</span>')
            markup_lines.append("".join(row_spans))
        markup_lines.append("</pre>")
        markup_body = "\n".join(markup_lines)

        html = (
            "<!DOCTYPE html>\n"
            "<html>\n"
            "<head>\n"
            '    <meta charset="utf-8">\n'
            f"    {style_block}\n"
            "</head>\n"
            "<body>\n"
            f"{markup_body}\n"
            "</body>\n"
            "</html>"
        )
        return html
