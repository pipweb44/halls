from django import template

register = template.Library()

@register.filter
def get_occupancy_color(rate):
    """Return a color class based on occupancy rate"""
    if rate < 30:
        return 'success'  # Green for low occupancy
    elif 30 <= rate < 70:
        return 'warning'  # Yellow for medium occupancy
    else:
        return 'danger'   # Red for high occupancy
