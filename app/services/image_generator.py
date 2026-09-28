from __future__ import annotations

import os
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from huggingface_hub import InferenceClient

from app.config import get_settings


settings = get_settings()

# -------------------------------------------------------------------
# Paths
# -------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

OUTPUT_DIR = BASE_DIR / "static" / "panels"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------

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


# -------------------------------------------------------------------
# Font handling
# -------------------------------------------------------------------

def _get_font(size: int, bold: bool = False):
    """
    Load a font in a cross-platform way.

    Works on:
    - Windows
    - Linux / Render
    - macOS

    Falls back to Pillow's default font if no system font is found.
    """

    if bold:
        candidates = [
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
        candidates = [
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

    for font_path in candidates:
        if os.path.exists(font_path):
            try:
                return ImageFont.truetype(font_path, size)
            except Exception:
                continue

    return ImageFont.load_default()


# -------------------------------------------------------------------
# Prompt validation
# -------------------------------------------------------------------

def _validate_prompt(prompt: str) -> str:
    """
    Validate and clean the image-generation prompt.
    """

    if prompt is None:
        raise ValueError("Image prompt cannot be None.")

    if not isinstance(prompt, str):
        raise TypeError("Image prompt must be a string.")

    prompt = prompt.strip()

    if not prompt:
        raise ValueError("Image prompt cannot be empty.")

    # Prevent extremely large prompts from causing unnecessary
    # requests to the image-generation service.
    if len(prompt) > 4000:
        prompt = prompt[:4000]

    return prompt


# -------------------------------------------------------------------
# Prompt enhancement
# -------------------------------------------------------------------

def _build_image_prompt(prompt: str) -> str:
    """
    Enhance the AI image prompt so generated panels have
    proper comic-style backgrounds and visual details.
    """

    return f"""
Create a high-quality colorful comic-book illustration.

Scene description:
{prompt}

Requirements:
- detailed environment and background
- clear main character
- expressive character pose and facial expression
- strong visual storytelling
- colorful professional comic-book artwork
- cinematic composition
- clean line art
- attractive lighting
- rich background details
- consistent visual style
- suitable for a five-panel comic
- landscape composition
- 4:3 aspect ratio

Do NOT include:
- speech bubbles
- dialogue text
- captions
- subtitles
- written words
- logos
- watermarks
- UI elements
- borders

The image should look like a finished comic panel illustration.
""".strip()


# -------------------------------------------------------------------
# Local placeholder
# -------------------------------------------------------------------

def _placeholder(panel_number: int, prompt: str) -> str:
    """
    Generate a colorful local fallback image.

    This is used when Hugging Face image generation is unavailable.
    """

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

    # Background
    draw.rectangle(
        [0, 0, width, height],
        fill=(245, 241, 234),
    )

    # Header area
    draw.rectangle(
        [0, 0, width, 105],
        fill=(25, 25, 25),
    )

    title_font = _get_font(42, bold=True)
    panel_font = _get_font(30, bold=True)
    text_font = _get_font(22)

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

    # Comic-style visual area
    margin = 45
    top = 185
    bottom = 650

    draw.rounded_rectangle(
        [margin, top, width - margin, bottom],
        radius=30,
        fill=(255, 255, 255),
        outline=(60, 60, 60),
        width=4,
    )

    # Decorative comic sun
    draw.ellipse(
        [720, 225, 850, 355],
        fill=(255, 200, 70),
        outline=(80, 60, 20),
        width=4,
    )

    # Decorative landscape
    draw.polygon(
        [
            (70, 590),
            (250, 420),
            (400, 590),
        ],
        fill=(110, 160, 110),
        outline=(50, 90, 50),
    )

    draw.polygon(
        [
            (300, 590),
            (510, 390),
            (750, 590),
        ],
        fill=(130, 150, 180),
        outline=(60, 70, 100),
    )

    # Character placeholder
    character_x = 480
    character_y = 445

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

    # Prompt description
    cleaned_prompt = " ".join(prompt.split())

    wrapped_lines = textwrap.wrap(
        cleaned_prompt,
        width=75,
    )

    # Limit display text
    if len(wrapped_lines) > 8:
        wrapped_lines = wrapped_lines[:8]
        if wrapped_lines:
            wrapped_lines[-1] = wrapped_lines[-1].rstrip(". ") + "..."

    y = 675

    for line in wrapped_lines:
        draw.text(
            (45, y),
            line,
            fill=(55, 55, 55),
            font=text_font,
        )
        y += 24

        if y > height - 25:
            break

    image.save(
        image_path,
        format="PNG",
    )

    return f"/static/panels/{image_path.name}"


# -------------------------------------------------------------------
# Hugging Face AI image generation
# -------------------------------------------------------------------

def _generate_ai_image(
    prompt: str,
    panel_number: int,
) -> str:
    """
    Generate an image using Hugging Face inference.
    """

    prompt = _validate_prompt(prompt)

    if not HF_TOKEN:
        raise RuntimeError(
            "HF_TOKEN is missing. Add your Hugging Face token "
            "to the environment variables."
        )

    enhanced_prompt = _build_image_prompt(prompt)

    filename = f"panel_{panel_number}.png"
    image_path = OUTPUT_DIR / filename

    print(
        f"Generating AI image for panel {panel_number} "
        f"using model: {HF_IMAGE_MODEL}"
    )

    try:
        client = InferenceClient(
            provider="auto",
            api_key=HF_TOKEN,
        )

        image = client.text_to_image(
            enhanced_prompt,
            model=HF_IMAGE_MODEL,
        )

        if image is None:
            raise RuntimeError(
                "Hugging Face returned an empty image."
            )

        # Resize if necessary so comic panels remain consistent.
        if image.mode != "RGB":
            image = image.convert("RGB")

        image.save(
            image_path,
            format="PNG",
        )

        print(
            f"AI image saved successfully: {image_path}"
        )

        # IMPORTANT:
        # Return the actual saved filename.
        return f"/static/panels/{image_path.name}"

    except Exception as exc:
        print(
            f"AI image generation failed for panel "
            f"{panel_number}: {exc}"
        )

        raise


# -------------------------------------------------------------------
# Public image-generation function
# -------------------------------------------------------------------

def generate_image(
    prompt: str,
    panel_number: int,
) -> str:
    """
    Main image-generation function used by routes.py.

    IMAGE_PROVIDER options:

        hf
            Use Hugging Face AI image generation.

        placeholder
            Use local colorful placeholder images.

    If Hugging Face fails, automatically falls back
    to the local placeholder.
    """

    prompt = _validate_prompt(prompt)

    print(
        f"Image generation started for panel "
        f"{panel_number}"
    )

    if IMAGE_PROVIDER == "placeholder":
        print(
            f"Using local placeholder for panel "
            f"{panel_number}"
        )

        return _placeholder(
            panel_number,
            prompt,
        )

    if IMAGE_PROVIDER == "hf":
        try:
            return _generate_ai_image(
                prompt,
                panel_number,
            )

        except Exception as exc:
            print(
                f"Falling back to placeholder for panel "
                f"{panel_number} because AI generation failed: "
                f"{exc}"
            )

            return _placeholder(
                panel_number,
                prompt,
            )

    # Unknown provider
    print(
        f"Unknown IMAGE_PROVIDER='{IMAGE_PROVIDER}'. "
        f"Using placeholder instead."
    )

    return _placeholder(
        panel_number,
        prompt,
    )
