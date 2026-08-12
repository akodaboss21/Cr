# Tenant Isolation Audit

## Scope

This audit reviews tenant isolation across backend controllers, public AI gateway paths, service access patterns, analytics/metrics, widget auth flows, and memory retrieval used by the reception agent.

Focused files and modules reviewed include:

- `packages/core/identity/api_gateway.py`
- `packages/core/identity/controllers/*`
- `packages/core/identity/ai_gateway/controllers/*`
- `packages/core/ai/memory.py`
- `packages/core/ai/reception/tools.py`
- `packages/core/identity/analytics/*`
- `packages/core/security.py`
- `packages/core/identity/event_system/*`
- `packages/core/identity/background_workers/controllers/background_workers_controller.py`
- `packages/core/identity/booking/controllers/booking_controller.py`
- `packages/core/identity/business/controllers/business_controller.py`
- `packages/core/identity/knowledge/controllers/knowledge_controller.py`
- `packages/core/identity/notification/controllers/notification_controller.py`
- `packages/core/identity/integration/controllers/integration_controller.py`
- `packages/core/identity/crm/controllers/crm_controller.py`
- `packages/core/identity/conversation/controllers/conversation_controller.py`
- `packages/core/identity/organizations/controllers/organization_controller.py`

## Summary

The codebase demonstrates strong tenant isolation in most CRUD endpoints. The dominant enforcement pattern is:

- require `current_user` via `get_current_user`
- validate `current_user` contains `organization_id`
- apply `Model.organization_id == current_user["organization_id"]` to queries

This pattern is consistently present in the majority of business, booking, CRM, notification, integration, knowledge, conversation, background worker, billing, and AI provider/prompt-template endpoints.

## Confirmed Coverage

The following controller areas show proper tenant-scoped enforcement:

- business profile endpoints
- booking CRUD endpoints
- CRM create/read/update/delete/search
- conversation CRUD and message access
- knowledge create/update/delete/search
- notification records and notification setting CRUD
- integration CRUD
- background worker and job CRUD
- billing subscription/usage endpoints
- AI provider, prompt template, and usage record CRUD
- organization endpoints with admin-only global access and scoped org access for non-admins
- auth token creation and current-user lookup properly validates `org_id` against stored user org
- streaming endpoints for completions and embeddings require `current_user` and attach `organization_id` from the authenticated user

## Major Gaps and Vulnerabilities

### 1. Analytics metrics are not tenant-scoped

File: `packages/core/identity/ai_gateway/controllers/analytics_controller.py`
- `GET /analytics/metrics` requires auth but uses `AnalyticsService.get_metrics()` which does not filter by the current user's organization.
- `GET /analytics/lead-metrics`, `/pipeline-metrics`, `/engagement-metrics` have no auth requirement and return global metrics.

File: `packages/core/identity/analytics/services.py`
- `AnalyticsService` methods query analytics tables without `organization_id` filters.
- `MetricCalculatorService` methods use model query syntax with no org filtering.

Impact:
- authenticated users may see global analytics for all organizations.
- unauthenticated clients can access analytics metrics endpoints.

### 2. Reception agent memory loading has no organization validation

File: `packages/core/ai/memory.py`
- `ShortTermMemory.load_conversation()` loads a conversation by `conversation_id` only.
- `LongTermMemory._load_customer()` loads a customer by `customer_id` only.

File: `packages/core/identity/ai_gateway/controllers/agent_controller.py`
- `conversation_id` may be provided by the client payload.
- `customer_id` may also be provided in payload or derived from widget token claims.

Impact:
- a client could supply an existing `conversation_id` from another organization and retrieve conversation history or context without org validation.
- a client could supply a `customer_id` from another organization and access cross-tenant customer memory.

### 3. Event system subscriber creation accepts payload org claims

File: `packages/core/identity/event_system/controllers/event_system_controller.py`
- `create_event_subscriber()` creates `EventSubscriber(organization_id=subscriber_create.organization_id)` using client-provided data.
- there is no enforcement that this `organization_id` matches `current_user["organization_id"]`.

