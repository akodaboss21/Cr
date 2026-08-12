from typing import List, Dict, Any
import pytest
from uuid import uuid4
from datetime import datetime

# Mock database session
class MockDB:
    def __init__(self):
        self.data: Dict[str, Any] = {}
    
    def save(self, collection: str, record: Dict[str, Any]):
        if collection not in self.data:
            self.data[collection] = []
        self.data[collection].append(record)
    
    def query(self, collection: str, **filters):
        results = self.data.get(collection, [])
        for filter_key, filter_value in filters.items():
            results = [r for r in results if r.get(filter_key) == filter_value]
        return results

# Mock services
class MockBusinessIdentityService:
    def __init__(self, db):
        self.db = db
    
    def create_brand_profile(self, business_data: Dict[str, Any]) -> Dict[str, Any]:
        profile_id = str(uuid4())
        profile = {
            'id': profile_id,
            'business_name': business_data['business_name'],
            'industry': business_data['industry'],
            'website_url': business_data['website_url'],
            'logo_url': business_data.get('logo_url', '')
        }
        self.db.save('brand_profiles', profile)
        return profile

class MockWebsiteScraper:
    async def scrape_website(self, url: str) -> Dict[str, Any]:
        return {
            'business_name': 'Test Business',
            'logo_url': 'https://example.com/logo.png',
            'brand_colors': {'primary': '#3B82F6', 'secondary': '#64748B'},
            'contact_info': {'phone': '123-456-7890', 'email': 'info@example.com'},
            'opening_hours': {'mon': '9:00-18:00', 'tue': '9:00-18:00'},
            'services': ['Service 1', 'Service 2'],
            'faq': [{'question': 'What are your hours?', 'answer': '9:00-18:00'}]
        }

class MockColorExtractor:
    def extract_from_css(self, css_content: str) -> Dict[str, str]:
        return {'primary': '#3B82F6', 'secondary': '#64748B', 'accent': '#F59E0B'}
    
    def extract_from_image(self, image_url: str) -> Dict[str, str]:
        return {'primary': '#3B82F6', 'secondary': '#64748B', 'accent': '#F59E0B'}

class MockThemeEngine:
    def generate_theme(self, brand_profile: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'theme_settings': {'colors': {'primary': '#3B82F6'}},
            'css_variables': {'--brand-primary': '#3B82F6'},
            'tailwind_config': {'theme': {'extend': {'colors': {'primary': '#3B82F6'}}}}}

class MockStyleClassifier:
    def classify_style(self, business_data: Dict[str, Any]) -> str:
        return 'luxury_salon'
    
    def get_style_characteristics(self, style: str) -> Dict[str, Any]:
        return {
            'description': 'Elegant, premium, sophisticated',
            'colors': {'primary': '#2C3E50', 'secondary': '#E74C3C', 'accent': '#F39C12'},
            'tone': 'Elegant, warm, premium',
            'personality': 'luxurious, attentive, professional'
        }

class MockBrandVoiceGenerator:
    def generate_voice_profile(self, business_style: str, brand_profile: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'tone': 'Elegant, warm, premium',
            'personality': 'luxurious, attentive, professional',
            'greeting_style': 'Welcome to [Business Name]. How may we elevate your experience today?'
        }

class MockKnowledgeGenerator:
    def generate_knowledge(self, scraped_data: Dict[str, Any], business_profile: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'faqs': [{'question': 'What are your hours?', 'answer': '9:00-18:00'}]
        }

# Test Cases
@pytest.fixture
async def mock_db():
    return MockDB()

@pytest.fixture
async def mock_services(mock_db):
    from packages.core.branding.business_identity_service import get_business_identity_service
    from packages.core.branding.website_scraper import get_website_scraper
    from packages.core.branding.color_extractor import get_color_extractor
    from packages.core.branding.theme_engine import get_theme_engine
    from packages.core.branding.business_style_options import get_style_classifier
    from packages.core.branding.ai_brand_voice import get_brand_voice_generator
    from packages.core.branding.knowledge_generation import get_knowledge_generator
    
    return {
        'business_identity': get_business_identity_service(mock_db),
        'website_scraper': get_website_scraper(mock_db),
        'color_extractor': get_color_extractor(),
        'theme_engine': get_theme_engine(),
        'style_classifier': get_style_classifier(),
        'brand_voice_generator': get_brand_voice_generator(),
        'knowledge_generator': get_knowledge_generator(mock_db)
    }

async def test_website_scraper_output(mock_services):
    """Test website scraper output structure"""
    scraper = mock_services['website_scraper']
    extracted = await scraper.scrape_website('https://example.com')
    
    assert 'business_name' in extracted
    assert 'logo_url' in extracted
    assert 'brand_colors' in extracted
    assert 'services' in extracted
    assert 'faq' in extracted

async def test_widget_branding_generation(mock_services):
    """Test widget branding generation"""
    from packages.core.branding.widget_branding import WidgetBrandingService
    
    service = WidgetBrandingService()
    brand_profile = {
        'business_name': 'Test Salon',
        'logo_url': 'https://example.com/logo.png',
        'colors': {'primary': '#3B82F6', 'secondary': '#64748B'}
    }
    voice_profile = {
        'greeting': 'Welcome to Test Salon!'
    }
    
    branding = service.generate_widget_branding(brand_profile, voice_profile)
    
    assert branding.business_name == 'Test Salon'
    assert branding.logo_url == 'https://example.com/logo.png'
    assert branding.primary_color == '#3B82F6'

# Run all tests
if __name__ == '__main__':
    pytest.main(['-v'])