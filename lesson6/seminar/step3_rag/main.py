"""Entry point for the RAG-based animation generation system.

This script orchestrates the end-to-end pipeline for creating animated GIFs
from natural language dance descriptions (e.g., "танец макарена").
It integrates:
- Fuzzy-based pose retrieval from a local knowledge base
- LLM-powered pose sequencing
- Remote pose visualization via Pose API
- GIF assembly from rendered frames

Usage:
    python main.py                          # Generates "танец макарена.gif"
    python main.py "T-pose dance"          # Generates custom animation
"""

import asyncio
import sys
from src.animation_pipeline import AnimationPipeline


async def main() -> None:
    """Main entry point that runs the animation generation pipeline.

    Parses the user query from command-line arguments (or uses a default)
    and executes the full animation pipeline:
    1. Retrieve relevant poses
    2. Sequence them using an LLM
    3. Render frames via Pose API
    4. Save as an animated GIF

    The resulting GIF is saved in the `outputs/` directory with a sanitized filename.
    """
    # Use command-line arguments as query, or default to "танец макарена"
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "танец макарена"
    pipeline = AnimationPipeline()
    await pipeline.run(query)


if __name__ == "__main__":
    # Run the async main function using asyncio
    asyncio.run(main())
