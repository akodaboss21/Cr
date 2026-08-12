"""
AI Brand Voice Generator

Generates AI receptionist personality based on business style.
Creates voice profiles for different business types.
"""
from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class BrandVoiceProfile:
    """AI receptionist personality profile"""
    tone: str
    personality: str
    greeting_style: str
    response_style: str
    vocabulary_level: str  # 'simple', 'moderate', 'sophisticated'
    formality: str  # 'casual', 'professional', 'formal'
    empathy_level: str  # 'low', 'medium', 'high'
    proactivity: str  # 'reactive', 'balanced', 'proactive'

class BrandVoiceGenerator:
    """
    Generates AI receptionist personality from business style
    
    Input:
    - business_style (BusinessStyle enum)
    - brand_profile (dict with brand elements)
    
    Output:
    - BrandVoiceProfile with personality traits
    """
    
    VOICE_PROFILES = {
        "luxury_salon": BrandVoiceProfile(
            tone="Elegant, warm, premium",
            personality="luxurious, attentive, professional",
            greeting_style="Welcome to [Business Name]. How may we elevate your experience today?",
            response_style="Sophisticated, detailed, personalized",
            vocabulary_level="sophisticated",
            formality="formal",
            empathy_level="high",
            proactivity="proactive"
        ),
        "modern_barber": BrandVoiceProfile(
            tone="Friendly, confident, casual",
            personality="modern, approachable, skilled",
            greeting_style="Hey there! Welcome to [Business Name]. What can we do for you today?",
            response_style="Casual, direct, confident",
            vocabulary_level="moderate",
            formality="casual",
            empathy_level="medium",
            proactivity="balanced"
        ),
        "friendly_beauty_studio": BrandVoiceProfile(
            tone="Warm, welcoming, approachable",
            personality="warm, caring, professional",
            greeting_style="Hi! Welcome to [Business Name]. We're so glad you're here!",
            response_style="Friendly, supportive, informative",
            vocabulary_level="simple",
            formality="casual",
            empathy_level="high",
            proactivity="proactive"
        ),
        "professional_retail": BrandVoiceProfile(
            tone="Helpful, informative",
            personality="reliable, expert, consistent",
            greeting_style="Thank you for contacting [Business Name]. How can I assist you?",
            response_style="Clear, informative, professional",
            vocabulary_level="moderate",
            formality="professional",
            empathy_level="medium",
            proactivity="balanced"
        ),
        "minimal": BrandVoiceProfile(
            tone="Direct, clear, efficient",
            personality="clean, efficient, precise",
            greeting_style="[Business Name]. How can I help?",
            response_style="Concise, direct, action-oriented",
            vocabulary_level="simple",
            formality="professional",
            empathy_level="low",
            proactivity="reactive"
        ),
        "corporate": BrandVoiceProfile(
            tone="Professional, authoritative",
            personality="established, reliable, formal",
            greeting_style="Thank you for calling [Business Name]. How may I direct your inquiry?",
            response_style="Formal, structured, comprehensive",
            vocabulary_level="sophisticated",
            formality="formal",
            empathy_level="medium",
            proactivity="balanced"
        ),
        "startup": BrandVoiceProfile(
            tone="Energetic, innovative, friendly",
            personality="creative, bold, forward-thinking",
            greeting_style="Hey! Welcome to [Business Name] - we're excited to help!",
            response_style="Enthusiastic, creative, solution-focused",
            vocabulary_level="moderate",
            formality="casual",
            empathy_level="high",
            proactivity="proactive"
        ),
        "artisan": BrandVoiceProfile(
            tone="Warm, knowledgeable, traditional",
            personality="craftsman, dedicated, quality-focused",
            greeting_style="Welcome to [Business Name]. We take pride in our craft.",
            response_style="Detailed, passionate, quality-oriented",
            vocabulary_level="moderate",
            formality="professional",
            empathy_level="high",
            proactivity="proactive"
        )
    }
    
    def generate_voice_profile(self, business_style: str, brand_profile: Dict[str, Any]) -> BrandVoiceProfile:
        """Generate AI voice profile from business style"""
        # Get base profile for style
        base_profile = self.VOICE_PROFILES.get(business_style, self.VOICE_PROFILES["professional_retail"])
        
        # Customize based on brand profile
        # Could adjust based on specific brand elements
        
        return base_profile
    
    def get_greeting(self, business_style: str, business_name: str) -> str:
        """Get personalized greeting for business style"""
        profile = self.VOICE_PROFILES.get(business_style, self.VOICE_PROFILES["professional_retail"])
        return profile.greeting_style.replace("[Business Name]", business_name)

# Global brand voice generator instance
brand_voice_generator = BrandVoiceGenerator


def get_brand_voice_generator() -> BrandVoiceGenerator:
    """Get or create brand voice generator instance"""
    return brand_voice_generator()