from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.html import format_html
from django.db.models import Count, Sum, F, Q
from .models import (
    Governorate, City, Category, Hall, HallImage, HallManager,
    Booking, BookingMealItem, BookingServiceItem, Contact, Notification,
    Ingredient, IngredientImage, Meal, MealImage, MealIngredient
)

User = get_user_model()

# Inlines
class HallImageInline(admin.TabularInline):
    model = HallImage
    extra = 1
    fields = ['image', 'image_type', 'title', 'is_featured', 'order']
    readonly_fields = ['get_image_preview']
    
    def get_image_preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" style="max-height: 100px;" />')
        return "لا توجد صورة"
    get_image_preview.short_description = 'معاينة الصورة'

class BookingMealItemInline(admin.TabularInline):
    model = BookingMealItem
    extra = 0
    readonly_fields = ['total_price', 'get_meal_price']
    fields = ['meal', 'get_meal_price', 'quantity', 'total_price', 'serving_time', 'special_instructions']
    
    def get_meal_price(self, obj):
        return f"{obj.price_at_booking} ريال"
    get_meal_price.short_description = 'سعر الوجبة'

class BookingServiceItemInline(admin.TabularInline):
    model = BookingServiceItem
    extra = 0
    readonly_fields = ['total_price', 'get_service_price']
    fields = ['service', 'get_service_price', 'quantity', 'total_price', 'status', 'start_time', 'end_time']
    
    def get_service_price(self, obj):
        return f"{obj.price_at_booking} ريال"
    get_service_price.short_description = 'سعر الخدمة'

class MealIngredientInline(admin.TabularInline):
    model = MealIngredient
    extra = 1
    autocomplete_fields = ['ingredient']

class MealImageInline(admin.TabularInline):
    model = MealImage
    extra = 1
    fields = ['image', 'caption', 'is_primary', 'order']

class IngredientImageInline(admin.TabularInline):
    model = IngredientImage
    extra = 1
    fields = ['image', 'caption', 'is_primary', 'order']

# Model Admins
@admin.register(Governorate)
class GovernorateAdmin(admin.ModelAdmin):
    list_display = ['name', 'name_en', 'code', 'region', 'city_count']
    search_fields = ['name', 'name_en', 'code']
    list_filter = ['region']
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            city_count=Count('cities')
        )
    
    def city_count(self, obj):
        return obj.city_count
    city_count.short_description = 'عدد المدن'
    city_count.admin_order_field = 'city_count'

@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ['name', 'name_en', 'governorate', 'is_capital', 'hall_count']
    search_fields = ['name', 'name_en']
    list_filter = ['governorate', 'is_capital']
    autocomplete_fields = ['governorate']
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            hall_count=Count('hall')
        )
    
    def hall_count(self, obj):
        return obj.hall_count
    hall_count.short_description = 'عدد القاعات'
    hall_count.admin_order_field = 'hall_count'

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'hall_count']
    search_fields = ['name', 'description']
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            hall_count=Count('hall')
        )
    
    def hall_count(self, obj):
        return obj.hall_count
    hall_count.short_description = 'عدد القاعات'
    hall_count.admin_order_field = 'hall_count'

