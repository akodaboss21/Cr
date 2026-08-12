"""
Event System - Controller
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import datetime

from packages.core.database import get_db
from packages.core.security import get_current_user
from packages.core.identity.event_system.models import Event, EventSubscriber, EventTrigger
from packages.core.identity.event_system.schemas import (
    EventCreate, EventUpdate, EventResponse,
    EventSubscriberCreate, EventSubscriberUpdate, EventSubscriberResponse,
    EventTriggerCreate, EventTriggerUpdate, EventTriggerResponse
)

router = APIRouter(tags=["events"])

# Event endpoints
@router.post("/", response_model=EventResponse)
async def create_event(
    event_create: EventCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new event"""
    # Verify user has permission to create event
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    # Create event
    db_event = Event(
        id=str(uuid4()),
        organization_id=current_user["organization_id"],
        name=event_create.name,
        event_type=event_create.event_type,
        description=event_create.description,
        is_active=event_create.is_active,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    
    return EventResponse.from_orm(db_event)

@router.get("/", response_model=List[EventResponse])
async def get_events(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """Get a list of events"""
    # Verify user has permission
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    events = db.query(Event).filter(
        Event.organization_id == current_user["organization_id"]
    ).offset(skip).limit(limit).all()
    
    return [EventResponse.from_orm(event) for event in events]

@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific event"""
    # Verify user has permission
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    event = db.query(Event).filter(
        Event.id == event_id,
        Event.organization_id == current_user["organization_id"]
    ).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    return EventResponse.from_orm(event)

@router.put("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: str,
    event_update: EventUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update an event"""
    # Verify user has permission
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    event = db.query(Event).filter(
        Event.id == event_id,
        Event.organization_id == current_user["organization_id"]
    ).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Update fields
    for field, value in event_update.dict(exclude_unset=True).items():
        setattr(event, field, value)
    
    event.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(event)
    
    return EventResponse.from_orm(event)

@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete an event"""
    # Verify user has permission
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    event = db.query(Event).filter(
        Event.id == event_id,
        Event.organization_id == current_user["organization_id"]
    ).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    db.delete(event)
    db.commit()
    
    return None

# Event Subscriber endpoints
@router.post("/subscribers/", response_model=EventSubscriberResponse)
async def create_event_subscriber(
    subscriber_create: EventSubscriberCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new event subscriber"""
    # Verify user has permission to create event subscriber
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    # Create event subscriber with organization from current user
    db_subscriber = EventSubscriber(
        id=str(uuid4()),
        event_id=subscriber_create.event_id,
        user_id=subscriber_create.user_id,
        organization_id=current_user["organization_id"],
        role=subscriber_create.role,
        notification_preferences=subscriber_create.notification_preferences,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(db_subscriber)
    db.commit()
    db.refresh(db_subscriber)
    
    return EventSubscriberResponse.from_orm(db_subscriber)

@router.get("/subscribers/", response_model=List[EventSubscriberResponse])
async def get_event_subscribers(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """Get a list of event subscribers"""
    # Verify user has permission
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    subscribers = db.query(EventSubscriber).filter(
        EventSubscriber.organization_id == current_user["organization_id"]
    ).offset(skip).limit(limit).all()
    
    return [EventSubscriberResponse.from_orm(subscriber) for subscriber in subscribers]

@router.get("/subscribers/{subscriber_id}", response_model=EventSubscriberResponse)
async def get_event_subscriber(
    subscriber_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific event subscriber"""
    # Verify user has permission
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    subscriber = db.query(EventSubscriber).filter(
        EventSubscriber.id == subscriber_id,
        EventSubscriber.organization_id == current_user["organization_id"]
    ).first()
    
    if not subscriber:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event subscriber not found"
        )
    
    return EventSubscriberResponse.from_orm(subscriber)

@router.put("/subscribers/{subscriber_id}", response_model=EventSubscriberResponse)
async def update_event_subscriber(
    subscriber_id: str,
    subscriber_update: EventSubscriberUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update an event subscriber"""
    # Verify user has permission
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    subscriber = db.query(EventSubscriber).filter(
        EventSubscriber.id == subscriber_id,
        EventSubscriber.organization_id == current_user["organization_id"]
    ).first()
    
    if not subscriber:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event subscriber not found"
        )
    
    # Update fields
    for field, value in subscriber_update.dict(exclude_unset=True).items():
        setattr(subscriber, field, value)
    
    subscriber.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(subscriber)
    
    return EventSubscriberResponse.from_orm(subscriber)

@router.delete("/subscribers/{subscriber_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event_subscriber(
    subscriber_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete an event subscriber"""
    # Verify user has permission
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    subscriber = db.query(EventSubscriber).filter(
        EventSubscriber.id == subscriber_id,
        EventSubscriber.organization_id == current_user["organization_id"]
    ).first()
    
    if not subscriber:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event subscriber not found"
        )
    
    db.delete(subscriber)
    db.commit()
    
    return None

# Event Trigger endpoints
@router.post("/triggers/", response_model=EventTriggerResponse)
async def create_event_trigger(
    trigger_create: EventTriggerCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new event trigger"""
    # Verify user has permission to create event trigger
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    event = db.query(Event).filter(
        Event.id == trigger_create.event_id,
        Event.organization_id == current_user["organization_id"]
    ).first()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Event does not exist or does not belong to your organization"
        )
    
    # Create event trigger
    db_trigger = EventTrigger(
        id=str(uuid4()),
        event_id=trigger_create.event_id,
        organization_id=current_user["organization_id"],
        name=trigger_create.name,
        condition=trigger_create.condition,
        action=trigger_create.action,
        parameters=trigger_create.parameters,
        is_active=trigger_create.is_active,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(db_trigger)
    db.commit()
    db.refresh(db_trigger)
    
    return EventTriggerResponse.from_orm(db_trigger)

@router.get("/triggers/", response_model=List[EventTriggerResponse])
async def get_event_triggers(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """Get a list of event triggers"""
    # Verify user has permission
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    triggers = db.query(EventTrigger).filter(
        EventTrigger.organization_id == current_user["organization_id"]
    ).offset(skip).limit(limit).all()
    
    return [EventTriggerResponse.from_orm(trigger) for trigger in triggers]

@router.get("/triggers/{trigger_id}", response_model=EventTriggerResponse)
async def get_event_trigger(
    trigger_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific event trigger"""
    # Verify user has permission
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    trigger = db.query(EventTrigger).filter(
        EventTrigger.id == trigger_id,
        EventTrigger.organization_id == current_user["organization_id"]
    ).first()
    
    if not trigger:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event trigger not found"
        )
    
    return EventTriggerResponse.from_orm(trigger)

@router.put("/triggers/{trigger_id}", response_model=EventTriggerResponse)
async def update_event_trigger(
    trigger_id: str,
    trigger_update: EventTriggerUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update an event trigger"""
    # Verify user has permission
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    trigger = db.query(EventTrigger).filter(
        EventTrigger.id == trigger_id,
        EventTrigger.organization_id == current_user["organization_id"]
    ).first()
    
    if not trigger:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event trigger not found"
        )
    
    # Update fields
    for field, value in trigger_update.dict(exclude_unset=True).items():
        setattr(trigger, field, value)
    
    trigger.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(trigger)
    
    return EventTriggerResponse.from_orm(trigger)

@router.delete("/triggers/{trigger_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event_trigger(
    trigger_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete an event trigger"""
    # Verify user has permission
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    trigger = db.query(EventTrigger).filter(
        EventTrigger.id == trigger_id,
        EventTrigger.organization_id == current_user["organization_id"]
    ).first()
    
    if not trigger:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event trigger not found"
        )
    
    db.delete(trigger)
    db.commit()
    
    return None