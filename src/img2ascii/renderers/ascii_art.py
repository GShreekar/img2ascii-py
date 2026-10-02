from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable

import numpy as np

from img2ascii.renderers.base import BaseRenderer

try:
    from scipy.ndimage import sobel

    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

try:
    from numba import jit

    HAS_NUMBA = True
except ImportError:
    HAS_NUMBA = False


def _dither_luma_2d(norm_luma: np.ndarray, ramp_len: int) -> np.ndarray:
    rows, cols = norm_luma.shape
    dithered: np.ndarray = norm_luma.copy().astype(np.float32)
    max_idx = ramp_len - 1
    factor = 255.0 / max_idx

    for r in range(rows):
        for c in range(cols):
            old_val = dithered[r, c]
            idx = int(round(old_val / factor))  # noqa: RUF046 - numba needs the cast
            if idx < 0:
                idx = 0
            elif idx > max_idx:
                idx = max_idx
            new_val = idx * factor
            dithered[r, c] = new_val
            err = old_val - new_val

            if c + 1 < cols:
                dithered[r, c + 1] += err * (7.0 / 16.0)
            if r + 1 < rows:
                if c - 1 >= 0:
                    dithered[r + 1, c - 1] += err * (3.0 / 16.0)
                dithered[r + 1, c] += err * (5.0 / 16.0)
                if c + 1 < cols:
                    dithered[r + 1, c + 1] += err * (1.0 / 16.0)
    return dithered


_dither_luma_2d_jit: Callable[..., np.ndarray]

if HAS_NUMBA:
    _dither_luma_2d_jit = jit(nopython=True, cache=True)(_dither_luma_2d)
else:
    _dither_luma_2d_jit = _dither_luma_2d


class AsciiStrategy(ABC):
    """Abstract base class for ASCII glyph mapping strategies."""

    @abstractmethod
    def map_luma(
        self,
        grid_luma: np.ndarray,
        ramp: str,
        auto_contrast: bool = True,
        grid_alpha: np.ndarray | None = None,
        dither: bool = False,
    ) -> list[list[str]]:
        """Map a 2D luma grid to a 2D grid of character strings.
        Args:
            grid_luma: 2D array of luma values (0-255).
            ramp: String of ASCII characters to use for mapping.
            auto_contrast: Whether to adjust the contrast of luma values.
            grid_alpha: Optional 2D array of alpha values (0.0-1.0).
            dither: Whether to apply Floyd-Steinberg dithering.
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
        dither: bool = False,
    ) -> list[list[str]]:
        min_luma = grid_luma.min()
        max_luma = grid_luma.max()

        if auto_contrast and (max_luma - min_luma) > 1e-5:
            norm_luma = (grid_luma - min_luma) * 255.0 / (max_luma - min_luma)
        else:
            norm_luma = np.clip(grid_luma, 0.0, 255.0)

        ramp_len = len(ramp)
        if dither:
            norm_luma = _dither_luma_2d_jit(norm_luma, ramp_len)

        indices = np.round((norm_luma / 255.0) * (ramp_len - 1)).astype(np.int32)
        indices = np.clip(indices, 0, ramp_len - 1)

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
        dither: bool = False,
    ) -> list[list[str]]:
        if not HAS_SCIPY:
            raise ImportError(
                "Optional dependency 'scipy' is required for edges mode. "
                "Install it with: pip install img2ascii-py[edges]"
            )

        char_grid = self.fallback.map_luma(
            grid_luma, ramp, auto_contrast, grid_alpha, dither
        )

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
    dither: bool = False,
) -> str:
    """Map a 2D luma array to ASCII characters using the provided character ramp,
    optionally using SciPy Sobel filters to outline edges.
    Args:
        grid_luma: 2D array of luma values (0-255).
        ramp: String of ASCII characters to use for mapping.
        auto_contrast: Whether to automatically adjust the contrast of the luma values.
        use_edges: Whether to map edge contours to line characters using SciPy Sobel filter.
        grid_alpha: Optional 2D array of alpha values (0.0-1.0).
        dither: Whether to apply Floyd-Steinberg dithering.
    Returns:
        String containing the ASCII art.
    """
    strategy = EdgeStrategy() if use_edges else BrightnessStrategy()
    char_grid = strategy.map_luma(grid_luma, ramp, auto_contrast, grid_alpha, dither)
    return "\n".join("".join(row) for row in char_grid)


class AsciiArtRenderer(BaseRenderer):
    """Simple ASCII Art renderer using blocks or standard characters."""

    def __init__(
        self,
        ramp: str,
        auto_contrast: bool = True,
        use_edges: bool = False,
        strategy: AsciiStrategy | None = None,
        dither: bool = False,
    ):
        self.ramp = ramp
        self.auto_contrast = auto_contrast
        self.use_edges = use_edges
        self.strategy = strategy or (
            EdgeStrategy() if use_edges else BrightnessStrategy()
        )
        self.dither = dither

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
            grid_luma, self.ramp, self.auto_contrast, grid_alpha, self.dither
        )
        return "\n".join("".join(row) for row in char_grid)
