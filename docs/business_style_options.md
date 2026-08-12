"""
Business Style Options

AI-assisted style classification for businesses.
Detects business style and generates appropriate branding.
"""
from typing import Dict, List, Optional
from enum import Enum

class BusinessStyle(str, Enum):
    """Business style classifications"""
    LUXURY_SALON = "luxury_salon"
    MODERN_BARBER = "modern_barber"
    FRIENDLY_BEAUTY_STUDIO = "friendly_beauty_studio"
    PROFESSIONAL_RETAIL = "professional_retail"
    MINIMAL = "minimal"
    CORPORATE = "corporate"
    STARTUP = "startup"
    ARTISAN = "artisan"

class StyleCharacteristics:
    """Characteristics for each business style"""
    
    STYLES = {
        BusinessStyle.LUXURY_SALON: {
            "description": "Elegant, premium, sophisticated",
            "colors": {"primary": "#2C3E50", "secondary": "#E74C3C", "accent": "#F39C12"},
            "tone": "Elegant, warm, premium",
            "personality": "luxurious, attentive, professional"
        },
        BusinessStyle.MODERN_BARBER: {
            "description": "Modern, confident, casual",
            "colors": {"primary": "#1A1A2E", "secondary": "#0F3D3E", "accent": "#F39C12"},
            "tone": "Friendly, confident, casual",
            "personality": "modern, approachable, skilled"
        },
        BusinessStyle.FRIENDLY_BEAUTY_STUDIO: {
            "description": "Warm, welcoming, approachable",
            "colors": {"primary": "#FF6B9D", "secondary": "#FFE5EC", "accent": "#4ECDC4"},
            "tone": "Helpful, informative",
            "personality": "warm, caring, professional"
        },
        BusinessStyle.PROFESSIONAL_RETAIL: {
            "description": "Professional, trustworthy, reliable",
            "colors": {"primary": "#2C3E50", "secondary": "#7F8C8D", "accent": "#3498DB"},
            "tone": "Helpful, informative",
            "personality": "reliable, expert, consistent"
        },
        BusinessStyle.MINIMAL: {
            "description": "Clean, simple, modern",
            "colors": {"primary": "#000000", "secondary": "#FFFFFF", "accent": "#CCCCCC"},
            "tone": "Direct, clear, efficient",
            "personality": "clean, efficient, precise"
        },
        BusinessStyle.CORPORATE: {
            "description": "Professional, established, trustworthy",
            "colors": {"primary": "#003366", "secondary": "#666666", "accent": "#CC0000"},
            "tone": "Professional, authoritative",
            "personality": "established, reliable, formal"
        },
        BusinessStyle.STARTUP: {
            "description": "Innovative, dynamic, creative",
            "colors": {"primary": "#FF6B6B", "secondary": "#4ECDC4", "accent": "#FFE66D"},
            "tone": "Energetic, innovative, friendly",
            "personality": "creative, bold, forward-thinking"
        },
        BusinessStyle.ARTISAN: {
            "description": "Craftsmanship, quality, tradition",
            "colors": {"primary": "#8B4513", "secondary": "#D2B48C", "accent": "#CD5C5C"},
            "tone": "Warm, knowledgeable, traditional",
            "personality": "craftsman, dedicated, quality-focused"
        }
    }

class StyleClassifier:
    """
    AI-assisted style classifier for businesses
    
    Analyzes business information to determine style classification
    """
    
    def __init__(self):
        self.style_patterns = {
            "luxury_salon": ["luxury", "premium", "elegant", "high-end", "exclusive"],
            "modern_barber": ["modern", "casual", "street", "trendy", "hip"],
            "friendly_beauty_studio": ["warm", "friendly", "approachable", "cosy", "relaxing"],
            "professional_retail": ["professional", "reliable", "trusted", "established"],
            "minimal": ["minimal", "clean", "simple", "modern", "sleek"],
            "corporate": ["corporate", "professional", "formal", "business"],
            "startup": ["innovative", "creative", "modern", "tech", "disruptive"],
            "artisan": ["artisan", "craft", "handmade", "traditional", "quality"]
        }
    
    def classify_style(self, business_data: Dict[str, Any]) -> BusinessStyle:
        """
        Classify business style based on business data
        
        Args:
            business_data: Business information (name, industry, description, etc.)
            
        Returns:
            BusinessStyle classification
        """
        # Analyze business name
        business_name = business_data.get('business_name', '').lower()
        
        # Analyze industry
        industry = business_data.get('industry', '').lower()
        
        # Analyze description
        description = business_data.get('description', '').lower()
        
        # Combine all text for analysis
        all_text = f"{business_name} {industry} {description}"
        
        # Score each style
        style_scores = {}
        for style, keywords in self.style_patterns.items():
            score = 0
            for keyword in keywords:
                if keyword in all_text:
                    score += 1
            style_scores[style] = score
        
        # Return style with highest score
        if style_scores:
            best_style = max(style_scores.items(), key=lambda x: x[1])
            if best_style[1] > 0:
                return BusinessStyle(best_style[0])
        
        # Default to professional retail if no clear match
        return BusinessStyle.PROFESSIONAL_RETAIL
    
    def get_style_characteristics(self, style: BusinessStyle) -> Dict[str, Any]:
        """Get characteristics for a specific style"""
        return StyleCharacteristics.STYLES.get(style, {})

# Global style classifier instance
style_classifier = StyleClassifier


def get_style_classifier() -> StyleClassifier:
    """Get or create style classifier instance"""
    return style_classifier()