from __future__ import annotations

import os
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from huggingface_hub import InferenceClient

from app.config import get_settings


# ============================================================
# SETTINGS
# ============================================================

settings = get_settings()

BASE_DIR = Path(__file__).resolve().parents[2]

OUTPUT_DIR = BASE_DIR / "static" / "panels"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


IMAGE_PROVIDER = os.getenv(
    "IMAGE_PROVIDER",
    getattr(settings, "image_provider", "hf"),
).lower()

HF_TOKEN = os.getenv(
    "HF_TOKEN",
    getattr(settings, "hf_token", ""),
)

HF_IMAGE_MODEL = os.getenv(
    "HF_IMAGE_MODEL",
    getattr(
        settings,
        "hf_image_model",
        "black-forest-labs/FLUX.1-schnell",
    ),
)


# ============================================================
# FONT LOADER
# ============================================================

def _get_font(size: int, bold: bool = False):

    if bold:
        font_candidates = [
            # Windows
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/segoeuib.ttf",

            # Linux / Render
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",

            # macOS
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/System/Library/Fonts/Supplemental/Helvetica Bold.ttf",
        ]
    else:
        font_candidates = [
            # Windows
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/segoeui.ttf",

            # Linux / Render
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",

            # macOS
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/System/Library/Fonts/Supplemental/Helvetica.ttf",
        ]

    for font_path in font_candidates:

        if os.path.exists(font_path):

            try:
                return ImageFont.truetype(
                    font_path,
                    size,
                )

            except Exception:
                pass

    return ImageFont.load_default()


# ============================================================
# PROMPT VALIDATION
# ============================================================

def _validate_prompt(prompt: str) -> str:

    if prompt is None:
        raise ValueError(
            "Image prompt cannot be None."
        )

    if not isinstance(prompt, str):
        raise TypeError(
            "Image prompt must be a string."
        )

    prompt = prompt.strip()

    if not prompt:
        raise ValueError(
            "Image prompt cannot be empty."
        )

    # Avoid excessively large requests
    if len(prompt) > 4000:
        prompt = prompt[:4000]

    return prompt


# ============================================================
# BUILD THE FINAL AI PROMPT
# ============================================================

def _build_image_prompt(prompt: str) -> str:

    prompt = _validate_prompt(prompt)

    final_prompt = f"""
Create a single detailed comic-book panel illustration.

IMPORTANT:
The scene described below is the MAIN CONTENT of the image.
Follow it closely.

USER SCENE:
{prompt}

VISUAL REQUIREMENTS:
- Show the exact characters described in the scene.
- Show the exact action described in the scene.
- Show the location/environment described in the scene.
- Preserve important objects mentioned in the scene.
- Make the character appearance visually clear.
- Make the background strongly reflect the described setting.
- Use a colorful professional comic-book illustration style.
- Use expressive characters and cinematic composition.
- Use detailed environment/background elements.
- Use dramatic but natural lighting.
- Make the image look like one panel from a finished comic book.
- Landscape composition.
- 4:3 style composition.

DO NOT:
- add speech bubbles
- add dialogue text
- add captions
- add subtitles
- add written words
- add logos
- add watermarks
- add UI elements
- add borders around the image

The image should contain visual storytelling only.
"""

    return final_prompt.strip()


# ============================================================
# LOCAL PLACEHOLDER
# ============================================================

def _placeholder(
    panel_number: int,
    prompt: str,
) -> str:

    filename = f"panel_{panel_number}.png"

    image_path = OUTPUT_DIR / filename

    width = 1024
    height = 768

    image = Image.new(
        "RGB",
        (width, height),
        (245, 241, 234),
    )

    draw = ImageDraw.Draw(image)

    # --------------------------------------------------------
    # Header
    # --------------------------------------------------------

    draw.rectangle(
        [0, 0, width, 100],
        fill=(25, 25, 25),
    )

    title_font = _get_font(
        40,
        bold=True,
    )

    panel_font = _get_font(
        28,
        bold=True,
    )

    text_font = _get_font(
        20,
    )

    draw.text(
        (40, 25),
        "COMICCRAFT",
        fill=(255, 255, 255),
        font=title_font,
    )

    draw.text(
        (40, 125),
        f"PANEL {panel_number}",
        fill=(30, 30, 30),
        font=panel_font,
    )

    # --------------------------------------------------------
    # Comic panel area
    # --------------------------------------------------------

    margin = 45

    draw.rounded_rectangle(
        [
            margin,
            180,
            width - margin,
            630,
        ],
        radius=30,
        fill=(255, 255, 255),
        outline=(60, 60, 60),
        width=4,
    )

    # Sun

    draw.ellipse(
        [730, 220, 850, 340],
        fill=(255, 200, 70),
        outline=(80, 60, 20),
        width=4,
    )

    # Mountains

    draw.polygon(
        [
            (80, 575),
            (280, 390),
            (450, 575),
        ],
        fill=(110, 160, 110),
        outline=(50, 90, 50),
    )

    draw.polygon(
        [
            (320, 575),
            (530, 370),
            (760, 575),
        ],
        fill=(130, 150, 180),
        outline=(60, 70, 100),
    )

    # --------------------------------------------------------
    # Character placeholder
    # --------------------------------------------------------

    character_x = 500
    character_y = 450

    # Head

    draw.ellipse(
        [
            character_x - 50,
            character_y - 115,
            character_x + 50,
            character_y - 15,
        ],
        fill=(245, 190, 150),
        outline=(50, 50, 50),
        width=4,
    )

    # Body

    draw.rounded_rectangle(
        [
            character_x - 70,
            character_y - 15,
            character_x + 70,
            character_y + 145,
        ],
        radius=25,
        fill=(70, 120, 210),
        outline=(50, 50, 50),
        width=4,
    )

    # --------------------------------------------------------
    # Prompt text
    # --------------------------------------------------------

    cleaned_prompt = " ".join(
        prompt.split()
    )

    wrapped_lines = textwrap.wrap(
        cleaned_prompt,
        width=80,
    )

    if len(wrapped_lines) > 5:

        wrapped_lines = wrapped_lines[:5]

        wrapped_lines[-1] = (
            wrapped_lines[-1].rstrip(". ")
            + "..."
        )

    y = 650

    for line in wrapped_lines:

        draw.text(
            (45, y),
            line,
            fill=(55, 55, 55),
            font=text_font,
        )

        y += 22

        if y > height - 20:
            break

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    image.save(
        image_path,
        format="PNG",
    )

    print(
        f"Placeholder image saved: {image_path}"
    )

    return f"/static/panels/{image_path.name}"


