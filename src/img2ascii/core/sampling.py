import numpy as np
from PIL import Image

def sample_grid(rgba_arr: np.ndarray, luma_arr: np.ndarray, cols: int, rows: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Sample the rgba_arr and luma_arr at the grid points defined by cols and rows.
    Args:
        rgba_arr: 4-channel numpy array (RGBA) of shape (height, width, 4)
        luma_arr: 1-channel numpy array (Luma) of shape (height, width)
        cols: Number of columns in the grid
        rows: Number of rows in the grid
    Returns:
        Tuple of (rgba_arr, luma_arr, valid_mask)
        valid_mask: Boolean numpy array of shape (rows, cols)
    """
    height, width, channels = rgba_arr.shape
    if cols == width and rows == height:
        return rgba_arr[:,:,:3], luma_arr, rgba_arr[:,:,3] / 255.0
    
    block_width = max(1, width // cols)
    block_height = max(1, height // rows)
    target_width = block_width * cols
    target_height = block_height * rows
    
    rgba_uint8 = np.clip(rgba_arr, 0.0, 255.0).astype(np.uint8)
    luma_uint8 = np.clip(luma_arr, 0.0, 255.0).astype(np.uint8)
    
    rgba_resized = np.array(
        Image.fromarray(rgba_uint8).resize((target_width, target_height), Image.Resampling.LANCZOS),
        dtype=np.float32
    )
    luma_resized = np.array(
        Image.fromarray(luma_uint8).resize((target_width, target_height), Image.Resampling.LANCZOS),
        dtype=np.float32
    )
    
    rgba_reshaped = rgba_resized.reshape(rows, block_height, cols, block_width, channels)
    rgba_block_avg = rgba_reshaped.mean(axis=(1, 3))
    
    luma_reshaped = luma_resized.reshape(rows, block_height, cols, block_width)
    luma_block_avg = luma_reshaped.mean(axis=(1, 3))
    
    rgb_arr = rgba_block_avg[:, :, :3]
    alpha_arr = rgba_block_avg[:, :, 3] / 255.0
    
    return rgb_arr, luma_block_avg, alpha_arr