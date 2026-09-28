from __future__ import annotations

import os
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from huggingface_hub import InferenceClient

from app.config import get_settings


# ============================================================
# SETTINGS
# ============================================================

settings = get_settings()

PANELS_DIR = settings.static_dir / "panels"
PANELS_DIR.mkdir(parents=True, exist_ok=True)

IMAGE_PROVIDER = (
    getattr(settings, "image_provider", "hf")
    or os.getenv("IMAGE_PROVIDER", "hf")
).lower().strip()

HF_TOKEN = (
    getattr(settings, "hf_token", "")
    or os.getenv("HF_TOKEN", "")
).strip()

HF_IMAGE_MODEL = (
    getattr(
        settings,
        "hf_image_model",
        "black-forest-labs/FLUX.1-schnell",
    )
    or os.getenv(
        "HF_IMAGE_MODEL",
        "black-forest-labs/FLUX.1-schnell",
    )
).strip()


# ============================================================
# FONT
# ============================================================

def _get_font(size: int, bold: bool = False):

    if bold:
        font_paths = [
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/segoeuib.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
        ]
    else:
        font_paths = [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/segoeui.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
        ]

    for font_path in font_paths:
        if Path(font_path).exists():
            try:
                return ImageFont.truetype(font_path, size)
            except Exception:
                pass

    return ImageFont.load_default()


# ============================================================
# CLEAN PROMPT
# ============================================================

def _clean_prompt(prompt: str) -> str:

    if prompt is None:
        raise ValueError("Image prompt cannot be None.")

    if not isinstance(prompt, str):
        raise TypeError("Image prompt must be a string.")

    prompt = prompt.strip()

    if not prompt:
        raise ValueError("Image prompt cannot be empty.")

    # Prevent unnecessarily huge prompts.
    if len(prompt) > 5000:
        prompt = prompt[:5000]

    # Remove accidental excessive whitespace.
    prompt = re.sub(r"\s+", " ", prompt).strip()

    return prompt


# ============================================================
# BUILD THE IMPORTANT AI PROMPT
# ============================================================

def _build_ai_prompt(
    prompt: str,
    panel_number: int,
) -> str:

    prompt = _clean_prompt(prompt)

    return f"""
COMIC PANEL {panel_number}

MOST IMPORTANT INSTRUCTION:
Create the image primarily from the EXACT SCENE DESCRIPTION below.
Do not replace the described scene with a generic comic scene.

============================================================
EXACT SCENE DESCRIPTION
============================================================

{prompt}

============================================================
SCENE INTERPRETATION
============================================================

The scene description above is the source of truth.

You must visually identify and represent:

1. WHO is present
2. WHAT each character is doing
3. WHERE the scene takes place
4. IMPORTANT objects mentioned
5. The character's expression and body language
6. The important action or event
7. The atmosphere and mood
8. The relationship between characters and objects

If the scene describes a specific location, show that location clearly.

If the scene describes a specific action, show that action clearly.

If the scene describes an important object, make that object visible and relevant.

Do not substitute unrelated characters, locations, objects, or actions.

============================================================
CONTINUITY
============================================================

This is panel {panel_number} of a five-panel comic.

Maintain visual continuity with the story.

The main character should remain visually consistent:
- same approximate age
- same hairstyle
- same clothing
- same general appearance

Only change the character's pose, expression, or action when required by
the scene description.

============================================================
ART STYLE
============================================================

Create a polished colorful comic-book illustration.

Style:
- professional digital comic artwork
- vibrant colors
- clean black line art
- expressive characters
- cinematic lighting
- detailed environment
- strong depth
- natural perspective
- dynamic composition
- polished professional illustration

============================================================
COMPOSITION
============================================================

Landscape comic-panel composition.

Show:
- foreground
- main characters
- important objects
- detailed environment
- background depth

The main action must be easy to understand immediately.

Do not make the character tiny.

Do not use a generic studio background.

Do not use an empty background.

============================================================
TEXT RESTRICTIONS
============================================================

Do NOT generate:
- speech bubbles
- captions
- subtitles
- dialogue text
- letters
- words
- logos
- watermarks
- UI elements

The story text will be added separately by ComicCraft.

============================================================
FINAL PRIORITY
============================================================

SCENE ACCURACY is more important than decorative elements.

The final image must look like a real comic panel showing
the exact event described in the scene description.
""".strip()


