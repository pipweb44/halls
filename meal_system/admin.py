from django.contrib import admin
from django.utils.html import format_html
from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple

# Import hall meal models
from .hall_meals_models import HallMealCategory, HallMeal, HallMealComponent



@admin.register(HallMealCategory)
class HallMealCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'hall', 'is_active', 'order', 'image_tag']
    list_filter = ['hall', 'is_active']
    search_fields = ['name', 'description']
    list_select_related = ['hall']
    readonly_fields = ['created_at', 'updated_at', 'image_tag']
    fieldsets = [
        (None, {
            'fields': [
                'hall', 'name', 'description', 'image', 'image_tag',
                'is_active', 'order', 'min_selections', 'max_selections', 'is_required'
            ]
        }),
        ('التواريخ', {
            'classes': ('collapse',),
            'fields': ['created_at', 'updated_at'],
        }),
    ]

    def image_tag(self, obj):
        return obj.image_tag()
    image_tag.short_description = 'صورة'


@admin.register(HallMealComponent)
class HallMealComponentAdmin(admin.ModelAdmin):
    list_display = ['name', 'hall', 'component_type', 'price', 'is_available', 'image_tag']
    list_filter = ['hall', 'component_type', 'is_available']
    search_fields = ['name', 'description']
    list_select_related = ['hall']
    readonly_fields = ['created_at', 'updated_at', 'image_tag']
    fieldsets = [
        (None, {
            'fields': [
                'hall', 'name', 'component_type', 'description',
                'price', 'image', 'image_tag', 'is_available'
            ]
        }),
        ('التواريخ', {
            'classes': ('collapse',),
            'fields': ['created_at', 'updated_at'],
        }),
    ]

    def image_tag(self, obj):
        return obj.image_tag()
    image_tag.short_description = 'صورة'


@admin.register(HallMeal)
class HallMealAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'hall', 'base_price', 'is_available', 'image_tag']
    list_filter = ['category', 'is_available']
    search_fields = ['name', 'description']
    list_select_related = ['category', 'category__hall']
    readonly_fields = ['created_at', 'updated_at', 'image_tag']
    fieldsets = [
        (None, {
            'fields': [
                'hall', 'category', 'name', 'description',
                'base_price', 'image', 'image_tag', 'is_available', 'order_in_category'
            ]
        }),
        ('التواريخ', {
            'classes': ('collapse',),
            'fields': ['created_at', 'updated_at'],
        }),
    ]

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing an existing object
            return self.readonly_fields + ['hall', 'category']
        return self.readonly_fields

    def save_model(self, request, obj, form, change):
        if not change:  # Only set hall on create
            obj.hall = obj.category.hall
        super().save_model(request, obj, form, change)

    def image_tag(self, obj):
        return obj.image_tag()
    image_tag.short_description = 'صورة'

    def hall(self, obj):
        return obj.category.hall
    hall.short_description = 'القاعة'
    hall.admin_order_field = 'category__hall__name'
