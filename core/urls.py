"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from hall_booking.admin import admin_site

# حفظ المرجع الأصلي لتجنب الـ recursion
from django.contrib.admin import site as default_admin_site
original_get_urls = default_admin_site.get_urls

def get_admin_urls():
    def statistics_view_wrapper(request):
        return admin_site.statistics_view(request)
    
    def bookings_chart_api_wrapper(request):
        return admin_site.bookings_chart_api(request)
    
    def revenue_chart_api_wrapper(request):
        return admin_site.revenue_chart_api(request)
    
    def halls_chart_api_wrapper(request):
        return admin_site.halls_chart_api(request)
    
    # استخدام المرجع الأصلي لتجنب الـ recursion
    urls = original_get_urls()
    custom_urls = [
        path('statistics/', default_admin_site.admin_view(statistics_view_wrapper), name='statistics'),
        path('statistics/api/bookings-chart/', default_admin_site.admin_view(bookings_chart_api_wrapper), name='bookings_chart_api'),
        path('statistics/api/revenue-chart/', default_admin_site.admin_view(revenue_chart_api_wrapper), name='revenue_chart_api'),
        path('statistics/api/halls-chart/', default_admin_site.admin_view(halls_chart_api_wrapper), name='halls_chart_api'),
    ]
    return custom_urls + urls

# تطبيق المسارات المخصصة
default_admin_site.get_urls = get_admin_urls

from hall_booking import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),  # لوحة الإدارة الافتراضية مع المسارات المخصصة
    path('admin-site/', admin_site.urls),  # لوحة الإدارة المخصصة إذا أردت الاحتفاظ بها
    
    # Add authentication URLs for admin theme compatibility
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    path('', include('hall_booking.urls')),
    path('', views.home, name='index'),  # Add index URL for admin theme compatibility
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
