from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .hall_meals_models import HallMeal, HallMealComponent, HallMealCategory


class HallMealCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'hall', 'meals_count', 'is_active', 'order', 'created_at', 'image_tag']
    list_filter = ['hall', 'is_active']
    search_fields = ['name', 'description', 'hall__name']
    list_editable = ['is_active', 'order']
    readonly_fields = ['created_at', 'updated_at', 'image_tag', 'meals_count']
    autocomplete_fields = ['hall']
    fieldsets = [
        (None, {
            'fields': [
                'hall', 'name', 'description', 'image', 'image_tag',
                'is_active', 'order', 'is_required',
                'min_selections', 'max_selections'
            ]
        }),
        ('التواريخ', {
            'classes': ['collapse'],
            'fields': ['created_at', 'updated_at'],
        }),
    ]

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('meals')

    def meals_count(self, obj):
        return obj.meals.count()
    meals_count.short_description = 'عدد الوجبات'


class HallMealComponentAdmin(admin.ModelAdmin):
    list_display = ['name', 'hall', 'component_type', 'price', 'is_available', 'created_at', 'image_tag']
    list_filter = ['hall', 'component_type', 'is_available']
    autocomplete_fields = ['hall']
    search_fields = ['name', 'description']
    list_editable = ['is_available', 'price']
    readonly_fields = ['created_at', 'updated_at', 'image_tag']
    fieldsets = [
        (None, {
            'fields': [
                'hall', 'name', 'component_type', 'description',
                'price', 'is_available', 'image', 'image_tag'
            ]
        }),
        ('التواريخ', {
            'classes': ['collapse'],
            'fields': ['created_at', 'updated_at'],
        }),
    ]


class HallMealAdmin(admin.ModelAdmin):
    list_display = ['name', 'hall', 'category', 'base_price', 'is_available', 'image_tag']
    list_filter = ['hall', 'category', 'is_available']
    search_fields = ['name', 'description', 'category__name']
    list_editable = ['is_available', 'base_price']
    list_select_related = ['hall', 'category']
    readonly_fields = ['created_at', 'updated_at', 'image_tag']
    autocomplete_fields = ['hall', 'category']

    fieldsets = [
        (None, {
            'fields': [
                'hall', 'category', 'name', 'description', 'base_price',
                'is_available', 'image', 'image_tag', 'order_in_category'
            ]
        }),
        ('التواريخ', {
            'classes': ['collapse'],
            'fields': ['created_at', 'updated_at'],
        }),
    ]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('hall', 'category')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'category':
            hall_id = request.GET.get('hall')
            if hall_id:
                kwargs['queryset'] = HallMealCategory.objects.filter(hall_id=hall_id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if 'category' in form.base_fields:
            form.base_fields['category'].widget.can_add_related = False
            form.base_fields['category'].widget.can_change_related = False
            form.base_fields['category'].widget.can_delete_related = False
        return form


# Register your models here.
admin.site.register(HallMeal, HallMealAdmin)
admin.site.register(HallMealComponent, HallMealComponentAdmin)
admin.site.register(HallMealCategory, HallMealCategoryAdmin)
