from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

import numpy as np
from PIL import Image

from img2ascii.charsets import get_charset_ramp
from img2ascii.core.aspect import target_grid_size
from img2ascii.core.loader import load_image
from img2ascii.core.preprocess import preprocess_image
from img2ascii.core.sampling import sample_grid
from img2ascii.exceptions import ImageTooLargeError
from img2ascii.renderers.ansi import build_ansi_output
from img2ascii.renderers.ascii_art import AsciiArtRenderer
from img2ascii.renderers.pixel_exact import PixelExactRenderer
from img2ascii.renderers.svg import SvgRenderer


@dataclass
class AsciiConfig:
    width: Optional[int] = None
    height: Optional[int] = None
    char_aspect: float = 2.0
    charset: str = "standard"
    color: bool = False
    dither: bool = False
    auto_contrast: bool = True
    invert: bool = False
    fast: bool = False
    edges: bool = False
    luma_method: str = "bt601"
    allow_large: bool = False
    max_cells: int = 16_000_000


def _get_luma_weights(luma_method: str) -> tuple[float, float, float]:
    if luma_method == "bt601":
        return (0.299, 0.587, 0.114)
    elif luma_method == "bt709":
        return (0.2126, 0.7152, 0.0722)
    else:
        raise ValueError(
            f"Invalid luma_method: {luma_method}. Must be 'bt601' or 'bt709'."
        )


def _check_grid_size(
    cols: int, rows: int, max_cells: int, allow_large: bool
) -> None:
    """Rejects grids large enough to exhaust memory during sampling or rendering."""
    if allow_large:
        return
    if (cols * rows) > max_cells:
        raise ImageTooLargeError(
            f"Grid size {cols}x{rows} ({cols * rows} cells) exceeds the safety limit of "
            f"{max_cells} cells. Reduce the requested width/height, raise max_cells, or "
            f"set allow_large to bypass the check."
        )


def _quantize_palette(rgb_grid: np.ndarray, palette_size: Optional[int]) -> np.ndarray:
    """Reduces the grid to at most palette_size distinct colors."""
    if palette_size is None:
        return rgb_grid
    if palette_size < 2 or palette_size > 256:
        raise ValueError("palette_size must be between 2 and 256.")
    img_rgb = Image.fromarray(np.clip(rgb_grid, 0.0, 255.0).astype(np.uint8), mode="RGB")
    quantized = img_rgb.quantize(colors=palette_size).convert("RGB")
    return np.array(quantized, dtype=rgb_grid.dtype)


def convert_to_ascii(
    source: Union[Path, str, bytes, Image.Image], config: Optional[AsciiConfig] = None
) -> str:
    """Convert an image to ASCII art.
    Args:
        source: Path to the image file.
        config: Configuration for the conversion.
    Returns:
        String containing the ASCII art.
    """
    if config is None:
        config = AsciiConfig()
    # Validated before the image is decoded so bad options fail fast.
    charset_ramp = get_charset_ramp(config.charset, invert=config.invert)
    weights = _get_luma_weights(config.luma_method)

    rgba_arr = load_image(source)
    height, width = rgba_arr.shape[:2]
    target_cols, target_rows = target_grid_size(
        width, height, config.width, config.height, config.char_aspect
    )
    _check_grid_size(target_cols, target_rows, config.max_cells, config.allow_large)

    rgba_prep, luma_prep = preprocess_image(rgba_arr, luma_weights=weights)

    rgb_grid, luma_grid, alpha_grid = sample_grid(
        rgba_prep, luma_prep, target_cols, target_rows, fast=config.fast
    )

    renderer = AsciiArtRenderer(
        charset_ramp,
        config.auto_contrast,
        use_edges=config.edges,
        dither=config.dither,
    )
    plain_ascii = renderer.render(rgb_grid, luma_grid, alpha_grid)
    char_grid = [list(line) for line in plain_ascii.splitlines()]
    return build_ansi_output(char_grid, rgb_grid, use_color=config.color)


@dataclass
class PixelConfig:
    width: Optional[int] = None
    height: Optional[int] = None
    char_aspect: float = 2.0
    glyph: str = "█"
    bg_color: str = "#000000"
    aspect_mode: str = "resize"
    allow_large: bool = False
    fast: bool = False
    max_cells: int = 16_000_000
    palette_size: Optional[int] = None
    luma_method: str = "bt601"


