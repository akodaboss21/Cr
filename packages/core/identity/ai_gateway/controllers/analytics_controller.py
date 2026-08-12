from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from typing import Any, Dict, Optional
from packages.core.database import get_db
from packages.core.security import get_current_user
from packages.core.identity.analytics.services import AnalyticsService, MetricCalculatorService
from packages.core.identity.analytics.schemas import AnalyticsSchema, LeadMetricsSchema, PipelineMetricsSchema, EngagementMetricsSchema

router = APIRouter(prefix="/analytics")


class WidgetAnalyticsPayload(BaseModel):
    event: str
    timestamp: Optional[float] = None
    business_id: Optional[str] = None
    organization_id: Optional[str] = None
    customer_id: Optional[str] = None
    source: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None


@router.post("/widget", status_code=status.HTTP_202_ACCEPTED)
async def ingest_widget_analytics(
    request: Request,
    payload: WidgetAnalyticsPayload,
):
    """Accept lightweight widget analytics beacon events."""
    return {"status": "accepted"}

@router.get("/metrics", response_model=dict)
async def get_analytics_metrics(
    db_session=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    service = AnalyticsService(db_session)
    metrics = service.get_metrics()
    return {
        "total_customers": metrics['total_customers'],
        "new_leads": metrics['new_leads'],
        "conversion_rate": metrics['conversion_rate'],
        "repeat_customers": metrics['repeat_customers']
    }

@router.get("/lead-metrics", response_model=LeadMetricsSchema)
async def get_lead_metrics(db_session=Depends(get_db)):
    service = MetricCalculatorService()
    return service.calculate_lead_metrics()

@router.get("/pipeline-metrics", response_model=PipelineMetricsSchema)
async def get_pipeline_metrics(db_session=Depends(get_db)):
    service = MetricCalculatorService()
    return service.calculate_pipeline_metrics()

@router.get("/engagement-metrics", response_model=EngagementMetricsSchema)
async def get_engagement_metrics(db_session=Depends(get_db)):
    service = MetricCalculatorService()
    return service.calculate_engagement_metrics()