from django.contrib import admin
from django.utils.html import format_html
from .models import MealCategory, MealItem, MealItemImage, MealComponent, MealComponentImage


class MealItemImageInline(admin.StackedInline):
    model = MealItemImage
    extra = 1
    fields = ['image', 'caption', 'is_primary']
    readonly_fields = ['created_at', 'updated_at', 'image_tag']
    verbose_name = 'صورة'
    verbose_name_plural = 'صور الوجبة'


class MealComponentInline(admin.StackedInline):
    model = MealComponent
    extra = 1
    fields = ['name', 'component_type', 'description', 'quantity', 'is_optional', 'order']
    verbose_name = 'مكون'
    verbose_name_plural = 'مكونات الوجبة'


@admin.register(MealCategory)
class MealCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'order', 'created_at', 'image_tag']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    fieldsets = [
        ('معلومات الصنف', {
            'fields': [
                'name', 'description', 'image', 'is_active', 'order'
            ]
        }),
        ('التواريخ', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    readonly_fields = ['created_at', 'updated_at', 'image_tag']


@admin.register(MealItem)
class MealItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'get_category', 'price', 'is_available', 'order', 'created_at', 'get_primary_image']
    list_filter = ['is_available', 'category']
    search_fields = ['name', 'description', 'category__name']
    inlines = [MealItemImageInline, MealComponentInline]
    fieldsets = [
        ('معلومات الوجبة', {
            'fields': [
                'category', 'name', 'description', 
                'price', 'is_available', 'order'
            ]
        }),
        ('التواريخ', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    readonly_fields = ['created_at', 'updated_at']

    def get_category(self, obj):
        return obj.category.name
    get_category.short_description = 'الصنف'
    get_category.admin_order_field = 'category__name'

    def get_primary_image(self, obj):
        primary_img = obj.images.filter(is_primary=True).first() or obj.images.first()
        if primary_img and hasattr(primary_img, 'image_tag'):
            return primary_img.image_tag()
        return "لا توجد صورة"
    get_primary_image.short_description = 'الصورة الرئيسية'
    get_primary_image.allow_tags = True


@admin.register(MealComponent)
class MealComponentAdmin(admin.ModelAdmin):
    list_display = ['name', 'get_meal', 'component_type', 'is_optional', 'order', 'created_at']
    list_filter = ['component_type', 'is_optional']
    search_fields = ['name', 'description', 'meal__name']
    fieldsets = [
        ('معلومات المكون', {
            'fields': [
                'meal', 'name', 'component_type', 'description',
                'quantity', 'is_optional', 'order'
            ]
        }),
        ('التواريخ', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    readonly_fields = ['created_at', 'updated_at']

    def get_meal(self, obj):
        return obj.meal.name
    get_meal.short_description = 'الوجبة'
    get_meal.admin_order_field = 'meal__name'


@admin.register(MealItemImage)
class MealItemImageAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'meal', 'is_primary', 'created_at', 'image_tag']
    list_filter = ['is_primary']
    search_fields = ['meal__name', 'caption']
    readonly_fields = ['created_at', 'updated_at', 'image_tag']
    fields = ['meal', 'image', 'image_tag', 'caption', 'is_primary', 'created_at', 'updated_at']


@admin.register(MealComponentImage)
class MealComponentImageAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'component', 'is_primary', 'created_at', 'image_tag']
    list_filter = ['is_primary']
    search_fields = ['component__name', 'caption']
    readonly_fields = ['created_at', 'updated_at', 'image_tag']
    fields = ['component', 'image', 'image_tag', 'caption', 'is_primary', 'created_at', 'updated_at']