# ============================================================
# AI IMAGE GENERATION
# ============================================================

def _generate_ai_image(
    prompt: str,
    panel_number: int,
) -> str:

    prompt = _clean_prompt(prompt)

    if not HF_TOKEN:
        raise RuntimeError(
            "HF_TOKEN is missing. Add HF_TOKEN to your environment variables."
        )

    final_prompt = _build_ai_prompt(
        prompt,
        panel_number,
    )

    print()
    print("=" * 80)
    print(f"GENERATING AI IMAGE - PANEL {panel_number}")
    print("=" * 80)

    print()
    print("MODEL:")
    print(HF_IMAGE_MODEL)

    print()
    print("ORIGINAL GEMINI IMAGE PROMPT:")
    print(prompt)

    print()
    print("FINAL FLUX PROMPT:")
    print(final_prompt)

    print("=" * 80)
    print()

    # --------------------------------------------------------
    # Hugging Face client
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

        print()
        print("❌ HUGGING FACE IMAGE ERROR")
        print(str(exc))
        print()

        raise RuntimeError(
            f"Hugging Face image generation failed: {exc}"
        ) from exc

    # --------------------------------------------------------
    # Validate
    # --------------------------------------------------------

    if image is None:
        raise RuntimeError(
            "Hugging Face returned no image."
        )

    try:

        if image.mode != "RGB":
            image = image.convert("RGB")

    except Exception as exc:
        raise RuntimeError(
            f"Could not process generated image: {exc}"
        ) from exc

    # --------------------------------------------------------
    # Fixed filename
    # --------------------------------------------------------

    filename = f"panel_{panel_number}.png"

    image_path = PANELS_DIR / filename

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    try:

        image.save(
            image_path,
            "PNG",
        )

    except Exception as exc:
        raise RuntimeError(
            f"Could not save generated image: {exc}"
        ) from exc

    print()
    print("✅ AI IMAGE GENERATED")
    print(f"Panel: {panel_number}")
    print(f"Saved: {image_path}")
    print(f"URL: /static/panels/{filename}")
    print()

    return f"/static/panels/{filename}"


# ============================================================
# LOCAL FALLBACK
# ============================================================

