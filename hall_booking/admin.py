from django.contrib import admin
from django.contrib.admin import AdminSite, TabularInline
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import render
from django.db.models import Count, Sum, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from .models import (
    Category, Hall, Booking, Contact, HallImage, HallManager, Notification, 
    Governorate, City
)

# ===========================================
# Custom Admin Classes
# ===========================================

class GovernorateAdmin(admin.ModelAdmin):
    list_display = ['name', 'name_en', 'code', 'region']
    search_fields = ['name', 'name_en', 'code']
    list_filter = ['region']

class CityAdmin(admin.ModelAdmin):
    list_display = ['name', 'name_en', 'governorate', 'is_capital']
    search_fields = ['name', 'name_en']
    list_filter = ['governorate', 'is_capital']
    autocomplete_fields = ['governorate']

class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon']
    search_fields = ['name', 'description']

class HallImageInline(admin.TabularInline):
    model = HallImage
    extra = 1
    fields = ['image', 'image_type', 'title', 'is_featured', 'order']

class HallAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'city', 'price_per_hour', 'status']
    list_filter = ['status', 'category', 'city__governorate', 'city']
    search_fields = ['name', 'description', 'address']
    inlines = [HallImageInline]
    autocomplete_fields = ['category', 'governorate', 'city']

class BookingAdmin(admin.ModelAdmin):
    list_display = ['event_title', 'customer_name', 'hall', 'start_datetime', 'end_datetime', 'status']
    list_filter = ['status', 'hall']
    search_fields = ['event_title', 'customer_name', 'customer_email', 'customer_phone']
    autocomplete_fields = ['hall', 'user']

class HallManagerAdmin(admin.ModelAdmin):
    list_display = ['user', 'hall', 'permission_level', 'is_active']
    list_filter = ['permission_level', 'is_active']
    search_fields = ['user__username', 'hall__name']
    autocomplete_fields = ['user', 'hall']

class ContactAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'subject', 'created_at', 'is_read']
    list_filter = ['is_read']
    search_fields = ['name', 'email', 'subject', 'message']
    readonly_fields = ['created_at']

class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read']
    search_fields = ['user__username', 'title', 'message']
    readonly_fields = ['created_at']

# ===========================================
# Register Models
# ===========================================

# Core Models
admin.site.register(Governorate, GovernorateAdmin)
admin.site.register(City, CityAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Hall, HallAdmin)
admin.site.register(Booking, BookingAdmin)
admin.site.register(HallManager, HallManagerAdmin)
admin.site.register(Contact, ContactAdmin)
admin.site.register(Notification, NotificationAdmin)

# Meal related models
# admin.site.register(Meal, MealAdmin)
# admin.site.register(MealImage)
# admin.site.register(MealItem, MealItemAdmin)
# admin.site.register(MealItemImage)
