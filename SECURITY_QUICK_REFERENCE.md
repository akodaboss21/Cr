# Authentication & Multi-Tenancy Security Hardening - Quick Reference

## What Was Changed

### 1. Backend Authentication (`packages/core/security.py`)
```python
# NEW: Create short-lived widget tokens (1 hour default)
token = create_widget_token(
    organization_id="org-123",
    business_id="biz-456",  # optional
    customer_id="cust-789"  # optional
)

# NEW: Validate widget tokens with type checking
claims = decode_widget_token(token)
# Returns: {"type": "widget", "organization_id": "org-123", ...}
```

### 2. Rate Limiting (`packages/core/config.py`)
```
RATE_LIMIT_REQUESTS: 100 (default authenticated)
RATE_LIMIT_REQUESTS_PUBLIC: 30 (unauthenticated/public agents)
RATE_LIMIT_REQUESTS_ORG: 500 (per-organization authenticated)
RATE_LIMIT_REQUESTS_ORG_PUBLIC: 100 (per-organization public agents)
```

### 3. CSRF Protection (`packages/core/middleware.py`)
- Required on: POST, PUT, PATCH, DELETE (except /auth endpoints)
- Exemptions: /auth/login, /auth/refresh, /auth/logout, /auth/register
- Validation: Header must match cookie, minimum 16 chars

### 4. Widget Controller (`agent_controller.py`)
```python
# Widget token resolution (priority order):
# 1. X-Widget-Token header (JWT)
# 2. X-Widget-Api-Key header (static)
# 3. payload.widget_token (for SSE)
# 4. payload.widget_api_key
# 5. business_id → organization_id lookup

# All endpoints require:
# - Bearer token OR
# - Widget token OR
# - Widget API key
```

### 5. Knowledge Management (`knowledge_controller.py`)
```python
# NEW ENDPOINT: POST /knowledge/upload
# Accepts: .txt, .pdf, .md, .html
# Max size: 10MB
# Returns: Knowledge entry with auto-generated embeddings

# CRITICAL: Search filters by authenticated user's organization
POST /knowledge/search
{
  "query": "...",
  "limit": 5  # max 100
}
# Ignores any organization_id in request body
# Uses current_user["organization_id"] exclusively
```

### 6. Frontend Auth (`carai-receptionist/src/lib/auth-store.ts`)
```typescript
// Changed: localStorage → sessionStorage
// Cleared on browser close automatically

// NEW: Token management
setTokens(accessToken, refreshToken)
getAccessToken()  // returns current token

// Includes: credentials: 'include' for CSRF
// Extracts: organization_id from token claims
```

### 7. Widget Security (`apps/widget/widget.js`)
```javascript
// Headers sent with every request:
// 1. X-Widget-Token (priority)
// 2. X-Widget-Api-Key (fallback)
// 3. Authorization: Bearer (user token)
// + X-Requested-With (CSRF prevention)
// + X-CSRF-Token (from cookies)

// Message validation:
// - Non-empty check
// - Size limit: 4000 chars (increased from 1000)
// - Content appropriateness check
```

---

## Security Checklist

### Before Deployment
- [ ] Set `SECRET_KEY` to strong random value (32+ chars)
- [ ] Generate `WIDGET_SIGNING_SECRET` (32+ chars)
- [ ] Configure `ALLOWED_ORIGINS` for CORS
- [ ] Ensure `CSRF_ENABLED=true`
- [ ] Verify `MAX_INPUT_LENGTH` (default 10000)
- [ ] Set `MAX_UPLOAD_SIZE` (default 10MB)

### Database Verification
- [ ] AuditLog table exists
- [ ] Knowledge table has `organization_id` column
- [ ] BusinessProfile table has `organization_id` column
- [ ] User table linked to Organization

### Frontend Integration
- [ ] _app.tsx handles Supabase OAuth callback
- [ ] API client extracts token from auth store
- [ ] sessionStorage used (not localStorage)
- [ ] Error handling for expired tokens

### Widget Integration
- [ ] Widget receives `businessId` from embedding
- [ ] Widget generates or receives `widgetToken`
- [ ] Widget fallback to `widgetApiKey` works
- [ ] CORS allows widget origin

---

## Common Issues & Fixes

### Issue: "Invalid CSRF token"
**Solution:**
- Ensure request includes both header and cookie
- Cookie name: `csrf_token`
- Header name: `x-csrf-token`
- Values must match exactly

### Issue: "Rate limit exceeded"
**Solution:**
- Public agent endpoints: 30 req/min per IP
- Authenticated endpoints: 100 req/min per IP
- Org-level limits apply additionally
- Window: 60 seconds (rolling)

### Issue: "Invalid widget token"
**Solution:**
- Token must be generated with `create_widget_token()`
- Token expires after 1 hour by default
- Regenerate with longer expiry if needed:
  ```python
  create_widget_token(
    organization_id=org_id,
    expires_delta=timedelta(hours=8)
  )
  ```

### Issue: "Cross-org data access denied"
**Solution:**
- Verify user's organization_id matches
- Knowledge search uses `current_user["organization_id"]`
- Cannot override with request parameter
- Widget must be scoped to same organization

### Issue: "Prompt injection detected"
**Solution:**
- Review message/knowledge content
- Pattern matching is strict (case-insensitive)
- Common phrases: "ignore previous", "forget all"
- Sanitization removes malicious patterns

---

## Testing Commands

```bash
# Test backend syntax
python -m py_compile packages/core/security.py

# Test widget auth
curl -H "X-Widget-Token: <jwt-token>" \
     -H "Content-Type: application/json" \
     -d '{"message":"Hello"}' \
     http://localhost:8000/api/v1/agent/message

# Test knowledge upload
curl -X POST \
     -H "Authorization: Bearer <access-token>" \
     -F "file=@document.txt" \
     -F "title=My Document" \
     http://localhost:8000/api/v1/knowledge/upload

# Test rate limiting (should fail after 30 requests)
for i in {1..35}; do
  curl http://localhost:8000/api/v1/agent/stream
done
```

---

## Token Expiry Defaults

| Token Type | Expiry | Config |
|---|---|---|
| Access Token | 30 minutes | ACCESS_TOKEN_EXPIRE_MINUTES |
| Refresh Token | 7 days | REFRESH_TOKEN_EXPIRE_DAYS |
| Widget Token | 1 hour | (function parameter) |
| CSRF Token | Session | (set in middleware) |

---

## Support & Troubleshooting

See [SECURITY_HARDENING_SUMMARY.md](SECURITY_HARDENING_SUMMARY.md) for:
- Detailed architecture overview
- Full implementation guide
- Security features explanation
- Database schema requirements
- Future enhancements
