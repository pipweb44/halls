from .models import SiteSettings

def site_settings(request):
    """Context processor لإعدادات الموقع"""
    try:
        settings = SiteSettings.get_settings()
        return {
            'site_settings': settings
        }
    except Exception:
        # في حالة عدم وجود إعدادات أو حدوث خطأ
        return {
            'site_settings': {
                'site_name': 'a7jazili',
                'site_name_ar': 'احجزلي',
                'phone_primary': '',
                'email_primary': '',
                'facebook_url': '',
                'twitter_url': '',
                'instagram_url': '',
                'linkedin_url': '',
                'youtube_url': '',
                'whatsapp_number': '',
                'telegram_url': '',
                'footer_text': 'جميع الحقوق محفوظة',
                'copyright_year': 2024,
            }
        }
