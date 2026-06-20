import numpy as np
from img2ascii.color import rgb_to_hex
from img2ascii.renderers.pixel_exact import PixelExactRenderer

def test_rgb_to_hex():
    assert rgb_to_hex(0, 0, 0) == "#000000"
    assert rgb_to_hex(255, 255, 255) == "#ffffff"
    assert rgb_to_hex(18, 52, 86) == "#123456"

def test_run_length_encode_row():
    renderer = PixelExactRenderer()
    colors = [(255, 0, 0), (255, 0, 0), (0, 0, 255)]
    glyphs = ["█", "█", "█"]
    runs = renderer.run_length_encode_row(colors, glyphs)
    
    assert len(runs) == 2
    # First run: 2 red blocks
    assert runs[0] == ((255, 0, 0), "█", 2)
    # Second run: 1 blue block
    assert runs[1] == ((0, 0, 255), "█", 1)

def test_run_length_encode_row_empty():
    renderer = PixelExactRenderer()
    assert renderer.run_length_encode_row([], []) == []

def test_pixel_exact_renderer_html():
    renderer = PixelExactRenderer(glyph="█", bg_color="#111111")
    grid_rgb = np.zeros((2, 2, 3), dtype=np.float32)
    # Give different colors to pixels
    grid_rgb[0, 0] = [255, 0, 0]
    grid_rgb[0, 1] = [255, 0, 0]
    grid_rgb[1, 0] = [0, 255, 0]
    grid_rgb[1, 1] = [0, 255, 0]
    
    grid_luma = np.zeros((2, 2), dtype=np.float32)
    grid_alpha = np.ones((2, 2), dtype=np.float32)
    
    html = renderer.render(grid_rgb, grid_luma, grid_alpha)
    
    assert "<!DOCTYPE html>" in html
    assert "background-color: #111111;" in html
    # Check CSS classes
    assert ".c_ff0000 { color: #ff0000; }" in html
    assert ".c_00ff00 { color: #00ff00; }" in html
    # Check markup
    assert '<span class="c_ff0000">██</span>' in html
    assert '<span class="c_00ff00">██</span>' in html

def test_pixel_exact_renderer_transparency():
    renderer = PixelExactRenderer(glyph="█", bg_color="#111111")
    grid_rgb = np.zeros((2, 2, 3), dtype=np.float32)
    grid_rgb[0, 0] = [255, 0, 0]
    grid_rgb[0, 1] = [255, 0, 0]
    grid_rgb[1, 0] = [0, 255, 0]
    grid_rgb[1, 1] = [0, 255, 0]
    
    grid_luma = np.zeros((2, 2), dtype=np.float32)
    # Row 0 is transparent (alpha = 0.5), Row 1 is opaque (alpha = 1.0)
    grid_alpha = np.zeros((2, 2), dtype=np.float32)
    grid_alpha[0, :] = 0.5
    grid_alpha[1, :] = 1.0
    
    html = renderer.render(grid_rgb, grid_luma, grid_alpha)
    
    assert "<!DOCTYPE html>" in html
    assert ".c_ff000080 { color: rgba(255, 0, 0, 0.5); }" in html
    assert ".c_00ff00 { color: #00ff00; }" in html
    assert '<span class="c_ff000080">██</span>' in html
    assert '<span class="c_00ff00">██</span>' in html
