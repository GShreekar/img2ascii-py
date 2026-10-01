import numpy as np
import pytest

import img2ascii.core.sampling as sampling
from img2ascii.core.sampling import HAS_NUMBA


def test_sample_grid_same_dimensions():
    # 4x4 image
    rgba = np.ones((4, 4, 4), dtype=np.float32) * 128
    luma = np.ones((4, 4), dtype=np.float32) * 100

    rgb_out, luma_out, alpha_out = sampling.sample_grid(rgba, luma, cols=4, rows=4)

    assert rgb_out.shape == (4, 4, 3)
    assert luma_out.shape == (4, 4)
    assert alpha_out.shape == (4, 4)
    np.testing.assert_allclose(rgb_out, 128.0)
    np.testing.assert_allclose(luma_out, 100.0)
    np.testing.assert_allclose(alpha_out, 128.0 / 255.0)


def test_sample_grid_downsample():
    # 8x8 image
    rgba = np.zeros((8, 8, 4), dtype=np.float32)
    rgba[:, :, :3] = 100.0
    rgba[:, :, 3] = 255.0
    luma = np.ones((8, 8), dtype=np.float32) * 50.0

    # Downsample to 2x2 grid
    rgb_out, luma_out, alpha_out = sampling.sample_grid(rgba, luma, cols=2, rows=2)

    assert rgb_out.shape == (2, 2, 3)
    assert luma_out.shape == (2, 2)
    assert alpha_out.shape == (2, 2)
    np.testing.assert_allclose(rgb_out, 100.0)
    np.testing.assert_allclose(luma_out, 50.0)
    np.testing.assert_allclose(alpha_out, 1.0)


@pytest.mark.skipif(not HAS_NUMBA, reason="requires the optional numba extra")
def test_sample_grid_fast():
    rgba = np.zeros((8, 8, 4), dtype=np.float32)
    rgba[:, :, :3] = 100.0
    rgba[:, :, 3] = 255.0
    luma = np.ones((8, 8), dtype=np.float32) * 50.0

    rgb_out, luma_out, alpha_out = sampling.sample_grid(
        rgba, luma, cols=2, rows=2, fast=True
    )

    assert rgb_out.shape == (2, 2, 3)
    assert luma_out.shape == (2, 2)
    assert alpha_out.shape == (2, 2)
    np.testing.assert_allclose(rgb_out, 100.0)
    np.testing.assert_allclose(luma_out, 50.0)
    np.testing.assert_allclose(alpha_out, 1.0)


def test_sample_grid_fast_missing_numba():
    rgba = np.zeros((8, 8, 4), dtype=np.float32)
    luma = np.ones((8, 8), dtype=np.float32) * 50.0
    import sys
    from unittest.mock import patch

    import pytest

    active_sampling = sys.modules["img2ascii.core.sampling"]
    with patch.object(active_sampling, "HAS_NUMBA", False):
        with pytest.raises(ImportError) as exc_info:
            active_sampling.sample_grid(rgba, luma, cols=2, rows=2, fast=True)
        assert "numba" in str(exc_info.value)


def test_numba_block_avg_py_func():
    from img2ascii.core.sampling import _numba_block_avg_2d, _numba_block_avg_3d

    func_3d = getattr(_numba_block_avg_3d, "py_func", _numba_block_avg_3d)
    func_2d = getattr(_numba_block_avg_2d, "py_func", _numba_block_avg_2d)

    arr_3d = np.ones((4, 4, 3), dtype=np.float32)
    res_3d = func_3d(arr_3d, 2, 2, 2, 2, 3)
    assert res_3d.shape == (2, 2, 3)
    np.testing.assert_allclose(res_3d, 1.0)

    arr_2d = np.ones((4, 4), dtype=np.float32)
    res_2d = func_2d(arr_2d, 2, 2, 2, 2)
    assert res_2d.shape == (2, 2)
    np.testing.assert_allclose(res_2d, 1.0)
