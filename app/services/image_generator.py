import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from huggingface_hub import InferenceClient

from app.config import get_settings


settings = get_settings()

PANELS_DIR = settings.static_dir / "panels"
PANELS_DIR.mkdir(parents=True, exist_ok=True)


# ----------------------------------------------------------------
# SAFE FILE NAME
# ---------------------------------------------------------------- 

def _safe_name(value: str) -> str:
    name = re.sub(
        r"[^a-zA-Z0-9_-]+",
        "_",
        value,
    )

    name = name[:60].strip("_")

    return name or "panel"


# ---------------------------------------------------------
# FONT
# ---------------------------------------------------------

def _get_font(size: int, bold: bool = False):

    if bold:
        font_paths = [
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/segoeuib.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]
    else:
        font_paths = [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/segoeui.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]

    for font_path in font_paths:

        if Path(font_path).exists():

            return ImageFont.truetype(
                font_path,
                size,
            )

    return ImageFont.load_default()


# ---------------------------------------------------------
# LOCAL PROFESSIONAL FALLBACK
# ---------------------------------------------------------

def _placeholder(
    prompt: str,
    panel_number: int,
) -> str:

    filename = (
        f"panel_{panel_number}_"
        f"{_safe_name(prompt)}.png"
    )

    path = PANELS_DIR / filename

    width = 1200
    height = 800

    # Muted, professional palette (cycled per panel)
    palettes = [
        ((30, 41, 59), (51, 65, 85), (99, 179, 237)),
        ((23, 51, 45), (30, 74, 65), (74, 179, 145)),
        ((45, 30, 60), (70, 45, 95), (170, 120, 220)),
        ((51, 35, 20), (92, 62, 30), (230, 170, 90)),
        ((30, 30, 40), (55, 55, 75), (150, 150, 200)),
    ]

    dark, mid, accent = palettes[
        (panel_number - 1) % len(palettes)
    ]

    image = Image.new(
        "RGB",
        (width, height),
        dark,
    )

    draw = ImageDraw.Draw(image)

    # -----------------------------------------------------
    # VERTICAL GRADIENT BACKGROUND
    # -----------------------------------------------------

    for y in range(height):
        t = y / height
        r = int(dark[0] + (mid[0] - dark[0]) * t)
        g = int(dark[1] + (mid[1] - dark[1]) * t)
        b = int(dark[2] + (mid[2] - dark[2]) * t)
        draw.line((0, y, width, y), fill=(r, g, b))

    # -----------------------------------------------------
    # THIN BORDER / FRAME
    # -----------------------------------------------------

    draw.rectangle(
        (
            20,
            20,
            width - 20,
            height - 20,
        ),
        outline=accent,
        width=3,
    )

    # -----------------------------------------------------
    # SUBTLE GEOMETRIC ACCENTS (corners)
    # -----------------------------------------------------

    draw.line((60, 60, 220, 60), fill=accent, width=4)
    draw.line((60, 60, 60, 220), fill=accent, width=4)
    draw.line(
        (width - 60, height - 60, width - 220, height - 60),
        fill=accent,
        width=4,
    )
    draw.line(
        (width - 60, height - 60, width - 60, height - 220),
        fill=accent,
        width=4,
    )

    # -----------------------------------------------------
    # PANEL LABEL
    # -----------------------------------------------------

    label_font = _get_font(30, bold=True)
    body_font = _get_font(22, bold=False)

    draw.text(
        (60, 90),
        f"PANEL {panel_number:02d}",
        fill=accent,
        font=label_font,
    )

    # -----------------------------------------------------
    # CONTENT CARD (holds the prompt text)
    # -----------------------------------------------------

    card_top = 320
    card_bottom = height - 90

    draw.rounded_rectangle(
        (
            60,
            card_top,
            width - 60,
            card_bottom,
        ),
        radius=12,
        fill=(255, 255, 255),
        outline=accent,
        width=2,
    )

    prompt_text = re.sub(
        r"\s+",
        " ",
        str(prompt),
    ).strip()

    # Simple word-wrap so text fits inside the card
    max_chars_per_line = 60
    words = prompt_text.split(" ")
    lines = []
    current_line = ""

    for word in words:
        candidate = f"{current_line} {word}".strip()
        if len(candidate) > max_chars_per_line:
            if current_line:
                lines.append(current_line)
            current_line = word
        else:
            current_line = candidate

    if current_line:
        lines.append(current_line)

    max_lines = 8
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1].rstrip() + "..."

    line_height = 30
    text_y = card_top + 30

    for line in lines:
        draw.text(
            (90, text_y),
            line,
            fill=(30, 30, 40),
            font=body_font,
        )
        text_y += line_height

    image.save(
        path,
        "PNG",
        optimize=True,
    )

    return f"/static/panels/{path.name}"


