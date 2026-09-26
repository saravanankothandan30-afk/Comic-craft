from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.routes import router

settings = get_settings()

# Ensure runtime folders exist.
(settings.static_dir / "panels").mkdir(parents=True, exist_ok=True)
(settings.static_dir / "exports").mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="ComicCraft",
    description="AI comic story creator using Gemini and Hugging Face image generation.",
    version="1.0.0",
)

app.mount("/static", StaticFiles(directory=str(settings.static_dir)), name="static")
app.include_router(router)

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "gemini_configured": bool(settings.gemini_api_key),
        "image_provider": settings.image_provider,
        "image_model": settings.hf_image_model,
    }
