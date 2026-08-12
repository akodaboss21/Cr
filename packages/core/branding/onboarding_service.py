"""
Onboarding Flow Service

Handles the multi-step onboarding process for businesses.
"""
from typing import Dict, Any, Optional
from datetime import datetime
from uuid import uuid4


class OnboardingService:
    """
    Service for managing business onboarding flow
    
    Steps:
    1. Business information
    2. Website URL
    3. Logo upload
    4. Automatic analysis
    5. Review extracted information
    6. Approve AI setup
    7. Activate receptionist
    """
    
    def __init__(self, db):
        self.db = db
        self.business_identity_service = None
        self.website_scraper = None
        self.color_extractor = None
        self.theme_engine = None
        self.style_classifier = None
        self.brand_voice_generator = None
        self.knowledge_generator = None
        self._store = getattr(db, "data", None)
        
    def initialize_services(self):
        """Initialize all required services"""
        from .business_identity_service import get_business_identity_service
        from .website_scraper import get_website_scraper
        from .color_extractor import get_color_extractor
        from .theme_engine import get_theme_engine
        from .business_style_options import get_style_classifier
        from .ai_brand_voice import get_brand_voice_generator
        from .knowledge_generation import get_knowledge_generator
        
        self.business_identity_service = get_business_identity_service(self.db)
        self.website_scraper = get_website_scraper(self.db)
        self.color_extractor = get_color_extractor()
        self.theme_engine = get_theme_engine()
        self.style_classifier = get_style_classifier()
        self.brand_voice_generator = get_brand_voice_generator()
        self.knowledge_generator = get_knowledge_generator(self.db)
    
    def start_onboarding(self, organization_id: str) -> Dict[str, Any]:
        """Start a new onboarding process"""
        onboarding_id = str(uuid4())
        onboarding_record = {
            'id': onboarding_id,
            'organization_id': organization_id,
            'current_step': 1,
            'status': 'in_progress',
            'started_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
            'data': {}
        }
        
        self._save_onboarding(onboarding_record)
        
        return onboarding_record
    
    def submit_step(self, onboarding_id: str, step: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Submit data for a specific onboarding step"""
        # Retrieve onboarding record
        onboarding = self._get_onboarding(onboarding_id)
        if not onboarding:
            raise ValueError("Onboarding not found")
        
        # Update data for this step
        onboarding['data'][f'step_{step}'] = data
        onboarding['current_step'] = step + 1
        onboarding['updated_at'] = datetime.utcnow().isoformat()
        
        # If step is complete, move to next
        if step == 7:
            onboarding['status'] = 'completed'
            onboarding['completed_at'] = datetime.utcnow().isoformat()
        
        self._save_onboarding(onboarding)
        
        return onboarding
    
    def process_website_analysis(self, onboarding_id: str) -> Dict[str, Any]:
        """Process website analysis step (step 4)"""
        onboarding = self._get_onboarding(onboarding_id)
        if not onboarding:
            raise ValueError("Onboarding not found")
        
        # Get website URL from step 2
        website_url = onboarding['data'].get('step_2', {}).get('website_url')
        if not website_url:
            raise ValueError("Website URL not provided")
        
        # Scrape website
        scraped_data = self.website_scraper.scrape_website(website_url, onboarding['organization_id'])
        
        # Extract colors
        colors = self.color_extractor.extract_from_css(scraped_data.get('css', ''))
        if not colors:
            colors = self.color_extractor.extract_from_logo(scraped_data.get('logo_url', ''))
        
        # Update onboarding data
        onboarding['data']['step_4'] = {
            'scraped_data': scraped_data,
            'extracted_colors': colors
        }
        onboarding['updated_at'] = datetime.utcnow().isoformat()
        
        self._save_onboarding(onboarding)
        
        return onboarding['data']['step_4']
    
    def generate_brand_profile(self, onboarding_id: str) -> Dict[str, Any]:
        """Generate brand profile from onboarding data"""
        onboarding = self._get_onboarding(onboarding_id)
        if not onboarding:
            raise ValueError("Onboarding not found")
        
        # Get business info from step 1
        business_data = onboarding['data'].get('step_1', {})
        website_data = onboarding['data'].get('step_2', {})
        
        # Combine data
        combined_data = {
            'business_name': business_data.get('business_name'),
            'industry': business_data.get('industry'),
            'website_url': website_data.get('website_url'),
            'logo_url': business_data.get('logo_url', website_data.get('logo_url', '')),
            'description': business_data.get('description', '')
        }
        
        # Create brand profile
        brand_profile = self.business_identity_service.create_brand_profile(combined_data)
        
        # Store in onboarding data
        onboarding['data']['step_5'] = {
            'brand_profile': brand_profile
        }
        onboarding['updated_at'] = datetime.utcnow().isoformat()
        
        self._save_onboarding(onboarding)
        
        return brand_profile
    
    def complete_onboarding(self, onboarding_id: str) -> Dict[str, Any]:
        """Complete the onboarding process and activate receptionist"""
        onboarding = self._get_onboarding(onboarding_id)
        if not onboarding:
            raise ValueError("Onboarding not found")
        
        # Generate brand profile if not done
        if 'step_5' not in onboarding['data']:
            self.generate_brand_profile(onboarding_id)
        
        # Get brand profile
        brand_profile = onboarding['data']['step_5']['brand_profile']
        
        # Generate theme
        theme = self.theme_engine.generate_theme(brand_profile)
        
        # Classify business style
        style = self.style_classifier.classify_style(brand_profile)
        
        # Generate AI brand voice
        voice_profile = self.brand_voice_generator.generate_voice_profile(style.value, brand_profile)
        
        # Generate knowledge base
        scraped_data = onboarding['data'].get('step_4', {}).get('scraped_data', {})
        knowledge_base = self.knowledge_generator.generate_knowledge(scraped_data, brand_profile)
        
        # Update onboarding data
        onboarding['data']['step_6'] = {
            'theme': theme,
            'style': style.value,
            'voice_profile': voice_profile,
            'knowledge_base': knowledge_base
        }
        onboarding['status'] = 'completed'
        onboarding['completed_at'] = datetime.utcnow().isoformat()
        onboarding['updated_at'] = datetime.utcnow().isoformat()
        
        self._save_onboarding(onboarding)
        
        # Enqueue activation job for background processing
        self._activate_receptionist_async(
            onboarding['organization_id'], 
            brand_profile, 
            theme, 
            voice_profile, 
            knowledge_base
        )
        
        return {
            'onboarding_id': onboarding_id,
            'organization_id': onboarding['organization_id'],
            'brand_profile': brand_profile,
            'theme': theme,
            'style': style.value,
            'voice_profile': voice_profile,
            'knowledge_base': knowledge_base
        }
    
    def _get_onboarding(self, onboarding_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve onboarding record from database"""
        if not self._store:
            return None

        records = self.db.query("onboardings", id=onboarding_id)
        if records:
            return records[0]
        return None
    
    def _save_onboarding(self, onboarding: Dict[str, Any]):
        """Save onboarding record to database"""
        existing = self.db.query("onboardings", id=onboarding["id"])
        if existing:
            self.db.data["onboardings"] = [
                record if record.get("id") != onboarding["id"] else onboarding
                for record in self.db.data.get("onboardings", [])
            ]
        else:
            self.db.save("onboardings", onboarding)
    
    def _activate_receptionist(self, organization_id: str, brand_profile: Dict, theme: Dict, 
                              voice_profile: Dict, knowledge_base: Dict):
        """Activate the AI receptionist for the business (synchronous wrapper)"""
        # This is kept for compatibility but delegates to async version
        self._activate_receptionist_async(
            organization_id, brand_profile, theme, voice_profile, knowledge_base
        )
    
    def _activate_receptionist_async(self, organization_id: str, brand_profile: Dict, theme: Dict,
                                     voice_profile: Dict, knowledge_base: Dict):
        """
        Enqueue background job for AI receptionist activation
        
        Creates a background job that will:
        1. Generate embeddings for knowledge base
        2. Build agent configuration
        3. Mark organization as active
        
        Args:
            organization_id: Organization ID
            brand_profile: Brand profile data
            theme: Generated theme
            voice_profile: AI voice profile
            knowledge_base: Generated knowledge base
        """
        try:
            from packages.core.identity.background_workers.job_manager import JobManager
            from packages.core.database import SessionLocal
            
            # Get a database session for job enqueueing
            db = SessionLocal()
            
            try:
                job_manager = JobManager(db)
                
                # Enqueue the onboarding activation job
                job_id = job_manager.enqueue(
                    organization_id=organization_id,
                    task_type=JobManager.TASK_ONBOARDING_ACTIVATE,
                    task_data={
                        "brand_profile": brand_profile,
                        "theme": theme,
                        "voice_profile": voice_profile,
                        "knowledge_base": knowledge_base
                    },
                    max_retries=3
                )
                
                print(f"[INFO] Onboarding activation job enqueued: {job_id} for org {organization_id}")
            
            finally:
                db.close()
        
        except Exception as e:
            print(f"[ERROR] Failed to enqueue activation job: {str(e)}")

# Global onboarding service instance
onboarding_service = OnboardingService


def get_onboarding_service(db) -> OnboardingService:
    """Get or create onboarding service instance"""
    return onboarding_service(db)