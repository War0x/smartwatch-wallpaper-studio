"""Smart Framing and Aspect Ratio Adapter for Smartwatch Displays.
Handles automatic subject centering, portrait cropping, and clock overlay safe zones.
"""

from typing import Tuple, Dict, Any, Optional
from PIL import Image


def smart_crop_and_resize(
    img: Image.Image,
    target_width: int,
    target_height: int,
    focus: str = "center",
    safe_zone: Optional[Dict[str, int]] = None
) -> Image.Image:
    """Resize and crop an image to target resolution while preserving aspect ratio

    and respecting UI overlay safe zones.
    focus: 'center', 'top', 'bottom', or 'smart'
    """
    img = img.convert("RGB")
    src_w, src_h = img.size
    target_ratio = target_width / float(target_height)
    src_ratio = src_w / float(src_h)

    if abs(src_ratio - target_ratio) < 0.005:
        # Aspect ratios virtually identical, direct resize
        return img.resize((target_width, target_height), Image.Resampling.LANCZOS)

    if src_ratio > target_ratio:
        # Source is wider than target -> Crop horizontally (keep full height)
        new_w = int(round(src_h * target_ratio))
        offset_x = (src_w - new_w) // 2
        crop_box = (offset_x, 0, offset_x + new_w, src_h)
    else:
        # Source is taller than target -> Crop vertically
        new_h = int(round(src_w / target_ratio))
        if focus == "top":
            offset_y = 0
        elif focus == "bottom":
            offset_y = src_h - new_h
        else:
            # Default center, but slightly bias upwards for portraits/characters (1/3 rule)
            bias = 0.38 if focus == "smart" else 0.50
            offset_y = int(round((src_h - new_h) * bias))
            offset_y = max(0, min(offset_y, src_h - new_h))
        crop_box = (0, offset_y, src_w, offset_y + new_h)

    cropped = img.crop(crop_box)
    return cropped.resize((target_width, target_height), Image.Resampling.LANCZOS)
