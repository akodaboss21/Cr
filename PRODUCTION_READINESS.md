# Carai AI Receptionist Production Readiness Tracker

This document is the single source of truth for the gaps that remain before Carai AI Receptionist is production-ready.

## Status legend
- TODO: Not started
- IN PROGRESS: Partial implementation exists, but the work is not complete
- DONE: The requirement is implemented and verified

---

## 1) Real RAG / Knowledge pipeline (embeddings + vector search)
- Status: IN PROGRESS
- Owner: AI Platform

### Files with current stubs or incomplete implementation
- packages/core/ai/gateway/provider.py
  - Ollama provider path contains fallback embeddings and incomplete provider support.
- packages/core/ai/gateway/openai_provider.py
  - Embedding/completion/streaming code is implemented but still requires verification and provider capability alignment.
- packages/core/ai/retrieval.py
  - Query embedding and retrieval fallback logic still supports non-production hashed embeddings.
- packages/core/ai/reception/agent.py
  - Retrieving knowledge falls back to the generic retrieval engine and may still rely on placeholder semantic ranking.
- packages/core/ai/memory.py
  - Memory manager and long-term memory remain largely placeholder and not fully persisted.
- packages/core/ai/prompt_manager.py
  - Prompt templates are hardcoded and not stored as production prompt assets.
- packages/core/identity/knowledge/controllers/knowledge_controller.py
  - Embedding generation is best-effort and errors are swallowed, leaving knowledge items unprocessed.

### Acceptance criteria for DONE
- Real embeddings are generated and persisted for knowledge objects.
- Vector search returns semantically ranked results from stored embedding vectors.
- ReceptionAgent retrieval uses the RAG pipeline rather than keyword-only fallback behavior.
- No production path relies on fallback embedding hashing as the primary retrieval signal.
- Retrieval behavior is covered by a relevance smoke test.

---

## 2) ReceptionAgent fully wired to CRM, Booking, Knowledge, Tools (no print statements)
- Status: DONE
- Owner: Backend AI / Integrations

### Files confirming the implementation
- packages/core/ai/reception/agent.py
  - Full pipeline is wired: intent classification, knowledge retrieval, planning, tool execution, response generation, memory update, and lead handling.
- packages/core/ai/reception/tools.py
  - `CRMService`, `BookingService`, `KnowledgeService`, and `BusinessService` are implemented and used by `ToolExecutor`.
- packages/core/identity/ai_gateway/controllers/agent_controller.py
  - The public endpoint constructs the agent and executes the full pipeline.

### Acceptance criteria for DONE
- The ReceptionAgent can call CRM, booking, knowledge, and tool services through real adapters.
- No `print()` debugging remains in the agent path.
- Tool execution is invoked through `ToolExecutor` and returns structured results.
- A normal chat request can create/update CRM records and perform knowledge lookups without manual intervention.

---

## 3) Public chat endpoint that runs the full ReceptionAgent
- Status: DONE
- Owner: Backend API

### Files confirming the implementation
- packages/core/identity/ai_gateway/controllers/agent_controller.py
  - Exposes `POST /api/v1/agent/message` and `POST /api/v1/agent/stream` for ReceptionAgent execution.
- packages/core/identity/api_gateway.py
  - Routes `agent_controller` under the `/api/v1` prefix.

### Acceptance criteria for DONE
- A public endpoint accepts a chat request and executes the full ReceptionAgent pipeline.
- The endpoint resolves tenant/auth context and returns structured agent responses.
- `conversation_id` is returned so the client can continue the session.
- Agent failure cases return structured errors.

---

## 4) Widget ↔ Backend contract alignment (paths, auth, WebSocket)
- Status: IN PROGRESS
- Owner: Frontend Platform

### Files with current contract gaps
- apps/widget/widget.js
  - Widget currently calls `/api/agent/message` and `/ws/widget`.
- carai-receptionist/src/features/widget/widget.ts
  - Widget defaults are static and not aligned with backend auth contract.
- packages/core/identity/ai_gateway/controllers/agent_controller.py
  - Backend exposes `/api/v1/agent/message` and `/api/v1/agent/stream`, not the widget’s current hardcoded path.
- packages/core/identity/ai_gateway/controllers/streaming.py
  - Existing generic streaming endpoint is still separate from widget expectations.

### Acceptance criteria for DONE
- The widget and backend share a single documented request/response contract for chat and streaming.
- The widget uses valid tenant/business identifiers and auth headers/token handling.
- REST chat and streaming routes use the same schema and conversation IDs.
- The widget no longer depends on an unsupported `/ws/widget` backend path unless WebSocket support is implemented.

---

## 5) Frontend onboarding connected to real backend + activation
- Status: IN PROGRESS
- Owner: Product / Frontend

### Files with current placeholders or missing integration
- carai-receptionist/src/features/onboarding/OnboardingWizard.tsx
  - UI is local-state only and does not submit data to the backend.
- carai-receptionist/pages/onboarding.tsx
  - Page renders the wizard shell without backend wiring.
