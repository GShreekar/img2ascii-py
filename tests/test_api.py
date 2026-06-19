import numpy as np
from PIL import Image
from img2ascii.api import convert_to_ascii, AsciiConfig

def test_convert_to_ascii_pillow_image():
    # 10x10 white image
    img = Image.new("RGB", (10, 10), color=(255, 255, 255))
    
    # 4 columns, char aspect 2.0. Expected height:
    # row_count = round(4 * 10 / (10 * 2.0)) = 2 rows
    config = AsciiConfig(width=4, char_aspect=2.0, charset="standard")
    
    result = convert_to_ascii(img, config)
    lines = result.splitlines()
    assert len(lines) == 2
    assert all(len(line) == 4 for line in lines)
    # White image -> luma = 255 -> standard charset ramp " .:-=+*#%@" -> maps to "@"
    assert lines[0] == "@@@@"
    assert lines[1] == "@@@@"

def test_convert_to_ascii_invert():
    img = Image.new("RGB", (10, 10), color=(255, 255, 255))
    config = AsciiConfig(width=4, char_aspect=2.0, charset="standard", invert=True)
    result = convert_to_ascii(img, config)
    lines = result.splitlines()
    # Inverted standard charset ramp ends with space " " instead of "@" for max luma
    assert lines[0] == "    "

def test_convert_to_ascii_default_config():
    img = Image.new("RGB", (100, 100), color=(0, 0, 0))
    result = convert_to_ascii(img) # defaults to 80 columns
    lines = result.splitlines()
    assert len(lines) > 0
    assert len(lines[0]) == 80
