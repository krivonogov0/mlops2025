"""RAG-based animation generation pipeline for dance sequences from natural language.

This package implements an end-to-end system that:
- Retrieves relevant human poses from a structured knowledge base (RAG),
- Uses a local LLM to sequence poses into coherent animations (e.g., "Macarena dance"),
- Renders each pose via a remote Pose Visualization API,
- Assembles the resulting frames into an animated GIF.

The core components are:
- `RAGRetriever`: Fuzzy-matching pose retrieval from JSON database.
- `AnimationAgent`: LLM-powered pose sequencing using structured prompting.
- `AnimationPipeline`: Orchestrates the full workflow from query to GIF.
- `gif_generator`: Utilities for base64-to-PIL conversion and GIF assembly.

Designed to integrate with external services:
- LLM server (Ollama/vLLM) on http://localhost:11434 or http://localhost:8000
- Pose Visualization API on http://localhost:8001

Entry point: `AnimationPipeline.run(query: str) -> str`
"""
