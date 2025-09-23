from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.admin import AdminSite

# Configure Django Admin site headers
admin.site.site_header = "نظام إدارة القاعات"
admin.site.site_title = "لوحة تحكم القاعات"
admin.site.index_title = "مرحباً بك في نظام إدارة حجز القاعات"
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import render
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from django.http import JsonResponse
from datetime import datetime, timedelta
from unfold.admin import ModelAdmin, TabularInline, StackedInline
from unfold.decorators import display
from unfold.contrib.filters.admin import RangeDateFilter
from .models import (Category, Hall, Booking, Contact, HallImage, HallManager, 
                    Notification, Governorate, City, HallService, HallMeal, 
                    BookingService, BookingMeal, SiteSettings)

# تخصيص لوحة الإدارة
class HallBookingAdminSite(AdminSite):
    site_header = "نظام إدارة حجز القاعات"
    site_title = "لوحة الإدارة"
    index_title = "مرحباً بك في نظام إدارة حجز القاعات"
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', self.admin_view(self.dashboard_view), name='dashboard'),
            path('statistics/', self.admin_view(self.statistics_view), name='statistics'),
            path('statistics/api/bookings-chart/', self.admin_view(self.bookings_chart_api), name='bookings_chart_api'),
            path('statistics/api/revenue-chart/', self.admin_view(self.revenue_chart_api), name='revenue_chart_api'),
            path('statistics/api/halls-chart/', self.admin_view(self.halls_chart_api), name='halls_chart_api'),
        ]
        return custom_urls + urls
    
    def dashboard_view(self, request):
        # إحصائيات عامة
        total_halls = Hall.objects.count()
        total_bookings = Booking.objects.count()
        pending_bookings = Booking.objects.filter(status='pending').count()
        completed_bookings = Booking.objects.filter(status='completed').count()
        total_revenue = Booking.objects.filter(status='completed').aggregate(total=Sum('total_price'))['total'] or 0
        
        # إحصائيات الشهر الحالي
        current_month = timezone.now().month
        current_year = timezone.now().year
        monthly_bookings = Booking.objects.filter(
            created_at__month=current_month,
            created_at__year=current_year
        ).count()
        
        # إحصائيات القاعات حسب الفئة
        category_stats = Category.objects.annotate(
            hall_count=Count('hall'),
            booking_count=Count('hall__booking')
        )
        
        # آخر الحجوزات
        recent_bookings = Booking.objects.select_related('hall').order_by('-created_at')[:10]
        
        # رسائل التواصل الجديدة
        new_contacts = Contact.objects.filter(is_read=False).order_by('-created_at')[:5]
        
        context = {
            'total_halls': total_halls,
            'total_bookings': total_bookings,
            'pending_bookings': pending_bookings,
            'completed_bookings': completed_bookings,
            'total_revenue': total_revenue,
            'monthly_bookings': monthly_bookings,
            'category_stats': category_stats,
            'recent_bookings': recent_bookings,
            'new_contacts': new_contacts,
        }
        
        return render(request, 'admin/dashboard.html', context)
    
    def statistics_view(self, request):
        """صفحة الإحصائيات مع الرسوم البيانية"""
        # إحصائيات عامة
        total_halls = Hall.objects.count()
        total_bookings = Booking.objects.count()
        total_revenue = Booking.objects.filter(status='completed').aggregate(total=Sum('total_price'))['total'] or 0
        
        # إحصائيات الحجوزات حسب الحالة
        booking_stats = {
            'pending': Booking.objects.filter(status='pending').count(),
            'approved': Booking.objects.filter(status='approved').count(),
            'completed': Booking.objects.filter(status='completed').count(),
            'cancelled': Booking.objects.filter(status='cancelled').count(),
            'rejected': Booking.objects.filter(status='rejected').count(),
        }
        
        # إحصائيات القاعات حسب الفئة
        category_stats = Category.objects.annotate(
            hall_count=Count('hall'),
            booking_count=Count('hall__booking')
        ).values('name', 'hall_count', 'booking_count')
        
        # إحصائيات المحافظات
        governorate_stats = Governorate.objects.annotate(
            hall_count=Count('hall'),
            booking_count=Count('hall__booking')
        ).values('name', 'hall_count', 'booking_count')
        
        # أفضل القاعات (الأكثر حجزاً)
        top_halls = Hall.objects.annotate(
            booking_count=Count('booking')
        ).order_by('-booking_count')[:10]
        
        # إحصائيات الإيرادات الشهرية (آخر 12 شهر)
        monthly_revenue = []
        for i in range(12):
            date = timezone.now() - timedelta(days=30*i)
            revenue = Booking.objects.filter(
                status='completed',
                created_at__year=date.year,
                created_at__month=date.month
            ).aggregate(total=Sum('total_price'))['total'] or 0
            monthly_revenue.append({
                'month': date.strftime('%Y-%m'),
                'revenue': float(revenue)
            })
        
        context = {
            'title': 'الإحصائيات والتقارير',
            'total_halls': total_halls,
            'total_bookings': total_bookings,
            'total_revenue': total_revenue,
            'booking_stats': booking_stats,
            'category_stats': list(category_stats),
            'governorate_stats': list(governorate_stats),
            'top_halls': top_halls,
            'monthly_revenue': monthly_revenue[::-1],  # عكس الترتيب للحصول على الأحدث أولاً
        }
        
        return render(request, 'admin/statistics.html', context)
    
    def bookings_chart_api(self, request):
        """API للحصول على بيانات مخطط الحجوزات"""
        # بيانات الحجوزات حسب الشهر (آخر 12 شهر)
        months = []
        bookings_data = []
        
        for i in range(12):
            date = timezone.now() - timedelta(days=30*i)
            month_name = date.strftime('%Y-%m')
            booking_count = Booking.objects.filter(
                created_at__year=date.year,
                created_at__month=date.month
            ).count()
            
            months.append(month_name)
            bookings_data.append(booking_count)
        
        return JsonResponse({
            'labels': months[::-1],
            'data': bookings_data[::-1]
        })
    
    def revenue_chart_api(self, request):
        """API للحصول على بيانات مخطط الإيرادات"""
        # بيانات الإيرادات حسب الشهر (آخر 12 شهر)
        months = []
        revenue_data = []
        
        for i in range(12):
            date = timezone.now() - timedelta(days=30*i)
            month_name = date.strftime('%Y-%m')
            revenue = Booking.objects.filter(
                status='completed',
                created_at__year=date.year,
                created_at__month=date.month
            ).aggregate(total=Sum('total_price'))['total'] or 0
            
            months.append(month_name)
            revenue_data.append(float(revenue))
        
        return JsonResponse({
            'labels': months[::-1],
            'data': revenue_data[::-1]
        })
    
    def halls_chart_api(self, request):
        """API للحصول على بيانات مخطط القاعات حسب الفئة"""
        categories = Category.objects.annotate(
            hall_count=Count('hall')
        ).values('name', 'hall_count')
        
        labels = [cat['name'] for cat in categories]
        data = [cat['hall_count'] for cat in categories]
        
        return JsonResponse({
            'labels': labels,
            'data': data
        })

