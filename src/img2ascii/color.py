def rgb_to_hex(r: int, g: int, b: int) -> str:
    """ Converts RGB color to hex code.
    Args:
        r: Red channel value (0-255).
        g: Green channel value (0-255).
        b: Blue channel value (0-255).
    Returns:
        Hex color code in the format "#RRGGBB".
    """
    return f"#{r:02x}{g:02x}{b:02x}"