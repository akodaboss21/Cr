"""
Knowledge Module - Controller
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import datetime
import json

from packages.core.database import get_db
from packages.core.security import get_current_user, sanitize_input, detect_prompt_injection
from packages.core.identity.knowledge.models import Knowledge
from packages.core.identity.schemas import (
    KnowledgeCreate, KnowledgeUpdate, KnowledgeResponse
)
from packages.core.ai.gateway import LLMGateway
from packages.core.ai.retrieval import KnowledgeSearchEngine

router = APIRouter(prefix="/knowledge", tags=["knowledge"])
llm_gateway = LLMGateway()
search_engine = KnowledgeSearchEngine(llm_gateway=llm_gateway)

@router.post("/", response_model=KnowledgeResponse)
async def create_knowledge(
    knowledge_create: KnowledgeCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new knowledge entry and embed it when possible."""
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    embedding_vector = None
    processed = False
    # Sanitize inputs and check for prompt injection
    sanitized = sanitize_input(knowledge_create.dict())
    if detect_prompt_injection(sanitized.get("title", "") + "\n" + sanitized.get("content", "")):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Knowledge content contains unsafe instructions.")

    try:
        response = await llm_gateway.embed(
            texts=[f"{sanitized.get('title', '')}\n{sanitized.get('content', '')}"],
            model="text-embedding-3-small",
            organization_id=current_user["organization_id"],
        )
        if response and getattr(response, "embeddings", None):
            embedding_vector = json.dumps(response.embeddings[0])
            processed = True
    except Exception:
        processed = False

    db_knowledge = Knowledge(
        id=str(uuid4()),
        organization_id=current_user["organization_id"],
        title=sanitized.get("title"),
        content=sanitized.get("content"),
        content_type=knowledge_create.content_type,
        source_url=knowledge_create.source_url,
        tags=knowledge_create.tags,
        category=knowledge_create.category,
        embedding_vector=embedding_vector or knowledge_create.embedding_vector,
        processed=processed,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    db.add(db_knowledge)
    db.commit()
    db.refresh(db_knowledge)

    return KnowledgeResponse.from_orm(db_knowledge)

@router.get("/", response_model=List[KnowledgeResponse])
async def get_knowledge(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """Get a list of knowledge entries"""
    # Verify user has permission
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    knowledge_entries = db.query(Knowledge).filter(
        Knowledge.organization_id == current_user["organization_id"]
    ).offset(skip).limit(limit).all()
    
    return [KnowledgeResponse.from_orm(k) for k in knowledge_entries]

@router.get("/{knowledge_id}", response_model=KnowledgeResponse)
async def get_knowledge_entry(
    knowledge_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific knowledge entry"""
    # Verify user has permission
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    knowledge = db.query(Knowledge).filter(
        Knowledge.id == knowledge_id,
        Knowledge.organization_id == current_user["organization_id"]
    ).first()
    
    if not knowledge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge entry not found"
        )
    
    return KnowledgeResponse.from_orm(knowledge)

@router.put("/{knowledge_id}", response_model=KnowledgeResponse)
async def update_knowledge(
    knowledge_id: str,
    knowledge_update: KnowledgeUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a knowledge entry and re-embed it when content changes."""
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    knowledge = db.query(Knowledge).filter(
        Knowledge.id == knowledge_id,
        Knowledge.organization_id == current_user["organization_id"]
    ).first()

    if not knowledge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge entry not found"
        )

    sanitized = sanitize_input(knowledge_update.dict(exclude_unset=True))
    # Check for prompt injection in updates
    if detect_prompt_injection((sanitized.get("title", "") or "") + "\n" + (sanitized.get("content", "") or "")):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Knowledge content contains unsafe instructions.")

    for field, value in sanitized.items():
        setattr(knowledge, field, value)

    if knowledge_update.content is not None or knowledge_update.title is not None:
        try:
            response = await llm_gateway.embed(
                texts=[f"{knowledge.title}\n{knowledge.content}"],
                model="text-embedding-3-small",
                organization_id=current_user["organization_id"],
            )
            if response and getattr(response, "embeddings", None):
                knowledge.embedding_vector = json.dumps(response.embeddings[0])
                knowledge.processed = True
        except Exception:
            knowledge.processed = False

    knowledge.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(knowledge)

    return KnowledgeResponse.from_orm(knowledge)

@router.delete("/{knowledge_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge(
    knowledge_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a knowledge entry"""
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    knowledge = db.query(Knowledge).filter(
        Knowledge.id == knowledge_id,
        Knowledge.organization_id == current_user["organization_id"]
    ).first()

    if not knowledge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge entry not found"
        )

    db.delete(knowledge)
    db.commit()

    return None


@router.post("/search", response_model=List[dict])
async def search_knowledge(
    body: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Search knowledge using embeddings and cosine similarity."""
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    query = body.get("query") or ""
    organization_id = body.get("organization_id") or current_user.get("organization_id")
    limit = int(body.get("limit", 5))

    if not query:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Query is required")

    knowledge_entries = db.query(Knowledge).filter(
        Knowledge.organization_id == organization_id,
        Knowledge.processed.is_(True),
    ).all()

    payload = [
        {
            "id": knowledge.id,
            "title": knowledge.title,
            "content": knowledge.content,
            "embedding_vector": knowledge.embedding_vector,
            "organization_id": knowledge.organization_id,
        }
        for knowledge in knowledge_entries
    ]

    results = await search_engine.search(query=query, knowledge_entries=payload, organization_id=organization_id, top_k=limit)
    return [{"id": item["id"], "title": item["title"], "content": item["content"], "score": item["score"]} for item in results]