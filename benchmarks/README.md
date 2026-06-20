# Performance Benchmark & Profiling Report

This directory contains the benchmark runner and documents the execution times and memory characteristics of the `img2ascii` pipeline stages.

## System & Environment
- **Python Version**: 3.12.3
- **OS**: Linux
- **CPU**: Intel/AMD x86_64 CPU (Local Test System)
- **Optional Dependencies**: `scipy` (edges), `numba` (fast mode JIT)

## Execution Times (Latency)

We benchmarked three typical image resolutions:
1. **0.3MP** (512x512)
2. **2.1MP** (1920x1080 - Full HD)
3. **12.0MP** (4000x3000 - Mobile Photo)

All runs below target a sampled text grid of width **400 columns**.

| Stage | 0.3MP (512x512) | 2.1MP (1920x1080) | 12.0MP (4000x3000) |
| :--- | :--- | :--- | :--- |
| **Load Image** (from PNG bytes) | ~0.005s | ~0.038s | ~0.148s |
| **Preprocess** (color/luma) | ~0.005s | ~0.091s | ~0.332s |
| **Sampling** (slow, NumPy mean) | ~0.018s | ~0.201s | ~0.436s |
| **Sampling** (fast, JIT Numba) | ~0.225s (JIT overhead first run) | ~0.140s | ~0.265s |
| **Render ASCII** (no edges) | ~0.023s | ~0.012s | ~0.010s |
| **Render ASCII** (with edges) | ~0.040s | ~0.013s | ~0.012s |
| **Render Pixel HTML** | ~0.087s | ~0.047s | ~0.043s |
| **Total Pipeline (ASCII)** | **~0.051s** | **~0.342s** | **~0.926s** |

*Note: Total Pipeline includes loading, preprocessing, sampling (slow), and rendering ascii without edges.*

## Memory Characteristics & Data Types

We verified the data types of arrays at each stage of the pipeline to ensure that no double-precision float (`float64`) overhead is introduced.
- **`load_image` output array**: `uint8` (RGBA, shape: `(H, W, 4)`) - minimal memory foot print.
- **`preprocess_image` output RGBA array**: `float32` (shape: `(H, W, 4)`) - single precision.
- **`preprocess_image` output luma array**: `float32` (shape: `(H, W)`) - single precision.
- **`sample_grid` output RGB/Luma/Alpha arrays**: `float32` (shape: `(Grid_H, Grid_W, 3)`/`(Grid_H, Grid_W)`) - lightweight representation.

No double-precision `float64` types are present in any of the hot-path computations.

## Profile Analysis (1080p Image)

A profile of the pipeline running on a Full HD (1920x1080) image shows that:
1. **Pillow Resize / NumPy Mean** dominates the sampling stage (`sample_grid`).
2. There are **no Python-level per-pixel loops** in the hot paths.
3. Preprocessing (`preprocess_image`) relies on vectorized array mathematics (multiplications and additions) which executes in less than 91ms on a 2.1MP image.
