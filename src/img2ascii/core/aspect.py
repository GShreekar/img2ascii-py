DEFAULT_CHAR_ASPECT = 2.0

def target_grid_size(image_width: int, image_height: int, out_width: int | None = None, out_height: int | None = None, char_aspect: float = DEFAULT_CHAR_ASPECT) -> tuple[int, int]:
    """ Calculate the output dimensions of the text grid, correcting for the
    2:1 aspect ratio of standard monospace fonts.
    """
    if out_width is not None and out_height is not None:
        return (out_width, out_height)

    if out_width is None and out_height is None:
        out_width = 80

    if out_width is not None:
        row_count = max(1, round(out_width * image_height / (image_width * char_aspect)))
        return (out_width, row_count)
    elif out_height is not None:
        col_count = max(1, round(out_height * image_width * char_aspect / image_height))
        return (col_count, out_height)
    
    return (80, 40)