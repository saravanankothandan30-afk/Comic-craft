# ComicCraft — AI Comic Story Creator

ComicCraft is a FastAPI + Jinja2 web application that turns a user prompt into a five-panel comic. Gemini generates structured panel/story content and Hugging Face Inference Providers generate panel illustrations. The final comic can be exported as a PDF.

## Architecture

Browser -> FastAPI routes -> Gemini story generation -> image provider -> layout builder -> PDF exporter -> browser

The image layer is provider-based:
- `hf`: real hosted image generation using Hugging Face Inference Providers.
- `placeholder`: offline development mode that creates simple placeholder panel images.

This design avoids requiring a local GPU just to run the web application. A local Diffusers implementation can be added later behind the same image service interface.

## Quick start (Windows PowerShell)

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Put your API keys in `.env`, then:

```powershell
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000 and API docs at http://127.0.0.1:8000/docs.

## API

`POST /generate-comic/json`

Example JSON:

```json
{
  "story_prompt": "A brave fox explores an enchanted forest.",
  "character_name": "Milo",
  "setting": "enchanted forest",
  "tone": "dramatic",
  "art_style": "comic book"
}
```

`POST /test-image` accepts `{ "prompt": "..." }`.

## Important

AI image generation is an external service and may require an account, token, credits, or provider availability. For a no-cost code-path test, set `IMAGE_PROVIDER=placeholder`. Gemini generation still requires `GEMINI_API_KEY`.

The original project brief specified older Gemini 1.5 model names and `google-generativeai`. This implementation uses the current Google GenAI SDK and a configurable current Gemini model while preserving the brief's Flash -> story -> image -> PDF workflow.
