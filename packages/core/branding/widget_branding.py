from typing import Dict

class WidgetBrandingService:
    def generate_widget_branding(self, brand_profile: Dict, voice_profile: Dict) -> Dict:
        return {
            'business_name': brand_profile['business_name'],
            'logo_url': brand_profile.get('logo_url', ''),
            'primary_color': brand_profile.get('colors', {}).get('primary', '#3B82F6'),
            'secondary_color': brand_profile.get('colors', {}).get('secondary', '#64748B'),
            'voice_greeting': voice_profile.get('greeting', 'Welcome to [Business Name]. How may we assist you?')
        }