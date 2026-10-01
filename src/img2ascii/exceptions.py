class Img2AsciiError(Exception):
    """Base exception for all img2ascii errors."""


class UnsupportedImageError(Img2AsciiError):
    """Raised when an unsupported image format or mode is encountered."""


class ImageTooLargeError(Img2AsciiError):
    """Raised when an image is too large for processing."""


class InvalidCharsetError(Img2AsciiError):
    """Raised when an invalid charset is provided."""


class InvalidColorError(Img2AsciiError, ValueError):
    """Raised when a color string cannot be parsed."""


class InvalidGlyphError(Img2AsciiError, ValueError):
    """Raised when a glyph is not a single printable character."""


class InvalidDimensionsError(Img2AsciiError, ValueError):
    """Raised when requested output dimensions are not positive."""
