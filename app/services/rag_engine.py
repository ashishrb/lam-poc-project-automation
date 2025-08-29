import logging
import json
import hashlib
from typing import Dict, List, Any, Optional
from datetime import datetime
import httpx
import chromadb
from chromadb.config import Settings

from app.core.config import settings
from app.models.document import Document, DocumentChunk

logger = logging.getLogger(__name__)


class RAGEngine:
    """RAG (Retrieval-Augmented Generation) engine for document processing and search"""
    
    def __init__(self):
        self.chroma_client = None
        self.collection_name = "project_documents"
        self.collection = None
        self.ollama_client = None
    
    def _initialize_clients(self):
        """Initialize clients lazily when needed"""
        if self.chroma_client is None:
            self.chroma_client = chromadb.HttpClient(
                host=settings.CHROMA_HOST,
                port=settings.CHROMA_PORT
            )
            self.collection = self._get_or_create_collection()
            self.ollama_client = httpx.AsyncClient(base_url=settings.OLLAMA_BASE_URL)
    
    def _get_or_create_collection(self):
        """Get or create the document collection"""
        try:
            # Try to get existing collection
            collection = self.chroma_client.get_collection(self.collection_name)
            logger.info(f"Using existing collection: {self.collection_name}")
        except Exception:
            # Create new collection
            collection = self.chroma_client.create_collection(
                name=self.collection_name,
                metadata={"description": "Project documents and knowledge base"}
            )
            logger.info(f"Created new collection: {self.collection_name}")
        
        return collection
    
    async def ingest_document(
        self,
        file_path: str,
        metadata: Dict[str, Any],
        project_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Ingest a document into the RAG system"""
        try:
            self._initialize_clients()
            # Read document content
            content = await self._read_document(file_path)
            
            # Chunk the document
            chunks = self._chunk_document(content, metadata)
            
            # Generate embeddings for chunks
            embeddings = await self._generate_embeddings([chunk["content"] for chunk in chunks])
            
            # Store in Chroma
            document_ids = []
            for i, chunk in enumerate(chunks):
                doc_id = f"{metadata['file_name']}_{i}_{hashlib.md5(chunk['content'].encode()).hexdigest()[:8]}"
                document_ids.append(doc_id)
                
                # Add metadata
                chunk_metadata = {
                    **metadata,
                    **chunk["metadata"],
                    "chunk_index": i,
                    "project_id": project_id,
                    "ingestion_date": datetime.now().isoformat()
                }
                
                # Store in Chroma
                self.collection.add(
                    documents=[chunk["content"]],
                    metadatas=[chunk_metadata],
                    ids=[doc_id]
                )
            
            logger.info(f"Ingested document {metadata['file_name']} with {len(chunks)} chunks")
            
            return {
                "success": True,
                "document_name": metadata["file_name"],
                "chunks_created": len(chunks),
                "document_ids": document_ids
            }
            
        except Exception as e:
            logger.error(f"Error ingesting document: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _read_document(self, file_path: str) -> str:
        """Read document content based on file type"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Try with different encoding
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.read()
    
    def _chunk_document(
        self,
        content: str,
        metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Chunk document into smaller pieces"""
        chunks = []
        chunk_size = settings.CHUNK_SIZE
        overlap = settings.CHUNK_OVERLAP
        
        # Simple text chunking
        start = 0
        chunk_index = 0
        
        while start < len(content):
            end = start + chunk_size
            
            # Try to break at sentence boundary
            if end < len(content):
                # Look for sentence endings
                for i in range(end, max(start, end - 100), -1):
                    if content[i] in '.!?':
                        end = i + 1
                        break
            
            chunk_content = content[start:end].strip()
            
            if chunk_content:
                chunks.append({
                    "content": chunk_content,
                    "metadata": {
                        "chunk_index": chunk_index,
                        "start_char": start,
                        "end_char": end,
                        "file_name": metadata.get("file_name", "unknown"),
                        "document_type": metadata.get("document_type", "unknown"),
                        "sensitivity": metadata.get("sensitivity_level", "public")
                    }
                })
            
            chunk_index += 1
            start = max(start + 1, end - overlap)
        
        return chunks
    
    async def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using Ollama"""
        try:
            embeddings = []
            
            for text in texts:
                response = await self.ollama_client.post(
                    "/api/embeddings",
                    json={
                        "model": settings.OLLAMA_EMBED_MODEL,
                        "prompt": text
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    embedding = result.get("embedding", [])
                    embeddings.append(embedding)
                else:
                    # Fallback to simple embedding (not recommended for production)
                    logger.warning("Using fallback embedding generation")
                    embeddings.append([0.0] * 384)  # Default dimension
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            # Return zero vectors as fallback
            return [[0.0] * 384] * len(texts)
    
    async def search(
        self,
        query: str,
        filters: Dict[str, Any] = None,
        k: int = 5
    ) -> Dict[str, Any]:
        """Search documents using semantic similarity"""
        try:
            self._initialize_clients()
            # Generate query embedding
            query_embedding = await self._generate_embeddings([query])
            
            if not query_embedding or not query_embedding[0]:
                return {"items": [], "metadata": {"error": "Failed to generate query embedding"}}
            
            # Build search filters
            where_clause = {}
            if filters:
                if "project_id" in filters:
                    where_clause["project_id"] = filters["project_id"]
                if "document_type" in filters:
                    where_clause["document_type"] = filters["document_type"]
                if "sensitivity" in filters:
                    where_clause["sensitivity"] = filters["sensitivity"]
            
            # Search in Chroma
            results = self.collection.query(
                query_embeddings=query_embedding,
                n_results=k,
                where=where_clause if where_clause else None,
                include=["metadatas", "documents", "distances"]
            )
            
            # Format results
            items = []
            for i in range(len(results["ids"][0])):
                item = {
                    "id": results["ids"][0][i],
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "score": 1.0 - results["distances"][0][i] if results["distances"] else 0.0
                }
                items.append(item)
            
            # Sort by score
            items.sort(key=lambda x: x["score"], reverse=True)
            
            return {
                "items": items,
                "query": query,
                "total_found": len(items),
                "metadata": {
                    "search_filters": filters,
                    "k": k,
                    "search_timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return {
                "items": [],
                "metadata": {"error": str(e)}
            }
    
    async def get_document_chunks(
        self,
        document_id: str,
        chunk_indices: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """Get specific chunks from a document"""
        try:
            # Build query
            where_clause = {"document_id": document_id}
            if chunk_indices:
                where_clause["chunk_index"] = {"$in": chunk_indices}
            
            # Query Chroma
            results = self.collection.query(
                query_embeddings=[[0.0] * 384],  # Dummy embedding for metadata query
                n_results=100,
                where=where_clause,
                include=["metadatas", "documents"]
            )
            
            chunks = []
            for i in range(len(results["ids"][0])):
                chunk = {
                    "id": results["ids"][0][i],
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i]
                }
                chunks.append(chunk)
            
            return chunks
            
        except Exception as e:
            logger.error(f"Error getting document chunks: {e}")
            return []
    
    async def update_document(
        self,
        document_id: str,
        new_content: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """Update an existing document"""
        try:
            # Delete existing chunks
            self.collection.delete(where={"document_id": document_id})
            
            # Re-ingest with new content
            chunks = self._chunk_document(new_content, metadata)
            embeddings = await self._generate_embeddings([chunk["content"] for chunk in chunks])
            
            # Store new chunks
            for i, chunk in enumerate(chunks):
                chunk_id = f"{document_id}_{i}"
                chunk_metadata = {
                    **metadata,
                    **chunk["metadata"],
                    "document_id": document_id,
                    "updated_date": datetime.now().isoformat()
                }
                
                self.collection.add(
                    documents=[chunk["content"]],
                    metadatas=[chunk_metadata],
                    ids=[chunk_id]
                )
            
            logger.info(f"Updated document {document_id} with {len(chunks)} chunks")
            return True
            
        except Exception as e:
            logger.error(f"Error updating document: {e}")
            return False
    
    async def delete_document(self, document_id: str) -> bool:
        """Delete a document and all its chunks"""
        try:
            self.collection.delete(where={"document_id": document_id})
            logger.info(f"Deleted document {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            return False
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        try:
            count = self.collection.count()
            
            return {
                "collection_name": self.collection_name,
                "total_documents": count,
                "status": "healthy",
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {
                "collection_name": self.collection_name,
                "total_documents": 0,
                "status": "error",
                "error": str(e)
            }
    
    async def reindex_collection(self) -> Dict[str, Any]:
        """Reindex the entire collection"""
        try:
            # Get all documents
            results = self.collection.get(include=["metadatas", "documents"])
            
            # Clear collection
            self.collection.delete(where={})
            
            # Re-ingest all documents
            total_chunks = 0
            for i, doc_id in enumerate(results["ids"]):
                metadata = results["metadatas"][i]
                content = results["documents"][i]
                
                # Re-chunk and re-embed
                chunks = self._chunk_document(content, metadata)
                embeddings = await self._generate_embeddings([chunk["content"] for chunk in chunks])
                
                # Store chunks
                for j, chunk in enumerate(chunks):
                    chunk_id = f"{doc_id}_{j}"
                    chunk_metadata = {
                        **metadata,
                        **chunk["metadata"],
                        "reindexed_date": datetime.now().isoformat()
                    }
                    
                    self.collection.add(
                        documents=[chunk["content"]],
                        metadatas=[chunk_metadata],
                        ids=[chunk_id]
                    )
                
                total_chunks += len(chunks)
            
            logger.info(f"Reindexed collection with {total_chunks} chunks")
            
            return {
                "success": True,
                "total_chunks": total_chunks,
                "reindexed_date": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error reindexing collection: {e}")
            return {
                "success": False,
                "error": str(e)
            }
