import argparse
import sys
from typing import Union
from img2ascii.api import (
    convert_to_ascii,
    AsciiConfig,
    convert_to_pixels,
    PixelConfig,
    convert_to_svg,
    convert_to_html,
    HtmlConfig,
)
from img2ascii.exceptions import Img2AsciiError
from img2ascii.charsets import CHARSETS


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert images to ASCII art or pixel-exact HTML."
    )
    parser.add_argument(
        "source", help="Path to the input image, or '-' to read from standard input."
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Path to the output file (if not specified, outputs to stdout).",
    )
    parser.add_argument(
        "-w", "--width", type=int, default=None, help="Target width of the output grid."
    )
    parser.add_argument(
        "--height", type=int, default=None, help="Target height of the output grid."
    )
    parser.add_argument(
        "--char-aspect",
        type=float,
        default=2.0,
        help="Monospace character aspect ratio (height/width).",
    )
    preset_names = ", ".join(CHARSETS.keys())
    parser.add_argument(
        "--charset",
        default="standard",
        help=f"Charset name (available: {preset_names}) or custom character ramp.",
    )
    parser.add_argument(
        "--color", action="store_true", help="Enable terminal ANSI truecolor output."
    )
    parser.add_argument("--dither", action="store_true", help="Enable dithering.")
    parser.add_argument(
        "--no-contrast",
        action="store_true",
        help="Disable automatic contrast adjustment.",
    )
    parser.add_argument(
        "-i", "--invert", action="store_true", help="Invert the character ramp."
    )
    parser.add_argument(
        "--mode",
        choices=["ascii", "pixel", "svg", "html"],
        default="ascii",
        help="Rendering mode: 'ascii' (default), 'pixel' (pixel-exact HTML), 'svg' (SVG), or 'html' (HTML ASCII).",
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Enable performance acceleration via JIT (requires numba).",
    )
    parser.add_argument(
        "--edges",
        action="store_true",
        help="Enable edge enhancement filters (requires scipy).",
    )

    parser.add_argument(
        "--glyph",
        default="█",
        help="Glyph used for pixel representation (pixel mode only).",
    )
    parser.add_argument(
        "--bg-color",
        default="#000000",
        help="HTML background color (pixel/html modes only).",
    )
    parser.add_argument(
        "--aspect-mode",
        choices=["resize", "css"],
        default="resize",
        help="HTML aspect mode (pixel/html modes only).",
    )
    parser.add_argument(
        "--allow-large",
        action="store_true",
        help="Allow processing very large grids in pixel/html modes.",
    )
    parser.add_argument(
        "--palette-size",
        type=int,
        default=None,
        help="Number of colors to quantize the image to (pixel/SVG/html modes only). Must be between 2 and 256.",
    )
    parser.add_argument(
        "--luma-method",
        choices=["bt601", "bt709"],
        default="bt601",
        help="Luma conversion weighting method: 'bt601' (default SD weights) or 'bt709' (HD weights).",
    )

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
                invert=args.invert,
                fast=args.fast,
                edges=args.edges,
                luma_method=args.luma_method,
            )
            output = convert_to_ascii(source_data, ascii_config)
        elif args.mode == "pixel":
            pixel_config = PixelConfig(
                width=args.width,
                height=args.height,
                char_aspect=args.char_aspect,
                glyph=args.glyph,
                bg_color=args.bg_color,
                aspect_mode=args.aspect_mode,
                allow_large=args.allow_large,
                fast=args.fast,
                palette_size=args.palette_size,
                luma_method=args.luma_method,
            )
            output = convert_to_pixels(source_data, pixel_config)
        elif args.mode == "svg":
            pixel_config = PixelConfig(
                width=args.width,
                height=args.height,
                char_aspect=args.char_aspect,
                glyph=args.glyph,
                bg_color=args.bg_color,
                aspect_mode=args.aspect_mode,
                allow_large=args.allow_large,
                fast=args.fast,
                palette_size=args.palette_size,
                luma_method=args.luma_method,
            )
            output = convert_to_svg(source_data, pixel_config)
        elif args.mode == "html":
            html_config = HtmlConfig(
                width=args.width,
                height=args.height,
                char_aspect=args.char_aspect,
                charset=args.charset,
                auto_contrast=not args.no_contrast,
                invert=args.invert,
                bg_color=args.bg_color,
                aspect_mode=args.aspect_mode,
                allow_large=args.allow_large,
                fast=args.fast,
                edges=args.edges,
                palette_size=args.palette_size,
                luma_method=args.luma_method,
            )
            output = convert_to_html(source_data, html_config)

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output)
                if not output.endswith("\n") and args.mode == "ascii":
                    f.write("\n")
        else:
            sys.stdout.write(output)
            if not output.endswith("\n") and args.mode == "ascii":
                sys.stdout.write("\n")
    except Img2AsciiError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ImportError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)
