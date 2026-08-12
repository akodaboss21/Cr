"""
Conversation Module - Controller
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import datetime

from packages.core.database import get_db
from packages.core.security import get_current_user
from packages.core.identity.conversation.models import Conversation, Message
from packages.core.identity.schemas import (
    ConversationCreate, ConversationUpdate, ConversationResponse,
    MessageCreate, MessageResponse
)

router = APIRouter(prefix="/conversations", tags=["conversations"])

@router.post("/", response_model=ConversationResponse)
async def create_conversation(
    conv_create: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new conversation"""
    # Verify user has permission to create conversation
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    # Create conversation
    db_conv = Conversation(
        id=str(uuid4()),
        organization_id=current_user["organization_id"],
        business_id=conv_create.business_id,
        participant_id=current_user["user_id"],
        title=conv_create.title,
        status=conv_create.status,
        channel=conv_create.channel,
        ai_provider=conv_create.ai_provider,
        model=conv_create.model,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(db_conv)
    db.commit()
    db.refresh(db_conv)
    
    return ConversationResponse.from_orm(db_conv)

@router.get("/", response_model=List[ConversationResponse])
async def get_conversations(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """Get a list of conversations for the current user's organization"""
    # Verify user has permission
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    conversations = db.query(Conversation).filter(
        Conversation.organization_id == current_user["organization_id"]
    ).offset(skip).limit(limit).all()
    
    return [ConversationResponse.from_orm(conv) for conv in conversations]

@router.get("/{conv_id}", response_model=ConversationResponse)
async def get_conversation(
    conv_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a conversation by ID"""
    # Verify user has permission
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    conversation = db.query(Conversation).filter(
        Conversation.id == conv_id,
        Conversation.organization_id == current_user["organization_id"]
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    return ConversationResponse.from_orm(conversation)

@router.put("/{conv_id}", response_model=ConversationResponse)
async def update_conversation(
    conv_id: str,
    conv_update: ConversationUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a conversation by ID"""
    # Verify user has permission
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    conversation = db.query(Conversation).filter(
        Conversation.id == conv_id,
        Conversation.organization_id == current_user["organization_id"]
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # Update fields
    for field, value in conv_update.dict(exclude_unset=True).items():
        setattr(conversation, field, value)
    
    conversation.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(conversation)
    
    return ConversationResponse.from_orm(conversation)

@router.delete("/{conv_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conv_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a conversation by ID"""
    # Verify user has permission
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    conversation = db.query(Conversation).filter(
        Conversation.id == conv_id,
        Conversation.organization_id == current_user["organization_id"]
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    db.delete(conversation)
    db.commit()
    
    return None

@router.post("/{conv_id}/messages", response_model=MessageResponse)
async def send_message(
    conv_id: str,
    message_create: MessageCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Send a message in a conversation"""
    # Verify user has permission
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    # Verify conversation exists and user has access
    conversation = db.query(Conversation).filter(
        Conversation.id == conv_id,
        Conversation.organization_id == current_user["organization_id"]
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # Create message
    db_message = Message(
        id=str(uuid4()),
        conversation_id=conv_id,
        content=message_create.content,
        role=message_create.role,
        timestamp=message_create.timestamp or datetime.utcnow(),
        ai_provider=message_create.ai_provider,
        model=message_create.model,
        tokens_used=message_create.tokens_used
    )
    
    db.add(db_message)
    
    # Update conversation's last_message_at
    conversation.last_message_at = datetime.utcnow()
    conversation.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_message)
    
    return MessageResponse.from_orm(db_message)

@router.get("/{conv_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    conv_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """Get messages for a conversation"""
    # Verify user has permission
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    # Verify conversation exists and user has access
    conversation = db.query(Conversation).filter(
        Conversation.id == conv_id,
        Conversation.organization_id == current_user["organization_id"]
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    messages = db.query(Message).filter(
        Message.conversation_id == conv_id
    ).order_by(Message.timestamp.asc()).offset(skip).limit(limit).all()
    
    return [MessageResponse.from_orm(msg) for msg in messages]