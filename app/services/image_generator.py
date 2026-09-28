import re
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from huggingface_hub import InferenceClient

from app.config import get_settings


settings = get_settings()

PANELS_DIR = settings.static_dir / "panels"
PANELS_DIR.mkdir(parents=True, exist_ok=True)


def _safe_name(value: str) -> str:
    return (
        re.sub(r"[^a-zA-Z0-9_-]+", "_", value)[:60].strip("_")
        or "panel"
    )


def _get_font(size: int, bold: bool = False):
    candidates = []

    if bold:
        candidates = [
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/segoeuib.ttf",
        ]
    else:
        candidates = [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/segoeui.ttf",
        ]

    for font_path in candidates:
        if Path(font_path).exists():
            return ImageFont.truetype(font_path, size)

    return ImageFont.load_default()


def _placeholder(prompt: str, panel_number: int) -> str:
    """
    Creates a colorful comic-style illustration when AI image generation
    is unavailable.
    """

    filename = (
        f"panel_{panel_number}_{_safe_name(prompt)}.png"
    )

    path = PANELS_DIR / filename

    width = 1200
    height = 850

    # Different background for each panel
    backgrounds = [
        (255, 226, 120),
        (166, 221, 255),
        (255, 181, 181),
        (191, 238, 190),
        (215, 190, 255),
    ]

    bg = backgrounds[(panel_number - 1) % len(backgrounds)]

    img = Image.new(
        "RGB",
        (width, height),
        bg,
    )

    draw = ImageDraw.Draw(img)

    title_font = _get_font(42, bold=True)
    subtitle_font = _get_font(30, bold=True)
    body_font = _get_font(24)

    # -------------------------------------------------
    # COMIC BORDER
    # -------------------------------------------------

    draw.rounded_rectangle(
        (20, 20, width - 20, height - 20),
        radius=30,
        outline=(20, 20, 30),
        width=12,
        fill=bg,
    )

    # -------------------------------------------------
    # TOP COMIC HEADER
    # -------------------------------------------------

    draw.rounded_rectangle(
        (55, 50, width - 55, 135),
        radius=20,
        fill=(25, 25, 35),
    )

    header = f"COMICCRAFT  •  PANEL {panel_number}"

    bbox = draw.textbbox(
        (0, 0),
        header,
        font=title_font,
    )

    header_width = bbox[2] - bbox[0]

    draw.text(
        (
            (width - header_width) / 2,
            70,
        ),
        header,
        fill="white",
        font=title_font,
    )

    # -------------------------------------------------
    # CARTOON CHARACTER
    # -------------------------------------------------

    center_x = width // 2
    character_y = 360

    # Shadow
    draw.ellipse(
        (
            center_x - 150,
            character_y + 120,
            center_x + 150,
            character_y + 175,
        ),
        fill=(90, 90, 100),
    )

    # Body
    draw.rounded_rectangle(
        (
            center_x - 95,
            character_y,
            center_x + 95,
            character_y + 190,
        ),
        radius=45,
        fill=(65, 125, 230),
        outline=(20, 20, 30),
        width=7,
    )

    # Head
    draw.ellipse(
        (
            center_x - 105,
            character_y - 130,
            center_x + 105,
            character_y + 80,
        ),
        fill=(255, 211, 160),
        outline=(20, 20, 30),
        width=7,
    )

    # Hair
    draw.arc(
        (
            center_x - 105,
            character_y - 145,
            center_x + 105,
            character_y + 50,
        ),
        180,
        360,
        fill=(55, 35, 25),
        width=25,
    )

    # Eyes
    draw.ellipse(
        (
            center_x - 55,
            character_y - 55,
            center_x - 30,
            character_y - 30,
        ),
        fill="black",
    )

    draw.ellipse(
        (
            center_x + 30,
            character_y - 55,
            center_x + 55,
            character_y - 30,
        ),
        fill="black",
    )

    # Smile
    draw.arc(
        (
            center_x - 50,
            character_y - 15,
            center_x + 50,
            character_y + 45,
        ),
        10,
        170,
        fill="black",
        width=6,
    )

    # Arms
    draw.line(
        (
            center_x - 90,
            character_y + 50,
            center_x - 180,
            character_y + 120,
        ),
        fill=(20, 20, 30),
        width=18,
    )

    draw.line(
        (
            center_x + 90,
            character_y + 50,
            center_x + 180,
            character_y + 120,
        ),
        fill=(20, 20, 30),
        width=18,
    )

    # -------------------------------------------------
    # COMIC SPEECH BUBBLE
    # -------------------------------------------------

    bubble_x1 = 690
    bubble_y1 = 190
    bubble_x2 = 1110
    bubble_y2 = 340

    draw.rounded_rectangle(
        (
            bubble_x1,
            bubble_y1,
            bubble_x2,
            bubble_y2,
        ),
        radius=30,
        fill="white",
        outline=(20, 20, 30),
        width=6,
    )

    # Speech bubble tail
    draw.polygon(
        [
            (760, 335),
            (710, 390),
            (850, 335),
        ],
        fill="white",
        outline=(20, 20, 30),
    )

    speech = "Let's create an amazing story!"

    speech_lines = textwrap.wrap(
        speech,
        width=25,
    )

    y = 220

    for line in speech_lines:
        draw.text(
            (735, y),
            line,
            fill=(20, 20, 30),
            font=subtitle_font,
        )
        y += 40

    # -------------------------------------------------
    # SCENE / PROMPT AREA
    # -------------------------------------------------

    draw.rounded_rectangle(
        (
            70,
            600,
            width - 70,
            790,
        ),
        radius=25,
        fill=(255, 255, 255),
        outline=(20, 20, 30),
        width=6,
    )

    draw.text(
        (100, 625),
        "Scene",
        fill=(30, 30, 30),
        font=subtitle_font,
    )

    clean_prompt = re.sub(
        r"\s+",
        " ",
        prompt,
    ).strip()

    prompt_lines = textwrap.wrap(
        clean_prompt,
        width=75,
    )

    y = 675

    for line in prompt_lines[:4]:
        draw.text(
            (100, y),
            line,
            fill=(45, 45, 45),
            font=body_font,
        )
        y += 32

    # -------------------------------------------------
    # SMALL COMIC DECORATIONS
    # -------------------------------------------------

    draw.ellipse(
        (80, 170, 125, 215),
        fill=(255, 80, 80),
        outline=(20, 20, 30),
        width=4,
    )

    draw.ellipse(
        (130, 155, 180, 205),
        fill=(255, 210, 50),
        outline=(20, 20, 30),
        width=4,
    )

    draw.ellipse(
        (185, 175, 230, 220),
        fill=(80, 190, 255),
        outline=(20, 20, 30),
        width=4,
    )

    img.save(
        path,
        "PNG",
        optimize=True,
    )

    return f"/static/panels/{path.name}"


