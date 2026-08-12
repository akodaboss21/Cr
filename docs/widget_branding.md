"""
Widget Branding System

The customer-facing widget inherits business branding including:
- Business logo
- Colors
- Greeting
- AI personality
"""
from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class WidgetBranding:
    """Widget branding configuration"""
    logo_url: str
    primary_color: str
    secondary_color: str
    accent_color: str
    background_color: str
    text_color: str
    greeting: str
    ai_personality: str
    business_name: str

class WidgetBrandingService:
    """
    Service for generating widget branding from brand profile
    
    Input:
    - brand_profile (dict with brand elements)
    - voice_profile (BrandVoiceProfile)
    
    Output:
    - WidgetBranding configuration
    """
    
    def generate_widget_branding(self, brand_profile: Dict[str, Any], voice_profile: Dict[str, Any]) -> WidgetBranding:
        """Generate widget branding configuration"""
        colors = brand_profile.get('colors', {})
        
        return WidgetBranding(
            logo_url=brand_profile.get('logo_url', ''),
            primary_color=colors.get('primary', '#3B82F6'),
            secondary_color=colors.get('secondary', '#64748B'),
            accent_color=colors.get('accent', '#F59E0B'),
            background_color=colors.get('background', '#FFFFFF'),
            text_color=colors.get('text', '#1F2937'),
            greeting=voice_profile.get('greeting', 'Welcome! How can I help you today?'),
            ai_personality=voice_profile.get('personality', 'helpful, informative'),
            business_name=brand_profile.get('business_name', 'Carai')
        )
    
    def get_widget_css_variables(self, branding: WidgetBranding) -> Dict[str, str]:
        """Generate CSS variables for widget"""
        return {
            '--widget-primary': branding.primary_color,
            '--widget-secondary': branding.secondary_color,
            '--widget-accent': branding.accent_color,
            '--widget-background': branding.background_color,
            '--widget-text': branding.text_color,
            '--widget-logo': f"url('{branding.logo_url}')" if branding.logo_url else 'none'
        }
    
    def get_widget_config(self, branding: WidgetBranding) -> Dict[str, Any]:
        """Generate widget configuration object"""
        return {
            'branding': {
                'logo': branding.logo_url,
                'colors': {
                    'primary': branding.primary_color,
                    'secondary': branding.secondary_color,
                    'accent': branding.accent_color,
                    'background': branding.background_color,
                    'text': branding.text_color
                },
                'greeting': branding.greeting,
                'personality': branding.ai_personality,
                'businessName': branding.business_name
            },
            'theme': 'auto',  # 'light', 'dark', 'auto'
            'position': 'bottom-right',
            'language': 'en'
        }

# Global widget branding service instance
widget_branding_service = WidgetBrandingService


def get_widget_branding_service() -> WidgetBrandingService:
    """Get or create widget branding service instance"""
    return widget_branding_service()