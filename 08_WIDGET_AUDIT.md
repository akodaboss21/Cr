# 08 Widget Audit

## Overall assessment
The widget is present and has a functional UI shell, but it is not yet production-integrated with the backend and is not ready for real site installation.

## Strengths
- The widget bundle in [apps/widget/widget.js](apps/widget/widget.js) includes chat UI, rate limiting, branding hooks, and websocket setup logic.
- The widget markup in [apps/widget/widget.html](apps/widget/widget.html) provides a browser-embedded experience.

## Gaps
- The widget attempts to call `/api/agent/message`, `/api/branding/:business_id`, and `/api/analytics/widget`, but there is no reliable backend path proving those routes are implemented end to end.
- The websocket setup points to `/ws/widget`, but there is no matching backend websocket implementation in the repository.
- The installation flow is not operationally wired to business registration and branding activation.

## Production readiness conclusion
The widget has architectural promise, but it cannot be sold as a ready-to-install customer feature until the backend endpoints and websocket path are implemented and validated.
