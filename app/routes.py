
from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.config import get_settings
from app.models.schemas import ImageTestRequest, PromptRequest
from app.services.exporters import save_pdf
from app.services.gemini_service import generate_outline, generate_story
from app.services.image_generator import generate_image
from app.services.layout_builder import build_comic_layout


router = APIRouter()

settings = get_settings()

templates = Jinja2Templates(
    directory=str(settings.templates_dir)
)


def run_generation(request_data: PromptRequest):
    """
    Complete ComicCraft generation pipeline:

    1. Generate comic outline using Gemini
    2. Generate detailed story/dialogue using Gemini
    3. Generate AI images for each panel
    4. Build comic layout
    5. Export comic as PDF
    """

    # Step 1: Generate comic outline
    outline = generate_outline(
        request_data.story_prompt,
        request_data.character_name,
        request_data.setting,
        request_data.tone,
        request_data.art_style,
    )

    # Step 2: Generate detailed comic story
    story = generate_story(
        outline,
        request_data.story_prompt,
        request_data.character_name,
        request_data.tone,
    )

    # Step 3: Generate images for all panels
    image_paths = []

    for panel in story.panels:
        image_path = generate_image(
            panel.image_prompt,
            panel.panel_number,
        )

        image_paths.append(image_path)

    # Step 4: Build comic layout
    layout = build_comic_layout(
        story,
        image_paths,
    )

    # Step 5: Export comic as PDF
    pdf_path = save_pdf(layout)

    return outline, story, layout, pdf_path


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """
    Display the ComicCraft home page.
    """

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={},
    )


@router.post("/generate", response_class=HTMLResponse)
async def generate(
    request: Request,
    story_prompt: str = Form(...),
    character_name: str = Form(...),
    setting: str = Form(...),
    tone: str = Form(...),
    art_style: str = Form(...),
):
    """
    Generate a complete comic from the web form.
    """

    try:
        # Create validated request data
        data = PromptRequest(
            story_prompt=story_prompt,
            character_name=character_name,
            setting=setting,
            tone=tone,
            art_style=art_style,
        )

        # Run complete generation pipeline
        outline, story, layout, pdf_path = run_generation(data)

        # Display generated comic
        return templates.TemplateResponse(
            request=request,
            name="comic_preview.html",
            context={
                "layout": layout,
                "pdf_path": pdf_path,
                "request_data": data.model_dump(),
                "outline": outline.model_dump(),
                "story": story.model_dump(),
            },
        )

    except Exception as exc:
        return templates.TemplateResponse(
            request=request,
            name="error.html",
            context={
                "message": str(exc),
            },
            status_code=500,
        )


@router.post("/generate-comic/json")
async def generate_json(data: PromptRequest):
    """
    Generate a comic through the JSON API.
    """

    try:
        outline, story, layout, pdf_path = run_generation(data)

        return {
            "success": True,
            "outline": outline.model_dump(),
            "story": story.model_dump(),
            "layout": layout,
            "pdf_path": pdf_path,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


@router.post("/test-image")
async def test_image(data: ImageTestRequest):
    """
    Test the image-generation service independently.
    """

    try:
        image_path = generate_image(
            data.prompt,
            0,
        )

        return {
            "success": True,
            "image_path": image_path,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


@router.get("/export-success", response_class=HTMLResponse)
async def export_success(
    request: Request,
    pdf_path: str = "",
):
    """
    Display the PDF export success page.
    """

    return templates.TemplateResponse(
        request=request,
        name="export_success.html",
        context={
            "pdf_path": pdf_path,
        },
    )