- packages/core/branding/onboarding_service.py
  - Onboarding flow persists data in-memory and has a commented-out `_activate_receptionist` hook.

### Acceptance criteria for DONE
- The onboarding wizard submits business profile, website, knowledge, and activation data to backend APIs.
- Backend persistence completes onboarding and activates the receptionist configuration.
- The UI displays live activation success/failure from the backend.
- A new customer can finish onboarding and reach a live receptionist state without manual back-office intervention.

---

## 6) Streaming path that uses ReceptionAgent (not generic LLM)
- Status: IN PROGRESS
- Owner: Streaming / AI Backend

### Files with current streaming gaps
- packages/core/identity/ai_gateway/controllers/agent_controller.py
  - Provides `POST /api/v1/agent/stream` for ReceptionAgent SSE streaming.
- packages/core/identity/ai_gateway/controllers/streaming.py
  - Generic `/ai/stream/complete` path still routes standard LLM streaming and is separate.
- packages/core/ai/reception/agent.py
  - ReceptionAgent supports streaming but the client contract is not yet fully aligned.
- apps/widget/widget.js
  - Widget expects a WebSocket-based stream path that is not implemented server-side.

### Acceptance criteria for DONE
- Streaming responses are delivered by `ReceptionAgent.process_message_stream` rather than the generic LLM gateway.
- The streaming endpoint preserves conversation state and tool execution context.
- Clients receive chunked tokens or SSE events and a clear done event.
- Streaming behavior is covered by a regression test.

---

## 7) Provider fixes (OpenAI client, real embeddings)
- Status: IN PROGRESS
- Owner: AI Infrastructure

### Files with provider issues
- packages/core/ai/gateway/provider.py
  - The Ollama/provider wrapper still contains incomplete provider plumbing.
- packages/core/ai/gateway/openai_provider.py
  - OpenAI-compatible request handling is implemented but requires production validation and model capability alignment.
- packages/core/ai/retrieval.py
  - Embedding fallback behavior still exists and must be de-emphasized.
- packages/core/identity/knowledge/controllers/knowledge_controller.py
  - Embedding generation can fail silently, leaving knowledge rows in an unprocessed state.

### Acceptance criteria for DONE
- Provider code uses correct OpenAI-compatible request/response formats for completions, streaming, and embeddings.
- Embeddings are generated with real vector values for production providers.
- Provider health checks and retry/error propagation are robust and test-covered.
- The gateway selects models/capabilities without manual patching.

---

## 8) Tenant isolation, auth, rate limiting, security hardening
- Status: IN PROGRESS
- Owner: Security / Platform

### Files with current security gaps
- packages/core/security.py
  - Core auth and JWT handling exist, but production hardening and access policy enforcement are incomplete.
- packages/core/middleware.py
  - Rate limiting and request validation are basic and need stronger production controls.
- packages/core/identity/ai_gateway/controllers/agent_controller.py
  - Organization resolution is implemented, but widget auth and tenant enforcement need validation across the full public path.
- packages/core/identity/knowledge/controllers/knowledge_controller.py
  - Knowledge endpoints enforce organization scope but should be audited for consistent behavior.

### Acceptance criteria for DONE
- Every public and internal endpoint enforces organization-scoped authorization.
- Auth tokens are validated with role/permission checks and no cross-tenant access exists.
- Rate limiting and request validation are active on public chat and knowledge paths.
- Security tests cover tenant isolation, auth failures, and abuse protection.

---

## 9) End-to-end test suite + smoke tests
- Status: TODO
- Owner: QA / Engineering

### Files with current test coverage gaps
- tests/
  - Existing tests are mostly unit-level and do not cover a full onboarding-to-chat production flow.
- carai-receptionist/__tests__/onboarding-wizard.test.tsx
  - UI tests exist, but there is no end-to-end backend onboarding integration validation.
- .github/workflows/ci-cd.yml
  - The workflow file is empty and does not run tests or smoke automation.

### Acceptance criteria for DONE
- A smoke test suite exercises widget chat, backend agent response, and onboarding activation.
- End-to-end tests validate provider fallback, auth/tenant failure paths, and streaming behavior.
- CI runs these tests automatically on every merge to main.

---

## 10) Observability, deployment, CI/CD
- Status: IN PROGRESS
- Owner: DevOps / Platform

### Files with current deployment/observability gaps
- .github/workflows/ci-cd.yml
  - Empty workflow file; no CI/CD automation is configured.
- packages/core/logging.py
  - Structured logging exists, but request IDs, error tracking, and alert hooks are not fully wired.
- packages/core/middleware.py
  - Audit logging exists, but production monitoring and event correlation need hardening.
- packages/core/identity/api_gateway.py
  - API registration exists, but deployment, health checks, and route-level observability are not fully defined.

### Acceptance criteria for DONE
- CI runs linting, unit tests, and smoke tests automatically.
- Production deployment is scripted and configuration-driven.
- Structured logs include request IDs, organization context, and error metadata.
- A documented deployment runbook and rollback process exist in the repository.
