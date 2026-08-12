"""
Knowledge Generation Service

Generates draft knowledge from website scraping.
Creates FAQs, services, policies, and opening hours.
"""
from typing import Dict, List, Any
from datetime import datetime
from uuid import uuid4

class KnowledgeGenerator:
    """
    Generates knowledge base content from scraped website data
    
    Input:
    - scraped_data (dict from website scraper)
    - business_profile (dict with business information)
    
    Output:
    - knowledge_base (dict with generated content)
    - requires_approval (bool - whether human approval needed)
    """
    
    def __init__(self, db):
        self.db = db
        
    def generate_knowledge(self, scraped_data: Dict[str, Any], business_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Generate knowledge base content from scraped data"""
        knowledge_base = {
            'id': str(uuid4()),
            'organization_id': business_profile.get('organization_id'),
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
            'status': 'draft',
            'content': {}
        }
        
        # Generate FAQs
        knowledge_base['content']['faqs'] = self._generate_faqs(scraped_data)
        
        # Generate services
        knowledge_base['content']['services'] = self._generate_services(scraped_data)
        
        # Generate policies
        knowledge_base['content']['policies'] = self._generate_policies(scraped_data)
        
        # Generate opening hours
        knowledge_base['content']['opening_hours'] = self._generate_opening_hours(scraped_data)
        
        # Store in database
        # self._save_knowledge(knowledge_base)
        
        return knowledge_base
    
    def _generate_faqs(self, scraped_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate FAQs from scraped data"""
        faqs = []
        
        # Extract from FAQ section if available
        if 'faq' in scraped_data:
            for item in scraped_data['faq']:
                faqs.append({
                    'question': item.get('question', ''),
                    'answer': item.get('answer', ''),
                    'category': 'general'
                })
        
        # Generate common FAQs if none found
        if not faqs:
            faqs = [
                {
                    'question': 'What are your business hours?',
                    'answer': 'Our business hours are [extracted from website].',
                    'category': 'hours'
                },
                {
                    'question': 'How can I contact you?',
                    'answer': 'You can contact us at [extracted contact information].',
                    'category': 'contact'
                },
                {
                    'question': 'What services do you offer?',
                    'answer': 'We offer [extracted services].',
                    'category': 'services'
                }
            ]
        
        return faqs
    
    def _generate_services(self, scraped_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate services list from scraped data"""
        services = []
        
        if 'services' in scraped_data:
            for service in scraped_data['services']:
                services.append({
                    'name': service,
                    'description': f'Professional {service.lower()} service',
                    'duration': 'Varies',
                    'price': 'Contact for pricing'
                })
        
        return services
    
    def _generate_policies(self, scraped_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate policies from scraped data"""
        policies = []
        
        if 'about' in scraped_data:
            policies.append({
                'name': 'About Us',
                'content': scraped_data['about'],
                'category': 'company'
            })
        
        # Add common policies
        policies.extend([
            {
                'name': 'Cancellation Policy',
                'content': 'Please call us at least 24 hours in advance to cancel or reschedule.',
                'category': 'policy'
            },
            {
                'name': 'Payment Policy',
                'content': 'We accept cash, credit cards, and electronic payments.',
                'category': 'policy'
            }
        ])
        
        return policies
    
    def _generate_opening_hours(self, scraped_data: Dict[str, Any]) -> Dict[str, str]:
        """Generate opening hours from scraped data"""
        if 'opening_hours' in scraped_data:
            return scraped_data['opening_hours']
        
        # Default opening hours
        return {
            'monday': '9:00 AM - 6:00 PM',
            'tuesday': '9:00 AM - 6:00 PM',
            'wednesday': '9:00 AM - 6:00 PM',
            'thursday': '9:00 AM - 6:00 PM',
            'friday': '9:00 AM - 6:00 PM',
            'saturday': '10:00 AM - 4:00 PM',
            'sunday': 'Closed'
        }

# Global knowledge generator instance
knowledge_generator = KnowledgeGenerator


def get_knowledge_generator(db) -> KnowledgeGenerator:
    """Get or create knowledge generator instance"""
    return knowledge_generator(db)