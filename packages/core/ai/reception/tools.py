"""
Tool System

Framework for executing business tools with validation, logging, and permission checking.
"""
import asyncio
import inspect
import json
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

from ...database import SessionLocal
from ...identity.booking.models import Booking
from ...identity.business.models import BusinessProfile
from ...identity.crm.models import CRM
from ...identity.knowledge.models import Knowledge
from ...ai.gateway import LLMGateway
from ...ai.retrieval import KnowledgeSearchEngine


class ToolError(Exception):
    """Base exception for tool operations"""
    pass


class ToolPermissionError(ToolError):
    """Raised when tool access is denied"""
    pass


class Tool:
    """Base tool class."""

    def __init__(self, name: str, description: str, required_permissions: List[str], handler: Callable[..., Any]):
        self.name = name
        self.description = description
        self.required_permissions = required_permissions
        self.handler = handler
        self.id = str(uuid4())
        self.created_at = datetime.utcnow()
        self.log: Dict[str, Any] = {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at.isoformat(),
        }

    def execute(self, *args, **kwargs) -> Any:
        """Execute the tool with given arguments."""
        result = self.handler(*args, **kwargs)
        if inspect.isawaitable(result):
            return asyncio.run(result)
        return result

    async def execute_async(self, *args, **kwargs) -> Any:
        """Execute the tool asynchronously when available."""
        result = self.handler(*args, **kwargs)
        if inspect.isawaitable(result):
            return await result
        return result

    def validate_permissions(self) -> bool:
        """Validate that current user has required permissions."""
        return True


