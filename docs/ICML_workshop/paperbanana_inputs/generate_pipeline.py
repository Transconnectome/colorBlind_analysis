#!/usr/bin/env python3
"""
Automated ICML figure generation pipeline.
Diagrams via Gemini API (Nano Banana) + Charts via Matplotlib.

Supports two backends:
  - google: Free via Google AI Studio (gemini-2.5-flash-image)
  - openrouter: Paid via OpenRouter (gemini-3-pro-image-preview, higher quality)

Setup:
    # Option A: Google AI (free)
    export GOOGLE_API_KEY="your-key-from-aistudio.google.com"

    # Option B: OpenRouter (better quality, ~$0.05/image)
    export OPENROUTER_API_KEY="your-key-from-openrouter.ai"

Usage:
    conda activate srm
    python generate_pipeline.py                     # all figures, google backend
    python generate_pipeline.py --backend openrouter # all, openrouter backend
    python generate_pipeline.py --only fig1a         # single figure
    python generate_pipeline.py --only fig2
    python generate_pipeline.py --only charts        # matplotlib only (no API)
    python generate_pipeline.py --refine fig1_panel_a.png "Make arrows thinner"
"""
import os
import sys
import json
import time
import base64
import argparse
import subprocess
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent


def load_dotenv():
    """Load .env file from script directory or parents."""
    for parent in [SCRIPT_DIR] + list(SCRIPT_DIR.parents):
        env_file = parent / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    val = val.strip().strip("'\"")
                    if val and val not in ("여기에_키_붙여넣기",):
                        os.environ.setdefault(key.strip(), val)
            break

load_dotenv()


# ═══════════════════════════════════════════════════
#  Backend: Google AI Studio (free tier)
# ═══════════════════════════════════════════════════

def google_generate(prompt, output_path, aspect_ratio="4:3"):
    """Generate image via Google AI Studio API (free)."""
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("  ERROR: GOOGLE_API_KEY not set")
        print("  Get free: https://aistudio.google.com/apikey")
        return False

    from google import genai
    from google.genai import types
    from PIL import Image
    import io

    client = genai.Client(api_key=api_key)

    try:
        print(f"  [google] gemini-2.5-flash-image, {aspect_ratio}... ", end="", flush=True)
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(aspect_ratio=aspect_ratio),
            ),
        )
        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    img = Image.open(io.BytesIO(part.inline_data.data))
                    img.save(str(output_path))
                    print(f"OK -> {output_path.name}")
                    return True
        print("No image in response")
        return False

    except Exception as e:
        err = str(e)
        print(f"ERROR: {err[:120]}")
        if "429" in err or "RESOURCE_EXHAUSTED" in err:
            print("  Rate limited. Wait 60s or use --backend openrouter")
        return False


def google_refine(image_path, instruction, output_path):
    """Edit existing image via Google AI Studio API."""
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return False

    from google import genai
    from google.genai import types
    from PIL import Image
    import io

    client = genai.Client(api_key=api_key)

    img = Image.open(image_path)
    print(f"  [google] Refining {image_path.name}... ", end="", flush=True)

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=[instruction, img],
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
            ),
        )
        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    out_img = Image.open(io.BytesIO(part.inline_data.data))
                    out_img.save(str(output_path))
                    print(f"OK -> {output_path.name}")
                    return True
        print("No image in response")
        return False
    except Exception as e:
        print(f"ERROR: {str(e)[:120]}")
        return False


# ═══════════════════════════════════════════════════
#  Backend: OpenRouter (paid, higher quality)
# ═══════════════════════════════════════════════════

def openrouter_generate(prompt, output_path, model="google/gemini-3-pro-image-preview"):
    """Generate image via OpenRouter API."""
    import requests

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        # Check .env files
        for parent in [Path.cwd()] + list(Path.cwd().parents):
            env_file = parent / ".env"
            if env_file.exists():
                for line in env_file.read_text().splitlines():
                    if line.startswith("OPENROUTER_API_KEY="):
                        api_key = line.split("=", 1)[1].strip().strip("'\"")
                        break
            if api_key:
                break

    if not api_key:
        print("  ERROR: OPENROUTER_API_KEY not set")
        print("  Get key: https://openrouter.ai/keys")
        return False

    print(f"  [openrouter] {model}... ", end="", flush=True)

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "modalities": ["image", "text"],
            },
            timeout=120,
        )

        if response.status_code != 200:
            print(f"ERROR ({response.status_code}): {response.text[:100]}")
            return False

        result = response.json()
        if result.get("choices"):
            msg = result["choices"][0]["message"]
            images = msg.get("images", [])
            if not images and isinstance(msg.get("content"), list):
                images = [p for p in msg["content"]
                          if isinstance(p, dict) and p.get("type") == "image"]

            if images:
                img_data = images[0]
                url = img_data.get("image_url", {}).get("url") or img_data.get("url", "")
                if "," in url:
                    url = url.split(",", 1)[1]
                with open(output_path, "wb") as f:
                    f.write(base64.b64decode(url))
                print(f"OK -> {output_path.name}")
                return True

        print("No image in response")
        return False

    except Exception as e:
        print(f"ERROR: {str(e)[:120]}")
        return False


# ═══════════════════════════════════════════════════
#  Prompts
# ═══════════════════════════════════════════════════

