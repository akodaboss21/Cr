from packages.core.branding.widget_branding import WidgetBrandingService

def test_widget_branding_generation():
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