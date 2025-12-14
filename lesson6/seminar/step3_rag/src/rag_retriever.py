"""Module for retrieving relevant poses from a knowledge base using fuzzy text matching."""

import json
from fuzzywuzzy import fuzz


class RAGRetriever:
    """Retrieves relevant pose entries from a JSON-based knowledge base using fuzzy string matching.

    This class implements a simple but effective retrieval mechanism for RAG (Retrieval-Augmented
    Generation) systems. Given a natural language query, it ranks pose descriptions by similarity
    using partial ratio matching and returns the top-k most relevant entries.

    Attributes:
        poses (list[dict]): List of pose entries loaded from the database file.
                            Each entry must contain at least a "description" key.
    """

    def __init__(self, db_path: str = "data/poses_database.json") -> None:
        """Initializes the retriever by loading pose data from a JSON file.

        Args:
            db_path (str): Path to the JSON file containing pose entries.
                Defaults to "data/poses_database.json".
        """
        with open(db_path, "r", encoding="utf-8") as f:
            self.poses = json.load(f)

    def retrieve(self, query: str, top_k: int = 7) -> list:
        """Retrieves the top-k most relevant poses for a given query using fuzzy matching.

        This method computes a partial ratio similarity score between the query and each pose
        description. It then returns the top-k entries with the highest scores.

        Args:
            query (str): Natural language query describing the desired pose or motion.
            top_k (int): Number of top-ranked poses to return. Defaults to 7.

        Returns:
            list[dict]: List of pose entries (dictionaries) sorted by relevance.
        """
        scored = []
        query_lower = query.lower()

        for item in self.poses:
            # Use partial_ratio for robust substring matching (e.g., "macarena" in long description)
            score = fuzz.partial_ratio(query_lower, item["description"].lower())
            scored.append((score, item))

        # Sort in descending order of similarity score
        scored.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored[:top_k]]
