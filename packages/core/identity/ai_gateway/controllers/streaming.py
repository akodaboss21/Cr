"""
Streaming Controller for LLM Gateway

This module implements streaming endpoints for the AI Gateway.
It handles Server-Sent Events (SSE) for real-time chat streaming.
"""
from typing import AsyncGenerator
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED, HTTP_500_INTERNAL_SERVER_ERROR
from uuid import uuid4
import json

from sqlalchemy.orm import Session
from packages.core.database import get_db
from packages.core.security import get_current_user, validate_prompt_messages
from packages.core.ai.gateway import LLMGateway
from packages.core.ai.gateway.base import CompletionRequest, EmbeddingRequest
from packages.core.identity.ai_gateway.controllers.agent_controller import _stream_agent_pipeline

router = APIRouter(prefix="/ai/stream", tags=["ai_stream"])

# Global LLM gateway instance
llm_gateway = LLMGateway()

@router.post("/complete")
async def stream_complete(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Stream a completion response
    
    Expects JSON body with:
    {
        "messages": [...],
        "model": "gpt-3.5-turbo",
        "temperature": 0.7,
        "max_tokens": 1000,
        "stream": true,
        ...
    }
    """
    try:
        body = await request.json()
        if body.get("use_reception_agent"):
            return await stream_agent_message(request, body, db, current_user)

        messages = body.get("messages")
        model = body.get("model")
        temperature = body.get("temperature", 0.7)
        max_tokens = body.get("max_tokens")
        stream = body.get("stream", True)
        tools = body.get("tools")
        tool_choice = body.get("tool_choice")
        user = body.get("user")
        metadata = body.get("metadata")
        organization_id = body.get("organization_id")
        
        if not messages:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="Messages are required"
            )

        # Validate messages for prompt-injection and structure
        validate_prompt_messages(messages)
        
        # Verify user has organization context
        if "organization_id" not in current_user:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        organization_id = current_user["organization_id"]

        # Create completion request
        completion_request = CompletionRequest(
            messages=messages,
            model=model or llm_gateway.default_model,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream,
            tools=tools,
            tool_choice=tool_choice,
            user=user,
            metadata=metadata
        )
        
        # Return streaming response
        async def event_generator():
            try:
                async for chunk in llm_gateway.stream(
                    messages=completion_request.messages,
                    model=completion_request.model,
                    temperature=completion_request.temperature,
                    max_tokens=completion_request.max_tokens,
                    tools=completion_request.tools,
                    tool_choice=completion_request.tool_choice,
                    user=completion_request.user,
                    metadata=completion_request.metadata,
                    organization_id=organization_id,
                ):
                    yield f"data: {json.dumps(chunk.__dict__)}\n\n"
            except Exception as e:
                # Handle provider errors
                error_chunk = {
                    "id": str(uuid4()),
                    "model": completion_request.model,
                    "content": "",
                    "role": "assistant",
                    "finish_reason": "error",
                    "error": str(e)
                }
                yield f"data: {json.dumps(error_chunk)}\n\n"
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Streaming failed: {str(e)}"
        )

@router.post("/embed/stream")
async def stream_embed(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Stream embeddings
    """
    try:
        body = await request.json()
        texts = body.get("texts")
        model = body.get("model")
        user = body.get("user")
        organization_id = body.get("organization_id")
        
        if not texts:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="Texts are required"
            )
        
        # Verify user has organization context
        if "organization_id" not in current_user:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        organization_id = current_user["organization_id"]

        # Create embedding request
        embedding_request = EmbeddingRequest(
            input=texts,
            model=model or llm_gateway.default_model,
            user=user
        )
        
        # Return streaming response (embeddings are not truly streamed,
        # but we can simulate it for consistency)
        async def event_generator():
            response = await llm_gateway.embed(
                texts=embedding_request.input,
                model=embedding_request.model,
                user=embedding_request.user,
                organization_id=organization_id,
            )
            chunk = {
                "id": str(uuid4()),
                "model": response.model,
                "embeddings": response.embeddings,
                "prompt_tokens": response.prompt_tokens,
                "total_tokens": response.total_tokens
            }
            yield f"data: {json.dumps(chunk)}\n\n"
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Embedding streaming failed: {str(e)}"
        )


async def stream_agent_message(request: Request, body: dict, db: Session, current_user: dict):
    auth_context = None
    if current_user:
        auth_context = {
            "user_id": current_user.get("user_id"),
            "organization_id": current_user.get("organization_id"),
        }
    _, generator, _ = await _stream_agent_pipeline(body, request, db, auth_context)
    return StreamingResponse(generator, media_type="text/event-stream")