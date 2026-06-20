import time
import cProfile
import pstats
import io
import numpy as np
from PIL import Image
from img2ascii.core.loader import load_image
from img2ascii.core.preprocess import preprocess_image
from img2ascii.core.sampling import sample_grid
from img2ascii.core.aspect import target_grid_size
from img2ascii.renderers.ascii_art import AsciiArtRenderer
from img2ascii.renderers.pixel_exact import PixelExactRenderer


def run_benchmark_for_size(width: int, height: int):
    print("\n==================================================")
    print(
        f"Benchmarking Image Size: {width}x{height} (~{width * height / 1_000_000:.1f}MP)"
    )
    print("==================================================")

    # 1. Create a dummy image in memory and save to bytes
    img = Image.new("RGBA", (width, height), color=(120, 150, 180, 200))
    img_bytes_io = io.BytesIO()
    img.save(img_bytes_io, format="PNG")
    img_bytes = img_bytes_io.getvalue()

    # Measure Loading
    t0 = time.perf_counter()
    rgba_arr = load_image(img_bytes)
    t_load = time.perf_counter() - t0
    print(
        f"Load Image (from PNG bytes): {t_load:.4f}s | shape: {rgba_arr.shape} | dtype: {rgba_arr.dtype}"
    )
    assert rgba_arr.dtype == np.uint8, f"Expected uint8, got {rgba_arr.dtype}"

    # Measure Preprocessing
    t0 = time.perf_counter()
    rgba_prep, luma_prep = preprocess_image(rgba_arr)
    t_preprocess = time.perf_counter() - t0
    print(
        f"Preprocess Image:            {t_preprocess:.4f}s | rgba dtype: {rgba_prep.dtype} | luma dtype: {luma_prep.dtype}"
    )
    assert rgba_prep.dtype == np.float32, f"Expected float32, got {rgba_prep.dtype}"
    assert luma_prep.dtype == np.float32, f"Expected float32, got {luma_prep.dtype}"

    # Target grid dimensions (standard width 80 for normal scaling, but let's test a larger grid e.g. width=400)
    target_cols, target_rows = target_grid_size(
        width, height, out_width=400, char_aspect=2.0
    )
    print(
        f"Target Grid Size:            {target_cols}x{target_rows} ({target_cols * target_rows} cells)"
    )

    # Measure Sampling (fast=False)
    t0 = time.perf_counter()
    rgb_grid, luma_grid, alpha_grid = sample_grid(
        rgba_prep, luma_prep, target_cols, target_rows, fast=False
    )
    t_sample_slow = time.perf_counter() - t0
    print(
        f"Sampling (fast=False):       {t_sample_slow:.4f}s | rgb dtype: {rgb_grid.dtype}"
    )

    # Try JIT if possible
    try:
        t0 = time.perf_counter()
        rgb_grid_fast, luma_grid_fast, alpha_grid_fast = sample_grid(
            rgba_prep, luma_prep, target_cols, target_rows, fast=True
        )
        t_sample_fast = time.perf_counter() - t0
        print(f"Sampling (fast=True JIT):    {t_sample_fast:.4f}s")
    except Exception as e:
        print(f"Sampling (fast=True JIT):    N/A ({e})")

    # Measure Rendering (Ascii)
    ascii_renderer = AsciiArtRenderer(
        ramp="standard", auto_contrast=True, use_edges=False
    )
    t0 = time.perf_counter()
    ascii_renderer.render(rgb_grid, luma_grid, alpha_grid)
    t_render_ascii = time.perf_counter() - t0
    print(f"Render Ascii (no edges):     {t_render_ascii:.4f}s")

    # Measure Rendering (Ascii + edges)
    try:
        ascii_edges_renderer = AsciiArtRenderer(
            ramp="standard", auto_contrast=True, use_edges=True
        )
        t0 = time.perf_counter()
        ascii_edges_renderer.render(rgb_grid, luma_grid, alpha_grid)
        t_render_ascii_edges = time.perf_counter() - t0
        print(f"Render Ascii (with edges):   {t_render_ascii_edges:.4f}s")
    except Exception as e:
        print(f"Render Ascii (with edges):   N/A ({e})")

    # Measure Rendering (Pixel HTML)
    pixel_renderer = PixelExactRenderer(
        glyph="█", bg_color="#000000", aspect_mode="resize"
    )
    t0 = time.perf_counter()
    pixel_out = pixel_renderer.render(rgb_grid, luma_grid, alpha_grid)
    t_render_pixel = time.perf_counter() - t0
    print(
        f"Render Pixel HTML:           {t_render_pixel:.4f}s | HTML size: {len(pixel_out) / 1024:.2f} KB"
    )


def run_cprofile():
    print("\n==================================================")
    print("Running cProfile on 1080p Image Pipeline")
    print("==================================================")

    img = Image.new("RGBA", (1920, 1080), color=(120, 150, 180, 200))
    img_bytes_io = io.BytesIO()
    img.save(img_bytes_io, format="PNG")
    img_bytes = img_bytes_io.getvalue()

    pr = cProfile.Profile()
    pr.enable()

    rgba_arr = load_image(img_bytes)
    rgba_prep, luma_prep = preprocess_image(rgba_arr)
    target_cols, target_rows = target_grid_size(
        1920, 1080, out_width=400, char_aspect=2.0
    )
    rgb_grid, luma_grid, alpha_grid = sample_grid(
        rgba_prep, luma_prep, target_cols, target_rows, fast=False
    )
    ascii_renderer = AsciiArtRenderer(
        ramp="standard", auto_contrast=True, use_edges=True
    )
    ascii_renderer.render(rgb_grid, luma_grid, alpha_grid)

    pr.disable()
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats("cumulative")
    ps.print_stats(30)
    print(s.getvalue())


if __name__ == "__main__":
    run_benchmark_for_size(512, 512)
    run_benchmark_for_size(1920, 1080)
    run_benchmark_for_size(4000, 3000)
    run_cprofile()
