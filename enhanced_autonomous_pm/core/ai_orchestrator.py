#!/usr/bin/env python3
from typing import Dict, Any, Optional, List
import logging

try:
    import ollama
    _ollama_available = True
except Exception:
    _ollama_available = False


class EnhancedAIOrchestrator:
    """Three-model coordination (xLAM, gpt-oss:20b, nomic-embed).
    Routes queries and provides embeddings for RAG.
    """

    def __init__(self):
        self.xlam_model = "Salesforce/xLAM-1b-fc-r"
        self.strategic_model = "gpt-oss:20b"
        self.embedding_model = "nomic-embed-text:v1.5"
        self.ollama_available = _ollama_available
        if not self.ollama_available:
            logging.warning("Ollama not available; running in xLAM-only mode")

    def _score_complexity(self, query: str) -> int:
        q = query.lower()
        indicators = [("strategy",3),("plan",2),("predict",2),("analysis",2),("optimize",2),("risk",1),("budget",1),("stakeholder",1),("lifecycle",2),("autonomous",1)]
        base = 3 if len(q) > 120 else 2
        return min(10, base + sum(w for k, w in indicators if k in q))

    def get_embedding(self, text: str) -> Optional[List[float]]:
        if not self.ollama_available:
            return None
        try:
            resp = ollama.embeddings(model=self.embedding_model, prompt=text)
            return resp.get("embedding")
        except Exception as e:
            logging.warning(f"Embedding failed: {e}")
            return None

    def route_query_to_appropriate_model(self, query: str, complexity_level: Optional[int] = None) -> Dict[str, Any]:
        score = complexity_level if complexity_level is not None else self._score_complexity(query)
        route = {"complexity_score": score, "use_embeddings": score>=5 and self.ollama_available, "selected_model": self.xlam_model, "provider":"transformers"}
        if self.ollama_available and score >= 6:
            route.update({"selected_model": self.strategic_model, "provider": "ollama"})
        simple_triggers = ["write file","read file","generate report","get weather","tool","function","call","api"]
        if any(t in query.lower() for t in simple_triggers):
            route.update({"selected_model": self.xlam_model, "provider": "transformers"})
        return route

