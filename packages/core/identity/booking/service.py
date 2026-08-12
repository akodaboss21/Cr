from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import uuid4


@dataclass
class ServiceRecord:
    id: str
    organization_id: str
    name: str
    description: str
    duration: int
    price: float
    active: bool


@dataclass
class StaffMember:
    id: str
    organization_id: str
    name: str
    role: str
    availability: Dict[str, Any]
    active: bool


@dataclass
class AppointmentRecord:
    id: str
    organization_id: str
    customer_id: str
    service_id: str
    staff_id: str
    start_time: datetime
    end_time: datetime
    status: str
    created_at: datetime = field(default_factory=datetime.utcnow)


class BookingEngineService:
    def __init__(self, organization_id: str):
        self.organization_id = organization_id
        self._services: Dict[str, ServiceRecord] = {}
        self._staff_members: Dict[str, StaffMember] = {}
        self._appointments: Dict[str, AppointmentRecord] = {}
        self._service_counter = 0
        self._staff_counter = 0
        self._appointment_counter = 0

    def create_service(
        self,
        organization_id: str,
        name: str,
        description: str,
        duration: int,
        price: float,
        active: bool,
    ) -> ServiceRecord:
        self._service_counter += 1
        service = ServiceRecord(
            id=f"service-{self._service_counter}",
            organization_id=organization_id,
            name=name,
            description=description,
            duration=duration,
            price=price,
            active=active,
        )
        self._services[service.id] = service
        return service

    def create_staff_member(
        self,
        organization_id: str,
        name: str,
        role: str,
        availability: Dict[str, Any],
        active: bool,
    ) -> StaffMember:
        self._staff_counter += 1
        staff = StaffMember(
            id=f"staff-{self._staff_counter}",
            organization_id=organization_id,
            name=name,
            role=role,
            availability=availability,
            active=active,
        )
        self._staff_members[staff.id] = staff
        return staff

    def create_appointment(
        self,
        organization_id: str,
        customer_id: str,
        service_id: str,
        staff_id: str,
        start_time: datetime,
        end_time: datetime,
        status: str = "REQUESTED",
    ) -> AppointmentRecord:
        self._validate_booking(organization_id, service_id, staff_id, start_time, end_time)
        self._appointment_counter += 1
        appointment = AppointmentRecord(
            id=f"appointment-{self._appointment_counter}",
            organization_id=organization_id,
            customer_id=customer_id,
            service_id=service_id,
            staff_id=staff_id,
            start_time=start_time,
            end_time=end_time,
            status=status,
        )
        self._appointments[appointment.id] = appointment
        return appointment

    def cancel_appointment(self, appointment_id: str) -> AppointmentRecord:
        appointment = self._appointments[appointment_id]
        appointment.status = "CANCELLED"
        return appointment

    def get_available_slots(
        self,
        organization_id: str,
        service_id: str,
        start_time: datetime,
        end_time: datetime,
    ) -> List[Dict[str, Any]]:
        service = self._services[service_id]
        slots: List[Dict[str, Any]] = []
        for staff_id, staff in self._staff_members.items():
            if staff.organization_id != organization_id or not staff.active:
                continue
            current = start_time
            while current + timedelta(minutes=service.duration) <= end_time:
                candidate_end = current + timedelta(minutes=service.duration)
                if self._is_slot_open(staff_id, current, candidate_end):
                    slots.append(
                        {
                            "staff_id": staff_id,
                            "staff_name": staff.name,
                            "service_id": service_id,
                            "service_name": service.name,
                            "start_time": current.isoformat(),
                            "end_time": candidate_end.isoformat(),
                        }
                    )
                current += timedelta(minutes=30)
        return slots

    def _is_slot_open(self, staff_id: str, start_time: datetime, end_time: datetime) -> bool:
        for appointment in self._appointments.values():
            if appointment.staff_id != staff_id:
                continue
            if appointment.status in {"CANCELLED", "COMPLETED", "NO_SHOW"}:
                continue
            if start_time < appointment.end_time and end_time > appointment.start_time:
                return False
        return True

    def _validate_booking(
        self,
        organization_id: str,
        service_id: str,
        staff_id: str,
        start_time: datetime,
        end_time: datetime,
    ) -> None:
        if start_time < datetime.utcnow():
            raise ValueError("Past appointments are not allowed")
        if start_time >= end_time:
            raise ValueError("Invalid appointment time range")
        if service_id not in self._services:
            raise ValueError("Service not found")
        if staff_id not in self._staff_members:
            raise ValueError("Staff not found")
        for appointment in self._appointments.values():
            if appointment.staff_id != staff_id:
                continue
            if appointment.status in {"CANCELLED", "COMPLETED", "NO_SHOW"}:
                continue
            if start_time < appointment.end_time and end_time > appointment.start_time:
                raise ValueError("Double booking prevented")