PROMPT_FIG1A = """Create a compact horizontal pipeline diagram for an academic paper (ICML proceedings style).

4 stages connected left-to-right by thin arrows on a single row:

Stage 1 "Structured Representation": A rounded rectangle containing a small brain cortex icon with 8 colored dots (red, orange, yellow, green, cyan, blue, purple, magenta) arranged in a small circle. Below: "fMRI hV4, K=3 basis".

Stage 2 "LOCO Vulnerability": A rounded rectangle containing a tiny 8-bar chart silhouette (some bars up, some down). Below: "v in R^8".

Stage 3 "Distortion Inference": A rounded rectangle with two sub-labels: "retinal: delta-lambda, g" and "cortical: beta_s, beta_c". Below: "1-2 DOF grid search".

Stage 4 "Correction Assessment": A rounded rectangle with a checkmark icon. Below: "pre-image filter".

Arrow labels (small, above each arrow): "LOCO CV", "composite loss", "inversion".

Style: Clean academic, white background, sans-serif font. No gradients, no shadows, no 3D. Box fill #EBF5FB, border #3498DB. Arrows #555555. All text clearly legible and correctly spelled."""

PROMPT_FIG2 = """Create a scientific diagram showing geometric distortion and correction in opponent color space for an academic paper.

3 panels side by side horizontally:

LEFT "(a) HC template": 8 colored dots (red, orange, yellow, green, cyan, blue, purple, magenta) evenly spaced on a dashed gray circle. Axes: horizontal "L-M", vertical "S-(L+M)". Clean symmetric.

CENTER "(b) CVD observed": Same 8 dots but distorted — red-green axis compressed, blue-yellow preserved. Ghost dots (gray unfilled) show original HC positions. Small dark arrows from ghost to actual positions. Overall shape is elongated ellipse.

RIGHT "(c) After correction": Dots partially restored toward circle. Green arrows showing correction. Some dots nearly on circle (solid), others still off (dashed outline).

Style: Clean academic, white background, sans-serif. No gradients, no shadows. Panel labels (a)(b)(c) bold above each. All text correctly spelled."""


# ═══════════════════════════════════════════════════
#  Pipeline
# ═══════════════════════════════════════════════════

def run_charts():
    """Run Matplotlib chart scripts."""
    os.chdir(SCRIPT_DIR)
    for script in ["fig1_panels_bcd.py", "fig_hc_specificity.py"]:
        if (SCRIPT_DIR / script).exists():
            print(f"\n[Chart] {script}")
            r = subprocess.run([sys.executable, script], capture_output=True, text=True)
            print(f"  {r.stdout.strip()}" if r.returncode == 0 else f"  ERROR: {r.stderr.strip()}")


def run_diagram(name, prompt, output_name, aspect_ratio, backend):
    """Generate a diagram with the selected backend."""
    os.chdir(SCRIPT_DIR)
    output = SCRIPT_DIR / output_name
    print(f"\n[Diagram] {name}")

    if backend == "google":
        ok = google_generate(prompt, output, aspect_ratio)
    else:
        ok = openrouter_generate(prompt, output)

    if not ok:
        print(f"  FALLBACK: Copy prompt below into gemini.google.com:")
        print(f"  -> {SCRIPT_DIR / (output_name.replace('.png', '_prompt.txt'))}")
        # Save prompt as txt for manual fallback
        (SCRIPT_DIR / (output_name.replace(".png", "_prompt.txt"))).write_text(prompt)

    return ok


def run_refine(image_path, instruction, backend):
    """Refine an existing image."""
    image_path = Path(image_path)
    if not image_path.exists():
        print(f"ERROR: {image_path} not found")
        return False

    output = image_path.with_name(image_path.stem + "_v2" + image_path.suffix)
    print(f"\n[Refine] {image_path.name} -> {output.name}")

    if backend == "google":
        return google_refine(image_path, instruction, output)
    else:
        print("  OpenRouter editing: use --backend google for refinement")
        return False


def main():
    parser = argparse.ArgumentParser(description="ICML Figure Pipeline")
    parser.add_argument("--only", choices=["fig1a", "fig2", "charts", "all"],
                        default="all")
    parser.add_argument("--backend", choices=["google", "openrouter"],
                        default="google",
                        help="google=free (2.5 Flash), openrouter=paid (3 Pro)")
    parser.add_argument("--refine", nargs=2, metavar=("IMAGE", "INSTRUCTION"),
                        help="Refine existing image: --refine fig1.png 'Make arrows thinner'")
    args = parser.parse_args()

    print("=" * 55)
    print(f"  ICML Figure Pipeline  |  backend: {args.backend}")
    print("=" * 55)

    # Refine mode
    if args.refine:
        run_refine(args.refine[0], args.refine[1], args.backend)
        return

    # Charts
    if args.only in ("all", "charts"):
        run_charts()

    # Diagrams
    if args.only in ("all", "fig1a"):
        run_diagram("Fig 1(a) Pipeline", PROMPT_FIG1A,
                    "fig1_panel_a.png", "4:3", args.backend)
        time.sleep(5)

    if args.only in ("all", "fig2"):
        run_diagram("Fig 2 Geometric Collapse", PROMPT_FIG2,
                    "fig2_collapse.png", "16:9", args.backend)

    # Summary
    print("\n" + "=" * 55)
    print("  Output files:")
    os.chdir(SCRIPT_DIR)
    for f in sorted(SCRIPT_DIR.glob("fig*.*")):
        if f.suffix in (".png", ".pdf"):
            print(f"    {f.name:35s} {f.stat().st_size/1024:6.0f} KB")

    print("\n  Next: Open PowerPoint -> Claude add-in -> compose panels")
    print("=" * 55)


if __name__ == "__main__":
    main()
