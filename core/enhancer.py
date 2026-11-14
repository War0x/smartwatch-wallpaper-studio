"""AMOLED Display Tuning and Color Optimization Engine.
Maintained by @enhancer for the Wallpaper & Watchface Pipeline.
Specifically tuned for Redmi Watch 5 Lite (1.96" AMOLED, 410x502) and customizable for other displays.
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, Tuple
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

try:
    from .profiles import get_profile, format_specs_summary
except (ImportError, ValueError):
    try:
        from profiles import get_profile, format_specs_summary
    except ImportError:
        sys.path.append(os.path.dirname(__file__))
        from profiles import get_profile, format_specs_summary

DEFAULT_OUTPUT_DIRS = [
    r"C:\Users\Warlin\OneDrive - Appod\Escritorio\WatchFaces",
    r"C:\Users\Warlin\.gemini\antigravity\scratch\output",
    r"C:\Users\Warlin\.gemini\antigravity\scratch\wallpaper_pipeline\enhanced",
]


def crush_blacks(img: Image.Image, threshold: int = 14, smooth_range: int = 12) -> Tuple[Image.Image, float]:
    """Crush deep background shadows to pure black (#000000) for true AMOLED battery saving

    and infinite contrast. Uses a smooth toe roll-off to avoid harsh banding/contouring.
    Returns (optimized_image, black_pixel_percentage).
    """
    img_rgb = img.convert("RGB")
    arr = np.array(img_rgb, dtype=np.float32)

    # Per-pixel max brightness across color channels
    max_c = np.maximum(np.maximum(arr[:, :, 0], arr[:, :, 1]), arr[:, :, 2])

    # Pixels strictly below or equal to threshold -> pure 0
    # Pixels between threshold and threshold + smooth_range -> smooth cosine/hermite ease-in
    pure_mask = max_c <= threshold
    smooth_mask = (max_c > threshold) & (max_c < (threshold + smooth_range))

    if smooth_range > 0:
        # Normalized t from 0.0 to 1.0
        t = np.clip((max_c - threshold) / float(smooth_range), 0.0, 1.0)
        # Smoothstep curve: 3*t^2 - 2*t^3
        smooth_factor = 3 * (t ** 2) - 2 * (t ** 3)
        # Scale RGB down towards 0 for pixels in the transition zone
        scale_ratio = smooth_factor
    else:
        scale_ratio = np.ones_like(max_c)

    for c in range(3):
        # Crush completely to 0
        arr[:, :, c] = np.where(pure_mask, 0.0, arr[:, :, c])
        # Apply smooth roll-off to avoid harsh steps
        if smooth_range > 0:
            arr[:, :, c] = np.where(smooth_mask, arr[:, :, c] * scale_ratio, arr[:, :, c])

    arr = np.clip(arr, 0, 255).astype(np.uint8)
    out_img = Image.fromarray(arr, "RGB")

    # Calculate percentage of pure black (#000000) pixels
    pure_black_count = np.sum((arr[:, :, 0] == 0) & (arr[:, :, 1] == 0) & (arr[:, :, 2] == 0))
    total_pixels = arr.shape[0] * arr.shape[1]
    black_pct = (pure_black_count / total_pixels) * 100.0

    return out_img, black_pct


def apply_vibrance_and_contrast(
    img: Image.Image,
    contrast_multiplier: float = 1.15,
    vibrancy_boost: float = 1.10
) -> Image.Image:
    """Enhance contrast and color saturation for punchy AMOLED visual pop."""
    # 1. Vibrance / Saturation boost
    if vibrancy_boost != 1.0:
        color_enhancer = ImageEnhance.Color(img)
        img = color_enhancer.enhance(vibrancy_boost)

    # 2. Contrast enhancement
    if contrast_multiplier != 1.0:
        contrast_enhancer = ImageEnhance.Contrast(img)
        img = contrast_enhancer.enhance(contrast_multiplier)

    return img


def apply_clarity(
    img: Image.Image,
    radius: float = 1.0,
    percent: int = 120,
    threshold: int = 3
) -> Image.Image:
    """Apply high-frequency clarity/sharpening so small micro-details pop on small high-PPI displays."""
    if percent > 0 and radius > 0:
        unsharp = ImageFilter.UnsharpMask(radius=radius, percent=percent, threshold=threshold)
        img = img.filter(unsharp)
    return img


def process_image(
    input_path: str,
    device_id: str = "redmi_watch_5_lite",
    custom_output_dirs: list = None
) -> Dict[str, Any]:
    """Execute full AMOLED enhancement pipeline based on target device profile."""
    in_file = Path(input_path)
    if not in_file.exists():
        raise FileNotFoundError(f"Input image not found: {input_path}")

    profile = get_profile(device_id)
    tuning = profile.get("tuning", {})
    t_black = tuning.get("black_point_crush", 14)
    pure_black = tuning.get("pure_black_bg", True)
    c_mult = tuning.get("contrast_multiplier", 1.15)
    v_boost = tuning.get("vibrancy_boost", 1.10)
    s_radius = tuning.get("sharpness_radius", 1.0)
    s_percent = tuning.get("sharpness_percent", 120)

    # Open base image
    orig_img = Image.open(in_file).convert("RGB")
    w, h = orig_img.size

    # 1. AMOLED Black Crush (if AMOLED profile)
    black_pct = 0.0
    if pure_black and t_black > 0:
        crushed_img, black_pct = crush_blacks(orig_img, threshold=t_black, smooth_range=10)
    else:
        crushed_img = orig_img

    # 2. Vibrancy & Contrast
    tuned_img = apply_vibrance_and_contrast(crushed_img, contrast_multiplier=c_mult, vibrancy_boost=v_boost)

    # 3. Clarity / Sharpening
    final_img = apply_clarity(tuned_img, radius=s_radius, percent=s_percent, threshold=3)

    # Output directories
    out_dirs = custom_output_dirs or DEFAULT_OUTPUT_DIRS
    saved_files = []

    stem = in_file.stem
    # If stem ends with _cropped, clean it or replace with _amoled
    clean_stem = stem.replace("_cropped", "")
    png_name = f"{clean_stem}_amoled.png"
    jpg_name = f"{clean_stem}_amoled.jpg"

    for d in out_dirs:
        out_p = Path(d)
        out_p.mkdir(parents=True, exist_ok=True)

        # 1. Lossless optimized PNG
        png_path = out_p / png_name
        final_img.save(png_path, format="PNG", optimize=True)
        saved_files.append(str(png_path))

        # 2. 98% quality JPG (subsampling=0 for 4:4:4 chroma, pristine fine text/edges)
        jpg_path = out_p / jpg_name
        final_img.save(jpg_path, format="JPEG", quality=98, subsampling=0, optimize=True)
        saved_files.append(str(jpg_path))

    return {
        "device": profile["name"],
        "resolution": f"{w}x{h}",
        "black_crush_threshold": t_black,
        "pure_black_percentage": round(black_pct, 2),
        "contrast_mult": c_mult,
        "vibrancy_boost": v_boost,
        "sharpness": f"radius={s_radius}, percent={s_percent}%",
        "saved_files": saved_files,
        "png_size_bytes": os.path.getsize(saved_files[0]),
        "jpg_size_bytes": os.path.getsize(saved_files[1]),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AMOLED Tuning & Color Optimization Engine")
    parser.add_argument("input", help="Path to cropped image")
    parser.add_argument("--device", default="redmi_watch_5_lite", help="Device profile key or alias")
    args = parser.parse_args()

    res = process_image(args.input, args.device)
    print("\n=== AMOLED Enhancement Complete ===")
    print(f"Target Device: {res['device']} ({res['resolution']})")
    print(f"Pure AMOLED Black Pixels: {res['pure_black_percentage']}% (#000000 zero power)")
    print(f"Contrast Multiplier: {res['contrast_mult']}x")
    print(f"Vibrancy Boost: {res['vibrancy_boost']}x")
    print(f"Clarity/Sharpness: {res['sharpness']}")
    print("Files Saved:")
    for f in res["saved_files"]:
        print(f" - {f}")
