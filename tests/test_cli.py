import io
from unittest.mock import patch

import pytest
from PIL import Image

from img2ascii.cli.main import main
from img2ascii.core.sampling import HAS_NUMBA
from img2ascii.renderers.ascii_art import HAS_SCIPY

requires_numba = pytest.mark.skipif(
    not HAS_NUMBA, reason="requires the optional numba extra"
)
requires_scipy = pytest.mark.skipif(
    not HAS_SCIPY, reason="requires the optional scipy extra"
)


def test_cli_help():
    with (
        patch("sys.argv", ["img2ascii", "--help"]),
        patch("sys.stdout", new_callable=io.StringIO) as mock_stdout,
    ):
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 0
        help_output = mock_stdout.getvalue()
        assert "Convert images to ASCII art" in help_output
        for preset in ["standard", "detailed", "blocks", "binary", "minimal"]:
            assert preset in help_output


def test_cli_ascii_mode(tmp_path):
    # Create a small temporary image
    img_path = tmp_path / "test.png"
    img = Image.new("RGB", (10, 10), color=(255, 255, 255))
    img.save(img_path)

    with (
        patch(
            "sys.argv",
            ["img2ascii", str(img_path), "--width", "5", "--char-aspect", "1.0"],
        ),
        patch("sys.stdout", new_callable=io.StringIO) as mock_stdout,
    ):
        main()
        # White image -> standard maps to @
        output = mock_stdout.getvalue()
        assert "@@@@@" in output


def test_cli_pixel_mode(tmp_path):
    img_path = tmp_path / "test.png"
    img = Image.new("RGB", (10, 10), color=(255, 255, 255))
    img.save(img_path)

    with (
        patch(
            "sys.argv",
            [
                "img2ascii",
                str(img_path),
                "--width",
                "5",
                "--char-aspect",
                "1.0",
                "--mode",
                "pixel",
            ],
        ),
        patch("sys.stdout", new_callable=io.StringIO) as mock_stdout,
    ):
        main()
        output = mock_stdout.getvalue()
        assert "<!DOCTYPE html>" in output


def test_cli_pixel_aspect_mode_css(tmp_path):
    img_path = tmp_path / "test.png"
    img = Image.new("RGB", (10, 10), color=(255, 255, 255))
    img.save(img_path)

    with (
        patch(
            "sys.argv",
            [
                "img2ascii",
                str(img_path),
                "--width",
                "5",
                "--char-aspect",
                "2.0",
                "--mode",
                "pixel",
                "--aspect-mode",
                "css",
            ],
        ),
        patch("sys.stdout", new_callable=io.StringIO) as mock_stdout,
    ):
        main()
        output = mock_stdout.getvalue()
        assert "<!DOCTYPE html>" in output
        assert "line-height: 0.5;" in output


def test_cli_stdin():
    # Mock reading from stdin buffer
    img_bytes = io.BytesIO()
    img = Image.new("RGB", (10, 10), color=(255, 255, 255))
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)

    with (
        patch("sys.argv", ["img2ascii", "-", "--width", "5", "--char-aspect", "1.0"]),
        patch("sys.stdin.buffer.read", return_value=img_bytes.read()),
        patch("sys.stdout", new_callable=io.StringIO) as mock_stdout,
    ):
        main()
        output = mock_stdout.getvalue()
        assert "@@@@@" in output


def test_cli_stdin_empty():
    with (
        patch("sys.argv", ["img2ascii", "-"]),
        patch("sys.stdin.buffer.read", return_value=b""),
        patch("sys.stderr", new_callable=io.StringIO) as mock_stderr,
    ):
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 1
        assert "standard input is empty" in mock_stderr.getvalue()


def test_cli_unsupported_image(tmp_path):
    # Write corrupt data to file
    img_path = tmp_path / "corrupt.png"
    img_path.write_bytes(b"not an image")

    with (
        patch("sys.argv", ["img2ascii", str(img_path)]),
        patch("sys.stderr", new_callable=io.StringIO) as mock_stderr,
    ):
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 1
        assert "Error:" in mock_stderr.getvalue()


def test_cli_stdin_read_error():
    with (
        patch("sys.argv", ["img2ascii", "-"]),
        patch("sys.stdin.buffer.read", side_effect=IOError("read error")),
        patch("sys.stderr", new_callable=io.StringIO) as mock_stderr,
    ):
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 1
        assert "Error reading from stdin" in mock_stderr.getvalue()


def test_cli_value_error_is_reported_as_a_plain_error(tmp_path):
    img_path = tmp_path / "test.png"
    img = Image.new("RGB", (10, 10), color=(255, 255, 255))
    img.save(img_path)

    with (
        patch("sys.argv", ["img2ascii", str(img_path)]),
        patch(
            "img2ascii.cli.main.convert_to_ascii",
            side_effect=ValueError("bad option"),
        ),
        patch("sys.stderr", new_callable=io.StringIO) as mock_stderr,
    ):
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 1
        stderr = mock_stderr.getvalue()
        assert "Error: bad option" in stderr
        assert "Unexpected error" not in stderr


