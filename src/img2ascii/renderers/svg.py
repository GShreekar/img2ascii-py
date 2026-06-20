import numpy as np
from img2ascii.renderers.base import BaseRenderer
from img2ascii.color import rgb_to_hex


class SvgRenderer(BaseRenderer):
    """Renderer that outputs pixel-exact SVG vector graphics."""

    def __init__(self, bg_color: str = "#000000", char_aspect: float = 2.0):
        super().__init__()
        self.bg_color = bg_color
        self.char_aspect = char_aspect

    def run_length_encode_row(
        self, colors: list[tuple[int, int, int, float]]
    ) -> list[tuple[tuple[int, int, int, float], int]]:
        """Run-length encode a single row of colors.
        Args:
            colors: list of RGBA tuples
        Returns:
            list of (color, count) tuples
        """
        if not colors:
            return []
        runs = []
        current_color = colors[0]
        run_len = 1
        for i in range(1, len(colors)):
            if colors[i] == current_color:
                run_len += 1
            else:
                runs.append((current_color, run_len))
                current_color = colors[i]
                run_len = 1
        runs.append((current_color, run_len))
        return runs

    def render(
        self, grid_rgb: np.ndarray, grid_luma: np.ndarray, grid_alpha: np.ndarray
    ) -> str:
        """Render the grid as an SVG document.
        Args:
            grid_rgb: (row, col, 3) array of RGB values
            grid_luma: (row, col) array of luma values (ignored)
            grid_alpha: (row, col) array of alpha values
        Returns:
            str: SVG string
        """
        row_count, col_count = grid_rgb.shape[:2]

        svg_width = col_count
        svg_height = row_count * self.char_aspect

        svg_lines = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_width} {svg_height}" width="{svg_width}" height="{svg_height}">'
        ]

        if self.bg_color and self.bg_color.lower() != "transparent":
            svg_lines.append(
                f'  <rect width="{svg_width}" height="{svg_height}" fill="{self.bg_color}" />'
            )

        for r in range(row_count):
            row_colors = [
                (
                    int(grid_rgb[r, c, 0]),
                    int(grid_rgb[r, c, 1]),
                    int(grid_rgb[r, c, 2]),
                    float(grid_alpha[r, c]),
                )
                for c in range(col_count)
            ]
            runs = self.run_length_encode_row(row_colors)

            c_idx = 0
            y_pos = r * self.char_aspect
            for color, length in runs:
                r_val, g_val, b_val, a_val = color
                if a_val > 0.0:
                    if a_val >= 0.999:
                        fill_str = rgb_to_hex(r_val, g_val, b_val)
                    else:
                        fill_str = f"rgba({r_val},{g_val},{b_val},{round(a_val, 3)})"

                    svg_lines.append(
                        f'  <rect x="{c_idx}" y="{y_pos}" width="{length}" height="{self.char_aspect}" fill="{fill_str}" />'
                    )
                c_idx += length

        svg_lines.append("</svg>")
        return "\n".join(svg_lines)
