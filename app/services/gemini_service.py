
import json
import re
import time
from typing import Type, TypeVar

from google import genai
from pydantic import BaseModel

from app.config import get_settings
from app.models.schemas import (
    ComicOutline,
    ComicStory,
    PanelOutline,
    PanelStory,
)


settings = get_settings()

T = TypeVar("T", bound=BaseModel)


class GeminiService:

    def __init__(self):
        self.api_key = settings.gemini_api_key

        self.model = (
            settings.gemini_model.strip()
            if settings.gemini_model
            else "gemini-3.8-flash"
        )

        self.client = None

        if self.api_key:
            self.client = genai.Client(
                api_key=self.api_key
            )

        print(f"Gemini model: {self.model}")

    # ---------------------------------------------------------
    # Public outline generator
    # ---------------------------------------------------------

    def generate_outline(
        self,
        prompt: str,
        character_name: str,
        setting: str,
        tone: str,
        art_style: str,
    ) -> ComicOutline:

        instruction = f"""
Create a five-panel comic story outline.

Story idea:
{prompt}

Main character:
{character_name}

Setting:
{setting}

Tone:
{tone}

Art style:
{art_style}

Return ONLY valid JSON.

The JSON must have this structure:

{{
  "panels": [
    {{
      "panel_number": 1,
      "title": "Panel title",
      "scene_description": "Scene description",
      "image_prompt": "Detailed visual prompt"
    }}
  ]
}}

Create exactly five panels.

Make the story coherent from beginning
to middle to ending.

Keep the main character consistent.
"""

        result = self._ask_gemini(
            instruction,
            ComicOutline,
        )

        if result is not None:
            return result

        print(
            "Gemini unavailable. "
            "Using local comic outline fallback."
        )

        return self._fallback_outline(
            prompt,
            character_name,
            setting,
            tone,
            art_style,
        )

    # ---------------------------------------------------------
    # Public story generator
    # ---------------------------------------------------------

    def generate_story(
        self,
        outline: ComicOutline,
        prompt: str,
        character_name: str,
        tone: str,
    ) -> ComicStory:

        outline_text = outline.model_dump_json(
            indent=2
        )

        instruction = f"""
Create the complete script for a five-panel comic.

Original story:
{prompt}

Character:
{character_name}

Tone:
{tone}

Outline:
{outline_text}

Return ONLY valid JSON.

The JSON must have this structure:

{{
  "panels": [
    {{
      "panel_number": 1,
      "title": "Panel title",
      "scene_description": "Scene description",
      "caption": "Short caption",
      "narration": "Short narration",
      "dialogue": "Short dialogue",
      "image_prompt": "Detailed visual prompt"
    }}
  ]
}}

Create exactly five panels.

Keep the character and story consistent.
Keep dialogue short enough for a comic.
"""

        result = self._ask_gemini(
            instruction,
            ComicStory,
        )

        if result is not None:
            return result

        print(
            "Gemini unavailable. "
            "Using local comic story fallback."
        )

        return self._fallback_story(
            outline,
            prompt,
            character_name,
            tone,
        )

    # ---------------------------------------------------------
    # Gemini request
    # ---------------------------------------------------------

    def _ask_gemini(
        self,
        prompt: str,
        response_model: Type[T],
    ) -> T | None:

        if not self.client:
            print(
                "GEMINI_API_KEY is not configured."
            )
            return None

        for attempt in range(1, 3):

            try:

                print(
                    f"Gemini request "
                    f"{attempt}/2..."
                )

                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                )

                if not response.text:
                    raise RuntimeError(
                        "Gemini returned an empty response."
                    )

                text = self._clean_json(
                    response.text
                )

                data = json.loads(text)

                return response_model.model_validate(
                    data
                )

            except Exception as exc:

                error_text = str(exc)

                print(
                    f"Gemini error: {error_text}"
                )

                # A 503 is a temporary provider problem.
                if "503" in error_text:

                    if attempt < 2:
                        time.sleep(2)
                        continue

                    print(
                        "Gemini service unavailable. "
                        "Switching to local fallback."
                    )

                    return None

                # Do not waste time retrying malformed
                # requests or invalid authentication.
                if (
                    "400" in error_text
                    or "401" in error_text
                    or "403" in error_text
                ):
                    print(
                        "Gemini request cannot be completed. "
                        "Switching to local fallback."
                    )

                    return None

                if attempt < 2:
                    time.sleep(1)
                    continue

                return None

        return None

    # ---------------------------------------------------------
    # Clean Gemini JSON response
    # ---------------------------------------------------------

    def _clean_json(self, text: str) -> str:

        text = text.strip()

        # Remove markdown code fences.
        text = re.sub(
            r"^```json\s*",
            "",
            text,
            flags=re.IGNORECASE,
        )

        text = re.sub(
            r"^```\s*",
            "",
            text,
        )

        text = re.sub(
            r"\s*```$",
            "",
            text,
        )

        # Find the JSON object if Gemini added extra text.
        start = text.find("{")
        end = text.rfind("}")

        if start != -1 and end != -1:
            text = text[start:end + 1]

        return text

    # ---------------------------------------------------------
    # Local fallback outline
    # ---------------------------------------------------------

    def _fallback_outline(
        self,
        prompt: str,
        character_name: str,
        setting: str,
        tone: str,
        art_style: str,
    ) -> ComicOutline:

        panels = [

            PanelOutline(
                panel_number=1,
                title="The Beginning",
                scene_description=(
                    f"{character_name} begins the adventure "
                    f"in {setting}."
                ),
                image_prompt=(
                    f"{character_name} in {setting}, "
                    f"starting an exciting adventure, "
                    f"{tone} mood, {art_style} comic art."
                ),
            ),

            PanelOutline(
                panel_number=2,
                title="A Discovery",
                scene_description=(
                    f"{character_name} discovers something "
                    f"unexpected connected to the story."
                ),
                image_prompt=(
                    f"{character_name} making an important "
                    f"discovery in {setting}, expressive "
                    f"face, cinematic composition, "
                    f"{art_style} comic art."
                ),
            ),

            PanelOutline(
                panel_number=3,
                title="The Challenge",
                scene_description=(
                    f"{character_name} faces a challenge "
                    f"and must find a solution."
                ),
                image_prompt=(
                    f"{character_name} facing a challenging "
                    f"moment in {setting}, dynamic action, "
                    f"dramatic composition, {tone} mood, "
                    f"{art_style} comic art."
                ),
            ),

            PanelOutline(
                panel_number=4,
                title="The Solution",
                scene_description=(
                    f"{character_name} finds a clever way "
                    f"to overcome the challenge."
                ),
                image_prompt=(
                    f"{character_name} solving the problem "
                    f"in {setting}, hopeful expression, "
                    f"strong visual storytelling, "
                    f"{art_style} comic art."
                ),
            ),

            PanelOutline(
                panel_number=5,
                title="The Ending",
                scene_description=(
                    f"{character_name} successfully completes "
                    f"the adventure and looks toward the future."
                ),
                image_prompt=(
                    f"{character_name} celebrating the successful "
                    f"ending in {setting}, inspiring final scene, "
                    f"bright atmosphere, {art_style} comic art."
                ),
            ),
        ]

        return ComicOutline(
            panels=panels
        )

    # ---------------------------------------------------------
    # Local fallback story
    # ---------------------------------------------------------

    def _fallback_story(
        self,
        outline: ComicOutline,
        prompt: str,
        character_name: str,
        tone: str,
    ) -> ComicStory:

        story_panels = []

        for panel in outline.panels:

            number = panel.panel_number

            if number == 1:
                caption = "A new adventure begins."
                narration = (
                    f"{character_name} begins the journey."
                )
                dialogue = "Something interesting is about to happen!"

            elif number == 2:
                caption = "An unexpected discovery."
                narration = (
                    f"{character_name} discovers something unusual."
                )
                dialogue = "What is this?"

            elif number == 3:
                caption = "A difficult challenge."
                narration = (
                    f"{character_name} faces a difficult moment."
                )
                dialogue = "I need to find a solution."

            elif number == 4:
                caption = "A clever idea."
                narration = (
                    f"{character_name} discovers a way forward."
                )
                dialogue = "I know what to do!"

            else:
                caption = "A successful ending."
                narration = (
                    f"{character_name} completes the adventure."
                )
                dialogue = "We did it!"

            story_panels.append(
                PanelStory(
                    panel_number=number,
                    title=panel.title,
                    scene_description=panel.scene_description,
                    caption=caption,
                    narration=narration,
                    dialogue=dialogue,
                    image_prompt=panel.image_prompt,
                )
            )

        return ComicStory(
            panels=story_panels
        )


# -------------------------------------------------------------
# Global service
# -------------------------------------------------------------

gemini_service = GeminiService()


# -------------------------------------------------------------
# Compatibility functions used by routes.py
# -------------------------------------------------------------

def generate_outline(
    prompt: str,
    character_name: str,
    setting: str,
    tone: str,
    art_style: str,
) -> ComicOutline:

    return gemini_service.generate_outline(
        prompt,
        character_name,
        setting,
        tone,
        art_style,
    )


def generate_story(
    outline: ComicOutline,
    prompt: str,
    character_name: str,
    tone: str,
) -> ComicStory:

    return gemini_service.generate_story(
        outline,
        prompt,
        character_name,
        tone,
    )