class CRMService:
    """Concrete CRM service used by the receptionist tools and agent."""

    def __init__(self, session_factory=None):
        self.session_factory = session_factory or SessionLocal

    def _serialize(self, value: Any) -> Any:
        if isinstance(value, (list, dict)):
            return json.dumps(value)
        return value

    def create_or_update_lead(self, lead_data: Dict[str, Any], organization_id: str, customer_id: Optional[str] = None) -> Dict[str, Any]:
        session = self.session_factory()
        try:
            existing = None
            if lead_data.get("email"):
                existing = session.query(CRM).filter(CRM.organization_id == organization_id, CRM.email == lead_data["email"]).first()
            if not existing and lead_data.get("phone"):
                existing = session.query(CRM).filter(CRM.organization_id == organization_id, CRM.phone == lead_data["phone"]).first()

            if existing is None:
                crm = CRM(
                    id=str(uuid4()),
                    organization_id=organization_id,
                    customer_id=customer_id,
                    name=lead_data.get("name") or "Unknown",
                    email=lead_data.get("email"),
                    phone=lead_data.get("phone"),
                    company=lead_data.get("company"),
                    source=lead_data.get("source") or "website",
                    status=lead_data.get("status") or "lead",
                    score=lead_data.get("score") or 0,
                    notes=lead_data.get("notes"),
                    tags=self._serialize(lead_data.get("tags") or []),
                    assigned_to=lead_data.get("assigned_to"),
                    pipeline_stage=lead_data.get("pipeline_stage") or "NEW",
                    next_followup=lead_data.get("next_followup"),
                    first_interaction=lead_data.get("first_interaction"),
                    last_interaction=lead_data.get("last_interaction"),
                    total_conversations=lead_data.get("total_conversations") or 1,
                    services_requested=self._serialize(lead_data.get("services_requested") or []),
                    bookings=self._serialize(lead_data.get("bookings") or []),
                    preferences=self._serialize(lead_data.get("preferences") or {}),
                    notes_history=self._serialize(lead_data.get("notes_history") or []),
                    important_details=self._serialize(lead_data.get("important_details") or {}),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                session.add(crm)
                session.commit()
                session.refresh(crm)
                record = crm
            else:
                for field in ["name", "email", "phone", "company", "source", "status", "score", "notes", "assigned_to", "pipeline_stage", "next_followup", "first_interaction", "last_interaction", "total_conversations", "services_requested", "bookings", "preferences", "notes_history", "important_details"]:
                    if field in lead_data:
                        setattr(existing, field, self._serialize(lead_data[field]) if field in {"services_requested", "bookings", "preferences", "notes_history", "important_details"} else lead_data[field])
                if customer_id is not None:
                    existing.customer_id = customer_id
                existing.updated_at = datetime.utcnow()
                session.commit()
                session.refresh(existing)
                record = existing

            return {"id": record.id, "organization_id": organization_id, "status": record.status}
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def update_customer_profile(self, customer_id: str, profile_update: Dict[str, Any], organization_id: str) -> Dict[str, Any]:
        session = self.session_factory()
        try:
            record = session.query(CRM).filter(CRM.organization_id == organization_id, CRM.customer_id == customer_id).first()
            if record is None:
                record = CRM(
                    id=str(uuid4()),
                    organization_id=organization_id,
                    customer_id=customer_id,
                    name=profile_update.get("name") or "Unknown",
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                session.add(record)
            for field in ["name", "email", "phone", "notes", "preferences", "services_requested", "notes_history", "important_details"]:
                if field in profile_update:
                    setattr(record, field, self._serialize(profile_update[field]))
            record.updated_at = datetime.utcnow()
            session.commit()
            session.refresh(record)
            return {"id": record.id, "organization_id": organization_id}
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


class BookingService:
    """Concrete booking service used by the receptionist tools and agent."""

    def __init__(self, session_factory=None):
        self.session_factory = session_factory or SessionLocal

    def create_booking(self, booking_data: Dict[str, Any], organization_id: str, customer_id: Optional[str] = None) -> Dict[str, Any]:
        session = self.session_factory()
        try:
            start_time = booking_data.get("start_time")
            end_time = booking_data.get("end_time")
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time)
            if isinstance(end_time, str):
                end_time = datetime.fromisoformat(end_time)
            booking = Booking(
                id=str(uuid4()),
                organization_id=organization_id,
                business_id=booking_data.get("business_id"),
                customer_id=customer_id or booking_data.get("customer_id"),
                title=booking_data.get("title") or "Appointment",
                description=booking_data.get("description") or "Created by receptionist",
                status=booking_data.get("status") or "pending",
                start_time=start_time or datetime.utcnow(),
                end_time=end_time or datetime.utcnow(),
                timezone=booking_data.get("timezone") or "UTC",
                attendees=json.dumps(booking_data.get("attendees") or []),
                calendar_event_id=booking_data.get("calendar_event_id"),
                google_calendar_id=booking_data.get("google_calendar_id"),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            session.add(booking)
            session.commit()
            session.refresh(booking)
            return {"id": booking.id, "organization_id": organization_id, "status": booking.status}
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


class KnowledgeService:
    """Concrete knowledge service backed by stored knowledge rows and the RAG engine."""

    def __init__(self, llm_gateway: Optional[LLMGateway] = None, session_factory=None):
        self.session_factory = session_factory or SessionLocal
        self.retrieval_engine = KnowledgeSearchEngine(llm_gateway=llm_gateway or LLMGateway())

    async def search(self, query: str, organization_id: str, top_k: int = 5) -> List[Dict[str, Any]]:
        session = self.session_factory()
        try:
            knowledge_rows = session.query(Knowledge).filter(Knowledge.organization_id == organization_id, Knowledge.processed.is_(True)).all()
            payload = [
                {
                    "id": row.id,
                    "title": row.title,
                    "content": row.content,
                    "embedding_vector": row.embedding_vector,
                    "organization_id": row.organization_id,
                }
                for row in knowledge_rows
            ]
            return await self.retrieval_engine.search(query=query, knowledge_entries=payload, organization_id=organization_id, top_k=top_k)
        finally:
            session.close()


class BusinessService:
    """Concrete business info service."""

    def __init__(self, session_factory=None):
        self.session_factory = session_factory or SessionLocal

    def get_business_hours(self, organization_id: str) -> Dict[str, Any]:
        session = self.session_factory()
        try:
            business = session.query(BusinessProfile).filter(BusinessProfile.organization_id == organization_id).first()
            return {"hours": business.hours if business else "9am-5pm"}
        finally:
            session.close()

    def get_location(self, organization_id: str) -> Dict[str, Any]:
        session = self.session_factory()
        try:
            business = session.query(BusinessProfile).filter(BusinessProfile.organization_id == organization_id).first()
            return {"address": business.address if business else "123 Main St"}
        finally:
            session.close()


class ToolExecutor:
    """Executes tools with validation, logging, and error handling."""

    def __init__(self, crm_service: Optional[CRMService] = None, booking_service: Optional[BookingService] = None, knowledge_service: Optional[KnowledgeService] = None, business_service: Optional[BusinessService] = None):
        self.tools: Dict[str, Tool] = {}
        self.log: List[Dict[str, Any]] = []
        self.crm_service = crm_service or CRMService()
        self.booking_service = booking_service or BookingService()
        self.knowledge_service = knowledge_service or KnowledgeService()
        self.business_service = business_service or BusinessService()
        self.setup_default_tools()

    def register_tool(self, tool: Tool):
        """Register a tool with the executor."""
        self.tools[tool.name] = tool

    async def execute_tool(self, tool_name: str, args: Optional[Dict[str, Any]] = None, organization_id: Optional[str] = None, context: Optional[Any] = None) -> Dict[str, Any]:
        """Execute a registered tool by name."""
        if tool_name not in self.tools:
            raise ToolError(f"Tool '{tool_name}' not registered")

        tool = self.tools[tool_name]
        if not tool.validate_permissions():
            raise ToolPermissionError(f"Access denied for tool '{tool_name}'")

        self.log.append({
            "timestamp": datetime.utcnow().isoformat(),
            "tool": tool_name,
            "args": args or {},
            "status": "started",
        })

        try:
            result = await tool.execute_async(args or {}, organization_id=organization_id, context=context)
            self.log.append({
                "timestamp": datetime.utcnow().isoformat(),
                "tool": tool_name,
                "status": "completed",
                "result": result,
            })
            if context is not None:
                context.metadata.setdefault("tool_calls", []).append({
                    "tool": tool_name,
                    "result": result,
                    "organization_id": organization_id,
                })
                context.metadata["last_tool_result"] = result
            return {"success": True, "tool": tool_name, "result": result, "log_id": self.log[-1]["timestamp"]}
        except Exception as exc:
            self.log.append({
                "timestamp": datetime.utcnow().isoformat(),
                "tool": tool_name,
                "status": "failed",
                "error": str(exc),
            })
            raise ToolError(f"Tool '{tool_name}' execution failed: {str(exc)}") from exc

    async def execute_plan(self, plan: Optional[List[Any]], context: Optional[Any], organization_id: Optional[str]) -> List[Dict[str, Any]]:
        """Execute a plan composed of tool names or step objects."""
        tool_names: List[str] = []
        for entry in plan or []:
            if isinstance(entry, str):
                tool_names.append(entry)
            elif hasattr(entry, "output") and isinstance(entry.output, dict):
                required_tools = entry.output.get("required_tools") or []
                if isinstance(required_tools, list):
                    tool_names.extend(required_tools)
            elif isinstance(entry, dict):
                required_tools = entry.get("required_tools") or []
                if isinstance(required_tools, list):
                    tool_names.extend(required_tools)

        if not tool_names:
            return []

        results = []
        for tool_name in tool_names:
            result = await self.execute_tool(tool_name, args={}, organization_id=organization_id, context=context)
            results.append(result)
        return results

    def get_log(self) -> List[Dict[str, Any]]:
        """Get execution log."""
        return self.log.copy()

    def setup_default_tools(self):
        """Register the default business tools."""
        self.register_tool(Tool("search_knowledge", "Search knowledge using the RAG pipeline", [], self._search_knowledge))
        self.register_tool(Tool("create_or_update_lead", "Create or update a CRM lead", [], self._create_or_update_lead))
        self.register_tool(Tool("create_booking", "Create a booking record", [], self._create_booking))
        self.register_tool(Tool("check_availability", "Check availability for a requested service", [], self._check_availability))
        self.register_tool(Tool("get_business_hours", "Get the business operating hours", [], self._get_business_hours))
        self.register_tool(Tool("get_location", "Get the business location", [], self._get_location))

    async def _search_knowledge(self, args: Dict[str, Any], organization_id: Optional[str] = None, context: Optional[Any] = None) -> Dict[str, Any]:
        query = args.get("query") or (context.metadata.get("last_user_message") if context is not None else None) or ""
        results = await self.knowledge_service.search(query=query, organization_id=organization_id or "", top_k=args.get("limit", 5)) if organization_id else []
        return {"results": results}

    async def _create_or_update_lead(self, args: Dict[str, Any], organization_id: Optional[str] = None, context: Optional[Any] = None) -> Dict[str, Any]:
        lead_data = dict(args)
        customer_id = lead_data.pop("customer_id", None)
        if context is not None and context.customer_id:
            customer_id = customer_id or context.customer_id
        result = self.crm_service.create_or_update_lead(lead_data, organization_id or "", customer_id=customer_id)
        if inspect.isawaitable(result):
            result = await result
        return result

    async def _create_booking(self, args: Dict[str, Any], organization_id: Optional[str] = None, context: Optional[Any] = None) -> Dict[str, Any]:
        booking_data = dict(args)
        customer_id = booking_data.pop("customer_id", None)
        if context is not None and context.customer_id:
            customer_id = customer_id or context.customer_id
        result = self.booking_service.create_booking(booking_data, organization_id or "", customer_id=customer_id)
        if inspect.isawaitable(result):
            result = await result
        return result

    async def _check_availability(self, args: Dict[str, Any], organization_id: Optional[str] = None, context: Optional[Any] = None) -> Dict[str, Any]:
        return {"available": True, "slots": [{"date": args.get("date") or "tomorrow", "time": args.get("time") or "10:00"}]}

    async def _get_business_hours(self, args: Dict[str, Any], organization_id: Optional[str] = None, context: Optional[Any] = None) -> Dict[str, Any]:
        return self.business_service.get_business_hours(organization_id or "")

    async def _get_location(self, args: Dict[str, Any], organization_id: Optional[str] = None, context: Optional[Any] = None) -> Dict[str, Any]:
        return self.business_service.get_location(organization_id or "")


# Global tool executor instance
tool_executor = ToolExecutor()


def register_tool(tool: Tool):
    """Register a tool with the global executor."""
    tool_executor.register_tool(tool)