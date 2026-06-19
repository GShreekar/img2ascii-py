from typing import Optional
from dataclasses import dataclass
from pathlib import Path
from typing import Union
from img2ascii.core.loader import load_image
from img2ascii.core.aspect import target_grid_size
from img2ascii.core.preprocess import preprocess_image
from img2ascii.core.sampling import sample_grid
from img2ascii.charsets import get_charset_ramp
from img2ascii.renderers.ascii_art import AsciiArtRenderer
from img2ascii.renderers.ansi import build_ansi_output
from img2ascii.renderers.pixel_exact import PixelExactRenderer
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

def convert_to_ascii(source: Union[Path, str, bytes], config: Optional[AsciiConfig] = None) -> str:
    """ Convert an image to ASCII art.
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
    target_cols, target_rows = target_grid_size(width, height, config.width, config.height, config.char_aspect)
    
    rgba_prep, luma_prep = preprocess_image(rgba_arr)
    
    rgb_grid, luma_grid, alpha_grid = sample_grid(rgba_prep, luma_prep, target_cols, target_rows)
    
    charset_ramp = get_charset_ramp(config.charset, invert=config.invert)
    renderer = AsciiArtRenderer(charset_ramp, config.auto_contrast)
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

def convert_to_pixels(source: Union[Path, str, bytes], config: Optional[PixelConfig] = None) -> str:
    """ Convert an image to pixel-exact HTML.
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
    target_cols, target_rows = target_grid_size(width, height, config.width, config.height, config.char_aspect)
    
    if (target_cols * target_rows) > 16_000_000 and not config.allow_large:
        raise ImageTooLargeError(f"Grid size {target_cols}x{target_rows} exceeds safety limit.")
        
    rgba_prep, luma_prep = preprocess_image(rgba_arr)
    rgb_grid, luma_grid, alpha_grid = sample_grid(rgba_prep, luma_prep, target_cols, target_rows)
    
    renderer = PixelExactRenderer(config.glyph, config.bg_color, config.aspect_mode)
    return renderer.render(rgb_grid, luma_grid, alpha_grid)