Impact:
- users can create subscriptions for a different organization by manipulating the request payload.

### 4. Event trigger model and controller are inconsistent

File: `packages/core/identity/event_system/models.py`
- `EventTrigger` does not define `organization_id`.

File: `packages/core/identity/event_system/controllers/event_system_controller.py`
- many actions filter on `EventTrigger.organization_id == current_user["organization_id"]`.
- this mismatch means the controller expectations do not match the stored model schema.

Impact:
- event trigger CRUD behavior is unreliable and may fail or silently bypass tenant enforcement.

### 5. Onboarding flow bypasses tenant auth and org validation

File: `packages/core/identity/onboarding/controller.py`
- onboarding endpoints are unauthenticated and accept `organization_id` in payload or query.
- `submit_step`, `get_onboarding`, and `activate_onboarding` all load `OnboardingRecord` by ID only, with no organization scope check.

Impact:
- an attacker with onboarding record IDs can read or modify onboarding data across organizations.
- a client can activate onboarding for a record belonging to another tenant.

### 6. Widget auth can be used to infer or control organization context without strict scoping

File: `packages/core/identity/ai_gateway/controllers/agent_controller.py`
- widget API key auth can accept `organization_id` from the payload without additional validation.
- widget token auth derives org/customer/business claims from an HMAC-signed token, but there is no business-to-org membership check beyond direct lookup when `business_id` is provided.

Impact:
- a global widget API key could be used to access or act on behalf of any org if the requester knows a valid `organization_id` or `business_id`.
- the system should scope widget keys/tokens to a single organization/business and reject mismatched payloads.

## Additional Observations

### Auth and token handling

- `packages/core/security.py` validates `org_id` from JWT claims against the user's stored `organization_id`.
- `get_current_user()` correctly rejects access tokens that do not match the user’s org.
- This is a strong foundation for tenant isolation when controllers require the dependency.

### Analytics and metrics

- `packages/core/identity/analytics/services.py` and `packages/core/identity/ai_gateway/controllers/analytics_controller.py` need org-scoped filters and auth on all metrics endpoints.
- `MetricCalculatorService` uses model query syntax with no DB session or org context; this is both unscoped and likely non-functional in the current codebase.

### Service layers and memory access

- `packages/core/ai/memory.py` loads conversation and customer memory without org constraints.
- `packages/core/ai/reception/tools.py` service methods correctly accept `organization_id` and filter by it, but the calling reception agent may still instantiate memory from unvalidated IDs.

### Event system

- `EventSubscriber` creation should be restricted to the current user's org.
- `EventTrigger` model should include `organization_id` if the controller is enforcing it.

## Recommendations

1. Fix analytics metrics endpoints:
   - require `get_current_user()` for all metrics routes
   - apply `Analytics.organization_id == current_user["organization_id"]` in `AnalyticsService`
   - add org-aware metrics for `LeadMetrics`, `PipelineMetrics`, and `EngagementMetrics` or remove unauthenticated endpoints

2. Harden onboarding:
   - require auth for onboarding record retrieval and updates
   - apply `OnboardingRecord.organization_id == current_user["organization_id"]` to all lookups
   - reject payload org IDs that do not match the authenticated org

3. Harden agent memory and widget auth:
   - validate `conversation_id` and `customer_id` against `organization_id` before loading memory
   - scope widget API keys/tokens to a specific organization/business and reject mismatched payloads

4. Fix event system model/controller mismatch:
   - add `organization_id` to `EventTrigger`
   - ensure `create_event_subscriber()` uses `current_user["organization_id"]` instead of payload-supplied org IDs

5. Add targeted tests:
   - cross-tenant access tests for analytics, onboarding, event subscriber creation, and agent memory retrieval
   - ensure widget auth does not permit org spoofing

## Conclusion

Tenant isolation is mostly enforced at the controller/query level, but there are critical gaps in analytics, onboarding, agent memory loading, widget auth context, and event system model consistency.

These areas should be remediated before claiming complete multi-tenant separation.
