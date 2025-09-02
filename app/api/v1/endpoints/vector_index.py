#!/usr/bin/env python3
"""
Vector Index Management API Endpoints
Provides endpoints for document embedding management and RAG operations.
"""

import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.vector_index_manager import (
    get_vector_index_manager,
    CollectionType,
    DocumentMetadata,
    CollectionConfig
)
from app.models.project import Project
from app.models.user import User

router = APIRouter()

logger = logging.getLogger(__name__)


@router.get("/status")
async def get_vector_index_status():
    """Get vector index system status"""
    try:
        vector_manager = get_vector_index_manager()
        status = await vector_manager.get_system_status()
        
        return JSONResponse(content={
            "success": True,
            "vector_index_status": status
        })
        
    except Exception as e:
        logger.error(f"Error getting vector index status: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Failed to get status: {str(e)}"
            }
        )


@router.post("/collections")
async def create_collection(
    collection_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """Create a new document collection"""
    try:
        name = collection_data.get("name")
        collection_type = CollectionType(collection_data.get("collection_type", "project_docs"))
        description = collection_data.get("description", "")
        
        if not name:
            raise HTTPException(status_code=400, detail="Collection name is required")
        
        vector_manager = get_vector_index_manager()
        
        # Create collection configuration
        config = None
        if "config" in collection_data:
            config = CollectionConfig(
                name=name,
                collection_type=collection_type,
                description=description,
                embedding_model=collection_data["config"].get("embedding_model", "nomic-embed-text:v1.5"),
                chunk_size=collection_data["config"].get("chunk_size", 1000),
                chunk_overlap=collection_data["config"].get("chunk_overlap", 200),
                max_documents=collection_data["config"].get("max_documents", 10000),
                retention_days=collection_data["config"].get("retention_days", 365),
                auto_refresh=collection_data["config"].get("auto_refresh", True)
            )
        
        result = await vector_manager.create_collection(
            name=name,
            collection_type=collection_type,
            description=description,
            config=config
        )
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Error creating collection: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Failed to create collection: {str(e)}"
            }
        )


@router.get("/collections")
async def list_collections():
    """List all document collections"""
    try:
        vector_manager = get_vector_index_manager()
        result = await vector_manager.list_collections()
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Error listing collections: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Failed to list collections: {str(e)}"
            }
        )


@router.get("/collections/{collection_name}")
async def get_collection_stats(collection_name: str):
    """Get statistics for a specific collection"""
    try:
        vector_manager = get_vector_index_manager()
        result = await vector_manager.get_collection_stats(collection_name)
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Error getting collection stats for {collection_name}: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Failed to get collection stats: {str(e)}"
            }
        )


@router.post("/collections/{collection_name}/documents")
async def add_documents(
    collection_name: str,
    documents_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """Add documents to a collection"""
    try:
        documents = documents_data.get("documents", [])
        
        if not documents:
            raise HTTPException(status_code=400, detail="No documents provided")
        
        # Validate document format
        for doc in documents:
            if "content" not in doc:
                raise HTTPException(status_code=400, detail="Document content is required")
            
            # Add default metadata if not provided
            if "metadata" not in doc:
                doc["metadata"] = {}
            
            # Add default document ID if not provided
            if "document_id" not in doc:
                doc["document_id"] = f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        vector_manager = get_vector_index_manager()
        result = await vector_manager.add_documents(collection_name, documents)
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Error adding documents to {collection_name}: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Failed to add documents: {str(e)}"
            }
        )


@router.post("/collections/{collection_name}/search")
async def search_documents(
    collection_name: str,
    search_data: Dict[str, Any]
):
    """Search documents in a collection"""
    try:
        query = search_data.get("query")
        n_results = search_data.get("n_results", 10)
        filter_metadata = search_data.get("filter_metadata")
        
        if not query:
            raise HTTPException(status_code=400, detail="Search query is required")
        
        vector_manager = get_vector_index_manager()
        result = await vector_manager.search_documents(
            collection_name=collection_name,
            query=query,
            n_results=n_results,
            filter_metadata=filter_metadata
        )
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Error searching in {collection_name}: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Failed to search documents: {str(e)}"
            }
        )


@router.put("/collections/{collection_name}/documents/{document_id}")
async def update_document(
    collection_name: str,
    document_id: str,
    update_data: Dict[str, Any]
):
    """Update a document in a collection"""
    try:
        new_content = update_data.get("content")
        new_metadata = update_data.get("metadata")
        
        if not new_content:
            raise HTTPException(status_code=400, detail="New content is required")
        
        vector_manager = get_vector_index_manager()
        result = await vector_manager.update_document(
            collection_name=collection_name,
            document_id=document_id,
            new_content=new_content,
            new_metadata=new_metadata
        )
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Error updating document {document_id}: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Failed to update document: {str(e)}"
            }
        )


