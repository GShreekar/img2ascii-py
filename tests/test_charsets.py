import pytest

from img2ascii.charsets import CHARSETS, get_charset_ramp
from img2ascii.exceptions import InvalidCharsetError


def test_get_charset_ramp_presets():
    assert get_charset_ramp("standard") == " .:-=+*#%@"
    assert get_charset_ramp("standard", invert=True) == "@%#*+=-:. "


def test_get_charset_ramp_custom():
    assert get_charset_ramp("abc") == "abc"
    assert get_charset_ramp("abc", invert=True) == "cba"


def test_get_charset_ramp_invalid():
    with pytest.raises(InvalidCharsetError):
        get_charset_ramp("a")
    with pytest.raises(InvalidCharsetError):
        get_charset_ramp("")
    with pytest.raises(InvalidCharsetError):
        get_charset_ramp("   ")


def test_every_preset_runs_light_to_dark():
    # Index 0 must be the lightest glyph, so that luma 0 maps to the sparsest character.
    # "detailed" used to be stored reversed, which inverted the whole image.
    lightest = set(" .'`░")
    densest = set("@$#█")
    for name, ramp in CHARSETS.items():
        assert ramp[0] in lightest, f"{name} starts on a dense glyph: {ramp[0]!r}"
        assert ramp[-1] in densest, f"{name} ends on a sparse glyph: {ramp[-1]!r}"


def test_blank_glyph_only_appears_at_the_light_end():
    # A space is the sparsest glyph available, so it cannot sit mid-ramp.
    for name, ramp in CHARSETS.items():
        assert " " not in ramp[1:].rstrip(" "), f"{name} has an interior blank glyph"


def test_detailed_preset_has_no_stray_escape():
    ramp = CHARSETS["detailed"]
    # The literal used to be a raw string containing \", which left an extra backslash.
    assert ramp.count("\\") == 1
    assert ramp.count('"') == 1
    assert len(ramp) == 70
    assert len(set(ramp)) == len(ramp), "a density ramp should not repeat a glyph"


def test_preset_direction_matches_rendered_output():
    from PIL import Image

    from img2ascii.api import AsciiConfig, convert_to_ascii

    gradient = Image.new("L", (256, 8))
    for x in range(256):
        for y in range(8):
            gradient.putpixel((x, y), x)
    gradient = gradient.convert("RGB")

    for name in CHARSETS:
        row = convert_to_ascii(
            gradient, AsciiConfig(charset=name, width=20, height=1)
        ).splitlines()[0]
        # Dark pixels are on the left, so the row must not start denser than it ends.
        assert row[0] != row[-1], name
        assert row.startswith(CHARSETS[name][0]), name


def test_charset_rejects_control_characters():
    for bad in [" \n#", "a\tb", "ab\r", " \x00#"]:
        with pytest.raises(InvalidCharsetError):
            get_charset_ramp(bad)


def test_charset_allows_unicode_blocks():
    assert get_charset_ramp("░▒▓█") == "░▒▓█"
