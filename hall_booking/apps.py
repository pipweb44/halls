from django.apps import AppConfig

class HallBookingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'hall_booking'
    
    def ready(self):
        # محاولة استيراد الإشارات إذا وجدت
        try:
            from . import signals
        except ImportError:
            # تجاهل الخطأ إذا لم يتم العثور على وحدة الإشارات
            pass
