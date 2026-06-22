import numpy as np
from abc import ABC, abstractmethod
from img2ascii.renderers.base import BaseRenderer

try:
    from scipy.ndimage import sobel  # type: ignore[import-untyped]

    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False


class AsciiStrategy(ABC):
    """Abstract base class for ASCII glyph mapping strategies."""

    @abstractmethod
    def map_luma(
        self,
        grid_luma: np.ndarray,
        ramp: str,
        auto_contrast: bool = True,
        grid_alpha: np.ndarray | None = None,
    ) -> list[list[str]]:
        """Map a 2D luma grid to a 2D grid of character strings.
        Args:
            grid_luma: 2D array of luma values (0-255).
            ramp: String of ASCII characters to use for mapping.
            auto_contrast: Whether to adjust the contrast of luma values.
            grid_alpha: Optional 2D array of alpha values (0.0-1.0).
        Returns:
            A list of lists of characters representing the mapped grid.
        """
        pass


class BrightnessStrategy(AsciiStrategy):
    """Maps luma values to characters directly based on perceptual brightness/density."""

    def map_luma(
        self,
        grid_luma: np.ndarray,
        ramp: str,
        auto_contrast: bool = True,
        grid_alpha: np.ndarray | None = None,
    ) -> list[list[str]]:
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

        if grid_alpha is not None:
            for r in range(rows):
                for c in range(cols):
                    if grid_alpha[r, c] < 0.5:
                        char_grid[r][c] = " "

        return char_grid


class EdgeStrategy(AsciiStrategy):
    """Detects strong edges using Sobel filters and maps them to directional line characters.

    Falls back to a brightness mapping strategy for regions without strong edges.
    """

    def __init__(self, fallback_strategy: BrightnessStrategy | None = None):
        self.fallback = fallback_strategy or BrightnessStrategy()

    def map_luma(
        self,
        grid_luma: np.ndarray,
        ramp: str,
        auto_contrast: bool = True,
        grid_alpha: np.ndarray | None = None,
    ) -> list[list[str]]:
        if not HAS_SCIPY:
            raise ImportError(
                "Optional dependency 'scipy' is required for edges mode. "
                "Install it with: pip install img2ascii-py[edges]"
            )

        char_grid = self.fallback.map_luma(grid_luma, ramp, auto_contrast, grid_alpha)

        dx = sobel(grid_luma, axis=1)
        dy = sobel(grid_luma, axis=0)
        magnitude = np.hypot(dx, dy)
        max_mag = magnitude.max()

        if max_mag > 1e-5:
            threshold = 0.25 * max_mag
            rows, cols = grid_luma.shape
            for r in range(rows):
                for c in range(cols):
                    if grid_alpha is not None and grid_alpha[r, c] < 0.5:
                        continue

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

        return char_grid


def map_luma_to_ascii(
    grid_luma: np.ndarray,
    ramp: str,
    auto_contrast: bool = True,
    use_edges: bool = False,
    grid_alpha: np.ndarray | None = None,
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
    strategy = EdgeStrategy() if use_edges else BrightnessStrategy()
    char_grid = strategy.map_luma(grid_luma, ramp, auto_contrast, grid_alpha)
    return "\n".join("".join(row) for row in char_grid)


class AsciiArtRenderer(BaseRenderer):
    """Simple ASCII Art renderer using blocks or standard characters."""

    def __init__(
        self,
        ramp: str,
        auto_contrast: bool = True,
        use_edges: bool = False,
        strategy: AsciiStrategy | None = None,
    ):
        self.ramp = ramp
        self.auto_contrast = auto_contrast
        self.use_edges = use_edges
        self.strategy = strategy or (
            EdgeStrategy() if use_edges else BrightnessStrategy()
        )

    def render(
        self, grid_rgb: np.ndarray, grid_luma: np.ndarray, grid_alpha: np.ndarray
    ) -> str:
        """Render the image as ASCII art.
        Args:
            grid_rgb: 3D array of RGB values (height, width, 3).
            grid_luma: 2D array of luma values (height, width).
            grid_alpha: 2D array of alpha values (height, width).
        Returns:
            String containing the ASCII art.
        """
        char_grid = self.strategy.map_luma(
            grid_luma, self.ramp, self.auto_contrast, grid_alpha
        )
        return "\n".join("".join(row) for row in char_grid)
