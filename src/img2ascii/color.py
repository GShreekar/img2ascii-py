from __future__ import annotations

import re

from PIL import ImageColor

from img2ascii.exceptions import InvalidColorError

# CSS rgba() carries a float alpha, which Pillow's parser rejects, so it is split off first.
_RGBA_PATTERN = re.compile(
    r"^rgba\(\s*([^,]+?)\s*,\s*([^,]+?)\s*,\s*([^,]+?)\s*,\s*([0-9]*\.?[0-9]+)\s*\)$",
    re.IGNORECASE,
)


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Converts RGB color to hex code.
    Args:
        r: Red channel value (0-255).
        g: Green channel value (0-255).
        b: Blue channel value (0-255).
    Returns:
        Hex color code in the format "#RRGGBB".
    """
    return f"#{_clamp_channel(r):02x}{_clamp_channel(g):02x}{_clamp_channel(b):02x}"


def _clamp_channel(value: float) -> int:
    return max(0, min(255, round(float(value))))


def parse_color(value: str) -> tuple[int, int, int, float]:
    """Parses a CSS color into canonical channels, rejecting anything unrecognised.

    Callers embed the returned channels in markup instead of the original string, so a
    value that would break out of a CSS declaration or an XML attribute cannot survive.

    Args:
        value: Hex (#rgb, #rgba, #rrggbb, #rrggbbaa), rgb()/rgba(), hsl(), a CSS color
            name, or "transparent".
    Returns:
        Tuple of (red, green, blue, alpha) with channels in 0-255 and alpha in 0.0-1.0.
    """
    if not isinstance(value, str):
        raise InvalidColorError(f"Color must be a string, got {type(value).__name__}.")

    text = value.strip()
    if text.lower() == "transparent":
        return (0, 0, 0, 0.0)

    rgba_match = _RGBA_PATTERN.match(text)
    if rgba_match:
        red, green, blue, alpha = rgba_match.groups()
        channels = _parse_with_pillow(f"rgb({red},{green},{blue})", value)
        return (channels[0], channels[1], channels[2], _clamp_alpha(float(alpha)))

    channels = _parse_with_pillow(text, value)
    if len(channels) == 4:
        return (channels[0], channels[1], channels[2], channels[3] / 255.0)
    return (channels[0], channels[1], channels[2], 1.0)


def _parse_with_pillow(text: str, original: str) -> tuple[int, ...]:
    try:
        return ImageColor.getrgb(text)
    except ValueError as exc:
        raise InvalidColorError(
            f"Invalid color {original!r}. Use a hex code (#rrggbb), an rgb()/rgba()/hsl() "
            "function, a CSS color name, or 'transparent'."
        ) from exc


def _clamp_alpha(alpha: float) -> float:
    return max(0.0, min(1.0, alpha))


def to_css_color(rgba: tuple[int, int, int, float]) -> str:
    """Formats parsed channels as a CSS color, using hex when fully opaque."""
    red, green, blue, alpha = rgba
    if alpha >= 0.999:
        return rgb_to_hex(red, green, blue)
    return f"rgba({red}, {green}, {blue}, {round(alpha, 3)})"