# إنشاء نسخة مخصصة من لوحة الإدارة
admin_site = HallBookingAdminSite(name='hall_booking_admin')

# إضافة views الإحصائيات مباشرة في admin
def statistics_view(self, request):
    """صفحة الإحصائيات مع الرسوم البيانية"""
    # إحصائيات عامة
    total_halls = Hall.objects.count()
    total_bookings = Booking.objects.count()
    total_revenue = Booking.objects.filter(status='completed').aggregate(total=Sum('total_price'))['total'] or 0
    
    # إحصائيات الحجوزات حسب الحالة
    booking_stats = {
        'pending': Booking.objects.filter(status='pending').count(),
        'approved': Booking.objects.filter(status='approved').count(),
        'completed': Booking.objects.filter(status='completed').count(),
        'cancelled': Booking.objects.filter(status='cancelled').count(),
        'rejected': Booking.objects.filter(status='rejected').count(),
    }
    
    # إحصائيات القاعات حسب الفئة
    category_stats = Category.objects.annotate(
        hall_count=Count('hall'),
        booking_count=Count('hall__bookings')
    ).values('name', 'hall_count', 'booking_count')
    
    # إحصائيات المحافظات
    governorate_stats = Governorate.objects.annotate(
        hall_count=Count('hall'),
        booking_count=Count('hall__bookings')
    ).values('name', 'hall_count', 'booking_count')
    
    # أفضل القاعات (الأكثر حجزاً)
    top_halls = Hall.objects.annotate(
        booking_count=Count('bookings')
    ).order_by('-booking_count')[:10]
    
    context = {
        'title': 'الإحصائيات والتقارير',
        'site_title': self.site_title,
        'site_header': self.site_header,
        'site_url': self.site_url,
        'has_permission': True,
        'available_apps': self.get_app_list(request),
        'is_popup': False,
        'total_halls': total_halls,
        'total_bookings': total_bookings,
        'total_revenue': total_revenue,
        'booking_stats': booking_stats,
        'category_stats': list(category_stats),
        'governorate_stats': list(governorate_stats),
        'top_halls': top_halls,
    }
    
    return render(request, 'admin/statistics_new.html', context)

