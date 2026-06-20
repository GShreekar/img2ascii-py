import numpy as np
from img2ascii.core.preprocess import preprocess_image

def test_preprocess_defaults():
    # 4x4 RGBA image, fully opaque red
    rgba = np.zeros((4, 4, 4), dtype=np.uint8)
    rgba[:, :, 0] = 255 # red
    rgba[:, :, 3] = 255 # opaque alpha

    rgba_out, luma_out = preprocess_image(rgba)
    
    # Check that output is float32
    assert rgba_out.dtype == np.float32
    assert luma_out.dtype == np.float32

    # Check color adjustments are no-op
    np.testing.assert_allclose(rgba_out, rgba)

    # Check default luma calculation: 255 * 0.299 + 0 + 0 = 76.245
    expected_luma = 255.0 * 0.299
    np.testing.assert_allclose(luma_out, expected_luma, atol=1e-3)

def test_preprocess_transparency():
    # 4x4 RGBA image, half transparent red
    rgba = np.zeros((4, 4, 4), dtype=np.uint8)
    rgba[:, :, 0] = 255 # red
    rgba[:, :, 3] = 127 # ~0.5 alpha

    _, luma_out = preprocess_image(rgba)
    expected_luma = 255.0 * 0.299
    np.testing.assert_allclose(luma_out, expected_luma, atol=1e-3)

def test_preprocess_brightness_contrast_gamma():
    rgba = np.ones((2, 2, 4), dtype=np.uint8) * 100
    rgba[:, :, 3] = 255

    # Test brightness
    rgba_out, _ = preprocess_image(rgba, brightness=1.5)
    np.testing.assert_allclose(rgba_out[:, :, :3], 150.0)

    # Test contrast
    # formula: (val - 127.5) * contrast + 127.5
    rgba_out, _ = preprocess_image(rgba, contrast=2.0)
    expected_contrast = (100.0 - 127.5) * 2.0 + 127.5 # -27.5 * 2 + 127.5 = 72.5
    np.testing.assert_allclose(rgba_out[:, :, :3], expected_contrast)

    # Test gamma
    # formula: power(val/255, 1/gamma) * 255
    rgba_out, _ = preprocess_image(rgba, gamma=2.0)
    expected_gamma = np.power(100.0 / 255.0, 1.0 / 2.0) * 255.0
    np.testing.assert_allclose(rgba_out[:, :, :3], expected_gamma)
