# img2ascii-py

[![PyPI version](https://img.shields.io/pypi/v/img2ascii-py.svg)](https://pypi.org/project/img2ascii-py/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/pypi/pyversions/img2ascii-py.svg)](https://pypi.org/project/img2ascii-py/)

A high-performance Python library and command-line (CLI) utility that converts images into beautiful, styled ASCII art or pixel-exact HTML/CSS output. 

Built with performance in mind using fully vectorized NumPy operations, `img2ascii-py` generates highly optimized terminal ANSI truecolor prints and run-length compressed HTML web pages.

---

## Features

- **Vectorized Core**: Color pre-processing (gamma, brightness, contrast) and block downsampling are fully vectorized using NumPy.
- **Terminal Truecolor**: Output ASCII art in 24-bit ANSI colors with a state-machine that minimizes escape-sequence overhead.
- **Pixel-Exact HTML**: Render pixel-art pages utilizing Run-Length Encoding (RLE) to bundle matching color spans and optimize filesize. Supports both `resize` (pre-sampling aspect scaling) and `css` (visual aspect scaling via line-height to preserve literal source pixel data) modes.
- **Pixel-Exact SVG Vector Output**: Convert images into scalable, clean SVG vector graphics with RLE-optimized `<rect>` nodes.
- **Curated Preset Ramps**: Includes preset charsets:
  - `standard`: ` .:-=+*#%@`
  - `detailed`: `$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\|()1{}[]?-_+~<>i! lI;:,"^`'. `
  - `blocks`: `░▒▓█`
  - `binary`: ` #`
  - `minimal`: ` .o0@`
  - Custom: Pass any string directly as your ramp!
- **Smart Image Handling**: Automatically transposes images based on EXIF rotation tags and handles transparent PNG alpha channels gracefully.
- **Full Stream Piping**: Pipe binary image streams directly into the CLI via `stdin`.

---

## Installation

Install the package directly from PyPI:

```bash
pip install img2ascii-py
```

### Optional Extras
- To enable faster image sampling (via Numba JIT compilation):
  ```bash
  pip install "img2ascii-py[fast]"
  ```
- To enable edge-detection enhancement filters:
  ```bash
  pip install "img2ascii-py[edges]"
  ```
- Install all features at once:
  ```bash
  pip install "img2ascii-py[fast,edges]"
  ```

---

## CLI Usage

When installed, the `img2ascii` command is added to your path.

```bash
img2ascii --help
```

### Quick Examples

#### 1. Basic Grayscale ASCII Art
Scale an image to a custom width and save the text file:
```bash
img2ascii path/to/image.jpg --width 80 > art.txt
```

#### 2. Colored Terminal Print
Display the image directly inside the terminal with 24-bit ANSI colors:
```bash
img2ascii path/to/image.jpg --width 100 --color
```

#### 3. Pixel-Exact HTML/CSS Output
Convert an image to a pixel-perfect HTML webpage using color-grouped HTML spans:
```bash
img2ascii path/to/image.jpg --width 150 --mode pixel -o page.html
```

#### 4. SVG Vector Graphic Output
Convert an image to a scalable SVG vector graphic file:
```bash
img2ascii path/to/image.jpg --width 120 --mode svg -o graphic.svg
```

#### 5. CSS Aspect Ratio Mode
Save a pixel-exact HTML file where visual aspect-ratio correction is done entirely in CSS (preserving literal original pixel coordinates):
```bash
img2ascii path/to/image.jpg --width 100 --mode pixel --aspect-mode css -o page.html
```

#### 6. Piping from Standard Input
Send binary stream output into the converter:
```bash
cat input.png | img2ascii - --width 60 -o output.txt
```

#### 7. JIT-Accelerated Fast Mode
Enable performance JIT acceleration using Numba for processing high-resolution files:
```bash
img2ascii path/to/large_image.jpg --width 200 --fast -o output.txt
```

#### 8. Edge Detection Enhancement
Overlay edge boundaries using Sobel filters to construct line art matching visual structures:
```bash
img2ascii path/to/line_art.png --width 100 --edges -o output.txt
```

---

## Library API Reference

You can also import and use `img2ascii` programmatically in your Python scripts.

### Grayscale or Colored ASCII Art

```python
from img2ascii.api import convert_to_ascii, AsciiConfig

# Configure settings
config = AsciiConfig(
    width=80,
    char_aspect=2.0,       # Adjusts height/width ratio for terminal fonts
    charset="standard",    # Supports presets: standard, detailed, blocks, binary, minimal
    color=True,            # Enable ANSI color escape codes
    auto_contrast=True,    # Stretch luma values for maximum dynamic range
    fast=True,             # Optional: Enable Numba JIT acceleration
    edges=True             # Optional: Enable SciPy Sobel edge-enhancement
)

# Render from file path, raw bytes, or a PIL Image object
art = convert_to_ascii("image.jpg", config)
print(art)
```

### Pixel-Exact Web Output (HTML)

```python
from img2ascii.api import convert_to_pixels, PixelConfig

config = PixelConfig(
    width=120,
    bg_color="#111111",
    glyph="█",             # Character block used to draw each pixel
    aspect_mode="css",     # aspect correction via CSS line-height (keeps raw pixel resolution)
    fast=True              # Optional: Enable Numba JIT acceleration
)

html_code = convert_to_pixels("image.png", config)
with open("output.html", "w") as f:
    f.write(html_code)
```

### Pixel-Exact Vector Output (SVG)

```python
from img2ascii.api import convert_to_svg, PixelConfig

config = PixelConfig(
    width=120,
    bg_color="#111111",
    fast=True              # Optional: Enable Numba JIT acceleration
)

svg_code = convert_to_svg("image.png", config)
with open("output.svg", "w") as f:
    f.write(svg_code)
```

---

## License

This project is open-source and licensed under the MIT License.