def bookings_chart_api(self, request):
    """API للحصول على بيانات مخطط الحجوزات"""
    months = []
    bookings_data = []
    
    for i in range(12):
        date = timezone.now() - timedelta(days=30*i)
        month_name = date.strftime('%Y-%m')
        booking_count = Booking.objects.filter(
            created_at__year=date.year,
            created_at__month=date.month
        ).count()
        
        months.append(month_name)
        bookings_data.append(booking_count)
    
    return JsonResponse({
        'labels': months[::-1],
        'data': bookings_data[::-1]
    })

def revenue_chart_api(self, request):
    """API للحصول على بيانات مخطط الإيرادات"""
    months = []
    revenue_data = []
    
    for i in range(12):
        date = timezone.now() - timedelta(days=30*i)
        month_name = date.strftime('%Y-%m')
        revenue = Booking.objects.filter(
            status='completed',
            created_at__year=date.year,
            created_at__month=date.month
        ).aggregate(total=Sum('total_price'))['total'] or 0
        
        months.append(month_name)
        revenue_data.append(float(revenue))
    
    return JsonResponse({
        'labels': months[::-1],
        'data': revenue_data[::-1]
    })

def halls_chart_api(self, request):
    """API للحصول على بيانات مخطط القاعات حسب الفئة"""
    categories = Category.objects.annotate(
        hall_count=Count('hall')
    ).values('name', 'hall_count')
    
    labels = [cat['name'] for cat in categories]
    data = [cat['hall_count'] for cat in categories]
    
    return JsonResponse({
        'labels': labels,
        'data': data
    })

# ربط الدوال بالكلاس
HallBookingAdminSite.statistics_view = statistics_view
HallBookingAdminSite.bookings_chart_api = bookings_chart_api
HallBookingAdminSite.revenue_chart_api = revenue_chart_api
HallBookingAdminSite.halls_chart_api = halls_chart_api

# تخصيص نموذج الفئات
@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ['name', 'hall_count', 'description']
    list_filter = ['name']
    search_fields = ['name', 'description']
    ordering = ['name']
    
    @display(description='عدد القاعات')
    def hall_count(self, obj):
        return obj.hall_set.count()

# تخصيص نموذج صور القاعات (inline)
class HallImageInline(TabularInline):
    model = HallImage
    extra = 1
    fields = ['image', 'image_type', 'title', 'is_featured', 'order', 'uploaded_at']
    readonly_fields = ['uploaded_at']

# Inline for Hall Services
class HallServiceInline(StackedInline):
    model = HallService
    extra = 1
    fields = ['name', 'description', 'price', 'is_available']
    show_change_link = True
    min_num = 0
    verbose_name = "خدمة"
    verbose_name_plural = "الخدمات"
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if 'object_id' in request.resolver_match.kwargs:
            return qs.filter(hall_id=request.resolver_match.kwargs['object_id'])
        return qs.none()

# Inline for Hall Meals
class HallMealInline(StackedInline):
    model = HallMeal
    extra = 1
    fields = ['name', 'meal_type', 'price_per_person', 'is_available', 'is_vegetarian', 'min_order']
    show_change_link = True
    min_num = 0
    verbose_name = "وجبة"
    verbose_name_plural = "الوجبات"
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if 'object_id' in request.resolver_match.kwargs:
            return qs.filter(hall_id=request.resolver_match.kwargs['object_id'])
        return qs.none()

# تخصيص نموذج مديري القاعات (inline)
class HallManagerInline(TabularInline):
    model = HallManager
    extra = 0
    fields = ['user', 'permission_level', 'is_active', 'assigned_at']
    readonly_fields = ['assigned_at']

