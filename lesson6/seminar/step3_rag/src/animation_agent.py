"""Agent that uses an LLM to select and order poses for animation sequences.

This module implements an AnimationAgent that communicates with a local
LLM server (e.g., Ollama or vLLM) to generate coherent pose sequences
from natural language dance descriptions. The agent formats a prompt with
available poses and expects a structured JSON response.
"""

import json
import httpx
from typing import List, Dict, Any


class AnimationAgent:
    """LLM-powered agent for selecting pose sequences from text descriptions.

    This agent constructs a prompt containing candidate pose descriptions,
    sends it to an LLM inference server, and parses the JSON response to
    extract an ordered list of poses. It includes fallback logic in case
    the LLM response is malformed or unavailable.

    Attributes:
        llm_url (str): Base URL of the LLM inference server (e.g., Ollama or vLLM).
    """

    def __init__(self, llm_url: str = "http://localhost:11434/v1"):
        """Initialize the agent with the LLM server endpoint.

        Note: Port 11434 is the default for Ollama. If using vLLM (port 8000),
        adjust the URL accordingly.

        Args:
            llm_url (str): URL of the OpenAI-compatible LLM API.
        """
        self.llm_url = llm_url

    async def select_sequence(self, query: str, candidate_poses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Select an ordered sequence of poses for animation using an LLM.

        Constructs a prompt listing available pose descriptions and asks the LLM
        to choose a coherent sequence (e.g., for a dance). Expects a JSON response
        with a "sequence" key containing description strings.

        Args:
            query (str): Natural language description of the desired animation
                (e.g., "танец макарена").
            candidate_poses (List[Dict]): List of pose entries, each containing
                at least a "description" key.

        Returns:
            List[Dict]: Ordered list of pose dictionaries matching the LLM's selection.
                        Falls back to the first 7 candidate poses if parsing fails.

        Raises:
            RuntimeError: If the LLM server returns a non-200 HTTP status.
        """
        descriptions = [p["description"] for p in candidate_poses]
        prompt = f"""
Ты — аниматор танцев. Пользователь просит: "{query}".
Вот доступные позы:
{chr(10).join(f"{i+1}. {desc}" for i, desc in enumerate(descriptions))}

Выбери оптимальную последовательность из 7 поз для анимации танца.
Верни ТОЛЬКО JSON в формате:
{{"sequence": ["описание позы 1", "описание позы 2", ...]}}
Без пояснений.
"""

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{self.llm_url}/chat/completions",
                json={
                    "model": "qwen2.5:1.5b",  # Ollama model tag
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                    "max_tokens": 200
                }
            )
            if resp.status_code != 200:
                raise RuntimeError(f"LLM error: {resp.text}")
            text = resp.json()["choices"][0]["message"]["content"]

        try:
            # Extract JSON from LLM response (robust to leading/trailing text)
            start = text.find("{")
            end = text.rfind("}") + 1
            if start == -1 or end == 0:
                raise ValueError("No JSON object found in LLM response")
            json_str = text[start:end]
            data = json.loads(json_str)
            selected_descs = data["sequence"]

            # Map descriptions back to full pose objects
            pose_map = {p["description"]: p for p in candidate_poses}
            return [pose_map[desc] for desc in selected_descs if desc in pose_map]

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"⚠️ LLM response parsing failed: {e}")
            print(f"Raw LLM output: {text}")
            # Fallback: return first 7 poses if LLM fails
            return candidate_poses[:7]
