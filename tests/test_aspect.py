from img2ascii.core.aspect import target_grid_size

def test_target_grid_size_defaults():
    # If both are None, default width should be 80.
    # Image aspect is 1:1, char aspect is 2.0. Output aspect should be 1:1 visually.
    # 80 columns. Visually height = row * char_aspect.
    # visually: col_width = row_height * char_aspect => col / row = char_aspect.
    # 80 / row = 2.0 => row = 40.
    cols, rows = target_grid_size(100, 100)
    assert cols == 80
    assert rows == 40

def test_target_grid_size_width_only():
    # Width specified as 120
    cols, rows = target_grid_size(100, 50, out_width=120, char_aspect=2.0)
    # Row = 120 * 50 / (100 * 2.0) = 30
    assert cols == 120
    assert rows == 30

def test_target_grid_size_height_only():
    # Height specified as 30
    cols, rows = target_grid_size(100, 50, out_height=30, char_aspect=2.0)
    # Cols = 30 * 100 * 2.0 / 50 = 120
    assert cols == 120
    assert rows == 30

def test_target_grid_size_both():
    # Both specified
    cols, rows = target_grid_size(100, 100, out_width=60, out_height=40)
    assert cols == 60
    assert rows == 40

def test_target_grid_size_minimum():
    # Small dimensions should result in at least 1x1
    cols, rows = target_grid_size(1000, 1, out_width=1, char_aspect=2.0)
    assert cols == 1
    assert rows == 1

    cols, rows = target_grid_size(1, 1000, out_height=1, char_aspect=2.0)
    assert cols == 1
    assert rows == 1