@admin.register(Hall)
class HallAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'city', 'price_per_hour', 'status', 'booking_count']
    list_filter = ['status', 'category', 'city__governorate', 'city']
    search_fields = ['name', 'description', 'address']
    inlines = [HallImageInline]
    autocomplete_fields = ['category', 'governorate', 'city']
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            booking_count=Count('booking')
        )
    
    def booking_count(self, obj):
        return obj.booking_count
    booking_count.short_description = 'عدد الحجوزات'
    booking_count.admin_order_field = 'booking_count'

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['event_title', 'customer_name', 'hall', 'start_datetime', 'total_price_display', 'status']
    list_filter = ['status', 'hall', 'start_datetime']
    search_fields = ['event_title', 'customer_name', 'customer_email', 'customer_phone', 'booking_id']
    autocomplete_fields = ['hall', 'user']
    readonly_fields = ['created_at', 'updated_at', 'total_price_display', 'duration_hours', 'get_booking_link']
    inlines = [BookingMealItemInline, BookingServiceItemInline]
    date_hierarchy = 'start_datetime'
    
    fieldsets = (
        ('معلومات الحجز', {
            'fields': ('user', 'get_booking_link', 'hall', 'status')
        }),
        ('تفاصيل الحدث', {
            'fields': ('event_title', 'event_description', 'start_datetime', 'end_datetime', 'duration_hours', 'attendees_count')
        }),
        ('معلومات العميل', {
            'fields': ('customer_name', 'customer_email', 'customer_phone')
        }),
        ('التكاليف', {
            'fields': ('hall_price', 'meals_price', 'services_price', 'total_price_display')
        }),
        ('التواريخ', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('hall', 'user')
    
    def get_booking_link(self, obj):
        if obj.pk:
            url = reverse('admin:hall_booking_booking_change', args=[obj.pk])
            return format_html('<a href="{}">عرض تفاصيل الحجز</a>', url)
        return "-"
    get_booking_link.short_description = 'رابط الحجز'
    get_booking_link.allow_tags = True
    
    def duration_hours(self, obj):
        return obj.get_duration_hours()
    duration_hours.short_description = 'المدة (ساعات)'
    
    def total_price_display(self, obj):
        return f"{obj.total_price} ريال"
    total_price_display.short_description = 'الإجمالي'

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'subject', 'created_at', 'is_read', 'short_message']
    list_filter = ['is_read']
    search_fields = ['name', 'email', 'subject', 'message']
    readonly_fields = ['created_at', 'formatted_message']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (None, {
            'fields': ('name', 'email', 'phone', 'subject')
        }),
        ('الرسالة', {
            'fields': ('formatted_message',)
        }),
        ('معلومات إضافية', {
            'fields': ('created_at', 'is_read')
        }),
    )
    
    def formatted_message(self, obj):
        return mark_safe(f'<div style="white-space: pre-line; padding: 10px; background: #f8f9fa; border-radius: 5px;">{obj.message}</div>')
    formatted_message.short_description = 'نص الرسالة'
    
    def short_message(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    short_message.short_description = 'نص مختصر'

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'notification_type', 'is_read', 'created_ago']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['user__username', 'title', 'message']
    readonly_fields = ['created_at', 'formatted_message']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (None, {
            'fields': ('user', 'booking', 'notification_type', 'title')
        }),
        ('محتوى الإشعار', {
            'fields': ('formatted_message',)
        }),
        ('حالة الإشعار', {
            'fields': ('is_read', 'created_at')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'booking')
    
    def formatted_message(self, obj):
        return mark_safe(f'<div style="white-space: pre-line; padding: 10px; background: #f8f9fa; border-radius: 5px;">{obj.message}</div>')
    formatted_message.short_description = 'نص الرسالة'
    
    def created_ago(self, obj):
        now = timezone.now()
        diff = now - obj.created_at
        
        if diff.days > 7:
            return obj.created_at.strftime('%Y-%m-%d')
        elif diff.days > 0:
            return f'منذ {diff.days} يوم'
        elif diff.seconds >= 3600:
            hours = diff.seconds // 3600
            return f'منذ {hours} ساعة'
        elif diff.seconds >= 60:
            minutes = diff.seconds // 60
            return f'منذ {minutes} دقيقة'
    created_ago.short_description = 'تاريخ الإرسال'

@admin.register(Meal)
class MealAdmin(admin.ModelAdmin):
    list_display = ['name', 'meal_type', 'price_per_person', 'is_available']
    list_filter = ['meal_type', 'is_available']
    search_fields = ['name', 'description']
    inlines = [MealIngredientInline, MealImageInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('ingredients')

@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_allergen']
    list_filter = ['is_allergen']
    search_fields = ['name', 'description']
    inlines = [IngredientImageInline]

@admin.register(HallManager)
class HallManagerAdmin(admin.ModelAdmin):
    list_display = ['user', 'hall', 'permission_level', 'is_active']
    list_filter = ['permission_level', 'is_active']
    search_fields = ['user__username', 'hall__name']
    autocomplete_fields = ['user', 'hall']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'hall')

# Register models with default admin
admin.site.register(MealIngredient)
admin.site.register(MealImage)
admin.site.register(IngredientImage)
admin.site.register(BookingMealItem)
admin.site.register(BookingServiceItem)
