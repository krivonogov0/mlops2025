"""Main pipeline for generating animations from text queries using RAG and LLM.

This module orchestrates the complete workflow:
1. Retrieve relevant poses from a knowledge base using fuzzy matching.
2. Use an LLM to select and order poses into a coherent animation sequence.
3. Visualize each pose via a remote Pose API.
4. Assemble the resulting images into an animated GIF.

The pipeline integrates with external services:
- Pose Visualization API (default: http://localhost:8001)
- LLM inference server (configured in AnimationAgent)
"""

import httpx
from pathlib import Path
from typing import Any

from .rag_retriever import RAGRetriever
from .animation_agent import AnimationAgent
from .gif_generator import create_gif, base64_to_image


class AnimationPipeline:
    """End-to-end animation generation pipeline from natural language queries.

    This class coordinates retrieval, LLM-based sequencing, pose visualization,
    and GIF assembly to produce animated outputs based on user input.

    Attributes:
        retriever (RAGRetriever): Handles pose retrieval from the local knowledge base.
        agent (AnimationAgent): Interfaces with the LLM to generate pose sequences.
        pose_api_url (str): Base URL of the Pose Visualization API.
    """

    def __init__(self, pose_api_url: str = "http://localhost:8001") -> None:
        """Initialize the animation pipeline with default service URLs.

        Args:
            pose_api_url (str): URL of the Pose Visualization API. Defaults to local dev server.
        """
        self.retriever = RAGRetriever()
        self.agent = AnimationAgent()
        self.pose_api_url = pose_api_url

    async def _visualize_pose(self, pose: dict[str, Any]) -> str:
        """Send a pose dictionary to the Pose API and return a base64-encoded PNG.

        The pose is wrapped in a {"pose": {...}} structure as required by the API.

        Args:
            pose (dict[str, Any]): Pose data with keys like "Torso", "Head", etc.

        Returns:
            str: Base64-encoded PNG image string.

        Raises:
            RuntimeError: If the Pose API returns a non-200 status code.
        """
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{self.pose_api_url}/visualize",
                json={"pose": pose}  # API expects pose under "pose" key
            )
            if resp.status_code != 200:
                raise RuntimeError(f"Pose API error: {resp.text}")
            return resp.json()["image"]

    async def run(self, query: str) -> str:
        """Generate an animated GIF from a natural language query.

        This method executes the full pipeline:
        - Retrieves candidate poses using fuzzy matching
        - Uses an LLM to select and order poses
        - Renders each pose via the Pose API
        - Saves the result as a GIF in the outputs/ directory

        Args:
            query (str): Natural language description of the desired animation
                (e.g., "танец макарена").

        Returns:
            str: Filesystem path to the generated GIF.

        Example:
            >>> pipeline = AnimationPipeline()
            >>> path = await pipeline.run("T-pose")
            >>> print(path)
            outputs/T-pose.gif
        """
        print(f"🎬 Generating animation for: {query}")

        # Step 1: Retrieve candidate poses using fuzzy text matching
        candidates = self.retriever.retrieve(query)
        print(f"🔍 Retrieved {len(candidates)} candidate poses")

        # Step 2: Use LLM to select and order poses into a coherent sequence
        sequence = await self.agent.select_sequence(query, candidates)
        print(f"🤖 LLM selected {len(sequence)} poses for animation")

        # Step 3: Visualize each pose via the Pose API
        frames_b64 = []
        for i, pose in enumerate(sequence):
            print(f"... Rendering frame {i+1}/{len(sequence)}...")
            b64 = await self._visualize_pose(pose["pose"])
            frames_b64.append(b64)

        # Step 4: Assemble frames into an animated GIF
        images = [base64_to_image(b64) for b64 in frames_b64]
        output_dir = Path("outputs")
        output_dir.mkdir(exist_ok=True)
        safe_filename = "".join(c for c in query.replace(" ", "_") if c.isalnum() or c in "._-")
        output_path = output_dir / f"{safe_filename}.gif"
        create_gif(images, str(output_path), duration=600)

        print(f"[OK]: Animation saved to: {output_path}")
        return str(output_path)
