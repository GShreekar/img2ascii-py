from typing import Optional
from dataclasses import dataclass
from pathlib import Path
from typing import Union
import numpy as np
from PIL import Image
from img2ascii.core.loader import load_image
from img2ascii.core.aspect import target_grid_size
from img2ascii.core.preprocess import preprocess_image
from img2ascii.core.sampling import sample_grid
from img2ascii.charsets import get_charset_ramp
from img2ascii.renderers.ascii_art import AsciiArtRenderer
from img2ascii.renderers.ansi import build_ansi_output
from img2ascii.renderers.pixel_exact import PixelExactRenderer
from img2ascii.renderers.svg import SvgRenderer
from img2ascii.exceptions import ImageTooLargeError


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


def _get_luma_weights(luma_method: str) -> tuple[float, float, float]:
    if luma_method == "bt601":
        return (0.299, 0.587, 0.114)
    elif luma_method == "bt709":
        return (0.2126, 0.7152, 0.0722)
    else:
        raise ValueError(
            f"Invalid luma_method: {luma_method}. Must be 'bt601' or 'bt709'."
        )


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
    rgba_arr = load_image(source)
    height, width = rgba_arr.shape[:2]
    target_cols, target_rows = target_grid_size(
        width, height, config.width, config.height, config.char_aspect
    )

    weights = _get_luma_weights(config.luma_method)
    rgba_prep, luma_prep = preprocess_image(rgba_arr, luma_weights=weights)

    rgb_grid, luma_grid, alpha_grid = sample_grid(
        rgba_prep, luma_prep, target_cols, target_rows, fast=config.fast
    )

    charset_ramp = get_charset_ramp(config.charset, invert=config.invert)
    renderer = AsciiArtRenderer(
        charset_ramp, config.auto_contrast, use_edges=config.edges
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
    rgba_arr = load_image(source)
    height, width = rgba_arr.shape[:2]
    if config.aspect_mode not in ("resize", "css"):
        raise ValueError(
            f"Invalid aspect_mode: {config.aspect_mode}. Must be 'resize' or 'css'."
        )
    char_aspect_to_use = 1.0 if config.aspect_mode == "css" else config.char_aspect
    target_cols, target_rows = target_grid_size(
        width, height, config.width, config.height, char_aspect_to_use
    )

    if (target_cols * target_rows) > config.max_cells and not config.allow_large:
        raise ImageTooLargeError(
            f"Grid size {target_cols}x{target_rows} ({target_cols * target_rows} cells) exceeds safety limit of {config.max_cells} cells. "
            f"Use --width/--height or scale down, or bypass with --allow-large."
        )

    weights = _get_luma_weights(config.luma_method)
    rgba_prep, luma_prep = preprocess_image(rgba_arr, luma_weights=weights)
    rgb_grid, luma_grid, alpha_grid = sample_grid(
        rgba_prep, luma_prep, target_cols, target_rows, fast=config.fast
    )

    if config.palette_size is not None:
        if config.palette_size < 2 or config.palette_size > 256:
            raise ValueError("palette_size must be between 2 and 256.")
        from PIL import Image

        img_rgb = Image.fromarray(
            np.clip(rgb_grid, 0.0, 255.0).astype(np.uint8), mode="RGB"
        )
        quantized_p = img_rgb.quantize(colors=config.palette_size)
        quantized_rgb = quantized_p.convert("RGB")
        rgb_grid = np.array(quantized_rgb, dtype=rgb_grid.dtype)

    renderer = PixelExactRenderer(
        config.glyph, config.bg_color, config.aspect_mode, config.char_aspect
    )
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
    rgba_arr = load_image(source)
    height, width = rgba_arr.shape[:2]
    target_cols, target_rows = target_grid_size(
        width, height, config.width, config.height, config.char_aspect
    )

    if (target_cols * target_rows) > config.max_cells and not config.allow_large:
        raise ImageTooLargeError(
            f"Grid size {target_cols}x{target_rows} ({target_cols * target_rows} cells) exceeds safety limit of {config.max_cells} cells. "
            f"Use --width/--height or scale down, or bypass with --allow-large."
        )

    weights = _get_luma_weights(config.luma_method)
    rgba_prep, luma_prep = preprocess_image(rgba_arr, luma_weights=weights)
    rgb_grid, luma_grid, alpha_grid = sample_grid(
        rgba_prep, luma_prep, target_cols, target_rows, fast=config.fast
    )

    if config.palette_size is not None:
        if config.palette_size < 2 or config.palette_size > 256:
            raise ValueError("palette_size must be between 2 and 256.")
        from PIL import Image

        img_rgb = Image.fromarray(
            np.clip(rgb_grid, 0.0, 255.0).astype(np.uint8), mode="RGB"
        )
        quantized_p = img_rgb.quantize(colors=config.palette_size)
        quantized_rgb = quantized_p.convert("RGB")
        rgb_grid = np.array(quantized_rgb, dtype=rgb_grid.dtype)

    renderer = SvgRenderer(config.bg_color, config.char_aspect)
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
    rgba_arr = load_image(source)
    height, width = rgba_arr.shape[:2]
    if config.aspect_mode not in ("resize", "css"):
        raise ValueError(
            f"Invalid aspect_mode: {config.aspect_mode}. Must be 'resize' or 'css'."
        )
    char_aspect_to_use = 1.0 if config.aspect_mode == "css" else config.char_aspect
    target_cols, target_rows = target_grid_size(
        width, height, config.width, config.height, char_aspect_to_use
    )

    if (target_cols * target_rows) > config.max_cells and not config.allow_large:
        raise ImageTooLargeError(
            f"Grid size {target_cols}x{target_rows} ({target_cols * target_rows} cells) exceeds safety limit of {config.max_cells} cells. "
            f"Use --width/--height or scale down, or bypass with --allow-large."
        )

    weights = _get_luma_weights(config.luma_method)
    rgba_prep, luma_prep = preprocess_image(rgba_arr, luma_weights=weights)
    rgb_grid, luma_grid, alpha_grid = sample_grid(
        rgba_prep, luma_prep, target_cols, target_rows, fast=config.fast
    )

    if config.palette_size is not None:
        if config.palette_size < 2 or config.palette_size > 256:
            raise ValueError("palette_size must be between 2 and 256.")
        from PIL import Image

        img_rgb = Image.fromarray(
            np.clip(rgb_grid, 0.0, 255.0).astype(np.uint8), mode="RGB"
        )
        quantized_p = img_rgb.quantize(colors=config.palette_size)
        quantized_rgb = quantized_p.convert("RGB")
        rgb_grid = np.array(quantized_rgb, dtype=rgb_grid.dtype)

    charset_ramp = get_charset_ramp(config.charset, invert=config.invert)
    ascii_renderer = AsciiArtRenderer(
        charset_ramp, config.auto_contrast, use_edges=config.edges
    )
    plain_ascii = ascii_renderer.render(rgb_grid, luma_grid, alpha_grid)
    char_grid = [list(line) for line in plain_ascii.splitlines()]

    pixel_renderer = PixelExactRenderer(
        bg_color=config.bg_color,
        aspect_mode=config.aspect_mode,
        char_aspect=config.char_aspect,
    )
    return pixel_renderer.render(rgb_grid, luma_grid, alpha_grid, glyphs=char_grid)
