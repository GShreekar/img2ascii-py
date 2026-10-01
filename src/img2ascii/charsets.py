from __future__ import annotations

from img2ascii.exceptions import InvalidCharsetError

# Every ramp is ordered lightest glyph first, so index 0 maps to the darkest luma.
CHARSETS = {
    "standard": " .:-=+*#%@",
    "detailed": (
        " .'`^\",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"
    ),
    "blocks": "░▒▓█",
    "binary": " #",
    "minimal": " .o0@",
}


def get_charset_ramp(name_or_custom: str, invert: bool = False) -> str:
    """Returns a normalized charset string by looking up a preset name or parsing the
    input directly.
    Args:
        name_or_custom: name or custom charset string.
        invert: If true, reverses the order of the characters.
    Returns:
        A string containing the final ordered charset.
    """
    ramp = CHARSETS.get(name_or_custom, name_or_custom)
    if len(ramp) < 2:
        raise InvalidCharsetError("Charset must contain at least two characters.")
    if not ramp.strip():
        raise InvalidCharsetError("Charset cannot contain only whitespace.")
    # A newline or tab glyph would shift every row of the rendered grid.
    if not ramp.isprintable():
        offenders = sorted({c for c in ramp if not c.isprintable()})
        raise InvalidCharsetError(
            "Charset cannot contain control or non-printable characters: "
            + ", ".join(repr(c) for c in offenders)
        )
    if invert:
        ramp = ramp[::-1]
    return ramp
