"""
Brand Color Extraction Service

Extracts brand colors from website CSS, images, and logos.
Generates a complete brand palette.
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
import colorsys

@dataclass
class BrandPalette:
    """Complete brand color palette"""
    primary: str
    secondary: str
    accent: str
    background: str
    text: str
    success: str = "#10B981"
    warning: str = "#F59E0B"
    error: str = "#EF4444"

class ColorExtractor:
    """
    Service for extracting brand colors from various sources
    
    Sources:
    - Website CSS
    - Images
    - Logo
    
    Output:
    - Primary color
    - Secondary color
    - Accent color
    - Background color
    - Text color
    """
    
    def __init__(self):
        self.color_cache = {}
    
    def extract_from_css(self, css_content: str) -> Dict[str, str]:
        """Extract colors from CSS content"""
        # Implementation would parse CSS for color values
        # Look for: color, background-color, border-color, etc.
        return {}
    
    def extract_from_image(self, image_url: str) -> Dict[str, str]:
        """Extract dominant colors from an image"""
        # Implementation would use PIL or similar to analyze image
        return {}
    
    def extract_from_logo(self, logo_url: str) -> Dict[str, str]:
        """Extract colors from logo image"""
        return self.extract_from_image(logo_url)
    
    def generate_palette(self, colors: List[str]) -> BrandPalette:
        """Generate a harmonious brand palette from extracted colors"""
        if not colors:
            # Default palette
            return BrandPalette(
                primary="#3B82F6",
                secondary="#64748B",
                accent="#F59E0B",
                background="#FFFFFF",
                text="#1F2937"
            )
        
        # Use first color as primary
        primary = colors[0]
        
        # Generate complementary colors
        secondary = self._adjust_hue(primary, 180)  # Complementary
        accent = self._adjust_hue(primary, 60)      # Triadic
        
        # Determine background and text based on primary lightness
        lightness = self._get_lightness(primary)
        if lightness > 0.5:
            background = "#FFFFFF"
            text = "#1F2937"
        else:
            background = "#1F2937"
            text = "#FFFFFF"
        
        return BrandPalette(
            primary=primary,
            secondary=secondary,
            accent=accent,
            background=background,
            text=text
        )
    
    def _adjust_hue(self, hex_color: str, degrees: int) -> str:
        """Adjust hue of a color by degrees"""
        rgb = self._hex_to_rgb(hex_color)
        h, s, v = colorsys.rgb_to_hsv(rgb[0]/255, rgb[1]/255, rgb[2]/255)
        h = (h + degrees/360) % 1.0
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        return self._rgb_to_hex(int(r*255), int(g*255), int(b*255))
    
    def _get_lightness(self, hex_color: str) -> float:
        """Get perceived lightness of a color"""
        rgb = self._hex_to_rgb(hex_color)
        return (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]) / 255
    
    def _hex_to_rgb(self, hex_color: str) -> tuple:
        """Convert hex color to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _rgb_to_hex(self, r: int, g: int, b: int) -> str:
        """Convert RGB to hex color"""
        return f"#{r:02x}{g:02x}{b:02x}"

# Global service instance
color_extractor = ColorExtractor


def get_color_extractor() -> ColorExtractor:
    """Get or create service instance"""
    return color_extractor()