from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Deque, Dict, List
import logging
import time
import re

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_403_FORBIDDEN, HTTP_429_TOO_MANY_REQUESTS

from packages.core.config import settings
from packages.core.database import SessionLocal
from packages.core.identity.models import AuditLog
from packages.core.logging import get_logger
from packages.core.security import decode_token, get_client_ip, validate_csrf_token
from jose import jwt as jose_jwt

logger = get_logger("middleware")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        response.headers.setdefault("Strict-Transport-Security", "max-age=63072000; includeSubDomains; preload")
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "same-origin")
        response.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=(), interest-cohort=()")
        response.headers.setdefault("X-XSS-Protection", "1; mode=block")
        response.headers.setdefault("Cache-Control", "no-store")
        response.headers.setdefault("Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'; base-uri 'self'; form-action 'self';")

        return response


class CSRFMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method not in ("GET", "HEAD", "OPTIONS", "TRACE") and settings.CSRF_ENABLED:
            if request.url.path.startswith("/api/v1/auth"):
                return await call_next(request)
            validate_csrf_token(request)

        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    _requests: Dict[str, Deque[float]] = defaultdict(deque)
    _requests_org: Dict[str, Deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        client_ip = get_client_ip(request)
        now = time.time()
        window_start = now - settings.RATE_LIMIT_WINDOW_SECONDS
        timestamps = self._requests[client_ip]

        while timestamps and timestamps[0] < window_start:
            timestamps.popleft()

        if len(timestamps) >= settings.RATE_LIMIT_REQUESTS:
            logger.warning(
                "Rate limit exceeded",
                extra={"client_ip": client_ip, "path": request.url.path}
            )
            raise HTTPException(
                status_code=HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again later."
            )

        timestamps.append(now)

        # Per-organization rate limiting (if org context available from bearer or widget token)
        org_id = None
        authorization_header = request.headers.get("authorization", "")
        if authorization_header.startswith("Bearer "):
            token = authorization_header.split(" ", 1)[1]
            try:
                payload = decode_token(token)
                org_id = payload.get("org_id")
            except Exception:
                org_id = None

        if not org_id:
            # Check widget token header
            header_token = request.headers.get("x-widget-token") or request.headers.get("X-Widget-Token")
            if header_token:
                try:
                    secret = settings.WIDGET_SIGNING_SECRET or settings.SECRET_KEY
                    claims = jose_jwt.decode(header_token, secret, algorithms=["HS256"])
                    org_id = claims.get("organization_id") or claims.get("org_id")
                except Exception:
                    org_id = None

        if org_id:
            org_timestamps = self._requests_org[org_id]
            while org_timestamps and org_timestamps[0] < window_start:
                org_timestamps.popleft()

            if len(org_timestamps) >= settings.RATE_LIMIT_REQUESTS_ORG:
                logger.warning(
                    "Org rate limit exceeded",
                    extra={"organization_id": org_id, "path": request.url.path}
                )
                raise HTTPException(
                    status_code=HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many requests for this organization. Please try again later."
                )

            org_timestamps.append(now)
        return await call_next(request)


class RequestValidationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method not in ("GET", "HEAD", "OPTIONS", "TRACE"):
            content_type = request.headers.get("content-type", "")
            if not (content_type.startswith("application/json") or content_type.startswith("multipart/form-data")):
                raise HTTPException(
                    status_code=HTTP_400_BAD_REQUEST,
                    detail="Unsupported Content-Type. Use application/json or multipart/form-data."
                )

        return await call_next(request)


class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(int(time.time() * 1000))
        start_time = time.time()
        request.state.request_id = request_id

        response = await call_next(request)
        duration_ms = int((time.time() - start_time) * 1000)
        client_ip = get_client_ip(request)
        user_agent = request.headers.get("user-agent")

        audit_data = {
            "request_id": request_id,
            "event": "request.completed",
            "path": request.url.path,
            "method": request.method,
            "status_code": response.status_code,
            "client_ip": client_ip,
            "user_agent": user_agent,
            "details": None,
        }

        authorization_header = request.headers.get("authorization", "")
        if authorization_header.startswith("Bearer "):
            token = authorization_header.split(" ", 1)[1]
            try:
                payload = decode_token(token)
                audit_data["user_id"] = payload.get("sub")
                audit_data["organization_id"] = payload.get("org_id")
            except Exception:
                audit_data["details"] = "Failed to decode bearer token for audit metadata"

        try:
            db = SessionLocal()
            audit_entry = AuditLog(
                id=str(int(time.time() * 1000)) + "-" + request_id,
                organization_id=audit_data.get("organization_id"),
                user_id=audit_data.get("user_id"),
                request_id=request_id,
                event=audit_data["event"],
                path=audit_data["path"],
                method=audit_data["method"],
                status_code=response.status_code,
                client_ip=client_ip,
                user_agent=user_agent,
                details=audit_data.get("details"),
                created_at=datetime.utcnow(),
            )
            db.add(audit_entry)
            db.commit()
        except Exception as exc:
            logger.warning(
                "Failed to persist audit log",
                extra={"error": str(exc), "request_id": request_id}
            )
        finally:
            db.close()

        logger.info(
            "request.completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "client_ip": client_ip,
            }
        )

        return response
