import argparse
import sys
from typing import Union
from img2ascii.api import convert_to_ascii, AsciiConfig, convert_to_pixels, PixelConfig
from img2ascii.exceptions import Img2AsciiError

def main() -> None:
    parser = argparse.ArgumentParser(description="Convert images to ASCII art or pixel-exact HTML.")
    parser.add_argument("source", help="Path to the input image, or '-' to read from standard input.")
    parser.add_argument("-w", "--width", type=int, default=None, help="Target width of the output grid.")
    parser.add_argument("--height", type=int, default=None, help="Target height of the output grid.")
    parser.add_argument("--char-aspect", type=float, default=2.0, help="Monospace character aspect ratio (height/width).")
    parser.add_argument("--charset", default="standard", help="Charset name or custom character ramp.")
    parser.add_argument("--color", action="store_true", help="Enable terminal ANSI truecolor output.")
    parser.add_argument("--dither", action="store_true", help="Enable dithering.")
    parser.add_argument("--no-contrast", action="store_true", help="Disable automatic contrast adjustment.")
    parser.add_argument("-i", "--invert", action="store_true", help="Invert the character ramp.")
    parser.add_argument("--mode", choices=["ascii", "pixel"], default="ascii", help="Rendering mode: 'ascii' (default) or 'pixel' (HTML).")
    
    # Pixel mode specific options
    parser.add_argument("--glyph", default="█", help="Glyph used for pixel representation (pixel mode only).")
    parser.add_argument("--bg-color", default="#000000", help="HTML background color (pixel mode only).")
    parser.add_argument("--aspect-mode", default="resize", help="HTML aspect mode (pixel mode only).")
    parser.add_argument("--allow-large", action="store_true", help="Allow processing very large grids in pixel mode.")

    args = parser.parse_args()

    source_data: Union[str, bytes]
    if args.source == "-":
        try:
            source_data = sys.stdin.buffer.read()
            if not source_data:
                print("Error: standard input is empty", file=sys.stderr)
                sys.exit(1)
        except Exception as e:
            print(f"Error reading from stdin: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        source_data = args.source

    try:
        if args.mode == "ascii":
            ascii_config = AsciiConfig(
                width=args.width,
                height=args.height,
                char_aspect=args.char_aspect,
                charset=args.charset,
                color=args.color,
                dither=args.dither,
                auto_contrast=not args.no_contrast,
                invert=args.invert
            )
            output = convert_to_ascii(source_data, ascii_config)
        else:
            pixel_config = PixelConfig(
                width=args.width,
                height=args.height,
                char_aspect=args.char_aspect,
                glyph=args.glyph,
                bg_color=args.bg_color,
                aspect_mode=args.aspect_mode,
                allow_large=args.allow_large
            )
            output = convert_to_pixels(source_data, pixel_config)
            
        sys.stdout.write(output)
        if not output.endswith("\n") and args.mode == "ascii":
            sys.stdout.write("\n")
    except Img2AsciiError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)
