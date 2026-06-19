import numpy as np
from img2ascii.renderers.base import BaseRenderer
from img2ascii.color import rgb_to_hex

class PixelExactRenderer(BaseRenderer):
    """ Renderer that outputs pixel-exact HTML table with CSS background colors."""

    def __init__(self, glyph: str = "█", bg_color: str = "#000000", aspect_mode: str = "resize"):
        super().__init__()
        self.glyph = glyph
        self.bg_color = bg_color
        self.aspect_mode = aspect_mode

    def run_length_encode_row(
        self, colors: list[tuple[int, int, int]], glyphs: list[str]
    ) -> list[tuple[tuple[int, int, int], str, int]]:
        """Run-length encode a single row of colors and glyphs.
        Args:
            colors: list of RGB tuples
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

    def render(self, grid_rgb: np.ndarray, grid_luma: np.ndarray, grid_alpha: np.ndarray) -> str:
        """Render the grid as an HTML table.
        Args:
            grid_rgb: (row, col, 3) array of RGB values
            grid_luma: (row, col) array of luma values (ignored)
            grid_alpha: (row, col) array of alpha values (ignored)
        Returns:
            str: HTML table string with pixel-exact colors
        """
        row_count, col_count = grid_rgb.shape[:2]
        unique_colors = set()
        encoded_runs = []

        for r in range(row_count):
            row_colors = [
                (int(grid_rgb[r, c, 0]), int(grid_rgb[r, c, 1]), int(grid_rgb[r, c, 2]))
                for c in range(col_count)
            ]
            row_glyphs = [self.glyph] * col_count
            runs = self.run_length_encode_row(row_colors, row_glyphs)
            encoded_runs.append(runs)
            for color in row_colors:
                unique_colors.add(color)
        
        style_rules = [
            "body {",
            f"    background-color: {self.bg_color};",
            "    margin: 0;",
            "    padding: 10px;",
            "}",
            "pre {",
            "    font-family: monospace;",
            "    line-height: 1.0;",
            "    margin: 0;",
            "    white-space: pre;",
            "}"
        ]
        
        rgb2css = {}
        for color in sorted(unique_colors):
            rgb_hex = rgb_to_hex(color[0], color[1], color[2])
            class_name = f"c_{rgb_hex[1:]}"
            rgb2css[color] = class_name
            style_rules.append(f".{class_name} {{ color: {rgb_hex}; }}")
            
        style_block = "<style>\n" + "\n".join(style_rules) + "\n</style>"
        
        markup_lines = ["<pre>"]
        for r in range(row_count):
            row_spans = []
            for color, glyph, length in encoded_runs[r]:
                class_name = rgb2css[color]
                repeated_text = glyph * length
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