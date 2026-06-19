import numpy as np
from img2ascii.renderers.base import BaseRenderer

def map_luma_to_ascii(grid_luma: np.ndarray, ramp: str, auto_contrast: bool = True) -> str:
    """Map a 2D luma array to ASCII characters using the provided character ramp.
    Args:
        grid_luma: 2D array of luma values (0-255).
        ramp: String of ASCII characters to use for mapping.
        auto_contrast: Whether to automatically adjust the contrast of the luma values.
    Returns:
        String containing the ASCII art.
    """
    min_luma = grid_luma.min()
    max_luma = grid_luma.max()
    
    if auto_contrast and (max_luma - min_luma) > 1e-5:
        grid_luma = (grid_luma - min_luma) * 255.0 / (max_luma - min_luma)
    else:
        grid_luma = np.clip(grid_luma, 0.0, 255.0)
        
    ramp_len = len(ramp)
    indices = np.round((grid_luma / 255.0) * (ramp_len - 1)).astype(np.int32)
    
    rows, cols = indices.shape
    ascii_rows = []
    for r in range(rows):
        row_str = "".join(ramp[idx] for idx in indices[r])
        ascii_rows.append(row_str)
        
    return "\n".join(ascii_rows)

class AsciiArtRenderer(BaseRenderer):
    """Simple ASCII Art renderer using blocks or standard characters."""
    def __init__(self, ramp: str, auto_contrast: bool = True):
        self.ramp = ramp
        self.auto_contrast = auto_contrast

    def render(self, grid_rgb: np.ndarray, grid_luma: np.ndarray, grid_alpha: np.ndarray) -> str:
        """Render the image as ASCII art.
        Args:
            grid_rgb: 3D array of RGB values (height, width, 3).
            grid_luma: 2D array of luma values (height, width).
            grid_alpha: 2D array of alpha values (height, width).
        Returns:
            String containing the ASCII art.
        """
        return map_luma_to_ascii(grid_luma, self.ramp, self.auto_contrast)