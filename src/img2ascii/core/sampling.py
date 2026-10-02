from collections.abc import Callable

import numpy as np
from PIL import Image

try:
    from numba import jit

    HAS_NUMBA = True
except ImportError:
    HAS_NUMBA = False


def _numba_block_avg_3d(
    arr: np.ndarray,
    rows: int,
    cols: int,
    block_height: int,
    block_width: int,
    channels: int,
) -> np.ndarray:
    out = np.zeros((rows, cols, channels), dtype=np.float32)
    for r in range(rows):
        for c in range(cols):
            for ch in range(channels):
                total = 0.0
                for bh in range(block_height):
                    for bw in range(block_width):
                        total += arr[r * block_height + bh, c * block_width + bw, ch]
                out[r, c, ch] = total / (block_height * block_width)
    return out


def _numba_block_avg_2d(
    arr: np.ndarray, rows: int, cols: int, block_height: int, block_width: int
) -> np.ndarray:
    out = np.zeros((rows, cols), dtype=np.float32)
    for r in range(rows):
        for c in range(cols):
            total = 0.0
            for bh in range(block_height):
                for bw in range(block_width):
                    total += arr[r * block_height + bh, c * block_width + bw]
            out[r, c] = total / (block_height * block_width)
    return out


_numba_block_avg_3d_jit: Callable[..., np.ndarray]
_numba_block_avg_2d_jit: Callable[..., np.ndarray]

if HAS_NUMBA:
    _numba_block_avg_3d_jit = jit(nopython=True, cache=True)(_numba_block_avg_3d)
    _numba_block_avg_2d_jit = jit(nopython=True, cache=True)(_numba_block_avg_2d)
else:
    _numba_block_avg_3d_jit = _numba_block_avg_3d
    _numba_block_avg_2d_jit = _numba_block_avg_2d


def sample_grid(
    rgba_arr: np.ndarray, luma_arr: np.ndarray, cols: int, rows: int, fast: bool = False
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Sample the rgba_arr and luma_arr at the grid points defined by cols and rows.
    Args:
        rgba_arr: 4-channel numpy array (RGBA) of shape (height, width, 4)
        luma_arr: 1-channel numpy array (Luma) of shape (height, width)
        cols: Number of columns in the grid
        rows: Number of rows in the grid
        fast: Enable Numba JIT accelerated block sampling.
    Returns:
        Tuple of (rgb_arr, luma_block_avg, alpha_arr)
    """
    height, width, channels = rgba_arr.shape
    if cols == width and rows == height:
        return rgba_arr[:, :, :3], luma_arr, rgba_arr[:, :, 3] / 255.0

    block_width = max(1, width // cols)
    block_height = max(1, height // rows)
    target_width = block_width * cols
    target_height = block_height * rows

    rgba_uint8 = np.clip(rgba_arr, 0.0, 255.0).astype(np.uint8)
    luma_uint8 = np.clip(luma_arr, 0.0, 255.0).astype(np.uint8)

    rgba_resized = np.array(
        Image.fromarray(rgba_uint8).resize(
            (target_width, target_height), Image.Resampling.LANCZOS
        ),
        dtype=np.float32,
    )
    luma_resized = np.array(
        Image.fromarray(luma_uint8).resize(
            (target_width, target_height), Image.Resampling.LANCZOS
        ),
        dtype=np.float32,
    )

    if fast:
        if not HAS_NUMBA:
            raise ImportError(
                "Optional dependency 'numba' is required for fast mode. "
                "Install it with: pip install img2ascii-py[fast]"
            )
        rgba_block_avg = _numba_block_avg_3d_jit(
            rgba_resized, rows, cols, block_height, block_width, channels
        )
        luma_block_avg = _numba_block_avg_2d_jit(
            luma_resized, rows, cols, block_height, block_width
        )
    else:
        rgba_reshaped = rgba_resized.reshape(
            rows, block_height, cols, block_width, channels
        )
        rgba_block_avg = rgba_reshaped.mean(axis=(1, 3))

        luma_reshaped = luma_resized.reshape(rows, block_height, cols, block_width)
        luma_block_avg = luma_reshaped.mean(axis=(1, 3))

    rgb_arr = rgba_block_avg[:, :, :3]
    alpha_arr = rgba_block_avg[:, :, 3] / 255.0

    return rgb_arr, luma_block_avg, alpha_arr
