from app.models.schemas import PromptRequest

def test_prompt_request():
    item = PromptRequest(
        story_prompt="A fox explores a forest.",
        character_name="Milo",
        setting="forest",
        tone="funny",
        art_style="comic book",
    )
    assert item.character_name == "Milo"
