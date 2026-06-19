import io
import sys
from unittest.mock import patch, MagicMock
import pytest
from PIL import Image
from img2ascii.cli.main import main
from img2ascii.exceptions import UnsupportedImageError

def test_cli_help():
    with patch("sys.argv", ["img2ascii", "--help"]), patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 0
        assert "Convert images to ASCII art" in mock_stdout.getvalue()

def test_cli_ascii_mode(tmp_path):
    # Create a small temporary image
    img_path = tmp_path / "test.png"
    img = Image.new("RGB", (10, 10), color=(255, 255, 255))
    img.save(img_path)
    
    with patch("sys.argv", ["img2ascii", str(img_path), "--width", "5", "--char-aspect", "1.0"]), \
         patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
        main()
        # White image -> standard maps to @
        output = mock_stdout.getvalue()
        assert "@@@@@" in output

def test_cli_pixel_mode(tmp_path):
    img_path = tmp_path / "test.png"
    img = Image.new("RGB", (10, 10), color=(255, 255, 255))
    img.save(img_path)
    
    with patch("sys.argv", ["img2ascii", str(img_path), "--width", "5", "--char-aspect", "1.0", "--mode", "pixel"]), \
         patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
        main()
        output = mock_stdout.getvalue()
        assert "<!DOCTYPE html>" in output

def test_cli_stdin():
    # Mock reading from stdin buffer
    img_bytes = io.BytesIO()
    img = Image.new("RGB", (10, 10), color=(255, 255, 255))
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)
    
    with patch("sys.argv", ["img2ascii", "-", "--width", "5", "--char-aspect", "1.0"]), \
         patch("sys.stdin.buffer.read", return_value=img_bytes.read()), \
         patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
        main()
        output = mock_stdout.getvalue()
        assert "@@@@@" in output

def test_cli_stdin_empty():
    with patch("sys.argv", ["img2ascii", "-"]), \
         patch("sys.stdin.buffer.read", return_value=b""), \
         patch("sys.stderr", new_callable=io.StringIO) as mock_stderr:
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 1
        assert "standard input is empty" in mock_stderr.getvalue()

def test_cli_unsupported_image(tmp_path):
    # Write corrupt data to file
    img_path = tmp_path / "corrupt.png"
    img_path.write_bytes(b"not an image")
    
    with patch("sys.argv", ["img2ascii", str(img_path)]), \
         patch("sys.stderr", new_callable=io.StringIO) as mock_stderr:
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 1
        assert "Error:" in mock_stderr.getvalue()

def test_cli_stdin_read_error():
    with patch("sys.argv", ["img2ascii", "-"]), \
         patch("sys.stdin.buffer.read", side_effect=IOError("read error")), \
         patch("sys.stderr", new_callable=io.StringIO) as mock_stderr:
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 1
        assert "Error reading from stdin" in mock_stderr.getvalue()

def test_cli_unexpected_error(tmp_path):
    img_path = tmp_path / "test.png"
    img = Image.new("RGB", (10, 10), color=(255, 255, 255))
    img.save(img_path)
    
    with patch("sys.argv", ["img2ascii", str(img_path)]), \
         patch("img2ascii.cli.main.convert_to_ascii", side_effect=ValueError("unexpected value error")), \
         patch("sys.stderr", new_callable=io.StringIO) as mock_stderr:
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 1
        assert "Unexpected error" in mock_stderr.getvalue()

