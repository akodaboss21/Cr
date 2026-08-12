"""
Notification Module - Controller
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import datetime

from packages.core.database import get_db
from packages.core.security import get_current_user
from packages.core.identity.notification.models import Notification, NotificationSetting
from packages.core.identity.notification.schemas import (
    NotificationCreate,
    NotificationUpdate,
    NotificationResponse,
    NotificationDispatchRequest,
    NotificationDispatchResponse,
    NotificationSettingCreate,
    NotificationSettingUpdate,
    NotificationSettingResponse,
)
from packages.core.identity.notification.services import NotificationService

router = APIRouter(tags=["notifications"])

@router.post("/", response_model=NotificationResponse)
async def create_notification(
    notification_create: NotificationCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new notification"""
    # Verify user has permission to create notification
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    # Create notification
    db_notification = Notification(
        id=str(uuid4()),
        organization_id=current_user["organization_id"],
        business_id=notification_create.business_id,
        recipient_id=notification_create.recipient_id,
        title=notification_create.title,
        message=notification_create.message,
        type=notification_create.type,
        recipient=notification_create.recipient,
        data=notification_create.data,
        status=notification_create.status,
        sent_at=notification_create.sent_at,
        delivered_at=notification_create.delivered_at,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    
    return NotificationResponse.from_orm(db_notification)

@router.post("/dispatch/", response_model=NotificationDispatchResponse)
async def dispatch_notification(
    dispatch_request: NotificationDispatchRequest,
    current_user: dict = Depends(get_current_user)
):
    """Dispatch a notification event through configured providers."""
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    results = NotificationService.send_event_notification(
        event_type=dispatch_request.event_type,
        recipient=dispatch_request.recipient,
        payload=dispatch_request.payload,
        channels=dispatch_request.channels,
    )

    return NotificationDispatchResponse(results=[
        {
            "channel": result.get("channel"),
            "recipient": result.get("recipient"),
            "status": result.get("status", "failed"),
            "details": result.get("details", result),
        }
        for result in results
    ])

@router.post("/settings/", response_model=NotificationSettingResponse)
async def create_notification_setting(
    setting_create: NotificationSettingCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    db_setting = NotificationSetting(
        id=str(uuid4()),
        organization_id=current_user["organization_id"],
        business_id=setting_create.business_id,
        event_type=setting_create.event_type,
        enabled=setting_create.enabled,
        channels=setting_create.channels,
        schedule=setting_create.schedule,
        timezone=setting_create.timezone,
        data=setting_create.data,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    db.add(db_setting)
    db.commit()
    db.refresh(db_setting)
    return NotificationSettingResponse.from_orm(db_setting)

@router.get("/settings/", response_model=List[NotificationSettingResponse])
async def get_notification_settings(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    settings_query = db.query(NotificationSetting).filter(
        NotificationSetting.organization_id == current_user["organization_id"]
    ).offset(skip).limit(limit).all()

    return [NotificationSettingResponse.from_orm(setting) for setting in settings_query]

@router.get("/settings/{setting_id}", response_model=NotificationSettingResponse)
async def get_notification_setting(
    setting_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    setting = db.query(NotificationSetting).filter(
        NotificationSetting.id == setting_id,
        NotificationSetting.organization_id == current_user["organization_id"]
    ).first()

    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification setting not found"
        )

    return NotificationSettingResponse.from_orm(setting)

@router.put("/settings/{setting_id}", response_model=NotificationSettingResponse)
async def update_notification_setting(
    setting_id: str,
    setting_update: NotificationSettingUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    setting = db.query(NotificationSetting).filter(
        NotificationSetting.id == setting_id,
        NotificationSetting.organization_id == current_user["organization_id"]
    ).first()

    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification setting not found"
        )

    for field, value in setting_update.dict(exclude_unset=True).items():
        setattr(setting, field, value)

    setting.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(setting)

    return NotificationSettingResponse.from_orm(setting)

@router.delete("/settings/{setting_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification_setting(
    setting_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    setting = db.query(NotificationSetting).filter(
        NotificationSetting.id == setting_id,
        NotificationSetting.organization_id == current_user["organization_id"]
    ).first()

    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification setting not found"
        )

    db.delete(setting)
    db.commit()

    return None

@router.get("/", response_model=List[NotificationResponse])
async def get_notifications(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """Get a list of notifications"""
    # Verify user has permission
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    notifications = db.query(Notification).filter(
        Notification.organization_id == current_user["organization_id"]
    ).offset(skip).limit(limit).all()
    
    return [NotificationResponse.from_orm(n) for n in notifications]

@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific notification"""
    # Verify user has permission
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.organization_id == current_user["organization_id"]
    ).first()
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    return NotificationResponse.from_orm(notification)

@router.put("/{notification_id}", response_model=NotificationResponse)
async def update_notification(
    notification_id: str,
    notification_update: NotificationUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a notification"""
    # Verify user has permission
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.organization_id == current_user["organization_id"]
    ).first()
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    # Update fields
    for field, value in notification_update.dict(exclude_unset=True).items():
        setattr(notification, field, value)
    
    notification.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(notification)
    
    return NotificationResponse.from_orm(notification)

@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a notification"""
    # Verify user has permission
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.organization_id == current_user["organization_id"]
    ).first()
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    db.delete(notification)
    db.commit()
    
    return None