from sqlalchemy import func
from packages.core.database import get_db
from packages.core.identity.analytics.models import Analytics, LeadMetrics, PipelineMetrics, EngagementMetrics
from packages.core.identity.analytics.schemas import AnalyticsSchema, LeadMetricsSchema, PipelineMetricsSchema, EngagementMetricsSchema
from datetime import datetime, timedelta

class AnalyticsService:
    def __init__(self, db_session):
        self.db = db_session

    def calculate_total_customers(self):
        return self.db.query(func.count(Analytics.organization_id)).scalar()

    def calculate_new_leads(self, period_days=7):
        start_date = datetime.utcnow() - timedelta(days=period_days)
        return self.db.query(Analytics).filter(Analytics.timestamp >= start_date).count()

    def calculate_conversion_rate(self):
        total_leads = self.db.query(LeadMetrics.total_leads).scalar()
        converted_leads = self.db.query(LeadMetrics.qualified_leads).scalar()
        return (converted_leads / total_leads * 100) if total_leads > 0 else 0

    def calculate_repeat_customers(self):
        return self.db.query(func.count(Analytics.organization_id)).filter(Analytics.event_type == 'customer_return').scalar()

    def get_metrics(self):
        return {
            'total_customers': self.calculate_total_customers(),
            'new_leads': self.calculate_new_leads(),
            'conversion_rate': self.calculate_conversion_rate(),
            'repeat_customers': self.calculate_repeat_customers()
        }

class MetricCalculatorService:
    def calculate_lead_metrics(self):
        metrics = LeadMetricsSchema(
            id=1,
            total_leads=LeadMetrics.query.count(),
            qualified_leads=LeadMetrics.query.filter(LeadMetrics.qualified_leads > 0).count(),
            conversion_velocity=LeadMetrics.query.filter(LeadMetrics.conversion_velocity > 0).count()
        )
        return metrics

    def calculate_pipeline_metrics(self):
        metrics = PipelineMetricsSchema(
            id=1,
            lead_to_customer_ratio=PipelineMetrics.query.filter(PipelineMetrics.lead_to_customer_ratio > 0).count(),
            average_lead_age=PipelineMetrics.query(func.avg(PipelineMetrics.lead_age)).scalar() or 0
        )
        return metrics

    def calculate_engagement_metrics(self):
        metrics = EngagementMetricsSchema(
            id=1,
            active_customers=EngagementMetrics.query.filter(EngagementMetrics.active_customers > 0).count(),
            returning_customers=EngagementMetrics.query.filter(EngagementMetrics.returning_customers > 0).count()
        )
        return metrics