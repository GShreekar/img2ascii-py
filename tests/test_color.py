import pytest

from img2ascii.color import parse_color, rgb_to_hex, to_css_color
from img2ascii.exceptions import InvalidColorError


def test_parse_hex_forms():
    assert parse_color("#112233") == (17, 34, 51, 1.0)
    assert parse_color("#fff") == (255, 255, 255, 1.0)
    assert parse_color("  #112233  ") == (17, 34, 51, 1.0)


def test_parse_hex_with_alpha():
    r, g, b, a = parse_color("#11223380")
    assert (r, g, b) == (17, 34, 51)
    assert a == pytest.approx(128 / 255.0)


def test_parse_functional_and_named_forms():
    assert parse_color("rgb(1, 2, 3)") == (1, 2, 3, 1.0)
    assert parse_color("red") == (255, 0, 0, 1.0)
    assert parse_color("hsl(0, 100%, 50%)") == (255, 0, 0, 1.0)


def test_parse_rgba_alpha():
    # Pillow's parser rejects a float alpha, so rgba() is handled separately.
    assert parse_color("rgba(255, 0, 0, 0.5)") == (255, 0, 0, 0.5)
    assert parse_color("RGBA(0,0,0,1)") == (0, 0, 0, 1.0)


def test_parse_transparent():
    assert parse_color("transparent") == (0, 0, 0, 0.0)
    assert parse_color("TRANSPARENT") == (0, 0, 0, 0.0)


def test_alpha_is_clamped():
    assert parse_color("rgba(0, 0, 0, 5)")[3] == 1.0


def test_rejects_injection_payloads():
    payloads = [
        "red; } body::after{content:'pwn'}",
        '#000" /><script>alert(1)</script><rect fill="#fff',
        "url(javascript:alert(1))",
        "expression(alert(1))",
        "#12",
        "",
        "not-a-color",
    ]
    for payload in payloads:
        with pytest.raises(InvalidColorError):
            parse_color(payload)


def test_rejects_non_string():
    with pytest.raises(InvalidColorError):
        parse_color(None)  # type: ignore[arg-type]


def test_rgb_to_hex_clamps_out_of_range_channels():
    # Used to emit malformed values such as "#12c-5100".
    assert rgb_to_hex(300, -5, 256) == "#ff00ff"
    assert rgb_to_hex(254.6, 0, 0) == "#ff0000"


def test_to_css_color_prefers_hex_when_opaque():
    assert to_css_color((17, 34, 51, 1.0)) == "#112233"
    assert to_css_color((17, 34, 51, 0.5)) == "rgba(17, 34, 51, 0.5)"
