"""Utilities for converting base64-encoded images and generating animated GIFs.

This module provides functions to:
- Decode base64-encoded PNG/JPEG strings into PIL Image objects
- Assemble a sequence of PIL Images into an animated GIF file

These utilities are primarily used in the RAG animation pipeline to
visualize pose sequences returned by the Pose Visualization API.
"""

import base64
import io
from PIL import Image


def base64_to_image(b64: str) -> Image.Image:
    """Convert a base64-encoded image string to a PIL Image object.

    This function decodes a base64 string (typically received from a web API)
    and loads it into a PIL Image for further processing or GIF creation.

    Args:
        b64 (str): Base64-encoded image data (without data URI prefix).

    Returns:
        Image.Image: A PIL Image object ready for manipulation or saving.

    Raises:
        binascii.Error: If the input string is not valid base64.
        PIL.UnidentifiedImageError: If the decoded bytes do not form a valid image.
    """
    img_data = base64.b64decode(b64)
    return Image.open(io.BytesIO(img_data))


def create_gif(images: list[Image.Image], output_path: str, duration: int = 500) -> None:
    """Create an animated GIF from a list of PIL Image objects.

    The first image in the list is used as the base frame, and all subsequent
    images are appended as animation frames. The resulting GIF loops indefinitely.

    Args:
        images (list[Image.Image]): Non-empty list of PIL Image objects.
        output_path (str): Filesystem path where the GIF will be saved.
        duration (int): Display duration per frame in milliseconds. Defaults to 500 ms.

    Raises:
        ValueError: If the input image list is empty.
        OSError: If the output file cannot be written (e.g., permission error).
    """
    if not images:
        raise ValueError("No images to create GIF")

    # Save the first image and append the rest as animation frames
    images[0].save(
        output_path,
        save_all=True,
        append_images=images[1:],
        duration=duration,
        loop=0  # Infinite loop
    )