def test_cli_unexpected_error(tmp_path):
    img_path = tmp_path / "test.png"
    img = Image.new("RGB", (10, 10), color=(255, 255, 255))
    img.save(img_path)

    with (
        patch("sys.argv", ["img2ascii", str(img_path)]),
        patch(
            "img2ascii.cli.main.convert_to_ascii",
            side_effect=RuntimeError("internal failure"),
        ),
        patch("sys.stderr", new_callable=io.StringIO) as mock_stderr,
    ):
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 1
        assert "Unexpected error" in mock_stderr.getvalue()


@requires_numba
@requires_scipy
def test_cli_fast_and_edges(tmp_path):
    img_path = tmp_path / "test.png"
    img = Image.new("RGB", (10, 10), color=(255, 255, 255))
    img.save(img_path)

    with (
        patch(
            "sys.argv",
            [
                "img2ascii",
                str(img_path),
                "--width",
                "5",
                "--char-aspect",
                "1.0",
                "--fast",
                "--edges",
            ],
        ),
        patch("sys.stdout", new_callable=io.StringIO) as mock_stdout,
    ):
        main()
        output = mock_stdout.getvalue()
        assert len(output) > 0


@requires_numba
def test_cli_pixel_fast(tmp_path):
    img_path = tmp_path / "test.png"
    img = Image.new("RGB", (10, 10), color=(255, 255, 255))
    img.save(img_path)

    with (
        patch(
            "sys.argv",
            [
                "img2ascii",
                str(img_path),
                "--width",
                "5",
                "--char-aspect",
                "1.0",
                "--mode",
                "pixel",
                "--fast",
            ],
        ),
        patch("sys.stdout", new_callable=io.StringIO) as mock_stdout,
    ):
        main()
        output = mock_stdout.getvalue()
        assert "<!DOCTYPE html>" in output


def test_cli_svg_mode(tmp_path):
    img_path = tmp_path / "test.png"
    img = Image.new("RGB", (10, 10), color=(255, 255, 255))
    img.save(img_path)

    with (
        patch(
            "sys.argv",
            [
                "img2ascii",
                str(img_path),
                "--width",
                "5",
                "--char-aspect",
                "1.0",
                "--mode",
                "svg",
            ],
        ),
        patch("sys.stdout", new_callable=io.StringIO) as mock_stdout,
    ):
        main()
        output = mock_stdout.getvalue()
        assert "<svg" in output


def test_cli_output_file(tmp_path):
    img_path = tmp_path / "test.png"
    img = Image.new("RGB", (10, 10), color=(255, 255, 255))
    img.save(img_path)
    output_path = tmp_path / "output.svg"

    with (
        patch(
            "sys.argv",
            [
                "img2ascii",
                str(img_path),
                "--width",
                "5",
                "--char-aspect",
                "1.0",
                "--mode",
                "svg",
                "--output",
                str(output_path),
            ],
        ),
        patch("sys.stdout", new_callable=io.StringIO) as mock_stdout,
    ):
        main()
        assert mock_stdout.getvalue() == ""
        assert output_path.exists()
        content = output_path.read_text(encoding="utf-8")
        assert "<svg" in content

    # Test output to file in ascii mode to cover newline appending
    output_path_ascii = tmp_path / "output.txt"
    with (
        patch(
            "sys.argv",
            [
                "img2ascii",
                str(img_path),
                "--width",
                "5",
                "--char-aspect",
                "1.0",
                "--mode",
                "ascii",
                "--output",
                str(output_path_ascii),
            ],
        ),
        patch("sys.stdout", new_callable=io.StringIO) as mock_stdout,
    ):
        main()
        assert mock_stdout.getvalue() == ""
        assert output_path_ascii.exists()
        content = output_path_ascii.read_text(encoding="utf-8")
        assert content.endswith("\n")


def test_cli_palette_size(tmp_path):
    img_path = tmp_path / "test.png"
    img = Image.new("RGB", (10, 10), color=(255, 255, 255))
    img.save(img_path)

    with (
        patch(
            "sys.argv",
            [
                "img2ascii",
                str(img_path),
                "--width",
                "5",
                "--mode",
                "pixel",
                "--palette-size",
                "8",
            ],
        ),
        patch("sys.stdout", new_callable=io.StringIO) as mock_stdout,
    ):
        main()
        output = mock_stdout.getvalue()
        assert "<!DOCTYPE html>" in output


