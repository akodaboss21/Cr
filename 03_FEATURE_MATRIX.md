# 03 Feature Matrix

| Feature | Status | Evidence | Notes |
|---|---|---|---|
| Authentication | 🟡 Partial | [packages/core/security.py](packages/core/security.py), [packages/core/identity/controllers/auth_controller.py](packages/core/identity/controllers/auth_controller.py) | JWT helpers and login endpoint exist, but real Supabase integration is incomplete and the frontend uses local-only auth state. |
| Authorization | 🟡 Partial | [packages/core/security.py](packages/core/security.py), [packages/core/identity/organizations/controllers/organization_controller.py](packages/core/organizations/controllers/organization_controller.py) | Role/permission checks are present in helpers, but permission assignment is not fully wired to runtime roles. |
| Tenant isolation | 🟡 Partial | [packages/core/identity/controllers/user_controller.py](packages/core/identity/controllers/user_controller.py), [packages/core/identity/crm/controllers/crm_controller.py](packages/core/identity/crm/controllers/crm_controller.py) | Organization-scoped queries are present in controllers, but end-to-end tenant enforcement is not validated in the full runtime. |
| Business onboarding | 🟡 Partial | [packages/core/branding/onboarding_service.py](packages/core/branding/onboarding_service.py) | Service exists, but it does not persist or complete production activation. |
| Knowledge upload | 🟡 Partial | [packages/core/identity/knowledge/controllers/knowledge_controller.py](packages/core/identity/knowledge/controllers/knowledge_controller.py) | CRUD exists, but upload, parsing, embedding, and retrieval are not fully operational. |
| Knowledge retrieval | 🔴 Missing | [packages/core/ai/reception/agent.py](packages/core/ai/reception/agent.py) | The agent returns an empty knowledge retrieval list. |
| Embedding pipeline | 🔴 Missing | [packages/core/ai/gateway/provider.py](packages/core/ai/gateway/provider.py) | Ollama embeddings are placeholder zeros. |
| Vector search | 🔴 Missing | [packages/core/identity/knowledge/models.py](packages/core/identity/knowledge/models.py) | Models exist, but no real vector search implementation is wired. |
| Conversation history | 🟡 Partial | [packages/core/identity/conversation/controllers/conversation_controller.py](packages/core/identity/conversation/controllers/conversation_controller.py) | CRUD exists, but the live agent flow does not fully use it. |
| CRM / lead capture | 🟡 Partial | [packages/core/identity/crm/controllers/crm_controller.py](packages/core/identity/crm/controllers/crm_controller.py) | CRUD exists, but lead creation is not fully connected to the live agent workflow. |
| Bookings | 🟡 Partial | [packages/core/identity/booking/controllers/booking_controller.py](packages/core/identity/booking/controllers/booking_controller.py) | CRUD and booking models exist, but calendar integration is incomplete. |
| Notifications | 🟡 Partial | [notifications/engine.py](notifications/engine.py) | Notification engine exists, but runtime provider configuration is not validated fully. |
| Widget | 🟡 Partial | [apps/widget/widget.js](apps/widget/widget.js) | Widget UI exists, but installation and backend integration are incomplete. |
| Realtime updates | 🔴 Missing | [apps/widget/widget.js](apps/widget/widget.js) | WebSocket connection is attempted but no backend websocket implementation is provided. |
| Analytics | 🟡 Partial | [packages/core/identity/ai_gateway/controllers/analytics_controller.py](packages/core/identity/ai_gateway/controllers/analytics_controller.py) | Endpoint scaffolding exists, but it is not tied to complete operational telemetry. |
| Billing / subscriptions | 🟡 Partial | [packages/core/identity/billing/controllers/billing_controller.py](packages/core/identity/billing/controllers/billing_controller.py) | Billing flows exist, but real payments depend on live Stripe configuration. |
| Admin dashboard | 🟡 Partial | [carai-receptionist/src/components/layout/AppShell.tsx](carai-receptionist/src/components/layout/AppShell.tsx) | Admin shell exists, but real data views are not connected. |
| Audit logging | 🟡 Partial | [packages/core/middleware.py](packages/core/middleware.py) | Middleware logs requests, but persistence is not fully proven for production use. |
| Worker / PyRunner | 🔴 Missing | [packages/core/identity/background_workers/controllers/background_workers_controller.py](packages/core/identity/background_workers/controllers/background_workers_controller.py) | Controllers exist, but actual queue processing is not implemented. |
| OpenAI compatibility | 🟡 Partial | [packages/core/ai/gateway/openai_provider.py](packages/core/ai/gateway/openai_provider.py) | Provider exists, but request handling is flawed and not reliable. |
| Ollama compatibility | 🟡 Partial | [packages/core/ai/gateway/provider.py](packages/core/ai/gateway/provider.py) | Provider exists, but embeddings and completions are placeholder-oriented. |
| Streaming | 🟡 Partial | [packages/core/identity/ai_gateway/controllers/streaming.py](packages/core/identity/ai_gateway/controllers/streaming.py) | Streaming endpoints exist, but they are not fully validated against a working provider. |
| Security headers / validation | 🟡 Partial | [packages/core/middleware.py](packages/core/middleware.py), [packages/core/security.py](packages/core/security.py) | Good foundation, but not enough for a public customer-facing deployment. |
| Docker / deployment | 🟡 Partial | [carai-receptionist/docker-compose.yml](carai-receptionist/docker-compose.yml) | Docker exists, but production deployment wiring is incomplete. |
| CI / CD | 🔴 Missing | [.github/workflows/ci-cd.yml](.github/workflows/ci-cd.yml) | Root workflow file is empty; the frontend workflow is incomplete. |
