# 02 Architecture Review

## Architectural shape
The repository is a hybrid system:
- Frontend: Next.js single-app SPA-style multi-page experience in [carai-receptionist](carai-receptionist).
- Backend: Python package-based service layer in [packages/core](packages/core).
- Widget: Standalone browser script in [apps/widget](apps/widget).
- Channel adapters: lightweight channel abstraction in [channels](channels).

## Strengths
- The codebase is organized by domain modules rather than a single monolithic file.
- The backend has clear domain boundaries for auth, organizations, billing, bookings, CRM, conversations, knowledge, and AI gateway.
- The frontend uses a reusable shell in [carai-receptionist/src/components/layout/AppShell.tsx](carai-receptionist/src/components/layout/AppShell.tsx), which is a good foundation for a multi-page admin experience.

## Gaps
- The architecture is not yet fully connected end-to-end. The frontend pages are not consuming real services, and the backend services are not fully integrated with persistence or real providers.
- The onboarding workflow is present as a service but not wired to persistent storage or end-to-end business activation.
- The AI subsystem is modular but not yet production-executed. It depends on placeholder knowledge retrieval and non-executed integrations.

## Assessment
The architecture is suitable as a foundation for eventual integration into Admin ESA, but it is incomplete as a production SaaS platform. It should be treated as a modular MVP foundation that still requires runtime integration, persistence, and operational hardening.

## Evidence
- API routes are assembled in [packages/core/identity/api_gateway.py](packages/core/identity/api_gateway.py).
- The AI gateway exists in [packages/core/ai/gateway/__init__.py](packages/core/ai/gateway/__init__.py).
- The onboarding service remains placeholder-driven in [packages/core/branding/onboarding_service.py](packages/core/branding/onboarding_service.py).
