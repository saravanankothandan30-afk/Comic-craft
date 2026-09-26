"""Optional local Stable Diffusion implementation.

This module is intentionally not imported by the default app because local
Diffusers models can be several GB and generally need a suitable GPU/CPU setup.

To use it, install diffusers/transformers/accelerate/torch and implement the
same generate_image(prompt, panel_number) interface as image_generator.py.
"""
