#!/usr/bin/env python3
"""
RAG Knowledge Engine
Indexes existing project data and provides retrieval for contextualized QA.
"""

from typing import List, Dict, Any, Optional
import os
import sqlite3
import logging
from datetime import datetime
import json

try:
    import numpy as np
except Exception:
    np = None  # Fallback

try:
    import chromadb
    from chromadb.config import Settings
    _chroma_available = True
except Exception:
    _chroma_available = False

# Local orchestrator for embeddings (Ollama nomic-embed)
try:
    from enhanced_lam_integration import EnhancedAIOrchestrator
except Exception:
    EnhancedAIOrchestrator = None


class RAGKnowledgeEngine:
    """Lightweight RAG wrapper using Chroma for vector storage."""

    def __init__(self, persist_dir: str = "enhanced_autonomous_pm/data/vector_store", embedding_model: str = "nomic-embed-text:v1.5"):
        self.embedding_model = embedding_model
        self.persist_dir = persist_dir
        self.enabled = _chroma_available
        self._ensure_storage()

        self.orchestrator = EnhancedAIOrchestrator() if EnhancedAIOrchestrator else None

        self.client = None
        self.collection = None
        if self.enabled:
            self.client = chromadb.Client(Settings(persist_directory=self.persist_dir, anonymized_telemetry=False))
            self.collection = self.client.get_or_create_collection(name="enterprise_knowledge")
        else:
            logging.warning("ChromaDB is not available. RAG features will be disabled.")

    def _ensure_storage(self):
        try:
            os.makedirs(self.persist_dir, exist_ok=True)
        except Exception:
            pass

    def _embed(self, texts: List[str]) -> Optional[List[List[float]]]:
        """Generate embeddings using Ollama if available; fallback to simple hashing."""
        if self.orchestrator and getattr(self.orchestrator, "ollama_available", False):
            vecs = []
            for t in texts:
                v = self.orchestrator.get_embedding(t)
                if v:
                    vecs.append(v)
            if len(vecs) == len(texts):
                return vecs

        # Fallback embedding: deterministic hashing to vector space
        if np is None:
            return None
        vecs = []
        for t in texts:
            rng = np.random.default_rng(abs(hash(t)) % (2**32))
            vecs.append(rng.normal(size=768).tolist())
        return vecs

    def _add_records(self, ids: List[str], texts: List[str], metadatas: List[Dict[str, Any]]):
        if not self.enabled or not self.collection:
            return
        try:
            embeddings = self._embed(texts)
            self.collection.add(ids=ids, documents=texts, metadatas=metadatas, embeddings=embeddings)
        except Exception as e:
            logging.warning(f"Vector add failed, retrying without embeddings: {e}. Trying documents-only mode.")
            try:
                self.collection.add(ids=ids, documents=texts, metadatas=metadatas)
            except Exception as e2:
                logging.error(f"Chroma add failed: {e2}")

    def index_existing_project_data(self, autonomous_db: str = "autonomous_projects.db", updates_db: str = "project_updates.db") -> Dict[str, Any]:
        """Index data from existing SQLite databases into vector store."""
        if not self.enabled or not self.collection:
            return {"success": False, "error": "ChromaDB not available"}

        indexed = 0
        sources = []

        # Index project records
        if os.path.exists(autonomous_db):
            with sqlite3.connect(autonomous_db) as conn:
                c = conn.cursor()
                try:
                    c.execute("SELECT project_id, name, description, status, client_name, project_manager FROM projects")
                    rows = c.fetchall()
                    ids, texts, metas = [], [], []
                    for r in rows:
                        pid, name, desc, status, client, pm = r
                        text = f"Project {name} ({pid})\nStatus: {status}\nClient: {client}\nManager: {pm}\nDescription: {desc or ''}"
                        ids.append(f"proj:{pid}")
                        texts.append(text)
                        metas.append({"type": "project", "project_id": pid, "name": name, "status": status})
                    if ids:
                        self._add_records(ids, texts, metas)
                        indexed += len(ids)
                        sources.append("projects")
                except Exception as e:
                    logging.warning(f"Project indexing skipped: {e}")

                # Employee performance
                try:
                    c.execute("SELECT employee_id, employee_name, project_id, quarter, quality_score, achievements FROM employee_performance")
                    rows = c.fetchall()
                    ids, texts, metas = [], [], []
                    for r in rows:
                        eid, ename, pid, qtr, qscore, ach = r
                        ach_list = []
                        try:
                            ach_list = json.loads(ach) if ach else []
                        except Exception:
                            ach_list = []
                        text = f"Employee {ename} ({eid}) on {pid} {qtr}\nQuality: {qscore}\nAchievements: {', '.join(ach_list)}"
                        ids.append(f"empperf:{eid}:{qtr}")
                        texts.append(text)
                        metas.append({"type": "employee_performance", "employee_id": eid, "project_id": pid, "quarter": qtr})
                    if ids:
                        self._add_records(ids, texts, metas)
                        indexed += len(ids)
                        sources.append("employee_performance")
                except Exception as e:
                    logging.warning(f"Employee performance indexing skipped: {e}")

        # Index daily updates from Flask app
        if os.path.exists(updates_db):
            with sqlite3.connect(updates_db) as conn:
                c = conn.cursor()
                try:
                    c.execute("SELECT id, name, project, update, date FROM updates")
                    rows = c.fetchall()
                    ids, texts, metas = [], [], []
                    for r in rows:
                        uid, name, project, text, date = r
                        doc = f"Update {uid} by {name} on {date}\nProject: {project}\n{text}"
                        ids.append(f"update:{uid}")
                        texts.append(doc)
                        metas.append({"type": "update", "project": project, "author": name, "date": date})
                    if ids:
                        self._add_records(ids, texts, metas)
                        indexed += len(ids)
                        sources.append("updates")
                except Exception as e:
                    logging.warning(f"Updates indexing skipped: {e}")

        # Company policies and best practices (sample docs)
        self._index_sample_policies()
        sources.append("policies")

        return {"success": True, "indexed": indexed, "sources": list(set(sources))}

    def _index_sample_policies(self):
        policies = [
            ("policy:security", "Company Security Policy", "Follow least privilege; rotate secrets; MFA required."),
            ("policy:quality", "Quality Standards", "All code requires peer review; 90% unit test coverage target."),
            ("policy:pm", "Project Management Best Practices", "Weekly status, risk logs, stakeholder updates, and retrospectives.")
        ]
        ids = [p[0] for p in policies]
        texts = [f"{p[1]}\n{p[2]}" for p in policies]
        metas = [{"type": "policy", "title": p[1]} for p in policies]
        if self.enabled and self.collection:
            self._add_records(ids, texts, metas)

    def enhance_query_with_context(self, user_query: str, top_k: int = 5) -> Dict[str, Any]:
        if not self.enabled or not self.collection:
            return {"success": False, "error": "ChromaDB not available"}
        try:
            # Try embedding query; fallback to text search
            query_embedding = None
            if self.orchestrator and getattr(self.orchestrator, "ollama_available", False):
                query_embedding = self.orchestrator.get_embedding(user_query)

            if query_embedding is not None:
                res = self.collection.query(query_embeddings=[query_embedding], n_results=top_k)
            else:
                res = self.collection.query(query_texts=[user_query], n_results=top_k)

            contexts = []
            for i in range(len(res.get("ids", [[]])[0])):
                item = {
                    "id": res["ids"][0][i],
                    "text": res["documents"][0][i],
                    "metadata": res["metadatas"][0][i]
                }
                contexts.append(item)

            augmented = user_query + "\n\nRelevant Context:\n" + "\n---\n".join(c["text"] for c in contexts)
            return {"success": True, "augmented_query": augmented, "contexts": contexts}
        except Exception as e:
            return {"success": False, "error": f"RAG retrieval failed: {e}"}