def generate_image(
    prompt: str,
    panel_number: int,
) -> str:

    provider = settings.image_provider.lower().strip()

    # -------------------------------------------------
    # COLORFUL LOCAL COMIC MODE
    # -------------------------------------------------

    if provider == "placeholder":
        return _placeholder(
            prompt,
            panel_number,
        )

    # -------------------------------------------------
    # HUGGING FACE AI MODE
    # -------------------------------------------------

    if provider != "hf":
        raise RuntimeError(
            "IMAGE_PROVIDER must be 'hf' or 'placeholder'."
        )

    if not settings.hf_token:
        raise RuntimeError(
            "HF_TOKEN is missing. "
            "Add it to .env or use IMAGE_PROVIDER=placeholder."
        )

    client = InferenceClient(
        provider="auto",
        api_key=settings.hf_token,
    )

    # Improve the user's Gemini-generated prompt
    enhanced_prompt = f"""
Create a high-quality colorful comic-book illustration.

{prompt}

Visual requirements:
- colorful professional comic art
- expressive characters
- cinematic composition
- detailed environment
- vibrant lighting
- clean line art
- rich colors
- dynamic perspective
- family-friendly
- no text
- no captions
- no speech bubbles
- 16:9 composition
""".strip()

    image = client.text_to_image(
        enhanced_prompt,
        model=settings.hf_image_model,
    )

    filename = (
        f"panel_{panel_number}_{_safe_name(prompt)}.png"
    )

    image_path = PANELS_DIR / filename

    image.save(
        image_path,
        "PNG",
    )

    return f"/static/panels/{filename}"