@router.delete("/collections/{collection_name}")
async def delete_collection(collection_name: str):
    """Delete a collection"""
    try:
        vector_manager = get_vector_index_manager()
        result = await vector_manager.delete_collection(collection_name)
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Error deleting collection {collection_name}: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Failed to delete collection: {str(e)}"
            }
        )


@router.post("/rag/query")
async def rag_query(
    query_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """Perform RAG query across multiple collections"""
    try:
        query = query_data.get("query")
        collections = query_data.get("collections", [])
        n_results_per_collection = query_data.get("n_results_per_collection", 5)
        filter_metadata = query_data.get("filter_metadata")
        
        if not query:
            raise HTTPException(status_code=400, detail="Query is required")
        
        if not collections:
            # Search in all collections
            vector_manager = get_vector_index_manager()
            collections_result = await vector_manager.list_collections()
            if collections_result["success"]:
                collections = [col["collection_name"] for col in collections_result["collections"]]
        
        vector_manager = get_vector_index_manager()
        all_results = []
        
        for collection_name in collections:
            try:
                result = await vector_manager.search_documents(
                    collection_name=collection_name,
                    query=query,
                    n_results=n_results_per_collection,
                    filter_metadata=filter_metadata
                )
                
                if result["success"]:
                    all_results.extend(result["results"])
            except Exception as e:
                logger.warning(f"Failed to search in collection {collection_name}: {str(e)}")
                continue
        
        # Sort results by distance (relevance)
        all_results.sort(key=lambda x: x["distance"])
        
        # Limit total results
        max_total_results = query_data.get("max_total_results", 20)
        all_results = all_results[:max_total_results]
        
        return JSONResponse(content={
            "success": True,
            "query": query,
            "collections_searched": collections,
            "total_results": len(all_results),
            "results": all_results
        })
        
    except Exception as e:
        logger.error(f"Error performing RAG query: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Failed to perform RAG query: {str(e)}"
            }
        )


@router.post("/documents/upload")
async def upload_documents(
    background_tasks: BackgroundTasks,
    collection_name: str = None,
    project_id: int = None,
    documents: List[Dict[str, Any]] = None
):
    """Upload and process documents for embedding"""
    try:
        if not documents:
            raise HTTPException(status_code=400, detail="No documents provided")
        
        if not collection_name:
            collection_name = f"project_{project_id}_docs" if project_id else "general_docs"
        
        # Process documents for embedding
        processed_documents = []
        
        for doc in documents:
            # Extract text content
            content = doc.get("content", "")
            if not content:
                continue
            
            # Create metadata
            metadata = {
                "title": doc.get("title", "Untitled"),
                "content_type": doc.get("content_type", "text"),
                "project_id": project_id,
                "author_id": doc.get("author_id"),
                "created_at": datetime.now().isoformat(),
                "tags": doc.get("tags", []),
                "file_size": len(content),
                "word_count": len(content.split())
            }
            
            processed_documents.append({
                "document_id": doc.get("document_id", f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
                "content": content,
                "metadata": metadata
            })
        
        if not processed_documents:
            raise HTTPException(status_code=400, detail="No valid documents to process")
        
        # Add to collection
        vector_manager = get_vector_index_manager()
        result = await vector_manager.add_documents(collection_name, processed_documents)
        
        return JSONResponse(content={
            "success": True,
            "documents_processed": len(processed_documents),
            "collection_name": collection_name,
            "upload_result": result
        })
        
    except Exception as e:
        logger.error(f"Error uploading documents: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Failed to upload documents: {str(e)}"
            }
        )


@router.get("/analytics/usage")
async def get_usage_analytics():
    """Get usage analytics for vector index"""
    try:
        vector_manager = get_vector_index_manager()
        
        # Get system status
        status = await vector_manager.get_system_status()
        
        # Get collections list
        collections = await vector_manager.list_collections()
        
        # Calculate analytics
        analytics = {
            "total_collections": status.get("total_collections", 0),
            "total_documents": status.get("total_documents", 0),
            "embedding_model": status.get("embedding_model", "nomic-embed-text:v1.5"),
            "system_status": status.get("status", "unknown"),
            "collections_breakdown": {},
            "document_distribution": {},
            "usage_trends": {
                "collections_growth": 0,
                "documents_growth": 0
            }
        }
        
        if collections["success"]:
            for collection in collections["collections"]:
                collection_type = collection.get("collection_type", "unknown")
                document_count = collection.get("document_count", 0)
                
                # Collections breakdown
                if collection_type not in analytics["collections_breakdown"]:
                    analytics["collections_breakdown"][collection_type] = 0
                analytics["collections_breakdown"][collection_type] += 1
                
                # Document distribution
                if collection_type not in analytics["document_distribution"]:
                    analytics["document_distribution"][collection_type] = 0
                analytics["document_distribution"][collection_type] += document_count
        
        return JSONResponse(content={
            "success": True,
            "analytics": analytics
        })
        
    except Exception as e:
        logger.error(f"Error getting usage analytics: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Failed to get analytics: {str(e)}"
            }
        )
