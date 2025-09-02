#!/usr/bin/env python3
"""
Vector Index Manager
Manages document embeddings, collections, and RAG operations.
"""

import logging
import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
import hashlib
import uuid

try:
    import chromadb
    from chromadb.config import Settings
    _chromadb_available = True
except ImportError:
    _chromadb_available = False

from app.services.enhanced_ai_orchestrator import get_ai_orchestrator

logger = logging.getLogger(__name__)


class CollectionType(str, Enum):
    """Types of document collections"""
    PROJECT_DOCS = "project_docs"
    TECHNICAL_DOCS = "technical_docs"
    BUSINESS_DOCS = "business_docs"
    USER_GUIDES = "user_guides"
    API_DOCS = "api_docs"
    CODE_SNIPPETS = "code_snippets"
    MEETING_NOTES = "meeting_notes"
    REQUIREMENTS = "requirements"


class EmbeddingStatus(str, Enum):
    """Status of embedding operations"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    UPDATED = "updated"


@dataclass
class DocumentMetadata:
    """Metadata for documents"""
    document_id: str
    title: str
    content_type: str
    project_id: Optional[int] = None
    author_id: Optional[int] = None
    created_at: datetime = None
    updated_at: datetime = None
    tags: List[str] = None
    version: str = "1.0"
    language: str = "en"
    file_size: int = 0
    word_count: int = 0
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
        if self.tags is None:
            self.tags = []


@dataclass
class CollectionConfig:
    """Configuration for document collections"""
    name: str
    collection_type: CollectionType
    description: str
    embedding_model: str = "nomic-embed-text:v1.5"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    max_documents: int = 10000
    retention_days: int = 365
    auto_refresh: bool = True
    metadata_schema: Dict[str, str] = None
    
    def __post_init__(self):
        if self.metadata_schema is None:
            self.metadata_schema = {
                "document_id": "string",
                "title": "string",
                "content_type": "string",
                "project_id": "integer",
                "author_id": "integer",
                "created_at": "datetime",
                "tags": "list"
            }


class VectorIndexManager:
    """Manages document embeddings and vector search operations"""
    
    def __init__(self, db_path: str = "./chroma_db"):
        self.chromadb_available = _chromadb_available
        self.db_path = db_path
        self.client = None
        self.collections = {}
        self.ai_orchestrator = get_ai_orchestrator()
        
        if self.chromadb_available:
            try:
                self.client = chromadb.PersistentClient(
                    path=db_path,
                    settings=Settings(
                        anonymized_telemetry=False,
                        allow_reset=True
                    )
                )
                logger.info("ChromaDB client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize ChromaDB: {str(e)}")
                self.chromadb_available = False
    
    async def create_collection(
        self,
        name: str,
        collection_type: CollectionType,
        description: str,
        config: Optional[CollectionConfig] = None
    ) -> Dict[str, Any]:
        """Create a new document collection"""
        try:
            if not self.chromadb_available:
                return {
                    "success": False,
                    "error": "ChromaDB not available"
                }
            
            if config is None:
                config = CollectionConfig(
                    name=name,
                    collection_type=collection_type,
                    description=description
                )
            
            # Create collection in ChromaDB
            collection = self.client.create_collection(name=name)
            
            self.collections[name] = {
                "collection": collection,
                "config": config,
                "stats": {
                    "document_count": 0,
                    "last_updated": datetime.now(),
                    "embedding_model": "nomic-embed-text:v1.5"
                }
            }
            
            logger.info(f"Created collection: {name}")
            
            return {
                "success": True,
                "collection_name": name,
                "collection_type": collection_type.value,
                "config": config.__dict__
            }
            
        except Exception as e:
            logger.error(f"Error creating collection {name}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def add_documents(
        self,
        collection_name: str,
        documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Add documents to a collection"""
        try:
            if not self.chromadb_available:
                return {
                    "success": False,
                    "error": "ChromaDB not available"
                }
            
            if collection_name not in self.collections:
                return {
                    "success": False,
                    "error": f"Collection {collection_name} not found"
                }
            
            collection = self.collections[collection_name]["collection"]
            config = self.collections[collection_name]["config"]
            
            # Process documents
            processed_docs = []
            embeddings = []
            metadatas = []
            ids = []
            
            for doc in documents:
                # Generate document ID if not provided
                doc_id = doc.get("document_id", str(uuid.uuid4()))
                
                # Extract content and metadata
                content = doc.get("content", "")
                metadata = doc.get("metadata", {})
                
                # Generate embedding
                embedding = await self.ai_orchestrator.get_embedding(content)
                if embedding is None:
                    logger.warning(f"Failed to generate embedding for document {doc_id}")
                    continue
                
                # Prepare for ChromaDB
                processed_docs.append(content)
                embeddings.append(embedding)
                metadatas.append(metadata)
                ids.append(doc_id)
            
            if not processed_docs:
                return {
                    "success": False,
                    "error": "No valid documents to add"
                }
            
            # Add to collection
            collection.add(
                documents=processed_docs,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            
            # Update stats
            self.collections[collection_name]["stats"]["document_count"] += len(processed_docs)
            self.collections[collection_name]["stats"]["last_updated"] = datetime.now()
            
            logger.info(f"Added {len(processed_docs)} documents to collection {collection_name}")
            
            return {
                "success": True,
                "documents_added": len(processed_docs),
                "collection_name": collection_name,
                "document_ids": ids
            }
            
        except Exception as e:
            logger.error(f"Error adding documents to {collection_name}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def search_documents(
        self,
        collection_name: str,
        query: str,
        n_results: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Search documents in a collection"""
        try:
            if not self.chromadb_available:
                return {
                    "success": False,
                    "error": "ChromaDB not available"
                }
            
            if collection_name not in self.collections:
                return {
                    "success": False,
                    "error": f"Collection {collection_name} not found"
                }
            
            collection = self.collections[collection_name]["collection"]
            
            # Generate query embedding
            query_embedding = await self.ai_orchestrator.get_embedding(query)
            if query_embedding is None:
                return {
                    "success": False,
                    "error": "Failed to generate query embedding"
                }
            
            # Search in collection
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=filter_metadata
            )
            
            # Format results
            formatted_results = []
            for i in range(len(results["ids"][0])):
                formatted_results.append({
                    "document_id": results["ids"][0][i],
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i]
                })
            
            return {
                "success": True,
                "query": query,
                "collection_name": collection_name,
                "results": formatted_results,
                "total_results": len(formatted_results)
            }
            
        except Exception as e:
            logger.error(f"Error searching in {collection_name}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """Get statistics for a collection"""
        try:
            if not self.chromadb_available:
                return {
                    "success": False,
                    "error": "ChromaDB not available"
                }
            
            if collection_name not in self.collections:
                return {
                    "success": False,
                    "error": f"Collection {collection_name} not found"
                }
            
            collection = self.collections[collection_name]["collection"]
            config = self.collections[collection_name]["config"]
            stats = self.collections[collection_name]["stats"]
            
            # Get collection info
            collection_info = collection.get()
            
            return {
                "success": True,
                "collection_name": collection_name,
                "collection_type": config.collection_type.value,
                "description": config.description,
                "document_count": len(collection_info["ids"]) if collection_info["ids"] else 0,
                "embedding_model": config.embedding_model,
                "chunk_size": config.chunk_size,
                "max_documents": config.max_documents,
                "retention_days": config.retention_days,
                "auto_refresh": config.auto_refresh,
                "last_updated": stats["last_updated"].isoformat(),
                "created_at": ""
            }
            
        except Exception as e:
            logger.error(f"Error getting stats for {collection_name}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def list_collections(self) -> Dict[str, Any]:
        """List all collections"""
        try:
            if not self.chromadb_available:
                return {
                    "success": False,
                    "error": "ChromaDB not available"
                }
            
            collections_info = []
            for name, collection_data in self.collections.items():
                stats = await self.get_collection_stats(name)
                if stats["success"]:
                    collections_info.append(stats)
            
            return {
                "success": True,
                "collections": collections_info,
                "total_collections": len(collections_info)
            }
            
        except Exception as e:
            logger.error(f"Error listing collections: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def delete_collection(self, collection_name: str) -> Dict[str, Any]:
        """Delete a collection"""
        try:
            if not self.chromadb_available:
                return {
                    "success": False,
                    "error": "ChromaDB not available"
                }
            
            if collection_name not in self.collections:
                return {
                    "success": False,
                    "error": f"Collection {collection_name} not found"
                }
            
            # Delete from ChromaDB
            self.client.delete_collection(collection_name)
            
            # Remove from local tracking
            del self.collections[collection_name]
            
            logger.info(f"Deleted collection: {collection_name}")
            
            return {
                "success": True,
                "collection_name": collection_name,
                "message": "Collection deleted successfully"
            }
            
        except Exception as e:
            logger.error(f"Error deleting collection {collection_name}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def update_document(
        self,
        collection_name: str,
        document_id: str,
        new_content: str,
        new_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Update a document in a collection"""
        try:
            if not self.chromadb_available:
                return {
                    "success": False,
                    "error": "ChromaDB not available"
                }
            
            if collection_name not in self.collections:
                return {
                    "success": False,
                    "error": f"Collection {collection_name} not found"
                }
            
            collection = self.collections[collection_name]["collection"]
            
            # Generate new embedding
            new_embedding = await self.ai_orchestrator.get_embedding(new_content)
            if new_embedding is None:
                return {
                    "success": False,
                    "error": "Failed to generate new embedding"
                }
            
            # Update document
            collection.update(
                ids=[document_id],
                documents=[new_content],
                embeddings=[new_embedding],
                metadatas=[new_metadata] if new_metadata else None
            )
            
            # Update stats
            self.collections[collection_name]["stats"]["last_updated"] = datetime.now()
            
            logger.info(f"Updated document {document_id} in collection {collection_name}")
            
            return {
                "success": True,
                "document_id": document_id,
                "collection_name": collection_name,
                "message": "Document updated successfully"
            }
            
        except Exception as e:
            logger.error(f"Error updating document {document_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        try:
            collections_list = await self.list_collections()
            
            total_documents = sum(
                collection.get("document_count", 0) 
                for collection in collections_list.get("collections", [])
            )
            
            return {
                "success": True,
                "chromadb_available": self.chromadb_available,
                "total_collections": collections_list.get("total_collections", 0),
                "total_documents": total_documents,
                "embedding_model": "nomic-embed-text:v1.5",
                "db_path": self.db_path,
                "status": "healthy" if self.chromadb_available else "unavailable"
            }
            
        except Exception as e:
            logger.error(f"Error getting system status: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }


# Global instance and getter function
_vector_index_manager = None

def get_vector_index_manager() -> VectorIndexManager:
    """Get the global vector index manager instance"""
    global _vector_index_manager
    if _vector_index_manager is None:
        _vector_index_manager = VectorIndexManager()
    return _vector_index_manager
