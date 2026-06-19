import numpy as np

def preprocess_image(rgba_arr: np.ndarray, brightness: float = 1.0, contrast: float = 1.0, gamma: float = 1.0, luma_weights: tuple[float, float, float] = (0.299, 0.587, 0.114)) -> tuple[np.ndarray, np.ndarray]:
    """ Preprocess the image for ascii conversion
    Args:
        rgba_arr (np.ndarray): The image array in RGBA format
        brightness (float): The brightness adjustment
        contrast (float): The contrast adjustment
        gamma (float): The gamma correction
        luma_weights (tuple[float, float, float]): The weights for luma calculation
    Returns:
        tuple[np.ndarray, np.ndarray]: The preprocessed image array and alpha channel
    """
    rgba_arr = np.array(rgba_arr, dtype=np.float32)
    rgb = rgba_arr[:,:,:3]
    alpha = rgba_arr[:,:,3]
    if brightness != 1.0:
        rgb = rgb * brightness
    if contrast != 1.0:
        rgb = (rgb - 127.5) * contrast + 127.5
    if gamma != 1.0:
        rgb = np.clip(rgb, 0.0, 255.0)
        rgb = rgb / 255.0
        rgb = np.power(rgb, 1.0 / gamma)
        rgb = rgb * 255.0
    rgba_arr[:,:,:3] = rgb
    rgba_arr = np.clip(rgba_arr, 0.0, 255.0)

    red_weight, green_weight, blue_weight = luma_weights
    luma = rgba_arr[:,:,0] * red_weight + rgba_arr[:,:,1] * green_weight + rgba_arr[:,:,2] * blue_weight
    alpha_norm = np.clip(alpha / 255.0, 0.0, 1.0)
    luma = (luma * alpha_norm) + (255.0 * (1.0 - alpha_norm))
    luma = np.clip(luma, 0.0, 255.0)
    
    return rgba_arr, luma

