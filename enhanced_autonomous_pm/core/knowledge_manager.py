#!/usr/bin/env python3
"""Knowledge manager for document ingestion and indexing via RAG."""
from typing import List, Dict, Any
import os

try:
    from enhanced_autonomous_pm.core.rag_engine import RAGKnowledgeEngine
except Exception:
    RAGKnowledgeEngine = None


class KnowledgeManager:
    def __init__(self):
        self.rag = RAGKnowledgeEngine() if RAGKnowledgeEngine else None

    def add_documents(self, docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not self.rag or not self.rag.enabled:
            return {"success": False, "error": "RAG engine unavailable"}
        ids = [d["id"] for d in docs]
        texts = [d["text"] for d in docs]
        metas = [d.get("metadata", {}) for d in docs]
        self.rag._add_records(ids, texts, metas)
        return {"success": True, "count": len(docs)}

    def refresh_indexes(self) -> Dict[str, Any]:
        if not self.rag:
            return {"success": False, "error": "RAG engine unavailable"}
        return self.rag.index_existing_project_data()

