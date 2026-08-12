from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from packages.core.database import get_db
from packages.core.identity.onboarding.models import OnboardingRecord
from packages.core.identity.onboarding.schemas import OnboardingCreate, OnboardingRecordSchema
from packages.core.identity.business.schemas import BusinessProfileCreate
from packages.core.config import settings
from packages.core.security import get_current_user
from datetime import datetime
import json

router = APIRouter(prefix="/onboarding", tags=["onboarding"])

@router.post("/start", response_model=OnboardingRecordSchema)
async def start_onboarding(
    payload: OnboardingCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    if payload.organization_id and payload.organization_id != current_user["organization_id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization mismatch"
        )

    record = OnboardingRecord(
        organization_id=current_user["organization_id"],
        current_step='1',
        status='in_progress',
        data=json.dumps({}),
        started_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.put("/{onboarding_id}/step/{step}", response_model=OnboardingRecordSchema)
async def submit_step(
    onboarding_id: str,
    step: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    body = await request.json()
    record = db.query(OnboardingRecord).filter(
        OnboardingRecord.id == onboarding_id,
        OnboardingRecord.organization_id == current_user["organization_id"]
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Onboarding not found")

    data = json.loads(record.data or "{}")
    data[f"step_{step}"] = body
    record.data = json.dumps(data)
    record.current_step = str(step + 1)
    record.updated_at = datetime.utcnow()

    if step >= 6:
        record.status = 'completed'

    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/{onboarding_id}", response_model=OnboardingRecordSchema)
async def get_onboarding(
    onboarding_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    record = db.query(OnboardingRecord).filter(
        OnboardingRecord.id == onboarding_id,
        OnboardingRecord.organization_id == current_user["organization_id"]
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Onboarding not found")
    return record


@router.post("/{onboarding_id}/activate", response_model=dict)
async def activate_onboarding(
    onboarding_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    record = db.query(OnboardingRecord).filter(
        OnboardingRecord.id == onboarding_id,
        OnboardingRecord.organization_id == current_user["organization_id"]
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Onboarding not found")

    data = json.loads(record.data or "{}")
    # Basic activation steps: create business profile, create knowledge entries, generate embeddings, mark active
    step1 = data.get('step_1', {})
    step2 = data.get('step_2', {})
    step3 = data.get('step_3', {})
    step5 = data.get('step_5', {})

    # Create business profile
    try:
        bp_payload = {
            'business_name': step1.get('businessName') or step1.get('business_name'),
            'website': step2.get('website') or step2.get('website_url'),
            'address': step3.get('address'),
            'phone': step3.get('phone'),
            'email': step1.get('email')
        }
        # Use BusinessProfile schema for validation
        BusinessProfileCreate(**bp_payload)

        from packages.core.identity.business.models import BusinessProfile
        from packages.core.identity.business.schemas import BusinessProfileCreate as BPCreate

        bp = BusinessProfile(
            id=str(__import__('uuid').uuid4()),
            organization_id=record.organization_id,
            owner_id='',
            business_name=bp_payload['business_name'],
            website=bp_payload.get('website'),
            address=bp_payload.get('address'),
            phone=bp_payload.get('phone'),
            email=bp_payload.get('email'),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(bp)
        db.commit()
        db.refresh(bp)

    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to create business profile: {exc}")

    # Create knowledge entries
    try:
        from packages.core.identity.knowledge.models import Knowledge
        knowledge_text = step5.get('faqs') or step5.get('faqs_text') or ''
        if knowledge_text:
            k = Knowledge(
                id=str(__import__('uuid').uuid4()),
                organization_id=record.organization_id,
                title=f"Imported FAQs for {bp.business_name}",
                content=knowledge_text,
                content_type='text',
                processed=False,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(k)
            db.commit()
            db.refresh(k)

            # Generate embeddings via gateway
            from packages.core.ai.gateway import LLMGateway
            gateway = LLMGateway()
            try:
                embed_resp = await gateway.embed(texts=[knowledge_text], organization_id=record.organization_id)
                if getattr(embed_resp, 'embeddings', None):
                    k.embedding_vector = json.dumps(embed_resp.embeddings[0])
                    k.processed = True
                    db.add(k)
                    db.commit()
            except Exception:
                # Continue even if embedding fails
                pass
    except Exception:
        pass

    # Mark onboarding record as activated and return widget embed
    record.status = 'activated'
    record.updated_at = datetime.utcnow()
    db.add(record)
    db.commit()
    db.refresh(record)

    # Create widget embed code
    widget_code = f"<script src=\"/widget.js\" data-business-id=\"{bp.id}\"></script>"

    return {
        'status': 'activated',
        'business_id': bp.id,
        'widget_code': widget_code
    }
