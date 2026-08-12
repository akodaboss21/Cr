# Security Hardening: Authentication & Multi-Tenancy Implementation

## Overview
Comprehensive hardening of authentication, multi-tenancy, and public API security across backend and frontend. All controller endpoints now enforce organization_id filtering, frontend uses real JWT tokens, and public widget endpoints have dedicated rate limiting and input validation.

---

## 1. Backend Authentication & Middleware Hardening

### ✅ Enhanced Security Configuration (`packages/core/config.py`)
- Added separate rate limit thresholds:
  - `RATE_LIMIT_REQUESTS_PUBLIC`: 30 req/min for unauthenticated endpoints
  - `RATE_LIMIT_REQUESTS_ORG`: 500 req/min for authenticated users
  - `RATE_LIMIT_REQUESTS_ORG_PUBLIC`: 100 req/min for public widget endpoints
- Maintains existing `RATE_LIMIT_REQUESTS`: 100 (default authenticated)
- `RATE_LIMIT_WINDOW_SECONDS`: 60

### ✅ Strengthened Security Utilities (`packages/core/security.py`)
**New Functions:**
- `create_widget_token()`: Generate short-lived widget tokens (1-hour default expiry)
  - Scoped to organization_id, business_id, customer_id
  - Type: "widget" for strict token validation
  
- `decode_widget_token()`: Validate widget tokens with type checking
  - Enforces "widget" type claim
  - Uses WIDGET_SIGNING_SECRET or SECRET_KEY

**Enhanced Validation:**
- `validate_csrf_token()`: Stricter validation
  - Both header and cookie must exist
  - Tokens must match exactly
  - Minimum length check (16 chars)

### ✅ Improved Middleware (`packages/core/middleware.py`)

**CSRFMiddleware:**
- Exemptions only for authentication endpoints (/auth/login, /auth/refresh, /auth/logout, /auth/register)
- All other POST/PUT/PATCH/DELETE require valid CSRF tokens

**RateLimitMiddleware:**
- Distinguishes public agent endpoints: `/api/v1/agent/message`, `/api/v1/agent/stream`
- Applies stricter limits to public endpoints
- Validates token type ("access") before extracting org_id
- Falls back to widget token headers for organization context

**RequestValidationMiddleware:**
- Content-Length validation (max 10MB payload)
- Supported content types: application/json, multipart/form-data
- Size enforcement before processing

**AuditMiddleware:**
- Captures organization_id and user_id from bearer tokens
- Logs all requests with full context
- Persists audit entries to database

### ✅ CORS Configuration (`apps/api/backend/main.py`)
```
allow_headers: [
  "Authorization", "Content-Type", "X-Requested-With", 
  "X-CSRF-Token", "X-Request-ID", "X-Widget-Token", "X-Widget-Api-Key"
]
expose_headers: [
  "X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining"
]
max_age: 3600 (Preflight cache)
```

### ✅ Security Headers Response (`SecurityHeadersMiddleware`)
- `Strict-Transport-Security`: 63072000s (2 years)
- `X-Content-Type-Options`: nosniff
- `X-Frame-Options`: DENY
- `Referrer-Policy`: same-origin
- `Permissions-Policy`: Denies geolocation, microphone, camera, interest-cohort
- `X-XSS-Protection`: 1; mode=block
- `Cache-Control`: no-store
- `Content-Security-Policy`: default-src 'none'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'

---

## 2. Agent & Widget Controller Security

### ✅ Agent Authentication (`packages/core/identity/ai_gateway/controllers/agent_controller.py`)

**Token Validation:**
- Validates Bearer token type == "access"
- Extracts organization_id and user_id from claims
- Rejects invalid/expired tokens with 401 Unauthorized

**Widget Context Resolution (Priority Order):**
1. X-Widget-Token header (JWT - preferred)
   - Uses `decode_widget_token()` for validation
   - Extracts organization_id, business_id, customer_id
   
