"""
Booking Module - Controller
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import datetime

from packages.core.database import get_db
from packages.core.security import get_current_user
from packages.core.identity.booking.models import Booking
from packages.core.identity.schemas import (
    BookingCreate, BookingUpdate, BookingResponse
)

router = APIRouter(prefix="/bookings", tags=["bookings"])

@router.post("/", response_model=BookingResponse)
async def create_booking(
    booking_create: BookingCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new booking"""
    # Verify user has permission to create booking
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    # Create booking
    db_booking = Booking(
        id=str(uuid4()),
        organization_id=current_user["organization_id"],
        business_id=booking_create.business_id,
        customer_id=current_user["user_id"],
        title=booking_create.title,
        description=booking_create.description,
        status=booking_create.status,
        start_time=booking_create.start_time,
        end_time=booking_create.end_time,
        timezone=booking_create.timezone,
        attendees=booking_create.attendees,
        calendar_event_id=booking_create.calendar_event_id,
        google_calendar_id=booking_create.google_calendar_id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    
    return BookingResponse.from_orm(db_booking)

@router.get("/", response_model=List[BookingResponse])
async def get_bookings(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """Get a list of bookings"""
    # Verify user has permission
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    bookings = db.query(Booking).filter(
        Booking.organization_id == current_user["organization_id"]
    ).offset(skip).limit(limit).all()
    
    return [BookingResponse.from_orm(booking) for booking in bookings]

@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific booking"""
    # Verify user has permission
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    booking = db.query(Booking).filter(
        Booking.id == booking_id,
        Booking.organization_id == current_user["organization_id"]
    ).first()
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    return BookingResponse.from_orm(booking)

@router.put("/{booking_id}", response_model=BookingResponse)
async def update_booking(
    booking_id: str,
    booking_update: BookingUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a booking"""
    # Verify user has permission
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    booking = db.query(Booking).filter(
        Booking.id == booking_id,
        Booking.organization_id == current_user["organization_id"]
    ).first()
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    # Update fields
    for field, value in booking_update.dict(exclude_unset=True).items():
        setattr(booking, field, value)
    
    booking.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(booking)
    
    return BookingResponse.from_orm(booking)

@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_booking(
    booking_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a booking"""
    # Verify user has permission
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    booking = db.query(Booking).filter(
        Booking.id == booking_id,
        Booking.organization_id == current_user["organization_id"]
    ).first()
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    db.delete(booking)
    db.commit()
    
    return None