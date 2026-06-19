# img2ascii

A high-performance Python library and CLI tool that converts images into text-based and HTML representations. Built with performance in mind using vectorized NumPy operations, `img2ascii` supports rich terminal truecolor formatting and pixel-exact HTML/CSS generation with compressed run-length encoding.

---

## Features

- **Vectorized Math Core**: Color preprocessing (contrast, brightness, gamma adjustments) and block-averaging downsampling are fully vectorized via NumPy.
- **ASCII Art Mode**: Convert images to grayscale text characters using curated built-in ramps (standard, detailed, blocks, binary, minimal) or your own custom character sets.
- **Terminal Truecolor (ANSI)**: Wrap ASCII art output with 24-bit ANSI escape codes, minimizing output size through a smart color state-machine.
- **Pixel-Exact Web Output**: Generate highly optimized, pixel-exact HTML representations using Run-Length Encoding (RLE) to group consecutive identical colors into single `span` tags.
- **Exif Transposition**: Automatically handles rotation metadata to ensure correct image orientation.
- **Stream Piping**: Full CLI support for input and output streaming, allowing you to pipe image binary data into standard input.

---

## Installation

To install `img2ascii` locally, navigate to the project directory and install the package with pip (optionally in a virtual environment):

```bash
pip install .
```

For development dependencies, install the `dev` extra:

```bash
pip install -e ".[dev]"
```

---

## CLI Usage

When installed, `img2ascii` provides a command-line script. You can run it directly:

```bash
img2ascii --help
```

### Basic ASCII Conversion
Convert an image to a text file with a width of 80 columns:
```bash
img2ascii path/to/image.jpg --width 80 > art.txt
```

### Colored ANSI Terminal Output
Render an image in the terminal with 24-bit colors enabled:
```bash
img2ascii path/to/image.jpg --width 100 --color
```

### Piping from Standard Input
Pipe image binary data directly into the tool:
```bash
cat photo.png | img2ascii - --width 60 > output.txt
```

### Pixel-Exact HTML Generation
Generate an optimized HTML webpage representation of an image using the pixel-exact renderer:
```bash
img2ascii path/to/image.jpg --width 120 --mode pixel > index.html
```

---

## Library API Reference

### 1. ASCII Art Mode
Use `convert_to_ascii` to programmatically render images to ASCII strings:

```python
from pathlib import Path
from img2ascii.api import convert_to_ascii, AsciiConfig

config = AsciiConfig(
    width=80,
    char_aspect=2.0,
    charset="standard",
    color=True,
    auto_contrast=True
)

# Accepts file paths (str, Path), raw bytes, or PIL Image objects
ascii_art = convert_to_ascii("image.jpg", config)
print(ascii_art)
```

### 2. Pixel-Exact Web Output (HTML)
Use `convert_to_pixels` to produce optimized pixel-art HTML layouts:

```python
from img2ascii.api import convert_to_pixels, PixelConfig

config = PixelConfig(
    width=150,
    bg_color="#111111",
    glyph="█"
)

html_markup = convert_to_pixels("image.png", config)
with open("output.html", "w") as f:
    f.write(html_markup)
```

---

## Development & Testing

We maintain a strict quality assurance suite. You can run unit tests, type-checking, and style validation using:

### Running Tests
Execute the entire test suite and verify test coverage (99% coverage target):
```bash
pytest --cov=img2ascii tests/
```

### Code Formatting and Linting
Ensure style compliance using Ruff:
```bash
ruff check src/
```

### Static Type-Checking
Verify type safety using strict Mypy rules:
```bash
mypy --strict src/
```

---

## License

This project is licensed under the MIT License.