2. X-Widget-Api-Key header (legacy static key)
   - Matches against WIDGET_API_KEY config
   
3. payload.widget_token (for SSE/streaming)
   - Fallback for environments with header limitations
   
4. payload.widget_api_key (legacy)
   
5. business_id lookup
   - Resolves organization_id from BusinessProfile

**Message Endpoints (`/message`, `/stream`):**
- Both POST endpoints require authentication via:
  - Bearer token (access_token), OR
  - Widget token (short-lived JWT), OR
  - Widget API key
- Prompt injection detection on all message content
- Input sanitization before processing
- Full organization context validation

---

## 3. Knowledge Management & File Upload Security

### ✅ Enhanced Knowledge Controller (`packages/core/identity/knowledge/controllers/knowledge_controller.py`)

**New File Upload Endpoint (`POST /knowledge/upload`):**
- Supports: .txt, .pdf, .md, .html
- File size validation (max 10MB)
- Streaming file read (1MB chunks) to prevent memory exhaustion
- UTF-8 content decoding with error handling
- Content sanitization via `sanitize_input()`
- Prompt injection detection
- Automatic embedding generation (with fallback)
- Tags: ["uploaded", "file"]

**Enhanced Create/Update:**
- All inputs sanitized
- Prompt injection detection on title + content
- Organization context enforced
- Automatic re-embedding on content changes

**Secured Search Endpoint (`POST /knowledge/search`):**
- **CRITICAL**: Enforces organization_id from authenticated user
- Ignores any organization_id in request body
- Query sanitization before processing
- Query validation (non-empty, min length)
- Result limit cap: 100 (configurable)
- Returns empty [] if no knowledge entries exist

**CRUD Operations:**
- GET `/` - Lists user's org knowledge (with pagination)
- GET `/{id}` - Retrieves single entry with org filter
- PUT `/{id}` - Updates entry with org verification
- DELETE `/{id}` - Deletes entry with org verification
- All operations verify user belongs to organization before access

---

## 4. Frontend Authentication Upgrade

### ✅ JWT-Based Auth Store (`carai-receptionist/src/lib/auth-store.ts`)

**Real JWT Integration:**
- Stores access_token and refresh_token
- Uses sessionStorage instead of localStorage
  - Cleared on browser close
  - More secure for sensitive tokens
- Token persistence configuration via custom storage adapter

**Enhanced Login Flow:**
- Validates tokens are non-empty
- Decodes JWT payload safely (atob with error handling)
- Extracts organization_id from token claims
- Includes credentials: 'include' for CSRF cookie handling
- Improved error handling and logging

**New Methods:**
- `setTokens(accessToken, refreshToken)`: Store tokens securely
- `getAccessToken()`: Retrieve current access token
- Token expiry handled by backend (via JWT exp claim)

**Supabase OAuth Support:**
- Redirect to Supabase auth flow for 'supabase' provider
- Callback handling in main _app.tsx (to implement)

---

## 5. Widget Security Enhancements

### ✅ Updated Widget (`apps/widget/widget.js`)

**Enhanced Authentication Headers:**
```javascript
getHeaders() {
  // Priority 1: Widget Token (short-lived JWT)
  // Priority 2: Widget API Key (static)
  // Priority 3: User auth token
  // Adds X-Requested-With header (CSRF prevention)
  // Includes CSRF token if available (from cookies)
}
```

**Message Validation:**
- Non-empty message validation
- Increased size limit validation (4000 chars, was 1000)
- Inappropriate content detection
- Local rate limiting enforcement

**Security Headers:**
- `X-Requested-With: XMLHttpRequest` on all requests
- CSRF token from `csrf_token` cookie automatically included
- Support for X-Widget-Token and X-Widget-Api-Key headers

---

## 6. Prompt Injection & Input Validation

