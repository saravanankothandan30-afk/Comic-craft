import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from huggingface_hub import InferenceClient

from app.config import get_settings


settings = get_settings()

PANELS_DIR = settings.static_dir / "panels"
PANELS_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------
# SAFE FILE NAME
# ---------------------------------------------------------

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
        ]
    else:
        font_paths = [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/segoeui.ttf",
        ]

    for font_path in font_paths:

        if Path(font_path).exists():

            return ImageFont.truetype(
                font_path,
                size,
            )

    return ImageFont.load_default()


# ---------------------------------------------------------
# LOCAL COLORFUL FALLBACK
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

    title_font = _get_font(
        38,
        bold=True,
    )

    body_font = _get_font(
        24,
        bold=False,
    )

    # -----------------------------------------------------
    # OUTER BORDER
    # -----------------------------------------------------

    draw.rounded_rectangle(
        (
            15,
            15,
            width - 15,
            height - 15,
        ),
        radius=25,
        fill=background,
        outline=(20, 20, 30),
        width=10,
    )

    # -----------------------------------------------------
    # SKY
    # -----------------------------------------------------

    draw.rectangle(
        (
            30,
            30,
            width - 30,
            450,
        ),
        fill=(
            135,
            206,
            235,
        ),
    )

    # -----------------------------------------------------
    # SUN
    # -----------------------------------------------------

    draw.ellipse(
        (
            80,
            80,
            200,
            200,
        ),
        fill=(255, 220, 60),
        outline=(240, 160, 30),
        width=5,
    )

    # -----------------------------------------------------
    # CLOUDS
    # -----------------------------------------------------

    clouds = [
        (300, 100),
        (850, 130),
    ]

    for x, y in clouds:

        draw.ellipse(
            (
                x,
                y,
                x + 100,
                y + 55,
            ),
            fill="white",
        )

        draw.ellipse(
            (
                x + 45,
                y - 25,
                x + 145,
                y + 55,
            ),
            fill="white",
        )

        draw.ellipse(
            (
                x + 90,
                y,
                x + 180,
                y + 55,
            ),
            fill="white",
        )

    # -----------------------------------------------------
    # GROUND
    # -----------------------------------------------------

    draw.rectangle(
        (
            30,
            450,
            width - 30,
            770,
        ),
        fill=(100, 180, 100),
    )

    # -----------------------------------------------------
    # SIMPLE BUILDING
    # -----------------------------------------------------

    draw.rectangle(
        (
            750,
            280,
            1060,
            470,
        ),
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
            (
                x,
                330,
                x + 55,
                390,
            ),
            fill=(100, 190, 240),
            outline=(30, 30, 30),
            width=4,
        )

    # -----------------------------------------------------
    # CHARACTER
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # SPEECH BUBBLE
    # -----------------------------------------------------

    draw.rounded_rectangle(
        (
            80,
            500,
            650,
            650,
        ),
        radius=30,
        fill="white",
        outline=(20, 20, 30),
        width=6,
    )

    draw.polygon(
        [
            (280, 650),
            (330, 700),
            (370, 650),
        ],
        fill="white",
        outline=(20, 20, 30),
    )

    speech_font = _get_font(
        27,
        bold=True,
    )

    draw.text(
        (
            115,
            545,
        ),
        "Let's begin",
        fill=(20, 20, 30),
        font=speech_font,
    )

    draw.text(
        (
            115,
            590,
        ),
        "our adventure!",
        fill=(20, 20, 30),
        font=speech_font,
    )

    # -----------------------------------------------------
    # PROMPT AREA
    # -----------------------------------------------------

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

    prompt_text = re.sub(
        r"\s+",
        " ",
        str(prompt),
    ).strip()

    if len(prompt_text) > 105:
        prompt_text = prompt_text[:105] + "..."

    draw.text(
        (
            75,
            708,
        ),
        prompt_text,
        fill=(30, 30, 30),
        font=body_font,
    )

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
                "Using colorful local fallback image."
            )

            return _placeholder(
                prompt,
                panel_number,
            )

    # -----------------------------------------------------
    # LOCAL COLORFUL IMAGE
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
