"""Device Specifications and Hardware Constraints Registry for Smartwatches and Fitness Bands.
Maintained by @profiler for the Wallpaper & Watchface Pipeline.
"""

import json
import os
import sys
from typing import Dict, Any, Optional

PROFILES_PATH = os.path.join(os.path.dirname(__file__), "profiles.json")


def load_profiles() -> Dict[str, Any]:
    with open(PROFILES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_profile(device_identifier: str = "default") -> Dict[str, Any]:
    """Retrieve device specification profile by key or alias (case-insensitive)."""
    profiles = load_profiles()
    key_norm = device_identifier.strip().lower().replace("-", "_").replace(" ", "_")

    if key_norm in profiles:
        return profiles[key_norm]

    # Search in aliases
    for p_key, p_data in profiles.items():
        if key_norm == p_key:
            return p_data
        aliases = [a.lower() for a in p_data.get("aliases", [])]
        if key_norm in aliases:
            return p_data
        if key_norm in p_data.get("name", "").lower():
            return p_data

    # Fallback to default
    return profiles["redmi_watch_5_lite"]


def format_specs_summary(profile: Dict[str, Any]) -> str:
    """Format specifications for board posting and agent-to-agent communication."""
    t = profile["tuning"]
    sz = profile["safe_zones"]
    return (
        f"Target Device: {profile['name']} ({profile['brand']})\n"
        f"- Resolution: {profile['width']}x{profile['height']} (Ratio: {profile['aspect_ratio']})\n"
        f"- Screen Shape: {profile['screen_shape']} (Radius: {profile['corner_radius']}px)\n"
        f"- Display Panel: {profile['panel']} (Diagonal: {profile['screen_diagonal_inches']}\", {profile['ppi']} PPI)\n"
        f"- Black Point / Tone Curve: {'AMOLED True-Black (crush <= ' + str(t['black_point_crush']) + ' RGB)' if t['pure_black_bg'] else 'LCD Non-crushing (lift floor +' + str(t.get('black_floor_lift', 5)) + ' RGB)'}\n"
        f"- Enhancements: Contrast x{t['contrast_multiplier']}, Vibrancy x{t['vibrancy_boost']}, Sharpness radius {t['sharpness_radius']} ({t['sharpness_percent']}%)\n"
        f"- Clock Safe Zones: Top {sz.get('top_clock', {}).get('y1', 0)}-{sz.get('top_clock', {}).get('y2', 0)}px | Bottom {sz.get('bottom_clock', {}).get('y1', 0)}-{sz.get('bottom_clock', {}).get('y2', 0)}px\n"
        f"- Recommended Subject Zone: Y={sz.get('recommended_subject_zone', {}).get('y1', 0)} to {sz.get('recommended_subject_zone', {}).get('y2', 0)} (Margin: {sz['margin_padding']}px)"
    )


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "default"
    prof = get_profile(target)
    print(format_specs_summary(prof))