# تخصيص نموذج القاعات
@admin.register(Hall)
class HallAdmin(ModelAdmin):
    list_display = ['name', 'category', 'governorate', 'city', 'price_per_hour', 'status', 'created_at']
    list_filter = ['status', 'category', 'governorate', 'city']
    search_fields = ['name', 'description', 'address']
    readonly_fields = ['created_at', 'updated_at', 'get_thumbnail_preview']
    inlines = [HallImageInline, HallServiceInline, HallMealInline]
    
    def get_inline_instances(self, request, obj=None):
        # Only show inlines when editing an existing object
        if obj:
            return [inline(self.model, self.admin_site) for inline in self.inlines]
        return []

    fieldsets = (
        ('معلومات أساسية', {
            'fields': ('name', 'category', 'description')
        }),
        ('الموقع', {
            'fields': ('governorate', 'city', 'address', 'latitude', 'longitude')
        }),
        ('المواصفات', {
            'fields': ('capacity', 'price_per_hour', 'features')
        }),
        ('معلومات الاتصال', {
            'fields': ('phone', 'email', 'website'),
            'classes': ('collapse',)
        }),
        ('الحالة', {
            'fields': ('status',)
        }),
        ('التواريخ', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

# Inline for Booking Services
class BookingServiceInline(TabularInline):
    model = BookingService
    extra = 1
    fields = ['service', 'quantity', 'price', 'notes']
    autocomplete_fields = ['service']

# Inline for Booking Meals
class BookingMealInline(TabularInline):
    model = BookingMeal
    extra = 1
    fields = ['meal', 'quantity', 'price_per_person', 'total_price', 'serving_time', 'notes']
    autocomplete_fields = ['meal']
    readonly_fields = ['total_price']

# تخصيص نموذج الحجوزات
@admin.register(Booking)
class BookingAdmin(ModelAdmin):
    list_display = ['event_title', 'customer_name', 'hall', 'start_datetime', 'end_datetime', 'status', 'total_price', 'created_at']
    list_filter = ['status', 'created_at', 'hall__category']
    search_fields = ['customer_name', 'customer_email', 'event_title', 'hall__name']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'total_price', 'updated_at']
    inlines = [BookingServiceInline, BookingMealInline]
    
    fieldsets = (
        ('معلومات العميل', {
            'fields': ('customer_name', 'customer_email', 'customer_phone')
        }),
        ('معلومات الحدث', {
            'fields': ('event_title', 'event_description', 'attendees_count')
        }),
        ('تفاصيل الحجز', {
            'fields': ('hall', 'start_datetime', 'end_datetime', 'total_price')
        }),
        ('الحالة', {
            'fields': ('status',)
        }),
        ('التواريخ', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_bookings', 'reject_bookings', 'mark_as_completed']
    
    def approve_bookings(self, request, queryset):
        updated = queryset.update(status='approved')
        self.message_user(request, f'تم الموافقة على {updated} حجز بنجاح.')
    approve_bookings.short_description = "الموافقة على الحجوزات المحددة"
    
    def reject_bookings(self, request, queryset):
        updated = queryset.update(status='rejected')
        self.message_user(request, f'تم رفض {updated} حجز بنجاح.')
    reject_bookings.short_description = "رفض الحجوزات المحددة"
    
    def mark_as_completed(self, request, queryset):
        updated = queryset.update(status='completed')
        self.message_user(request, f'تم تحديد {updated} حجز كمكتمل بنجاح.')
    mark_as_completed.short_description = "تحديد الحجوزات كمكتملة"

# Inline للحجوزات ضمن صفحة المستخدم في لوحة الإدارة
class BookingInline(TabularInline):
    model = Booking
    extra = 0
    fields = (
        'hall', 'event_title', 'start_datetime', 'end_datetime', 'status', 'total_price',
    )
    readonly_fields = ('total_price',)
    show_change_link = True

class UserAdmin(DjangoUserAdmin):
    inlines = [BookingInline]

# تسجيل التخصيص في لوحة الإدارة الافتراضية
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass
admin.site.register(User, UserAdmin)

# وتسجيله أيضاً في لوحة الإدارة المخصصة إن كنت تستخدمها
try:
    admin_site.unregister(User)
except Exception:
    pass
admin_site.register(User, UserAdmin)

# تخصيص نموذج التواصل
@admin.register(Contact)
class ContactAdmin(ModelAdmin):
    list_display = ['name', 'email', 'subject', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['name', 'email', 'subject', 'message']
    ordering = ['-created_at']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('معلومات المرسل', {
            'fields': ('name', 'email', 'phone')
        }),
        ('محتوى الرسالة', {
            'fields': ('subject', 'message')
        }),
        ('الحالة', {
            'fields': ('is_read',)
        }),
        ('التواريخ', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f'تم تحديد {updated} رسالة كمقروءة بنجاح.')
    mark_as_read.short_description = "تحديد الرسائل كمقروءة"
    
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f'تم تحديد {updated} رسالة كغير مقروءة بنجاح.')
    mark_as_unread.short_description = "تحديد الرسائل كغير مقروءة"

# تخصيص نموذج مديري القاعات
@admin.register(HallManager)
class HallManagerAdmin(ModelAdmin):
    list_display = ['user', 'hall', 'permission_level', 'is_active', 'assigned_at']
    list_filter = ['permission_level', 'is_active', 'assigned_at', 'hall__category']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'hall__name']
    ordering = ['-assigned_at']
    readonly_fields = ['assigned_at']

    fieldsets = (
        ('معلومات التعيين', {
            'fields': ('user', 'hall', 'permission_level')
        }),
        ('الحالة', {
            'fields': ('is_active',)
        }),
        ('ملاحظات', {
            'fields': ('notes',)
        }),
        ('التواريخ', {
            'fields': ('assigned_at',),
            'classes': ('collapse',)
        }),
    )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "user":
            # عرض المستخدمين الذين ليسوا مديرين لقاعات أخرى
            assigned_users = HallManager.objects.filter(is_active=True).values_list('user_id', flat=True)
            kwargs["queryset"] = User.objects.exclude(id__in=assigned_users)
        elif db_field.name == "hall":
            # عرض القاعات التي ليس لها مدير
            assigned_halls = HallManager.objects.filter(is_active=True).values_list('hall_id', flat=True)
            kwargs["queryset"] = Hall.objects.exclude(id__in=assigned_halls)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

# تخصيص نموذج الإشعارات
@admin.register(Notification, site=admin_site)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['title', 'message', 'user__username', 'user__email']
    ordering = ['-created_at']
    readonly_fields = ['created_at']

    fieldsets = (
        ('معلومات الإشعار', {
            'fields': ('user', 'booking', 'notification_type', 'title', 'message')
        }),
        ('الحالة', {
            'fields': ('is_read',)
        }),
        ('التواريخ', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    actions = ['mark_as_read', 'mark_as_unread']

    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f'تم تحديد {updated} إشعار كمقروء.')
    mark_as_read.short_description = "تحديد كمقروء"

    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f'تم تحديد {updated} إشعار كغير مقروء.')
    mark_as_unread.short_description = "تحديد كغير مقروء"

# إدارة المحافظات
@admin.register(Governorate)
class GovernorateAdmin(ModelAdmin):
    list_display = ['name', 'name_en', 'code', 'region', 'cities_count', 'created_at']
    list_filter = ['region', 'created_at']
    search_fields = ['name', 'name_en', 'code']
    ordering = ['name']
    readonly_fields = ['created_at']

    @display(description="عدد المدن")
    def cities_count(self, obj):
        return obj.cities.count()

# إدارة المدن
class CityInline(TabularInline):
    model = City
    extra = 1
    fields = ['name', 'name_en', 'is_capital']

@admin.register(City)
class CityAdmin(ModelAdmin):
    list_display = ['name', 'name_en', 'governorate', 'is_capital', 'halls_count', 'created_at']
    list_filter = ['governorate', 'is_capital', 'created_at']
    search_fields = ['name', 'name_en', 'governorate__name']
    ordering = ['governorate', 'name']
    readonly_fields = ['created_at']

    @display(description="عدد القاعات")
    def halls_count(self, obj):
        return obj.hall_set.count()

# تسجيل النماذج في لوحة الإدارة المخصصة
# Register new models
@admin.register(HallService)
class HallServiceAdmin(ModelAdmin):
    list_display = ['name', 'hall', 'price', 'is_available', 'created_at']
    list_filter = ['is_available', 'hall', 'created_at']
    search_fields = ['name', 'description', 'hall__name']
    list_select_related = ['hall']
    ordering = ['hall__name', 'name']
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['hall']


@admin.register(HallMeal)
class HallMealAdmin(ModelAdmin):
    list_display = ['name', 'hall', 'meal_type_display', 'price_per_person', 'is_available', 'is_vegetarian', 'created_at']
    list_filter = ['meal_type', 'is_available', 'is_vegetarian', 'hall', 'created_at']
    search_fields = ['name', 'description', 'hall__name']
    list_select_related = ['hall']
    ordering = ['hall__name', 'meal_type', 'name']
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['hall']
    
    @display(description='نوع الوجبة')
    def meal_type_display(self, obj):
        return obj.get_meal_type_display()


@admin.register(BookingService)
class BookingServiceAdmin(ModelAdmin):
    list_display = ['booking', 'service', 'quantity', 'price', 'total_price']
    list_filter = ['service']
    search_fields = ['booking__customer_name', 'service__name']
    autocomplete_fields = ['booking', 'service']
    
    def get_readonly_fields(self, request, obj=None):
        return ['created_at'] if obj else []
    
    @display(description='الإجمالي')
    def total_price(self, obj):
        return obj.quantity * obj.price


@admin.register(BookingMeal)
class BookingMealAdmin(ModelAdmin):
    list_display = ['booking', 'meal', 'quantity', 'price_per_person', 'total_price', 'serving_time']
    list_filter = ['meal__meal_type', 'serving_time']
    search_fields = ['booking__customer_name', 'meal__name']
    autocomplete_fields = ['booking', 'meal']
    
    def get_readonly_fields(self, request, obj=None):
        return ['total_price']
    
    @display(description='الإجمالي')
    def total_price(self, obj):
        return obj.quantity * obj.price_per_person


@admin.register(HallImage)
class HallImageAdmin(ModelAdmin):
    list_display = ['hall', 'title', 'image_type', 'is_featured', 'order', 'uploaded_at']
    list_filter = ['image_type', 'is_featured', 'hall', 'uploaded_at']
    search_fields = ['title', 'description', 'hall__name']
    list_select_related = ['hall']
    ordering = ['hall__name', 'order', '-uploaded_at']
    readonly_fields = ['uploaded_at']
    autocomplete_fields = ['hall']
    
    fieldsets = (
        ('معلومات الصورة', {
            'fields': ('hall', 'image', 'image_type', 'title', 'description')
        }),
        ('إعدادات العرض', {
            'fields': ('is_featured', 'order')
        }),
        ('التواريخ', {
            'fields': ('uploaded_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(SiteSettings)
class SiteSettingsAdmin(ModelAdmin):
    """إدارة إعدادات الموقع"""
    
    def has_add_permission(self, request):
        # السماح بإضافة إعداد واحد فقط
        return not SiteSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # منع حذف الإعدادات
        return False
    
    fieldsets = (
        ('معلومات الموقع الأساسية', {
            'fields': ('site_name', 'site_name_ar', 'logo', 'favicon')
        }),
        ('معلومات التواصل', {
            'fields': ('phone_primary', 'phone_secondary', 'email_primary', 'email_secondary'),
            'classes': ('wide',)
        }),
        ('العنوان', {
            'fields': ('address', 'city', 'country'),
            'classes': ('wide',)
        }),
        ('وسائل التواصل الاجتماعي', {
            'fields': ('facebook_url', 'twitter_url', 'instagram_url', 'linkedin_url', 
                      'youtube_url', 'whatsapp_number', 'telegram_url'),
            'classes': ('wide',)
        }),
        ('إعدادات إضافية', {
            'fields': ('footer_text', 'copyright_year', 'working_hours', 'support_email'),
            'classes': ('wide',)
        }),
        ('تحسين محركات البحث (SEO)', {
            'fields': ('meta_description', 'meta_keywords'),
            'classes': ('collapse',)
        }),
        ('معلومات النظام', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def changelist_view(self, request, extra_context=None):
        # إذا لم توجد إعدادات، قم بإنشائها وتوجيه إلى صفحة التحرير
        if not SiteSettings.objects.exists():
            settings = SiteSettings.get_settings()
            return self.response_change(request, settings)
        return super().changelist_view(request, extra_context)


# Register models with the custom admin site
admin_site.register(Governorate, GovernorateAdmin)
admin_site.register(City, CityAdmin)
admin_site.register(Category, CategoryAdmin)
admin_site.register(Hall, HallAdmin)
admin_site.register(HallService, HallServiceAdmin)
admin_site.register(HallMeal, HallMealAdmin)
admin_site.register(Booking, BookingAdmin)
admin_site.register(Contact, ContactAdmin)
admin_site.register(HallManager, HallManagerAdmin)