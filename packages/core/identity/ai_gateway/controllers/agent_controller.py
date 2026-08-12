"""Production chat controller for the reception agent."""
from __future__ import annotations

import json
from typing import Any, AsyncGenerator, Dict, List, Optional
from uuid import uuid4

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from packages.core.ai.gateway import LLMGateway
from packages.core.ai.memory import MemoryManager
from packages.core.ai.reception.agent import AgentResponse, ReceptionAgent
from packages.core.ai.reception.evaluator import Evaluator
from packages.core.ai.reception.prompts import PromptManager
from packages.core.ai.reception.tools import (
    BookingService,
    BusinessService,
    CRMService,
    KnowledgeService,
    ToolExecutor,
)
from packages.core.config import settings
from packages.core.database import get_db
from packages.core.identity.business.models import BusinessProfile
from packages.core.identity.knowledge.models import Knowledge
from packages.core.security import decode_token, sanitize_input, detect_prompt_injection

router = APIRouter(prefix="/agent", tags=["agent"])


class AgentMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=settings.MAX_INPUT_LENGTH)
    conversation_id: Optional[str] = None
    customer_id: Optional[str] = None
    organization_id: Optional[str] = None
    business_id: Optional[str] = None
    stream: bool = False
    use_reception_agent: bool = True
    widget_api_key: Optional[str] = None
    widget_token: Optional[str] = None
    user: Optional[str] = None


class AgentMessageResponse(BaseModel):
    content: str
    intent: Optional[str] = None
    tools_used: List[str] = []
    knowledge_used: List[str] = []
    requires_human: bool = False
    conversation_id: str
    metadata: Dict[str, Any] = {}


class WidgetAuthContext(BaseModel):
    organization_id: Optional[str] = None
    customer_id: Optional[str] = None
    business_id: Optional[str] = None


def _build_business_context(db: Session, organization_id: str) -> Dict[str, Any]:
    business_profile = (
        db.query(BusinessProfile)
        .filter(BusinessProfile.organization_id == organization_id)
        .first()
    )
    knowledge_rows = (
        db.query(Knowledge)
        .filter(Knowledge.organization_id == organization_id, Knowledge.processed.is_(True))
        .all()
    )

    return {
        "organization_id": organization_id,
        "business_name": getattr(business_profile, "business_name", None) or "",
        "business_hours": getattr(business_profile, "hours", None) or {},
        "location": {
            "address": getattr(business_profile, "address", None) or "",
            "city": "",
            "state": "",
        },
        "knowledge_base": [
            {
                "id": row.id,
                "title": row.title,
                "content": row.content,
                "embedding_vector": row.embedding_vector,
                "organization_id": row.organization_id,
            }
            for row in knowledge_rows
        ],
        "llm_model": settings.APP_VERSION and "gpt-3.5-turbo",
    }


def _resolve_widget_context(request: Request, payload: Dict[str, Any], db: Session) -> WidgetAuthContext:
    context = WidgetAuthContext()

    if payload.get("business_id"):
        context.business_id = payload["business_id"]

    header_api_key = request.headers.get("x-widget-api-key") or request.headers.get("X-Widget-Api-Key")
    header_token = request.headers.get("x-widget-token") or request.headers.get("X-Widget-Token")

    if header_api_key:
        if settings.WIDGET_API_KEY and header_api_key == settings.WIDGET_API_KEY:
            return context
        raise HTTPException(status_code=401, detail="Invalid widget API key")

    if header_token:
        try:
            secret = settings.WIDGET_SIGNING_SECRET or settings.SECRET_KEY
            claims = jwt.decode(header_token, secret, algorithms=["HS256"])
            context.organization_id = claims.get("organization_id") or claims.get("org_id")
            context.customer_id = claims.get("customer_id") or claims.get("sub")
            context.business_id = context.business_id or claims.get("business_id")
            return context
        except Exception as exc:
            raise HTTPException(status_code=401, detail="Invalid widget token") from exc

    if payload.get("widget_api_key"):
        if settings.WIDGET_API_KEY and payload["widget_api_key"] == settings.WIDGET_API_KEY:
            return context
        raise HTTPException(status_code=401, detail="Invalid widget API key")

    if payload.get("widget_token"):
        try:
            secret = settings.WIDGET_SIGNING_SECRET or settings.SECRET_KEY
            claims = jwt.decode(payload["widget_token"], secret, algorithms=["HS256"])
            context.organization_id = claims.get("organization_id") or claims.get("org_id")
            context.customer_id = claims.get("customer_id") or claims.get("sub")
            context.business_id = context.business_id or claims.get("business_id")
            return context
        except Exception as exc:
            raise HTTPException(status_code=401, detail="Invalid widget token") from exc

    if context.business_id:
        business = db.query(BusinessProfile).filter(BusinessProfile.id == context.business_id).first()
        if business:
            context.organization_id = business.organization_id

    return context


def _resolve_organization_id(request: Request, payload: Dict[str, Any], db: Session, auth_context: Optional[Dict[str, Any]] = None) -> str:
    widget_context = _resolve_widget_context(request, payload, db)
    org_id = widget_context.organization_id
    if auth_context and auth_context.get("organization_id"):
        org_id = auth_context["organization_id"]
    if not org_id and widget_context.business_id:
        business = db.query(BusinessProfile).filter(BusinessProfile.id == widget_context.business_id).first()
        if business:
            org_id = business.organization_id
    if not org_id:
        raise HTTPException(status_code=400, detail="organization_id or business_id is required")
    return org_id


