"""
Crop candidate images to Tier-1 (c1–c8) only.

Usage:
    python scripts/annotate_candidates.py
Output:
    candidates/cropped_canonical.png
    candidates/cropped_primary.png
    candidates/cropped_cycle14.png
"""

from PIL import Image
import numpy as np
import os


def detect_tier1_bounds(img_array, probe_x1=260, probe_x2=380):
    """Return (y_top, y_bottom) that encloses c1–c8 rows plus the column header."""
    strip = img_array[:, probe_x1:probe_x2, :3].astype(float)
    brightness = np.mean(strip, axis=(1, 2))
    std        = np.std(strip, axis=(1, 2))

    # Collect color-block segments (brightness not almost-white)
    segs, state, seg_start = [], "white", 150
    for y in range(150, min(1200, img_array.shape[0])):
        cur = "white" if brightness[y] > 245 and std[y] < 15 else "color"
        if cur != state:
            segs.append((state, seg_start, y - 1))
            state, seg_start = cur, y
    segs.append((state, seg_start, min(1199, img_array.shape[0] - 1)))

    color_segs = [(y0, y1) for kind, y0, y1 in segs if kind == "color" and (y1 - y0) > 30]
    # Skip the column-header mini-row (first entry, ~24 px tall)
    header_seg = color_segs[0] if color_segs and (color_segs[0][1] - color_segs[0][0]) < 35 else None
    main_segs  = [s for s in color_segs if s is not header_seg][:8]

    if not main_segs:
        return 150, min(900, img_array.shape[0] - 1)

    # Extend upward enough to capture the column-header row (white area above first row)
    first_row_top = (header_seg[0] if header_seg else main_segs[0][0])
    # Walk up to include the nearest white block (column headers live there)
    scan_top = max(0, first_row_top - 80)
    y_top    = scan_top
    y_bottom = main_segs[-1][1] + 10
    return max(0, y_top), min(img_array.shape[0] - 1, y_bottom)


def crop_to_tier1(src_path: str, dst_path: str):
    img = Image.open(src_path).convert("RGBA")
    arr = np.array(img)
    y0, y1 = detect_tier1_bounds(arr)
    cropped = img.crop((0, y0, img.width, y1)).convert("RGB")
    cropped.save(dst_path, dpi=(150, 150))
    print(f"  {os.path.basename(src_path)} → cropped y={y0}:{y1}  →  {dst_path}")


if __name__ == "__main__":
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cand = os.path.join(base, "candidates")

    for src, dst in [
        ("canonical.png", "cropped_canonical.png"),
        ("primary.png",   "cropped_primary.png"),
        ("cycle14.png",   "cropped_cycle14.png"),
    ]:
        crop_to_tier1(os.path.join(cand, src), os.path.join(cand, dst))

    print("\nDone. Cropped files saved in candidates/")
