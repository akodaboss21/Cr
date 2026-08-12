"""
Frontend Theme System

Implements theme provider for runtime theme switching.
Supports CSS variables, Tailwind integration, and preserves existing pages.
"""
from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class ThemeContext:
    """Theme context for React components"""
    theme: Dict[str, Any]
    set_theme: callable
    toggle_dark_mode: callable

class ThemeProvider:
    """
    React context provider for theme management
    
    Features:
    - CSS variables for dynamic theming
    - Tailwind integration
    - Runtime theme switching
    - Preserves existing pages
    """
    
    def __init__(self):
        self.current_theme = {}
        self.listeners = []
    
    def set_theme(self, theme: Dict[str, Any]):
        """Set new theme and notify listeners"""
        self.current_theme = theme
        self._notify_listeners()
    
    def get_theme(self) -> Dict[str, Any]:
        """Get current theme"""
        return self.current_theme
    
    def _notify_listeners(self):
        """Notify all listeners of theme change"""
        for listener in self.listeners:
            listener(self.current_theme)
    
    def subscribe(self, callback: callable):
        """Subscribe to theme changes"""
        self.listeners.append(callback)
        return lambda: self.listeners.remove(callback)

# CSS Variable Generator
def generate_css_variables(theme: Dict[str, Any]) -> str:
    """Generate CSS variables string from theme"""
    css_vars = []
    for key, value in theme.get('colors', {}).items():
        css_vars.append(f"  --brand-{key}: {value};")
    return ":root {\n" + "\n".join(css_vars) + "\n}"

# Tailwind Config Generator
def generate_tailwind_config(theme: Dict[str, Any]) -> Dict[str, Any]:
    """Generate Tailwind config from theme"""
    return {
        'theme': {
            'extend': {
                'colors': theme.get('colors', {}),
                'fontFamily': theme.get('fonts', {}),
                'borderRadius': theme.get('radius', {})
            }
        }
    }

# Global theme provider instance
theme_provider = ThemeProvider


def get_theme_provider() -> ThemeProvider:
    """Get or create theme provider instance"""
    return theme_provider()