def test_cli_edges_missing_scipy(tmp_path):
    img_path = tmp_path / "test.png"
    img = Image.new("RGB", (10, 10), color=(255, 255, 255))
    img.save(img_path)

    with (
        patch(
            "sys.argv",
            [
                "img2ascii",
                str(img_path),
                "--width",
                "5",
                "--edges",
            ],
        ),
        patch("img2ascii.renderers.ascii_art.HAS_SCIPY", False),
        patch("sys.stderr", new_callable=io.StringIO) as mock_stderr,
        pytest.raises(SystemExit) as excinfo,
    ):
        main()
    assert excinfo.value.code == 1
    assert "Optional dependency 'scipy' is required" in mock_stderr.getvalue()


def test_cli_html_mode(tmp_path):
    img_path = tmp_path / "test.png"
    img = Image.new("RGB", (10, 10), color=(255, 255, 255))
    img.save(img_path)

    with (
        patch(
            "sys.argv",
            [
                "img2ascii",
                str(img_path),
                "--width",
                "5",
                "--char-aspect",
                "1.0",
                "--mode",
                "html",
            ],
        ),
        patch("sys.stdout", new_callable=io.StringIO) as mock_stdout,
    ):
        main()
        output = mock_stdout.getvalue()
        assert "<!DOCTYPE html>" in output
        assert "@@@@@" in output  # maps to standard ramp @ for white


@requires_numba
@requires_scipy
def test_cli_html_mode_options(tmp_path):
    img_path = tmp_path / "test.png"
    img = Image.new("RGB", (10, 10), color=(255, 255, 255))
    img.save(img_path)

    with (
        patch(
            "sys.argv",
            [
                "img2ascii",
                str(img_path),
                "--width",
                "5",
                "--mode",
                "html",
                "--bg-color",
                "#123456",
                "--aspect-mode",
                "css",
                "--fast",
                "--edges",
                "--palette-size",
                "16",
            ],
        ),
        patch("sys.stdout", new_callable=io.StringIO) as mock_stdout,
    ):
        main()
        output = mock_stdout.getvalue()
        assert "<!DOCTYPE html>" in output
        assert "background-color: #123456;" in output


def test_cli_luma_method(tmp_path):
    img_path = tmp_path / "test.png"
    img = Image.new("RGB", (10, 10), color=(0, 255, 0))
    img.save(img_path)

    # Test bt709
    with (
        patch(
            "sys.argv",
            [
                "img2ascii",
                str(img_path),
                "--width",
                "5",
                "--luma-method",
                "bt709",
            ],
        ),
        patch("sys.stdout", new_callable=io.StringIO) as mock_stdout,
    ):
        main()
        output = mock_stdout.getvalue()
        assert len(output) > 0

    # Test invalid luma method (handled by argparse's choice list)
    with (
        patch(
            "sys.argv",
            [
                "img2ascii",
                str(img_path),
                "--width",
                "5",
                "--luma-method",
                "invalid",
            ],
        ),
        patch("sys.stderr", new_callable=io.StringIO) as mock_stderr,
        pytest.raises(SystemExit) as excinfo,
    ):
        main()
    assert excinfo.value.code != 0
    assert "invalid choice" in mock_stderr.getvalue()


def test_cli_dither(tmp_path):
    img_path = tmp_path / "test.png"
    img = Image.new("RGB", (20, 20))
    for x in range(20):
        for y in range(20):
            val = int((x / 19) * 255)
            img.putpixel((x, y), (val, val, val))
    img.save(img_path)

    # Test dither flag in ASCII mode
    with (
        patch(
            "sys.argv",
            [
                "img2ascii",
                str(img_path),
                "--width",
                "20",
                "--dither",
            ],
        ),
        patch("sys.stdout", new_callable=io.StringIO) as mock_stdout,
    ):
        main()
        output_dither = mock_stdout.getvalue()

    with (
        patch(
            "sys.argv",
            [
                "img2ascii",
                str(img_path),
                "--width",
                "20",
            ],
        ),
        patch("sys.stdout", new_callable=io.StringIO) as mock_stdout,
    ):
        main()
        output_no_dither = mock_stdout.getvalue()

    assert output_dither != output_no_dither


def test_cli_unwritable_output_path_reports_a_plain_error(tmp_path):
    img_path = tmp_path / "test.png"
    Image.new("RGB", (10, 10), color=(255, 255, 255)).save(img_path)
    missing_dir = tmp_path / "does-not-exist" / "out.txt"

    with (
        patch("sys.argv", ["img2ascii", str(img_path), "-o", str(missing_dir)]),
        patch("sys.stderr", new_callable=io.StringIO) as mock_stderr,
    ):
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 1
        stderr = mock_stderr.getvalue()
        assert "Error:" in stderr
        assert "Unexpected error" not in stderr
