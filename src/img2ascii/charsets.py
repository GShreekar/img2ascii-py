from img2ascii.exceptions import InvalidCharsetError

CHARSETS = {
    "standard": " .:-=+*#%@",
    "detailed": r"$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\|()1{}[]?-_+~<>i! lI;:,\"^`'. ",
    "blocks": "░▒▓█",
    "binary": " #",
    "minimal": " .o0@",
}


def get_charset_ramp(name_or_custom: str, invert: bool = False) -> str:
    """Returns a normalized charset string by looking up a preset name or parsing the input directly.
    Args:
        name_or_custom: name or custom charset string.
        invert: If true, reverses the order of the characters.
    Returns:
        A string containing the final ordered charset.
    """
    if name_or_custom in CHARSETS:
        ramp = CHARSETS[name_or_custom]
    else:
        ramp = name_or_custom
    if len(ramp) < 2:
        raise InvalidCharsetError("Charset must contain at least two characters.")
    if not ramp.strip():
        raise InvalidCharsetError("Charset cannot contain only whitespace.")
    if invert:
        ramp = ramp[::-1]
    return ramp