# ============================================================
# HUGGING FACE AI IMAGE GENERATION
# ============================================================

def _generate_ai_image(
    prompt: str,
    panel_number: int,
) -> str:

    prompt = _validate_prompt(prompt)

    if not HF_TOKEN:

        raise RuntimeError(
            "HF_TOKEN is missing. "
            "Add your Hugging Face token to the environment."
        )

    final_prompt = _build_image_prompt(
        prompt
    )

    filename = (
        f"panel_{panel_number}.png"
    )

    image_path = (
        OUTPUT_DIR / filename
    )

    # --------------------------------------------------------
    # DEBUG INFORMATION
    # --------------------------------------------------------

    print("")
    print("=" * 70)
    print(
        f"GENERATING AI IMAGE - PANEL {panel_number}"
    )
    print("=" * 70)

    print(
        f"Model: {HF_IMAGE_MODEL}"
    )

    print(
        "Original panel prompt:"
    )

    print(
        prompt
    )

    print("")
    print(
        "Final prompt sent to Hugging Face:"
    )

    print(
        final_prompt
    )

    print("=" * 70)
    print("")

    # --------------------------------------------------------
    # Create HF client
    # --------------------------------------------------------

    try:

        client = InferenceClient(
            provider="auto",
            api_key=HF_TOKEN,
        )

    except Exception as exc:

        raise RuntimeError(
            f"Could not create Hugging Face client: {exc}"
        ) from exc

    # --------------------------------------------------------
    # Generate image
    # --------------------------------------------------------

    try:

        image = client.text_to_image(
            prompt=final_prompt,
            model=HF_IMAGE_MODEL,
        )

    except Exception as exc:

        print("")
        print(
            f"❌ HUGGING FACE ERROR - PANEL {panel_number}"
        )
        print(
            str(exc)
        )
        print("")

        raise RuntimeError(
            f"Hugging Face image generation failed: {exc}"
        ) from exc

    # --------------------------------------------------------
    # Validate returned image
    # --------------------------------------------------------

    if image is None:

        raise RuntimeError(
            "Hugging Face returned no image."
        )

    # --------------------------------------------------------
    # Convert to RGB
    # --------------------------------------------------------

    try:

        if image.mode != "RGB":

            image = image.convert(
                "RGB"
            )

    except Exception as exc:

        raise RuntimeError(
            f"Could not process generated image: {exc}"
        ) from exc

    # --------------------------------------------------------
    # Save image
    # --------------------------------------------------------

    try:

        image.save(
            image_path,
            format="PNG",
        )

    except Exception as exc:

        raise RuntimeError(
            f"Could not save generated image: {exc}"
        ) from exc

    # --------------------------------------------------------
    # Success
    # --------------------------------------------------------

    print("")
    print(
        f"✅ AI IMAGE GENERATED SUCCESSFULLY"
    )

    print(
        f"Panel: {panel_number}"
    )

    print(
        f"Saved to: {image_path}"
    )

    print(
        f"URL: /static/panels/{image_path.name}"
    )

    print("")

    # IMPORTANT:
    # Use the actual saved file name.
    return f"/static/panels/{image_path.name}"


# ============================================================
# MAIN IMAGE GENERATION FUNCTION
# ============================================================

def generate_image(
    prompt: str,
    panel_number: int,
) -> str:

    prompt = _validate_prompt(
        prompt
    )

    print("")
    print(
        f"Starting image generation for panel {panel_number}"
    )

    print(
        f"IMAGE_PROVIDER = {IMAGE_PROVIDER}"
    )

    # --------------------------------------------------------
    # PLACEHOLDER MODE
    # --------------------------------------------------------

    if IMAGE_PROVIDER == "placeholder":

        print(
            "⚠ Using PLACEHOLDER image generation."
        )

        return _placeholder(
            panel_number,
            prompt,
        )

    # --------------------------------------------------------
    # HUGGING FACE MODE
    # --------------------------------------------------------

    if IMAGE_PROVIDER == "hf":

        try:

            return _generate_ai_image(
                prompt,
                panel_number,
            )

        except Exception as exc:

            # IMPORTANT:
            # We intentionally DO NOT silently create a
            # placeholder here.
            #
            # This lets us see the actual Hugging Face
            # problem in the browser/terminal.

            print("")
            print(
                "❌ IMAGE GENERATION FAILED"
            )

            print(
                f"Panel: {panel_number}"
            )

            print(
                f"Error: {exc}"
            )

            print("")

            raise RuntimeError(
                f"AI image generation failed for "
                f"panel {panel_number}: {exc}"
            ) from exc

    # --------------------------------------------------------
    # UNKNOWN PROVIDER
    # --------------------------------------------------------

    raise RuntimeError(
        f"Unknown IMAGE_PROVIDER='{IMAGE_PROVIDER}'. "
        f"Use 'hf' or 'placeholder'."
    )
