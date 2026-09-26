from typing import Any
from app.models.schemas import ComicStory

def build_comic_layout(story: ComicStory, image_paths: list[str]) -> list[dict[str, Any]]:
    if len(story.panels) != len(image_paths):
        raise ValueError("Panel/story/image counts do not match.")

    layout = []
    for panel, image_path in zip(story.panels, image_paths):
        layout.append({
            "panel_number": panel.panel_number,
            "title": panel.title,
            "image_path": image_path,
            "scene_description": panel.scene_description,
            "caption": panel.caption,
            "narration": panel.narration,
            "dialogue": panel.dialogue,
            "image_prompt": panel.image_prompt,
        })
    return layout
