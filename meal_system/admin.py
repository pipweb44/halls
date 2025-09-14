from django.contrib import admin
from django.utils.html import format_html
from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple

# Import hall meal models
from .hall_meals_models import HallMealComponent, HallMeal
from .hall_meals_admin import HallMealComponentAdmin, HallMealAdmin


# Register the hall meal models if not already registered
if not admin.site.is_registered(HallMealComponent):
    admin.site.register(HallMealComponent, HallMealComponentAdmin)
if not admin.site.is_registered(HallMeal):
    admin.site.register(HallMeal, HallMealAdmin)
