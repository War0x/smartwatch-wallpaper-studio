#!/usr/bin/env python3
"""Smartwatch Wallpaper Studio CLI.

Multi-Agent inspired pipeline for downloading, framing, cropping,
and AMOLED-optimizing wallpapers for smartwatches and fitness bands.
"""

import os
import sys
import argparse
from pathlib import Path
from PIL import Image, ImageDraw

from core.profiles import get_profile, load_profiles, format_specs_summary
from core.ingester import load_image
from core.cropper import smart_crop_and_resize
from core.enhancer import crush_blacks, apply_vibrance_and_contrast, apply_clarity


def draw_safe_zone_overlay(img: Image.Image, profile: dict) -> Image.Image:
    """Draw a semi-transparent overlay showing clock safe zones and subject bounds."""
    overlay_img = img.copy().convert("RGBA")
    overlay = Image.new("RGBA", overlay_img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    w, h = overlay_img.size
    sz = profile.get("safe_zones", {})

    # Top clock zone
    if "top_clock" in sz:
        tc = sz["top_clock"]
        draw.rectangle([0, tc["y1"], w, tc["y2"]], fill=(255, 60, 60, 70), outline=(255, 80, 80, 200), width=2)

    # Bottom clock zone
    if "bottom_clock" in sz:
        bc = sz["bottom_clock"]
        draw.rectangle([0, bc["y1"], w, bc["y2"]], fill=(255, 60, 60, 70), outline=(255, 80, 80, 200), width=2)

    # Recommended subject zone
    if "recommended_subject_zone" in sz:
        sb = sz["recommended_subject_zone"]
        draw.rectangle([10, sb["y1"], w - 10, sb["y2"]], fill=(0, 200, 255, 40), outline=(0, 220, 255, 180), width=2)

    combined = Image.alpha_composite(overlay_img, overlay)
    return combined.convert("RGB")


def process_wallpaper(
    input_source: str,
    device_id: str = "redmi_watch_5_lite",
    focus: str = "smart",
    output_dir: str = "output",
    enable_amoled_tune: bool = True,
    generate_safe_zone_preview: bool = False,
    output_name: str = None
) -> dict:
    """Run full pipeline: Ingestion -> Profiling -> Smart Cropping -> AMOLED Tuning -> Export."""
    profile = get_profile(device_id)
    target_w = profile["width"]
    target_h = profile["height"]
    tuning = profile.get("tuning", {})

    print(f"\n[*] Device Selected: {profile['name']} ({profile['brand']})")
    print(f"    Resolution: {target_w}x{target_h} (Aspect Ratio: {profile['aspect_ratio']}) | Panel: {profile['panel']}")

    # 1. Ingestion
    print(f"[*] Ingesting image: {input_source} ...")
    raw_img = load_image(input_source)
    print(f"    Source Image Loaded: {raw_img.width}x{raw_img.height} ({raw_img.format or 'RGB'})")

    # 2. Smart Crop & Resample
    print(f"[*] Cropping & resampling (Focus: '{focus}', Algorithm: Lanczos) ...")
    cropped = smart_crop_and_resize(raw_img, target_w, target_h, focus=focus)

    # 3. AMOLED & Color Tuning
    black_pct = 0.0
    if enable_amoled_tune:
        print("[*] Applying AMOLED display tuning & color enhancement ...")
        t_black = tuning.get("black_point_crush", 14)
        pure_black = tuning.get("pure_black_bg", True)

        if pure_black and t_black > 0:
            enhanced, black_pct = crush_blacks(cropped, threshold=t_black, smooth_range=10)
        else:
            enhanced = cropped

        enhanced = apply_vibrance_and_contrast(
            enhanced,
            contrast_multiplier=tuning.get("contrast_multiplier", 1.15),
            vibrancy_boost=tuning.get("vibrancy_boost", 1.10)
        )
        enhanced = apply_clarity(
            enhanced,
            radius=tuning.get("sharpness_radius", 1.0),
            percent=tuning.get("sharpness_percent", 120),
            threshold=3
        )
    else:
        enhanced = cropped

    # 4. Save Outputs
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    if not output_name:
        if isinstance(input_source, str) and not input_source.startswith("http"):
            stem = Path(input_source).stem
        else:
            stem = "wallpaper"
        base_name = f"{stem}_{target_w}x{target_h}"
    else:
        base_name = output_name

    saved_files = []

    # PNG (Lossless)
    png_file = out_path / f"{base_name}.png"
    enhanced.save(png_file, format="PNG", optimize=True)
    saved_files.append(str(png_file))

    # JPG (High Quality 98%, 4:4:4 chroma subsampling for official Mi Fitness / Wear app compatibility)
    jpg_file = out_path / f"{base_name}.jpg"
    enhanced.save(jpg_file, format="JPEG", quality=98, subsampling=0, optimize=True)
    saved_files.append(str(jpg_file))

    # Optional Safe Zone Preview
    if generate_safe_zone_preview:
        sz_preview = draw_safe_zone_overlay(enhanced, profile)
        preview_file = out_path / f"{base_name}_safezone_preview.png"
        sz_preview.save(preview_file, format="PNG")
        saved_files.append(str(preview_file))

    print("\n[+] Done! Output files generated successfully:")
    for f in saved_files:
        size_kb = os.path.getsize(f) / 1024.0
        print(f"    - {f} ({size_kb:.1f} KB)")

    if black_pct > 0:
        print(f"    AMOLED True-Black: {black_pct:.1f}% pixels at zero power (#000000)")

    return {
        "device": profile["name"],
        "resolution": f"{target_w}x{target_h}",
        "black_pct": round(black_pct, 2),
        "files": saved_files
    }


def main():
    parser = argparse.ArgumentParser(
        description="Smartwatch Wallpaper Studio - Multi-Agent AI pipeline for adapting wallpapers to smartwatch displays."
    )
    parser.add_argument("-i", "--input", help="Path to local image file or direct HTTP(S) image URL")
    parser.add_argument("-d", "--device", default="redmi_watch_5_lite", help="Device name or alias (e.g. 'rw5_lite', 'band9', 'watch_s4')")
    parser.add_argument("-f", "--focus", choices=["smart", "center", "top", "bottom"], default="smart", help="Cropping focus rule")
    parser.add_argument("-o", "--output-dir", default="output", help="Directory where results will be saved")
    parser.add_argument("--name", help="Custom output filename prefix (without extension)")
    parser.add_argument("--no-amoled", action="store_true", help="Disable AMOLED black crush and vibrance boost")
    parser.add_argument("--safe-zone-preview", action="store_true", help="Also generate an overlay image previewing clock safe zones")
    parser.add_argument("--list-devices", action="store_true", help="List all supported smartwatch and band profiles")
    parser.add_argument("--device-info", help="Print full hardware specifications and safe zones for a device")

    args = parser.parse_args()

    if args.list_devices:
        profiles = load_profiles()
        print("\n=== Supported Devices & Displays ===")
        print(f"{'Key':<22} | {'Device Name':<28} | {'Resolution':<11} | {'Panel':<8}")
        print("-" * 75)
        for k, p in profiles.items():
            res_str = f"{p['width']}x{p['height']}"
            print(f"{k:<22} | {p['name']:<28} | {res_str:<11} | {p['panel']:<8}")
        print("\nTip: Use `--device <key_or_alias>` or `--device-info <key>` for details.\n")
        return

    if args.device_info:
        p = get_profile(args.device_info)
        print("\n" + format_specs_summary(p) + "\n")
        return

    if not args.input:
        parser.print_help()
        print("\nError: Please provide an input image with -i / --input, or use --list-devices.")
        sys.exit(1)

    process_wallpaper(
        input_source=args.input,
        device_id=args.device,
        focus=args.focus,
        output_dir=args.output_dir,
        enable_amoled_tune=not args.no_amoled,
        generate_safe_zone_preview=args.safe_zone_preview,
        output_name=args.name
    )


if __name__ == "__main__":
    main()
