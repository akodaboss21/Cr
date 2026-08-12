# Booking Audit Report

## Scope
This audit reviews the existing booking foundations in the repository and defines the booking engine additions required for Carai's appointment workflow.

## Current state
- A basic booking module exists under packages/core/identity/booking with simple SQLAlchemy models and FastAPI controllers.
- The current implementation stores generic bookings but does not include service catalogs, staff records, availability logic, AI-driven booking flow, reminders, or calendar adapters.
- The AI receptionist tool layer includes placeholder booking and availability tools, but they are not yet connected to a real scheduling engine.

## Gaps identified
1. No business scheduling entities for services or staff.
2. No availability engine for business hours, staff schedules, and existing appointments.
3. No appointment lifecycle with statuses like REQUESTED, CONFIRMED, COMPLETED, CANCELLED, and NO_SHOW.
4. No reminder abstraction for email, SMS, or WhatsApp.
5. No booking security rules for double booking, invalid times, and past appointments.
6. No end-to-end flow that translates an AI message into a completed appointment.

## Recommended implementation
- Add a business scheduling service that manages services, staff, appointments, availability, AI conversation prompts, reminders, and calendar adapters.
- Expose the engine through the existing backend package structure without modifying frontend pages.
- Add tests that cover customer booking, cancellation, availability, multiple staff, and multiple services.
