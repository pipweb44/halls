from django import template
from hall_booking.models import HallManager

register = template.Library()

@register.filter
def is_hall_manager(user):
    """تحقق من كون المستخدم مدير قاعة"""
    if not user.is_authenticated:
        return False
    return HallManager.objects.filter(user=user, is_active=True).exists()

@register.simple_tag
def get_managed_hall(user):
    """الحصول على القاعة التي يديرها المستخدم"""
    if not user.is_authenticated:
        return None
    try:
        manager = HallManager.objects.get(user=user, is_active=True)
        return manager.hall
    except HallManager.DoesNotExist:
        return None
