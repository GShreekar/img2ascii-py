from __future__ import annotations

import math

from img2ascii.exceptions import InvalidDimensionsError

DEFAULT_CHAR_ASPECT = 2.0


def target_grid_size(
    image_width: int,
    image_height: int,
    out_width: int | None = None,
    out_height: int | None = None,
    char_aspect: float = DEFAULT_CHAR_ASPECT,
) -> tuple[int, int]:
    """Calculate the output dimensions of the text grid, correcting for the 2:1 aspect
    ratio of standard monospace fonts.
    Args:
        image_width (int): The width of the image
        image_height (int): The height of the image
        out_width (int | None): The desired width of the output grid
        out_height (int | None): The desired height of the output grid
        char_aspect (float): The aspect ratio of the characters
    Returns:
        tuple[int, int]: The dimensions of the output grid
    """
    _validate_dimensions(image_width, image_height, out_width, out_height, char_aspect)

    if out_width is not None and out_height is not None:
        return (out_width, out_height)

    if out_width is None and out_height is None:
        out_width = 80

    if out_width is not None:
        row_count = max(
            1, round(out_width * image_height / (image_width * char_aspect))
        )
        return (out_width, row_count)

    # Out height is guaranteed not to be None here
    assert out_height is not None
    col_count = max(1, round(out_height * image_width * char_aspect / image_height))
    return (col_count, out_height)


def _validate_dimensions(
    image_width: int,
    image_height: int,
    out_width: int | None,
    out_height: int | None,
    char_aspect: float,
) -> None:
    if image_width < 1 or image_height < 1:
        raise InvalidDimensionsError(
            f"Image dimensions must be at least 1x1, got {image_width}x{image_height}."
        )
    for name, value in (("width", out_width), ("height", out_height)):
        if value is None:
            continue
        if not isinstance(value, int) or isinstance(value, bool):
            raise InvalidDimensionsError(
                f"Output {name} must be an integer, got {type(value).__name__}."
            )
        if value < 1:
            raise InvalidDimensionsError(
                f"Output {name} must be at least 1, got {value}."
            )
    if not math.isfinite(char_aspect) or char_aspect <= 0:
        raise InvalidDimensionsError(
            f"char_aspect must be a positive finite number, got {char_aspect}."
        )
