from datetime import datetime, timedelta

from packages.core.identity.booking.service import BookingEngineService
from packages.core.identity.booking.conversation import BookingConversationService
from packages.core.identity.booking.reminders import ReminderService
from packages.core.identity.booking.calendar_adapters import GoogleCalendarAdapter, OutlookCalendarAdapter


def test_customer_booking_flow_and_cancellation():
    service = BookingEngineService(organization_id="org-1")
    service.create_service("org-1", "Haircut", "Classic haircut", 45, 50.0, True)
    service.create_staff_member("org-1", "Barber", "Barber", {"monday": "09:00-17:00"}, True)

    tomorrow = (datetime.utcnow() + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
    appointment = service.create_appointment(
        organization_id="org-1",
        customer_id="cust-1",
        service_id="service-1",
        staff_id="staff-1",
        start_time=tomorrow,
        end_time=tomorrow + timedelta(minutes=45),
        status="REQUESTED",
    )

    assert appointment.status == "REQUESTED"
    cancelled = service.cancel_appointment(appointment.id)
    assert cancelled.status == "CANCELLED"


def test_availability_and_multiple_staff():
    service = BookingEngineService(organization_id="org-2")
    service.create_service("org-2", "Braiding", "Braiding service", 60, 80.0, True)
    service.create_staff_member("org-2", "Stylist", "Stylist", {"monday": "09:00-17:00"}, True)
    service.create_staff_member("org-2", "Assistant", "Stylist", {"monday": "09:00-17:00"}, True)

    start = datetime(2026, 8, 10, 9, 0, 0)
    slots = service.get_available_slots("org-2", service_id="service-1", start_time=start, end_time=start + timedelta(days=1))

    assert len(slots) > 0
    assert any(slot["staff_id"] == "staff-1" for slot in slots)
    assert any(slot["staff_id"] == "staff-2" for slot in slots)


def test_ai_booking_flow_asks_for_service_and_time():
    service = BookingEngineService(organization_id="org-3")
    service.create_service("org-3", "Manicure", "Manicure service", 30, 40.0, True)
    service.create_staff_member("org-3", "Nail technician", "Nail technician", {"monday": "09:00-17:00"}, True)

    conversation = BookingConversationService(service)
    result = conversation.handle_message("I want a manicure tomorrow")

    assert result["step"] == "ask_time"
    assert "Manicure" in result["message"]


def test_reminders_and_calendar_adapters_are_ready():
    reminders = ReminderService()
    reminder = reminders.schedule_reminder("org-4", "cust-4", "email", "Appointment reminder")
    assert reminder["status"] == "queued"

    google = GoogleCalendarAdapter()
    outlook = OutlookCalendarAdapter()
    assert google.publish({"id": "1"})["status"] == "pending"
    assert outlook.publish({"id": "1"})["status"] == "pending"