### ✅ Prompt Injection Patterns Detected
- "ignore previous instructions"
- "disregard earlier"
- "forget all previous"
- "ignore all prior"
- "do not follow"
- "ignore these rules"
- "delete all"
- "reset your"
- "disable safety"
- "open the pod bay doors"

### ✅ Input Sanitization
- XSS pattern removal: `<script>`, `<iframe>`, etc.
- Event handler removal: `onload=`, `onclick=`, etc.
- JavaScript URL removal: `javascript:`
- HTML tag stripping
- Recursive sanitization for nested objects/arrays
- Length validation (configurable MAX_INPUT_LENGTH: 10000)

---

## 7. Multi-Tenant Data Isolation

### ✅ Organization Filtering Enforcement
**Every controller enforces organization_id:**

1. **Agent Controller:**
   - `_resolve_organization_id()`: Mandatory org resolution
   - Both `/message` and `/stream` endpoints
   - Rejects requests without organization context

2. **Knowledge Controller:**
   - All CRUD operations filter by `current_user["organization_id"]`
   - Search endpoint **ignores request body org_id**, uses authenticated user's org
   - File uploads tagged with uploader's organization
   - Prevents cross-organization data access

3. **Business Profile Lookups:**
   - Validates business belongs to authenticated user's organization
   - Used as fallback when explicit org_id unavailable

---

## 8. Widget Token Generation & Expiry

### Widget Token Lifecycle:
```python
# Backend creates short-lived widget tokens
create_widget_token(
  organization_id="org-uuid",      # Required
  business_id="optional",          # For business-scoped widgets
  customer_id="optional",          # For customer tracking
  expires_delta=timedelta(hours=1) # 1-hour default
)
# Returns: JWT with type="widget", org_id, exp
```

### Token Validation:
```python
decode_widget_token(token)
# Verifies: valid signature, type=="widget", not expired
# Returns: claims dict with organization_id
```

---

## 9. Rate Limiting Tiers

| Endpoint Type | IP Limit | Org Limit | Window |
|---|---|---|---|
| Authenticated | 100/min | 500/min | 60s |
| Public Agent | 30/min | 100/min | 60s |
| Auth Endpoints | 100/min | 500/min | 60s |

---

## 10. Audit Trail & Logging

### AuditMiddleware captures:
- request_id (X-Request-ID header or generated)
- method, path, status_code
- client_ip (via X-Forwarded-For or client.host)
- user_agent
- user_id, organization_id (from token)
- Persists to AuditLog table
- Full debug logging to application logs

---

## Testing Checklist

- [ ] Widget cannot access knowledge from other organizations
- [ ] Agent /message and /stream enforce organization filters
- [ ] CSRF tokens required for all state-changing requests
- [ ] Public agent endpoints rate-limited at 30 req/min per IP
- [ ] Prompt injection patterns rejected with 400 Bad Request
- [ ] File uploads validate size, type, encoding
- [ ] Widget tokens expire after 1 hour
- [ ] JWT tokens cannot be forged (signature validation)
- [ ] Frontend uses sessionStorage (not localStorage)
- [ ] Security headers present on all responses
- [ ] Cross-org searches return empty results

---

## Configuration Required

Ensure `.env` includes:
```
SECRET_KEY=<strong-secret>
WIDGET_SIGNING_SECRET=<widget-signing-key>  # Optional; uses SECRET_KEY if not set
WIDGET_API_KEY=<static-widget-key>          # For legacy static key support
CSRF_ENABLED=true
ALLOWED_ORIGINS=https://yourdomain.com
MAX_INPUT_LENGTH=10000
MAX_UPLOAD_SIZE=10485760  # 10MB
```

---

## Future Enhancements

1. Implement token refresh flow with refresh_token
2. Add device fingerprinting for additional CSRF protection
3. Implement OAuth2 with Supabase integration
4. Add per-user API key generation
5. Implement Web Authentication (WebAuthn) support
6. Add security event alerting
7. Implement progressive token expiry
8. Add login attempt rate limiting (per email)
