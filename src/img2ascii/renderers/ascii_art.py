import numpy as np
from img2ascii.renderers.base import BaseRenderer

try:
    from scipy.ndimage import sobel  # type: ignore[import-untyped]
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

def map_luma_to_ascii(
    grid_luma: np.ndarray,
    ramp: str,
    auto_contrast: bool = True,
    use_edges: bool = False,
    grid_alpha: np.ndarray | None = None
) -> str:
    """Map a 2D luma array to ASCII characters using the provided character ramp, optionally using SciPy Sobel filters to outline edges.
    Args:
        grid_luma: 2D array of luma values (0-255).
        ramp: String of ASCII characters to use for mapping.
        auto_contrast: Whether to automatically adjust the contrast of the luma values.
        use_edges: Whether to map edge contours to line characters using SciPy Sobel filter.
        grid_alpha: Optional 2D array of alpha values (0.0-1.0).
    Returns:
        String containing the ASCII art.
    """
    min_luma = grid_luma.min()
    max_luma = grid_luma.max()
    
    if auto_contrast and (max_luma - min_luma) > 1e-5:
        norm_luma = (grid_luma - min_luma) * 255.0 / (max_luma - min_luma)
    else:
        norm_luma = np.clip(grid_luma, 0.0, 255.0)
        
    ramp_len = len(ramp)
    indices = np.round((norm_luma / 255.0) * (ramp_len - 1)).astype(np.int32)
    
    rows, cols = indices.shape
    char_grid = [[ramp[idx] for idx in row] for row in indices]

    if use_edges:
        if not HAS_SCIPY:
            raise ImportError(
                "Optional dependency 'scipy' is required for edges mode. "
                "Install it with: pip install img2ascii-py[edges]"
            )
        dx = sobel(grid_luma, axis=1)
        dy = sobel(grid_luma, axis=0)
        magnitude = np.hypot(dx, dy)
        max_mag = magnitude.max()
        if max_mag > 1e-5:
            threshold = 0.25 * max_mag
            for r in range(rows):
                for c in range(cols):
                    if magnitude[r, c] > threshold:
                        val_x = dx[r, c]
                        val_y = dy[r, c]
                        abs_x = abs(val_x)
                        abs_y = abs(val_y)
                        if abs_x > 2.0 * abs_y:
                            char_grid[r][c] = "|"
                        elif abs_y > 2.0 * abs_x:
                            char_grid[r][c] = "-"
                        elif val_x * val_y > 0:
                            char_grid[r][c] = "\\"
                        else:
                            char_grid[r][c] = "/"

    if grid_alpha is not None:
        for r in range(rows):
            for c in range(cols):
                if grid_alpha[r, c] < 0.5:
                    char_grid[r][c] = " "

    return "\n".join("".join(row) for row in char_grid)

class AsciiArtRenderer(BaseRenderer):
    """Simple ASCII Art renderer using blocks or standard characters."""
    def __init__(self, ramp: str, auto_contrast: bool = True, use_edges: bool = False):
        self.ramp = ramp
        self.auto_contrast = auto_contrast
        self.use_edges = use_edges

    def render(self, grid_rgb: np.ndarray, grid_luma: np.ndarray, grid_alpha: np.ndarray) -> str:
        """Render the image as ASCII art.
        Args:
            grid_rgb: 3D array of RGB values (height, width, 3).
            grid_luma: 2D array of luma values (height, width).
            grid_alpha: 2D array of alpha values (height, width).
        Returns:
            String containing the ASCII art.
        """
        return map_luma_to_ascii(grid_luma, self.ramp, self.auto_contrast, self.use_edges, grid_alpha)