# ---------------------------------------------------------
# AI IMAGE GENERATION
# ---------------------------------------------------------

def _generate_ai_image(
    prompt: str,
    panel_number: int,
) -> str:

    if not settings.hf_token:

        raise RuntimeError(
            "HF_TOKEN is missing."
        )

    client = InferenceClient(
        provider="auto",
        api_key=settings.hf_token,
    )

    # -----------------------------------------------------
    # IMPORTANT:
    # The user's Gemini panel prompt becomes the main
    # description of the image.
    # -----------------------------------------------------

    enhanced_prompt = f"""
Create a high-quality colorful comic-book illustration
for panel {panel_number} of a continuous comic story.

MAIN SCENE DESCRIPTION:
{prompt}

The image MUST visually represent the scene described above.

BACKGROUND REQUIREMENTS:
- Create a detailed environment based on the location
  described in the prompt.
- If the prompt describes a school, create a school
  environment.
- If it describes a laboratory, create a laboratory.
- If it describes a forest, create a detailed forest.
- If it describes a city, create a detailed city.
- If it describes space, create a detailed space environment.
- If it describes a village, create a detailed village.
- If it describes a room, create the appropriate room.
- Do not use a generic blank background.

CHARACTER REQUIREMENTS:
- Include the main character described in the prompt.
- Show the character performing the action described.
- Use expressive facial expressions and body language.
- Keep the character visually clear.

ART STYLE:
- colorful comic-book illustration
- professional digital illustration
- vibrant colors
- clean black line art
- cinematic lighting
- detailed background
- dynamic composition
- depth and perspective
- visually rich environment
- polished artwork

COMPOSITION:
- landscape orientation
- wide cinematic scene
- characters clearly visible
- background clearly visible
- foreground, middle ground and background
- suitable for a comic panel

DO NOT:
- create a blank background
- create a white background
- create a plain studio background
- add written text
- add captions
- add speech bubbles
- add watermarks
- add logos

The final result should look like a real colorful
comic-book panel rather than a presentation slide.
""".strip()

    image = client.text_to_image(
        enhanced_prompt,
        model=settings.hf_image_model,
    )

    filename = (
        f"panel_{panel_number}_"
        f"{_safe_name(prompt)}.png"
    )

    image_path = PANELS_DIR / filename

    image.save(
        image_path,
        "PNG",
    )

    return f"/static/panels/{filename}"


# ---------------------------------------------------------
# MAIN IMAGE FUNCTION
# ---------------------------------------------------------

def generate_image(
    prompt: str,
    panel_number: int,
) -> str:

    provider = (
        settings.image_provider
        .lower()
        .strip()
    )

    # -----------------------------------------------------
    # REAL AI IMAGE
    # -----------------------------------------------------

    if provider == "hf":

        try:

            return _generate_ai_image(
                prompt,
                panel_number,
            )

        except Exception as exc:

            print(
                f"AI image generation failed for "
                f"panel {panel_number}: {exc}"
            )

            print(
                "Using professional local fallback image."
            )

            return _placeholder(
                prompt,
                panel_number,
            )

    # -----------------------------------------------------
    # LOCAL PROFESSIONAL IMAGE
    # -----------------------------------------------------

    if provider == "placeholder":

        return _placeholder(
            prompt,
            panel_number,
        )

    # -----------------------------------------------------
    # INVALID PROVIDER
    # -----------------------------------------------------

    raise RuntimeError(
        "IMAGE_PROVIDER must be "
        "'hf' or 'placeholder'."
    )
