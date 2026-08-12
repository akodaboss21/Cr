from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.cors import CORSMiddleware
from packages.core.database import get_db
from packages.core.security import get_current_user
from packages.core.logging import get_logger, setup_logging
import datetime

# Initialize logging
setup_logging()
logger = get_logger("api_gateway")

router = APIRouter(prefix="/api/v1")

# Include routers for all modules
from packages.core.identity.controllers.auth_controller import router as auth
from packages.core.identity.controllers.user_controller import router as users
from packages.core.identity.controllers.audit_controller import router as audit
from packages.core.identity.event_system.controllers import event_system_controller as events
from packages.core.identity.organizations.controllers import organization_controller as orgs
from packages.core.identity.billing.controllers import billing_controller as billing
from packages.core.identity.notification.controllers import notification_controller as notifications
from packages.core.identity.ai_gateway.controllers.ai_gateway_controller import router as ai_gateway
from packages.core.identity.ai_gateway.controllers.analytics_controller import router as ai_analytics
from packages.core.identity.ai_gateway.controllers.streaming import router as ai_stream
from packages.core.identity.ai_gateway.controllers.agent_controller import router as agent_router
from packages.core.identity.background_workers.controllers.background_workers_controller import router as background_workers
from packages.core.identity.booking.controllers.booking_controller import router as bookings
from packages.core.identity.business.controllers.business_controller import router as business_profiles
from packages.core.identity.onboarding import controller as onboarding_controller
from packages.core.identity.conversation.controllers.conversation_controller import router as conversations
from packages.core.identity.crm.controllers.crm_controller import router as crm
from packages.core.identity.integration.controllers.integration_controller import router as integrations
from packages.core.identity.knowledge.controllers.knowledge_controller import router as knowledge

router.include_router(auth, prefix="/auth")
router.include_router(users, prefix="/users")
router.include_router(audit)
router.include_router(events.router, prefix="/events")
router.include_router(orgs.router, prefix="/organizations")
router.include_router(billing.router, prefix="/billing")
router.include_router(notifications.router, prefix="/notifications")
router.include_router(ai_gateway)
router.include_router(ai_analytics)
router.include_router(ai_stream)
router.include_router(agent_router)
router.include_router(background_workers)
router.include_router(bookings)
router.include_router(business_profiles)
router.include_router(onboarding_controller.router)
router.include_router(conversations)
router.include_router(crm)
router.include_router(integrations)
router.include_router(knowledge)

# Versioned endpoints
@router.get("/version", response_model=str)
def get_version():
    return "v1.0"

# Health check endpoint
@router.get("/health", response_model=dict)
def health_check():
    return {
        "status": "healthy",
        "database": "connected" if get_db() else "disconnected"
    }