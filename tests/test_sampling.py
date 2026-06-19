import numpy as np
from img2ascii.core.sampling import sample_grid

def test_sample_grid_same_dimensions():
    # 4x4 image
    rgba = np.ones((4, 4, 4), dtype=np.float32) * 128
    luma = np.ones((4, 4), dtype=np.float32) * 100

    rgb_out, luma_out, alpha_out = sample_grid(rgba, luma, cols=4, rows=4)

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
    rgb_out, luma_out, alpha_out = sample_grid(rgba, luma, cols=2, rows=2)

    assert rgb_out.shape == (2, 2, 3)
    assert luma_out.shape == (2, 2)
    assert alpha_out.shape == (2, 2)
    np.testing.assert_allclose(rgb_out, 100.0)
    np.testing.assert_allclose(luma_out, 50.0)
    np.testing.assert_allclose(alpha_out, 1.0)