async def _create_agent_for_request(
    db: Session,
    organization_id: str,
    llm_gateway: Optional[LLMGateway] = None,
) -> ReceptionAgent:
    gateway = llm_gateway or LLMGateway()
    memory_manager = MemoryManager(db, organization_id)
    prompt_manager = PromptManager()
    evaluator = Evaluator(llm_gateway=gateway, memory_manager=memory_manager)
    tool_executor = ToolExecutor(
        crm_service=CRMService(session_factory=lambda: db),
        booking_service=BookingService(session_factory=lambda: db),
        knowledge_service=KnowledgeService(llm_gateway=gateway, session_factory=lambda: db),
        business_service=BusinessService(session_factory=lambda: db),
    )
    return ReceptionAgent(
        organization_id=organization_id,
        llm_gateway=gateway,
        memory_manager=memory_manager,
        tool_executor=tool_executor,
        prompt_manager=prompt_manager,
        evaluator=evaluator,
        business_context=_build_business_context(db, organization_id),
    )


async def _run_agent_pipeline(
    payload: Dict[str, Any],
    request: Request,
    db: Session,
    auth_context: Optional[Dict[str, Any]] = None,
) -> tuple[ReceptionAgent, AgentResponse, str]:
    sanitized = sanitize_input(payload)
    # Prompt-injection defense
    if detect_prompt_injection(sanitized.get("message")):
        raise HTTPException(status_code=400, detail="Prompt content contains unsafe instructions.")
    conversation_id = sanitized.get("conversation_id") or str(uuid4())
    customer_id = sanitized.get("customer_id")
    organization_id = _resolve_organization_id(request, sanitized, db, auth_context)

    if auth_context and auth_context.get("user_id") and not customer_id:
        customer_id = auth_context["user_id"]

    agent = await _create_agent_for_request(db, organization_id)
    response = await agent.process_message(
        message=sanitized["message"],
        conversation_id=conversation_id,
        customer_id=customer_id,
    )
    return agent, response, conversation_id


async def _stream_agent_pipeline(
    payload: Dict[str, Any],
    request: Request,
    db: Session,
    auth_context: Optional[Dict[str, Any]] = None,
) -> tuple[ReceptionAgent, AsyncGenerator[str, None], str]:
    sanitized = sanitize_input(payload)
    # Prompt-injection defense
    if detect_prompt_injection(sanitized.get("message")):
        raise HTTPException(status_code=400, detail="Prompt content contains unsafe instructions.")
    conversation_id = sanitized.get("conversation_id") or str(uuid4())
    customer_id = sanitized.get("customer_id")
    organization_id = _resolve_organization_id(request, sanitized, db, auth_context)

    if auth_context and auth_context.get("user_id") and not customer_id:
        customer_id = auth_context["user_id"]

    agent = await _create_agent_for_request(db, organization_id)

    async def generator() -> AsyncGenerator[str, None]:
        async for chunk in agent.process_message_stream(
            message=sanitized["message"],
            conversation_id=conversation_id,
            customer_id=customer_id,
        ):
            yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"

        final_response = AgentResponse(
            content="",
            intent=None,
            tools_used=[],
            knowledge_used=[],
            requires_human=False,
            metadata={},
        )
        yield f"data: {json.dumps({'type': 'done', 'response': final_response.__dict__})}\n\n"

    return agent, generator(), conversation_id


@router.post("/message", response_model=AgentMessageResponse)
async def create_agent_message(
    request: Request,
    payload: AgentMessageRequest,
    db: Session = Depends(get_db),
):
    """Run the full reception-agent pipeline for a public or widget-authenticated chat request."""
    auth_context: Optional[Dict[str, Any]] = None
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        try:
            token = auth_header.split(" ", 1)[1]
            claims = decode_token(token)
            auth_context = {
                "user_id": claims.get("sub"),
                "organization_id": claims.get("org_id"),
            }
        except HTTPException:
            raise

    agent, response, conversation_id = await _run_agent_pipeline(payload.model_dump(), request, db, auth_context)
    payload_dict = {
        "content": response.content,
        "intent": response.intent.value if response.intent is not None else None,
        "tools_used": response.tools_used,
        "knowledge_used": response.knowledge_used,
        "requires_human": response.requires_human,
        "conversation_id": conversation_id,
        "metadata": response.metadata,
    }
    return payload_dict


@router.post("/stream")
async def stream_agent_message(
    request: Request,
    payload: AgentMessageRequest,
    db: Session = Depends(get_db),
):
    """Stream reception-agent tokens over SSE for public or widget-authenticated chat requests."""
    auth_context: Optional[Dict[str, Any]] = None
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        try:
            token = auth_header.split(" ", 1)[1]
            claims = decode_token(token)
            auth_context = {
                "user_id": claims.get("sub"),
                "organization_id": claims.get("org_id"),
            }
        except HTTPException:
            raise

    _, generator, conversation_id = await _stream_agent_pipeline(payload.model_dump(), request, db, auth_context)
    return StreamingResponse(generator, media_type="text/event-stream")
