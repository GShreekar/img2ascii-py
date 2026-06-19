import pytest
from img2ascii.charsets import get_charset_ramp
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

