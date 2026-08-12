"""
Theme Engine

Creates dynamic UI themes based on brand profiles.
Generates CSS variables, Tailwind configurations, and theme objects.
"""
from typing import Dict, Any
from dataclasses import dataclass
import json

@dataclass
class ThemeSettings:
    """Theme configuration object"""
    brand_name: str
    logo_url: str
    colors: Dict[str, str]
    fonts: Dict[str, str]
    radius: str
    style: str  # 'light', 'dark', 'modern', etc.

class ThemeEngine:
    """
    Service for generating UI themes from brand profiles
    
    Input:
    - brand_profile (dict with brand elements)
    
    Output:
    - theme_settings (ThemeSettings object)
    - css_variables (dict for CSS)
    - tailwind_config (dict for Tailwind)
    """
    
    def generate_theme(self, brand_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Generate theme settings from brand profile"""
        # Extract colors from brand profile
        colors = brand_profile.get('colors', {})
        if not colors:
            # Use default colors if none provided
            colors = {
                'primary': '#3B82F6',
                'secondary': '#64748B',
                'accent': '#F59E0B',
                'background': '#FFFFFF',
                'text': '#1F2937'
            }
        
        # Create theme settings
        theme_settings = ThemeSettings(
            brand_name=brand_profile.get('business_name', 'Carai'),
            logo_url=brand_profile.get('logo_url', ''),
            colors=colors,
            fonts={'body': 'System Sans', 'heading': 'System Sans Bold'},
            radius='md',
            style='modern'
        )
        
        # Generate CSS variables
        css_variables = {
            '--brand-primary': colors['primary'],
            '--brand-secondary': colors['secondary'],
            '--brand-accent': colors['accent'],
            '--background': colors['background'],
            '--text': colors['text']
        }
        
        # Generate Tailwind config
        tailwind_config = {
            'theme': {
                'extend': {
                    'colors': colors,
                    'spacing': [2, 4, 6, 8, 10, 12, 16, 20, 24, 32, 40, 48, 56, 64]
                }
            }
        }
        
        return {
            'theme_settings': theme_settings,
            'css_variables': css_variables,
            'tailwind_config': tailwind_config
        }
    
# Global theme engine instance
theme_engine = ThemeEngine


def get_theme_engine() -> ThemeEngine:
    """Get or create theme engine instance"""
    return theme_engine()