def convert_to_pixels(
    source: Union[Path, str, bytes, Image.Image], config: Optional[PixelConfig] = None
) -> str:
    """Convert an image to pixel-exact HTML.
    Args:
        source: Path to the image file or bytes.
        config: Configuration for the pixel-exact rendering.
    Returns:
        String containing the HTML document.
    """
    if config is None:
        config = PixelConfig()
    # Built before the image is decoded so an invalid glyph, color or aspect mode
    # fails fast instead of after the whole pipeline has run.
    renderer = PixelExactRenderer(
        config.glyph, config.bg_color, config.aspect_mode, config.char_aspect
    )
    weights = _get_luma_weights(config.luma_method)

    rgba_arr = load_image(source)
    height, width = rgba_arr.shape[:2]
    char_aspect_to_use = 1.0 if config.aspect_mode == "css" else config.char_aspect
    target_cols, target_rows = target_grid_size(
        width, height, config.width, config.height, char_aspect_to_use
    )

    _check_grid_size(target_cols, target_rows, config.max_cells, config.allow_large)

    rgba_prep, luma_prep = preprocess_image(rgba_arr, luma_weights=weights)
    rgb_grid, luma_grid, alpha_grid = sample_grid(
        rgba_prep, luma_prep, target_cols, target_rows, fast=config.fast
    )

    rgb_grid = _quantize_palette(rgb_grid, config.palette_size)
    return renderer.render(rgb_grid, luma_grid, alpha_grid)


def convert_to_svg(
    source: Union[Path, str, bytes, Image.Image], config: Optional[PixelConfig] = None
) -> str:
    """Convert an image to pixel-exact SVG vector graphic.
    Args:
        source: Path to the image file or bytes.
        config: Configuration for the rendering (shares fields with PixelConfig).
    Returns:
        String containing the SVG document.
    """
    if config is None:
        config = PixelConfig()
    # Built first so an invalid background color fails fast.
    renderer = SvgRenderer(config.bg_color, config.char_aspect)
    weights = _get_luma_weights(config.luma_method)

    rgba_arr = load_image(source)
    height, width = rgba_arr.shape[:2]
    target_cols, target_rows = target_grid_size(
        width, height, config.width, config.height, config.char_aspect
    )

    _check_grid_size(target_cols, target_rows, config.max_cells, config.allow_large)

    rgba_prep, luma_prep = preprocess_image(rgba_arr, luma_weights=weights)
    rgb_grid, luma_grid, alpha_grid = sample_grid(
        rgba_prep, luma_prep, target_cols, target_rows, fast=config.fast
    )

    rgb_grid = _quantize_palette(rgb_grid, config.palette_size)
    return renderer.render(rgb_grid, luma_grid, alpha_grid)


@dataclass
class HtmlConfig:
    width: Optional[int] = None
    height: Optional[int] = None
    char_aspect: float = 2.0
    charset: str = "standard"
    auto_contrast: bool = True
    invert: bool = False
    bg_color: str = "#000000"
    aspect_mode: str = "resize"
    allow_large: bool = False
    fast: bool = False
    edges: bool = False
    max_cells: int = 16_000_000
    palette_size: Optional[int] = None
    luma_method: str = "bt601"
    dither: bool = False


def convert_to_html(
    source: Union[Path, str, bytes, Image.Image], config: Optional[HtmlConfig] = None
) -> str:
    """Convert an image to HTML with styled ASCII art glyphs.
    Args:
        source: Path to the image file or bytes.
        config: Configuration for the HTML rendering.
    Returns:
        String containing the HTML document.
    """
    if config is None:
        config = HtmlConfig()
    # Built before the image is decoded so bad options fail fast.
    charset_ramp = get_charset_ramp(config.charset, invert=config.invert)
    pixel_renderer = PixelExactRenderer(
        bg_color=config.bg_color,
        aspect_mode=config.aspect_mode,
        char_aspect=config.char_aspect,
    )
    weights = _get_luma_weights(config.luma_method)

    rgba_arr = load_image(source)
    height, width = rgba_arr.shape[:2]
    char_aspect_to_use = 1.0 if config.aspect_mode == "css" else config.char_aspect
    target_cols, target_rows = target_grid_size(
        width, height, config.width, config.height, char_aspect_to_use
    )

    _check_grid_size(target_cols, target_rows, config.max_cells, config.allow_large)

    rgba_prep, luma_prep = preprocess_image(rgba_arr, luma_weights=weights)
    rgb_grid, luma_grid, alpha_grid = sample_grid(
        rgba_prep, luma_prep, target_cols, target_rows, fast=config.fast
    )

    rgb_grid = _quantize_palette(rgb_grid, config.palette_size)

    ascii_renderer = AsciiArtRenderer(
        charset_ramp,
        config.auto_contrast,
        use_edges=config.edges,
        dither=config.dither,
    )
    plain_ascii = ascii_renderer.render(rgb_grid, luma_grid, alpha_grid)
    char_grid = [list(line) for line in plain_ascii.splitlines()]
    return pixel_renderer.render(rgb_grid, luma_grid, alpha_grid, glyphs=char_grid)
