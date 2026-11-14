"""Smart Framing and Aspect Ratio Adapter for Smartwatch Displays.
Handles automatic subject centering, portrait cropping, and clock overlay safe zones.
"""

from typing import Tuple, Dict, Any, Optional
import numpy as np
from PIL import Image, ImageFilter, ImageDraw


def detect_focal_point(img: Image.Image) -> Tuple[float, float, Dict[str, Any]]:
    """Detect the main subject or focal center using gradient energy, edge saliency,

    and warm skin/character color heuristics.
    Returns (focal_x, focal_y, metrics_dict) in normalized coordinates [0.0, 1.0].
    """
    analysis_size = (320, int(320 * (img.height / max(1, img.width))))
    analysis_size = (max(64, analysis_size[0]), max(64, analysis_size[1]))
    thumb = img.convert("RGB").resize(analysis_size, Image.Resampling.BILINEAR)
    arr = np.array(thumb, dtype=np.float32)

    h, w, _ = arr.shape

    # Luminance gradient energy
    gray = 0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]
    gy, gx = np.gradient(gray)
    gradient_energy = np.sqrt(gx**2 + gy**2)

    # Skin tone and character warm feature detection heuristic
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    skin_mask = (r > 80) & (g > 40) & (b > 20) & (r > g) & (g > b) & (np.abs(r - g) > 12)
    skin_boost = np.where(skin_mask, 1.8, 1.0)

    # Color contrast
    perimeter = np.concatenate([arr[0, :, :], arr[-1, :, :], arr[:, 0, :], arr[:, -1, :]], axis=0)
    bg_color = np.mean(perimeter, axis=0)
    color_diff = np.linalg.norm(arr - bg_color, axis=2)

    saliency = (gradient_energy * 0.6 + color_diff * 0.4) * skin_boost

    # Spatial prior
    y_coords, x_coords = np.ogrid[:h, :w]
    cy, cx = h / 2.0, w / 2.0
    dist_sq = ((x_coords - cx) / cx)**2 + ((y_coords - cy) / cy)**2
    spatial_prior = np.exp(-0.5 * dist_sq)
    saliency = saliency * (0.6 + 0.4 * spatial_prior)

    threshold = np.percentile(saliency, 75)
    salient_mask = saliency >= threshold
    salient_energy = np.where(salient_mask, saliency, 0.0)
    total_energy = np.sum(salient_energy)

    if total_energy > 1e-5:
        norm_fy = float(np.sum(y_coords * salient_energy) / (total_energy * h))
        norm_fx = float(np.sum(x_coords * salient_energy) / (total_energy * w))
    else:
        norm_fx, norm_fy = 0.5, 0.42

    norm_fx = max(0.1, min(0.9, norm_fx))
    norm_fy = max(0.1, min(0.9, norm_fy))

    metrics = {
        "norm_fx": round(norm_fx, 4),
        "norm_fy": round(norm_fy, 4),
        "has_skin_tones": bool(np.mean(skin_mask) > 0.03),
        "edge_density": float(np.mean(gradient_energy)),
    }
    return norm_fx, norm_fy, metrics


def smart_crop_and_resize(
    img: Image.Image,
    target_width: int,
    target_height: int,
    focus: str = "smart",
    safe_zone: Optional[Dict[str, Any]] = None
) -> Image.Image:
    """Resize and crop an image to target resolution while preserving aspect ratio

    and respecting UI overlay safe zones.
    focus: 'smart', 'center', 'top', 'bottom', 'extend_black', or 'extend_blur'
    """
    img = img.convert("RGB")
    src_w, src_h = img.size
    target_ratio = target_width / float(target_height)
    src_ratio = src_w / float(src_h)

    # Canvas extension modes
    if focus in ("extend_black", "extend_blur"):
        scale = min(target_width / src_w, target_height / src_h)
        scaled_w = int(round(src_w * scale))
        scaled_h = int(round(src_h * scale))
        scaled_img = img.resize((scaled_w, scaled_h), Image.Resampling.LANCZOS)

        if focus == "extend_black":
            canvas = Image.new("RGB", (target_width, target_height), (0, 0, 0))
        else:
            backdrop = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
            backdrop = backdrop.filter(ImageFilter.GaussianBlur(radius=25))
            backdrop = backdrop.point(lambda p: int(p * 0.4))
            canvas = backdrop

        pos_x = (target_width - scaled_w) // 2
        pos_y = (target_height - scaled_h) // 2
        canvas.paste(scaled_img, (pos_x, pos_y))
        return canvas

    if abs(src_ratio - target_ratio) < 0.005:
        return img.resize((target_width, target_height), Image.Resampling.LANCZOS)

    safe_target_fy_ratio = 0.44
    if safe_zone and "recommended_subject_zone" in safe_zone:
        sz = safe_zone["recommended_subject_zone"]
        safe_target_fy_ratio = ((sz.get("y1", 130) + sz.get("y2", 470)) / 2.0) / float(target_height)

    if src_ratio > target_ratio:
        # Source is wider than target -> Crop horizontally (keep full height)
        crop_h = src_h
        crop_w = int(round(src_h * target_ratio))
        if focus == "smart":
            norm_fx, _, _ = detect_focal_point(img)
            offset_x = int(round(norm_fx * src_w - crop_w / 2.0))
        else:
            offset_x = (src_w - crop_w) // 2

        offset_x = max(0, min(offset_x, src_w - crop_w))
        crop_box = (offset_x, 0, offset_x + crop_w, crop_h)
    else:
        # Source is taller than target -> Crop vertically
        crop_w = src_w
        crop_h = int(round(src_w / target_ratio))
        if focus == "top":
            offset_y = 0
        elif focus == "bottom":
            offset_y = src_h - crop_h
        elif focus == "smart":
            _, norm_fy, _ = detect_focal_point(img)
            offset_y = int(round(norm_fy * src_h - (crop_h * safe_target_fy_ratio)))
            offset_y = max(0, min(offset_y, src_h - crop_h))
        else:
            offset_y = (src_h - crop_h) // 2

        crop_box = (0, offset_y, crop_w, offset_y + crop_h)

    cropped = img.crop(crop_box)
    return cropped.resize((target_width, target_height), Image.Resampling.LANCZOS)