def _placeholder(
    prompt: str,
    panel_number: int,
) -> str:

    width = 1200
    height = 800

    backgrounds = [
        (135, 206, 235),
        (255, 218, 140),
        (170, 220, 180),
        (210, 190, 240),
        (250, 180, 180),
    ]

    background = backgrounds[
        (panel_number - 1) % len(backgrounds)
    ]

    image = Image.new(
        "RGB",
        (width, height),
        background,
    )

    draw = ImageDraw.Draw(image)

    # --------------------------------------------------------
    # Border
    # --------------------------------------------------------

    draw.rounded_rectangle(
        (15, 15, width - 15, height - 15),
        radius=25,
        fill=background,
        outline=(20, 20, 30),
        width=10,
    )

    # --------------------------------------------------------
    # Sky
    # --------------------------------------------------------

    draw.rectangle(
        (30, 30, width - 30, 450),
        fill=(135, 206, 235),
    )

    # --------------------------------------------------------
    # Sun
    # --------------------------------------------------------

    draw.ellipse(
        (80, 80, 200, 200),
        fill=(255, 220, 60),
        outline=(240, 160, 30),
        width=5,
    )

    # --------------------------------------------------------
    # Ground
    # --------------------------------------------------------

    draw.rectangle(
        (30, 450, width - 30, 770),
        fill=(100, 180, 100),
    )

    # --------------------------------------------------------
    # Building
    # --------------------------------------------------------

    draw.rectangle(
        (750, 280, 1060, 470),
        fill=(245, 180, 100),
        outline=(30, 30, 30),
        width=6,
    )

    draw.polygon(
        [
            (710, 280),
            (900, 170),
            (1100, 280),
        ],
        fill=(190, 70, 70),
        outline=(30, 30, 30),
    )

    # Windows

    for x in [790, 900, 1010]:

        draw.rectangle(
            (x, 330, x + 55, 390),
            fill=(100, 190, 240),
            outline=(30, 30, 30),
            width=4,
        )

    # --------------------------------------------------------
    # Character
    # --------------------------------------------------------

    cx = 470
    cy = 390

    # Shadow

    draw.ellipse(
        (
            cx - 110,
            cy + 145,
            cx + 110,
            cy + 180,
        ),
        fill=(70, 100, 70),
    )

    # Body

    draw.rounded_rectangle(
        (
            cx - 75,
            cy,
            cx + 75,
            cy + 170,
        ),
        radius=30,
        fill=(60, 110, 220),
        outline=(20, 20, 30),
        width=6,
    )

    # Head

    draw.ellipse(
        (
            cx - 85,
            cy - 120,
            cx + 85,
            cy + 50,
        ),
        fill=(255, 210, 160),
        outline=(20, 20, 30),
        width=6,
    )

    # Hair

    draw.arc(
        (
            cx - 85,
            cy - 135,
            cx + 85,
            cy + 40,
        ),
        180,
        360,
        fill=(50, 30, 20),
        width=20,
    )

    # Eyes

    draw.ellipse(
        (
            cx - 45,
            cy - 45,
            cx - 25,
            cy - 25,
        ),
        fill="black",
    )

    draw.ellipse(
        (
            cx + 25,
            cy - 45,
            cx + 45,
            cy - 25,
        ),
        fill="black",
    )

    # Smile

    draw.arc(
        (
            cx - 40,
            cy - 10,
            cx + 40,
            cy + 35,
        ),
        10,
        170,
        fill="black",
        width=5,
    )

    # Arms

    draw.line(
        (
            cx - 65,
            cy + 50,
            cx - 150,
            cy + 110,
        ),
        fill=(20, 20, 30),
        width=15,
    )

    draw.line(
        (
            cx + 65,
            cy + 50,
            cx + 150,
            cy + 110,
        ),
        fill=(20, 20, 30),
        width=15,
    )

    # --------------------------------------------------------
    # Panel label
    # --------------------------------------------------------

    title_font = _get_font(
        38,
        bold=True,
    )

    body_font = _get_font(
        22,
    )

    draw.text(
        (55, 50),
        f"COMICCRAFT — PANEL {panel_number}",
        fill=(20, 20, 30),
        font=title_font,
    )

    # --------------------------------------------------------
    # Prompt description
    # --------------------------------------------------------

    prompt_text = re.sub(
        r"\s+",
        " ",
        str(prompt),
    ).strip()

    if len(prompt_text) > 110:
        prompt_text = prompt_text[:110] + "..."

    draw.rounded_rectangle(
        (
            55,
            690,
            width - 55,
            755,
        ),
        radius=15,
        fill=(255, 255, 255),
        outline=(20, 20, 30),
        width=4,
    )

    draw.text(
        (75, 708),
        prompt_text,
        fill=(30, 30, 30),
        font=body_font,
    )

    filename = f"panel_{panel_number}.png"

    path = PANELS_DIR / filename

    image.save(
        path,
        "PNG",
        optimize=True,
    )

    return f"/static/panels/{filename}"


# ============================================================
# MAIN FUNCTION
# ============================================================

def generate_image(
    prompt: str,
    panel_number: int,
) -> str:

    prompt = _clean_prompt(prompt)

    provider = (
        IMAGE_PROVIDER
        or "hf"
    ).lower().strip()

    print()
    print(
        f"Starting image generation for panel {panel_number}"
    )

    print(
        f"IMAGE_PROVIDER = {provider}"
    )

    # --------------------------------------------------------
    # HUGGING FACE
    # --------------------------------------------------------

    if provider == "hf":

        # IMPORTANT:
        # Do NOT silently replace a failed AI image.
        # We want the real error in Render logs.

        return _generate_ai_image(
            prompt,
            panel_number,
        )

    # --------------------------------------------------------
    # PLACEHOLDER
    # --------------------------------------------------------

    if provider == "placeholder":

        print(
            "Using local placeholder image."
        )

        return _placeholder(
            prompt,
            panel_number,
        )

    # --------------------------------------------------------
    # INVALID
    # --------------------------------------------------------

    raise RuntimeError(
        "IMAGE_PROVIDER must be "
        "'hf' or 'placeholder'."
    )
