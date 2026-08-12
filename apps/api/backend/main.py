from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from packages.core.config import settings
from packages.core.identity.api_gateway import router as api_router
from packages.core.middleware import (
    SecurityHeadersMiddleware,
    CSRFMiddleware,
    RateLimitMiddleware,
    RequestValidationMiddleware,
    AuditMiddleware,
)
from packages.core.logging import setup_logging, get_logger

try:
    import sentry_sdk
    from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
    SENTRY_AVAILABLE = True
except Exception:
    sentry_sdk = None
    SentryAsgiMiddleware = None
    SENTRY_AVAILABLE = False

setup_logging(level=settings.APP_VERSION and ("INFO" if not settings.DEBUG else "DEBUG"))
logger = get_logger("main")

app = FastAPI(
    title="Carai Receptionist API",
    description="AI Receptionist Backend API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.include_router(api_router)

allowed_origins = [origin.strip() for origin in settings.ALLOWED_ORIGINS.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With", "X-CSRF-Token", "X-Request-ID"],
    expose_headers=["X-Request-ID"],
)

app.add_middleware(AuditMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestValidationMiddleware)
app.add_middleware(CSRFMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

# Optionally wrap the app with Sentry ASGI middleware if SDK is available and DSN is configured
if SENTRY_AVAILABLE and settings.SENTRY_DSN:
    try:
        sentry_sdk.init(dsn=settings.SENTRY_DSN, environment=settings.SENTRY_ENV)
        app.add_middleware(SentryAsgiMiddleware)
        logger.info("Sentry initialized")
    except Exception as e:
        logger.warning("Failed to initialize Sentry", extra={"error": str(e)})

@app.on_event("startup")
async def startup_event():
    logger.info("Starting Carai Receptionist API...")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Carai Receptionist API...")

@app.get("/")
async def read_root():
    return {"message": "Welcome to Carai Receptionist API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)